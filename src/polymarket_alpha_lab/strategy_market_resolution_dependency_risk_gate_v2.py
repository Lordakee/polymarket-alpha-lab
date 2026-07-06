"""Phase 1 paper report for market resolution dependency risk."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_MARKET_RESOLUTION_DEPENDENCY_RISK_GATE_V2_CONFIG_VERSION = (
    "strategy-market-resolution-dependency-risk-gate-v2-phase1"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

PAPER_OK_STATUS = "paper_ok"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
RISK_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PAPER_OK_STATUS)

EMPTY_REASON = "resolution_dependency_risk_gate_v2_empty"
REPORT_REASON_PRIORITY = (
    "correlated_resolution_dependency_blocked",
    "settlement_delay_penalty_blocked",
    "external_dependency_pressure_blocked",
    "source_confidence_gap_blocked",
    "market_dependency_weight_blocked",
    "resolution_dependency_risk_gate_blocked",
    "correlated_resolution_dependency_watch",
    "settlement_delay_penalty_watch",
    "resolution_dependency_risk_gate_watch",
    "external_dependency_pressure_watch",
    "source_confidence_gap_watch",
    "market_dependency_weight_watch",
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
    ("dependency_count_penalty", Decimal("0.200000")),
    ("correlated_resolution_penalty", Decimal("0.250000")),
    ("settlement_delay_penalty", Decimal("0.200000")),
    ("source_confidence_penalty", Decimal("0.250000")),
    ("market_dependency_weight", Decimal("0.108333")),
)

__all__ = (
    "DEFAULT_STRATEGY_MARKET_RESOLUTION_DEPENDENCY_RISK_GATE_V2_CONFIG_VERSION",
    "StrategyMarketResolutionDependencyRiskGateV2Candidate",
    "StrategyMarketResolutionDependencyRiskGateV2Config",
    "StrategyMarketResolutionDependencyRiskGateV2Report",
    "StrategyMarketResolutionDependencyRiskGateV2Row",
    "build_strategy_market_resolution_dependency_risk_gate_v2_report",
    "strategy_market_resolution_dependency_risk_gate_v2_payload",
)


@dataclass(frozen=True)
class StrategyMarketResolutionDependencyRiskGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_MARKET_RESOLUTION_DEPENDENCY_RISK_GATE_V2_CONFIG_VERSION
    )
    watch_dependency_risk_score: Decimal = Decimal("0.350000")
    blocked_dependency_risk_score: Decimal = Decimal("0.700000")
    high_settlement_delay_hours: Decimal = Decimal("72.000000")
    dependency_count_block_count: Decimal = Decimal("3")
    correlated_resolution_block_count: Decimal = Decimal("2")
    low_source_confidence_watch: Decimal = Decimal("0.750000")
    low_source_confidence_blocked: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyMarketResolutionDependencyRiskGateV2Config:
            raise ValueError(
                "config must be exactly "
                "StrategyMarketResolutionDependencyRiskGateV2Config",
            )
        _require_plain_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_MARKET_RESOLUTION_DEPENDENCY_RISK_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "watch_dependency_risk_score",
            "blocked_dependency_risk_score",
            "low_source_confidence_watch",
            "low_source_confidence_blocked",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "high_settlement_delay_hours",
            _normalize_positive_decimal(
                "high_settlement_delay_hours",
                self.high_settlement_delay_hours,
            ),
        )
        for field_name in (
            "dependency_count_block_count",
            "correlated_resolution_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.blocked_dependency_risk_score < self.watch_dependency_risk_score:
            raise ValueError("blocked_dependency_risk_score must be at least watch score")
        if self.low_source_confidence_blocked > self.low_source_confidence_watch:
            raise ValueError(
                "low_source_confidence_blocked must not exceed watch confidence",
            )
        _reject_unsafe_public_text(self.config_version)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyMarketResolutionDependencyRiskGateV2Candidate:
    candidate_reference: str
    market_slug: str
    evaluated_at: datetime
    resolution_dependency_key: str
    external_dependency_count: Decimal
    correlated_resolution_count: Decimal
    source_confidence_ratio: Decimal
    settlement_delay_hours: Decimal
    market_dependency_weight: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyMarketResolutionDependencyRiskGateV2Candidate:
            raise ValueError(
                "candidate must be exactly "
                "StrategyMarketResolutionDependencyRiskGateV2Candidate",
            )
        for field_name in (
            "candidate_reference",
            "market_slug",
            "resolution_dependency_key",
        ):
            _require_plain_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        for field_name in ("external_dependency_count", "correlated_resolution_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_confidence_ratio",
            "market_dependency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_delay_hours",
            _normalize_nonnegative_decimal(
                "settlement_delay_hours",
                self.settlement_delay_hours,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        for value in (
            self.candidate_reference,
            self.market_slug,
            self.resolution_dependency_key,
        ):
            _reject_unsafe_public_text(value)
        for reason_code in self.reason_codes:
            _reject_unsafe_public_text(reason_code)
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyMarketResolutionDependencyRiskGateV2Row:
    dependency_rank: Decimal
    redacted_candidate_reference: str
    market_slug: str
    evaluated_at: datetime
    resolution_dependency_key: str
    external_dependency_count: Decimal
    correlated_resolution_count: Decimal
    source_confidence_ratio: Decimal
    unresolved_source_risk: Decimal
    settlement_delay_hours: Decimal
    market_dependency_weight: Decimal
    dependency_count_penalty: Decimal
    correlated_resolution_penalty: Decimal
    settlement_delay_penalty: Decimal
    total_dependency_risk_score: Decimal
    dependency_risk_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyMarketResolutionDependencyRiskGateV2Row:
            raise ValueError("row must be exactly StrategyMarketResolutionDependencyRiskGateV2Row")
        object.__setattr__(
            self,
            "dependency_rank",
            _normalize_count_decimal("dependency_rank", self.dependency_rank),
        )
        _require_redacted_reference(self.redacted_candidate_reference)
        for field_name in ("market_slug", "resolution_dependency_key"):
            _require_plain_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        for field_name in ("external_dependency_count", "correlated_resolution_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_confidence_ratio",
            "unresolved_source_risk",
            "market_dependency_weight",
            "dependency_count_penalty",
            "correlated_resolution_penalty",
            "settlement_delay_penalty",
            "total_dependency_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_delay_hours",
            _normalize_nonnegative_decimal(
                "settlement_delay_hours",
                self.settlement_delay_hours,
            ),
        )
        _require_member("dependency_risk_status", self.dependency_risk_status, RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        for value in (self.market_slug, self.resolution_dependency_key):
            _reject_unsafe_public_text(value)
        for reason_code in self.reason_codes:
            _reject_unsafe_public_text(reason_code)
        _require_hard_flags("row", self)
        _set_or_verify_digest(self, _row_digest)
        _validate_row(self)


@dataclass(frozen=True)
class StrategyMarketResolutionDependencyRiskGateV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    paper_ok_count: Decimal
    max_total_dependency_risk_score: Decimal
    max_settlement_delay_hours: Decimal
    max_correlated_resolution_count: Decimal
    max_external_dependency_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyMarketResolutionDependencyRiskGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyMarketResolutionDependencyRiskGateV2Report:
            raise ValueError(
                "report must be exactly StrategyMarketResolutionDependencyRiskGateV2Report",
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
            "max_correlated_resolution_count",
            "max_external_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_total_dependency_risk_score",):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_settlement_delay_hours",
            _normalize_nonnegative_decimal(
                "max_settlement_delay_hours",
                self.max_settlement_delay_hours,
            ),
        )
        _require_member("status", self.status, RISK_STATUSES)
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


def build_strategy_market_resolution_dependency_risk_gate_v2_report(
    candidates: Iterable[object],
    *,
    config: StrategyMarketResolutionDependencyRiskGateV2Config,
    generated_at: datetime,
) -> StrategyMarketResolutionDependencyRiskGateV2Report:
    if type(config) is not StrategyMarketResolutionDependencyRiskGateV2Config:
        raise ValueError(
            "config must be exactly StrategyMarketResolutionDependencyRiskGateV2Config",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    source_candidates = _normalize_candidates(candidates)
    for candidate in source_candidates:
        if candidate.evaluated_at > generated_at:
            raise ValueError("evaluated_at must not be after generated_at")
    key_counts = _resolution_dependency_key_counts(source_candidates)
    preliminary_rows = tuple(
        _row_from_candidate(candidate, config=config, key_counts=key_counts)
        for candidate in source_candidates
    )
    sorted_rows = tuple(sorted(preliminary_rows, key=_row_sort_key))
    rows = tuple(
        _row_with_rank(row, _count_decimal(index))
        for index, row in enumerate(sorted_rows, start=1)
    )
    return StrategyMarketResolutionDependencyRiskGateV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(rows)),
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        paper_ok_count=_status_count(rows, PAPER_OK_STATUS),
        max_total_dependency_risk_score=_max_decimal(
            row.total_dependency_risk_score for row in rows
        ),
        max_settlement_delay_hours=_max_decimal(row.settlement_delay_hours for row in rows),
        max_correlated_resolution_count=_max_decimal(
            row.correlated_resolution_count for row in rows
        ),
        max_external_dependency_count=_max_decimal(
            row.external_dependency_count for row in rows
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_market_resolution_dependency_risk_gate_v2_payload(
    report: StrategyMarketResolutionDependencyRiskGateV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyMarketResolutionDependencyRiskGateV2Report:
        raise ValueError(
            "report must be a StrategyMarketResolutionDependencyRiskGateV2Report",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return payload


def _row_from_candidate(
    candidate: StrategyMarketResolutionDependencyRiskGateV2Candidate,
    *,
    config: StrategyMarketResolutionDependencyRiskGateV2Config,
    key_counts: dict[str, Decimal],
) -> StrategyMarketResolutionDependencyRiskGateV2Row:
    correlated_count = _effective_correlated_resolution_count(
        candidate,
        config=config,
        key_counts=key_counts,
    )
    dependency_penalty = _capped_ratio(
        candidate.external_dependency_count,
        config.dependency_count_block_count,
    )
    correlated_penalty = _capped_ratio(
        correlated_count,
        config.correlated_resolution_block_count,
    )
    settlement_penalty = _capped_ratio(
        candidate.settlement_delay_hours,
        config.high_settlement_delay_hours,
    )
    unresolved_source_risk = _subtract_decimal(ONE, candidate.source_confidence_ratio)
    score = _dependency_risk_score(
        dependency_count_penalty=dependency_penalty,
        correlated_resolution_penalty=correlated_penalty,
        settlement_delay_penalty=settlement_penalty,
        source_confidence_penalty=unresolved_source_risk,
        market_dependency_weight=candidate.market_dependency_weight,
    )
    status = _dependency_risk_status(
        candidate,
        config=config,
        correlated_count=correlated_count,
        settlement_delay_penalty=settlement_penalty,
        total_dependency_risk_score=score,
    )
    return StrategyMarketResolutionDependencyRiskGateV2Row(
        dependency_rank=ONE,
        redacted_candidate_reference=_redacted_reference(candidate.candidate_reference),
        market_slug=candidate.market_slug,
        evaluated_at=candidate.evaluated_at,
        resolution_dependency_key=candidate.resolution_dependency_key,
        external_dependency_count=candidate.external_dependency_count,
        correlated_resolution_count=correlated_count,
        source_confidence_ratio=candidate.source_confidence_ratio,
        unresolved_source_risk=unresolved_source_risk,
        settlement_delay_hours=candidate.settlement_delay_hours,
        market_dependency_weight=candidate.market_dependency_weight,
        dependency_count_penalty=dependency_penalty,
        correlated_resolution_penalty=correlated_penalty,
        settlement_delay_penalty=settlement_penalty,
        total_dependency_risk_score=score,
        dependency_risk_status=status,
        reason_codes=_row_reason_codes(
            candidate.reason_codes,
            candidate,
            config=config,
            correlated_count=correlated_count,
            settlement_delay_penalty=settlement_penalty,
            status=status,
        ),
    )


def _row_with_rank(
    row: StrategyMarketResolutionDependencyRiskGateV2Row,
    rank: Decimal,
) -> StrategyMarketResolutionDependencyRiskGateV2Row:
    return StrategyMarketResolutionDependencyRiskGateV2Row(
        dependency_rank=rank,
        redacted_candidate_reference=row.redacted_candidate_reference,
        market_slug=row.market_slug,
        evaluated_at=row.evaluated_at,
        resolution_dependency_key=row.resolution_dependency_key,
        external_dependency_count=row.external_dependency_count,
        correlated_resolution_count=row.correlated_resolution_count,
        source_confidence_ratio=row.source_confidence_ratio,
        unresolved_source_risk=row.unresolved_source_risk,
        settlement_delay_hours=row.settlement_delay_hours,
        market_dependency_weight=row.market_dependency_weight,
        dependency_count_penalty=row.dependency_count_penalty,
        correlated_resolution_penalty=row.correlated_resolution_penalty,
        settlement_delay_penalty=row.settlement_delay_penalty,
        total_dependency_risk_score=row.total_dependency_risk_score,
        dependency_risk_status=row.dependency_risk_status,
        reason_codes=row.reason_codes,
    )


def _dependency_risk_score(**components: Decimal) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for name, weight in SCORE_WEIGHTS:
            total += components[name] * weight
        if total > ONE:
            total = ONE
        return total.quantize(QUANTUM)


def _dependency_risk_status(
    candidate: StrategyMarketResolutionDependencyRiskGateV2Candidate,
    *,
    config: StrategyMarketResolutionDependencyRiskGateV2Config,
    correlated_count: Decimal,
    settlement_delay_penalty: Decimal,
    total_dependency_risk_score: Decimal,
) -> str:
    if (
        correlated_count >= config.correlated_resolution_block_count
        or candidate.external_dependency_count >= config.dependency_count_block_count
        or candidate.source_confidence_ratio <= config.low_source_confidence_blocked
        or settlement_delay_penalty >= ONE
        or total_dependency_risk_score >= config.blocked_dependency_risk_score
    ):
        return BLOCKED_STATUS
    if (
        total_dependency_risk_score >= config.watch_dependency_risk_score
        or candidate.external_dependency_count > ZERO
        or candidate.source_confidence_ratio < config.low_source_confidence_watch
        or settlement_delay_penalty > ZERO
        or candidate.market_dependency_weight > ZERO
        or correlated_count > ZERO
    ):
        return WATCH_STATUS
    return PAPER_OK_STATUS


def _row_reason_codes(
    candidate_reason_codes: tuple[str, ...],
    candidate: StrategyMarketResolutionDependencyRiskGateV2Candidate,
    *,
    config: StrategyMarketResolutionDependencyRiskGateV2Config,
    correlated_count: Decimal,
    settlement_delay_penalty: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes = list(candidate_reason_codes)
    reason_codes.append(
        "external_dependency_pressure_"
        + _count_state(candidate.external_dependency_count, config.dependency_count_block_count),
    )
    reason_codes.append(
        "correlated_resolution_dependency_"
        + _count_state(correlated_count, config.correlated_resolution_block_count),
    )
    reason_codes.append(
        "settlement_delay_penalty_"
        + _ratio_state(settlement_delay_penalty, config.watch_dependency_risk_score, ONE),
    )
    reason_codes.append(
        "source_confidence_gap_"
        + _source_confidence_state(candidate.source_confidence_ratio, config),
    )
    reason_codes.append(
        "market_dependency_weight_"
        + _ratio_state(
            candidate.market_dependency_weight,
            config.watch_dependency_risk_score,
            config.blocked_dependency_risk_score,
        ),
    )
    reason_codes.append(f"resolution_dependency_risk_gate_{status}")
    return _normalize_reason_codes(tuple(sorted(set(reason_codes))), require_nonempty=True)


def _count_state(value: Decimal, blocked_threshold: Decimal) -> str:
    if value >= blocked_threshold:
        return BLOCKED_STATUS
    if value > ZERO:
        return WATCH_STATUS
    return "clear"


def _ratio_state(value: Decimal, watch_threshold: Decimal, blocked_threshold: Decimal) -> str:
    if value >= blocked_threshold:
        return BLOCKED_STATUS
    if value >= watch_threshold:
        return WATCH_STATUS
    return "clear"


def _source_confidence_state(
    value: Decimal,
    config: StrategyMarketResolutionDependencyRiskGateV2Config,
) -> str:
    if value <= config.low_source_confidence_blocked:
        return BLOCKED_STATUS
    if value < config.low_source_confidence_watch:
        return WATCH_STATUS
    return "clear"


def _effective_correlated_resolution_count(
    candidate: StrategyMarketResolutionDependencyRiskGateV2Candidate,
    *,
    config: StrategyMarketResolutionDependencyRiskGateV2Config,
    key_counts: dict[str, Decimal],
) -> Decimal:
    cluster_count = key_counts[candidate.resolution_dependency_key]
    if cluster_count >= config.correlated_resolution_block_count:
        return max(candidate.correlated_resolution_count, cluster_count)
    return candidate.correlated_resolution_count


def _resolution_dependency_key_counts(
    candidates: tuple[StrategyMarketResolutionDependencyRiskGateV2Candidate, ...],
) -> dict[str, Decimal]:
    counts: dict[str, Decimal] = {}
    for candidate in candidates:
        counts[candidate.resolution_dependency_key] = (
            counts.get(candidate.resolution_dependency_key, ZERO) + ONE
        )
    return counts


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[StrategyMarketResolutionDependencyRiskGateV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        source_candidates = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    normalized: list[StrategyMarketResolutionDependencyRiskGateV2Candidate] = []
    for candidate in source_candidates:
        if type(candidate) is not StrategyMarketResolutionDependencyRiskGateV2Candidate:
            raise ValueError(
                "candidates must contain "
                "StrategyMarketResolutionDependencyRiskGateV2Candidate",
            )
        _require_hard_flags("candidate", candidate)
        if candidate.candidate_reference in seen:
            raise ValueError("duplicate candidate_reference")
        seen.add(candidate.candidate_reference)
        normalized.append(candidate)
    return tuple(normalized)


def _normalize_rows(
    value: object,
) -> tuple[StrategyMarketResolutionDependencyRiskGateV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyMarketResolutionDependencyRiskGateV2Row:
            raise ValueError("rows must contain StrategyMarketResolutionDependencyRiskGateV2Row")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    expected_ranks = tuple(_count_decimal(index) for index in range(1, len(rows) + 1))
    if tuple(row.dependency_rank for row in rows) != expected_ranks:
        raise ValueError("rows must use sequential dependency_rank values")
    return rows


def _row_sort_key(
    row: StrategyMarketResolutionDependencyRiskGateV2Row,
) -> tuple[Decimal, str, str]:
    return (
        -row.total_dependency_risk_score,
        row.market_slug,
        row.redacted_candidate_reference,
    )


def _status_count(
    rows: tuple[StrategyMarketResolutionDependencyRiskGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.dependency_risk_status == status))


def _report_status(rows: tuple[StrategyMarketResolutionDependencyRiskGateV2Row, ...]) -> str:
    if any(row.dependency_risk_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.dependency_risk_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PAPER_OK_STATUS


def _report_reason_codes(
    rows: tuple[StrategyMarketResolutionDependencyRiskGateV2Row, ...],
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
        return selected[:1]
    return (f"resolution_dependency_risk_gate_{status}",)


def _validate_row(row: StrategyMarketResolutionDependencyRiskGateV2Row) -> None:
    if row.unresolved_source_risk != _subtract_decimal(ONE, row.source_confidence_ratio):
        raise ValueError("unresolved_source_risk must match confidence")
    expected_score = _dependency_risk_score(
        dependency_count_penalty=row.dependency_count_penalty,
        correlated_resolution_penalty=row.correlated_resolution_penalty,
        settlement_delay_penalty=row.settlement_delay_penalty,
        source_confidence_penalty=row.unresolved_source_risk,
        market_dependency_weight=row.market_dependency_weight,
    )
    if row.total_dependency_risk_score != expected_score:
        raise ValueError("total_dependency_risk_score must match row fields")
    if f"resolution_dependency_risk_gate_{row.dependency_risk_status}" not in row.reason_codes:
        raise ValueError("dependency_risk_status must match reason_codes")


def _validate_report(report: StrategyMarketResolutionDependencyRiskGateV2Report) -> None:
    rows = report.rows
    if report.candidate_count != _count_decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.blocked_count != _status_count(rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.paper_ok_count != _status_count(rows, PAPER_OK_STATUS):
        raise ValueError("paper_ok_count must match rows")
    if report.max_total_dependency_risk_score != _max_decimal(
        row.total_dependency_risk_score for row in rows
    ):
        raise ValueError("max_total_dependency_risk_score must match rows")
    if report.max_settlement_delay_hours != _max_decimal(
        row.settlement_delay_hours for row in rows
    ):
        raise ValueError("max_settlement_delay_hours must match rows")
    if report.max_correlated_resolution_count != _max_decimal(
        row.correlated_resolution_count for row in rows
    ):
        raise ValueError("max_correlated_resolution_count must match rows")
    if report.max_external_dependency_count != _max_decimal(
        row.external_dependency_count for row in rows
    ):
        raise ValueError("max_external_dependency_count must match rows")
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


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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


def _row_digest(row: StrategyMarketResolutionDependencyRiskGateV2Row) -> str:
    return _digest_for_value(row, skip=("derived_validation_digest",))


def _report_digest(report: StrategyMarketResolutionDependencyRiskGateV2Report) -> str:
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
    if type(value) is str:
        _reject_unsafe_public_text(value)
        return value
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (float, int):
        raise ValueError("public numeric value must be Decimal")
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            if field.name in skip:
                continue
            _reject_unsafe_public_text(field.name)
            ready[field.name] = _payload_value(getattr(value, field.name), skip=skip)
        return ready
    if isinstance(value, dict):
        ready = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(key)
            ready[key] = _payload_value(item, skip=skip)
        return ready
    if isinstance(value, (list, tuple)):
        return [_payload_value(item, skip=skip) for item in value]
    raise ValueError("value is not public payload serializable")


def _reject_unsafe_public_text(value: object) -> None:
    if type(value) is not str:
        return
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError("unsafe public text")
