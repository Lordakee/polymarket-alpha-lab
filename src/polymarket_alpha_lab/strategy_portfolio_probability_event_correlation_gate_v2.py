"""Portfolio probability-event correlation gate v2."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


DEFAULT_CONFIG_VERSION = "strategy-portfolio-probability-event-correlation-gate-v2"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
GATE_STATUSES = ("pass", "watch", "blocked")
PASS_REASON_CODE = "portfolio_probability_event_correlation_pass"
ROW_REASON_CODES = (
    "shared_catalyst",
    "shared_source_family",
    "category_overlap",
    "market_close_cluster",
    "liquidity_overlap",
    "uncorrelated_position",
)
REPORT_DIMENSION_REASON_CODES = (
    "shared_catalyst_detected",
    "shared_source_family_detected",
    "category_overlap_detected",
    "market_close_cluster_detected",
    "liquidity_overlap_detected",
)
REPORT_EXPOSURE_REASON_CODES = (
    "maximum_correlated_exposure_watch",
    "maximum_correlated_exposure_block",
    "candidate_notional_exceeds_correlated_exposure_cap",
)
REPORT_REASON_CODES = (
    PASS_REASON_CODE,
    *REPORT_DIMENSION_REASON_CODES,
    *REPORT_EXPOSURE_REASON_CODES,
)


@dataclass(frozen=True)
class StrategyPortfolioProbabilityEventCorrelationGateV2Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    close_cluster_window_seconds: Decimal = Decimal("3600.000000")
    correlated_exposure_watch_share: Decimal = Decimal("0.100000")
    correlated_exposure_block_share: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "close_cluster_window_seconds",
            _normalize_nonnegative_decimal(
                "close_cluster_window_seconds",
                self.close_cluster_window_seconds,
            ),
        )
        object.__setattr__(
            self,
            "correlated_exposure_watch_share",
            _normalize_probability(
                "correlated_exposure_watch_share",
                self.correlated_exposure_watch_share,
            ),
        )
        object.__setattr__(
            self,
            "correlated_exposure_block_share",
            _normalize_probability(
                "correlated_exposure_block_share",
                self.correlated_exposure_block_share,
            ),
        )
        if self.correlated_exposure_block_share < self.correlated_exposure_watch_share:
            raise ValueError(
                "correlated_exposure_block_share must not be below "
                "correlated_exposure_watch_share",
            )
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyPortfolioProbabilityEventCorrelationGateV2Candidate:
    candidate_id: str
    market_slug: str
    event_slug: str
    category: str
    tags: tuple[str, ...]
    catalyst_id: str
    source_family: str
    market_close_at: datetime
    liquidity_pool_id: str
    available_liquidity_usdc: Decimal
    candidate_notional: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _normalize_event_identity(self)
        object.__setattr__(self, "tags", _normalize_string_tuple("tags", self.tags))
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        object.__setattr__(
            self,
            "available_liquidity_usdc",
            _normalize_nonnegative_decimal(
                "available_liquidity_usdc",
                self.available_liquidity_usdc,
            ),
        )
        object.__setattr__(
            self,
            "candidate_notional",
            _normalize_nonnegative_decimal("candidate_notional", self.candidate_notional),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyPortfolioProbabilityEventCorrelationGateV2Position:
    position_id: str
    market_slug: str
    event_slug: str
    category: str
    tags: tuple[str, ...]
    catalyst_id: str
    source_family: str
    market_close_at: datetime
    liquidity_pool_id: str
    available_liquidity_usdc: Decimal
    exposure_notional: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("position_id", self.position_id)
        _normalize_event_identity(self)
        object.__setattr__(self, "tags", _normalize_string_tuple("tags", self.tags))
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        object.__setattr__(
            self,
            "available_liquidity_usdc",
            _normalize_nonnegative_decimal(
                "available_liquidity_usdc",
                self.available_liquidity_usdc,
            ),
        )
        object.__setattr__(
            self,
            "exposure_notional",
            _normalize_nonnegative_decimal("exposure_notional", self.exposure_notional),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyPortfolioProbabilityEventCorrelationGateV2Row:
    position_id: str
    market_slug: str
    event_slug: str
    exposure_notional: Decimal
    shared_catalyst: bool
    shared_source_family: bool
    category_overlap: bool
    market_close_clustered: bool
    liquidity_overlap: bool
    close_time_distance_seconds: Decimal
    liquidity_overlap_notional: Decimal
    liquidity_overlap_share: Decimal
    correlation_dimension_count: Decimal
    correlated_exposure_notional: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("position_id", "market_slug", "event_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "exposure_notional",
            "close_time_distance_seconds",
            "liquidity_overlap_notional",
            "liquidity_overlap_share",
            "correlated_exposure_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.liquidity_overlap_share > ONE:
            raise ValueError("liquidity_overlap_share must be at most one")
        object.__setattr__(
            self,
            "correlation_dimension_count",
            _normalize_count_decimal(
                "correlation_dimension_count",
                self.correlation_dimension_count,
            ),
        )
        for field_name in (
            "shared_catalyst",
            "shared_source_family",
            "category_overlap",
            "market_close_clustered",
            "liquidity_overlap",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _require_safety_flags(self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyPortfolioProbabilityEventCorrelationGateV2Report:
    generated_at: datetime
    config_version: str
    candidate_id: str
    market_slug: str
    event_slug: str
    candidate_notional: Decimal
    portfolio_nav: Decimal
    position_count: Decimal
    correlated_position_count: Decimal
    shared_catalyst_count: Decimal
    shared_source_family_count: Decimal
    category_overlap_count: Decimal
    market_close_cluster_count: Decimal
    liquidity_overlap_count: Decimal
    existing_correlated_exposure_notional: Decimal
    maximum_correlated_exposure_notional: Decimal
    maximum_correlated_exposure_share: Decimal
    correlated_exposure_watch_share: Decimal
    correlated_exposure_block_share: Decimal
    allowed_candidate_notional: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyPortfolioProbabilityEventCorrelationGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in ("config_version", "candidate_id", "market_slug", "event_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "candidate_notional",
            "existing_correlated_exposure_notional",
            "maximum_correlated_exposure_notional",
            "maximum_correlated_exposure_share",
            "correlated_exposure_watch_share",
            "correlated_exposure_block_share",
            "allowed_candidate_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "portfolio_nav",
            _normalize_positive_decimal("portfolio_nav", self.portfolio_nav),
        )
        for field_name in (
            "position_count",
            "correlated_position_count",
            "shared_catalyst_count",
            "shared_source_family_count",
            "category_overlap_count",
            "market_close_cluster_count",
            "liquidity_overlap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.maximum_correlated_exposure_share > ONE:
            raise ValueError("maximum_correlated_exposure_share must be at most one")
        if self.correlated_exposure_watch_share > ONE:
            raise ValueError("correlated_exposure_watch_share must be at most one")
        if self.correlated_exposure_block_share > ONE:
            raise ValueError("correlated_exposure_block_share must be at most one")
        if self.correlated_exposure_block_share < self.correlated_exposure_watch_share:
            raise ValueError(
                "correlated_exposure_block_share must not be below "
                "correlated_exposure_watch_share",
            )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_safety_flags(self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_strategy_portfolio_probability_event_correlation_gate_v2_report(
    candidate: StrategyPortfolioProbabilityEventCorrelationGateV2Candidate,
    positions: Iterable[StrategyPortfolioProbabilityEventCorrelationGateV2Position],
    *,
    config: StrategyPortfolioProbabilityEventCorrelationGateV2Config,
    portfolio_nav: Decimal,
    generated_at: datetime,
) -> StrategyPortfolioProbabilityEventCorrelationGateV2Report:
    if type(candidate) is not StrategyPortfolioProbabilityEventCorrelationGateV2Candidate:
        raise ValueError(
            "candidate must be a "
            "StrategyPortfolioProbabilityEventCorrelationGateV2Candidate",
        )
    if type(config) is not StrategyPortfolioProbabilityEventCorrelationGateV2Config:
        raise ValueError(
            "config must be a StrategyPortfolioProbabilityEventCorrelationGateV2Config",
        )
    _require_safety_flags(candidate)
    _require_safety_flags(config)
    portfolio_nav = _normalize_positive_decimal("portfolio_nav", portfolio_nav)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_positions = _normalize_positions(positions)
    rows = tuple(
        sorted(
            (
                _row_from_position(candidate, value, config=config)
                for value in normalized_positions
            ),
            key=_row_sort_key,
        ),
    )
    existing_correlated_exposure_notional = _sum_decimals(
        tuple(row.correlated_exposure_notional for row in rows),
    )
    maximum_correlated_exposure_notional = _add_decimal(
        existing_correlated_exposure_notional,
        candidate.candidate_notional,
    )
    maximum_correlated_exposure_share = _ratio_decimal(
        maximum_correlated_exposure_notional,
        portfolio_nav,
    )
    allowed_candidate_notional = _allowed_candidate_notional(
        candidate.candidate_notional,
        existing_correlated_exposure_notional,
        portfolio_nav,
        config.correlated_exposure_block_share,
    )
    gate_status, reason_codes = _report_status_and_reason_codes(
        shared_catalyst_count=_count_matching(rows, "shared_catalyst"),
        shared_source_family_count=_count_matching(rows, "shared_source_family"),
        category_overlap_count=_count_matching(rows, "category_overlap"),
        market_close_cluster_count=_count_matching(rows, "market_close_clustered"),
        liquidity_overlap_count=_count_matching(rows, "liquidity_overlap"),
        maximum_correlated_exposure_share=maximum_correlated_exposure_share,
        correlated_exposure_watch_share=config.correlated_exposure_watch_share,
        correlated_exposure_block_share=config.correlated_exposure_block_share,
        candidate_notional=candidate.candidate_notional,
        allowed_candidate_notional=allowed_candidate_notional,
    )

    return StrategyPortfolioProbabilityEventCorrelationGateV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        event_slug=candidate.event_slug,
        candidate_notional=candidate.candidate_notional,
        portfolio_nav=portfolio_nav,
        position_count=_count_decimal(len(rows)),
        correlated_position_count=_count_correlated_rows(rows),
        shared_catalyst_count=_count_matching(rows, "shared_catalyst"),
        shared_source_family_count=_count_matching(rows, "shared_source_family"),
        category_overlap_count=_count_matching(rows, "category_overlap"),
        market_close_cluster_count=_count_matching(rows, "market_close_clustered"),
        liquidity_overlap_count=_count_matching(rows, "liquidity_overlap"),
        existing_correlated_exposure_notional=existing_correlated_exposure_notional,
        maximum_correlated_exposure_notional=maximum_correlated_exposure_notional,
        maximum_correlated_exposure_share=maximum_correlated_exposure_share,
        correlated_exposure_watch_share=config.correlated_exposure_watch_share,
        correlated_exposure_block_share=config.correlated_exposure_block_share,
        allowed_candidate_notional=allowed_candidate_notional,
        gate_status=gate_status,
        reason_codes=reason_codes,
        rows=rows,
    )


def strategy_portfolio_probability_event_correlation_gate_v2_payload(
    report: StrategyPortfolioProbabilityEventCorrelationGateV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyPortfolioProbabilityEventCorrelationGateV2Report:
        raise ValueError(
            "report must be a StrategyPortfolioProbabilityEventCorrelationGateV2Report",
        )
    _require_safety_flags(report)
    _verify_report_integrity(report)
    return _json_ready(asdict(report))


def _row_from_position(
    candidate: StrategyPortfolioProbabilityEventCorrelationGateV2Candidate,
    position: StrategyPortfolioProbabilityEventCorrelationGateV2Position,
    *,
    config: StrategyPortfolioProbabilityEventCorrelationGateV2Config,
) -> StrategyPortfolioProbabilityEventCorrelationGateV2Row:
    shared_catalyst = candidate.catalyst_id == position.catalyst_id
    shared_source_family = candidate.source_family == position.source_family
    category_overlap = _has_category_overlap(candidate, position)
    close_time_distance_seconds = _absolute_seconds_between(
        candidate.market_close_at,
        position.market_close_at,
    )
    market_close_clustered = close_time_distance_seconds <= config.close_cluster_window_seconds
    liquidity_overlap = candidate.liquidity_pool_id == position.liquidity_pool_id
    liquidity_overlap_notional = (
        _min_decimal(candidate.available_liquidity_usdc, position.available_liquidity_usdc)
        if liquidity_overlap
        else ZERO
    )
    liquidity_overlap_share = (
        _ratio_decimal(liquidity_overlap_notional, candidate.available_liquidity_usdc)
        if liquidity_overlap and candidate.available_liquidity_usdc > ZERO
        else ZERO
    )
    correlation_dimension_count = _count_decimal(
        sum(
            1
            for value in (
                shared_catalyst,
                shared_source_family,
                category_overlap,
                market_close_clustered,
                liquidity_overlap,
            )
            if value
        ),
    )
    correlated_exposure_notional = (
        position.exposure_notional if correlation_dimension_count > ZERO else ZERO
    )
    return StrategyPortfolioProbabilityEventCorrelationGateV2Row(
        position_id=position.position_id,
        market_slug=position.market_slug,
        event_slug=position.event_slug,
        exposure_notional=position.exposure_notional,
        shared_catalyst=shared_catalyst,
        shared_source_family=shared_source_family,
        category_overlap=category_overlap,
        market_close_clustered=market_close_clustered,
        liquidity_overlap=liquidity_overlap,
        close_time_distance_seconds=close_time_distance_seconds,
        liquidity_overlap_notional=liquidity_overlap_notional,
        liquidity_overlap_share=liquidity_overlap_share,
        correlation_dimension_count=correlation_dimension_count,
        correlated_exposure_notional=correlated_exposure_notional,
        reason_codes=_row_reason_codes(
            shared_catalyst=shared_catalyst,
            shared_source_family=shared_source_family,
            category_overlap=category_overlap,
            market_close_clustered=market_close_clustered,
            liquidity_overlap=liquidity_overlap,
        ),
    )


def _has_category_overlap(
    candidate: StrategyPortfolioProbabilityEventCorrelationGateV2Candidate,
    position: StrategyPortfolioProbabilityEventCorrelationGateV2Position,
) -> bool:
    if candidate.category == position.category:
        return True
    return bool(set(candidate.tags).intersection(position.tags))


def _row_reason_codes(
    *,
    shared_catalyst: bool,
    shared_source_family: bool,
    category_overlap: bool,
    market_close_clustered: bool,
    liquidity_overlap: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if shared_catalyst:
        reason_codes.append("shared_catalyst")
    if shared_source_family:
        reason_codes.append("shared_source_family")
    if category_overlap:
        reason_codes.append("category_overlap")
    if market_close_clustered:
        reason_codes.append("market_close_cluster")
    if liquidity_overlap:
        reason_codes.append("liquidity_overlap")
    if reason_codes:
        return tuple(reason_codes)
    return ("uncorrelated_position",)


def _report_status_and_reason_codes(
    *,
    shared_catalyst_count: Decimal,
    shared_source_family_count: Decimal,
    category_overlap_count: Decimal,
    market_close_cluster_count: Decimal,
    liquidity_overlap_count: Decimal,
    maximum_correlated_exposure_share: Decimal,
    correlated_exposure_watch_share: Decimal,
    correlated_exposure_block_share: Decimal,
    candidate_notional: Decimal,
    allowed_candidate_notional: Decimal,
) -> tuple[str, tuple[str, ...]]:
    reason_codes: list[str] = []
    if shared_catalyst_count > ZERO:
        reason_codes.append("shared_catalyst_detected")
    if shared_source_family_count > ZERO:
        reason_codes.append("shared_source_family_detected")
    if category_overlap_count > ZERO:
        reason_codes.append("category_overlap_detected")
    if market_close_cluster_count > ZERO:
        reason_codes.append("market_close_cluster_detected")
    if liquidity_overlap_count > ZERO:
        reason_codes.append("liquidity_overlap_detected")

    if maximum_correlated_exposure_share > correlated_exposure_block_share:
        reason_codes.append("maximum_correlated_exposure_block")
        if candidate_notional > allowed_candidate_notional:
            reason_codes.append("candidate_notional_exceeds_correlated_exposure_cap")
        return "blocked", tuple(reason_codes)
    if maximum_correlated_exposure_share > correlated_exposure_watch_share:
        reason_codes.append("maximum_correlated_exposure_watch")
    if reason_codes:
        return "watch", tuple(reason_codes)
    return "pass", (PASS_REASON_CODE,)


def _row_sort_key(
    row: StrategyPortfolioProbabilityEventCorrelationGateV2Row,
) -> tuple[Decimal, Decimal, Decimal, str, str, str]:
    return (
        -row.correlation_dimension_count,
        -row.correlated_exposure_notional,
        row.close_time_distance_seconds,
        row.market_slug,
        row.position_id,
        row.event_slug,
    )


def _normalize_positions(
    positions: Iterable[StrategyPortfolioProbabilityEventCorrelationGateV2Position],
) -> tuple[StrategyPortfolioProbabilityEventCorrelationGateV2Position, ...]:
    if isinstance(positions, (str, bytes)):
        raise ValueError(
            "positions must be an iterable of "
            "StrategyPortfolioProbabilityEventCorrelationGateV2Position values",
        )
    try:
        normalized = tuple(positions)
    except TypeError as exc:
        raise ValueError(
            "positions must be an iterable of "
            "StrategyPortfolioProbabilityEventCorrelationGateV2Position values",
        ) from exc
    for value in normalized:
        if type(value) is not StrategyPortfolioProbabilityEventCorrelationGateV2Position:
            raise ValueError(
                "positions must contain only "
                "StrategyPortfolioProbabilityEventCorrelationGateV2Position values",
            )
        _require_safety_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[StrategyPortfolioProbabilityEventCorrelationGateV2Row],
) -> tuple[StrategyPortfolioProbabilityEventCorrelationGateV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for value in normalized:
        if type(value) is not StrategyPortfolioProbabilityEventCorrelationGateV2Row:
            raise ValueError(
                "rows must contain only "
                "StrategyPortfolioProbabilityEventCorrelationGateV2Row values",
            )
        _require_safety_flags(value)
        _verify_digest(value)
    return normalized


def _normalize_event_identity(value: object) -> None:
    for field_name in (
        "market_slug",
        "event_slug",
        "category",
        "catalyst_id",
        "source_family",
        "liquidity_pool_id",
    ):
        _require_canonical_string(field_name, getattr(value, field_name))
    if hasattr(value, "candidate_id"):
        _require_canonical_string("candidate_id", getattr(value, "candidate_id"))


def _validate_row_consistency(
    row: StrategyPortfolioProbabilityEventCorrelationGateV2Row,
) -> None:
    expected_dimension_count = _count_decimal(
        sum(
            1
            for value in (
                row.shared_catalyst,
                row.shared_source_family,
                row.category_overlap,
                row.market_close_clustered,
                row.liquidity_overlap,
            )
            if value
        ),
    )
    if row.correlation_dimension_count != expected_dimension_count:
        raise ValueError("correlation_dimension_count must match row flags")
    if row.correlation_dimension_count == ZERO:
        if row.correlated_exposure_notional != ZERO:
            raise ValueError("correlated_exposure_notional must be zero without overlap")
    elif row.correlated_exposure_notional != row.exposure_notional:
        raise ValueError("correlated_exposure_notional must match exposure_notional")
    if row.liquidity_overlap:
        if row.liquidity_overlap_notional == ZERO:
            raise ValueError("liquidity_overlap_notional must be positive when overlap is true")
    elif row.liquidity_overlap_notional != ZERO or row.liquidity_overlap_share != ZERO:
        raise ValueError("liquidity overlap values must be zero when overlap is false")
    expected_reason_codes = _row_reason_codes(
        shared_catalyst=row.shared_catalyst,
        shared_source_family=row.shared_source_family,
        category_overlap=row.category_overlap,
        market_close_clustered=row.market_close_clustered,
        liquidity_overlap=row.liquidity_overlap,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row flags")


def _validate_report_consistency(
    report: StrategyPortfolioProbabilityEventCorrelationGateV2Report,
) -> None:
    if report.position_count != _count_decimal(len(report.rows)):
        raise ValueError("position_count must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must be sorted by correlation severity")
    if report.correlated_position_count != _count_correlated_rows(report.rows):
        raise ValueError("correlated_position_count must match rows")
    for field_name, row_field_name in (
        ("shared_catalyst_count", "shared_catalyst"),
        ("shared_source_family_count", "shared_source_family"),
        ("category_overlap_count", "category_overlap"),
        ("market_close_cluster_count", "market_close_clustered"),
        ("liquidity_overlap_count", "liquidity_overlap"),
    ):
        if getattr(report, field_name) != _count_matching(report.rows, row_field_name):
            raise ValueError(f"{field_name} must match rows")
    expected_existing = _sum_decimals(
        tuple(row.correlated_exposure_notional for row in report.rows),
    )
    if report.existing_correlated_exposure_notional != expected_existing:
        raise ValueError("existing_correlated_exposure_notional must match rows")
    expected_maximum = _add_decimal(
        report.existing_correlated_exposure_notional,
        report.candidate_notional,
    )
    if report.maximum_correlated_exposure_notional != expected_maximum:
        raise ValueError("maximum_correlated_exposure_notional must match inputs")
    expected_share = _ratio_decimal(
        report.maximum_correlated_exposure_notional,
        report.portfolio_nav,
    )
    if report.maximum_correlated_exposure_share != expected_share:
        raise ValueError("maximum_correlated_exposure_share must match inputs")
    expected_allowed = _allowed_candidate_notional(
        report.candidate_notional,
        report.existing_correlated_exposure_notional,
        report.portfolio_nav,
        report.correlated_exposure_block_share,
    )
    if report.allowed_candidate_notional != expected_allowed:
        raise ValueError("allowed_candidate_notional must match inputs")
    expected_status, expected_reason_codes = _report_status_and_reason_codes(
        shared_catalyst_count=report.shared_catalyst_count,
        shared_source_family_count=report.shared_source_family_count,
        category_overlap_count=report.category_overlap_count,
        market_close_cluster_count=report.market_close_cluster_count,
        liquidity_overlap_count=report.liquidity_overlap_count,
        maximum_correlated_exposure_share=report.maximum_correlated_exposure_share,
        correlated_exposure_watch_share=report.correlated_exposure_watch_share,
        correlated_exposure_block_share=report.correlated_exposure_block_share,
        candidate_notional=report.candidate_notional,
        allowed_candidate_notional=report.allowed_candidate_notional,
    )
    if report.gate_status != expected_status:
        raise ValueError("gate_status must match report values")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report values")
    for row in report.rows:
        _verify_digest(row)


def _verify_report_integrity(
    report: StrategyPortfolioProbabilityEventCorrelationGateV2Report,
) -> None:
    _validate_report_consistency(report)
    _verify_digest(report)
    for row in report.rows:
        _verify_digest(row)


def _count_matching(
    rows: tuple[StrategyPortfolioProbabilityEventCorrelationGateV2Row, ...],
    field_name: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if getattr(row, field_name)))


def _count_correlated_rows(
    rows: tuple[StrategyPortfolioProbabilityEventCorrelationGateV2Row, ...],
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.correlation_dimension_count > ZERO))


def _allowed_candidate_notional(
    candidate_notional: Decimal,
    existing_correlated_exposure_notional: Decimal,
    portfolio_nav: Decimal,
    correlated_exposure_block_share: Decimal,
) -> Decimal:
    cap_notional = _multiply_decimal(portfolio_nav, correlated_exposure_block_share)
    remaining = _max_decimal(_subtract_decimal(cap_notional, existing_correlated_exposure_notional), ZERO)
    return _min_decimal(candidate_notional, remaining)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return total


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _ratio_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _absolute_seconds_between(left: datetime, right: datetime) -> Decimal:
    delta = left - right
    if delta.days < 0:
        delta = -delta
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(seconds + microseconds)


def _min_decimal(left: Decimal, right: Decimal) -> Decimal:
    return left if left <= right else right


def _max_decimal(left: Decimal, right: Decimal) -> Decimal:
    return left if left >= right else right


def _count_decimal(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _normalize_string_tuple(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string(field_name, value)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    for value in values:
        if value not in allowed_values:
            raise ValueError(f"{field_name} contains an unknown reason code")
    return tuple(dict.fromkeys(values))


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _apply_or_verify_digest(
    value: (
        StrategyPortfolioProbabilityEventCorrelationGateV2Row
        | StrategyPortfolioProbabilityEventCorrelationGateV2Report
    ),
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(
    value: (
        StrategyPortfolioProbabilityEventCorrelationGateV2Row
        | StrategyPortfolioProbabilityEventCorrelationGateV2Report
    ),
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: (
        StrategyPortfolioProbabilityEventCorrelationGateV2Row
        | StrategyPortfolioProbabilityEventCorrelationGateV2Report
    ),
) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    payload = _json_ready(digest_input)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload value is not JSON-ready")


__all__ = (
    "StrategyPortfolioProbabilityEventCorrelationGateV2Candidate",
    "StrategyPortfolioProbabilityEventCorrelationGateV2Config",
    "StrategyPortfolioProbabilityEventCorrelationGateV2Position",
    "StrategyPortfolioProbabilityEventCorrelationGateV2Report",
    "StrategyPortfolioProbabilityEventCorrelationGateV2Row",
    "build_strategy_portfolio_probability_event_correlation_gate_v2_report",
    "strategy_portfolio_probability_event_correlation_gate_v2_payload",
)
