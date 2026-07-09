"""Pure public settlement and resolution friction report."""

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
    "DEFAULT_RESEARCH_MARKET_SETTLEMENT_RESOLUTION_FRICTION_CONFIG_VERSION",
    "ResearchMarketSettlementResolutionFrictionCandidate",
    "ResearchMarketSettlementResolutionFrictionConfig",
    "ResearchMarketSettlementResolutionFrictionReasonCodeCount",
    "ResearchMarketSettlementResolutionFrictionReport",
    "ResearchMarketSettlementResolutionFrictionRow",
    "build_research_market_settlement_resolution_friction_report",
    "research_market_settlement_resolution_friction_digest",
    "research_market_settlement_resolution_friction_report_payload",
)


DEFAULT_RESEARCH_MARKET_SETTLEMENT_RESOLUTION_FRICTION_CONFIG_VERSION = (
    "research-market-settlement-resolution-friction-report-v0"
)
STATUSES = ("pass", "watch", "block")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {"block": 2, "watch": 1, "pass": 0}
NO_CANDIDATES_REASON = "no_settlement_resolution_friction_candidates"

ROW_REASON_CODES = (
    "settlement_resolution_friction_clear",
    "settlement_lag_watch",
    "settlement_lag_blocking",
    "resolution_ambiguity_watch",
    "resolution_ambiguity_blocking",
    "source_rule_alignment_gap_watch",
    "source_rule_alignment_gap_blocking",
    "fee_spread_drag_watch",
    "fee_spread_drag_blocking",
    "liquidity_constraint_watch",
    "liquidity_constraint_blocking",
    "composite_resolution_friction_watch",
    "composite_resolution_friction_blocking",
)
REPORT_REASON_CODES = (
    NO_CANDIDATES_REASON,
    "settlement_resolution_friction_report_clear",
    "settlement_lag_detected",
    "resolution_ambiguity_detected",
    "source_rule_alignment_gap_detected",
    "fee_spread_drag_detected",
    "liquidity_constraint_detected",
    "composite_resolution_friction_detected",
)
REASON_CODES = tuple(sorted(ROW_REASON_CODES + REPORT_REASON_CODES))
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "api" "_key",
    "auth",
    "authentication",
    "authorization",
    "buy",
    "candidate_id",
    "dsn",
    "exec" "ution",
    "live",
    "market_id",
    "market_slug",
    "order",
    "postgres",
    "private" "_key",
    "question",
    "recom" "mend",
    "recom" "mendation",
    "sec" "ret",
    "sell",
    "siz" "ing",
    "source_text",
    "source_url",
    "table_name",
    "token",
    "trade",
    "trading",
    "wallet",
)


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
class ResearchMarketSettlementResolutionFrictionConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_SETTLEMENT_RESOLUTION_FRICTION_CONFIG_VERSION
    )
    pass_max_friction_score: Decimal = Decimal("0.300000")
    watch_max_friction_score: Decimal = Decimal("0.650000")
    settlement_lag_watch_hours: Decimal = Decimal("24.000000")
    settlement_lag_block_hours: Decimal = Decimal("72.000000")
    resolution_ambiguity_watch_score: Decimal = Decimal("0.350000")
    resolution_ambiguity_block_score: Decimal = Decimal("0.800000")
    source_rule_alignment_watch_score: Decimal = Decimal("0.650000")
    source_rule_alignment_block_score: Decimal = Decimal("0.300000")
    fee_spread_drag_watch_ratio: Decimal = Decimal("0.020000")
    fee_spread_drag_block_ratio: Decimal = Decimal("0.060000")
    liquidity_constraint_watch_score: Decimal = Decimal("0.300000")
    liquidity_constraint_block_score: Decimal = Decimal("0.750000")
    settlement_lag_weight: Decimal = Decimal("0.200000")
    resolution_ambiguity_weight: Decimal = Decimal("0.250000")
    source_rule_alignment_weight: Decimal = Decimal("0.200000")
    fee_spread_drag_weight: Decimal = Decimal("0.150000")
    liquidity_constraint_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementResolutionFrictionConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_max_friction_score",
            "watch_max_friction_score",
            "resolution_ambiguity_watch_score",
            "resolution_ambiguity_block_score",
            "source_rule_alignment_watch_score",
            "source_rule_alignment_block_score",
            "fee_spread_drag_watch_ratio",
            "fee_spread_drag_block_ratio",
            "liquidity_constraint_watch_score",
            "liquidity_constraint_block_score",
            "settlement_lag_weight",
            "resolution_ambiguity_weight",
            "source_rule_alignment_weight",
            "fee_spread_drag_weight",
            "liquidity_constraint_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "settlement_lag_watch_hours",
            "settlement_lag_block_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "pass_max_friction_score",
            self.pass_max_friction_score,
            "watch_max_friction_score",
            self.watch_max_friction_score,
        )
        _require_threshold_pair(
            "settlement_lag_watch_hours",
            self.settlement_lag_watch_hours,
            "settlement_lag_block_hours",
            self.settlement_lag_block_hours,
        )
        _require_threshold_pair(
            "resolution_ambiguity_watch_score",
            self.resolution_ambiguity_watch_score,
            "resolution_ambiguity_block_score",
            self.resolution_ambiguity_block_score,
        )
        _require_descending_threshold_pair(
            "source_rule_alignment_watch_score",
            self.source_rule_alignment_watch_score,
            "source_rule_alignment_block_score",
            self.source_rule_alignment_block_score,
        )
        _require_threshold_pair(
            "fee_spread_drag_watch_ratio",
            self.fee_spread_drag_watch_ratio,
            "fee_spread_drag_block_ratio",
            self.fee_spread_drag_block_ratio,
        )
        _require_threshold_pair(
            "liquidity_constraint_watch_score",
            self.liquidity_constraint_watch_score,
            "liquidity_constraint_block_score",
            self.liquidity_constraint_block_score,
        )
        _require_weights_total_one(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketSettlementResolutionFrictionCandidate(_FinalPublicDataclass):
    raw_candidate_id: str
    observed_at: datetime
    settlement_lag_hours: Decimal
    resolution_ambiguity_score: Decimal
    source_rule_alignment_score: Decimal
    fee_spread_drag_ratio: Decimal
    liquidity_constraint_score: Decimal
    sensitive_context: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementResolutionFrictionCandidate,
            "candidate",
        )
        _require_nonblank_string("raw_candidate_id", self.raw_candidate_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "settlement_lag_hours",
            _normalize_nonnegative_decimal("settlement_lag_hours", self.settlement_lag_hours),
        )
        for field_name in (
            "resolution_ambiguity_score",
            "source_rule_alignment_score",
            "fee_spread_drag_ratio",
            "liquidity_constraint_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sensitive_context",
            _normalize_optional_string("sensitive_context", self.sensitive_context),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchMarketSettlementResolutionFrictionRow(_FinalPublicDataclass):
    row_number: Decimal
    observed_at: datetime
    settlement_lag_hours: Decimal
    settlement_lag_score: Decimal
    resolution_ambiguity_score: Decimal
    source_rule_gap_score: Decimal
    fee_spread_drag_ratio: Decimal
    fee_spread_drag_score: Decimal
    liquidity_constraint_score: Decimal
    friction_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementResolutionFrictionRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "settlement_lag_hours",
            _normalize_nonnegative_decimal("settlement_lag_hours", self.settlement_lag_hours),
        )
        for field_name in (
            "settlement_lag_score",
            "resolution_ambiguity_score",
            "source_rule_gap_score",
            "fee_spread_drag_ratio",
            "fee_spread_drag_score",
            "liquidity_constraint_score",
            "friction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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
class ResearchMarketSettlementResolutionFrictionReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementResolutionFrictionReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketSettlementResolutionFrictionReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    settlement_lag_count: Decimal
    resolution_ambiguity_count: Decimal
    source_rule_alignment_gap_count: Decimal
    fee_spread_drag_count: Decimal
    liquidity_constraint_count: Decimal
    mean_friction_score: Decimal
    mean_settlement_lag_hours: Decimal
    max_fee_spread_drag_ratio: Decimal
    status: str
    reason_code_counts: tuple[ResearchMarketSettlementResolutionFrictionReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketSettlementResolutionFrictionRow, ...]
    public_report_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementResolutionFrictionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "settlement_lag_count",
            "resolution_ambiguity_count",
            "source_rule_alignment_gap_count",
            "fee_spread_drag_count",
            "liquidity_constraint_count",
            "mean_friction_score",
            "mean_settlement_lag_hours",
            "max_fee_spread_drag_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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
    settlement_lag_hours: Decimal
    settlement_lag_score: Decimal
    resolution_ambiguity_score: Decimal
    source_rule_gap_score: Decimal
    fee_spread_drag_ratio: Decimal
    fee_spread_drag_score: Decimal
    liquidity_constraint_score: Decimal
    friction_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def build_research_market_settlement_resolution_friction_report(
    candidates: Iterable[ResearchMarketSettlementResolutionFrictionCandidate],
    *,
    config: ResearchMarketSettlementResolutionFrictionConfig,
    generated_at: datetime,
) -> ResearchMarketSettlementResolutionFrictionReport:
    if type(config) is not ResearchMarketSettlementResolutionFrictionConfig:
        raise ValueError(
            "config must be a ResearchMarketSettlementResolutionFrictionConfig",
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
        "settlement_lag_count": _reason_count(
            rows,
            ("settlement_lag_watch", "settlement_lag_blocking"),
        ),
        "resolution_ambiguity_count": _reason_count(
            rows,
            ("resolution_ambiguity_watch", "resolution_ambiguity_blocking"),
        ),
        "source_rule_alignment_gap_count": _reason_count(
            rows,
            ("source_rule_alignment_gap_watch", "source_rule_alignment_gap_blocking"),
        ),
        "fee_spread_drag_count": _reason_count(
            rows,
            ("fee_spread_drag_watch", "fee_spread_drag_blocking"),
        ),
        "liquidity_constraint_count": _reason_count(
            rows,
            ("liquidity_constraint_watch", "liquidity_constraint_blocking"),
        ),
        "mean_friction_score": _mean(tuple(row.friction_score for row in rows)),
        "mean_settlement_lag_hours": _mean(
            tuple(row.settlement_lag_hours for row in rows),
        ),
        "max_fee_spread_drag_ratio": _max_decimal(
            tuple(row.fee_spread_drag_ratio for row in rows),
        ),
        "status": _report_status(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
    }
    return ResearchMarketSettlementResolutionFrictionReport(
        **report_values,
        public_report_digest=_public_digest(_report_payload_without_digest(**report_values)),
    )


def research_market_settlement_resolution_friction_report_payload(
    report: ResearchMarketSettlementResolutionFrictionReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketSettlementResolutionFrictionReport:
        raise ValueError(
            "report must be a ResearchMarketSettlementResolutionFrictionReport",
        )
    _require_public_report_surface(report)
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


def research_market_settlement_resolution_friction_digest(
    report: ResearchMarketSettlementResolutionFrictionReport,
) -> str:
    payload = research_market_settlement_resolution_friction_report_payload(report)
    digest = payload.get("public_report_digest")
    if type(digest) is not str:
        raise ValueError("public_report_digest must be a string")
    return digest


def _row_draft(
    candidate: ResearchMarketSettlementResolutionFrictionCandidate,
    *,
    config: ResearchMarketSettlementResolutionFrictionConfig,
) -> _RowDraft:
    settlement_lag_score = _ratio_score(
        candidate.settlement_lag_hours,
        config.settlement_lag_block_hours,
    )
    source_rule_gap_score = _normalize_probability(
        "source_rule_gap_score",
        ONE - candidate.source_rule_alignment_score,
    )
    fee_spread_drag_score = _ratio_score(
        candidate.fee_spread_drag_ratio,
        config.fee_spread_drag_block_ratio,
    )
    friction_score = _weighted_score(
        settlement_lag_score=settlement_lag_score,
        resolution_ambiguity_score=candidate.resolution_ambiguity_score,
        source_rule_gap_score=source_rule_gap_score,
        fee_spread_drag_score=fee_spread_drag_score,
        liquidity_constraint_score=candidate.liquidity_constraint_score,
        config=config,
    )
    status = _row_status(
        candidate=candidate,
        friction_score=friction_score,
        config=config,
    )
    return _RowDraft(
        observed_at=candidate.observed_at,
        settlement_lag_hours=candidate.settlement_lag_hours,
        settlement_lag_score=settlement_lag_score,
        resolution_ambiguity_score=candidate.resolution_ambiguity_score,
        source_rule_gap_score=source_rule_gap_score,
        fee_spread_drag_ratio=candidate.fee_spread_drag_ratio,
        fee_spread_drag_score=fee_spread_drag_score,
        liquidity_constraint_score=candidate.liquidity_constraint_score,
        friction_score=friction_score,
        status=status,
        reason_codes=_row_reason_codes(
            candidate=candidate,
            friction_score=friction_score,
            config=config,
        ),
    )


def _row_from_draft(
    *,
    row_number: Decimal,
    draft: _RowDraft,
) -> ResearchMarketSettlementResolutionFrictionRow:
    return ResearchMarketSettlementResolutionFrictionRow(
        row_number=row_number,
        observed_at=draft.observed_at,
        settlement_lag_hours=draft.settlement_lag_hours,
        settlement_lag_score=draft.settlement_lag_score,
        resolution_ambiguity_score=draft.resolution_ambiguity_score,
        source_rule_gap_score=draft.source_rule_gap_score,
        fee_spread_drag_ratio=draft.fee_spread_drag_ratio,
        fee_spread_drag_score=draft.fee_spread_drag_score,
        liquidity_constraint_score=draft.liquidity_constraint_score,
        friction_score=draft.friction_score,
        status=draft.status,
        reason_codes=draft.reason_codes,
    )


def _weighted_score(
    *,
    settlement_lag_score: Decimal,
    resolution_ambiguity_score: Decimal,
    source_rule_gap_score: Decimal,
    fee_spread_drag_score: Decimal,
    liquidity_constraint_score: Decimal,
    config: ResearchMarketSettlementResolutionFrictionConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            settlement_lag_score * config.settlement_lag_weight
            + resolution_ambiguity_score * config.resolution_ambiguity_weight
            + source_rule_gap_score * config.source_rule_alignment_weight
            + fee_spread_drag_score * config.fee_spread_drag_weight
            + liquidity_constraint_score * config.liquidity_constraint_weight
        )
    return _normalize_probability("friction_score", score)


def _ratio_score(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        score = value / denominator
    if score >= ONE:
        return ONE
    return _normalize_probability("ratio_score", score)


def _row_status(
    *,
    candidate: ResearchMarketSettlementResolutionFrictionCandidate,
    friction_score: Decimal,
    config: ResearchMarketSettlementResolutionFrictionConfig,
) -> str:
    if (
        candidate.settlement_lag_hours >= config.settlement_lag_block_hours
        or candidate.resolution_ambiguity_score >= config.resolution_ambiguity_block_score
        or candidate.source_rule_alignment_score <= config.source_rule_alignment_block_score
        or candidate.fee_spread_drag_ratio >= config.fee_spread_drag_block_ratio
        or candidate.liquidity_constraint_score >= config.liquidity_constraint_block_score
        or friction_score > config.watch_max_friction_score
    ):
        return "block"
    if (
        candidate.settlement_lag_hours >= config.settlement_lag_watch_hours
        or candidate.resolution_ambiguity_score >= config.resolution_ambiguity_watch_score
        or candidate.source_rule_alignment_score <= config.source_rule_alignment_watch_score
        or candidate.fee_spread_drag_ratio >= config.fee_spread_drag_watch_ratio
        or candidate.liquidity_constraint_score >= config.liquidity_constraint_watch_score
        or friction_score > config.pass_max_friction_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    candidate: ResearchMarketSettlementResolutionFrictionCandidate,
    friction_score: Decimal,
    config: ResearchMarketSettlementResolutionFrictionConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_threshold_code(
        codes,
        candidate.settlement_lag_hours,
        config.settlement_lag_watch_hours,
        config.settlement_lag_block_hours,
        "settlement_lag_watch",
        "settlement_lag_blocking",
    )
    _append_threshold_code(
        codes,
        candidate.resolution_ambiguity_score,
        config.resolution_ambiguity_watch_score,
        config.resolution_ambiguity_block_score,
        "resolution_ambiguity_watch",
        "resolution_ambiguity_blocking",
    )
    _append_inverse_threshold_code(
        codes,
        candidate.source_rule_alignment_score,
        config.source_rule_alignment_watch_score,
        config.source_rule_alignment_block_score,
        "source_rule_alignment_gap_watch",
        "source_rule_alignment_gap_blocking",
    )
    _append_threshold_code(
        codes,
        candidate.fee_spread_drag_ratio,
        config.fee_spread_drag_watch_ratio,
        config.fee_spread_drag_block_ratio,
        "fee_spread_drag_watch",
        "fee_spread_drag_blocking",
    )
    _append_threshold_code(
        codes,
        candidate.liquidity_constraint_score,
        config.liquidity_constraint_watch_score,
        config.liquidity_constraint_block_score,
        "liquidity_constraint_watch",
        "liquidity_constraint_blocking",
    )
    _append_threshold_code(
        codes,
        friction_score,
        config.pass_max_friction_score,
        config.watch_max_friction_score,
        "composite_resolution_friction_watch",
        "composite_resolution_friction_blocking",
    )
    if not codes:
        return ("settlement_resolution_friction_clear",)
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
    if value <= block_threshold:
        codes.append(block_code)
    elif value <= watch_threshold:
        codes.append(watch_code)


def _report_status(rows: tuple[ResearchMarketSettlementResolutionFrictionRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketSettlementResolutionFrictionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    if all(row.status == "pass" for row in rows):
        return ("settlement_resolution_friction_report_clear",)
    codes: list[str] = []
    if _has_any_row_reason(rows, ("settlement_lag_watch", "settlement_lag_blocking")):
        codes.append("settlement_lag_detected")
    if _has_any_row_reason(
        rows,
        ("resolution_ambiguity_watch", "resolution_ambiguity_blocking"),
    ):
        codes.append("resolution_ambiguity_detected")
    if _has_any_row_reason(
        rows,
        ("source_rule_alignment_gap_watch", "source_rule_alignment_gap_blocking"),
    ):
        codes.append("source_rule_alignment_gap_detected")
    if _has_any_row_reason(rows, ("fee_spread_drag_watch", "fee_spread_drag_blocking")):
        codes.append("fee_spread_drag_detected")
    if _has_any_row_reason(
        rows,
        ("liquidity_constraint_watch", "liquidity_constraint_blocking"),
    ):
        codes.append("liquidity_constraint_detected")
    if _has_any_row_reason(
        rows,
        (
            "composite_resolution_friction_watch",
            "composite_resolution_friction_blocking",
        ),
    ):
        codes.append("composite_resolution_friction_detected")
    return tuple(codes)


def _reason_code_counts(
    rows: tuple[ResearchMarketSettlementResolutionFrictionRow, ...],
) -> tuple[ResearchMarketSettlementResolutionFrictionReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketSettlementResolutionFrictionReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ONE,
            ),
        )
    counts = Counter(code for row in rows for code in row.reason_codes)
    return tuple(
        ResearchMarketSettlementResolutionFrictionReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_candidates(
    candidates: Iterable[ResearchMarketSettlementResolutionFrictionCandidate],
) -> tuple[ResearchMarketSettlementResolutionFrictionCandidate, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Iterable):
        raise ValueError("candidates must be an iterable")
    normalized = tuple(candidates)
    for row in normalized:
        if type(row) is not ResearchMarketSettlementResolutionFrictionCandidate:
            raise ValueError(
                "candidates must contain ResearchMarketSettlementResolutionFrictionCandidate",
            )
        _require_hard_flags("candidate", row)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketSettlementResolutionFrictionRow],
) -> tuple[ResearchMarketSettlementResolutionFrictionRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketSettlementResolutionFrictionRow:
            raise ValueError(
                "rows must contain ResearchMarketSettlementResolutionFrictionRow",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketSettlementResolutionFrictionReasonCodeCount],
) -> tuple[ResearchMarketSettlementResolutionFrictionReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketSettlementResolutionFrictionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketSettlementResolutionFrictionReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row(row: ResearchMarketSettlementResolutionFrictionRow) -> None:
    if row.status == "block" and not any(code.endswith("_blocking") for code in row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != ("settlement_resolution_friction_clear",):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchMarketSettlementResolutionFrictionReport) -> None:
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
    if report.settlement_lag_count != _reason_count(
        report.rows,
        ("settlement_lag_watch", "settlement_lag_blocking"),
    ):
        raise ValueError("settlement_lag_count must match rows")
    if report.resolution_ambiguity_count != _reason_count(
        report.rows,
        ("resolution_ambiguity_watch", "resolution_ambiguity_blocking"),
    ):
        raise ValueError("resolution_ambiguity_count must match rows")
    if report.source_rule_alignment_gap_count != _reason_count(
        report.rows,
        ("source_rule_alignment_gap_watch", "source_rule_alignment_gap_blocking"),
    ):
        raise ValueError("source_rule_alignment_gap_count must match rows")
    if report.fee_spread_drag_count != _reason_count(
        report.rows,
        ("fee_spread_drag_watch", "fee_spread_drag_blocking"),
    ):
        raise ValueError("fee_spread_drag_count must match rows")
    if report.liquidity_constraint_count != _reason_count(
        report.rows,
        ("liquidity_constraint_watch", "liquidity_constraint_blocking"),
    ):
        raise ValueError("liquidity_constraint_count must match rows")
    if report.mean_friction_score != _mean(tuple(row.friction_score for row in report.rows)):
        raise ValueError("mean_friction_score must match rows")
    if report.mean_settlement_lag_hours != _mean(
        tuple(row.settlement_lag_hours for row in report.rows),
    ):
        raise ValueError("mean_settlement_lag_hours must match rows")
    if report.max_fee_spread_drag_ratio != _max_decimal(
        tuple(row.fee_spread_drag_ratio for row in report.rows),
    ):
        raise ValueError("max_fee_spread_drag_ratio must match rows")


def _report_payload_without_digest_from_report(
    report: ResearchMarketSettlementResolutionFrictionReport,
) -> dict[str, Any]:
    return _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        settlement_lag_count=report.settlement_lag_count,
        resolution_ambiguity_count=report.resolution_ambiguity_count,
        source_rule_alignment_gap_count=report.source_rule_alignment_gap_count,
        fee_spread_drag_count=report.fee_spread_drag_count,
        liquidity_constraint_count=report.liquidity_constraint_count,
        mean_friction_score=report.mean_friction_score,
        mean_settlement_lag_hours=report.mean_settlement_lag_hours,
        max_fee_spread_drag_ratio=report.max_fee_spread_drag_ratio,
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
        "settlement_lag_count": values["settlement_lag_count"],
        "resolution_ambiguity_count": values["resolution_ambiguity_count"],
        "source_rule_alignment_gap_count": values["source_rule_alignment_gap_count"],
        "fee_spread_drag_count": values["fee_spread_drag_count"],
        "liquidity_constraint_count": values["liquidity_constraint_count"],
        "mean_friction_score": values["mean_friction_score"],
        "mean_settlement_lag_hours": values["mean_settlement_lag_hours"],
        "max_fee_spread_drag_ratio": values["max_fee_spread_drag_ratio"],
        "status": values["status"],
        "reason_code_counts": values["reason_code_counts"],
        "reason_codes": values["reason_codes"],
        "rows": values["rows"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _expected_public_report_digest(
    report: ResearchMarketSettlementResolutionFrictionReport,
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
    if type(value) is ResearchMarketSettlementResolutionFrictionReasonCodeCount:
        return {
            "reason_code": value.reason_code,
            "count": _json_ready(value.count),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
    if type(value) is ResearchMarketSettlementResolutionFrictionRow:
        return {
            "row_number": _json_ready(value.row_number),
            "observed_at": _json_ready(value.observed_at),
            "settlement_lag_hours": _json_ready(value.settlement_lag_hours),
            "settlement_lag_score": _json_ready(value.settlement_lag_score),
            "resolution_ambiguity_score": _json_ready(
                value.resolution_ambiguity_score,
            ),
            "source_rule_gap_score": _json_ready(value.source_rule_gap_score),
            "fee_spread_drag_ratio": _json_ready(value.fee_spread_drag_ratio),
            "fee_spread_drag_score": _json_ready(value.fee_spread_drag_score),
            "liquidity_constraint_score": _json_ready(value.liquidity_constraint_score),
            "friction_score": _json_ready(value.friction_score),
            "status": value.status,
            "reason_codes": _json_ready(value.reason_codes),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int:
        raise ValueError("JSON value must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    raise ValueError(f"unsupported JSON value: {type(value).__name__}")


def _status_count(
    rows: tuple[ResearchMarketSettlementResolutionFrictionRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchMarketSettlementResolutionFrictionRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)))


def _has_any_row_reason(
    rows: tuple[ResearchMarketSettlementResolutionFrictionRow, ...],
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


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty")
    if not all(char.isalnum() or char in "._-" for char in value):
        raise ValueError(f"{field_name} must be public")
    canonical_value = f"_{value.lower().replace('.', '_').replace('-', '_')}_"
    if any(
        f"_{fragment}_" in canonical_value
        for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS
    ):
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _require_nonblank_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _normalize_optional_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_nonblank_string(field_name, value)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return value


def _normalize_reason_codes(
    field_name: str,
    reason_codes: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized = tuple(reason_codes)
    for reason_code in normalized:
        _require_member("reason_code", reason_code, allowed)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_threshold_pair(
    low_name: str,
    low_value: Decimal,
    high_name: str,
    high_value: Decimal,
) -> None:
    if high_value <= low_value:
        raise ValueError(f"{high_name} must exceed {low_name}")


def _require_descending_threshold_pair(
    high_name: str,
    high_value: Decimal,
    low_name: str,
    low_value: Decimal,
) -> None:
    if low_value >= high_value:
        raise ValueError(f"{low_name} must be less than {high_name}")


def _require_weights_total_one(
    config: ResearchMarketSettlementResolutionFrictionConfig,
) -> None:
    total = _quantize_decimal(
        config.settlement_lag_weight
        + config.resolution_ambiguity_weight
        + config.source_rule_alignment_weight
        + config.fee_spread_drag_weight
        + config.liquidity_constraint_weight,
    )
    if total != ONE:
        raise ValueError("friction weights must total one")


def _draft_sort_key(
    draft: _RowDraft,
) -> tuple[
    int,
    Decimal,
    datetime,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
]:
    return (
        -STATUS_WEIGHT[draft.status],
        -draft.friction_score,
        draft.observed_at,
        -draft.settlement_lag_hours,
        -draft.fee_spread_drag_ratio,
        -draft.resolution_ambiguity_score,
        -draft.source_rule_gap_score,
        -draft.fee_spread_drag_score,
        -draft.liquidity_constraint_score,
    )


def _row_sort_key(
    row: ResearchMarketSettlementResolutionFrictionRow,
) -> tuple[int, Decimal, Decimal]:
    return (-STATUS_WEIGHT[row.status], -row.friction_score, row.row_number)


def _require_public_report_surface(
    report: ResearchMarketSettlementResolutionFrictionReport,
) -> None:
    _require_hard_flags("report", report)
    for row in report.rows:
        _require_hard_flags("row", row)
    for count in report.reason_code_counts:
        _require_hard_flags("reason_code_count", count)
