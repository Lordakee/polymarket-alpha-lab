"""Pure typed human review queue v6 for paper strategy recommendations."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


REVIEW_ACTIONS = ("enter", "watch", "skip")
REVIEW_STATUSES = (
    "incomplete_audit_packet",
    "risk_review",
    "source_conflict_review",
    "large_notional_review",
    "low_confidence_review",
    "review_ready",
)
ACTION_PRIORITY = {"enter": 0, "watch": 1, "skip": 2}
SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


__all__ = (
    "PaperStrategyHumanReviewQueueV6Config",
    "PaperStrategyHumanReviewQueueV6Recommendation",
    "PaperStrategyHumanReviewQueueV6Report",
    "PaperStrategyHumanReviewQueueV6Row",
    "build_paper_strategy_human_review_queue_v6",
    "paper_strategy_human_review_queue_v6_payload",
)


@dataclass(frozen=True)
class PaperStrategyHumanReviewQueueV6Config:
    config_version: str
    large_notional_threshold: Decimal
    min_team_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "large_notional_threshold",
            _normalize_nonnegative_decimal(
                "large_notional_threshold",
                self.large_notional_threshold,
            ),
        )
        object.__setattr__(
            self,
            "min_team_confidence",
            _normalize_probability("min_team_confidence", self.min_team_confidence),
        )
        require_paper_only_flags("PaperStrategyHumanReviewQueueV6Config", self)
        reject_unsafe_surface_fields("PaperStrategyHumanReviewQueueV6Config", self)


@dataclass(frozen=True)
class PaperStrategyHumanReviewQueueV6Recommendation:
    recommendation_id: str
    candidate_id: str
    market_slug: str
    outcome_name: str
    team_id: str
    action: str
    audit_packet_complete: bool
    risk_flags: tuple[str, ...]
    source_conflict: bool
    notional_size: Decimal
    team_confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "recommendation_id",
            "candidate_id",
            "market_slug",
            "outcome_name",
            "team_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_action("action", self.action)
        _require_bool("audit_packet_complete", self.audit_packet_complete)
        object.__setattr__(
            self,
            "risk_flags",
            _normalize_string_tuple("risk_flags", self.risk_flags),
        )
        _require_bool("source_conflict", self.source_conflict)
        object.__setattr__(
            self,
            "notional_size",
            _normalize_nonnegative_decimal("notional_size", self.notional_size),
        )
        object.__setattr__(
            self,
            "team_confidence",
            _normalize_probability("team_confidence", self.team_confidence),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("PaperStrategyHumanReviewQueueV6Recommendation", self)
        reject_unsafe_surface_fields(
            "PaperStrategyHumanReviewQueueV6Recommendation",
            self,
        )


@dataclass(frozen=True)
class PaperStrategyHumanReviewQueueV6Row:
    recommendation_id: str
    candidate_id: str
    market_slug: str
    outcome_name: str
    team_id: str
    action: str
    audit_packet_complete: bool
    risk_flags: tuple[str, ...]
    source_conflict: bool
    notional_size: Decimal
    team_confidence: Decimal
    review_rank: int
    review_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "recommendation_id",
            "candidate_id",
            "market_slug",
            "outcome_name",
            "team_id",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_action("action", self.action)
        _require_bool("audit_packet_complete", self.audit_packet_complete)
        object.__setattr__(
            self,
            "risk_flags",
            _normalize_string_tuple("risk_flags", self.risk_flags),
        )
        _require_bool("source_conflict", self.source_conflict)
        object.__setattr__(
            self,
            "notional_size",
            _normalize_nonnegative_decimal("notional_size", self.notional_size),
        )
        object.__setattr__(
            self,
            "team_confidence",
            _normalize_probability("team_confidence", self.team_confidence),
        )
        _require_positive_int("review_rank", self.review_rank)
        _require_review_status("review_status", self.review_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("PaperStrategyHumanReviewQueueV6Row", self)
        reject_unsafe_surface_fields("PaperStrategyHumanReviewQueueV6Row", self)


@dataclass(frozen=True)
class PaperStrategyHumanReviewQueueV6Report:
    generated_at: datetime
    config_version: str
    input_count: int
    queue_count: int
    incomplete_audit_packet_count: int
    risk_flagged_count: int
    source_conflict_count: int
    large_notional_count: int
    low_confidence_count: int
    top_recommendation_id: str | None
    rows: tuple[PaperStrategyHumanReviewQueueV6Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "queue_count",
            "incomplete_audit_packet_count",
            "risk_flagged_count",
            "source_conflict_count",
            "large_notional_count",
            "low_confidence_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.top_recommendation_id is not None:
            _require_canonical_string("top_recommendation_id", self.top_recommendation_id)
        object.__setattr__(
            self,
            "rows",
            _normalize_typed_tuple(
                "rows",
                self.rows,
                PaperStrategyHumanReviewQueueV6Row,
            ),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("PaperStrategyHumanReviewQueueV6Report", self)
        reject_unsafe_surface_fields("PaperStrategyHumanReviewQueueV6Report", self)


def build_paper_strategy_human_review_queue_v6(
    recommendations: Iterable[PaperStrategyHumanReviewQueueV6Recommendation],
    *,
    config: PaperStrategyHumanReviewQueueV6Config,
    generated_at: datetime,
) -> PaperStrategyHumanReviewQueueV6Report:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable")
    if type(config) is not PaperStrategyHumanReviewQueueV6Config:
        raise ValueError("config must be a PaperStrategyHumanReviewQueueV6Config")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    try:
        input_rows = tuple(recommendations)
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable") from exc

    seen_ids: set[str] = set()
    normalized: list[PaperStrategyHumanReviewQueueV6Recommendation] = []
    for item in input_rows:
        if type(item) is not PaperStrategyHumanReviewQueueV6Recommendation:
            raise ValueError(
                "recommendations must contain "
                "PaperStrategyHumanReviewQueueV6Recommendation values",
            )
        if item.recommendation_id in seen_ids:
            raise ValueError("duplicate recommendation_id values are not allowed")
        seen_ids.add(item.recommendation_id)
        normalized.append(item)

    ranked_inputs = sorted(normalized, key=_recommendation_sort_key)
    rows = tuple(
        _build_row(item, rank, config)
        for rank, item in enumerate(ranked_inputs, start=1)
    )
    return PaperStrategyHumanReviewQueueV6Report(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=len(input_rows),
        queue_count=len(rows),
        incomplete_audit_packet_count=sum(
            1 for row in rows if not row.audit_packet_complete
        ),
        risk_flagged_count=sum(1 for row in rows if row.risk_flags),
        source_conflict_count=sum(1 for row in rows if row.source_conflict),
        large_notional_count=sum(
            1 for row in rows if row.notional_size >= config.large_notional_threshold
        ),
        low_confidence_count=sum(
            1 for row in rows if row.team_confidence < config.min_team_confidence
        ),
        top_recommendation_id=rows[0].recommendation_id if rows else None,
        rows=rows,
    )


def paper_strategy_human_review_queue_v6_payload(
    report: PaperStrategyHumanReviewQueueV6Report,
) -> dict[str, Any]:
    if type(report) is not PaperStrategyHumanReviewQueueV6Report:
        raise ValueError("report must be a PaperStrategyHumanReviewQueueV6Report")
    require_paper_only_flags("PaperStrategyHumanReviewQueueV6Report", report)
    reject_unsafe_surface_fields("PaperStrategyHumanReviewQueueV6Report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    reject_unsafe_surface_fields("PaperStrategyHumanReviewQueueV6Report payload", payload)
    return payload


def _build_row(
    item: PaperStrategyHumanReviewQueueV6Recommendation,
    rank: int,
    config: PaperStrategyHumanReviewQueueV6Config,
) -> PaperStrategyHumanReviewQueueV6Row:
    return PaperStrategyHumanReviewQueueV6Row(
        recommendation_id=item.recommendation_id,
        candidate_id=item.candidate_id,
        market_slug=item.market_slug,
        outcome_name=item.outcome_name,
        team_id=item.team_id,
        action=item.action,
        audit_packet_complete=item.audit_packet_complete,
        risk_flags=item.risk_flags,
        source_conflict=item.source_conflict,
        notional_size=item.notional_size,
        team_confidence=item.team_confidence,
        review_rank=rank,
        review_status=_review_status(item, config),
        reason_codes=_row_reason_codes(item, config),
    )


def _review_status(
    item: PaperStrategyHumanReviewQueueV6Recommendation,
    config: PaperStrategyHumanReviewQueueV6Config,
) -> str:
    if not item.audit_packet_complete:
        return "incomplete_audit_packet"
    if item.risk_flags:
        return "risk_review"
    if item.source_conflict:
        return "source_conflict_review"
    if item.notional_size >= config.large_notional_threshold:
        return "large_notional_review"
    if item.team_confidence < config.min_team_confidence:
        return "low_confidence_review"
    return "review_ready"


def _row_reason_codes(
    item: PaperStrategyHumanReviewQueueV6Recommendation,
    config: PaperStrategyHumanReviewQueueV6Config,
) -> tuple[str, ...]:
    reasons = [
        f"action_{item.action}",
        "audit_packet_complete"
        if item.audit_packet_complete
        else "audit_packet_incomplete",
        "human_review_required",
    ]
    if item.notional_size >= config.large_notional_threshold:
        reasons.append("large_notional_size")
    if item.team_confidence < config.min_team_confidence:
        reasons.append("low_team_confidence")
    if item.risk_flags:
        reasons.append("risk_flags_present")
    if item.source_conflict:
        reasons.append("source_conflict_present")
    reasons.extend(item.reason_codes)
    return tuple(reasons)


def _recommendation_sort_key(
    item: PaperStrategyHumanReviewQueueV6Recommendation,
) -> tuple[int, int, int, int, Decimal, Decimal, str]:
    return (
        ACTION_PRIORITY[item.action],
        0 if not item.audit_packet_complete else 1,
        0 if item.risk_flags else 1,
        0 if item.source_conflict else 1,
        -item.notional_size,
        item.team_confidence,
        item.recommendation_id,
    )


def _validate_report_consistency(report: PaperStrategyHumanReviewQueueV6Report) -> None:
    if report.queue_count != len(report.rows):
        raise ValueError("queue_count must equal rows length")
    if report.input_count < report.queue_count:
        raise ValueError("input_count must be at least queue_count")
    if report.incomplete_audit_packet_count != sum(
        1 for row in report.rows if not row.audit_packet_complete
    ):
        raise ValueError("incomplete_audit_packet_count must match rows")
    if report.risk_flagged_count != sum(1 for row in report.rows if row.risk_flags):
        raise ValueError("risk_flagged_count must match rows")
    if report.source_conflict_count != sum(1 for row in report.rows if row.source_conflict):
        raise ValueError("source_conflict_count must match rows")
    if report.rows:
        if tuple(row.review_rank for row in report.rows) != tuple(
            range(1, len(report.rows) + 1),
        ):
            raise ValueError("review_rank values must be consecutive")
        if report.top_recommendation_id != report.rows[0].recommendation_id:
            raise ValueError("top_recommendation_id must match first row")
    elif report.top_recommendation_id is not None:
        raise ValueError("top_recommendation_id must be absent without rows")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(SCORE_QUANT)


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _normalize_typed_tuple(
    field_name: str,
    value: object,
    expected_type: type[PaperStrategyHumanReviewQueueV6Row],
) -> tuple[PaperStrategyHumanReviewQueueV6Row, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain typed rows")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain typed rows") from exc
    for item in items:
        if type(item) is not expected_type:
            raise ValueError(f"{field_name} must contain typed rows")
    return items


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REVIEW_ACTIONS:
        raise ValueError(f"{field_name} must be enter, watch, or skip")


def _require_review_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REVIEW_STATUSES:
        raise ValueError(f"{field_name} must be a known review status")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive int")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")
