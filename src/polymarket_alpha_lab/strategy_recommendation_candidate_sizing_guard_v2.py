"""Paper-only candidate sizing guard for strategy recommendations."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_STRATEGY_RECOMMENDATION_CANDIDATE_SIZING_GUARD_V2_CONFIG_VERSION = (
    "strategy-recommendation-candidate-sizing-guard-v2"
)

_COUNT_QUANTUM = Decimal("1")
_VALUE_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")

_SIZING_STATUSES = frozenset(("pass", "watch", "blocked"))
_REPORT_REASON_CODE_ORDER = (
    "manual_review",
    "candidate_sizing_pass",
    "candidate_sizing_watch",
    "candidate_sizing_blocked",
    "market_depth_cap_limited",
    "category_budget_limited",
    "correlation_pressure_watch",
    "correlation_pressure_block",
    "confidence_below_ready",
    "confidence_below_watch",
    "cost_adjusted_edge_below_ready",
    "cost_adjusted_edge_below_watch",
    "max_loss_above_cap",
    "requested_notional_exceeds_allowed",
)


@dataclass(frozen=True)
class StrategyRecommendationCandidateSizingGuardV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_CANDIDATE_SIZING_GUARD_V2_CONFIG_VERSION
    )
    bankroll_notional: Decimal = Decimal("0.000000")
    bankroll_cap_share: Decimal = Decimal("0.000000")
    market_depth_cap_share: Decimal = Decimal("0.000000")
    category_budget_share: Decimal = Decimal("0.000000")
    correlation_budget_share: Decimal = Decimal("0.000000")
    correlation_pressure_watch_share: Decimal = Decimal("0.000000")
    correlation_pressure_block_share: Decimal = Decimal("0.000000")
    min_ready_confidence: Decimal = Decimal("0.000000")
    min_watch_confidence: Decimal = Decimal("0.000000")
    min_ready_cost_adjusted_edge: Decimal = Decimal("0.000000")
    min_watch_cost_adjusted_edge: Decimal = Decimal("0.000000")
    max_loss_share: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationCandidateSizingGuardV2Config:
            raise ValueError(
                "config must be StrategyRecommendationCandidateSizingGuardV2Config",
            )
        _require_text("config_version", self.config_version)
        object.__setattr__(
            self,
            "bankroll_notional",
            _positive_decimal("bankroll_notional", self.bankroll_notional),
        )
        for field_name in (
            "bankroll_cap_share",
            "market_depth_cap_share",
            "category_budget_share",
            "correlation_budget_share",
            "correlation_pressure_watch_share",
            "correlation_pressure_block_share",
            "min_ready_confidence",
            "min_watch_confidence",
            "max_loss_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_ready_cost_adjusted_edge",
            "min_watch_cost_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal(field_name, getattr(self, field_name)),
            )
        if self.bankroll_cap_share <= _ZERO:
            raise ValueError("bankroll_cap_share must be positive")
        if self.market_depth_cap_share <= _ZERO:
            raise ValueError("market_depth_cap_share must be positive")
        if self.category_budget_share <= _ZERO:
            raise ValueError("category_budget_share must be positive")
        if self.correlation_budget_share <= _ZERO:
            raise ValueError("correlation_budget_share must be positive")
        if self.correlation_pressure_block_share < self.correlation_pressure_watch_share:
            raise ValueError(
                "correlation_pressure_block_share must be at least "
                "correlation_pressure_watch_share",
            )
        if self.min_watch_confidence > self.min_ready_confidence:
            raise ValueError("min_watch_confidence must not exceed min_ready_confidence")
        if self.min_watch_cost_adjusted_edge > self.min_ready_cost_adjusted_edge:
            raise ValueError(
                "min_watch_cost_adjusted_edge must not exceed "
                "min_ready_cost_adjusted_edge",
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationCandidateSizingGuardV2ExposureSnapshot:
    category: str
    correlation_key: str
    current_category_exposure: Decimal
    current_correlation_exposure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationCandidateSizingGuardV2ExposureSnapshot:
            raise ValueError(
                "exposure snapshot must be "
                "StrategyRecommendationCandidateSizingGuardV2ExposureSnapshot",
            )
        _require_text("category", self.category)
        _require_text("correlation_key", self.correlation_key)
        for field_name in (
            "current_category_exposure",
            "current_correlation_exposure",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("exposure snapshot", self)


@dataclass(frozen=True)
class StrategyRecommendationCandidateSizingGuardV2Candidate:
    candidate_id: str
    recommendation_id: str
    market_slug: str
    category: str
    correlation_key: str
    requested_notional: Decimal
    market_depth_notional: Decimal
    confidence: Decimal
    gross_edge: Decimal
    total_cost: Decimal
    max_loss_notional: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationCandidateSizingGuardV2Candidate:
            raise ValueError(
                "candidate must be StrategyRecommendationCandidateSizingGuardV2Candidate",
            )
        for field_name in (
            "candidate_id",
            "recommendation_id",
            "market_slug",
            "category",
            "correlation_key",
        ):
            _require_text(field_name, getattr(self, field_name))
        for field_name in (
            "requested_notional",
            "market_depth_notional",
            "total_cost",
            "max_loss_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence",
            _unit_decimal("confidence", self.confidence),
        )
        object.__setattr__(self, "gross_edge", _decimal("gross_edge", self.gross_edge))
        object.__setattr__(
            self,
            "reason_codes",
            _reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("candidate", self)


@dataclass(frozen=True)
class StrategyRecommendationCandidateSizingGuardV2Row:
    rank: Decimal
    candidate_id: str
    recommendation_id: str
    market_slug: str
    category: str
    correlation_key: str
    requested_notional: Decimal
    market_depth_notional: Decimal
    confidence: Decimal
    gross_edge: Decimal
    total_cost: Decimal
    cost_adjusted_edge: Decimal
    max_loss_notional: Decimal
    bankroll_cap_notional: Decimal
    market_depth_cap_notional: Decimal
    category_budget_notional: Decimal
    category_remaining_notional: Decimal
    correlation_budget_notional: Decimal
    post_trade_correlation_exposure: Decimal
    correlation_pressure: Decimal
    max_loss_cap_notional: Decimal
    allowed_candidate_notional: Decimal
    sizing_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationCandidateSizingGuardV2Row:
            raise ValueError("row must be StrategyRecommendationCandidateSizingGuardV2Row")
        object.__setattr__(self, "rank", _count_decimal("rank", self.rank))
        if self.rank <= _ZERO:
            raise ValueError("rank must be positive")
        for field_name in (
            "candidate_id",
            "recommendation_id",
            "market_slug",
            "category",
            "correlation_key",
        ):
            _require_text(field_name, getattr(self, field_name))
        for field_name in (
            "requested_notional",
            "market_depth_notional",
            "confidence",
            "gross_edge",
            "total_cost",
            "cost_adjusted_edge",
            "max_loss_notional",
            "bankroll_cap_notional",
            "market_depth_cap_notional",
            "category_budget_notional",
            "category_remaining_notional",
            "correlation_budget_notional",
            "post_trade_correlation_exposure",
            "correlation_pressure",
            "max_loss_cap_notional",
            "allowed_candidate_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal(field_name, getattr(self, field_name)),
            )
        if self.confidence < _ZERO or self.confidence > _ONE:
            raise ValueError("confidence must be between zero and one")
        if self.sizing_status not in _SIZING_STATUSES:
            raise ValueError("sizing_status must be pass, watch, or blocked")
        object.__setattr__(
            self,
            "reason_codes",
            _reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("row", self)
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        expected_digest = _digest_from_values(_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match row payload")


@dataclass(frozen=True)
class StrategyRecommendationCandidateSizingGuardV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    digest_status: str
    total_requested_notional: Decimal
    total_allowed_notional: Decimal
    min_allowed_notional: Decimal
    max_correlation_pressure: Decimal
    min_confidence: Decimal
    min_cost_adjusted_edge: Decimal
    max_loss_notional: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyRecommendationCandidateSizingGuardV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationCandidateSizingGuardV2Report:
            raise ValueError("report must be StrategyRecommendationCandidateSizingGuardV2Report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_requested_notional",
            "total_allowed_notional",
            "min_allowed_notional",
            "max_correlation_pressure",
            "min_confidence",
            "min_cost_adjusted_edge",
            "max_loss_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal(field_name, getattr(self, field_name)),
            )
        if self.digest_status not in _SIZING_STATUSES:
            raise ValueError("digest_status must be pass, watch, or blocked")
        object.__setattr__(
            self,
            "reason_codes",
            _reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_flags("report", self)
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        expected_digest = _digest_from_values(_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_consistency(self)


def build_strategy_recommendation_candidate_sizing_guard_v2_report(
    candidates: Iterable[StrategyRecommendationCandidateSizingGuardV2Candidate],
    *,
    exposure_snapshots: Iterable[
        StrategyRecommendationCandidateSizingGuardV2ExposureSnapshot
    ],
    config: StrategyRecommendationCandidateSizingGuardV2Config,
    generated_at: datetime,
) -> StrategyRecommendationCandidateSizingGuardV2Report:
    if type(config) is not StrategyRecommendationCandidateSizingGuardV2Config:
        raise ValueError(
            "config must be StrategyRecommendationCandidateSizingGuardV2Config",
        )
    _require_flags("config", config)
    normalized_generated_at = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    snapshot_by_key = _snapshot_mapping(exposure_snapshots)

    unranked_values: list[dict[str, object]] = []
    for candidate in normalized_candidates:
        key = (candidate.category, candidate.correlation_key)
        if key not in snapshot_by_key:
            raise ValueError("exposure_snapshots must cover every candidate")
        unranked_values.append(
            _row_values_for_candidate(
                candidate,
                snapshot_by_key[key],
                config,
            ),
        )

    rows = _ranked_rows(tuple(unranked_values))
    report_values: dict[str, object] = {
        "generated_at": normalized_generated_at,
        "config_version": config.config_version,
        "candidate_count": _count_from_int(len(rows)),
        "pass_count": _count_from_int(_status_count(rows, "pass")),
        "watch_count": _count_from_int(_status_count(rows, "watch")),
        "blocked_count": _count_from_int(_status_count(rows, "blocked")),
        "digest_status": _report_status(rows),
        "total_requested_notional": _sum_values(
            row.requested_notional for row in rows
        ),
        "total_allowed_notional": _sum_values(
            row.allowed_candidate_notional for row in rows
        ),
        "min_allowed_notional": _min_value(
            tuple(row.allowed_candidate_notional for row in rows),
        ),
        "max_correlation_pressure": _max_value(
            tuple(row.correlation_pressure for row in rows),
        ),
        "min_confidence": _min_value(tuple(row.confidence for row in rows)),
        "min_cost_adjusted_edge": _min_value(
            tuple(row.cost_adjusted_edge for row in rows),
        ),
        "max_loss_notional": _max_value(tuple(row.max_loss_notional for row in rows)),
        "reason_codes": _report_reason_codes(rows, config),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyRecommendationCandidateSizingGuardV2Report(
        **report_values,
        derived_validation_digest=_digest_from_values(report_values),
    )


def strategy_recommendation_candidate_sizing_guard_v2_payload(
    report: StrategyRecommendationCandidateSizingGuardV2Report,
) -> dict[str, object]:
    if type(report) is not StrategyRecommendationCandidateSizingGuardV2Report:
        raise ValueError("report must be StrategyRecommendationCandidateSizingGuardV2Report")
    _require_flags("report", report)
    expected_digest = _digest_from_values(_values_without_digest(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    return payload


def _row_values_for_candidate(
    candidate: StrategyRecommendationCandidateSizingGuardV2Candidate,
    snapshot: StrategyRecommendationCandidateSizingGuardV2ExposureSnapshot,
    config: StrategyRecommendationCandidateSizingGuardV2Config,
) -> dict[str, object]:
    bankroll_cap_notional = _notional(
        "bankroll_cap_notional",
        config.bankroll_notional * config.bankroll_cap_share,
    )
    market_depth_cap_notional = _notional(
        "market_depth_cap_notional",
        candidate.market_depth_notional * config.market_depth_cap_share,
    )
    category_budget_notional = _notional(
        "category_budget_notional",
        config.bankroll_notional * config.category_budget_share,
    )
    category_remaining_notional = _notional(
        "category_remaining_notional",
        max(_ZERO, category_budget_notional - snapshot.current_category_exposure),
    )
    correlation_budget_notional = _notional(
        "correlation_budget_notional",
        config.bankroll_notional * config.correlation_budget_share,
    )
    post_trade_correlation_exposure = _notional(
        "post_trade_correlation_exposure",
        snapshot.current_correlation_exposure + candidate.requested_notional,
    )
    correlation_pressure = _ratio(
        "correlation_pressure",
        post_trade_correlation_exposure,
        correlation_budget_notional,
    )
    max_loss_cap_notional = _notional(
        "max_loss_cap_notional",
        config.bankroll_notional * config.max_loss_share,
    )
    cost_adjusted_edge = _decimal(
        "cost_adjusted_edge",
        candidate.gross_edge - candidate.total_cost,
    )
    allowed_candidate_notional = _notional(
        "allowed_candidate_notional",
        min(
            candidate.requested_notional,
            bankroll_cap_notional,
            market_depth_cap_notional,
            category_remaining_notional,
        ),
    )
    sizing_status, reason_codes = _candidate_status_and_reasons(
        candidate=candidate,
        config=config,
        market_depth_cap_notional=market_depth_cap_notional,
        category_remaining_notional=category_remaining_notional,
        correlation_pressure=correlation_pressure,
        cost_adjusted_edge=cost_adjusted_edge,
        max_loss_cap_notional=max_loss_cap_notional,
        allowed_candidate_notional=allowed_candidate_notional,
    )
    return {
        "rank": _count_from_int(1),
        "candidate_id": candidate.candidate_id,
        "recommendation_id": candidate.recommendation_id,
        "market_slug": candidate.market_slug,
        "category": candidate.category,
        "correlation_key": candidate.correlation_key,
        "requested_notional": candidate.requested_notional,
        "market_depth_notional": candidate.market_depth_notional,
        "confidence": candidate.confidence,
        "gross_edge": candidate.gross_edge,
        "total_cost": candidate.total_cost,
        "cost_adjusted_edge": cost_adjusted_edge,
        "max_loss_notional": candidate.max_loss_notional,
        "bankroll_cap_notional": bankroll_cap_notional,
        "market_depth_cap_notional": market_depth_cap_notional,
        "category_budget_notional": category_budget_notional,
        "category_remaining_notional": category_remaining_notional,
        "correlation_budget_notional": correlation_budget_notional,
        "post_trade_correlation_exposure": post_trade_correlation_exposure,
        "correlation_pressure": correlation_pressure,
        "max_loss_cap_notional": max_loss_cap_notional,
        "allowed_candidate_notional": allowed_candidate_notional,
        "sizing_status": sizing_status,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _candidate_status_and_reasons(
    *,
    candidate: StrategyRecommendationCandidateSizingGuardV2Candidate,
    config: StrategyRecommendationCandidateSizingGuardV2Config,
    market_depth_cap_notional: Decimal,
    category_remaining_notional: Decimal,
    correlation_pressure: Decimal,
    cost_adjusted_edge: Decimal,
    max_loss_cap_notional: Decimal,
    allowed_candidate_notional: Decimal,
) -> tuple[str, tuple[str, ...]]:
    status = "pass"
    detail_reasons: list[str] = []

    if market_depth_cap_notional < candidate.requested_notional:
        detail_reasons.append("market_depth_cap_limited")
    if category_remaining_notional < candidate.requested_notional:
        detail_reasons.append("category_budget_limited")

    if correlation_pressure >= config.correlation_pressure_block_share:
        status = "blocked"
        detail_reasons.append("correlation_pressure_block")
    elif correlation_pressure >= config.correlation_pressure_watch_share:
        status = _more_severe_status(status, "watch")
        detail_reasons.append("correlation_pressure_watch")

    if candidate.confidence < config.min_watch_confidence:
        status = "blocked"
        detail_reasons.append("confidence_below_watch")
    elif candidate.confidence < config.min_ready_confidence:
        status = _more_severe_status(status, "watch")
        detail_reasons.append("confidence_below_ready")

    if cost_adjusted_edge < config.min_watch_cost_adjusted_edge:
        status = "blocked"
        detail_reasons.append("cost_adjusted_edge_below_watch")
    elif cost_adjusted_edge < config.min_ready_cost_adjusted_edge:
        status = _more_severe_status(status, "watch")
        detail_reasons.append("cost_adjusted_edge_below_ready")

    if candidate.max_loss_notional > max_loss_cap_notional:
        status = "blocked"
        detail_reasons.append("max_loss_above_cap")
    if candidate.requested_notional > allowed_candidate_notional:
        status = "blocked"
        detail_reasons.append("requested_notional_exceeds_allowed")

    reason_codes = list(candidate.reason_codes)
    reason_codes.append(f"candidate_sizing_{status}")
    reason_codes.extend(detail_reasons)
    return status, _deduped_reason_codes(tuple(reason_codes))


def _ranked_rows(
    row_values: tuple[dict[str, object], ...],
) -> tuple[StrategyRecommendationCandidateSizingGuardV2Row, ...]:
    ordered = sorted(row_values, key=_row_value_sort_key)
    rows: list[StrategyRecommendationCandidateSizingGuardV2Row] = []
    for rank, values in enumerate(ordered, start=1):
        ranked_values = dict(values)
        ranked_values["rank"] = _count_from_int(rank)
        rows.append(
            StrategyRecommendationCandidateSizingGuardV2Row(
                **ranked_values,
                derived_validation_digest=_digest_from_values(ranked_values),
            ),
        )
    return tuple(rows)


def _row_value_sort_key(values: Mapping[str, object]) -> tuple[object, ...]:
    sizing_status = values["sizing_status"]
    if type(sizing_status) is not str:
        raise ValueError("sizing_status must be text")
    correlation_pressure = values["correlation_pressure"]
    requested_notional = values["requested_notional"]
    candidate_id = values["candidate_id"]
    recommendation_id = values["recommendation_id"]
    market_slug = values["market_slug"]
    if type(correlation_pressure) is not Decimal:
        raise ValueError("correlation_pressure must be Decimal")
    if type(requested_notional) is not Decimal:
        raise ValueError("requested_notional must be Decimal")
    for field_name, value in (
        ("candidate_id", candidate_id),
        ("recommendation_id", recommendation_id),
        ("market_slug", market_slug),
    ):
        if type(value) is not str:
            raise ValueError(f"{field_name} must be text")
    return (
        _status_sort_index(sizing_status),
        -correlation_pressure,
        -requested_notional,
        candidate_id,
        recommendation_id,
        market_slug,
    )


def _normalize_candidates(
    candidates: Iterable[StrategyRecommendationCandidateSizingGuardV2Candidate],
) -> tuple[StrategyRecommendationCandidateSizingGuardV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Iterable):
        raise ValueError("candidates must be iterable")
    normalized = tuple(candidates)
    for candidate in normalized:
        if type(candidate) is not StrategyRecommendationCandidateSizingGuardV2Candidate:
            raise ValueError(
                "candidates must contain "
                "StrategyRecommendationCandidateSizingGuardV2Candidate",
            )
        _require_flags("candidate", candidate)
    return normalized


def _snapshot_mapping(
    exposure_snapshots: Iterable[
        StrategyRecommendationCandidateSizingGuardV2ExposureSnapshot
    ],
) -> dict[tuple[str, str], StrategyRecommendationCandidateSizingGuardV2ExposureSnapshot]:
    if isinstance(exposure_snapshots, (str, bytes)) or not isinstance(
        exposure_snapshots,
        Iterable,
    ):
        raise ValueError("exposure_snapshots must be iterable")
    snapshot_by_key: dict[
        tuple[str, str],
        StrategyRecommendationCandidateSizingGuardV2ExposureSnapshot,
    ] = {}
    for snapshot in tuple(exposure_snapshots):
        if type(snapshot) is not StrategyRecommendationCandidateSizingGuardV2ExposureSnapshot:
            raise ValueError(
                "exposure_snapshots must contain "
                "StrategyRecommendationCandidateSizingGuardV2ExposureSnapshot",
            )
        _require_flags("exposure snapshot", snapshot)
        key = (snapshot.category, snapshot.correlation_key)
        if key in snapshot_by_key:
            raise ValueError("exposure_snapshots must not contain duplicate keys")
        snapshot_by_key[key] = snapshot
    return snapshot_by_key


def _normalize_rows(
    rows: tuple[StrategyRecommendationCandidateSizingGuardV2Row, ...],
) -> tuple[StrategyRecommendationCandidateSizingGuardV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be tuple")
    for row in rows:
        if type(row) is not StrategyRecommendationCandidateSizingGuardV2Row:
            raise ValueError("rows must contain StrategyRecommendationCandidateSizingGuardV2Row")
        _require_flags("row", row)
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be deterministically sorted")
    expected_ranks = tuple(_count_from_int(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must use sequential ranks")
    return rows


def _row_sort_key(row: StrategyRecommendationCandidateSizingGuardV2Row) -> tuple[object, ...]:
    return (
        _status_sort_index(row.sizing_status),
        -row.correlation_pressure,
        -row.requested_notional,
        row.candidate_id,
        row.recommendation_id,
        row.market_slug,
    )


def _status_sort_index(status: str) -> Decimal:
    if status == "blocked":
        return Decimal("0")
    if status == "watch":
        return Decimal("1")
    if status == "pass":
        return Decimal("2")
    raise ValueError("status must be pass, watch, or blocked")


def _more_severe_status(current_status: str, candidate_status: str) -> str:
    if _status_sort_index(candidate_status) < _status_sort_index(current_status):
        return candidate_status
    return current_status


def _status_count(
    rows: tuple[StrategyRecommendationCandidateSizingGuardV2Row, ...],
    sizing_status: str,
) -> int:
    return sum(1 for row in rows if row.sizing_status == sizing_status)


def _report_status(
    rows: tuple[StrategyRecommendationCandidateSizingGuardV2Row, ...],
) -> str:
    if any(row.sizing_status == "blocked" for row in rows):
        return "blocked"
    if any(row.sizing_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationCandidateSizingGuardV2Row, ...],
    config: StrategyRecommendationCandidateSizingGuardV2Config,
) -> tuple[str, ...]:
    reason_set: set[str] = set()
    for row in rows:
        reason_set.update(row.reason_codes)
    if any(row.confidence < config.min_ready_confidence for row in rows):
        reason_set.add("confidence_below_ready")
    if any(row.confidence < config.min_watch_confidence for row in rows):
        reason_set.add("confidence_below_watch")
    if any(row.cost_adjusted_edge < config.min_ready_cost_adjusted_edge for row in rows):
        reason_set.add("cost_adjusted_edge_below_ready")
    if any(row.cost_adjusted_edge < config.min_watch_cost_adjusted_edge for row in rows):
        reason_set.add("cost_adjusted_edge_below_watch")

    ordered = [reason for reason in _REPORT_REASON_CODE_ORDER if reason in reason_set]
    extras = sorted(reason for reason in reason_set if reason not in _REPORT_REASON_CODE_ORDER)
    return _reason_codes("reason_codes", tuple(ordered + extras))


def _validate_report_consistency(
    report: StrategyRecommendationCandidateSizingGuardV2Report,
) -> None:
    rows = report.rows
    if report.candidate_count != _count_from_int(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count_from_int(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_from_int(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count_from_int(_status_count(rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status must match rows")
    if report.total_requested_notional != _sum_values(
        row.requested_notional for row in rows
    ):
        raise ValueError("total_requested_notional must match rows")
    if report.total_allowed_notional != _sum_values(
        row.allowed_candidate_notional for row in rows
    ):
        raise ValueError("total_allowed_notional must match rows")
    if report.min_allowed_notional != _min_value(
        tuple(row.allowed_candidate_notional for row in rows),
    ):
        raise ValueError("min_allowed_notional must match rows")
    if report.max_correlation_pressure != _max_value(
        tuple(row.correlation_pressure for row in rows),
    ):
        raise ValueError("max_correlation_pressure must match rows")
    if report.min_confidence != _min_value(tuple(row.confidence for row in rows)):
        raise ValueError("min_confidence must match rows")
    if report.min_cost_adjusted_edge != _min_value(
        tuple(row.cost_adjusted_edge for row in rows),
    ):
        raise ValueError("min_cost_adjusted_edge must match rows")
    if report.max_loss_notional != _max_value(tuple(row.max_loss_notional for row in rows)):
        raise ValueError("max_loss_notional must match rows")


def _sum_values(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _decimal("sum", total)


def _min_value(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _decimal("minimum", min(values))


def _max_value(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _decimal("maximum", max(values))


def _ratio(name: str, numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError(f"{name} denominator must be positive")
    return _decimal(name, numerator / denominator)


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _unit_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _notional(name: str, value: Decimal) -> Decimal:
    return _nonnegative_decimal(name, value)


def _decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(_VALUE_QUANTUM)


def _count_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be whole Decimal")
    return value.quantize(_COUNT_QUANTUM)


def _count_from_int(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _require_text(name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be text")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be canonical text")


def _reason_codes(name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be tuple")
    return _deduped_reason_codes(value)


def _deduped_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain text")
        if not reason_code or reason_code.strip() != reason_code:
            raise ValueError("reason_codes must contain canonical text")
        if reason_code.lower() != reason_code:
            raise ValueError("reason_codes must contain lowercase values")
        if reason_code in seen:
            continue
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_sha256_digest(name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be text")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{name} must be lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be lowercase sha256 digest") from exc


def _values_without_digest(value: object) -> dict[str, object]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("value must be a dataclass")
    return {
        field.name: getattr(value, field.name)
        for field in fields(value)
        if field.name != "derived_validation_digest"
    }


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            payload[key] = _json_ready(item)
        return payload
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_CANDIDATE_SIZING_GUARD_V2_CONFIG_VERSION",
    "StrategyRecommendationCandidateSizingGuardV2Candidate",
    "StrategyRecommendationCandidateSizingGuardV2Config",
    "StrategyRecommendationCandidateSizingGuardV2ExposureSnapshot",
    "StrategyRecommendationCandidateSizingGuardV2Report",
    "StrategyRecommendationCandidateSizingGuardV2Row",
    "build_strategy_recommendation_candidate_sizing_guard_v2_report",
    "strategy_recommendation_candidate_sizing_guard_v2_payload",
)
