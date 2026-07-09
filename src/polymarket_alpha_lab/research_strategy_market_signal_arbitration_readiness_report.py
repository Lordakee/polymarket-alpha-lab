"""Report-only market signal arbitration readiness reducer."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MARKET_SIGNAL_ARBITRATION_READINESS_CONFIG_VERSION",
    "ResearchStrategyMarketSignalArbitrationInput",
    "ResearchStrategyMarketSignalArbitrationReadinessConfig",
    "ResearchStrategyMarketSignalArbitrationReadinessReport",
    "ResearchStrategyMarketSignalArbitrationReadinessRow",
    "build_research_strategy_market_signal_arbitration_readiness_report",
    "research_strategy_market_signal_arbitration_readiness_report_digest",
    "research_strategy_market_signal_arbitration_readiness_report_public_payload",
)


DEFAULT_RESEARCH_STRATEGY_MARKET_SIGNAL_ARBITRATION_READINESS_CONFIG_VERSION = (
    "research-strategy-market-signal-arbitration-readiness-report-v1"
)

_COUNT_QUANTUM = Decimal("1")
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_THREE = Decimal("3.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_STATUSES = ("pass", "watch", "block")
_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "signal_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_arbitration_score",
        "max_disagreement_pressure",
        "max_cost_pressure",
        "report_status",
        "reason_codes",
        "rows",
        "public_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_KEYS = frozenset(
    (
        "signal_ref",
        "observed_at",
        "model_probability",
        "team_consensus_probability",
        "source_confidence",
        "market_implied_probability",
        "fee_pressure",
        "spread_pressure",
        "slippage_pressure",
        "model_team_gap",
        "model_market_gap",
        "team_market_gap",
        "disagreement_pressure",
        "cost_pressure",
        "arbitration_score",
        "status",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_STATUS_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_BLOCK_REASONS = frozenset(
    (
        "disagreement_pressure_block",
        "source_confidence_block",
        "cost_pressure_block",
        "arbitration_score_block",
    ),
)
_PASS_REASON = "arbitration_readiness_pass"
_EMPTY_REASON = "arbitration_readiness_empty"
_REASON_PRIORITY = (
    "disagreement_pressure_block",
    "source_confidence_block",
    "cost_pressure_block",
    "arbitration_score_block",
    "disagreement_pressure_watch",
    "source_confidence_watch",
    "cost_pressure_watch",
    "arbitration_score_watch",
    _PASS_REASON,
    _EMPTY_REASON,
)
_HEX_CHARS = frozenset("0123456789abcdef")


def _join(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_TEXT_FRAGMENTS = (
    _join("raw", "_candidate", "_id"),
    _join("candidate", "_id"),
    _join("market", "_id"),
    _join("market", "_slug"),
    _join("ques", "tion"),
    _join("source", "_url"),
    _join("source", "_text"),
    _join("http", "://"),
    _join("https", "://"),
    _join("postgres", "://"),
    _join("d", "sn"),
    _join("table", "_name"),
    _join("tok", "en"),
    _join("wallet"),
    _join("order"),
    _join("trade"),
    _join("trading"),
    _join("live"),
    _join("position"),
    _join("sizing"),
    _join("recommend"),
    _join("auth"),
    _join("secret"),
    _join("api", "_key"),
    _join("private", "_key"),
)


@dataclass(frozen=True)
class ResearchStrategyMarketSignalArbitrationReadinessConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MARKET_SIGNAL_ARBITRATION_READINESS_CONFIG_VERSION
    )
    agreement_weight: Decimal = Decimal("0.400000")
    source_confidence_weight: Decimal = Decimal("0.300000")
    cost_clearance_weight: Decimal = Decimal("0.300000")
    pass_disagreement_ceiling: Decimal = Decimal("0.080000")
    block_disagreement_floor: Decimal = Decimal("0.250000")
    pass_source_confidence_floor: Decimal = Decimal("0.700000")
    block_source_confidence_ceiling: Decimal = Decimal("0.450000")
    pass_cost_pressure_ceiling: Decimal = Decimal("0.150000")
    block_cost_pressure_floor: Decimal = Decimal("0.450000")
    pass_score_floor: Decimal = Decimal("0.750000")
    watch_score_floor: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketSignalArbitrationReadinessConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MARKET_SIGNAL_ARBITRATION_READINESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "agreement_weight",
            "source_confidence_weight",
            "cost_clearance_weight",
            "pass_disagreement_ceiling",
            "block_disagreement_floor",
            "pass_source_confidence_floor",
            "block_source_confidence_ceiling",
            "pass_cost_pressure_ceiling",
            "block_cost_pressure_floor",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "agreement_weight",
            "source_confidence_weight",
            "cost_clearance_weight",
        ):
            if getattr(self, field_name) <= _ZERO:
                raise ValueError(f"{field_name} must be positive")
        if _quantize(
            self.agreement_weight
            + self.source_confidence_weight
            + self.cost_clearance_weight,
        ) != _ONE:
            raise ValueError("weights must sum to 1.000000")
        if self.pass_disagreement_ceiling >= self.block_disagreement_floor:
            raise ValueError(
                "pass_disagreement_ceiling must be less than block_disagreement_floor",
            )
        if self.block_source_confidence_ceiling >= self.pass_source_confidence_floor:
            raise ValueError(
                "block_source_confidence_ceiling must be less than "
                "pass_source_confidence_floor",
            )
        if self.pass_cost_pressure_ceiling >= self.block_cost_pressure_floor:
            raise ValueError(
                "pass_cost_pressure_ceiling must be less than block_cost_pressure_floor",
            )
        if self.pass_score_floor < self.watch_score_floor:
            raise ValueError("pass_score_floor must be at least watch_score_floor")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyMarketSignalArbitrationInput:
    signal_ref: str
    model_probability: Decimal
    team_consensus_probability: Decimal
    source_confidence: Decimal
    market_implied_probability: Decimal
    fee_pressure: Decimal
    spread_pressure: Decimal
    slippage_pressure: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMarketSignalArbitrationInput, "input")
        _require_public_text("signal_ref", self.signal_ref)
        for field_name in (
            "model_probability",
            "team_consensus_probability",
            "source_confidence",
            "market_implied_probability",
            "fee_pressure",
            "spread_pressure",
            "slippage_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyMarketSignalArbitrationReadinessRow:
    signal_ref: str
    observed_at: datetime
    model_probability: Decimal
    team_consensus_probability: Decimal
    source_confidence: Decimal
    market_implied_probability: Decimal
    fee_pressure: Decimal
    spread_pressure: Decimal
    slippage_pressure: Decimal
    model_team_gap: Decimal
    model_market_gap: Decimal
    team_market_gap: Decimal
    disagreement_pressure: Decimal
    cost_pressure: Decimal
    arbitration_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketSignalArbitrationReadinessRow,
            "row",
        )
        _require_public_text("signal_ref", self.signal_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "team_consensus_probability",
            "source_confidence",
            "market_implied_probability",
            "fee_pressure",
            "spread_pressure",
            "slippage_pressure",
            "model_team_gap",
            "model_market_gap",
            "team_market_gap",
            "disagreement_pressure",
            "cost_pressure",
            "arbitration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyMarketSignalArbitrationReadinessReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_arbitration_score: Decimal
    max_disagreement_pressure: Decimal
    max_cost_pressure: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyMarketSignalArbitrationReadinessRow, ...]
    public_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketSignalArbitrationReadinessReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "signal_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_arbitration_score",
            "max_disagreement_pressure",
            "max_cost_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("public_digest", self.public_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)


def build_research_strategy_market_signal_arbitration_readiness_report(
    signals: Iterable[ResearchStrategyMarketSignalArbitrationInput],
    *,
    config: ResearchStrategyMarketSignalArbitrationReadinessConfig,
    generated_at: datetime,
) -> ResearchStrategyMarketSignalArbitrationReadinessReport:
    if type(config) is not ResearchStrategyMarketSignalArbitrationReadinessConfig:
        raise ValueError(
            "config must be a ResearchStrategyMarketSignalArbitrationReadinessConfig",
        )
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_inputs(signals)
    for item in normalized_signals:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at values must be at or before generated_at")
    rows = tuple(
        sorted(
            (_row_from_signal(item, config=config) for item in normalized_signals),
            key=_row_sort_key,
        ),
    )
    report_values = _report_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    return ResearchStrategyMarketSignalArbitrationReadinessReport(
        **report_values,
        public_digest=_digest_from_mapping(report_values),
    )


def research_strategy_market_signal_arbitration_readiness_report_digest(
    report: ResearchStrategyMarketSignalArbitrationReadinessReport,
) -> str:
    if type(report) is not ResearchStrategyMarketSignalArbitrationReadinessReport:
        raise ValueError(
            "report must be a ResearchStrategyMarketSignalArbitrationReadinessReport",
        )
    _validate_report(report)
    return _computed_report_digest(report)


def research_strategy_market_signal_arbitration_readiness_report_public_payload(
    report: ResearchStrategyMarketSignalArbitrationReadinessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyMarketSignalArbitrationReadinessReport:
        _validate_report(report)
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyMarketSignalArbitrationReadinessReport",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_flags("payload", payload)
    _validate_public_payload(payload)
    return payload


def _normalize_inputs(
    signals: Iterable[ResearchStrategyMarketSignalArbitrationInput],
) -> tuple[ResearchStrategyMarketSignalArbitrationInput, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        rows = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyMarketSignalArbitrationInput:
            raise ValueError(
                "signals must contain ResearchStrategyMarketSignalArbitrationInput",
            )
        _require_hard_flags("input", row)
        _reject_unsafe_public_payload("input", row)
        if row.signal_ref in seen_refs:
            raise ValueError("signal_ref values must be unique")
        seen_refs.add(row.signal_ref)
    return rows


def _row_from_signal(
    signal: ResearchStrategyMarketSignalArbitrationInput,
    *,
    config: ResearchStrategyMarketSignalArbitrationReadinessConfig,
) -> ResearchStrategyMarketSignalArbitrationReadinessRow:
    model_team_gap = _absolute_gap(
        signal.model_probability,
        signal.team_consensus_probability,
    )
    model_market_gap = _absolute_gap(
        signal.model_probability,
        signal.market_implied_probability,
    )
    team_market_gap = _absolute_gap(
        signal.team_consensus_probability,
        signal.market_implied_probability,
    )
    disagreement_pressure = max(model_team_gap, model_market_gap, team_market_gap)
    cost_pressure = _ratio(
        signal.fee_pressure + signal.spread_pressure + signal.slippage_pressure,
        _THREE,
    )
    arbitration_score = _arbitration_score(
        disagreement_pressure=disagreement_pressure,
        source_confidence=signal.source_confidence,
        cost_pressure=cost_pressure,
        config=config,
    )
    reason_codes = _row_reason_codes(
        disagreement_pressure=disagreement_pressure,
        source_confidence=signal.source_confidence,
        cost_pressure=cost_pressure,
        arbitration_score=arbitration_score,
        config=config,
    )
    row_values = {
        "signal_ref": signal.signal_ref,
        "observed_at": signal.observed_at,
        "model_probability": signal.model_probability,
        "team_consensus_probability": signal.team_consensus_probability,
        "source_confidence": signal.source_confidence,
        "market_implied_probability": signal.market_implied_probability,
        "fee_pressure": signal.fee_pressure,
        "spread_pressure": signal.spread_pressure,
        "slippage_pressure": signal.slippage_pressure,
        "model_team_gap": model_team_gap,
        "model_market_gap": model_market_gap,
        "team_market_gap": team_market_gap,
        "disagreement_pressure": disagreement_pressure,
        "cost_pressure": cost_pressure,
        "arbitration_score": arbitration_score,
        "status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyMarketSignalArbitrationReadinessRow(
        **row_values,
        validation_digest=_digest_from_mapping(row_values),
    )


def _row_reason_codes(
    *,
    disagreement_pressure: Decimal,
    source_confidence: Decimal,
    cost_pressure: Decimal,
    arbitration_score: Decimal,
    config: ResearchStrategyMarketSignalArbitrationReadinessConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if disagreement_pressure >= config.block_disagreement_floor:
        block_reasons.append("disagreement_pressure_block")
    elif disagreement_pressure > config.pass_disagreement_ceiling:
        watch_reasons.append("disagreement_pressure_watch")
    if source_confidence <= config.block_source_confidence_ceiling:
        block_reasons.append("source_confidence_block")
    elif source_confidence < config.pass_source_confidence_floor:
        watch_reasons.append("source_confidence_watch")
    if cost_pressure >= config.block_cost_pressure_floor:
        block_reasons.append("cost_pressure_block")
    elif cost_pressure > config.pass_cost_pressure_ceiling:
        watch_reasons.append("cost_pressure_watch")
    if arbitration_score < config.watch_score_floor:
        block_reasons.append("arbitration_score_block")
    elif arbitration_score < config.pass_score_floor:
        watch_reasons.append("arbitration_score_watch")
    reason_codes = tuple(block_reasons + watch_reasons)
    if not reason_codes:
        reason_codes = (_PASS_REASON,)
    return _normalize_row_reason_codes("reason_codes", reason_codes)


def _arbitration_score(
    *,
    disagreement_pressure: Decimal,
    source_confidence: Decimal,
    cost_pressure: Decimal,
    config: ResearchStrategyMarketSignalArbitrationReadinessConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            (config.agreement_weight * (_ONE - disagreement_pressure))
            + (config.source_confidence_weight * source_confidence)
            + (config.cost_clearance_weight * (_ONE - cost_pressure)),
        )


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchStrategyMarketSignalArbitrationReadinessRow, ...],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "signal_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "mean_arbitration_score": _mean(
            tuple(row.arbitration_score for row in rows),
        ),
        "max_disagreement_pressure": _max_decimal(
            tuple(row.disagreement_pressure for row in rows),
        ),
        "max_cost_pressure": _max_decimal(tuple(row.cost_pressure for row in rows)),
        "report_status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_row(
    row: ResearchStrategyMarketSignalArbitrationReadinessRow,
) -> None:
    if row.model_team_gap != _absolute_gap(
        row.model_probability,
        row.team_consensus_probability,
    ):
        raise ValueError("model_team_gap must match probabilities")
    if row.model_market_gap != _absolute_gap(
        row.model_probability,
        row.market_implied_probability,
    ):
        raise ValueError("model_market_gap must match probabilities")
    if row.team_market_gap != _absolute_gap(
        row.team_consensus_probability,
        row.market_implied_probability,
    ):
        raise ValueError("team_market_gap must match probabilities")
    if row.disagreement_pressure != max(
        row.model_team_gap,
        row.model_market_gap,
        row.team_market_gap,
    ):
        raise ValueError("disagreement_pressure must match probability gaps")
    if row.cost_pressure != _ratio(
        row.fee_pressure + row.spread_pressure + row.slippage_pressure,
        _THREE,
    ):
        raise ValueError("cost_pressure must match fee spread slippage pressure")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.validation_digest != _digest_from_mapping(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_report(
    report: ResearchStrategyMarketSignalArbitrationReadinessReport,
) -> None:
    if report.signal_count != _count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_arbitration_score != _mean(
        tuple(row.arbitration_score for row in report.rows),
    ):
        raise ValueError("mean_arbitration_score must match rows")
    if report.max_disagreement_pressure != _max_decimal(
        tuple(row.disagreement_pressure for row in report.rows),
    ):
        raise ValueError("max_disagreement_pressure must match rows")
    if report.max_cost_pressure != _max_decimal(
        tuple(row.cost_pressure for row in report.rows),
    ):
        raise ValueError("max_cost_pressure must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.public_digest != _computed_report_digest(report):
        raise ValueError("public_digest must match report payload")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _require_exact_public_keys(
        "public payload",
        payload,
        _PAYLOAD_KEYS,
        "unexpected public payload keys",
    )
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list in public payload")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain objects in public payload")
        _require_exact_public_keys(
            "public row",
            row,
            _ROW_PAYLOAD_KEYS,
            "unexpected public row keys",
        )
        supplied_row_digest = row.get("validation_digest")
        _require_digest("validation_digest", supplied_row_digest)
        if supplied_row_digest != _payload_row_digest(row):
            raise ValueError("validation_digest must match row payload")
    supplied_digest = payload.get("public_digest")
    _require_digest("public_digest", supplied_digest)
    if supplied_digest != _payload_report_digest(payload):
        raise ValueError("public_digest must match public payload")
    ResearchStrategyMarketSignalArbitrationReadinessReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        signal_count=_payload_count("signal_count", payload["signal_count"]),
        pass_count=_payload_count("pass_count", payload["pass_count"]),
        watch_count=_payload_count("watch_count", payload["watch_count"]),
        block_count=_payload_count("block_count", payload["block_count"]),
        mean_arbitration_score=_payload_unit_decimal(
            "mean_arbitration_score",
            payload["mean_arbitration_score"],
        ),
        max_disagreement_pressure=_payload_unit_decimal(
            "max_disagreement_pressure",
            payload["max_disagreement_pressure"],
        ),
        max_cost_pressure=_payload_unit_decimal(
            "max_cost_pressure",
            payload["max_cost_pressure"],
        ),
        report_status=payload["report_status"],
        reason_codes=_payload_reason_codes("reason_codes", payload["reason_codes"]),
        rows=tuple(_payload_row(row) for row in rows),
        public_digest=payload["public_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _require_exact_public_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: frozenset[str],
    error_message: str,
) -> None:
    actual_keys = frozenset(value)
    if actual_keys != expected_keys:
        raise ValueError(error_message)


def _payload_row(
    row: dict[str, Any],
) -> ResearchStrategyMarketSignalArbitrationReadinessRow:
    return ResearchStrategyMarketSignalArbitrationReadinessRow(
        signal_ref=row["signal_ref"],
        observed_at=_payload_datetime("observed_at", row["observed_at"]),
        model_probability=_payload_unit_decimal(
            "model_probability",
            row["model_probability"],
        ),
        team_consensus_probability=_payload_unit_decimal(
            "team_consensus_probability",
            row["team_consensus_probability"],
        ),
        source_confidence=_payload_unit_decimal(
            "source_confidence",
            row["source_confidence"],
        ),
        market_implied_probability=_payload_unit_decimal(
            "market_implied_probability",
            row["market_implied_probability"],
        ),
        fee_pressure=_payload_unit_decimal("fee_pressure", row["fee_pressure"]),
        spread_pressure=_payload_unit_decimal(
            "spread_pressure",
            row["spread_pressure"],
        ),
        slippage_pressure=_payload_unit_decimal(
            "slippage_pressure",
            row["slippage_pressure"],
        ),
        model_team_gap=_payload_unit_decimal("model_team_gap", row["model_team_gap"]),
        model_market_gap=_payload_unit_decimal(
            "model_market_gap",
            row["model_market_gap"],
        ),
        team_market_gap=_payload_unit_decimal("team_market_gap", row["team_market_gap"]),
        disagreement_pressure=_payload_unit_decimal(
            "disagreement_pressure",
            row["disagreement_pressure"],
        ),
        cost_pressure=_payload_unit_decimal("cost_pressure", row["cost_pressure"]),
        arbitration_score=_payload_unit_decimal(
            "arbitration_score",
            row["arbitration_score"],
        ),
        status=row["status"],
        reason_codes=_payload_reason_codes("reason_codes", row["reason_codes"]),
        validation_digest=row["validation_digest"],
        paper_only=row["paper_only"],
        report_only=row["report_only"],
        readonly=row["readonly"],
    )


def _payload_count(name: str, value: object) -> Decimal:
    return _normalize_nonnegative_count(name, _payload_decimal(name, value))


def _payload_unit_decimal(name: str, value: object) -> Decimal:
    return _normalize_unit_decimal(name, _payload_decimal(name, value))


def _payload_decimal(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string in public payload")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a Decimal string in public payload") from exc
    return _normalize_decimal(name, parsed)


def _payload_datetime(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be an ISO datetime string in public payload")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string in public payload") from exc
    return _as_utc(name, parsed)


def _payload_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list in public payload")
    return _normalize_public_reason_codes(name, tuple(value))


def _row_digest_values(
    row: ResearchStrategyMarketSignalArbitrationReadinessRow,
) -> dict[str, Any]:
    return {
        "signal_ref": row.signal_ref,
        "observed_at": row.observed_at,
        "model_probability": row.model_probability,
        "team_consensus_probability": row.team_consensus_probability,
        "source_confidence": row.source_confidence,
        "market_implied_probability": row.market_implied_probability,
        "fee_pressure": row.fee_pressure,
        "spread_pressure": row.spread_pressure,
        "slippage_pressure": row.slippage_pressure,
        "model_team_gap": row.model_team_gap,
        "model_market_gap": row.model_market_gap,
        "team_market_gap": row.team_market_gap,
        "disagreement_pressure": row.disagreement_pressure,
        "cost_pressure": row.cost_pressure,
        "arbitration_score": row.arbitration_score,
        "status": row.status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_values(
    report: ResearchStrategyMarketSignalArbitrationReadinessReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "signal_count": report.signal_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "mean_arbitration_score": report.mean_arbitration_score,
        "max_disagreement_pressure": report.max_disagreement_pressure,
        "max_cost_pressure": report.max_cost_pressure,
        "report_status": report.report_status,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _computed_report_digest(
    report: ResearchStrategyMarketSignalArbitrationReadinessReport,
) -> str:
    return _digest_from_mapping(_report_digest_values(report))


def _payload_row_digest(row: dict[str, Any]) -> str:
    values = {key: item for key, item in row.items() if key != "validation_digest"}
    return _digest_from_mapping(values)


def _payload_report_digest(payload: dict[str, Any]) -> str:
    values = {key: item for key, item in payload.items() if key != "public_digest"}
    return _digest_from_mapping(values)


def _digest_from_mapping(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        _require_aware_datetime("JSON datetime value", value)
        return value.astimezone(UTC).isoformat()
    if value is None or type(value) is bool:
        return value
    if type(value) is str:
        _require_public_text("JSON string value", value)
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal strings")
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyMarketSignalArbitrationReadinessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyMarketSignalArbitrationReadinessRow:
            raise ValueError(
                "rows must contain ResearchStrategyMarketSignalArbitrationReadinessRow",
            )
        _require_hard_flags("row", row)
        if row.signal_ref in seen_refs:
            raise ValueError("rows must not contain duplicate signal_ref values")
        seen_refs.add(row.signal_ref)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return normalized


def _row_sort_key(
    row: ResearchStrategyMarketSignalArbitrationReadinessRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        _STATUS_WEIGHT[row.status],
        -row.disagreement_pressure,
        -row.cost_pressure,
        row.signal_ref,
    )


def _status_count(
    rows: tuple[ResearchStrategyMarketSignalArbitrationReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _report_status(
    rows: tuple[ResearchStrategyMarketSignalArbitrationReadinessRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyMarketSignalArbitrationReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    return _normalize_report_reason_codes(
        "reason_codes",
        tuple(reason for row in rows for reason in row.reason_codes),
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reason_codes):
        return "block"
    if reason_codes == (_PASS_REASON,):
        return "pass"
    return "watch"


def _normalize_row_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if codes == (_PASS_REASON,):
        return codes
    if _PASS_REASON in codes:
        raise ValueError(f"{name} pass reason must stand alone")
    if _EMPTY_REASON in codes:
        raise ValueError(f"{name} empty reason is report-only")
    return codes


def _normalize_report_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if codes == (_EMPTY_REASON,):
        return codes
    if _EMPTY_REASON in codes:
        raise ValueError(f"{name} empty reason must stand alone")
    return codes


def _normalize_public_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    for code in codes:
        _require_public_text(name, code)
        compact_code = "".join(part for part in code if part != "_")
        if not compact_code.isalnum() or code.lower() != code:
            raise ValueError(f"{name} must contain lowercase snake case values")
    if len(frozenset(codes)) != len(codes):
        raise ValueError(f"{name} must be unique")
    return tuple(sorted(dict.fromkeys(codes), key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in _REASON_PRIORITY:
        return (_REASON_PRIORITY.index(reason_code), reason_code)
    return (len(_REASON_PRIORITY), reason_code)


def _absolute_gap(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(abs(left - right))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _ratio(_sum_decimal(values), Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(max(values))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    for value in values:
        total += _normalize_decimal("sum value", value)
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return normalized.quantize(_COUNT_QUANTUM)


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    _require_aware_datetime(name, value)
    return value.astimezone(UTC)


def _require_aware_datetime(name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in _STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_public_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{name} must be single-line text")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{name} contains unsafe public text")
    if _looks_like_raw_identifier(value):
        raise ValueError(f"{name} contains raw identifier")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError(f"{name} must be a SHA-256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in _FLAG_NAMES:
        if payload.get(field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{label} contains unsafe public value")
        return
    if type(value) in (Decimal, datetime) or value is None or type(value) is bool:
        return
    if type(value) in (tuple, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"{label} contains unsafe public key")
            if key in _FLAG_NAMES and item is not True:
                raise ValueError(f"{key} must be True in payload")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if type(value) in (int, float):
        raise ValueError(f"{label} numeric values must use Decimal strings")
    raise ValueError(f"{label} has unknown public value")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    compact = "".join(char for char in normalized if char.isalnum())
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in normalized:
            return True
        compact_fragment = "".join(char for char in fragment if char.isalnum())
        if compact_fragment and compact_fragment in compact:
            return True
    return False


def _looks_like_raw_identifier(value: str) -> bool:
    normalized = value.lower()
    uuid_parts = normalized.split("-")
    if len(uuid_parts) == 5 and tuple(len(part) for part in uuid_parts) == (
        8,
        4,
        4,
        4,
        12,
    ):
        return all(part and set(part) <= _HEX_CHARS for part in uuid_parts)
    return len(normalized) == 32 and set(normalized) <= _HEX_CHARS
