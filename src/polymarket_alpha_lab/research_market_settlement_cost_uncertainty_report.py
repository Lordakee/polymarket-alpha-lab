"""Pure public settlement cost uncertainty report."""

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
    "DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_UNCERTAINTY_CONFIG_VERSION",
    "ResearchMarketSettlementCostUncertaintyCandidate",
    "ResearchMarketSettlementCostUncertaintyConfig",
    "ResearchMarketSettlementCostUncertaintyReasonCodeCount",
    "ResearchMarketSettlementCostUncertaintyReport",
    "ResearchMarketSettlementCostUncertaintyRow",
    "build_research_market_settlement_cost_uncertainty_report",
    "research_market_settlement_cost_uncertainty_digest",
    "research_market_settlement_cost_uncertainty_report_payload",
)


DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_UNCERTAINTY_CONFIG_VERSION = (
    "research-market-settlement-cost-uncertainty-report-v0"
)
STATUSES = ("pass", "watch", "block")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {"block": 2, "watch": 1, "pass": 0}
NO_CANDIDATES_REASON = "no_settlement_cost_uncertainty_candidates"

ROW_REASON_CODES = (
    "settlement_cost_uncertainty_clear",
    "resolution_timing_uncertainty_watch",
    "resolution_timing_uncertainty_blocking",
    "settlement_lag_watch",
    "settlement_lag_blocking",
    "fee_spread_haircut_watch",
    "fee_spread_haircut_blocking",
    "market_mechanics_risk_watch",
    "market_mechanics_risk_blocking",
    "composite_settlement_cost_uncertainty_watch",
    "composite_settlement_cost_uncertainty_blocking",
)
REPORT_REASON_CODES = (
    NO_CANDIDATES_REASON,
    "settlement_cost_uncertainty_report_clear",
    "resolution_timing_uncertainty_detected",
    "settlement_lag_detected",
    "fee_spread_haircut_detected",
    "market_mechanics_risk_detected",
    "composite_settlement_cost_uncertainty_detected",
)
REASON_CODES = tuple(sorted(ROW_REASON_CODES + REPORT_REASON_CODES))
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
TOP_LEVEL_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "candidate_count",
    "pass_count",
    "watch_count",
    "block_count",
    "resolution_timing_uncertainty_count",
    "settlement_lag_count",
    "fee_spread_haircut_count",
    "market_mechanics_risk_count",
    "mean_uncertainty_cost_score",
    "mean_cost_drag_score",
    "max_settlement_lag_hours",
    "max_fee_spread_haircut_ratio",
    "status",
    "reason_code_counts",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
