"""Pure local paper-trade settlement validation reducer.

This module joins already-typed paper trade records to already-typed outcome
tracking observations and computes paper-only settlement diagnostics. It does no
IO, network access, auth, wallet access, order placement, ranking, or advice.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    PaperForecastEvidenceReport,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport


__all__ = (
    "PaperTradeSettlementValidationConfig",
    "PaperTradeSettlementValidationReport",
    "PaperTradeSettlementValidationRow",
    "build_paper_trade_settlement_validation_report",
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

ROW_STATUSES = ("pending", "observed", "quality_flags")
REPORT_STATUSES = (
    "empty",
    "pending",
    "insufficient_sample",
    "observed",
    "quality_flags",
)


@dataclass(frozen=True)
class PaperTradeSettlementValidationConfig:
    config_version: str
    min_resolved_trades: int = 30
    forecast_evidence_config: PaperForecastEvidenceConfig = field(
        default_factory=lambda: PaperForecastEvidenceConfig(
            config_version="paper-trade-settlement-validation-v0",
        ),
    )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("min_resolved_trades", self.min_resolved_trades)
        if type(self.forecast_evidence_config) is not PaperForecastEvidenceConfig:
            raise ValueError(
                "forecast_evidence_config must be a PaperForecastEvidenceConfig",
            )


@dataclass(frozen=True)
class PaperTradeSettlementValidationRow:
    packet_id: str
    source_packet_id: str | None
    condition_id: str
    token_id: str
    market_slug: str
    outcome_name: str
    strategy_type: str
    status: str
    entry_notional: Decimal
    settlement_payout: Decimal | None
    realized_pnl: Decimal | None
    return_ratio: Decimal | None
    predicted_probability: Decimal | None
    actual_outcome_value: Decimal | None
    probability_loss: Decimal | None
    cost_adjusted_edge: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "packet_id",
            "condition_id",
            "token_id",
            "market_slug",
            "outcome_name",
            "strategy_type",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        if self.source_packet_id is not None:
            _require_canonical_string("source_packet_id", self.source_packet_id)
        if self.status not in ROW_STATUSES:
            raise ValueError("status must be a known settlement validation row status")
        _require_nonnegative_decimal("entry_notional", self.entry_notional)
        _require_optional_nonnegative_decimal(
            "settlement_payout",
            self.settlement_payout,
        )
        _require_optional_decimal("realized_pnl", self.realized_pnl)
        _require_optional_decimal("return_ratio", self.return_ratio)
        _require_optional_probability_decimal(
            "predicted_probability",
            self.predicted_probability,
        )
        if self.actual_outcome_value is not None:
            _require_zero_one_decimal("actual_outcome_value", self.actual_outcome_value)
        _require_optional_nonnegative_decimal(
            "probability_loss",
            self.probability_loss,
        )
        _require_decimal("cost_adjusted_edge", self.cost_adjusted_edge)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _validate_hard_flags(self)


@dataclass(frozen=True)
class PaperTradeSettlementValidationReport:
    generated_at: datetime
    config_version: str
    trade_count: int
    outcome_observation_count: int
    row_count: int
    resolved_count: int
    pending_count: int
    quality_flag_count: int
    duplicate_outcome_count: int
    unmatched_outcome_count: int
    total_entry_notional: Decimal
    total_settlement_payout: Decimal
    total_realized_pnl: Decimal
    win_rate: Decimal | None
    positive_return_rate: Decimal | None
    mean_probability_loss: Decimal | None
    mean_return_ratio: Decimal | None
    mean_cost_adjusted_edge: Decimal | None
    positive_edge_hit_rate: Decimal | None
    first_trade_decision_at: datetime | None
    latest_trade_decision_at: datetime | None
    first_observed_at: datetime | None
    latest_observed_at: datetime | None
    status: str
    rows: tuple[PaperTradeSettlementValidationRow, ...]
    forecast_evidence_report: PaperForecastEvidenceReport | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.generated_at) is not datetime:
            raise ValueError("generated_at must be a datetime")
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "trade_count",
            "outcome_observation_count",
            "row_count",
            "resolved_count",
            "pending_count",
            "quality_flag_count",
            "duplicate_outcome_count",
            "unmatched_outcome_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "total_entry_notional",
            "total_settlement_payout",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_decimal("total_realized_pnl", self.total_realized_pnl)
        for field_name in (
            "win_rate",
            "positive_return_rate",
            "positive_edge_hit_rate",
        ):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "mean_probability_loss",
            "mean_return_ratio",
            "mean_cost_adjusted_edge",
        ):
            _require_optional_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "first_trade_decision_at",
            "latest_trade_decision_at",
            "first_observed_at",
            "latest_observed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known settlement validation report status")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if self.forecast_evidence_report is not None:
            if type(self.forecast_evidence_report) is not PaperForecastEvidenceReport:
                raise ValueError(
                    "forecast_evidence_report must be a PaperForecastEvidenceReport or None",
                )
            if self.forecast_evidence_report.paper_only is not True:
                raise ValueError("forecast_evidence_report paper_only must be True")
        _validate_report_consistency(self)
        _validate_hard_flags(self)


def build_paper_trade_settlement_validation_report(
    trade_records: Iterable[PaperTradeRecord],
    *,
    outcome_report: OutcomeTrackingReport | None,
    config: PaperTradeSettlementValidationConfig,
    generated_at: datetime,
) -> PaperTradeSettlementValidationReport:
    """Validate local paper-trade settlement outcomes against local evidence."""

    if type(config) is not PaperTradeSettlementValidationConfig:
        raise ValueError("config must be a PaperTradeSettlementValidationConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if outcome_report is not None:
        if type(outcome_report) is not OutcomeTrackingReport:
            raise ValueError("outcome_report must be an OutcomeTrackingReport or None")
        _validate_outcome_report_flags(outcome_report)

    trades = _normalize_trade_records(trade_records)
    observations = _normalize_outcome_observations(outcome_report)
    trade_keys = _trade_keys(trades)
    duplicate_trade_keys = _duplicate_trade_keys(trades)
    observations_by_key = _observations_by_join_key(observations)
    duplicate_keys = {
        key for key, values in observations_by_key.items() if len(values) > 1
    }
    duplicate_outcome_count = sum(
        len(values)
        for key, values in observations_by_key.items()
        if key in duplicate_keys
    )
    unmatched_outcome_count = sum(
        len(values)
        for key, values in observations_by_key.items()
        if key not in trade_keys
    )
    outcome_report_trade_set_mismatch = _outcome_report_has_trade_set_mismatch(
        outcome_report=outcome_report,
        trade_count=len(trades),
        unmatched_outcome_count=unmatched_outcome_count,
    )

    rows: list[PaperTradeSettlementValidationRow] = []
    evidence_observations: list[PaperForecastEvidenceObservation] = []
    for trade in trades:
        key = _join_key_for_trade(trade)
        observation_values = observations_by_key.get(key, ())
        entry_notional = _entry_notional(trade)
        if key in duplicate_trade_keys:
            rows.append(
                _quality_flag_row(
                    trade,
                    entry_notional=entry_notional,
                    reason_code="duplicate_trade_join_key",
                ),
            )
            continue
        if trade.order_side == "sell":
            rows.append(
                _quality_flag_row(
                    trade,
                    entry_notional=entry_notional,
                    reason_code="sell_side_settlement_requires_position_context",
                ),
            )
            continue
        if key in duplicate_keys:
            rows.append(
                _quality_flag_row(
                    trade,
                    entry_notional=entry_notional,
                    reason_code="duplicate_outcomes",
                ),
            )
            continue
        if not observation_values:
            if outcome_report_trade_set_mismatch:
                rows.append(
                    _quality_flag_row(
                        trade,
                        entry_notional=entry_notional,
                        reason_code="outcome_report_trade_set_mismatch",
                    ),
                )
                continue
            rows.append(_pending_row(trade, entry_notional=entry_notional))
            continue

        observation = observation_values[0]
        if not _observation_identity_matches_trade(observation, trade):
            rows.append(
                _quality_flag_row(
                    trade,
                    entry_notional=entry_notional,
                    source_packet_id=observation.source_packet_id,
                    reason_code="outcome_identity_mismatch",
                ),
            )
            continue
        if (
            observation.predicted_probability is None
            or observation.actual_outcome_value is None
        ):
            rows.append(
                _quality_flag_row(
                    trade,
                    entry_notional=entry_notional,
                    source_packet_id=observation.source_packet_id,
                    reason_code="incomplete_outcome_observation",
                ),
            )
            continue

        row = _observed_row(
            trade,
            observation,
            entry_notional=entry_notional,
        )
        rows.append(row)
        evidence_observations.append(
            _settlement_evidence_observation(
                trade=trade,
                observation=observation,
                row=row,
            ),
        )

    evidence_report = (
        build_paper_forecast_evidence_report(
            tuple(evidence_observations),
            config=config.forecast_evidence_config,
            generated_at=generated_at,
        )
        if evidence_observations
        else None
    )
    decision_times = tuple(_as_utc(trade.decision_timestamp_utc) for trade in trades)
    observed_times = tuple(_as_utc(item.observed_at) for item in observations)

    return _report_from_rows(
        generated_at=_as_utc(generated_at),
        config=config,
        rows=tuple(rows),
        outcome_observation_count=len(observations),
        duplicate_outcome_count=duplicate_outcome_count,
        unmatched_outcome_count=unmatched_outcome_count,
        first_trade_decision_at=min(decision_times) if decision_times else None,
        latest_trade_decision_at=max(decision_times) if decision_times else None,
        first_observed_at=min(observed_times) if observed_times else None,
        latest_observed_at=max(observed_times) if observed_times else None,
        forecast_evidence_report=evidence_report,
    )


def _report_from_rows(
    *,
    generated_at: datetime,
    config: PaperTradeSettlementValidationConfig,
    rows: tuple[PaperTradeSettlementValidationRow, ...],
    outcome_observation_count: int,
    duplicate_outcome_count: int,
    unmatched_outcome_count: int,
    first_trade_decision_at: datetime | None,
    latest_trade_decision_at: datetime | None,
    first_observed_at: datetime | None,
    latest_observed_at: datetime | None,
    forecast_evidence_report: PaperForecastEvidenceReport | None,
) -> PaperTradeSettlementValidationReport:
    observed_rows = tuple(row for row in rows if row.status == "observed")
    pending_rows = tuple(row for row in rows if row.status == "pending")
    quality_rows = tuple(row for row in rows if row.status == "quality_flags")
    status = _report_status(
        trade_count=len(rows),
        resolved_count=len(observed_rows),
        quality_flag_count=len(quality_rows),
        duplicate_outcome_count=duplicate_outcome_count,
        unmatched_outcome_count=unmatched_outcome_count,
        min_resolved_trades=config.min_resolved_trades,
    )

    return PaperTradeSettlementValidationReport(
        generated_at=generated_at,
        config_version=config.config_version,
        trade_count=len(rows),
        outcome_observation_count=outcome_observation_count,
        row_count=len(rows),
        resolved_count=len(observed_rows),
        pending_count=len(pending_rows),
        quality_flag_count=len(quality_rows),
        duplicate_outcome_count=duplicate_outcome_count,
        unmatched_outcome_count=unmatched_outcome_count,
        total_entry_notional=sum((row.entry_notional for row in rows), ZERO),
        total_settlement_payout=sum(
            (row.settlement_payout for row in rows if row.settlement_payout is not None),
            ZERO,
        ),
        total_realized_pnl=sum(
            (row.realized_pnl for row in rows if row.realized_pnl is not None),
            ZERO,
        ),
        win_rate=_rate(
            sum(1 for row in observed_rows if row.actual_outcome_value == ONE),
            len(observed_rows),
        ),
        positive_return_rate=_rate(
            sum(
                1
                for row in observed_rows
                if row.return_ratio is not None and row.return_ratio > ZERO
            ),
            sum(1 for row in observed_rows if row.return_ratio is not None),
        ),
        mean_probability_loss=_mean_optional(
            row.probability_loss for row in observed_rows
        ),
        mean_return_ratio=_mean_optional(row.return_ratio for row in observed_rows),
        mean_cost_adjusted_edge=_mean_optional(
            row.cost_adjusted_edge for row in observed_rows
        ),
        positive_edge_hit_rate=_positive_edge_hit_rate(observed_rows),
        first_trade_decision_at=first_trade_decision_at,
        latest_trade_decision_at=latest_trade_decision_at,
        first_observed_at=first_observed_at,
        latest_observed_at=latest_observed_at,
        status=status,
        rows=rows,
        forecast_evidence_report=forecast_evidence_report,
    )


def _observed_row(
    trade: PaperTradeRecord,
    observation: PaperForecastEvidenceObservation,
    *,
    entry_notional: Decimal,
) -> PaperTradeSettlementValidationRow:
    actual = observation.actual_outcome_value
    predicted = observation.predicted_probability
    if actual is None or predicted is None:
        raise ValueError("resolved observation must include probability outcome values")
    settlement_payout = trade.fill_filled_size * actual
    realized_pnl = settlement_payout - entry_notional
    return PaperTradeSettlementValidationRow(
        packet_id=trade.packet_id,
        source_packet_id=observation.source_packet_id,
        condition_id=trade.condition_id,
        token_id=trade.token_id,
        market_slug=trade.market_slug,
        outcome_name=trade.outcome_name,
        strategy_type=trade.strategy_type,
        status="observed",
        entry_notional=entry_notional,
        settlement_payout=settlement_payout,
        realized_pnl=realized_pnl,
        return_ratio=_optional_ratio(realized_pnl, entry_notional),
        predicted_probability=predicted,
        actual_outcome_value=actual,
        probability_loss=_probability_loss(predicted, actual),
        cost_adjusted_edge=trade.research_cost_adjusted_edge,
        reason_codes=("settlement_observed",),
    )


def _pending_row(
    trade: PaperTradeRecord,
    *,
    entry_notional: Decimal,
) -> PaperTradeSettlementValidationRow:
    return PaperTradeSettlementValidationRow(
        packet_id=trade.packet_id,
        source_packet_id=None,
        condition_id=trade.condition_id,
        token_id=trade.token_id,
        market_slug=trade.market_slug,
        outcome_name=trade.outcome_name,
        strategy_type=trade.strategy_type,
        status="pending",
        entry_notional=entry_notional,
        settlement_payout=None,
        realized_pnl=None,
        return_ratio=None,
        predicted_probability=None,
        actual_outcome_value=None,
        probability_loss=None,
        cost_adjusted_edge=trade.research_cost_adjusted_edge,
        reason_codes=("outcome_pending",),
    )


def _quality_flag_row(
    trade: PaperTradeRecord,
    *,
    entry_notional: Decimal,
    reason_code: str,
    source_packet_id: str | None = None,
) -> PaperTradeSettlementValidationRow:
    return PaperTradeSettlementValidationRow(
        packet_id=trade.packet_id,
        source_packet_id=source_packet_id,
        condition_id=trade.condition_id,
        token_id=trade.token_id,
        market_slug=trade.market_slug,
        outcome_name=trade.outcome_name,
        strategy_type=trade.strategy_type,
        status="quality_flags",
        entry_notional=entry_notional,
        settlement_payout=None,
        realized_pnl=None,
        return_ratio=None,
        predicted_probability=None,
        actual_outcome_value=None,
        probability_loss=None,
        cost_adjusted_edge=trade.research_cost_adjusted_edge,
        reason_codes=(reason_code,),
    )


def _settlement_evidence_observation(
    *,
    trade: PaperTradeRecord,
    observation: PaperForecastEvidenceObservation,
    row: PaperTradeSettlementValidationRow,
) -> PaperForecastEvidenceObservation:
    fill_probability = _optional_ratio(
        trade.fill_filled_size,
        trade.order_requested_size,
    )
    residual_exposure_ratio = _optional_ratio(
        trade.fill_unfilled_size,
        trade.order_requested_size,
    )
    edge_values = {}
    if (
        row.return_ratio is not None
        and fill_probability is not None
        and residual_exposure_ratio is not None
    ):
        edge_values = {
            "theoretical_edge_ratio": trade.research_theoretical_edge,
            "executable_edge_ratio": trade.research_cost_adjusted_edge,
            "fill_probability": fill_probability,
            "residual_exposure_ratio": residual_exposure_ratio,
            "paper_return_ratio": row.return_ratio,
        }
    return PaperForecastEvidenceObservation(
        observed_at=observation.observed_at,
        source_packet_id=observation.source_packet_id,
        condition_id=trade.condition_id,
        token_id=trade.token_id,
        market_slug=trade.market_slug,
        strategy_type=trade.strategy_type,
        risk_tags=trade.risk_tags,
        predicted_probability=row.predicted_probability,
        actual_outcome_value=row.actual_outcome_value,
        **edge_values,
    )


def _normalize_trade_records(
    trade_records: Iterable[PaperTradeRecord],
) -> tuple[PaperTradeRecord, ...]:
    if isinstance(trade_records, (str, bytes)):
        raise ValueError("trade_records must be an iterable of PaperTradeRecord values")
    try:
        trades = tuple(trade_records)
    except TypeError as exc:
        raise ValueError(
            "trade_records must be an iterable of PaperTradeRecord values",
        ) from exc
    seen_keys: set[tuple[str, str]] = set()
    for trade in trades:
        if type(trade) is not PaperTradeRecord:
            raise ValueError("trade_records must contain only PaperTradeRecord values")
        _validate_trade_record(trade)
        seen_keys.add(_join_key_for_trade(trade))
    return trades


def _validate_trade_record(trade: PaperTradeRecord) -> None:
    for field_name in (
        "packet_id",
        "condition_id",
        "token_id",
        "market_slug",
        "outcome_name",
        "strategy_type",
    ):
        _require_canonical_string(field_name, getattr(trade, field_name))
    _as_utc(trade.decision_timestamp_utc)
    if trade.order_side not in ("buy", "sell"):
        raise ValueError("order_side must be buy or sell")
    _require_positive_decimal("order_requested_size", trade.order_requested_size)
    _require_positive_decimal("fill_filled_size", trade.fill_filled_size)
    _require_nonnegative_decimal("fill_unfilled_size", trade.fill_unfilled_size)
    if trade.fill_filled_size + trade.fill_unfilled_size != trade.order_requested_size:
        raise ValueError("fill accounting must match requested size")
    _require_probability_decimal("fill_average_price", trade.fill_average_price)
    _require_probability_decimal(
        "research_fair_value_estimate",
        trade.research_fair_value_estimate,
    )
    _require_decimal("research_theoretical_edge", trade.research_theoretical_edge)
    _require_decimal("research_cost_adjusted_edge", trade.research_cost_adjusted_edge)


def _normalize_outcome_observations(
    outcome_report: OutcomeTrackingReport | None,
) -> tuple[PaperForecastEvidenceObservation, ...]:
    if outcome_report is None:
        return ()
    observations = tuple(outcome_report.observations)
    for observation in observations:
        if type(observation) is not PaperForecastEvidenceObservation:
            raise ValueError(
                "outcome_report observations must contain PaperForecastEvidenceObservation values",
            )
        if observation.paper_only is not True:
            raise ValueError("outcome_report observations must be paper_only")
    return observations


def _validate_outcome_report_flags(outcome_report: OutcomeTrackingReport) -> None:
    if outcome_report.paper_only is not True:
        raise ValueError("outcome_report must be paper_only")
    if outcome_report.report_only is not True:
        raise ValueError("outcome_report must be report_only")
    if outcome_report.readonly is not True:
        raise ValueError("outcome_report must be readonly")


def _trade_keys(
    trades: tuple[PaperTradeRecord, ...],
) -> set[tuple[str, str]]:
    return {_join_key_for_trade(trade) for trade in trades}


def _duplicate_trade_keys(
    trades: tuple[PaperTradeRecord, ...],
) -> set[tuple[str, str]]:
    seen_keys: set[tuple[str, str]] = set()
    duplicate_keys: set[tuple[str, str]] = set()
    for trade in trades:
        key = _join_key_for_trade(trade)
        if key in seen_keys:
            duplicate_keys.add(key)
        seen_keys.add(key)
    return duplicate_keys


def _outcome_report_has_trade_set_mismatch(
    *,
    outcome_report: OutcomeTrackingReport | None,
    trade_count: int,
    unmatched_outcome_count: int,
) -> bool:
    if outcome_report is None or trade_count == 0:
        return False
    return (
        outcome_report.total_markets_checked != trade_count
        or unmatched_outcome_count > 0
    )


def _observations_by_join_key(
    observations: tuple[PaperForecastEvidenceObservation, ...],
) -> dict[tuple[str, str], tuple[PaperForecastEvidenceObservation, ...]]:
    grouped: dict[tuple[str, str], list[PaperForecastEvidenceObservation]] = {}
    for observation in observations:
        grouped.setdefault(_join_key_for_observation(observation), []).append(observation)
    return {key: tuple(values) for key, values in grouped.items()}


def _join_key_for_trade(trade: PaperTradeRecord) -> tuple[str, str]:
    return (trade.packet_id, trade.token_id)


def _join_key_for_observation(
    observation: PaperForecastEvidenceObservation,
) -> tuple[str, str]:
    return (observation.source_packet_id, observation.token_id)


def _observation_identity_matches_trade(
    observation: PaperForecastEvidenceObservation,
    trade: PaperTradeRecord,
) -> bool:
    return (
        observation.condition_id == trade.condition_id
        and observation.market_slug == trade.market_slug
        and observation.strategy_type == trade.strategy_type
        and observation.predicted_probability == trade.research_fair_value_estimate
    )


def _entry_notional(trade: PaperTradeRecord) -> Decimal:
    return trade.fill_filled_size * trade.fill_average_price


def _probability_loss(predicted: Decimal, actual: Decimal) -> Decimal:
    return _quantize_ratio((predicted - actual) ** 2)


def _positive_edge_hit_rate(
    observed_rows: tuple[PaperTradeSettlementValidationRow, ...],
) -> Decimal | None:
    positive_edge_rows = tuple(
        row for row in observed_rows if row.cost_adjusted_edge > ZERO
    )
    if not positive_edge_rows:
        return None
    return _rate(
        sum(
            1
            for row in positive_edge_rows
            if row.return_ratio is not None and row.return_ratio > ZERO
        ),
        len(positive_edge_rows),
    )


def _report_status(
    *,
    trade_count: int,
    resolved_count: int,
    quality_flag_count: int,
    duplicate_outcome_count: int,
    unmatched_outcome_count: int,
    min_resolved_trades: int,
) -> str:
    if trade_count == 0 and duplicate_outcome_count == 0 and unmatched_outcome_count == 0:
        return "empty"
    if (
        quality_flag_count > 0
        or duplicate_outcome_count > 0
        or unmatched_outcome_count > 0
    ):
        return "quality_flags"
    if resolved_count == 0:
        return "pending"
    if resolved_count < min_resolved_trades:
        return "insufficient_sample"
    return "observed"


def _rate(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return _quantize_ratio(Decimal(numerator) / Decimal(denominator))


def _mean_optional(values: Iterable[Decimal | None]) -> Decimal | None:
    items = tuple(item for item in values if item is not None)
    if not items:
        return None
    return _quantize_ratio(sum(items, ZERO) / Decimal(len(items)))


def _optional_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator <= ZERO:
        return None
    return _quantize_ratio(numerator / denominator)


def _quantize_ratio(value: Decimal) -> Decimal:
    _require_decimal("ratio", value)
    return value.quantize(RATIO_QUANTUM)


def _validate_row_consistency(row: PaperTradeSettlementValidationRow) -> None:
    if row.status == "observed":
        for field_name in (
            "source_packet_id",
            "settlement_payout",
            "realized_pnl",
            "predicted_probability",
            "actual_outcome_value",
            "probability_loss",
        ):
            if getattr(row, field_name) is None:
                raise ValueError(f"{field_name} is required for observed rows")
        if row.reason_codes != ("settlement_observed",):
            raise ValueError("observed rows must use the settlement_observed reason code")
        return
    for field_name in (
        "settlement_payout",
        "realized_pnl",
        "return_ratio",
        "predicted_probability",
        "actual_outcome_value",
        "probability_loss",
    ):
        if getattr(row, field_name) is not None:
            raise ValueError(f"{field_name} must be absent for unresolved rows")
    if row.status == "pending" and row.reason_codes != ("outcome_pending",):
        raise ValueError("pending rows must use the outcome_pending reason code")
    if row.status == "quality_flags" and not row.reason_codes:
        raise ValueError("quality flag rows must include a reason code")


def _validate_report_consistency(report: PaperTradeSettlementValidationReport) -> None:
    if report.row_count != len(report.rows):
        raise ValueError("row_count must equal rows length")
    if report.trade_count != report.row_count:
        raise ValueError("trade_count must equal row_count")
    resolved_count = sum(1 for row in report.rows if row.status == "observed")
    pending_count = sum(1 for row in report.rows if row.status == "pending")
    quality_flag_count = sum(
        1 for row in report.rows if row.status == "quality_flags"
    )
    if report.resolved_count != resolved_count:
        raise ValueError("resolved_count must equal observed row count")
    if report.pending_count != pending_count:
        raise ValueError("pending_count must equal pending row count")
    if report.quality_flag_count != quality_flag_count:
        raise ValueError("quality_flag_count must equal quality flag row count")
    if report.total_entry_notional != sum(
        (row.entry_notional for row in report.rows),
        ZERO,
    ):
        raise ValueError("total_entry_notional must equal summed row entry notional")
    if report.total_settlement_payout != sum(
        (row.settlement_payout for row in report.rows if row.settlement_payout is not None),
        ZERO,
    ):
        raise ValueError("total_settlement_payout must equal summed row payout")
    if report.total_realized_pnl != sum(
        (row.realized_pnl for row in report.rows if row.realized_pnl is not None),
        ZERO,
    ):
        raise ValueError("total_realized_pnl must equal summed row realized pnl")
    if report.trade_count == 0:
        _require_none("first_trade_decision_at", report.first_trade_decision_at)
        _require_none("latest_trade_decision_at", report.latest_trade_decision_at)
    if report.outcome_observation_count == 0:
        _require_none("first_observed_at", report.first_observed_at)
        _require_none("latest_observed_at", report.latest_observed_at)
    if report.resolved_count == 0 and report.forecast_evidence_report is not None:
        raise ValueError(
            "forecast_evidence_report must be None when there are no resolved rows",
        )
    if report.resolved_count > 0:
        if report.forecast_evidence_report is None:
            raise ValueError(
                "forecast_evidence_report is required when rows are resolved",
            )
        if report.forecast_evidence_report.observation_count != report.resolved_count:
            raise ValueError("forecast_evidence_report must match resolved rows")
    _validate_report_status_matches_counts(report)


def _validate_report_status_matches_counts(
    report: PaperTradeSettlementValidationReport,
) -> None:
    if (
        report.trade_count == 0
        and report.duplicate_outcome_count == 0
        and report.unmatched_outcome_count == 0
    ):
        expected_statuses = ("empty",)
    elif (
        report.quality_flag_count > 0
        or report.duplicate_outcome_count > 0
        or report.unmatched_outcome_count > 0
    ):
        expected_statuses = ("quality_flags",)
    elif report.resolved_count == 0:
        expected_statuses = ("pending",)
    else:
        expected_statuses = ("insufficient_sample", "observed")
    if report.status not in expected_statuses:
        raise ValueError("status must match report counts")


def _normalize_rows(
    rows: Iterable[PaperTradeSettlementValidationRow],
) -> tuple[PaperTradeSettlementValidationRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in items:
        if type(row) is not PaperTradeSettlementValidationRow:
            raise ValueError(
                "rows must contain PaperTradeSettlementValidationRow values",
            )
    return items


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for item in items:
        _require_canonical_string("reason_codes", item)
    return tuple(sorted(set(items)))


def _validate_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime or None")
    return _as_utc(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_positive_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is not None:
        _require_decimal(field_name, value)


def _require_optional_nonnegative_decimal(field_name: str, value: object) -> None:
    if value is not None:
        _require_nonnegative_decimal(field_name, value)


def _require_probability_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_optional_probability_decimal(field_name: str, value: object) -> None:
    if value is not None:
        _require_probability_decimal(field_name, value)


def _require_zero_one_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value not in (ZERO, ONE):
        raise ValueError(f"{field_name} must be 0 or 1")


def _require_none(field_name: str, value: object) -> None:
    if value is not None:
        raise ValueError(f"{field_name} must be None")
