"""Pure public settlement friction edge decay report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_SETTLEMENT_FRICTION_EDGE_DECAY_CONFIG_VERSION",
    "ResearchMarketSettlementFrictionEdgeDecayCandidate",
    "ResearchMarketSettlementFrictionEdgeDecayConfig",
    "ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount",
    "ResearchMarketSettlementFrictionEdgeDecayReport",
    "ResearchMarketSettlementFrictionEdgeDecayRow",
    "build_research_market_settlement_friction_edge_decay_report",
    "research_market_settlement_friction_edge_decay_digest",
    "research_market_settlement_friction_edge_decay_report_payload",
)


DEFAULT_RESEARCH_MARKET_SETTLEMENT_FRICTION_EDGE_DECAY_CONFIG_VERSION = (
    "research-market-settlement-friction-edge-decay-report-v0"
)
STATUSES = ("pass", "watch", "block")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {"block": 2, "watch": 1, "pass": 0}
NO_CANDIDATES_REASON = "no_settlement_friction_edge_decay_candidates"

ROW_REASON_CODES = (
    "settlement_friction_edge_decay_clear",
    "direct_cost_drag_watch",
    "direct_cost_drag_blocking",
    "liquidity_depth_shortfall_watch",
    "liquidity_depth_shortfall_blocking",
    "settlement_friction_watch",
    "settlement_friction_blocking",
    "time_to_resolution_decay_watch",
    "time_to_resolution_decay_blocking",
    "edge_decay_watch",
    "edge_decay_blocking",
    "net_edge_watch",
    "net_edge_blocking",
)
REPORT_REASON_CODES = (
    NO_CANDIDATES_REASON,
    "settlement_friction_edge_decay_report_clear",
    "direct_cost_drag_detected",
    "liquidity_depth_shortfall_detected",
    "settlement_friction_detected",
    "time_to_resolution_decay_detected",
    "edge_decay_detected",
    "net_edge_detected",
)
REASON_CODES = tuple(sorted(ROW_REASON_CODES + REPORT_REASON_CODES))


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchMarketSettlementFrictionEdgeDecayConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_SETTLEMENT_FRICTION_EDGE_DECAY_CONFIG_VERSION
    )
    pass_min_decayed_edge_ratio: Decimal = Decimal("0.030000")
    watch_min_decayed_edge_ratio: Decimal = Decimal("0.005000")
    direct_cost_drag_watch_ratio: Decimal = Decimal("0.020000")
    direct_cost_drag_block_ratio: Decimal = Decimal("0.060000")
    liquidity_depth_target_ratio: Decimal = Decimal("1.000000")
    liquidity_depth_shortfall_watch_score: Decimal = Decimal("0.200000")
    liquidity_depth_shortfall_block_score: Decimal = Decimal("0.600000")
    liquidity_depth_max_drag_ratio: Decimal = Decimal("0.020000")
    settlement_friction_watch_score: Decimal = Decimal("0.350000")
    settlement_friction_block_score: Decimal = Decimal("0.750000")
    settlement_friction_max_decay_ratio: Decimal = Decimal("0.030000")
    time_to_resolution_watch_hours: Decimal = Decimal("48.000000")
    time_to_resolution_block_hours: Decimal = Decimal("168.000000")
    time_to_resolution_max_decay_ratio: Decimal = Decimal("0.020000")
    edge_decay_watch_ratio: Decimal = Decimal("0.025000")
    edge_decay_block_ratio: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementFrictionEdgeDecayConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_min_decayed_edge_ratio",
            "watch_min_decayed_edge_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "direct_cost_drag_watch_ratio",
            "direct_cost_drag_block_ratio",
            "liquidity_depth_shortfall_watch_score",
            "liquidity_depth_shortfall_block_score",
            "liquidity_depth_max_drag_ratio",
            "settlement_friction_watch_score",
            "settlement_friction_block_score",
            "settlement_friction_max_decay_ratio",
            "time_to_resolution_max_decay_ratio",
            "edge_decay_watch_ratio",
            "edge_decay_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "liquidity_depth_target_ratio",
            "time_to_resolution_watch_hours",
            "time_to_resolution_block_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.liquidity_depth_target_ratio <= ZERO:
            raise ValueError("liquidity_depth_target_ratio must be positive")
        if self.watch_min_decayed_edge_ratio >= self.pass_min_decayed_edge_ratio:
            raise ValueError(
                "pass_min_decayed_edge_ratio must exceed watch_min_decayed_edge_ratio",
            )
        _require_threshold_pair(
            "direct_cost_drag_watch_ratio",
            self.direct_cost_drag_watch_ratio,
            "direct_cost_drag_block_ratio",
            self.direct_cost_drag_block_ratio,
        )
        _require_threshold_pair(
            "liquidity_depth_shortfall_watch_score",
            self.liquidity_depth_shortfall_watch_score,
            "liquidity_depth_shortfall_block_score",
            self.liquidity_depth_shortfall_block_score,
        )
        _require_threshold_pair(
            "settlement_friction_watch_score",
            self.settlement_friction_watch_score,
            "settlement_friction_block_score",
            self.settlement_friction_block_score,
        )
        _require_threshold_pair(
            "time_to_resolution_watch_hours",
            self.time_to_resolution_watch_hours,
            "time_to_resolution_block_hours",
            self.time_to_resolution_block_hours,
        )
        _require_threshold_pair(
            "edge_decay_watch_ratio",
            self.edge_decay_watch_ratio,
            "edge_decay_block_ratio",
            self.edge_decay_block_ratio,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketSettlementFrictionEdgeDecayCandidate(_FinalPublicDataclass):
    raw_candidate_id: str
    observed_at: datetime
    gross_edge_ratio: Decimal
    fee_drag_ratio: Decimal
    spread_drag_ratio: Decimal
    slippage_drag_ratio: Decimal
    liquidity_depth_coverage_ratio: Decimal
    settlement_friction_score: Decimal
    time_to_resolution_hours: Decimal
    sensitive_context: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementFrictionEdgeDecayCandidate,
            "candidate",
        )
        _require_nonblank_string("raw_candidate_id", self.raw_candidate_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "gross_edge_ratio",
            "fee_drag_ratio",
            "spread_drag_ratio",
            "slippage_drag_ratio",
            "settlement_friction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "liquidity_depth_coverage_ratio",
            "time_to_resolution_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sensitive_context",
            _normalize_optional_string("sensitive_context", self.sensitive_context),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchMarketSettlementFrictionEdgeDecayRow(_FinalPublicDataclass):
    row_number: Decimal
    observed_at: datetime
    gross_edge_ratio: Decimal
    fee_drag_ratio: Decimal
    spread_drag_ratio: Decimal
    slippage_drag_ratio: Decimal
    liquidity_depth_coverage_ratio: Decimal
    liquidity_depth_shortfall_score: Decimal
    liquidity_depth_drag_ratio: Decimal
    direct_cost_drag_ratio: Decimal
    cost_adjusted_edge_ratio: Decimal
    settlement_friction_score: Decimal
    settlement_friction_decay_ratio: Decimal
    time_to_resolution_hours: Decimal
    time_decay_score: Decimal
    time_decay_ratio: Decimal
    total_edge_decay_ratio: Decimal
    decayed_edge_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementFrictionEdgeDecayRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "gross_edge_ratio",
            "fee_drag_ratio",
            "spread_drag_ratio",
            "slippage_drag_ratio",
            "liquidity_depth_shortfall_score",
            "liquidity_depth_drag_ratio",
            "direct_cost_drag_ratio",
            "settlement_friction_score",
            "settlement_friction_decay_ratio",
            "time_decay_score",
            "time_decay_ratio",
            "total_edge_decay_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "liquidity_depth_coverage_ratio",
            "time_to_resolution_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("cost_adjusted_edge_ratio", "decayed_edge_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketSettlementFrictionEdgeDecayReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    direct_cost_drag_count: Decimal
    liquidity_depth_shortfall_count: Decimal
    settlement_friction_count: Decimal
    time_to_resolution_decay_count: Decimal
    edge_decay_count: Decimal
    net_edge_count: Decimal
    mean_direct_cost_drag_ratio: Decimal
    mean_total_edge_decay_ratio: Decimal
    mean_decayed_edge_ratio: Decimal
    min_decayed_edge_ratio: Decimal
    max_total_edge_decay_ratio: Decimal
    status: str
    reason_code_counts: tuple[ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketSettlementFrictionEdgeDecayRow, ...]
    public_report_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementFrictionEdgeDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "direct_cost_drag_count",
            "liquidity_depth_shortfall_count",
            "settlement_friction_count",
            "time_to_resolution_decay_count",
            "edge_decay_count",
            "net_edge_count",
            "mean_direct_cost_drag_ratio",
            "mean_total_edge_decay_ratio",
            "max_total_edge_decay_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_decayed_edge_ratio", "min_decayed_edge_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
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
        _require_digest("public_report_digest", self.public_report_digest)
        _validate_report(self)
        if self.public_report_digest != _expected_public_report_digest(self):
            raise ValueError("public_report_digest must match public report payload")
        _require_hard_flags("report", self)


@dataclass(frozen=True)
class _RowDraft:
    observed_at: datetime
    gross_edge_ratio: Decimal
    fee_drag_ratio: Decimal
    spread_drag_ratio: Decimal
    slippage_drag_ratio: Decimal
    liquidity_depth_coverage_ratio: Decimal
    liquidity_depth_shortfall_score: Decimal
    liquidity_depth_drag_ratio: Decimal
    direct_cost_drag_ratio: Decimal
    cost_adjusted_edge_ratio: Decimal
    settlement_friction_score: Decimal
    settlement_friction_decay_ratio: Decimal
    time_to_resolution_hours: Decimal
    time_decay_score: Decimal
    time_decay_ratio: Decimal
    total_edge_decay_ratio: Decimal
    decayed_edge_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]


def build_research_market_settlement_friction_edge_decay_report(
    candidates: Iterable[ResearchMarketSettlementFrictionEdgeDecayCandidate],
    *,
    config: ResearchMarketSettlementFrictionEdgeDecayConfig,
    generated_at: datetime,
) -> ResearchMarketSettlementFrictionEdgeDecayReport:
    if type(config) is not ResearchMarketSettlementFrictionEdgeDecayConfig:
        raise ValueError(
            "config must be a ResearchMarketSettlementFrictionEdgeDecayConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidate_rows = _normalize_candidates(candidates)
    for row in candidate_rows:
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at must be less than or equal to generated_at")
    drafts = tuple(_row_draft(row, config=config) for row in candidate_rows)
    rows = tuple(
        _row_from_draft(row_number=_count(index), draft=draft)
        for index, draft in enumerate(sorted(drafts, key=_draft_sort_key), start=1)
    )
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "direct_cost_drag_count": _reason_count(
            rows,
            ("direct_cost_drag_watch", "direct_cost_drag_blocking"),
        ),
        "liquidity_depth_shortfall_count": _reason_count(
            rows,
            ("liquidity_depth_shortfall_watch", "liquidity_depth_shortfall_blocking"),
        ),
        "settlement_friction_count": _reason_count(
            rows,
            ("settlement_friction_watch", "settlement_friction_blocking"),
        ),
        "time_to_resolution_decay_count": _reason_count(
            rows,
            ("time_to_resolution_decay_watch", "time_to_resolution_decay_blocking"),
        ),
        "edge_decay_count": _reason_count(
            rows,
            ("edge_decay_watch", "edge_decay_blocking"),
        ),
        "net_edge_count": _reason_count(
            rows,
            ("net_edge_watch", "net_edge_blocking"),
        ),
        "mean_direct_cost_drag_ratio": _mean(
            tuple(row.direct_cost_drag_ratio for row in rows),
        ),
        "mean_total_edge_decay_ratio": _mean(
            tuple(row.total_edge_decay_ratio for row in rows),
        ),
        "mean_decayed_edge_ratio": _mean(
            tuple(row.decayed_edge_ratio for row in rows),
        ),
        "min_decayed_edge_ratio": _min_decimal(
            tuple(row.decayed_edge_ratio for row in rows),
        ),
        "max_total_edge_decay_ratio": _max_decimal(
            tuple(row.total_edge_decay_ratio for row in rows),
        ),
        "status": _report_status(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
    }
    return ResearchMarketSettlementFrictionEdgeDecayReport(
        **report_values,
        public_report_digest=_public_digest(_report_payload_without_digest(**report_values)),
    )


def research_market_settlement_friction_edge_decay_report_payload(
    report: ResearchMarketSettlementFrictionEdgeDecayReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketSettlementFrictionEdgeDecayReport:
        raise ValueError(
            "report must be a ResearchMarketSettlementFrictionEdgeDecayReport",
        )
    _validate_report(report)
    if report.public_report_digest != _expected_public_report_digest(report):
        raise ValueError("public_report_digest must match public report payload")
    payload = _report_payload_without_digest_from_report(report)
    payload["public_report_digest"] = report.public_report_digest
    payload["paper_only"] = True
    payload["report_only"] = True
    payload["readonly"] = True
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    return ready


def research_market_settlement_friction_edge_decay_digest(
    report: ResearchMarketSettlementFrictionEdgeDecayReport,
) -> str:
    payload = research_market_settlement_friction_edge_decay_report_payload(report)
    digest = payload.get("public_report_digest")
    if type(digest) is not str:
        raise ValueError("public_report_digest must be a string")
    return digest


def _row_draft(
    candidate: ResearchMarketSettlementFrictionEdgeDecayCandidate,
    *,
    config: ResearchMarketSettlementFrictionEdgeDecayConfig,
) -> _RowDraft:
    liquidity_depth_shortfall_score = _liquidity_depth_shortfall_score(
        candidate.liquidity_depth_coverage_ratio,
        config.liquidity_depth_target_ratio,
    )
    liquidity_depth_drag_ratio = _multiply_probability(
        liquidity_depth_shortfall_score,
        config.liquidity_depth_max_drag_ratio,
    )
    direct_cost_drag_ratio = _sum_probabilities(
        (
            candidate.fee_drag_ratio,
            candidate.spread_drag_ratio,
            candidate.slippage_drag_ratio,
            liquidity_depth_drag_ratio,
        ),
        "direct_cost_drag_ratio",
    )
    cost_adjusted_edge_ratio = _subtract_decimal(
        candidate.gross_edge_ratio,
        direct_cost_drag_ratio,
    )
    settlement_friction_decay_ratio = _multiply_probability(
        candidate.settlement_friction_score,
        config.settlement_friction_max_decay_ratio,
    )
    time_decay_score = _ratio_score(
        candidate.time_to_resolution_hours,
        config.time_to_resolution_block_hours,
    )
    time_decay_ratio = _multiply_probability(
        time_decay_score,
        config.time_to_resolution_max_decay_ratio,
    )
    total_edge_decay_ratio = _sum_probabilities(
        (settlement_friction_decay_ratio, time_decay_ratio),
        "total_edge_decay_ratio",
    )
    decayed_edge_ratio = _subtract_decimal(
        cost_adjusted_edge_ratio,
        total_edge_decay_ratio,
    )
    status = _row_status(
        direct_cost_drag_ratio=direct_cost_drag_ratio,
        liquidity_depth_shortfall_score=liquidity_depth_shortfall_score,
        settlement_friction_score=candidate.settlement_friction_score,
        time_to_resolution_hours=candidate.time_to_resolution_hours,
        total_edge_decay_ratio=total_edge_decay_ratio,
        decayed_edge_ratio=decayed_edge_ratio,
        config=config,
    )
    return _RowDraft(
        observed_at=candidate.observed_at,
        gross_edge_ratio=candidate.gross_edge_ratio,
        fee_drag_ratio=candidate.fee_drag_ratio,
        spread_drag_ratio=candidate.spread_drag_ratio,
        slippage_drag_ratio=candidate.slippage_drag_ratio,
        liquidity_depth_coverage_ratio=candidate.liquidity_depth_coverage_ratio,
        liquidity_depth_shortfall_score=liquidity_depth_shortfall_score,
        liquidity_depth_drag_ratio=liquidity_depth_drag_ratio,
        direct_cost_drag_ratio=direct_cost_drag_ratio,
        cost_adjusted_edge_ratio=cost_adjusted_edge_ratio,
        settlement_friction_score=candidate.settlement_friction_score,
        settlement_friction_decay_ratio=settlement_friction_decay_ratio,
        time_to_resolution_hours=candidate.time_to_resolution_hours,
        time_decay_score=time_decay_score,
        time_decay_ratio=time_decay_ratio,
        total_edge_decay_ratio=total_edge_decay_ratio,
        decayed_edge_ratio=decayed_edge_ratio,
        status=status,
        reason_codes=_row_reason_codes(
            direct_cost_drag_ratio=direct_cost_drag_ratio,
            liquidity_depth_shortfall_score=liquidity_depth_shortfall_score,
            settlement_friction_score=candidate.settlement_friction_score,
            time_to_resolution_hours=candidate.time_to_resolution_hours,
            total_edge_decay_ratio=total_edge_decay_ratio,
            decayed_edge_ratio=decayed_edge_ratio,
            config=config,
        ),
    )


def _row_from_draft(
    *,
    row_number: Decimal,
    draft: _RowDraft,
) -> ResearchMarketSettlementFrictionEdgeDecayRow:
    return ResearchMarketSettlementFrictionEdgeDecayRow(
        row_number=row_number,
        observed_at=draft.observed_at,
        gross_edge_ratio=draft.gross_edge_ratio,
        fee_drag_ratio=draft.fee_drag_ratio,
        spread_drag_ratio=draft.spread_drag_ratio,
        slippage_drag_ratio=draft.slippage_drag_ratio,
        liquidity_depth_coverage_ratio=draft.liquidity_depth_coverage_ratio,
        liquidity_depth_shortfall_score=draft.liquidity_depth_shortfall_score,
        liquidity_depth_drag_ratio=draft.liquidity_depth_drag_ratio,
        direct_cost_drag_ratio=draft.direct_cost_drag_ratio,
        cost_adjusted_edge_ratio=draft.cost_adjusted_edge_ratio,
        settlement_friction_score=draft.settlement_friction_score,
        settlement_friction_decay_ratio=draft.settlement_friction_decay_ratio,
        time_to_resolution_hours=draft.time_to_resolution_hours,
        time_decay_score=draft.time_decay_score,
        time_decay_ratio=draft.time_decay_ratio,
        total_edge_decay_ratio=draft.total_edge_decay_ratio,
        decayed_edge_ratio=draft.decayed_edge_ratio,
        status=draft.status,
        reason_codes=draft.reason_codes,
    )


def _liquidity_depth_shortfall_score(
    coverage_ratio: Decimal,
    target_ratio: Decimal,
) -> Decimal:
    if coverage_ratio >= target_ratio:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        score = (target_ratio - coverage_ratio) / target_ratio
    if score >= ONE:
        return ONE
    return _normalize_probability("liquidity_depth_shortfall_score", score)


def _ratio_score(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        score = value / denominator
    if score >= ONE:
        return ONE
    return _normalize_probability("ratio_score", score)


def _multiply_probability(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("multiplied_probability", left * right)


def _sum_probabilities(values: tuple[Decimal, ...], field_name: str) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = sum(values, ZERO)
    return _normalize_probability(field_name, value)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("decimal_difference", left - right)


def _row_status(
    *,
    direct_cost_drag_ratio: Decimal,
    liquidity_depth_shortfall_score: Decimal,
    settlement_friction_score: Decimal,
    time_to_resolution_hours: Decimal,
    total_edge_decay_ratio: Decimal,
    decayed_edge_ratio: Decimal,
    config: ResearchMarketSettlementFrictionEdgeDecayConfig,
) -> str:
    if (
        direct_cost_drag_ratio >= config.direct_cost_drag_block_ratio
        or liquidity_depth_shortfall_score
        >= config.liquidity_depth_shortfall_block_score
        or settlement_friction_score >= config.settlement_friction_block_score
        or time_to_resolution_hours >= config.time_to_resolution_block_hours
        or total_edge_decay_ratio >= config.edge_decay_block_ratio
        or decayed_edge_ratio < config.watch_min_decayed_edge_ratio
    ):
        return "block"
    if (
        direct_cost_drag_ratio >= config.direct_cost_drag_watch_ratio
        or liquidity_depth_shortfall_score
        >= config.liquidity_depth_shortfall_watch_score
        or settlement_friction_score >= config.settlement_friction_watch_score
        or time_to_resolution_hours >= config.time_to_resolution_watch_hours
        or total_edge_decay_ratio >= config.edge_decay_watch_ratio
        or decayed_edge_ratio < config.pass_min_decayed_edge_ratio
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    direct_cost_drag_ratio: Decimal,
    liquidity_depth_shortfall_score: Decimal,
    settlement_friction_score: Decimal,
    time_to_resolution_hours: Decimal,
    total_edge_decay_ratio: Decimal,
    decayed_edge_ratio: Decimal,
    config: ResearchMarketSettlementFrictionEdgeDecayConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_threshold_code(
        codes,
        direct_cost_drag_ratio,
        config.direct_cost_drag_watch_ratio,
        config.direct_cost_drag_block_ratio,
        "direct_cost_drag_watch",
        "direct_cost_drag_blocking",
    )
    _append_threshold_code(
        codes,
        liquidity_depth_shortfall_score,
        config.liquidity_depth_shortfall_watch_score,
        config.liquidity_depth_shortfall_block_score,
        "liquidity_depth_shortfall_watch",
        "liquidity_depth_shortfall_blocking",
    )
    _append_threshold_code(
        codes,
        settlement_friction_score,
        config.settlement_friction_watch_score,
        config.settlement_friction_block_score,
        "settlement_friction_watch",
        "settlement_friction_blocking",
    )
    _append_threshold_code(
        codes,
        time_to_resolution_hours,
        config.time_to_resolution_watch_hours,
        config.time_to_resolution_block_hours,
        "time_to_resolution_decay_watch",
        "time_to_resolution_decay_blocking",
    )
    _append_threshold_code(
        codes,
        total_edge_decay_ratio,
        config.edge_decay_watch_ratio,
        config.edge_decay_block_ratio,
        "edge_decay_watch",
        "edge_decay_blocking",
    )
    _append_inverse_threshold_code(
        codes,
        decayed_edge_ratio,
        config.pass_min_decayed_edge_ratio,
        config.watch_min_decayed_edge_ratio,
        "net_edge_watch",
        "net_edge_blocking",
    )
    if not codes:
        return ("settlement_friction_edge_decay_clear",)
    return tuple(codes)


def _append_threshold_code(
    codes: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if value >= block_threshold:
        codes.append(block_code)
    elif value >= watch_threshold:
        codes.append(watch_code)


def _append_inverse_threshold_code(
    codes: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if value < block_threshold:
        codes.append(block_code)
    elif value < watch_threshold:
        codes.append(watch_code)


def _report_status(rows: tuple[ResearchMarketSettlementFrictionEdgeDecayRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketSettlementFrictionEdgeDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    if all(row.status == "pass" for row in rows):
        return ("settlement_friction_edge_decay_report_clear",)
    codes: list[str] = []
    if _has_any_row_reason(rows, ("direct_cost_drag_watch", "direct_cost_drag_blocking")):
        codes.append("direct_cost_drag_detected")
    if _has_any_row_reason(
        rows,
        ("liquidity_depth_shortfall_watch", "liquidity_depth_shortfall_blocking"),
    ):
        codes.append("liquidity_depth_shortfall_detected")
    if _has_any_row_reason(
        rows,
        ("settlement_friction_watch", "settlement_friction_blocking"),
    ):
        codes.append("settlement_friction_detected")
    if _has_any_row_reason(
        rows,
        ("time_to_resolution_decay_watch", "time_to_resolution_decay_blocking"),
    ):
        codes.append("time_to_resolution_decay_detected")
    if _has_any_row_reason(rows, ("edge_decay_watch", "edge_decay_blocking")):
        codes.append("edge_decay_detected")
    if _has_any_row_reason(rows, ("net_edge_watch", "net_edge_blocking")):
        codes.append("net_edge_detected")
    return tuple(codes)


def _reason_code_counts(
    rows: tuple[ResearchMarketSettlementFrictionEdgeDecayRow, ...],
) -> tuple[ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ONE,
            ),
        )
    counts = Counter(code for row in rows for code in row.reason_codes)
    return tuple(
        ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_candidates(
    candidates: Iterable[ResearchMarketSettlementFrictionEdgeDecayCandidate],
) -> tuple[ResearchMarketSettlementFrictionEdgeDecayCandidate, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Iterable):
        raise ValueError("candidates must be an iterable")
    normalized = tuple(candidates)
    for row in normalized:
        if type(row) is not ResearchMarketSettlementFrictionEdgeDecayCandidate:
            raise ValueError(
                "candidates must contain ResearchMarketSettlementFrictionEdgeDecayCandidate",
            )
        _require_hard_flags("candidate", row)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketSettlementFrictionEdgeDecayRow],
) -> tuple[ResearchMarketSettlementFrictionEdgeDecayRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketSettlementFrictionEdgeDecayRow:
            raise ValueError("rows must contain ResearchMarketSettlementFrictionEdgeDecayRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount],
) -> tuple[ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row(row: ResearchMarketSettlementFrictionEdgeDecayRow) -> None:
    if row.status == "block" and not any(code.endswith("_blocking") for code in row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != ("settlement_friction_edge_decay_clear",):
        raise ValueError("status must match reason_codes")
    if row.direct_cost_drag_ratio != _sum_probabilities(
        (
            row.fee_drag_ratio,
            row.spread_drag_ratio,
            row.slippage_drag_ratio,
            row.liquidity_depth_drag_ratio,
        ),
        "direct_cost_drag_ratio",
    ):
        raise ValueError("direct_cost_drag_ratio must match component drags")
    if row.cost_adjusted_edge_ratio != _subtract_decimal(
        row.gross_edge_ratio,
        row.direct_cost_drag_ratio,
    ):
        raise ValueError("cost_adjusted_edge_ratio must match gross edge and costs")
    if row.total_edge_decay_ratio != _sum_probabilities(
        (row.settlement_friction_decay_ratio, row.time_decay_ratio),
        "total_edge_decay_ratio",
    ):
        raise ValueError("total_edge_decay_ratio must match decay inputs")
    if row.decayed_edge_ratio != _subtract_decimal(
        row.cost_adjusted_edge_ratio,
        row.total_edge_decay_ratio,
    ):
        raise ValueError("decayed_edge_ratio must match cost adjusted edge and decay")


def _validate_report(report: ResearchMarketSettlementFrictionEdgeDecayReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.candidate_count:
        raise ValueError("status counts must match candidate_count")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.direct_cost_drag_count != _reason_count(
        report.rows,
        ("direct_cost_drag_watch", "direct_cost_drag_blocking"),
    ):
        raise ValueError("direct_cost_drag_count must match rows")
    if report.liquidity_depth_shortfall_count != _reason_count(
        report.rows,
        ("liquidity_depth_shortfall_watch", "liquidity_depth_shortfall_blocking"),
    ):
        raise ValueError("liquidity_depth_shortfall_count must match rows")
    if report.settlement_friction_count != _reason_count(
        report.rows,
        ("settlement_friction_watch", "settlement_friction_blocking"),
    ):
        raise ValueError("settlement_friction_count must match rows")
    if report.time_to_resolution_decay_count != _reason_count(
        report.rows,
        ("time_to_resolution_decay_watch", "time_to_resolution_decay_blocking"),
    ):
        raise ValueError("time_to_resolution_decay_count must match rows")
    if report.edge_decay_count != _reason_count(
        report.rows,
        ("edge_decay_watch", "edge_decay_blocking"),
    ):
        raise ValueError("edge_decay_count must match rows")
    if report.net_edge_count != _reason_count(
        report.rows,
        ("net_edge_watch", "net_edge_blocking"),
    ):
        raise ValueError("net_edge_count must match rows")
    if report.mean_direct_cost_drag_ratio != _mean(
        tuple(row.direct_cost_drag_ratio for row in report.rows),
    ):
        raise ValueError("mean_direct_cost_drag_ratio must match rows")
    if report.mean_total_edge_decay_ratio != _mean(
        tuple(row.total_edge_decay_ratio for row in report.rows),
    ):
        raise ValueError("mean_total_edge_decay_ratio must match rows")
    if report.mean_decayed_edge_ratio != _mean(
        tuple(row.decayed_edge_ratio for row in report.rows),
    ):
        raise ValueError("mean_decayed_edge_ratio must match rows")
    if report.min_decayed_edge_ratio != _min_decimal(
        tuple(row.decayed_edge_ratio for row in report.rows),
    ):
        raise ValueError("min_decayed_edge_ratio must match rows")
    if report.max_total_edge_decay_ratio != _max_decimal(
        tuple(row.total_edge_decay_ratio for row in report.rows),
    ):
        raise ValueError("max_total_edge_decay_ratio must match rows")


def _report_payload_without_digest_from_report(
    report: ResearchMarketSettlementFrictionEdgeDecayReport,
) -> dict[str, Any]:
    return _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        direct_cost_drag_count=report.direct_cost_drag_count,
        liquidity_depth_shortfall_count=report.liquidity_depth_shortfall_count,
        settlement_friction_count=report.settlement_friction_count,
        time_to_resolution_decay_count=report.time_to_resolution_decay_count,
        edge_decay_count=report.edge_decay_count,
        net_edge_count=report.net_edge_count,
        mean_direct_cost_drag_ratio=report.mean_direct_cost_drag_ratio,
        mean_total_edge_decay_ratio=report.mean_total_edge_decay_ratio,
        mean_decayed_edge_ratio=report.mean_decayed_edge_ratio,
        min_decayed_edge_ratio=report.min_decayed_edge_ratio,
        max_total_edge_decay_ratio=report.max_total_edge_decay_ratio,
        status=report.status,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        rows=report.rows,
    )


def _report_payload_without_digest(**values: Any) -> dict[str, Any]:
    return {
        "generated_at": values["generated_at"],
        "config_version": values["config_version"],
        "candidate_count": values["candidate_count"],
        "pass_count": values["pass_count"],
        "watch_count": values["watch_count"],
        "block_count": values["block_count"],
        "direct_cost_drag_count": values["direct_cost_drag_count"],
        "liquidity_depth_shortfall_count": values["liquidity_depth_shortfall_count"],
        "settlement_friction_count": values["settlement_friction_count"],
        "time_to_resolution_decay_count": values["time_to_resolution_decay_count"],
        "edge_decay_count": values["edge_decay_count"],
        "net_edge_count": values["net_edge_count"],
        "mean_direct_cost_drag_ratio": values["mean_direct_cost_drag_ratio"],
        "mean_total_edge_decay_ratio": values["mean_total_edge_decay_ratio"],
        "mean_decayed_edge_ratio": values["mean_decayed_edge_ratio"],
        "min_decayed_edge_ratio": values["min_decayed_edge_ratio"],
        "max_total_edge_decay_ratio": values["max_total_edge_decay_ratio"],
        "status": values["status"],
        "reason_code_counts": values["reason_code_counts"],
        "reason_codes": values["reason_codes"],
        "rows": values["rows"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _expected_public_report_digest(
    report: ResearchMarketSettlementFrictionEdgeDecayReport,
) -> str:
    return _public_digest(_report_payload_without_digest_from_report(report))


def _public_digest(payload: dict[str, Any]) -> str:
    ready = _json_ready(payload)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return format(value, ".6f")
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) is ResearchMarketSettlementFrictionEdgeDecayReasonCodeCount:
        return {
            "reason_code": value.reason_code,
            "count": _json_ready(value.count),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
    if type(value) is ResearchMarketSettlementFrictionEdgeDecayRow:
        return {
            "row_number": _json_ready(value.row_number),
            "observed_at": _json_ready(value.observed_at),
            "gross_edge_ratio": _json_ready(value.gross_edge_ratio),
            "fee_drag_ratio": _json_ready(value.fee_drag_ratio),
            "spread_drag_ratio": _json_ready(value.spread_drag_ratio),
            "slippage_drag_ratio": _json_ready(value.slippage_drag_ratio),
            "liquidity_depth_coverage_ratio": _json_ready(
                value.liquidity_depth_coverage_ratio,
            ),
            "liquidity_depth_shortfall_score": _json_ready(
                value.liquidity_depth_shortfall_score,
            ),
            "liquidity_depth_drag_ratio": _json_ready(value.liquidity_depth_drag_ratio),
            "direct_cost_drag_ratio": _json_ready(value.direct_cost_drag_ratio),
            "cost_adjusted_edge_ratio": _json_ready(value.cost_adjusted_edge_ratio),
            "settlement_friction_score": _json_ready(value.settlement_friction_score),
            "settlement_friction_decay_ratio": _json_ready(
                value.settlement_friction_decay_ratio,
            ),
            "time_to_resolution_hours": _json_ready(value.time_to_resolution_hours),
            "time_decay_score": _json_ready(value.time_decay_score),
            "time_decay_ratio": _json_ready(value.time_decay_ratio),
            "total_edge_decay_ratio": _json_ready(value.total_edge_decay_ratio),
            "decayed_edge_ratio": _json_ready(value.decayed_edge_ratio),
            "status": value.status,
            "reason_codes": _json_ready(value.reason_codes),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int:
        return value
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    raise ValueError(f"unsupported JSON value: {type(value).__name__}")


def _status_count(
    rows: tuple[ResearchMarketSettlementFrictionEdgeDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchMarketSettlementFrictionEdgeDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)))


def _has_any_row_reason(
    rows: tuple[ResearchMarketSettlementFrictionEdgeDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> bool:
    return any(any(code in row.reason_codes for code in reason_codes) for row in rows)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal(max(values))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal(min(values))


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize_decimal(value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer count")
    return normalized.quantize(COUNT_QUANTUM)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for value in normalized:
        _require_member(field_name, value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _normalize_optional_string(field_name: str, value: str | None) -> str | None:
    if value is None:
        return None
    _require_nonblank_string(field_name, value)
    return value


def _require_public_string(field_name: str, value: str) -> None:
    _require_nonblank_string(field_name, value)
    lowered = value.lower()
    for unsafe in ("http://", "https://", "postgres://", "token", "wallet"):
        if unsafe in lowered:
            raise ValueError(f"{field_name} must be public-safe")


def _require_nonblank_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_name} must exceed {watch_name}")


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _draft_sort_key(draft: _RowDraft) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        _count(-STATUS_WEIGHT[draft.status]),
        draft.decayed_edge_ratio,
        _quantize_decimal(-draft.total_edge_decay_ratio),
        draft.observed_at.isoformat(),
    )


def _row_sort_key(
    row: ResearchMarketSettlementFrictionEdgeDecayRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        _count(-STATUS_WEIGHT[row.status]),
        row.decayed_edge_ratio,
        _quantize_decimal(-row.total_edge_decay_ratio),
        row.observed_at.isoformat(),
    )