TOP_LEVEL_PAYLOAD_FIELDS = TOP_LEVEL_PAYLOAD_FIELDS_WITHOUT_DIGEST + (
    "public_report_digest",
)
TOP_LEVEL_DECIMAL_PAYLOAD_FIELDS = (
    "candidate_count",
    "pass_count",
    "watch_count",
    "block_count",
    "resolution_timing_uncertainty_count",
    "settlement_lag_count",
    "fee_spread_haircut_count",
    "market_mechanics_risk_count",
    "mean_uncertainty_cost_score",
    "mean_cost_drag_score",
    "max_settlement_lag_hours",
    "max_fee_spread_haircut_ratio",
)
REASON_CODE_COUNT_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_FIELDS = (
    "row_number",
    "observed_at",
    "resolution_timing_uncertainty_score",
    "settlement_lag_hours",
    "settlement_lag_score",
    "fee_spread_haircut_ratio",
    "fee_spread_haircut_score",
    "market_mechanics_risk_score",
    "cost_drag_score",
    "uncertainty_cost_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_DECIMAL_PAYLOAD_FIELDS = (
    "row_number",
    "resolution_timing_uncertainty_score",
    "settlement_lag_hours",
    "settlement_lag_score",
    "fee_spread_haircut_ratio",
    "fee_spread_haircut_score",
    "market_mechanics_risk_score",
    "cost_drag_score",
    "uncertainty_cost_score",
)
UNSAFE_PUBLIC_KEY_NAMES = (
    "raw_candidate_id",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "source_id",
    "source_url",
    "source_text",
    "dsn",
    "table_name",
    "token",
    "wallet",
    "order",
    "trade",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "://",
    "raw-candidate",
    "candidate-id",
    "candidate_id",
    "market-id",
    "market_slug",
    "market-slug",
    "market_question",
    "source-id",
    "source_url",
    "source text",
    "source_text",
    "dsn",
    "table_name",
    "fills_table",
    "token",
    "wallet",
    "order",
    "trade",
    "buy sell",
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
class ResearchMarketSettlementCostUncertaintyConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_UNCERTAINTY_CONFIG_VERSION
    pass_max_uncertainty_cost_score: Decimal = Decimal("0.300000")
    watch_max_uncertainty_cost_score: Decimal = Decimal("0.650000")
    settlement_lag_watch_hours: Decimal = Decimal("24.000000")
    settlement_lag_block_hours: Decimal = Decimal("72.000000")
    fee_spread_haircut_watch_ratio: Decimal = Decimal("0.020000")
    fee_spread_haircut_block_ratio: Decimal = Decimal("0.060000")
    resolution_timing_watch_score: Decimal = Decimal("0.350000")
    resolution_timing_block_score: Decimal = Decimal("0.800000")
    market_mechanics_watch_score: Decimal = Decimal("0.300000")
    market_mechanics_block_score: Decimal = Decimal("0.750000")
    resolution_timing_weight: Decimal = Decimal("0.250000")
    settlement_lag_weight: Decimal = Decimal("0.250000")
    fee_spread_haircut_weight: Decimal = Decimal("0.250000")
    market_mechanics_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementCostUncertaintyConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_max_uncertainty_cost_score",
            "watch_max_uncertainty_cost_score",
            "fee_spread_haircut_watch_ratio",
            "fee_spread_haircut_block_ratio",
            "resolution_timing_watch_score",
            "resolution_timing_block_score",
            "market_mechanics_watch_score",
            "market_mechanics_block_score",
            "resolution_timing_weight",
            "settlement_lag_weight",
            "fee_spread_haircut_weight",
            "market_mechanics_weight",
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
            "pass_max_uncertainty_cost_score",
            self.pass_max_uncertainty_cost_score,
            "watch_max_uncertainty_cost_score",
            self.watch_max_uncertainty_cost_score,
        )
        _require_threshold_pair(
            "settlement_lag_watch_hours",
            self.settlement_lag_watch_hours,
            "settlement_lag_block_hours",
            self.settlement_lag_block_hours,
        )
        _require_threshold_pair(
            "fee_spread_haircut_watch_ratio",
            self.fee_spread_haircut_watch_ratio,
            "fee_spread_haircut_block_ratio",
            self.fee_spread_haircut_block_ratio,
        )
        _require_threshold_pair(
            "resolution_timing_watch_score",
            self.resolution_timing_watch_score,
            "resolution_timing_block_score",
            self.resolution_timing_block_score,
        )
        _require_threshold_pair(
            "market_mechanics_watch_score",
            self.market_mechanics_watch_score,
            "market_mechanics_block_score",
            self.market_mechanics_block_score,
        )
        _require_weights_total_one(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketSettlementCostUncertaintyCandidate(_FinalPublicDataclass):
    raw_candidate_id: str
    observed_at: datetime
    resolution_timing_uncertainty: Decimal
    settlement_lag_hours: Decimal
    fee_spread_haircut_ratio: Decimal
    market_mechanics_risk: Decimal
    sensitive_context: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementCostUncertaintyCandidate,
            "candidate",
        )
        _require_nonblank_string("raw_candidate_id", self.raw_candidate_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "resolution_timing_uncertainty",
            "fee_spread_haircut_ratio",
            "market_mechanics_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_lag_hours",
            _normalize_nonnegative_decimal("settlement_lag_hours", self.settlement_lag_hours),
        )
        object.__setattr__(
            self,
            "sensitive_context",
            _normalize_optional_string("sensitive_context", self.sensitive_context),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchMarketSettlementCostUncertaintyRow(_FinalPublicDataclass):
    row_number: Decimal
    observed_at: datetime
    resolution_timing_uncertainty_score: Decimal
    settlement_lag_hours: Decimal
    settlement_lag_score: Decimal
    fee_spread_haircut_ratio: Decimal
    fee_spread_haircut_score: Decimal
    market_mechanics_risk_score: Decimal
    cost_drag_score: Decimal
    uncertainty_cost_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementCostUncertaintyRow, "row")
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
            "resolution_timing_uncertainty_score",
            "settlement_lag_score",
            "fee_spread_haircut_ratio",
            "fee_spread_haircut_score",
            "market_mechanics_risk_score",
            "cost_drag_score",
            "uncertainty_cost_score",
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
class ResearchMarketSettlementCostUncertaintyReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementCostUncertaintyReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketSettlementCostUncertaintyReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    resolution_timing_uncertainty_count: Decimal
    settlement_lag_count: Decimal
    fee_spread_haircut_count: Decimal
    market_mechanics_risk_count: Decimal
    mean_uncertainty_cost_score: Decimal
    mean_cost_drag_score: Decimal
    max_settlement_lag_hours: Decimal
    max_fee_spread_haircut_ratio: Decimal
    status: str
    reason_code_counts: tuple[ResearchMarketSettlementCostUncertaintyReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketSettlementCostUncertaintyRow, ...]
    public_report_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementCostUncertaintyReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "resolution_timing_uncertainty_count",
            "settlement_lag_count",
            "fee_spread_haircut_count",
            "market_mechanics_risk_count",
            "mean_uncertainty_cost_score",
            "mean_cost_drag_score",
            "max_settlement_lag_hours",
            "max_fee_spread_haircut_ratio",
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
    resolution_timing_uncertainty_score: Decimal
    settlement_lag_hours: Decimal
    settlement_lag_score: Decimal
    fee_spread_haircut_ratio: Decimal
    fee_spread_haircut_score: Decimal
    market_mechanics_risk_score: Decimal
    cost_drag_score: Decimal
    uncertainty_cost_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def build_research_market_settlement_cost_uncertainty_report(
    candidates: Iterable[ResearchMarketSettlementCostUncertaintyCandidate],
    *,
    config: ResearchMarketSettlementCostUncertaintyConfig,
    generated_at: datetime,
) -> ResearchMarketSettlementCostUncertaintyReport:
    if type(config) is not ResearchMarketSettlementCostUncertaintyConfig:
        raise ValueError(
            "config must be a ResearchMarketSettlementCostUncertaintyConfig",
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
        "resolution_timing_uncertainty_count": _reason_count(
            rows,
            (
                "resolution_timing_uncertainty_watch",
                "resolution_timing_uncertainty_blocking",
            ),
        ),
        "settlement_lag_count": _reason_count(
            rows,
            ("settlement_lag_watch", "settlement_lag_blocking"),
        ),
        "fee_spread_haircut_count": _reason_count(
            rows,
            ("fee_spread_haircut_watch", "fee_spread_haircut_blocking"),
        ),
        "market_mechanics_risk_count": _reason_count(
            rows,
            ("market_mechanics_risk_watch", "market_mechanics_risk_blocking"),
        ),
        "mean_uncertainty_cost_score": _mean(
            tuple(row.uncertainty_cost_score for row in rows),
        ),
        "mean_cost_drag_score": _mean(tuple(row.cost_drag_score for row in rows)),
        "max_settlement_lag_hours": _max_decimal(
            tuple(row.settlement_lag_hours for row in rows),
        ),
        "max_fee_spread_haircut_ratio": _max_decimal(
            tuple(row.fee_spread_haircut_ratio for row in rows),
        ),
        "status": _report_status(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
    }
    return ResearchMarketSettlementCostUncertaintyReport(
        **report_values,
        public_report_digest=_public_digest(_report_payload_without_digest(**report_values)),
    )


def research_market_settlement_cost_uncertainty_report_payload(
    report: ResearchMarketSettlementCostUncertaintyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketSettlementCostUncertaintyReport:
        raise ValueError(
            "report must be a ResearchMarketSettlementCostUncertaintyReport",
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
    _validate_public_payload_schema(ready, include_digest=True)
    return ready


def research_market_settlement_cost_uncertainty_digest(
    report: ResearchMarketSettlementCostUncertaintyReport,
) -> str:
    payload = research_market_settlement_cost_uncertainty_report_payload(report)
    digest = payload.get("public_report_digest")
    if type(digest) is not str:
        raise ValueError("public_report_digest must be a string")
    return digest


def _row_draft(
    candidate: ResearchMarketSettlementCostUncertaintyCandidate,
    *,
    config: ResearchMarketSettlementCostUncertaintyConfig,
) -> _RowDraft:
    settlement_lag_score = _ratio_score(
        candidate.settlement_lag_hours,
        config.settlement_lag_block_hours,
    )
    fee_spread_haircut_score = _ratio_score(
        candidate.fee_spread_haircut_ratio,
        config.fee_spread_haircut_block_ratio,
    )
    cost_drag_score = _mean((settlement_lag_score, fee_spread_haircut_score))
    uncertainty_cost_score = _weighted_score(
        resolution_timing_uncertainty_score=candidate.resolution_timing_uncertainty,
        settlement_lag_score=settlement_lag_score,
        fee_spread_haircut_score=fee_spread_haircut_score,
        market_mechanics_risk_score=candidate.market_mechanics_risk,
        config=config,
    )
    status = _row_status(
        candidate=candidate,
        uncertainty_cost_score=uncertainty_cost_score,
        config=config,
    )
    return _RowDraft(
        observed_at=candidate.observed_at,
        resolution_timing_uncertainty_score=candidate.resolution_timing_uncertainty,
        settlement_lag_hours=candidate.settlement_lag_hours,
        settlement_lag_score=settlement_lag_score,
        fee_spread_haircut_ratio=candidate.fee_spread_haircut_ratio,
        fee_spread_haircut_score=fee_spread_haircut_score,
        market_mechanics_risk_score=candidate.market_mechanics_risk,
        cost_drag_score=cost_drag_score,
        uncertainty_cost_score=uncertainty_cost_score,
        status=status,
        reason_codes=_row_reason_codes(
            candidate=candidate,
            uncertainty_cost_score=uncertainty_cost_score,
            config=config,
        ),
    )


def _row_from_draft(
    *,
    row_number: Decimal,
    draft: _RowDraft,
) -> ResearchMarketSettlementCostUncertaintyRow:
    return ResearchMarketSettlementCostUncertaintyRow(
        row_number=row_number,
        observed_at=draft.observed_at,
        resolution_timing_uncertainty_score=draft.resolution_timing_uncertainty_score,
        settlement_lag_hours=draft.settlement_lag_hours,
        settlement_lag_score=draft.settlement_lag_score,
        fee_spread_haircut_ratio=draft.fee_spread_haircut_ratio,
        fee_spread_haircut_score=draft.fee_spread_haircut_score,
        market_mechanics_risk_score=draft.market_mechanics_risk_score,
        cost_drag_score=draft.cost_drag_score,
        uncertainty_cost_score=draft.uncertainty_cost_score,
        status=draft.status,
        reason_codes=draft.reason_codes,
    )


def _weighted_score(
    *,
    resolution_timing_uncertainty_score: Decimal,
    settlement_lag_score: Decimal,
    fee_spread_haircut_score: Decimal,
    market_mechanics_risk_score: Decimal,
    config: ResearchMarketSettlementCostUncertaintyConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            resolution_timing_uncertainty_score * config.resolution_timing_weight
            + settlement_lag_score * config.settlement_lag_weight
            + fee_spread_haircut_score * config.fee_spread_haircut_weight
            + market_mechanics_risk_score * config.market_mechanics_weight
        )
    return _normalize_probability("uncertainty_cost_score", score)


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
    candidate: ResearchMarketSettlementCostUncertaintyCandidate,
    uncertainty_cost_score: Decimal,
    config: ResearchMarketSettlementCostUncertaintyConfig,
) -> str:
    if (
        candidate.resolution_timing_uncertainty >= config.resolution_timing_block_score
        or candidate.settlement_lag_hours >= config.settlement_lag_block_hours
        or candidate.fee_spread_haircut_ratio >= config.fee_spread_haircut_block_ratio
        or candidate.market_mechanics_risk >= config.market_mechanics_block_score
        or uncertainty_cost_score > config.watch_max_uncertainty_cost_score
    ):
        return "block"
    if (
        candidate.resolution_timing_uncertainty >= config.resolution_timing_watch_score
        or candidate.settlement_lag_hours >= config.settlement_lag_watch_hours
        or candidate.fee_spread_haircut_ratio >= config.fee_spread_haircut_watch_ratio
        or candidate.market_mechanics_risk >= config.market_mechanics_watch_score
        or uncertainty_cost_score > config.pass_max_uncertainty_cost_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    candidate: ResearchMarketSettlementCostUncertaintyCandidate,
    uncertainty_cost_score: Decimal,
    config: ResearchMarketSettlementCostUncertaintyConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_threshold_code(
        codes,
        candidate.resolution_timing_uncertainty,
        config.resolution_timing_watch_score,
        config.resolution_timing_block_score,
        "resolution_timing_uncertainty_watch",
        "resolution_timing_uncertainty_blocking",
    )
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
        candidate.fee_spread_haircut_ratio,
        config.fee_spread_haircut_watch_ratio,
        config.fee_spread_haircut_block_ratio,
        "fee_spread_haircut_watch",
        "fee_spread_haircut_blocking",
    )
    _append_threshold_code(
        codes,
        candidate.market_mechanics_risk,
        config.market_mechanics_watch_score,
        config.market_mechanics_block_score,
        "market_mechanics_risk_watch",
        "market_mechanics_risk_blocking",
    )
    _append_max_threshold_code(
        codes,
        uncertainty_cost_score,
        config.pass_max_uncertainty_cost_score,
        config.watch_max_uncertainty_cost_score,
        "composite_settlement_cost_uncertainty_watch",
        "composite_settlement_cost_uncertainty_blocking",
    )
    if not codes:
        return ("settlement_cost_uncertainty_clear",)
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


def _append_max_threshold_code(
    codes: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if value > block_threshold:
        codes.append(block_code)
    elif value > watch_threshold:
        codes.append(watch_code)


def _report_status(rows: tuple[ResearchMarketSettlementCostUncertaintyRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketSettlementCostUncertaintyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    if all(row.status == "pass" for row in rows):
        return ("settlement_cost_uncertainty_report_clear",)
    codes: list[str] = []
    if _has_any_row_reason(
        rows,
        (
            "resolution_timing_uncertainty_watch",
            "resolution_timing_uncertainty_blocking",
        ),
    ):
        codes.append("resolution_timing_uncertainty_detected")
    if _has_any_row_reason(rows, ("settlement_lag_watch", "settlement_lag_blocking")):
        codes.append("settlement_lag_detected")
    if _has_any_row_reason(
        rows,
        ("fee_spread_haircut_watch", "fee_spread_haircut_blocking"),
    ):
        codes.append("fee_spread_haircut_detected")
    if _has_any_row_reason(
        rows,
        ("market_mechanics_risk_watch", "market_mechanics_risk_blocking"),
    ):
        codes.append("market_mechanics_risk_detected")
    if _has_any_row_reason(
        rows,
        (
            "composite_settlement_cost_uncertainty_watch",
            "composite_settlement_cost_uncertainty_blocking",
        ),
    ):
        codes.append("composite_settlement_cost_uncertainty_detected")
    return tuple(codes)


def _reason_code_counts(
    rows: tuple[ResearchMarketSettlementCostUncertaintyRow, ...],
) -> tuple[ResearchMarketSettlementCostUncertaintyReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketSettlementCostUncertaintyReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ONE,
            ),
        )
    counts = Counter(code for row in rows for code in row.reason_codes)
    return tuple(
        ResearchMarketSettlementCostUncertaintyReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_candidates(
    candidates: Iterable[ResearchMarketSettlementCostUncertaintyCandidate],
) -> tuple[ResearchMarketSettlementCostUncertaintyCandidate, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Iterable):
        raise ValueError("candidates must be an iterable")
    normalized = tuple(candidates)
    for row in normalized:
        if type(row) is not ResearchMarketSettlementCostUncertaintyCandidate:
            raise ValueError(
                "candidates must contain ResearchMarketSettlementCostUncertaintyCandidate",
            )
        _require_hard_flags("candidate", row)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketSettlementCostUncertaintyRow],
) -> tuple[ResearchMarketSettlementCostUncertaintyRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketSettlementCostUncertaintyRow:
            raise ValueError("rows must contain ResearchMarketSettlementCostUncertaintyRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketSettlementCostUncertaintyReasonCodeCount],
) -> tuple[ResearchMarketSettlementCostUncertaintyReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketSettlementCostUncertaintyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketSettlementCostUncertaintyReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row(row: ResearchMarketSettlementCostUncertaintyRow) -> None:
    if row.status == "block" and not any(code.endswith("_blocking") for code in row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != ("settlement_cost_uncertainty_clear",):
        raise ValueError("status must match reason_codes")
    if row.cost_drag_score != _mean((row.settlement_lag_score, row.fee_spread_haircut_score)):
        raise ValueError("cost_drag_score must match settlement lag and haircut scores")


def _validate_report(report: ResearchMarketSettlementCostUncertaintyReport) -> None:
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
    if report.resolution_timing_uncertainty_count != _reason_count(
        report.rows,
        (
            "resolution_timing_uncertainty_watch",
            "resolution_timing_uncertainty_blocking",
        ),
    ):
        raise ValueError("resolution_timing_uncertainty_count must match rows")
    if report.settlement_lag_count != _reason_count(
        report.rows,
        ("settlement_lag_watch", "settlement_lag_blocking"),
    ):
        raise ValueError("settlement_lag_count must match rows")
    if report.fee_spread_haircut_count != _reason_count(
        report.rows,
        ("fee_spread_haircut_watch", "fee_spread_haircut_blocking"),
    ):
        raise ValueError("fee_spread_haircut_count must match rows")
    if report.market_mechanics_risk_count != _reason_count(
        report.rows,
        ("market_mechanics_risk_watch", "market_mechanics_risk_blocking"),
    ):
        raise ValueError("market_mechanics_risk_count must match rows")
    if report.mean_uncertainty_cost_score != _mean(
        tuple(row.uncertainty_cost_score for row in report.rows),
    ):
        raise ValueError("mean_uncertainty_cost_score must match rows")
    if report.mean_cost_drag_score != _mean(tuple(row.cost_drag_score for row in report.rows)):
        raise ValueError("mean_cost_drag_score must match rows")
    if report.max_settlement_lag_hours != _max_decimal(
        tuple(row.settlement_lag_hours for row in report.rows),
    ):
        raise ValueError("max_settlement_lag_hours must match rows")
    if report.max_fee_spread_haircut_ratio != _max_decimal(
        tuple(row.fee_spread_haircut_ratio for row in report.rows),
    ):
        raise ValueError("max_fee_spread_haircut_ratio must match rows")


def _report_payload_without_digest_from_report(
    report: ResearchMarketSettlementCostUncertaintyReport,
) -> dict[str, Any]:
    return _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        resolution_timing_uncertainty_count=report.resolution_timing_uncertainty_count,
        settlement_lag_count=report.settlement_lag_count,
        fee_spread_haircut_count=report.fee_spread_haircut_count,
        market_mechanics_risk_count=report.market_mechanics_risk_count,
        mean_uncertainty_cost_score=report.mean_uncertainty_cost_score,
        mean_cost_drag_score=report.mean_cost_drag_score,
        max_settlement_lag_hours=report.max_settlement_lag_hours,
        max_fee_spread_haircut_ratio=report.max_fee_spread_haircut_ratio,
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
        "resolution_timing_uncertainty_count": values[
            "resolution_timing_uncertainty_count"
        ],
        "settlement_lag_count": values["settlement_lag_count"],
        "fee_spread_haircut_count": values["fee_spread_haircut_count"],
        "market_mechanics_risk_count": values["market_mechanics_risk_count"],
        "mean_uncertainty_cost_score": values["mean_uncertainty_cost_score"],
        "mean_cost_drag_score": values["mean_cost_drag_score"],
        "max_settlement_lag_hours": values["max_settlement_lag_hours"],
        "max_fee_spread_haircut_ratio": values["max_fee_spread_haircut_ratio"],
        "status": values["status"],
        "reason_code_counts": values["reason_code_counts"],
        "reason_codes": values["reason_codes"],
        "rows": values["rows"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _expected_public_report_digest(
    report: ResearchMarketSettlementCostUncertaintyReport,
) -> str:
    return _public_digest(_report_payload_without_digest_from_report(report))


def _public_digest(payload: dict[str, Any]) -> str:
    ready = _json_ready(payload)
    _validate_public_payload_schema(ready, include_digest=False)
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
    if type(value) is ResearchMarketSettlementCostUncertaintyReasonCodeCount:
        return {
            "reason_code": value.reason_code,
            "count": _json_ready(value.count),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
    if type(value) is ResearchMarketSettlementCostUncertaintyRow:
        return {
            "row_number": _json_ready(value.row_number),
            "observed_at": _json_ready(value.observed_at),
            "resolution_timing_uncertainty_score": _json_ready(
                value.resolution_timing_uncertainty_score,
            ),
            "settlement_lag_hours": _json_ready(value.settlement_lag_hours),
            "settlement_lag_score": _json_ready(value.settlement_lag_score),
            "fee_spread_haircut_ratio": _json_ready(value.fee_spread_haircut_ratio),
            "fee_spread_haircut_score": _json_ready(value.fee_spread_haircut_score),
            "market_mechanics_risk_score": _json_ready(value.market_mechanics_risk_score),
            "cost_drag_score": _json_ready(value.cost_drag_score),
            "uncertainty_cost_score": _json_ready(value.uncertainty_cost_score),
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


def _validate_public_payload_schema(
    payload: dict[str, Any],
    *,
    include_digest: bool,
) -> None:
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    expected_fields = (
        TOP_LEVEL_PAYLOAD_FIELDS if include_digest else TOP_LEVEL_PAYLOAD_FIELDS_WITHOUT_DIGEST
    )
    _require_payload_keys("report payload", payload, expected_fields)
    _reject_unsafe_public_payload("report payload", payload)
    _require_payload_datetime_string("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    for field_name in TOP_LEVEL_DECIMAL_PAYLOAD_FIELDS:
        _require_payload_decimal_string(field_name, payload[field_name])
    _require_member("status", payload["status"], STATUSES)
    _require_payload_reason_code_counts(payload["reason_code_counts"])
    _require_payload_reason_codes("reason_codes", payload["reason_codes"], REPORT_REASON_CODES)
    _require_payload_rows(payload["rows"])
    if include_digest:
        _require_digest("public_report_digest", payload["public_report_digest"])
    _require_payload_flags("report payload", payload)


def _require_payload_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    if not value:
        raise ValueError("reason_code_counts must not be empty")
    for item in value:
        if type(item) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        _require_payload_keys(
            "reason_code_count",
            item,
            REASON_CODE_COUNT_PAYLOAD_FIELDS,
        )
        _reject_unsafe_public_payload("reason_code_count", item)
        _require_member("reason_code", item["reason_code"], REASON_CODES)
        _require_payload_decimal_string("count", item["count"])
        _require_payload_flags("reason_code_count", item)


def _require_payload_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    for item in value:
        if type(item) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_payload_keys("row", item, ROW_PAYLOAD_FIELDS)
        _reject_unsafe_public_payload("row", item)
        _require_payload_datetime_string("observed_at", item["observed_at"])
        for field_name in ROW_DECIMAL_PAYLOAD_FIELDS:
            _require_payload_decimal_string(field_name, item[field_name])
        _require_member("status", item["status"], STATUSES)
        _require_payload_reason_codes("reason_codes", item["reason_codes"], ROW_REASON_CODES)
        _require_payload_flags("row", item)


def _require_payload_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for item in value:
        _require_member(field_name, item, allowed)


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_fields: tuple[str, ...],
) -> None:
    actual_fields = set(payload)
    expected_field_set = set(expected_fields)
    if actual_fields - expected_field_set:
        raise ValueError(f"{label} contains unexpected public field")
    if expected_field_set - actual_fields:
        raise ValueError(f"{label} is missing a public field")


def _require_payload_datetime_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a UTC datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"{field_name} must be a UTC datetime string")


def _require_payload_decimal_string(field_name: str, value: object) -> None:
    if type(value) is not str or not _is_payload_decimal_string(value):
        raise ValueError(f"{field_name} must use Decimal-derived string values")


def _is_payload_decimal_string(value: str) -> bool:
    integer_part, separator, fractional_part = value.partition(".")
    return (
        separator == "."
        and integer_part.isdigit()
        and len(fractional_part) == 6
        and fractional_part.isdigit()
    )


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_key(key):
                raise ValueError("public payload has unsafe field")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        if value.strip() != value or _has_unsafe_public_value(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_key(value: str) -> bool:
    lowered = value.lower()
    return lowered in UNSAFE_PUBLIC_KEY_NAMES


def _has_unsafe_public_value(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS)


def _status_count(
    rows: tuple[ResearchMarketSettlementCostUncertaintyRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchMarketSettlementCostUncertaintyRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)))


def _has_any_row_reason(
    rows: tuple[ResearchMarketSettlementCostUncertaintyRow, ...],
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


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for value in normalized:
        _require_member(field_name, value, allowed)
    return tuple(dict.fromkeys(normalized))


def _normalize_optional_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_nonblank_string(field_name, value)
    return value


def _require_nonblank_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_nonblank_string(field_name, value)
    if not all(ch.islower() or ch.isdigit() or ch in "-_" for ch in value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or not all(ch in "0123456789abcdef" for ch in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_weights_total_one(
    config: ResearchMarketSettlementCostUncertaintyConfig,
) -> None:
    total = _quantize_decimal(
        config.resolution_timing_weight
        + config.settlement_lag_weight
        + config.fee_spread_haircut_weight
        + config.market_mechanics_weight,
    )
    if total != ONE:
        raise ValueError("component weights must sum to one")


def _require_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_name} must exceed {watch_name}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _draft_sort_key(row: _RowDraft) -> tuple[int, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.uncertainty_cost_score,
        -row.cost_drag_score,
        row.observed_at.isoformat(),
    )


def _row_sort_key(
    row: ResearchMarketSettlementCostUncertaintyRow,
) -> tuple[int, Decimal, Decimal, Decimal]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.uncertainty_cost_score,
        -row.cost_drag_score,
        row.row_number,
    )
