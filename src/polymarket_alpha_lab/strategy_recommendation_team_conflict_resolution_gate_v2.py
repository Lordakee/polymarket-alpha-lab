"""Pure Phase 1 gate for specialist-team recommendation conflicts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_RECOMMENDATION_TEAM_CONFLICT_RESOLUTION_GATE_V2_CONFIG_VERSION = (
    "strategy-recommendation-team-conflict-resolution-gate-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_NEGATIVE_ONE = Decimal("-1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)

_SIDES = ("yes", "no")
_STATUSES = ("blocked", "watch", "qualified")
_STATUS_RANK = {"blocked": 0, "watch": 1, "qualified": 2}
_EMPTY_REASON = "empty_team_conflict_resolution_gate_v2"
_REASON_CODES = (
    "side_disagreement",
    "forecast_dispersion_high",
    "evidence_quality_difference_high",
    "source_family_overlap_high",
    "recency_mismatch_high",
    "resolution_ambiguity_high",
    "cost_adjusted_edge_margin_low",
    "team_conflict_resolution_gate_v2_blocked",
    "team_conflict_resolution_gate_v2_watch",
    "team_conflict_resolution_gate_v2_qualified",
    _EMPTY_REASON,
)
_STATUS_REASON = {
    "blocked": "team_conflict_resolution_gate_v2_blocked",
    "watch": "team_conflict_resolution_gate_v2_watch",
    "qualified": "team_conflict_resolution_gate_v2_qualified",
}
_BLOCKING_REASONS = frozenset(
    (
        "recency_mismatch_high",
        "resolution_ambiguity_high",
        "cost_adjusted_edge_margin_low",
    ),
)
_REPORT_KEYS = (
    "generated_at",
    "config_version",
    "input_count",
    "candidate_count",
    "qualified_count",
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
    "market_slug",
    "chosen_recommendation_id",
    "chosen_team_id",
    "chosen_side",
    "team_count",
    "side_count",
    "source_family_count",
    "forecast_dispersion",
    "evidence_quality_difference",
    "source_family_overlap_ratio",
    "recency_mismatch_seconds",
    "max_resolution_ambiguity_score",
    "best_cost_adjusted_edge",
    "cost_adjusted_edge_margin",
    "gate_status",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "auth",
        "private_key",
        "wallet",
        "account",
        "balance",
        "order",
        "cancel",
        "replace",
        "sign",
        "exchange_mutation",
        "sk_live",
        "pk_live",
        "://",
        "database",
        "persist",
        "network",
        "mutation",
        "buy",
        "sell",
        "trade",
    ),
)


@dataclass(frozen=True)
class StrategyRecommendationTeamConflictResolutionGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_TEAM_CONFLICT_RESOLUTION_GATE_V2_CONFIG_VERSION
    )
    max_forecast_dispersion: Decimal = Decimal("0.050000")
    max_evidence_quality_difference: Decimal = Decimal("0.100000")
    max_source_family_overlap_ratio: Decimal = Decimal("0.250000")
    max_recency_mismatch_seconds: Decimal = Decimal("3600.000000")
    max_resolution_ambiguity_score: Decimal = Decimal("0.300000")
    min_cost_adjusted_edge: Decimal = Decimal("0.020000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationTeamConflictResolutionGateV2Config:
            raise ValueError(
                "config must be a StrategyRecommendationTeamConflictResolutionGateV2Config",
            )
        _require_text("config_version", self.config_version)
        for field_name in (
            "max_forecast_dispersion",
            "max_evidence_quality_difference",
            "max_source_family_overlap_ratio",
            "max_resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_recency_mismatch_seconds",
            _normalize_seconds(
                "max_recency_mismatch_seconds",
                self.max_recency_mismatch_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_cost_adjusted_edge",
            _normalize_edge("min_cost_adjusted_edge", self.min_cost_adjusted_edge),
        )
        _require_flags("config", self)
        _reject_unsafe_public("config", self)


@dataclass(frozen=True)
class StrategyRecommendationTeamConflictResolutionGateV2Input:
    recommendation_id: str
    candidate_id: str
    market_slug: str
    team_id: str
    recommendation_side: str
    forecast_probability: Decimal
    evidence_quality_score: Decimal
    source_family: str
    evidence_observed_at: datetime
    resolution_ambiguity_score: Decimal
    cost_adjusted_edge: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationTeamConflictResolutionGateV2Input:
            raise ValueError(
                "input must be a StrategyRecommendationTeamConflictResolutionGateV2Input",
            )
        for field_name in (
            "recommendation_id",
            "candidate_id",
            "market_slug",
            "team_id",
            "source_family",
        ):
            _require_text(field_name, getattr(self, field_name))
        _require_member("recommendation_side", self.recommendation_side, _SIDES)
        for field_name in (
            "forecast_probability",
            "evidence_quality_score",
            "resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_edge("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        _require_flags("input", self)
        _reject_unsafe_public("input", self)


@dataclass(frozen=True)
class StrategyRecommendationTeamConflictResolutionGateV2Row:
    candidate_id: str
    market_slug: str
    chosen_recommendation_id: str
    chosen_team_id: str
    chosen_side: str
    team_count: Decimal
    side_count: Decimal
    source_family_count: Decimal
    forecast_dispersion: Decimal
    evidence_quality_difference: Decimal
    source_family_overlap_ratio: Decimal
    recency_mismatch_seconds: Decimal
    max_resolution_ambiguity_score: Decimal
    best_cost_adjusted_edge: Decimal
    cost_adjusted_edge_margin: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationTeamConflictResolutionGateV2Row:
            raise ValueError(
                "row must be a StrategyRecommendationTeamConflictResolutionGateV2Row",
            )
        for field_name in (
            "candidate_id",
            "market_slug",
            "chosen_recommendation_id",
            "chosen_team_id",
        ):
            _require_text(field_name, getattr(self, field_name))
        _require_member("chosen_side", self.chosen_side, _SIDES)
        for field_name in ("team_count", "side_count", "source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "forecast_dispersion",
            "evidence_quality_difference",
            "source_family_overlap_ratio",
            "max_resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recency_mismatch_seconds",
            _normalize_seconds("recency_mismatch_seconds", self.recency_mismatch_seconds),
        )
        object.__setattr__(
            self,
            "best_cost_adjusted_edge",
            _normalize_edge("best_cost_adjusted_edge", self.best_cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge_margin",
            _normalize_decimal("cost_adjusted_edge_margin", self.cost_adjusted_edge_margin),
        )
        _require_member("gate_status", self.gate_status, _STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("row", self)
        _reject_unsafe_public("row", self)
        _check_row(self)
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


@dataclass(frozen=True)
class StrategyRecommendationTeamConflictResolutionGateV2Report:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    candidate_count: Decimal
    qualified_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyRecommendationTeamConflictResolutionGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationTeamConflictResolutionGateV2Report:
            raise ValueError(
                "report must be a StrategyRecommendationTeamConflictResolutionGateV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in (
            "input_count",
            "candidate_count",
            "qualified_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_flags("report", self)
        _reject_unsafe_public("report", self)
        _check_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_strategy_recommendation_team_conflict_resolution_gate_v2_report(
    recommendations: object,
    *,
    config: StrategyRecommendationTeamConflictResolutionGateV2Config,
    generated_at: datetime,
) -> StrategyRecommendationTeamConflictResolutionGateV2Report:
    if type(config) is not StrategyRecommendationTeamConflictResolutionGateV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationTeamConflictResolutionGateV2Config",
        )
    _require_flags("config", config)
    _reject_unsafe_public("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(recommendations)
    for item in items:
        if item.evidence_observed_at > generated_at_utc:
            raise ValueError("evidence_observed_at must not be in the future")
    rows = tuple(
        sorted(
            (
                _candidate_row(candidate_items, config=config, generated_at=generated_at_utc)
                for candidate_items in _candidate_groups(items)
            ),
            key=_row_key,
        ),
    )
    return StrategyRecommendationTeamConflictResolutionGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(items)),
        candidate_count=_count(len(rows)),
        qualified_count=_status_count(rows, "qualified"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_recommendation_team_conflict_resolution_gate_v2_payload(
    report: StrategyRecommendationTeamConflictResolutionGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyRecommendationTeamConflictResolutionGateV2Report:
        _require_flags("report", report)
        _require_report_digest(report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        return payload
    if type(report) is dict:
        _reject_raw_public_numbers("payload", report)
        _reject_unsafe_public("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        _reject_unsafe_public("payload", payload)
        return payload
    raise ValueError(
        "report must be a StrategyRecommendationTeamConflictResolutionGateV2Report",
    )


def _candidate_row(
    items: tuple[StrategyRecommendationTeamConflictResolutionGateV2Input, ...],
    *,
    config: StrategyRecommendationTeamConflictResolutionGateV2Config,
    generated_at: datetime,
) -> StrategyRecommendationTeamConflictResolutionGateV2Row:
    chosen = _choose_recommendation(items, generated_at)
    probabilities = tuple(item.forecast_probability for item in items)
    evidence_scores = tuple(item.evidence_quality_score for item in items)
    observed_ages = tuple(_age_seconds(generated_at, item.evidence_observed_at) for item in items)
    ambiguity_scores = tuple(item.resolution_ambiguity_score for item in items)
    source_family_count = len({item.source_family for item in items})
    overlap_ratio = _ratio(len(items) - source_family_count, len(items))
    edge_margin = _normalize_decimal(
        "cost_adjusted_edge_margin",
        chosen.cost_adjusted_edge - config.min_cost_adjusted_edge,
    )
    forecast_dispersion = _ratio_difference(probabilities)
    evidence_quality_difference = _ratio_difference(evidence_scores)
    recency_mismatch = _normalize_seconds(
        "recency_mismatch_seconds",
        max(observed_ages) - min(observed_ages),
    )
    max_resolution_ambiguity = max(ambiguity_scores)
    reasons_without_status = _row_reasons(
        items=items,
        forecast_dispersion=forecast_dispersion,
        evidence_quality_difference=evidence_quality_difference,
        source_family_overlap_ratio=overlap_ratio,
        recency_mismatch_seconds=recency_mismatch,
        max_resolution_ambiguity_score=max_resolution_ambiguity,
        cost_adjusted_edge_margin=edge_margin,
        config=config,
    )
    gate_status = _gate_status(reasons_without_status)
    reason_codes = reasons_without_status + (_STATUS_REASON[gate_status],)
    return StrategyRecommendationTeamConflictResolutionGateV2Row(
        candidate_id=chosen.candidate_id,
        market_slug=chosen.market_slug,
        chosen_recommendation_id=chosen.recommendation_id,
        chosen_team_id=chosen.team_id,
        chosen_side=chosen.recommendation_side,
        team_count=_count(len({item.team_id for item in items})),
        side_count=_count(len({item.recommendation_side for item in items})),
        source_family_count=_count(source_family_count),
        forecast_dispersion=forecast_dispersion,
        evidence_quality_difference=evidence_quality_difference,
        source_family_overlap_ratio=overlap_ratio,
        recency_mismatch_seconds=recency_mismatch,
        max_resolution_ambiguity_score=max_resolution_ambiguity,
        best_cost_adjusted_edge=chosen.cost_adjusted_edge,
        cost_adjusted_edge_margin=edge_margin,
        gate_status=gate_status,
        reason_codes=reason_codes,
    )


def _row_reasons(
    *,
    items: tuple[StrategyRecommendationTeamConflictResolutionGateV2Input, ...],
    forecast_dispersion: Decimal,
    evidence_quality_difference: Decimal,
    source_family_overlap_ratio: Decimal,
    recency_mismatch_seconds: Decimal,
    max_resolution_ambiguity_score: Decimal,
    cost_adjusted_edge_margin: Decimal,
    config: StrategyRecommendationTeamConflictResolutionGateV2Config,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if len({item.recommendation_side for item in items}) > 1:
        reasons.append("side_disagreement")
    if forecast_dispersion > config.max_forecast_dispersion:
        reasons.append("forecast_dispersion_high")
    if evidence_quality_difference > config.max_evidence_quality_difference:
        reasons.append("evidence_quality_difference_high")
    if source_family_overlap_ratio > config.max_source_family_overlap_ratio:
        reasons.append("source_family_overlap_high")
    if recency_mismatch_seconds > config.max_recency_mismatch_seconds:
        reasons.append("recency_mismatch_high")
    if max_resolution_ambiguity_score > config.max_resolution_ambiguity_score:
        reasons.append("resolution_ambiguity_high")
    if cost_adjusted_edge_margin < _ZERO:
        reasons.append("cost_adjusted_edge_margin_low")
    if not reasons:
        return ()
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _gate_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCKING_REASONS for reason_code in reason_codes):
        return "blocked"
    if reason_codes:
        return "watch"
    return "qualified"


def _choose_recommendation(
    items: tuple[StrategyRecommendationTeamConflictResolutionGateV2Input, ...],
    generated_at: datetime,
) -> StrategyRecommendationTeamConflictResolutionGateV2Input:
    return tuple(sorted(items, key=lambda item: _recommendation_key(item, generated_at)))[0]


def _recommendation_key(
    item: StrategyRecommendationTeamConflictResolutionGateV2Input,
    generated_at: datetime,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        -item.cost_adjusted_edge,
        -item.evidence_quality_score,
        -item.forecast_probability,
        _age_seconds(generated_at, item.evidence_observed_at),
        item.team_id,
        item.recommendation_id,
    )


def _candidate_groups(
    items: tuple[StrategyRecommendationTeamConflictResolutionGateV2Input, ...],
) -> tuple[tuple[StrategyRecommendationTeamConflictResolutionGateV2Input, ...], ...]:
    grouped: dict[str, list[StrategyRecommendationTeamConflictResolutionGateV2Input]] = {}
    for item in items:
        if item.candidate_id not in grouped:
            grouped[item.candidate_id] = []
        grouped[item.candidate_id].append(item)
    groups = []
    for candidate_id in sorted(grouped):
        groups.append(
            tuple(
                sorted(
                    grouped[candidate_id],
                    key=lambda item: (item.recommendation_id, item.team_id),
                ),
            ),
        )
    return tuple(groups)


def _normalize_inputs(
    recommendations: object,
) -> tuple[StrategyRecommendationTeamConflictResolutionGateV2Input, ...]:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable of input rows")
    try:
        items = tuple(recommendations)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable of input rows") from exc
    seen_ids: set[str] = set()
    for item in items:
        if type(item) is not StrategyRecommendationTeamConflictResolutionGateV2Input:
            raise ValueError(
                "recommendations must contain "
                "StrategyRecommendationTeamConflictResolutionGateV2Input values",
            )
        _require_flags("input", item)
        _reject_unsafe_public("input", item)
        if item.recommendation_id in seen_ids:
            raise ValueError("recommendations must not contain duplicate recommendation_id values")
        seen_ids.add(item.recommendation_id)
    return tuple(sorted(items, key=lambda item: (item.candidate_id, item.recommendation_id)))


def _normalize_rows(rows: object) -> tuple[StrategyRecommendationTeamConflictResolutionGateV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of report rows")
    try:
        items = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable of report rows") from exc
    seen_candidates: set[str] = set()
    for item in items:
        if type(item) is not StrategyRecommendationTeamConflictResolutionGateV2Row:
            raise ValueError(
                "rows must contain StrategyRecommendationTeamConflictResolutionGateV2Row values",
            )
        _require_flags("row", item)
        _require_row_digest(item)
        if item.candidate_id in seen_candidates:
            raise ValueError("rows must not contain duplicate candidate_id values")
        seen_candidates.add(item.candidate_id)
    return tuple(sorted(items, key=_row_key))


def _row_key(row: StrategyRecommendationTeamConflictResolutionGateV2Row) -> tuple[int, Decimal, str]:
    return (
        _STATUS_RANK[row.gate_status],
        row.cost_adjusted_edge_margin,
        row.candidate_id,
    )


def _status_count(
    rows: tuple[StrategyRecommendationTeamConflictResolutionGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _report_status(rows: tuple[StrategyRecommendationTeamConflictResolutionGateV2Row, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.gate_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "qualified"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationTeamConflictResolutionGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in _REASON_CODES if reason_code in present)


def _check_row(row: StrategyRecommendationTeamConflictResolutionGateV2Row) -> None:
    status_reason = _STATUS_REASON[row.gate_status]
    if status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include gate_status reason")
    status_reason_count = sum(1 for reason_code in row.reason_codes if reason_code in _STATUS_REASON.values())
    if status_reason_count != 1:
        raise ValueError("reason_codes must include exactly one gate status reason")
    reasons_without_status = tuple(reason_code for reason_code in row.reason_codes if reason_code != status_reason)
    if row.gate_status != _gate_status(reasons_without_status):
        raise ValueError("gate_status must match reason_codes")
    if row.gate_status == "qualified" and row.reason_codes != (_STATUS_REASON["qualified"],):
        raise ValueError("qualified rows must have only the qualified reason")
    if row.source_family_count > row.team_count:
        raise ValueError("source_family_count must not exceed team_count")


def _check_report(report: StrategyRecommendationTeamConflictResolutionGateV2Report) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.qualified_count != _status_count(report.rows, "qualified"):
        raise ValueError("qualified_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.candidate_count != report.qualified_count + report.watch_count + report.blocked_count:
        raise ValueError("candidate_count must reconcile with status counts")
    if report.input_count < report.candidate_count:
        raise ValueError("input_count must be greater than or equal to candidate_count")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_key)):
        raise ValueError("rows must use stable sort")
    for row in report.rows:
        _require_row_digest(row)


def _require_row_digest(row: StrategyRecommendationTeamConflictResolutionGateV2Row) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest mismatch")


def _require_report_digest(report: StrategyRecommendationTeamConflictResolutionGateV2Report) -> None:
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest mismatch")


def _row_digest(row: StrategyRecommendationTeamConflictResolutionGateV2Row) -> str:
    value = asdict(row)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _report_digest(report: StrategyRecommendationTeamConflictResolutionGateV2Report) -> str:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _verify_report_payload(payload: dict[str, Any]) -> None:
    _require_exact_keys("payload", payload, _REPORT_KEYS)
    _require_payload_digest_matches(payload)
    report = StrategyRecommendationTeamConflictResolutionGateV2Report(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_text("config_version", payload["config_version"]),
        input_count=_payload_decimal("input_count", payload["input_count"]),
        candidate_count=_payload_decimal("candidate_count", payload["candidate_count"]),
        qualified_count=_payload_decimal("qualified_count", payload["qualified_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        blocked_count=_payload_decimal("blocked_count", payload["blocked_count"]),
        status=_payload_text("status", payload["status"]),
        reason_codes=_payload_text_tuple("reason_codes", payload["reason_codes"]),
        rows=_payload_rows(payload["rows"]),
        derived_validation_digest=_payload_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )
    if _json_ready(report) != payload:
        raise ValueError("report payload must match derived validation")


def _payload_rows(value: object) -> tuple[StrategyRecommendationTeamConflictResolutionGateV2Row, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    return tuple(_payload_row(item) for item in value)


def _payload_row(value: object) -> StrategyRecommendationTeamConflictResolutionGateV2Row:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_exact_keys("payload row", value, _ROW_KEYS)
    _require_payload_digest_matches(value)
    return StrategyRecommendationTeamConflictResolutionGateV2Row(
        candidate_id=_payload_text("candidate_id", value["candidate_id"]),
        market_slug=_payload_text("market_slug", value["market_slug"]),
        chosen_recommendation_id=_payload_text(
            "chosen_recommendation_id",
            value["chosen_recommendation_id"],
        ),
        chosen_team_id=_payload_text("chosen_team_id", value["chosen_team_id"]),
        chosen_side=_payload_text("chosen_side", value["chosen_side"]),
        team_count=_payload_decimal("team_count", value["team_count"]),
        side_count=_payload_decimal("side_count", value["side_count"]),
        source_family_count=_payload_decimal(
            "source_family_count",
            value["source_family_count"],
        ),
        forecast_dispersion=_payload_decimal(
            "forecast_dispersion",
            value["forecast_dispersion"],
        ),
        evidence_quality_difference=_payload_decimal(
            "evidence_quality_difference",
            value["evidence_quality_difference"],
        ),
        source_family_overlap_ratio=_payload_decimal(
            "source_family_overlap_ratio",
            value["source_family_overlap_ratio"],
        ),
        recency_mismatch_seconds=_payload_decimal(
            "recency_mismatch_seconds",
            value["recency_mismatch_seconds"],
        ),
        max_resolution_ambiguity_score=_payload_decimal(
            "max_resolution_ambiguity_score",
            value["max_resolution_ambiguity_score"],
        ),
        best_cost_adjusted_edge=_payload_decimal(
            "best_cost_adjusted_edge",
            value["best_cost_adjusted_edge"],
        ),
        cost_adjusted_edge_margin=_payload_decimal(
            "cost_adjusted_edge_margin",
            value["cost_adjusted_edge_margin"],
        ),
        gate_status=_payload_text("gate_status", value["gate_status"]),
        reason_codes=_payload_text_tuple("reason_codes", value["reason_codes"]),
        derived_validation_digest=_payload_digest(
            "derived_validation_digest",
            value["derived_validation_digest"],
        ),
        paper_only=_payload_flag("paper_only", value["paper_only"]),
        report_only=_payload_flag("report_only", value["report_only"]),
        readonly=_payload_flag("readonly", value["readonly"]),
    )


def _require_exact_keys(label: str, payload: dict[str, Any], expected: tuple[str, ...]) -> None:
    if set(payload) != set(expected):
        raise ValueError(f"{label} must contain exactly the expected public fields")


def _require_payload_digest_matches(payload: dict[str, Any]) -> None:
    supplied_digest = _payload_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _payload_datetime(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be an ISO datetime string")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string") from exc


def _payload_decimal(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc


def _payload_text(name: str, value: object) -> str:
    _require_text(name, value)
    return value


def _payload_text_tuple(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list")
    return tuple(_payload_text(name, item) for item in value)


def _payload_digest(name: str, value: object) -> str:
    _require_digest(name, value)
    return value


def _payload_flag(name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{name} must be True")
    return True


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        _json_ready(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric values must be Decimal strings")
    if isinstance(value, float):
        raise ValueError("JSON values must not be floats")
    if type(value) is str:
        _require_text("JSON string", value)
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_text("JSON object key", key)
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            StrategyRecommendationTeamConflictResolutionGateV2Config,
            StrategyRecommendationTeamConflictResolutionGateV2Input,
            StrategyRecommendationTeamConflictResolutionGateV2Row,
            StrategyRecommendationTeamConflictResolutionGateV2Report,
        ):
            raise ValueError(f"{label} must be a supported public dataclass")
        for field in fields(value):
            _reject_unsafe_public(f"{label}.{field.name}", getattr(value, field.name))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if type(value) is dict:
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
    if type(value) is dict:
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
        raise ValueError(f"{name} must be a canonical string")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{name} has unsafe public text")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}")


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an iterable of strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{name} must contain at least one value")
    if len(set(items)) != len(items):
        raise ValueError(f"{name} must not contain duplicate values")
    for item in items:
        _require_member(name, item, _REASON_CODES)
    if items != tuple(reason_code for reason_code in _REASON_CODES if reason_code in items):
        raise ValueError(f"{name} must be deterministic")
    return items


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_edge(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _NEGATIVE_ONE or normalized > _ONE:
        raise ValueError(f"{name} must be between -1.000000 and 1.000000")
    return normalized


def _normalize_seconds(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator <= 0:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return (Decimal(numerator) / Decimal(denominator)).quantize(
            _QUANT,
            rounding=ROUND_HALF_UP,
        )


def _ratio_difference(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _normalize_ratio("ratio_difference", max(values) - min(values))


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _age_seconds(generated_at: datetime, earlier_at: datetime) -> Decimal:
    delta = _as_utc("generated_at", generated_at) - _as_utc("earlier_at", earlier_at)
    with localcontext(_DECIMAL_CONTEXT):
        age_seconds = (
            Decimal(delta.days) * _SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND)
        )
    if age_seconds < _ZERO:
        raise ValueError("timestamp must not be in the future")
    return _normalize_seconds("age_seconds", age_seconds)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_TEAM_CONFLICT_RESOLUTION_GATE_V2_CONFIG_VERSION",
    "StrategyRecommendationTeamConflictResolutionGateV2Config",
    "StrategyRecommendationTeamConflictResolutionGateV2Input",
    "StrategyRecommendationTeamConflictResolutionGateV2Report",
    "StrategyRecommendationTeamConflictResolutionGateV2Row",
    "build_strategy_recommendation_team_conflict_resolution_gate_v2_report",
    "strategy_recommendation_team_conflict_resolution_gate_v2_payload",
)
