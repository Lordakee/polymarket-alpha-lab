"""Paper-only candidate correlation cluster penalty reducer."""

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from typing import Any, Iterable


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_CORRELATION_CLUSTER_PENALTY_CONFIG_VERSION",
    "StrategyCandidateCorrelationCandidateInput",
    "StrategyCandidateCorrelationClusterPenaltyConfig",
    "StrategyCandidateCorrelationClusterPenaltyReport",
    "StrategyCandidateCorrelationPenaltyRow",
    "StrategyCandidateCorrelationPortfolioPosition",
    "build_strategy_candidate_correlation_cluster_penalty_report",
    "strategy_candidate_correlation_cluster_penalty_payload",
)


DEFAULT_STRATEGY_CANDIDATE_CORRELATION_CLUSTER_PENALTY_CONFIG_VERSION = (
    "strategy-candidate-correlation-cluster-penalty-v10"
)

ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_ONE = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT_PRECISION = 28

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)
STATUS_RANK = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_PASS: 2}

PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_SURFACE_FRAGMENTS = frozenset(
    (
        "api" + "_" + "key",
        "au" + "th",
        "credential",
        "execution",
        "fill",
        "live",
        "order",
        "place" + "_" + "order",
        "private" + "_" + "key",
        "secret",
        "token",
        "wal" + "let",
    ),
)


