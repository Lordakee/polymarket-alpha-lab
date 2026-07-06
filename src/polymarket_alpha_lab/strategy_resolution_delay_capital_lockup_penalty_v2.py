"""Phase 1 paper report for resolution delay and capital lockup pressure."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_RESOLUTION_DELAY_CAPITAL_LOCKUP_PENALTY_V2_CONFIG_VERSION = (
    "strategy-resolution-delay-capital-lockup-penalty-v2-phase1"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

PAPER_OK_STATUS = "paper_ok"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
PENALTY_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PAPER_OK_STATUS)

EMPTY_REASON = "resolution_delay_capital_lockup_penalty_v2_empty"
REPORT_REASON_PRIORITY = (
    "capital_lockup_penalty_blocked",
    "claim_latency_penalty_blocked",
    "opportunity_cost_pressure_blocked",
    "outcome_source_risk_blocked",
    "settlement_delay_penalty_blocked",
    "capital_lockup_penalty_watch",
    "claim_latency_penalty_watch",
    "opportunity_cost_pressure_watch",
    "outcome_source_risk_watch",
    "settlement_delay_penalty_watch",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wall" "et",
    "ord" "er",
    "net" "work",
    "data" "base",
    "per" "sist",
    "sign" "ing",
    "mut" "ation",
    "b" "uy",
    "s" "ell",
    "tr" "ade",
)

SCORE_WEIGHTS = (
    ("settlement_delay_penalty", Decimal("0.250000")),
    ("capital_lockup_penalty", Decimal("0.250000")),
    ("outcome_source_penalty", Decimal("0.200000")),
    ("claim_latency_penalty", Decimal("0.200000")),
    ("opportunity_cost_penalty", Decimal("0.100000")),
)

__all__ = (
    "DEFAULT_STRATEGY_RESOLUTION_DELAY_CAPITAL_LOCKUP_PENALTY_V2_CONFIG_VERSION",
    "StrategyResolutionDelayCapitalLockupPenaltyV2Candidate",
    "StrategyResolutionDelayCapitalLockupPenaltyV2Config",
    "StrategyResolutionDelayCapitalLockupPenaltyV2Report",
    "StrategyResolutionDelayCapitalLockupPenaltyV2Row",
    "build_strategy_resolution_delay_capital_lockup_penalty_v2_report",
    "strategy_resolution_delay_capital_lockup_penalty_v2_payload",
)


@dataclass(frozen=True)
class StrategyResolutionDelayCapitalLockupPenaltyV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RESOLUTION_DELAY_CAPITAL_LOCKUP_PENALTY_V2_CONFIG_VERSION
    )
    high_settlement_delay_hours: Decimal = Decimal("72.000000")
    high_capital_lockup_hours: Decimal = Decimal("168.000000")
    high_claim_latency_hours: Decimal = Decimal("24.000000")
    watch_penalty_score: Decimal = Decimal("0.350000")
    blocked_penalty_score: Decimal = Decimal("0.700000")
    watch_unresolved_outcome_source_risk: Decimal = Decimal("0.250000")
    blocked_unresolved_outcome_source_risk: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionDelayCapitalLockupPenaltyV2Config:
            raise ValueError(
                "config must be exactly "
                "StrategyResolutionDelayCapitalLockupPenaltyV2Config",
            )
        _require_plain_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_RESOLUTION_DELAY_CAPITAL_LOCKUP_PENALTY_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "high_settlement_delay_hours",
            "high_capital_lockup_hours",
            "high_claim_latency_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_penalty_score",
            "blocked_penalty_score",
            "watch_unresolved_outcome_source_risk",
            "blocked_unresolved_outcome_source_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.blocked_penalty_score < self.watch_penalty_score:
            raise ValueError("blocked_penalty_score must be at least watch threshold")
        if (
            self.blocked_unresolved_outcome_source_risk
            < self.watch_unresolved_outcome_source_risk
        ):
            raise ValueError(
                "blocked_unresolved_outcome_source_risk must be at least watch threshold",
            )
        _reject_unsafe_public_text(self.config_version)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyResolutionDelayCapitalLockupPenaltyV2Candidate:
    candidate_reference: str
    market_slug: str
    evaluated_at: datetime
    market_close_at: datetime
    expected_settlement_delay_hours: Decimal
    capital_lockup_hours: Decimal
    outcome_source_confidence_ratio: Decimal
    expected_claim_latency_hours: Decimal
    opportunity_cost_pressure: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionDelayCapitalLockupPenaltyV2Candidate:
            raise ValueError(
                "candidate must be exactly "
                "StrategyResolutionDelayCapitalLockupPenaltyV2Candidate",
            )
        for field_name in ("candidate_reference", "market_slug"):
            _require_plain_text(field_name, getattr(self, field_name))
        for field_name in ("evaluated_at", "market_close_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_settlement_delay_hours",
            "capital_lockup_hours",
            "expected_claim_latency_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "outcome_source_confidence_ratio",
            "opportunity_cost_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        for field_name in ("market_slug",):
            _reject_unsafe_public_text(getattr(self, field_name))
        for reason_code in self.reason_codes:
            _reject_unsafe_public_text(reason_code)
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyResolutionDelayCapitalLockupPenaltyV2Row:
    penalty_rank: Decimal
    redacted_candidate_reference: str
    market_slug: str
    evaluated_at: datetime
    market_close_at: datetime
    expected_settlement_delay_hours: Decimal
    capital_lockup_hours: Decimal
    outcome_source_confidence_ratio: Decimal
    unresolved_outcome_source_risk: Decimal
    expected_claim_latency_hours: Decimal
    opportunity_cost_pressure: Decimal
    settlement_delay_penalty: Decimal
    capital_lockup_penalty: Decimal
    outcome_source_penalty: Decimal
    claim_latency_penalty: Decimal
    opportunity_cost_penalty: Decimal
    total_lockup_penalty_score: Decimal
    penalty_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionDelayCapitalLockupPenaltyV2Row:
            raise ValueError(
                "row must be exactly StrategyResolutionDelayCapitalLockupPenaltyV2Row",
            )
        object.__setattr__(
            self,
            "penalty_rank",
            _normalize_count_decimal("penalty_rank", self.penalty_rank),
        )
        _require_redacted_reference(self.redacted_candidate_reference)
        _require_plain_text("market_slug", self.market_slug)
        for field_name in ("evaluated_at", "market_close_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_settlement_delay_hours",
            "capital_lockup_hours",
            "expected_claim_latency_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "outcome_source_confidence_ratio",
            "unresolved_outcome_source_risk",
            "opportunity_cost_pressure",
            "settlement_delay_penalty",
            "capital_lockup_penalty",
            "outcome_source_penalty",
            "claim_latency_penalty",
            "opportunity_cost_penalty",
            "total_lockup_penalty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("penalty_status", self.penalty_status, PENALTY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _reject_unsafe_public_text(self.market_slug)
        for reason_code in self.reason_codes:
            _reject_unsafe_public_text(reason_code)
        _require_hard_flags("row", self)
        _set_or_verify_digest(self, _row_digest)
        _validate_row(self)


@dataclass(frozen=True)
class StrategyResolutionDelayCapitalLockupPenaltyV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    paper_ok_count: Decimal
    max_total_lockup_penalty_score: Decimal
    max_capital_lockup_hours: Decimal
    max_settlement_delay_hours: Decimal
    max_claim_latency_hours: Decimal
    max_unresolved_outcome_source_risk: Decimal
    max_opportunity_cost_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyResolutionDelayCapitalLockupPenaltyV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyResolutionDelayCapitalLockupPenaltyV2Report:
            raise ValueError(
                "report must be exactly StrategyResolutionDelayCapitalLockupPenaltyV2Report",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_plain_text("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "blocked_count",
            "watch_count",
            "paper_ok_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_total_lockup_penalty_score",
            "max_unresolved_outcome_source_risk",
            "max_opportunity_cost_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_capital_lockup_hours",
            "max_settlement_delay_hours",
            "max_claim_latency_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, PENALTY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _reject_unsafe_public_text(self.config_version)
        for reason_code in self.reason_codes:
            _reject_unsafe_public_text(reason_code)
        _require_hard_flags("report", self)
        _set_or_verify_digest(self, _report_digest)
        _validate_report(self)


def build_strategy_resolution_delay_capital_lockup_penalty_v2_report(
    candidates: Iterable[object],
    *,
    config: StrategyResolutionDelayCapitalLockupPenaltyV2Config,
    generated_at: datetime,
) -> StrategyResolutionDelayCapitalLockupPenaltyV2Report:
    if type(config) is not StrategyResolutionDelayCapitalLockupPenaltyV2Config:
        raise ValueError(
            "config must be exactly StrategyResolutionDelayCapitalLockupPenaltyV2Config",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    source_candidates = _normalize_candidates(candidates)
    for candidate in source_candidates:
        if candidate.evaluated_at > generated_at:
            raise ValueError("evaluated_at must not be after generated_at")
    preliminary_rows = tuple(
        _row_from_candidate(candidate, config=config) for candidate in source_candidates
    )
    sorted_rows = tuple(sorted(preliminary_rows, key=_row_sort_key))
    rows = tuple(
        _row_with_rank(row, _count_decimal(index))
        for index, row in enumerate(sorted_rows, start=1)
    )
    return StrategyResolutionDelayCapitalLockupPenaltyV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(rows)),
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        paper_ok_count=_status_count(rows, PAPER_OK_STATUS),
        max_total_lockup_penalty_score=_max_decimal(
            row.total_lockup_penalty_score for row in rows
        ),
        max_capital_lockup_hours=_max_decimal(row.capital_lockup_hours for row in rows),
        max_settlement_delay_hours=_max_decimal(
            row.expected_settlement_delay_hours for row in rows
        ),
        max_claim_latency_hours=_max_decimal(
            row.expected_claim_latency_hours for row in rows
        ),
        max_unresolved_outcome_source_risk=_max_decimal(
            row.unresolved_outcome_source_risk for row in rows
        ),
        max_opportunity_cost_pressure=_max_decimal(
            row.opportunity_cost_pressure for row in rows
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_resolution_delay_capital_lockup_penalty_v2_payload(
    report: StrategyResolutionDelayCapitalLockupPenaltyV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyResolutionDelayCapitalLockupPenaltyV2Report:
        raise ValueError(
            "report must be a StrategyResolutionDelayCapitalLockupPenaltyV2Report",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return payload


def _row_from_candidate(
    candidate: StrategyResolutionDelayCapitalLockupPenaltyV2Candidate,
    *,
    config: StrategyResolutionDelayCapitalLockupPenaltyV2Config,
) -> StrategyResolutionDelayCapitalLockupPenaltyV2Row:
    unresolved_risk = _subtract_decimal(ONE, candidate.outcome_source_confidence_ratio)
    settlement_penalty = _capped_ratio(
        candidate.expected_settlement_delay_hours,
        config.high_settlement_delay_hours,
    )
    capital_penalty = _capped_ratio(
        candidate.capital_lockup_hours,
        config.high_capital_lockup_hours,
    )
    claim_penalty = _capped_ratio(
        candidate.expected_claim_latency_hours,
        config.high_claim_latency_hours,
    )
    score = _penalty_score(
        settlement_delay_penalty=settlement_penalty,
        capital_lockup_penalty=capital_penalty,
        outcome_source_penalty=unresolved_risk,
        claim_latency_penalty=claim_penalty,
        opportunity_cost_penalty=candidate.opportunity_cost_pressure,
    )
    status = _penalty_status(score, unresolved_risk, config)
    return StrategyResolutionDelayCapitalLockupPenaltyV2Row(
        penalty_rank=ONE,
        redacted_candidate_reference=_redacted_reference(candidate.candidate_reference),
        market_slug=candidate.market_slug,
        evaluated_at=candidate.evaluated_at,
        market_close_at=candidate.market_close_at,
        expected_settlement_delay_hours=candidate.expected_settlement_delay_hours,
        capital_lockup_hours=candidate.capital_lockup_hours,
        outcome_source_confidence_ratio=candidate.outcome_source_confidence_ratio,
        unresolved_outcome_source_risk=unresolved_risk,
        expected_claim_latency_hours=candidate.expected_claim_latency_hours,
        opportunity_cost_pressure=candidate.opportunity_cost_pressure,
        settlement_delay_penalty=settlement_penalty,
        capital_lockup_penalty=capital_penalty,
        outcome_source_penalty=unresolved_risk,
        claim_latency_penalty=claim_penalty,
        opportunity_cost_penalty=candidate.opportunity_cost_pressure,
        total_lockup_penalty_score=score,
        penalty_status=status,
        reason_codes=_row_reason_codes(candidate.reason_codes, status, config, score, {
            "settlement_delay_penalty": settlement_penalty,
            "capital_lockup_penalty": capital_penalty,
            "outcome_source_risk": unresolved_risk,
            "claim_latency_penalty": claim_penalty,
            "opportunity_cost_pressure": candidate.opportunity_cost_pressure,
        }),
    )


def _row_with_rank(
    row: StrategyResolutionDelayCapitalLockupPenaltyV2Row,
    rank: Decimal,
) -> StrategyResolutionDelayCapitalLockupPenaltyV2Row:
    return StrategyResolutionDelayCapitalLockupPenaltyV2Row(
        penalty_rank=rank,
        redacted_candidate_reference=row.redacted_candidate_reference,
        market_slug=row.market_slug,
        evaluated_at=row.evaluated_at,
        market_close_at=row.market_close_at,
        expected_settlement_delay_hours=row.expected_settlement_delay_hours,
        capital_lockup_hours=row.capital_lockup_hours,
        outcome_source_confidence_ratio=row.outcome_source_confidence_ratio,
        unresolved_outcome_source_risk=row.unresolved_outcome_source_risk,
        expected_claim_latency_hours=row.expected_claim_latency_hours,
        opportunity_cost_pressure=row.opportunity_cost_pressure,
        settlement_delay_penalty=row.settlement_delay_penalty,
        capital_lockup_penalty=row.capital_lockup_penalty,
        outcome_source_penalty=row.outcome_source_penalty,
        claim_latency_penalty=row.claim_latency_penalty,
        opportunity_cost_penalty=row.opportunity_cost_penalty,
        total_lockup_penalty_score=row.total_lockup_penalty_score,
        penalty_status=row.penalty_status,
        reason_codes=row.reason_codes,
    )


def _penalty_score(**components: Decimal) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for name, weight in SCORE_WEIGHTS:
            total += components[name] * weight
        return total.quantize(QUANTUM)


def _penalty_status(
    score: Decimal,
    unresolved_risk: Decimal,
    config: StrategyResolutionDelayCapitalLockupPenaltyV2Config,
) -> str:
    if (
        score >= config.blocked_penalty_score
        or unresolved_risk >= config.blocked_unresolved_outcome_source_risk
    ):
        return BLOCKED_STATUS
    if (
        score >= config.watch_penalty_score
        or unresolved_risk >= config.watch_unresolved_outcome_source_risk
    ):
        return WATCH_STATUS
    return PAPER_OK_STATUS


def _row_reason_codes(
    candidate_reason_codes: tuple[str, ...],
    status: str,
    config: StrategyResolutionDelayCapitalLockupPenaltyV2Config,
    score: Decimal,
    components: dict[str, Decimal],
) -> tuple[str, ...]:
    reason_codes = list(candidate_reason_codes)
    for prefix, value in components.items():
        reason_codes.append(f"{prefix}_{_component_state(prefix, value, config)}")
    reason_codes.append(f"settlement_delay_capital_lockup_penalty_{status}")
    return _normalize_reason_codes(tuple(sorted(set(reason_codes))), require_nonempty=True)


def _component_state(
    prefix: str,
    value: Decimal,
    config: StrategyResolutionDelayCapitalLockupPenaltyV2Config,
) -> str:
    if prefix == "outcome_source_risk":
        if value >= config.blocked_unresolved_outcome_source_risk:
            return BLOCKED_STATUS
        if value >= config.watch_unresolved_outcome_source_risk:
            return WATCH_STATUS
        return "clear"
    if value >= config.blocked_penalty_score:
        return BLOCKED_STATUS
    if value >= config.watch_penalty_score:
        return WATCH_STATUS
    return "clear"


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[StrategyResolutionDelayCapitalLockupPenaltyV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        source_candidates = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    normalized: list[StrategyResolutionDelayCapitalLockupPenaltyV2Candidate] = []
    for candidate in source_candidates:
        if type(candidate) is not StrategyResolutionDelayCapitalLockupPenaltyV2Candidate:
            raise ValueError(
                "candidates must contain "
                "StrategyResolutionDelayCapitalLockupPenaltyV2Candidate",
            )
        _require_hard_flags("candidate", candidate)
        if candidate.candidate_reference in seen:
            raise ValueError("duplicate candidate_reference")
        seen.add(candidate.candidate_reference)
        normalized.append(candidate)
    return tuple(normalized)


def _normalize_rows(
    value: object,
) -> tuple[StrategyResolutionDelayCapitalLockupPenaltyV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyResolutionDelayCapitalLockupPenaltyV2Row:
            raise ValueError(
                "rows must contain StrategyResolutionDelayCapitalLockupPenaltyV2Row",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    expected_ranks = tuple(_count_decimal(index) for index in range(1, len(rows) + 1))
    if tuple(row.penalty_rank for row in rows) != expected_ranks:
        raise ValueError("rows must use sequential penalty_rank values")
    return rows


def _row_sort_key(
    row: StrategyResolutionDelayCapitalLockupPenaltyV2Row,
) -> tuple[Decimal, str, str]:
    return (-row.total_lockup_penalty_score, row.market_slug, row.redacted_candidate_reference)


def _status_count(
    rows: tuple[StrategyResolutionDelayCapitalLockupPenaltyV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.penalty_status == status))


def _report_status(rows: tuple[StrategyResolutionDelayCapitalLockupPenaltyV2Row, ...]) -> str:
    if any(row.penalty_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.penalty_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PAPER_OK_STATUS


def _report_reason_codes(
    rows: tuple[StrategyResolutionDelayCapitalLockupPenaltyV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    status = _report_status(rows)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    selected = tuple(
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in observed and reason_code.endswith(f"_{status}")
    )
    if selected:
        return selected
    return (f"settlement_delay_capital_lockup_penalty_{status}",)


def _validate_row(row: StrategyResolutionDelayCapitalLockupPenaltyV2Row) -> None:
    if row.unresolved_outcome_source_risk != _subtract_decimal(
        ONE,
        row.outcome_source_confidence_ratio,
    ):
        raise ValueError("unresolved_outcome_source_risk must match confidence")
    if row.outcome_source_penalty != row.unresolved_outcome_source_risk:
        raise ValueError("outcome_source_penalty must match unresolved risk")
    if row.opportunity_cost_penalty != row.opportunity_cost_pressure:
        raise ValueError("opportunity_cost_penalty must match pressure")
    expected_score = _penalty_score(
        settlement_delay_penalty=row.settlement_delay_penalty,
        capital_lockup_penalty=row.capital_lockup_penalty,
        outcome_source_penalty=row.outcome_source_penalty,
        claim_latency_penalty=row.claim_latency_penalty,
        opportunity_cost_penalty=row.opportunity_cost_penalty,
    )
    if row.total_lockup_penalty_score != expected_score:
        raise ValueError("total_lockup_penalty_score must match row fields")
    if f"settlement_delay_capital_lockup_penalty_{row.penalty_status}" not in row.reason_codes:
        raise ValueError("penalty_status must match reason_codes")


def _validate_report(report: StrategyResolutionDelayCapitalLockupPenaltyV2Report) -> None:
    rows = report.rows
    if report.candidate_count != _count_decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.blocked_count != _status_count(rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.paper_ok_count != _status_count(rows, PAPER_OK_STATUS):
        raise ValueError("paper_ok_count must match rows")
    if report.max_total_lockup_penalty_score != _max_decimal(
        row.total_lockup_penalty_score for row in rows
    ):
        raise ValueError("max_total_lockup_penalty_score must match rows")
    if report.max_capital_lockup_hours != _max_decimal(
        row.capital_lockup_hours for row in rows
    ):
        raise ValueError("max_capital_lockup_hours must match rows")
    if report.max_settlement_delay_hours != _max_decimal(
        row.expected_settlement_delay_hours for row in rows
    ):
        raise ValueError("max_settlement_delay_hours must match rows")
    if report.max_claim_latency_hours != _max_decimal(
        row.expected_claim_latency_hours for row in rows
    ):
        raise ValueError("max_claim_latency_hours must match rows")
    if report.max_unresolved_outcome_source_risk != _max_decimal(
        row.unresolved_outcome_source_risk for row in rows
    ):
        raise ValueError("max_unresolved_outcome_source_risk must match rows")
    if report.max_opportunity_cost_pressure != _max_decimal(
        row.opportunity_cost_pressure for row in rows
    ):
        raise ValueError("max_opportunity_cost_pressure must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_member(field_name: str, value: object, values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in values:
        raise ValueError(f"{field_name} must be one of {values}")


def _require_plain_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_redacted_reference(value: object) -> None:
    if type(value) is not str:
        raise ValueError("redacted_candidate_reference must be a string")
    prefix = "candidate_ref_"
    digest = value.removeprefix(prefix)
    if (
        value.startswith(prefix)
        and len(digest) == 16
        and all(character in "0123456789abcdef" for character in digest)
    ):
        return
    raise ValueError("redacted_candidate_reference must be redacted")


def _normalize_reason_codes(
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(values)
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes is required")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_reason_code(value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError("reason_codes must contain canonical values")
    if value != value.lower() or value.strip() != value:
        raise ValueError("reason_codes must contain canonical values")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError("reason_codes must contain canonical values")


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return Decimal(value.to_integral_value())


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=ZERO)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(QUANTUM)


def _capped_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        ratio = (value / denominator).quantize(QUANTUM)
    if ratio > ONE:
        return ONE
    return ratio


def _redacted_reference(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"candidate_ref_{digest}"


def _set_or_verify_digest(value: object, digest_func: Any) -> None:
    current = getattr(value, "derived_validation_digest")
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = digest_func(value)
    if current == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    if current != expected:
        raise ValueError("derived_validation_digest does not match derived fields")
    _require_sha256(current)


def _row_digest(row: StrategyResolutionDelayCapitalLockupPenaltyV2Row) -> str:
    return _digest_for_value(row, skip=("derived_validation_digest",))


def _report_digest(report: StrategyResolutionDelayCapitalLockupPenaltyV2Report) -> str:
    return _digest_for_value(report, skip=("derived_validation_digest",))


def _digest_for_value(value: object, *, skip: tuple[str, ...]) -> str:
    payload = _payload_value(value, skip=skip)
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(rendered.encode("utf-8")).hexdigest()


def _require_sha256(value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be sha256")


def _payload_value(value: Any, *, skip: tuple[str, ...] = ()) -> Any:
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) in (float, int):
        raise ValueError("public payload numeric values must be Decimal strings")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is str:
        _reject_unsafe_public_text(value)
        return value
    if is_dataclass(value) and not isinstance(value, type):
        _require_hard_flags(type(value).__name__, value)
        return _payload_mapping(
            {field.name: getattr(value, field.name) for field in fields(value)},
            skip=skip,
        )
    if type(value) is dict:
        return _payload_mapping(value, skip=skip)
    if type(value) in (list, tuple):
        return [_payload_value(item, skip=skip) for item in value]
    raise ValueError("public payload value is not serializable")


def _payload_mapping(value: dict[Any, Any], *, skip: tuple[str, ...]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("public payload keys must be strings")
        if key.startswith("_") or key in skip:
            continue
        _reject_unsafe_public_text(key)
        payload[key] = _payload_value(item, skip=skip)
    return payload


def _reject_unsafe_public_text(value: str) -> None:
    normalized = value.lower()
    for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS:
        if fragment in normalized:
            raise ValueError("unsafe public payload text")
