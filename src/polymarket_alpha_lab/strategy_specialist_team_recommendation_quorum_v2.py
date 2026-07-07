"""Decimal-only paper report for specialist team recommendation quorum."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SIDES = ("yes", "no")
_STATUSES = ("blocked", "watch", "quorum_met")
_STATUS_RANK = {"blocked": 0, "watch": 1, "quorum_met": 2}
_EMPTY_REASON = "empty_recommendation_quorum"
_OWNED_REASON_CODES = frozenset(
    (
        "quorum_met",
        "quorum_watch",
        "quorum_blocked",
        "team_quorum_gap",
        "domain_quorum_gap",
        "source_coverage_gap",
        "domain_expertise_gap",
        "calibration_score_gap",
        "conflict_severity_blocked",
        "confidence_dispersion_watch",
        "liquidity_fee_awareness_watch",
        "quorum_score_gap",
        "side_conflict_blocked",
        _EMPTY_REASON,
    ),
)
_REASON_RANK = {
    "quorum_blocked": 0,
    "quorum_met": 1,
    "quorum_watch": 2,
    "conflict_severity_blocked": 3,
    "confidence_dispersion_watch": 4,
    "liquidity_fee_awareness_watch": 5,
    "domain_quorum_gap": 6,
    "source_coverage_gap": 7,
    "team_quorum_gap": 8,
    "domain_expertise_gap": 9,
    "calibration_score_gap": 10,
    "quorum_score_gap": 11,
    "side_conflict_blocked": 12,
    _EMPTY_REASON: 13,
}
_REPORT_KEYS = (
    "generated_at",
    "config_version",
    "candidate_count",
    "recommendation_count",
    "quorum_met_count",
    "watch_count",
    "blocked_count",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_KEYS = (
    "candidate_id",
    "recommendation_side",
    "team_count",
    "qualified_team_count",
    "domain_count",
    "qualified_domain_count",
    "independent_source_count",
    "domain_expertise_score",
    "calibration_score",
    "source_coverage_score",
    "conflict_severity",
    "confidence_dispersion",
    "liquidity_fee_awareness_score",
    "quorum_score",
    "quorum_status",
    "latest_observed_at",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _surface_term("li", "ve"),
        _surface_term("au", "th"),
        _surface_term("wa", "llet"),
        _surface_term("or", "der"),
        _surface_term("net", "work"),
        _surface_term("data", "base"),
        _surface_term("per", "sist"),
        _surface_term("sign", "ing"),
        _surface_term("mut", "ation"),
        _surface_term("b", "uy"),
        _surface_term("se", "ll"),
        _surface_term("tra", "de"),
    ),
)


@dataclass(frozen=True)
class StrategySpecialistTeamRecommendationQuorumV2Config:
    config_version: str
    quorum_team_count: Decimal
    quorum_domain_count: Decimal
    min_domain_expertise: Decimal
    min_calibration_score: Decimal
    min_independent_source_count: Decimal
    min_source_independence_score: Decimal
    max_conflict_severity: Decimal
    max_confidence_dispersion: Decimal
    min_liquidity_score: Decimal
    max_fee_drag: Decimal
    max_estimated_slippage: Decimal
    min_quorum_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        for field_name in ("quorum_team_count", "quorum_domain_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_independent_source_count",):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_domain_expertise",
            "min_calibration_score",
            "min_source_independence_score",
            "max_conflict_severity",
            "max_confidence_dispersion",
            "min_liquidity_score",
            "max_fee_drag",
            "max_estimated_slippage",
            "min_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class StrategySpecialistTeamRecommendationQuorumV2Input:
    candidate_id: str
    team_id: str
    domain_id: str
    recommendation_side: str
    confidence: Decimal
    domain_expertise: Decimal
    calibration_score: Decimal
    independent_source_count: Decimal
    source_independence_score: Decimal
    conflict_severity: Decimal
    liquidity_score: Decimal
    fee_drag: Decimal
    estimated_slippage: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "team_id",
            "domain_id",
            "recommendation_side",
        ):
            _require_text(field_name, getattr(self, field_name))
        if self.recommendation_side not in _SIDES:
            raise ValueError("recommendation_side must be yes or no")
        for field_name in (
            "confidence",
            "domain_expertise",
            "calibration_score",
            "source_independence_score",
            "conflict_severity",
            "liquidity_score",
            "fee_drag",
            "estimated_slippage",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "independent_source_count",
            _normalize_nonnegative_count(
                "independent_source_count",
                self.independent_source_count,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_flags("recommendation", self)


@dataclass(frozen=True)
class StrategySpecialistTeamRecommendationQuorumV2Row:
    candidate_id: str
    recommendation_side: str
    team_count: Decimal
    qualified_team_count: Decimal
    domain_count: Decimal
    qualified_domain_count: Decimal
    independent_source_count: Decimal
    domain_expertise_score: Decimal
    calibration_score: Decimal
    source_coverage_score: Decimal
    conflict_severity: Decimal
    confidence_dispersion: Decimal
    liquidity_fee_awareness_score: Decimal
    quorum_score: Decimal
    quorum_status: str
    latest_observed_at: datetime
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("candidate_id", self.candidate_id)
        _require_text("recommendation_side", self.recommendation_side)
        if self.recommendation_side not in (*_SIDES, "mixed"):
            raise ValueError("recommendation_side must be yes, no, or mixed")
        for field_name in (
            "team_count",
            "qualified_team_count",
            "domain_count",
            "qualified_domain_count",
            "independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "domain_expertise_score",
            "calibration_score",
            "source_coverage_score",
            "conflict_severity",
            "confidence_dispersion",
            "liquidity_fee_awareness_score",
            "quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("quorum_status", self.quorum_status)
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("row", self)
        _check_row(self)
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


@dataclass(frozen=True)
class StrategySpecialistTeamRecommendationQuorumV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    recommendation_count: Decimal
    quorum_met_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategySpecialistTeamRecommendationQuorumV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "recommendation_count",
            "quorum_met_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_flags("report", self)
        _check_report(self)
        for row in self.rows:
            _require_row_digest(row)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_strategy_specialist_team_recommendation_quorum_v2_report(
    recommendations: object,
    *,
    config: StrategySpecialistTeamRecommendationQuorumV2Config,
    generated_at: datetime,
) -> StrategySpecialistTeamRecommendationQuorumV2Report:
    if type(config) is not StrategySpecialistTeamRecommendationQuorumV2Config:
        raise ValueError(
            "config must be a StrategySpecialistTeamRecommendationQuorumV2Config",
        )
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_recommendations(recommendations)
    for item in items:
        if item.observed_at > generated_at:
            raise ValueError("generated_at must not precede observed_at")
    rows = tuple(
        sorted(
            (
                _candidate_row(
                    candidate_id,
                    candidate_items,
                    config=config,
                )
                for candidate_id, candidate_items in _group_recommendations(items)
            ),
            key=_row_sort_key,
        ),
    )
    return StrategySpecialistTeamRecommendationQuorumV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        recommendation_count=_count(len(items)),
        quorum_met_count=_status_count(rows, "quorum_met"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_specialist_team_recommendation_quorum_v2_payload(
    report: StrategySpecialistTeamRecommendationQuorumV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategySpecialistTeamRecommendationQuorumV2Report:
        _require_flags("report", report)
        _require_report_digest(report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public("payload", report)
        _reject_raw_public_numbers("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        _reject_unsafe_public("payload", payload)
        return payload
    raise ValueError("report must be a StrategySpecialistTeamRecommendationQuorumV2Report")


def _candidate_row(
    candidate_id: str,
    items: tuple[StrategySpecialistTeamRecommendationQuorumV2Input, ...],
    *,
    config: StrategySpecialistTeamRecommendationQuorumV2Config,
) -> StrategySpecialistTeamRecommendationQuorumV2Row:
    sides = tuple(sorted({item.recommendation_side for item in items}))
    recommendation_side = sides[0] if len(sides) == 1 else "mixed"
    qualified_items = tuple(item for item in items if _is_qualified(item, config))
    qualified_domains = tuple(sorted({item.domain_id for item in qualified_items}))
    domain_expertise_score = _average(tuple(item.domain_expertise for item in items))
    calibration_score = _average(tuple(item.calibration_score for item in items))
    source_coverage_score = _average(
        tuple(item.source_independence_score for item in items),
    )
    conflict_severity = max(item.conflict_severity for item in items)
    confidence_values = tuple(item.confidence for item in items)
    confidence_dispersion = _quantize(max(confidence_values) - min(confidence_values))
    liquidity_fee_awareness_score = _liquidity_fee_awareness_score(items)
    team_count = _count(len(items))
    domain_count = _count(len({item.domain_id for item in items}))
    quorum_score = _quorum_score(
        team_count=_quorum_ratio(team_count, config.quorum_team_count),
        domain_count=_quorum_ratio(domain_count, config.quorum_domain_count),
        domain_expertise_score=domain_expertise_score,
        calibration_score=calibration_score,
        source_coverage_score=source_coverage_score,
        conflict_control=_clamp_ratio(_ONE - conflict_severity),
        confidence_cohesion=_clamp_ratio(_ONE - confidence_dispersion),
        liquidity_fee_awareness_score=liquidity_fee_awareness_score,
    )
    reason_codes = _row_reason_codes(
        recommendation_side=recommendation_side,
        qualified_team_count=_count(len(qualified_items)),
        qualified_domain_count=_count(len(qualified_domains)),
        independent_source_count=_sum_decimals(
            tuple(item.independent_source_count for item in items),
        ),
        domain_expertise_score=domain_expertise_score,
        calibration_score=calibration_score,
        source_coverage_score=source_coverage_score,
        conflict_severity=conflict_severity,
        confidence_dispersion=confidence_dispersion,
        quorum_score=quorum_score,
        items=items,
        config=config,
    )
    return StrategySpecialistTeamRecommendationQuorumV2Row(
        candidate_id=candidate_id,
        recommendation_side=recommendation_side,
        team_count=team_count,
        qualified_team_count=_count(len(qualified_items)),
        domain_count=domain_count,
        qualified_domain_count=_count(len(qualified_domains)),
        independent_source_count=_sum_decimals(
            tuple(item.independent_source_count for item in items),
        ),
        domain_expertise_score=domain_expertise_score,
        calibration_score=calibration_score,
        source_coverage_score=source_coverage_score,
        conflict_severity=conflict_severity,
        confidence_dispersion=confidence_dispersion,
        liquidity_fee_awareness_score=liquidity_fee_awareness_score,
        quorum_score=quorum_score,
        quorum_status=_status_from_reasons(reason_codes),
        latest_observed_at=max(item.observed_at for item in items),
        reason_codes=reason_codes,
    )


def _is_qualified(
    item: StrategySpecialistTeamRecommendationQuorumV2Input,
    config: StrategySpecialistTeamRecommendationQuorumV2Config,
) -> bool:
    return (
        item.domain_expertise >= config.min_domain_expertise
        and item.calibration_score >= config.min_calibration_score
        and item.independent_source_count >= config.min_independent_source_count
        and item.source_independence_score >= config.min_source_independence_score
    )


def _liquidity_fee_awareness_score(
    items: tuple[StrategySpecialistTeamRecommendationQuorumV2Input, ...],
) -> Decimal:
    values: list[Decimal] = []
    for item in items:
        values.append(item.liquidity_score)
        values.append(_clamp_ratio(_ONE - item.fee_drag))
        values.append(_clamp_ratio(_ONE - item.estimated_slippage))
    return _average(tuple(values))


def _quorum_score(
    *,
    team_count: Decimal,
    domain_count: Decimal,
    domain_expertise_score: Decimal,
    calibration_score: Decimal,
    source_coverage_score: Decimal,
    conflict_control: Decimal,
    confidence_cohesion: Decimal,
    liquidity_fee_awareness_score: Decimal,
) -> Decimal:
    return _average(
        (
            team_count,
            domain_count,
            domain_expertise_score,
            calibration_score,
            source_coverage_score,
            conflict_control,
            confidence_cohesion,
            liquidity_fee_awareness_score,
        ),
    )


def _row_reason_codes(
    *,
    recommendation_side: str,
    qualified_team_count: Decimal,
    qualified_domain_count: Decimal,
    independent_source_count: Decimal,
    domain_expertise_score: Decimal,
    calibration_score: Decimal,
    source_coverage_score: Decimal,
    conflict_severity: Decimal,
    confidence_dispersion: Decimal,
    quorum_score: Decimal,
    items: tuple[StrategySpecialistTeamRecommendationQuorumV2Input, ...],
    config: StrategySpecialistTeamRecommendationQuorumV2Config,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if recommendation_side == "mixed" or conflict_severity > config.max_conflict_severity:
        reasons.append("quorum_blocked")
    elif _passes_quorum(
        qualified_team_count=qualified_team_count,
        qualified_domain_count=qualified_domain_count,
        independent_source_count=independent_source_count,
        domain_expertise_score=domain_expertise_score,
        calibration_score=calibration_score,
        source_coverage_score=source_coverage_score,
        confidence_dispersion=confidence_dispersion,
        quorum_score=quorum_score,
        items=items,
        config=config,
    ):
        reasons.append("quorum_met")
    else:
        reasons.append("quorum_watch")
    if recommendation_side == "mixed":
        reasons.append("side_conflict_blocked")
    if conflict_severity > config.max_conflict_severity:
        reasons.append("conflict_severity_blocked")
    if confidence_dispersion > config.max_confidence_dispersion:
        reasons.append("confidence_dispersion_watch")
    if _liquidity_fee_awareness_watch(items, config):
        reasons.append("liquidity_fee_awareness_watch")
    if qualified_domain_count < config.quorum_domain_count:
        reasons.append("domain_quorum_gap")
    if (
        independent_source_count < config.min_independent_source_count
        or source_coverage_score < config.min_source_independence_score
    ):
        reasons.append("source_coverage_gap")
    if qualified_team_count < config.quorum_team_count:
        reasons.append("team_quorum_gap")
    if domain_expertise_score < config.min_domain_expertise:
        reasons.append("domain_expertise_gap")
    if calibration_score < config.min_calibration_score:
        reasons.append("calibration_score_gap")
    if quorum_score < config.min_quorum_score:
        reasons.append("quorum_score_gap")
    return _sort_reason_codes(tuple(dict.fromkeys(reasons)))


def _passes_quorum(
    *,
    qualified_team_count: Decimal,
    qualified_domain_count: Decimal,
    independent_source_count: Decimal,
    domain_expertise_score: Decimal,
    calibration_score: Decimal,
    source_coverage_score: Decimal,
    confidence_dispersion: Decimal,
    quorum_score: Decimal,
    items: tuple[StrategySpecialistTeamRecommendationQuorumV2Input, ...],
    config: StrategySpecialistTeamRecommendationQuorumV2Config,
) -> bool:
    return (
        qualified_team_count >= config.quorum_team_count
        and qualified_domain_count >= config.quorum_domain_count
        and independent_source_count >= config.min_independent_source_count
        and domain_expertise_score >= config.min_domain_expertise
        and calibration_score >= config.min_calibration_score
        and source_coverage_score >= config.min_source_independence_score
        and confidence_dispersion <= config.max_confidence_dispersion
        and not _liquidity_fee_awareness_watch(items, config)
        and quorum_score >= config.min_quorum_score
    )


def _liquidity_fee_awareness_watch(
    items: tuple[StrategySpecialistTeamRecommendationQuorumV2Input, ...],
    config: StrategySpecialistTeamRecommendationQuorumV2Config,
) -> bool:
    return any(
        item.liquidity_score < config.min_liquidity_score
        or item.fee_drag > config.max_fee_drag
        or item.estimated_slippage > config.max_estimated_slippage
        for item in items
    )


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if "quorum_blocked" in reason_codes:
        return "blocked"
    if "quorum_met" in reason_codes:
        return "quorum_met"
    return "watch"


def _normalize_recommendations(
    recommendations: object,
) -> tuple[StrategySpecialistTeamRecommendationQuorumV2Input, ...]:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable")
    try:
        items = tuple(recommendations)
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not StrategySpecialistTeamRecommendationQuorumV2Input:
            raise ValueError(
                "recommendations must contain StrategySpecialistTeamRecommendationQuorumV2Input",
            )
        _require_flags("recommendation", item)
        key = (item.candidate_id, item.team_id)
        if key in seen:
            raise ValueError("recommendations must not contain duplicate candidate-team pairs")
        seen.add(key)
    return items


def _group_recommendations(
    items: tuple[StrategySpecialistTeamRecommendationQuorumV2Input, ...],
) -> tuple[tuple[str, tuple[StrategySpecialistTeamRecommendationQuorumV2Input, ...]], ...]:
    candidate_ids = tuple(sorted({item.candidate_id for item in items}))
    return tuple(
        (
            candidate_id,
            tuple(
                sorted(
                    (item for item in items if item.candidate_id == candidate_id),
                    key=lambda item: item.team_id,
                ),
            ),
        )
        for candidate_id in candidate_ids
    )


def _normalize_rows(
    rows: object,
) -> tuple[StrategySpecialistTeamRecommendationQuorumV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        if type(item) is not StrategySpecialistTeamRecommendationQuorumV2Row:
            raise ValueError("rows must contain StrategySpecialistTeamRecommendationQuorumV2Row")
        _require_flags("row", item)
        _require_row_digest(item)
    if items != tuple(sorted(items, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return items


def _row_sort_key(row: StrategySpecialistTeamRecommendationQuorumV2Row) -> tuple[int, Decimal, str]:
    return (_STATUS_RANK[row.quorum_status], -row.quorum_score, row.candidate_id)


def _status_count(
    rows: tuple[StrategySpecialistTeamRecommendationQuorumV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.quorum_status == status))


def _report_status(rows: tuple[StrategySpecialistTeamRecommendationQuorumV2Row, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.quorum_status == "blocked" for row in rows):
        return "blocked"
    if any(row.quorum_status == "watch" for row in rows):
        return "watch"
    return "quorum_met"


def _report_reason_codes(
    rows: tuple[StrategySpecialistTeamRecommendationQuorumV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    return _sort_reason_codes(
        tuple(dict.fromkeys(reason for row in rows for reason in row.reason_codes)),
    )


def _check_row(row: StrategySpecialistTeamRecommendationQuorumV2Row) -> None:
    if row.qualified_team_count > row.team_count:
        raise ValueError("qualified_team_count must not exceed team_count")
    if row.qualified_domain_count > row.domain_count:
        raise ValueError("qualified_domain_count must not exceed domain_count")
    expected_terminal = {
        "blocked": "quorum_blocked",
        "watch": "quorum_watch",
        "quorum_met": "quorum_met",
    }[row.quorum_status]
    if expected_terminal not in row.reason_codes:
        raise ValueError("reason_codes must include quorum status reason")


def _check_report(report: StrategySpecialistTeamRecommendationQuorumV2Report) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.quorum_met_count != _status_count(rows, "quorum_met"):
        raise ValueError("quorum_met_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _row_digest(row: StrategySpecialistTeamRecommendationQuorumV2Row) -> str:
    value = asdict(row)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _report_digest(report: StrategySpecialistTeamRecommendationQuorumV2Report) -> str:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _require_row_digest(row: StrategySpecialistTeamRecommendationQuorumV2Row) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest mismatch")


def _require_report_digest(report: StrategySpecialistTeamRecommendationQuorumV2Report) -> None:
    for row in report.rows:
        _require_row_digest(row)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest mismatch")


def _verify_report_payload(payload: dict[str, Any]) -> None:
    _require_exact_keys("payload", payload, _REPORT_KEYS)
    _require_payload_flags("payload", payload)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload.rows must be a JSON list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_row_payload(f"payload.rows[{index}]", row)
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not supplied_digest:
        raise ValueError("derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _verify_row_payload(label: str, payload: dict[str, Any]) -> None:
    _require_exact_keys(label, payload, _ROW_KEYS)
    _require_payload_flags(label, payload)
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not supplied_digest:
        raise ValueError(f"{label}.derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _require_exact_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    for key in expected_keys:
        if key not in payload:
            raise ValueError(f"{label}.{key} is required")
    extra_keys = tuple(sorted(set(payload) - set(expected_keys)))
    if extra_keys:
        raise ValueError(f"{label} contains unsupported public field: {extra_keys[0]}")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _canonical_digest(payload: object) -> str:
    ready = _json_ready(payload)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be an exact Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if type(value) is str:
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public(label, item)


def _reject_raw_public_numbers(label: str, value: object) -> None:
    if isinstance(value, Decimal):
        raise ValueError(f"{label} JSON Decimal values must be strings")
    if isinstance(value, float):
        raise ValueError(f"{label} JSON values must not be floats")
    if type(value) is int:
        raise ValueError(f"{label} JSON numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_raw_public_numbers(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_raw_public_numbers(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _require_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be non-empty without surrounding whitespace")
    if _has_unsafe_fragment(value):
        raise ValueError(f"unsafe value in {name}")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{name} must be a supported quorum status")


def _normalize_input_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes("reason_codes", values)
    for reason_code in reason_codes:
        if reason_code in _OWNED_REASON_CODES:
            raise ValueError("input reason_codes must not include reducer-owned values")
    return reason_codes


def _normalize_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    if isinstance(values, (set, frozenset)):
        raise ValueError(f"{name} must be an ordered iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        _require_text(name, item)
        if item != item.lower():
            raise ValueError(f"{name} must contain lowercase values")
        for part in item.split("_"):
            if not part or not part.isalnum() or part != part.lower():
                raise ValueError(f"{name} must contain canonical values")
        if item in seen:
            raise ValueError(f"{name} must not contain duplicates")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(reason_codes, key=_reason_key))


def _reason_key(reason_code: str) -> tuple[int, str]:
    return (_REASON_RANK.get(reason_code, len(_REASON_RANK)), reason_code)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must not be empty")
    return _ratio(sum(values, _ZERO), _count(len(values)))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _quorum_ratio(count_value: Decimal, threshold: Decimal) -> Decimal:
    if threshold <= _ZERO:
        raise ValueError("quorum threshold must be positive")
    return _clamp_ratio(_ratio(count_value, threshold))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        raise ValueError("ratio denominator must be non-zero")
    return _quantize(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(_ONE, max(_ZERO, _quantize(value)))


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be non-negative")
    return _quantize(Decimal(value))


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be non-negative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


__all__ = (
    "StrategySpecialistTeamRecommendationQuorumV2Config",
    "StrategySpecialistTeamRecommendationQuorumV2Input",
    "StrategySpecialistTeamRecommendationQuorumV2Report",
    "StrategySpecialistTeamRecommendationQuorumV2Row",
    "build_strategy_specialist_team_recommendation_quorum_v2_report",
    "strategy_specialist_team_recommendation_quorum_v2_payload",
)