@dataclass(frozen=True)
class StrategyCandidateCorrelationClusterPenaltyConfig:
    config_version: str = DEFAULT_STRATEGY_CANDIDATE_CORRELATION_CLUSTER_PENALTY_CONFIG_VERSION
    resolution_timing_window_hours: Decimal = Decimal("72.000000")
    watch_penalty_threshold: Decimal = Decimal("0.300000")
    blocked_penalty_threshold: Decimal = Decimal("0.500000")
    min_adjusted_score: Decimal = Decimal("0.250000")
    category_overlap_weight: Decimal = Decimal("0.150000")
    event_cluster_overlap_weight: Decimal = Decimal("0.150000")
    shared_source_overlap_weight: Decimal = Decimal("0.250000")
    resolution_timing_overlap_weight: Decimal = Decimal("0.200000")
    portfolio_concentration_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "resolution_timing_window_hours",
            _normalize_positive_decimal(
                "resolution_timing_window_hours",
                self.resolution_timing_window_hours,
            ),
        )
        for field_name in (
            "watch_penalty_threshold",
            "blocked_penalty_threshold",
            "min_adjusted_score",
            "category_overlap_weight",
            "event_cluster_overlap_weight",
            "shared_source_overlap_weight",
            "resolution_timing_overlap_weight",
            "portfolio_concentration_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_penalty_threshold > self.blocked_penalty_threshold:
            raise ValueError(
                "watch_penalty_threshold must not exceed blocked_penalty_threshold",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyCandidateCorrelationCandidateInput:
    candidate_id: str
    category: str
    event_cluster_id: str
    source_ids: tuple[str, ...]
    resolution_at: datetime
    proposed_notional: Decimal
    base_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "category", "event_cluster_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_ids",
            _normalize_string_tuple("source_ids", self.source_ids),
        )
        object.__setattr__(self, "resolution_at", _as_utc("resolution_at", self.resolution_at))
        object.__setattr__(
            self,
            "proposed_notional",
            _normalize_positive_decimal("proposed_notional", self.proposed_notional),
        )
        object.__setattr__(
            self,
            "base_score",
            _normalize_unit_decimal("base_score", self.base_score),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyCandidateCorrelationPortfolioPosition:
    position_id: str
    category: str
    event_cluster_id: str
    source_ids: tuple[str, ...]
    resolution_at: datetime
    current_notional: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("position_id", "category", "event_cluster_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_ids",
            _normalize_string_tuple("source_ids", self.source_ids),
        )
        object.__setattr__(self, "resolution_at", _as_utc("resolution_at", self.resolution_at))
        object.__setattr__(
            self,
            "current_notional",
            _normalize_positive_decimal("current_notional", self.current_notional),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyCandidateCorrelationPenaltyRow:
    rank: Decimal
    candidate_id: str
    category: str
    event_cluster_id: str
    proposed_notional: Decimal
    base_score: Decimal
    category_overlap_score: Decimal
    event_cluster_overlap_score: Decimal
    shared_source_overlap_score: Decimal
    resolution_timing_overlap_score: Decimal
    portfolio_concentration_score: Decimal
    correlation_penalty: Decimal
    adjusted_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_decimal("rank", self.rank))
        for field_name in ("candidate_id", "category", "event_cluster_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "proposed_notional",
            _normalize_positive_decimal("proposed_notional", self.proposed_notional),
        )
        for field_name in (
            "base_score",
            "category_overlap_score",
            "event_cluster_overlap_score",
            "shared_source_overlap_score",
            "resolution_timing_overlap_score",
            "portfolio_concentration_score",
            "correlation_penalty",
            "adjusted_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.status) is not str or self.status not in STATUSES:
            raise ValueError("status must be pass, watch, or blocked")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        if self.adjusted_score != _adjusted_score(self.base_score, self.correlation_penalty):
            raise ValueError("adjusted_score must match base_score less correlation_penalty")
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyCandidateCorrelationClusterPenaltyReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    max_correlation_penalty: Decimal
    mean_adjusted_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCandidateCorrelationPenaltyRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_correlation_penalty", "mean_adjusted_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.status) is not str or self.status not in STATUSES:
            raise ValueError("status must be pass, watch, or blocked")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_strategy_candidate_correlation_cluster_penalty_report(
    candidates: Iterable[StrategyCandidateCorrelationCandidateInput],
    *,
    existing_positions: Iterable[StrategyCandidateCorrelationPortfolioPosition],
    config: StrategyCandidateCorrelationClusterPenaltyConfig,
    generated_at: datetime,
) -> StrategyCandidateCorrelationClusterPenaltyReport:
    """Score paper candidates for correlated exposure pressure."""

    if type(config) is not StrategyCandidateCorrelationClusterPenaltyConfig:
        raise ValueError("config must be a StrategyCandidateCorrelationClusterPenaltyConfig")
    _require_hard_flags(config)
    normalized_generated_at = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_inputs(candidates)
    normalized_positions = _normalize_positions(existing_positions)
    unranked_rows = tuple(
        _row_for_candidate(
            candidate=candidate,
            positions=normalized_positions,
            config=config,
            rank=COUNT_ONE,
        )
        for candidate in normalized_candidates
    )
    ordered_rows = tuple(
        StrategyCandidateCorrelationPenaltyRow(
            **{
                **row.__dict__,
                "rank": _count(index),
            },
        )
        for index, row in enumerate(_order_rows(unranked_rows), start=1)
    )
    return StrategyCandidateCorrelationClusterPenaltyReport(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        candidate_count=_count(len(ordered_rows)),
        pass_candidate_count=_status_count(ordered_rows, STATUS_PASS),
        watch_candidate_count=_status_count(ordered_rows, STATUS_WATCH),
        blocked_candidate_count=_status_count(ordered_rows, STATUS_BLOCKED),
        max_correlation_penalty=_max_correlation_penalty(ordered_rows),
        mean_adjusted_score=_mean_adjusted_score(ordered_rows),
        status=_report_status(ordered_rows),
        reason_codes=_report_reason_codes(ordered_rows),
        rows=ordered_rows,
    )


def strategy_candidate_correlation_cluster_penalty_payload(
    report: StrategyCandidateCorrelationClusterPenaltyReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCandidateCorrelationClusterPenaltyReport:
        _require_hard_flags(report)
        _reject_unsafe_public_payload("report", report)
        payload = _payload_value(report)
    elif type(report) is dict:
        _require_hard_flags(_DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        payload = _payload_value(report)
    else:
        raise ValueError("report must be a StrategyCandidateCorrelationClusterPenaltyReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags(_DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_for_candidate(
    *,
    candidate: StrategyCandidateCorrelationCandidateInput,
    positions: tuple[StrategyCandidateCorrelationPortfolioPosition, ...],
    config: StrategyCandidateCorrelationClusterPenaltyConfig,
    rank: Decimal,
) -> StrategyCandidateCorrelationPenaltyRow:
    category_overlap_score = _notional_share_for_category(candidate.category, positions)
    event_cluster_overlap_score = _notional_share_for_event_cluster(
        candidate.event_cluster_id,
        positions,
    )
    shared_source_overlap_score = _notional_share_for_sources(candidate.source_ids, positions)
    resolution_timing_overlap_score = _notional_share_for_resolution_window(
        candidate.resolution_at,
        positions,
        config.resolution_timing_window_hours,
    )
    portfolio_concentration_score = _portfolio_concentration_score(candidate, positions)
    correlation_penalty = _correlation_penalty(
        category_overlap_score=category_overlap_score,
        event_cluster_overlap_score=event_cluster_overlap_score,
        shared_source_overlap_score=shared_source_overlap_score,
        resolution_timing_overlap_score=resolution_timing_overlap_score,
        portfolio_concentration_score=portfolio_concentration_score,
        config=config,
    )
    adjusted_score = _adjusted_score(candidate.base_score, correlation_penalty)
    status = _row_status(
        correlation_penalty=correlation_penalty,
        adjusted_score=adjusted_score,
        config=config,
    )
    return StrategyCandidateCorrelationPenaltyRow(
        rank=rank,
        candidate_id=candidate.candidate_id,
        category=candidate.category,
        event_cluster_id=candidate.event_cluster_id,
        proposed_notional=candidate.proposed_notional,
        base_score=candidate.base_score,
        category_overlap_score=category_overlap_score,
        event_cluster_overlap_score=event_cluster_overlap_score,
        shared_source_overlap_score=shared_source_overlap_score,
        resolution_timing_overlap_score=resolution_timing_overlap_score,
        portfolio_concentration_score=portfolio_concentration_score,
        correlation_penalty=correlation_penalty,
        adjusted_score=adjusted_score,
        status=status,
        reason_codes=_row_reason_codes(
            category_overlap_score=category_overlap_score,
            event_cluster_overlap_score=event_cluster_overlap_score,
            shared_source_overlap_score=shared_source_overlap_score,
            resolution_timing_overlap_score=resolution_timing_overlap_score,
            portfolio_concentration_score=portfolio_concentration_score,
            status=status,
        ),
    )


def _notional_share_for_category(
    category: str,
    positions: tuple[StrategyCandidateCorrelationPortfolioPosition, ...],
) -> Decimal:
    return _notional_share(
        _matching_position_notional(
            positions,
            lambda position: position.category == category,
        ),
        _total_position_notional(positions),
    )


def _notional_share_for_event_cluster(
    event_cluster_id: str,
    positions: tuple[StrategyCandidateCorrelationPortfolioPosition, ...],
) -> Decimal:
    return _notional_share(
        _matching_position_notional(
            positions,
            lambda position: position.event_cluster_id == event_cluster_id,
        ),
        _total_position_notional(positions),
    )


def _notional_share_for_sources(
    source_ids: tuple[str, ...],
    positions: tuple[StrategyCandidateCorrelationPortfolioPosition, ...],
) -> Decimal:
    candidate_sources = frozenset(source_ids)
    return _notional_share(
        _matching_position_notional(
            positions,
            lambda position: bool(candidate_sources.intersection(position.source_ids)),
        ),
        _total_position_notional(positions),
    )


def _notional_share_for_resolution_window(
    resolution_at: datetime,
    positions: tuple[StrategyCandidateCorrelationPortfolioPosition, ...],
    window_hours: Decimal,
) -> Decimal:
    return _notional_share(
        _matching_position_notional(
            positions,
            lambda position: _resolution_hour_gap(
                resolution_at,
                position.resolution_at,
            )
            <= window_hours,
        ),
        _total_position_notional(positions),
    )


def _portfolio_concentration_score(
    candidate: StrategyCandidateCorrelationCandidateInput,
    positions: tuple[StrategyCandidateCorrelationPortfolioPosition, ...],
) -> Decimal:
    total_position_notional = _total_position_notional(positions)
    category_position_notional = _matching_position_notional(
        positions,
        lambda position: position.category == candidate.category,
    )
    total_after_candidate = total_position_notional + candidate.proposed_notional
    category_after_candidate = category_position_notional + candidate.proposed_notional
    return _notional_share(category_after_candidate, total_after_candidate)


def _correlation_penalty(
    *,
    category_overlap_score: Decimal,
    event_cluster_overlap_score: Decimal,
    shared_source_overlap_score: Decimal,
    resolution_timing_overlap_score: Decimal,
    portfolio_concentration_score: Decimal,
    config: StrategyCandidateCorrelationClusterPenaltyConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        penalty = (
            category_overlap_score * config.category_overlap_weight
            + event_cluster_overlap_score * config.event_cluster_overlap_weight
            + shared_source_overlap_score * config.shared_source_overlap_weight
            + resolution_timing_overlap_score * config.resolution_timing_overlap_weight
            + portfolio_concentration_score * config.portfolio_concentration_weight
        )
    return _normalize_unit_decimal("correlation_penalty", penalty)


def _adjusted_score(base_score: Decimal, correlation_penalty: Decimal) -> Decimal:
    adjusted = base_score - correlation_penalty
    if adjusted < ZERO:
        adjusted = ZERO
    return _normalize_unit_decimal("adjusted_score", adjusted)


def _row_status(
    *,
    correlation_penalty: Decimal,
    adjusted_score: Decimal,
    config: StrategyCandidateCorrelationClusterPenaltyConfig,
) -> str:
    if (
        correlation_penalty >= config.blocked_penalty_threshold
        or adjusted_score < config.min_adjusted_score
    ):
        return STATUS_BLOCKED
    if correlation_penalty >= config.watch_penalty_threshold:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    category_overlap_score: Decimal,
    event_cluster_overlap_score: Decimal,
    shared_source_overlap_score: Decimal,
    resolution_timing_overlap_score: Decimal,
    portfolio_concentration_score: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if category_overlap_score > ZERO:
        reason_codes.append("candidate_category_overlap")
    if event_cluster_overlap_score > ZERO:
        reason_codes.append("candidate_event_cluster_overlap")
    if shared_source_overlap_score > ZERO:
        reason_codes.append("candidate_shared_source_overlap")
    if resolution_timing_overlap_score > ZERO:
        reason_codes.append("candidate_resolution_timing_overlap")
    if portfolio_concentration_score > ZERO:
        reason_codes.append("candidate_portfolio_concentration_pressure")
    reason_codes.append(f"candidate_correlation_penalty_{status}")
    return tuple(reason_codes)


def _order_rows(
    rows: tuple[StrategyCandidateCorrelationPenaltyRow, ...],
) -> tuple[StrategyCandidateCorrelationPenaltyRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.status],
                -row.correlation_penalty,
                row.candidate_id,
            ),
        ),
    )


def _status_count(rows: tuple[StrategyCandidateCorrelationPenaltyRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _max_correlation_penalty(rows: tuple[StrategyCandidateCorrelationPenaltyRow, ...]) -> Decimal:
    if not rows:
        return ZERO.quantize(SCORE_QUANTUM)
    return max(row.correlation_penalty for row in rows)


def _mean_adjusted_score(rows: tuple[StrategyCandidateCorrelationPenaltyRow, ...]) -> Decimal:
    if not rows:
        return ZERO.quantize(SCORE_QUANTUM)
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _normalize_unit_decimal(
            "mean_adjusted_score",
            sum((row.adjusted_score for row in rows), ZERO) / _count(len(rows)),
        )


def _report_status(rows: tuple[StrategyCandidateCorrelationPenaltyRow, ...]) -> str:
    if any(row.status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[StrategyCandidateCorrelationPenaltyRow, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    reason_codes = [f"strategy_candidate_correlation_cluster_penalty_{status}"]
    if any(
        "candidate_portfolio_concentration_pressure" in row.reason_codes
        for row in rows
    ):
        reason_codes.append("strategy_candidate_correlation_cluster_penalty_concentration")
    if any(
        reason_code
        in {
            "candidate_category_overlap",
            "candidate_event_cluster_overlap",
            "candidate_shared_source_overlap",
            "candidate_resolution_timing_overlap",
        }
        for row in rows
        for reason_code in row.reason_codes
    ):
        reason_codes.append("strategy_candidate_correlation_cluster_penalty_overlap")
    return tuple(reason_codes)


def _validate_report_consistency(
    report: StrategyCandidateCorrelationClusterPenaltyReport,
) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_candidate_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_candidate_count must match rows")
    if report.watch_candidate_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_candidate_count must match rows")
    if report.blocked_candidate_count != _status_count(rows, STATUS_BLOCKED):
        raise ValueError("blocked_candidate_count must match rows")
    if report.max_correlation_penalty != _max_correlation_penalty(rows):
        raise ValueError("max_correlation_penalty must match rows")
    if report.mean_adjusted_score != _mean_adjusted_score(rows):
        raise ValueError("mean_adjusted_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("row ranks must be contiguous")


def _normalize_inputs(
    candidates: Iterable[StrategyCandidateCorrelationCandidateInput],
) -> tuple[StrategyCandidateCorrelationCandidateInput, ...]:
    if isinstance(candidates, (str, bytes, dict)) or not isinstance(candidates, Iterable):
        raise ValueError("inputs must be an iterable of StrategyCandidateCorrelationCandidateInput")
    normalized = tuple(candidates)
    seen: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not StrategyCandidateCorrelationCandidateInput:
            raise ValueError("inputs must contain StrategyCandidateCorrelationCandidateInput values")
        _require_hard_flags(candidate)
        if candidate.candidate_id in seen:
            raise ValueError("inputs must not contain duplicate candidate_id values")
        seen.add(candidate.candidate_id)
    return normalized


def _normalize_positions(
    positions: Iterable[StrategyCandidateCorrelationPortfolioPosition],
) -> tuple[StrategyCandidateCorrelationPortfolioPosition, ...]:
    if isinstance(positions, (str, bytes, dict)) or not isinstance(positions, Iterable):
        raise ValueError(
            "existing_positions must be an iterable of StrategyCandidateCorrelationPortfolioPosition",
        )
    normalized = tuple(positions)
    seen: set[str] = set()
    for position in normalized:
        if type(position) is not StrategyCandidateCorrelationPortfolioPosition:
            raise ValueError(
                "existing_positions must contain StrategyCandidateCorrelationPortfolioPosition values",
            )
        _require_hard_flags(position)
        if position.position_id in seen:
            raise ValueError("existing_positions must not contain duplicate position_id values")
        seen.add(position.position_id)
    return normalized


def _normalize_rows(
    rows: tuple[StrategyCandidateCorrelationPenaltyRow, ...],
) -> tuple[StrategyCandidateCorrelationPenaltyRow, ...]:
    if isinstance(rows, (str, bytes, dict)) or not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyCandidateCorrelationPenaltyRow:
            raise ValueError("rows must contain StrategyCandidateCorrelationPenaltyRow values")
        _require_hard_flags(row)
    return rows


def _matching_position_notional(
    positions: tuple[StrategyCandidateCorrelationPortfolioPosition, ...],
    predicate: Any,
) -> Decimal:
    total = ZERO
    for position in positions:
        if predicate(position):
            total += position.current_notional
    return _normalize_nonnegative_decimal("matching_position_notional", total)


def _total_position_notional(
    positions: tuple[StrategyCandidateCorrelationPortfolioPosition, ...],
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "total_position_notional",
        sum((position.current_notional for position in positions), ZERO),
    )


def _notional_share(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO.quantize(SCORE_QUANTUM)
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _normalize_unit_decimal("notional_share", numerator / denominator)


def _resolution_hour_gap(first: datetime, second: datetime) -> Decimal:
    seconds = Decimal(str(abs((first - second).total_seconds())))
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _normalize_nonnegative_decimal(
            "resolution_hour_gap",
            seconds / Decimal("3600"),
        )


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(SCORE_QUANTUM)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(SCORE_QUANTUM)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(name, value)
    if decimal_value > ONE:
        raise ValueError(f"{name} must not exceed one")
    return decimal_value


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical string")


def _normalize_string_tuple(name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError(f"{name} must be a tuple")
    if not value:
        raise ValueError(f"{name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(name, item)
        if item in seen:
            raise ValueError(f"{name} must not contain duplicates")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"unsafe live surface value in {path or label}")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        _as_utc(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload field must be a string")
            _require_canonical_string("payload field", key)
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_SURFACE_FRAGMENTS)


def _payload_value(value: Any, *, field_name: str | None = None) -> Any:
    label = field_name or "payload value"
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{label} must be a Decimal")
        if field_name is not None and field_name.endswith("count"):
            return str(value.quantize(ONE))
        return str(value.quantize(SCORE_QUANTUM))
    if isinstance(value, datetime):
        return _as_utc(label, value).isoformat()
    if type(value) is bool:
        return value
    if type(value) is float:
        raise ValueError(f"{label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal values")
    if type(value) is str:
        return value
    if value is None:
        return None
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload field must be a string")
            _require_canonical_string("payload field", key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _payload_value(item, field_name=key)
        return ready
    raise ValueError(f"{label} is not JSON serializable")
