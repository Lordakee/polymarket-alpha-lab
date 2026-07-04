"""Paper-only probability-event candidate selection gate reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256


__all__ = (
    "StrategyProbabilityEventSelectionGateDigestCandidate",
    "StrategyProbabilityEventSelectionGateDigestConfig",
    "StrategyProbabilityEventSelectionGateDigestReport",
    "StrategyProbabilityEventSelectionGateDigestRow",
    "build_strategy_probability_event_selection_gate_digest",
    "strategy_probability_event_selection_gate_digest_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-probability-event-selection-gate-digest-v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
SIDES = ("yes", "no")
ROW_STATUSES = ("select", "watch", "blocked")
REPORT_STATUSES = ("select", "watch", "blocked")
EMPTY_REASON_CODE = "event_selection_gate_digest_empty"
SELECT_REASON_CODE = "event_selection_selected"
WATCH_REASON_CODE = "event_selection_watch"
BLOCKED_REASON_CODE = "event_selection_blocked"
EVIDENCE_WATCH_REASON_CODE = "evidence_freshness_watch"
TEAM_MEMORY_CONFIDENCE_WATCH_REASON_CODE = "team_memory_confidence_watch"
TEAM_MEMORY_AGE_WATCH_REASON_CODE = "team_memory_freshness_watch"
TAKER_FEE_REASON_CODE = "taker_fee_cost_present"
SPREAD_REASON_CODE = "spread_cost_present"
SLIPPAGE_REASON_CODE = "slippage_cost_present"
EXTERNAL_BUFFER_REASON_CODE = "external_cost_buffer_present"
REPORT_REASON_PRIORITY = (
    "candidate_positive_edge",
    EVIDENCE_WATCH_REASON_CODE,
    BLOCKED_REASON_CODE,
    SELECT_REASON_CODE,
    WATCH_REASON_CODE,
    EXTERNAL_BUFFER_REASON_CODE,
    SPREAD_REASON_CODE,
    SLIPPAGE_REASON_CODE,
    TAKER_FEE_REASON_CODE,
    TEAM_MEMORY_CONFIDENCE_WATCH_REASON_CODE,
    TEAM_MEMORY_AGE_WATCH_REASON_CODE,
    EMPTY_REASON_CODE,
)
ROW_STATUS_SORT_PRIORITY = {"blocked": 0, "watch": 1, "select": 2}
SENSITIVE_REFERENCE_TOKENS = (
    "secret",
    "token",
    "private",
    "key",
    "bearer",
    "dsn",
    "password",
    "wallet",
)
UNSAFE_FIELD_FRAGMENTS = (
    "private_key",
    "exchange_mutation",
    "broker",
    "cancel",
    "replace",
    "sign",
)


@dataclass(frozen=True)
class StrategyProbabilityEventSelectionGateDigestConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_net_probability_edge: Decimal = Decimal("0.020000")
    watch_net_probability_edge: Decimal = Decimal("0.005000")
    taker_fee_rate: Decimal = Decimal("0.020000")
    max_evidence_age_seconds: Decimal = Decimal("1800.000000")
    max_team_memory_age_seconds: Decimal = Decimal("3600.000000")
    min_team_memory_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_net_probability_edge",
            "watch_net_probability_edge",
            "taker_fee_rate",
            "min_team_memory_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_evidence_age_seconds",
            "max_team_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_net_probability_edge > self.min_net_probability_edge:
            raise ValueError(
                "watch_net_probability_edge must not exceed min_net_probability_edge",
            )
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class StrategyProbabilityEventSelectionGateDigestCandidate:
    candidate_reference: str
    event_title: str
    side: str
    evaluated_at: datetime
    market_implied_probability: Decimal
    model_probability: Decimal
    spread_probability_cost: Decimal
    slippage_probability_cost: Decimal
    external_cost_buffer_probability: Decimal
    evidence_fresh_at: datetime
    team_memory_updated_at: datetime
    team_memory_confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_reference", self.candidate_reference)
        _require_canonical_string("event_title", self.event_title)
        _require_side("side", self.side)
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        object.__setattr__(
            self,
            "evidence_fresh_at",
            _as_utc("evidence_fresh_at", self.evidence_fresh_at),
        )
        object.__setattr__(
            self,
            "team_memory_updated_at",
            _as_utc("team_memory_updated_at", self.team_memory_updated_at),
        )
        for field_name in (
            "market_implied_probability",
            "model_probability",
            "team_memory_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_probability_cost",
            "slippage_probability_cost",
            "external_cost_buffer_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("candidate", self)


@dataclass(frozen=True)
class StrategyProbabilityEventSelectionGateDigestRow:
    redacted_candidate_reference: str
    event_title: str
    side: str
    evaluated_at: datetime
    market_implied_probability: Decimal
    model_probability: Decimal
    side_market_implied_probability: Decimal
    side_model_probability: Decimal
    gross_probability_edge: Decimal
    taker_fee_probability_cost: Decimal
    spread_probability_cost: Decimal
    slippage_probability_cost: Decimal
    external_cost_buffer_probability: Decimal
    total_probability_cost: Decimal
    net_probability_edge: Decimal
    required_edge_shortfall: Decimal
    evidence_fresh_at: datetime
    evidence_age_seconds: Decimal
    team_memory_updated_at: datetime
    team_memory_age_seconds: Decimal
    team_memory_confidence: Decimal
    selection_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string(
            "redacted_candidate_reference",
            self.redacted_candidate_reference,
        )
        _require_redacted_reference(self.redacted_candidate_reference)
        _require_canonical_string("event_title", self.event_title)
        _require_side("side", self.side)
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        object.__setattr__(
            self,
            "evidence_fresh_at",
            _as_utc("evidence_fresh_at", self.evidence_fresh_at),
        )
        object.__setattr__(
            self,
            "team_memory_updated_at",
            _as_utc("team_memory_updated_at", self.team_memory_updated_at),
        )
        for field_name in (
            "market_implied_probability",
            "model_probability",
            "side_market_implied_probability",
            "side_model_probability",
            "team_memory_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_probability_edge",
            "net_probability_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "taker_fee_probability_cost",
            "spread_probability_cost",
            "slippage_probability_cost",
            "external_cost_buffer_probability",
            "total_probability_cost",
            "required_edge_shortfall",
            "evidence_age_seconds",
            "team_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("selection_status", self.selection_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_safety_flags("row", self)


@dataclass(frozen=True)
class StrategyProbabilityEventSelectionGateDigestReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    select_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_net_probability_edge: Decimal
    max_required_edge_shortfall: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyProbabilityEventSelectionGateDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "select_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_net_probability_edge",
            "max_required_edge_shortfall",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_safety_flags("report", self)


def build_strategy_probability_event_selection_gate_digest(
    candidates: Iterable[object],
    *,
    config: StrategyProbabilityEventSelectionGateDigestConfig,
    generated_at: datetime,
) -> StrategyProbabilityEventSelectionGateDigestReport:
    if type(config) is not StrategyProbabilityEventSelectionGateDigestConfig:
        raise ValueError("config must be a StrategyProbabilityEventSelectionGateDigestConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_safety_flags("config", config)
    source_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    candidate,
                    config=config,
                    generated_at=generated_at,
                )
                for candidate in source_candidates
            ),
            key=_row_sort_key,
        ),
    )

    return StrategyProbabilityEventSelectionGateDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(rows)),
        select_count=_status_count(rows, "select"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        max_net_probability_edge=_max_net_probability_edge(rows),
        max_required_edge_shortfall=_max_required_edge_shortfall(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_probability_event_selection_gate_digest_payload(
    report: StrategyProbabilityEventSelectionGateDigestReport,
) -> dict[str, object]:
    if type(report) is not StrategyProbabilityEventSelectionGateDigestReport:
        raise ValueError(
            "report must be a StrategyProbabilityEventSelectionGateDigestReport",
        )
    _require_safety_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_count": _count_payload(report.candidate_count),
        "select_count": _count_payload(report.select_count),
        "watch_count": _count_payload(report.watch_count),
        "blocked_count": _count_payload(report.blocked_count),
        "max_net_probability_edge": _decimal_payload(report.max_net_probability_edge),
        "max_required_edge_shortfall": _decimal_payload(
            report.max_required_edge_shortfall,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: StrategyProbabilityEventSelectionGateDigestRow) -> dict[str, object]:
    _require_safety_flags("row", row)
    return {
        "redacted_candidate_reference": row.redacted_candidate_reference,
        "event_title": row.event_title,
        "side": row.side,
        "evaluated_at": row.evaluated_at.isoformat(),
        "market_implied_probability": _decimal_payload(row.market_implied_probability),
        "model_probability": _decimal_payload(row.model_probability),
        "side_market_implied_probability": _decimal_payload(
            row.side_market_implied_probability,
        ),
        "side_model_probability": _decimal_payload(row.side_model_probability),
        "gross_probability_edge": _decimal_payload(row.gross_probability_edge),
        "taker_fee_probability_cost": _decimal_payload(row.taker_fee_probability_cost),
        "spread_probability_cost": _decimal_payload(row.spread_probability_cost),
        "slippage_probability_cost": _decimal_payload(row.slippage_probability_cost),
        "external_cost_buffer_probability": _decimal_payload(
            row.external_cost_buffer_probability,
        ),
        "total_probability_cost": _decimal_payload(row.total_probability_cost),
        "net_probability_edge": _decimal_payload(row.net_probability_edge),
        "required_edge_shortfall": _decimal_payload(row.required_edge_shortfall),
        "evidence_fresh_at": row.evidence_fresh_at.isoformat(),
        "evidence_age_seconds": _count_payload(row.evidence_age_seconds),
        "team_memory_updated_at": row.team_memory_updated_at.isoformat(),
        "team_memory_age_seconds": _count_payload(row.team_memory_age_seconds),
        "team_memory_confidence": _decimal_payload(row.team_memory_confidence),
        "selection_status": row.selection_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_candidate(
    candidate: StrategyProbabilityEventSelectionGateDigestCandidate,
    *,
    config: StrategyProbabilityEventSelectionGateDigestConfig,
    generated_at: datetime,
) -> StrategyProbabilityEventSelectionGateDigestRow:
    _require_not_future("evaluated_at", candidate.evaluated_at, generated_at)
    _require_not_future("evidence_fresh_at", candidate.evidence_fresh_at, generated_at)
    _require_not_future(
        "team_memory_updated_at",
        candidate.team_memory_updated_at,
        generated_at,
    )
    side_market_implied_probability = _side_probability(
        candidate.side,
        candidate.market_implied_probability,
    )
    side_model_probability = _side_probability(
        candidate.side,
        candidate.model_probability,
    )
    gross_probability_edge = _subtract_decimal(
        side_model_probability,
        side_market_implied_probability,
    )
    taker_fee_probability_cost = _multiply_decimal(
        side_market_implied_probability,
        config.taker_fee_rate,
    )
    total_probability_cost = _add_decimal(
        taker_fee_probability_cost,
        candidate.spread_probability_cost,
        candidate.slippage_probability_cost,
        candidate.external_cost_buffer_probability,
    )
    net_probability_edge = _subtract_decimal(
        gross_probability_edge,
        total_probability_cost,
    )
    required_edge_shortfall = _max_decimal(
        _subtract_decimal(config.watch_net_probability_edge, net_probability_edge),
        ZERO,
    )
    evidence_age_seconds = _seconds_between(
        generated_at,
        candidate.evidence_fresh_at,
        "evidence_age_seconds",
    )
    team_memory_age_seconds = _seconds_between(
        generated_at,
        candidate.team_memory_updated_at,
        "team_memory_age_seconds",
    )
    status, terminal_reason = _row_status_and_reason(
        net_probability_edge=net_probability_edge,
        evidence_age_seconds=evidence_age_seconds,
        team_memory_age_seconds=team_memory_age_seconds,
        team_memory_confidence=candidate.team_memory_confidence,
        config=config,
    )
    reason_codes = _normalize_reason_codes(
        (
            *candidate.reason_codes,
            terminal_reason,
            *_cost_reason_codes(
                taker_fee_probability_cost=taker_fee_probability_cost,
                spread_probability_cost=candidate.spread_probability_cost,
                slippage_probability_cost=candidate.slippage_probability_cost,
                external_cost_buffer_probability=(
                    candidate.external_cost_buffer_probability
                ),
            ),
            *_context_reason_codes(
                evidence_age_seconds=evidence_age_seconds,
                team_memory_age_seconds=team_memory_age_seconds,
                team_memory_confidence=candidate.team_memory_confidence,
                config=config,
            ),
        ),
        require_nonempty=True,
    )
    return StrategyProbabilityEventSelectionGateDigestRow(
        redacted_candidate_reference=_redacted_reference(candidate.candidate_reference),
        event_title=candidate.event_title,
        side=candidate.side,
        evaluated_at=candidate.evaluated_at,
        market_implied_probability=candidate.market_implied_probability,
        model_probability=candidate.model_probability,
        side_market_implied_probability=side_market_implied_probability,
        side_model_probability=side_model_probability,
        gross_probability_edge=gross_probability_edge,
        taker_fee_probability_cost=taker_fee_probability_cost,
        spread_probability_cost=candidate.spread_probability_cost,
        slippage_probability_cost=candidate.slippage_probability_cost,
        external_cost_buffer_probability=candidate.external_cost_buffer_probability,
        total_probability_cost=total_probability_cost,
        net_probability_edge=net_probability_edge,
        required_edge_shortfall=required_edge_shortfall,
        evidence_fresh_at=candidate.evidence_fresh_at,
        evidence_age_seconds=evidence_age_seconds,
        team_memory_updated_at=candidate.team_memory_updated_at,
        team_memory_age_seconds=team_memory_age_seconds,
        team_memory_confidence=candidate.team_memory_confidence,
        selection_status=status,
        reason_codes=reason_codes,
    )


def _side_probability(side: str, yes_probability: Decimal) -> Decimal:
    if side == "yes":
        return yes_probability
    return _subtract_decimal(ONE, yes_probability)


def _row_status_and_reason(
    *,
    net_probability_edge: Decimal,
    evidence_age_seconds: Decimal,
    team_memory_age_seconds: Decimal,
    team_memory_confidence: Decimal,
    config: StrategyProbabilityEventSelectionGateDigestConfig,
) -> tuple[str, str]:
    if net_probability_edge < config.watch_net_probability_edge:
        if (
            evidence_age_seconds > config.max_evidence_age_seconds
            or team_memory_age_seconds > config.max_team_memory_age_seconds
            or team_memory_confidence < config.min_team_memory_confidence
        ):
            return "watch", WATCH_REASON_CODE
        return "blocked", BLOCKED_REASON_CODE
    if (
        net_probability_edge < config.min_net_probability_edge
        or evidence_age_seconds > config.max_evidence_age_seconds
        or team_memory_age_seconds > config.max_team_memory_age_seconds
        or team_memory_confidence < config.min_team_memory_confidence
    ):
        return "watch", WATCH_REASON_CODE
    return "select", SELECT_REASON_CODE


def _cost_reason_codes(
    *,
    taker_fee_probability_cost: Decimal,
    spread_probability_cost: Decimal,
    slippage_probability_cost: Decimal,
    external_cost_buffer_probability: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if taker_fee_probability_cost > ZERO:
        reason_codes.append(TAKER_FEE_REASON_CODE)
    if spread_probability_cost > ZERO:
        reason_codes.append(SPREAD_REASON_CODE)
    if slippage_probability_cost > ZERO:
        reason_codes.append(SLIPPAGE_REASON_CODE)
    if external_cost_buffer_probability > ZERO:
        reason_codes.append(EXTERNAL_BUFFER_REASON_CODE)
    return tuple(reason_codes)


def _context_reason_codes(
    *,
    evidence_age_seconds: Decimal,
    team_memory_age_seconds: Decimal,
    team_memory_confidence: Decimal,
    config: StrategyProbabilityEventSelectionGateDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if evidence_age_seconds > config.max_evidence_age_seconds:
        reason_codes.append(EVIDENCE_WATCH_REASON_CODE)
    if team_memory_age_seconds > config.max_team_memory_age_seconds:
        reason_codes.append(TEAM_MEMORY_AGE_WATCH_REASON_CODE)
    if team_memory_confidence < config.min_team_memory_confidence:
        reason_codes.append(TEAM_MEMORY_CONFIDENCE_WATCH_REASON_CODE)
    return tuple(reason_codes)


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[StrategyProbabilityEventSelectionGateDigestCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    normalized = tuple(_candidate_from_supplied_row(row) for row in rows)
    seen: set[str] = set()
    for row in normalized:
        if row.candidate_reference in seen:
            raise ValueError("duplicate candidate_reference")
        seen.add(row.candidate_reference)
    return normalized


def _candidate_from_supplied_row(
    row: object,
) -> StrategyProbabilityEventSelectionGateDigestCandidate:
    if type(row) is StrategyProbabilityEventSelectionGateDigestCandidate:
        _require_safety_flags("candidate", row)
        return row
    raise ValueError(
        "candidates must contain StrategyProbabilityEventSelectionGateDigestCandidate",
    )


def _normalize_rows(
    rows: object,
) -> tuple[StrategyProbabilityEventSelectionGateDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyProbabilityEventSelectionGateDigestRow:
            raise ValueError(
                "rows must contain StrategyProbabilityEventSelectionGateDigestRow",
            )
        _require_safety_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _row_sort_key(
    row: StrategyProbabilityEventSelectionGateDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        ROW_STATUS_SORT_PRIORITY[row.selection_status],
        -row.required_edge_shortfall,
        -row.net_probability_edge,
        row.redacted_candidate_reference,
        row.side,
    )


def _status_count(
    rows: tuple[StrategyProbabilityEventSelectionGateDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.selection_status == status))


def _max_net_probability_edge(
    rows: tuple[StrategyProbabilityEventSelectionGateDigestRow, ...],
) -> Decimal:
    if not rows:
        return _zero()
    return _max_decimal(max(row.net_probability_edge for row in rows), ZERO)


def _max_required_edge_shortfall(
    rows: tuple[StrategyProbabilityEventSelectionGateDigestRow, ...],
) -> Decimal:
    if not rows:
        return _zero()
    return max(row.required_edge_shortfall for row in rows)


def _report_status(
    rows: tuple[StrategyProbabilityEventSelectionGateDigestRow, ...],
) -> str:
    if any(row.selection_status == "blocked" for row in rows):
        return "blocked"
    if any(row.selection_status == "watch" for row in rows) or not rows:
        return "watch"
    return "select"


def _report_reason_codes(
    rows: tuple[StrategyProbabilityEventSelectionGateDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    prioritized = [
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in observed
    ]
    prioritized.extend(
        sorted(reason_code for reason_code in observed if reason_code not in prioritized),
    )
    return tuple(prioritized)


def _validate_row(row: StrategyProbabilityEventSelectionGateDigestRow) -> None:
    if row.side_market_implied_probability != _side_probability(
        row.side,
        row.market_implied_probability,
    ):
        raise ValueError("side_market_implied_probability must match side")
    if row.side_model_probability != _side_probability(row.side, row.model_probability):
        raise ValueError("side_model_probability must match side")
    if row.gross_probability_edge != _subtract_decimal(
        row.side_model_probability,
        row.side_market_implied_probability,
    ):
        raise ValueError("gross_probability_edge must match side probabilities")
    if row.total_probability_cost != _add_decimal(
        row.taker_fee_probability_cost,
        row.spread_probability_cost,
        row.slippage_probability_cost,
        row.external_cost_buffer_probability,
    ):
        raise ValueError("total_probability_cost must match component costs")
    if row.net_probability_edge != _subtract_decimal(
        row.gross_probability_edge,
        row.total_probability_cost,
    ):
        raise ValueError("net_probability_edge must match gross edge less costs")


def _validate_report(report: StrategyProbabilityEventSelectionGateDigestReport) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.select_count != _status_count(report.rows, "select"):
        raise ValueError("select_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.max_net_probability_edge != _max_net_probability_edge(report.rows):
        raise ValueError("max_net_probability_edge must match rows")
    if report.max_required_edge_shortfall != _max_required_edge_shortfall(
        report.rows,
    ):
        raise ValueError("max_required_edge_shortfall must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_not_future(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _seconds_between(
    generated_at: datetime,
    source_at: datetime,
    field_name: str,
) -> Decimal:
    seconds = Decimal(str((generated_at - source_at).total_seconds()))
    if seconds < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _normalize_count_decimal(field_name, seconds)


def _require_safety_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")
    _reject_unsafe_fields(label, value)


def _reject_unsafe_fields(label: str, payload: object) -> None:
    for key in _iter_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe surface field in {label}: {key}")


def _iter_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_keys(item))
        return tuple(keys)
    return ()


def _require_side(field_name: str, value: object) -> None:
    _require_member(field_name, value, SIDES)


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_redacted_reference(value: str) -> None:
    lowered = value.lower()
    if any(token in lowered for token in SENSITIVE_REFERENCE_TOKENS):
        raise ValueError("redacted_candidate_reference contains sensitive text")
    prefix = "candidate_ref_"
    digest = value.removeprefix(prefix)
    if (
        value.startswith(prefix)
        and len(digest) == 12
        and all(character in "0123456789abcdef" for character in digest)
    ):
        return
    raise ValueError("redacted_candidate_reference must be a candidate_ref digest")


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes is required")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole nonnegative Decimal")
    return normalized.quantize(QUANTUM)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _zero() -> Decimal:
    return ZERO.quantize(QUANTUM)


def _add_decimal(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(QUANTUM)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(QUANTUM)


def _max_decimal(left: Decimal, right: Decimal) -> Decimal:
    return left if left >= right else right


def _redacted_reference(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"candidate_ref_{digest}"


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("payload Decimal must be finite")
    return str(value)


def _count_payload(value: Decimal) -> str:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("payload count must be finite")
    return str(value.quantize(Decimal("1")))
