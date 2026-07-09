"""Pure public settlement liquidity cost buffer report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_SETTLEMENT_LIQUIDITY_COST_BUFFER_CONFIG_VERSION",
    "ResearchMarketSettlementLiquidityCostBufferCandidate",
    "ResearchMarketSettlementLiquidityCostBufferConfig",
    "ResearchMarketSettlementLiquidityCostBufferReasonCodeCount",
    "ResearchMarketSettlementLiquidityCostBufferReport",
    "ResearchMarketSettlementLiquidityCostBufferRow",
    "build_research_market_settlement_liquidity_cost_buffer_report",
    "research_market_settlement_liquidity_cost_buffer_digest",
    "research_market_settlement_liquidity_cost_buffer_report_payload",
    "validate_research_market_settlement_liquidity_cost_buffer_report_payload",
)


DEFAULT_RESEARCH_MARKET_SETTLEMENT_LIQUIDITY_COST_BUFFER_CONFIG_VERSION = (
    "research-market-settlement-liquidity-cost-buffer-report-v0"
)
STATUSES = ("pass", "watch", "block")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {"block": 2, "watch": 1, "pass": 0}
NO_CANDIDATES_REASON = "no_settlement_liquidity_cost_buffer_candidates"

ROW_REASON_CODES = (
    "settlement_liquidity_cost_buffer_clear",
    "settlement_cost_load_watch",
    "settlement_cost_load_blocking",
    "liquidity_buffer_gap_watch",
    "liquidity_buffer_gap_blocking",
    "exit_cost_buffer_watch",
    "exit_cost_buffer_blocking",
    "settlement_delay_pressure_watch",
    "settlement_delay_pressure_blocking",
    "composite_liquidity_cost_buffer_watch",
    "composite_liquidity_cost_buffer_blocking",
)
REPORT_REASON_CODES = (
    NO_CANDIDATES_REASON,
    "settlement_liquidity_cost_buffer_report_clear",
    "settlement_cost_load_detected",
    "liquidity_buffer_gap_detected",
    "exit_cost_buffer_detected",
    "settlement_delay_pressure_detected",
    "composite_liquidity_cost_buffer_detected",
)
REASON_CODES = tuple(sorted(ROW_REASON_CODES + REPORT_REASON_CODES))
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "settlement_cost_load_count",
        "liquidity_buffer_gap_count",
        "exit_cost_buffer_count",
        "settlement_delay_pressure_count",
        "mean_liquidity_cost_buffer_score",
        "max_settlement_cost_ratio",
        "min_liquidity_buffer_ratio",
        "max_projected_exit_cost_ratio",
        "max_settlement_delay_hours",
        "status",
        "reason_code_counts",
        "reason_codes",
        "rows",
        "public_report_digest",
        *HARD_FLAG_FIELDS,
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "row_number",
        "observed_at",
        "settlement_cost_ratio",
        "settlement_cost_load_score",
        "liquidity_buffer_ratio",
        "liquidity_buffer_gap_ratio",
        "liquidity_buffer_gap_score",
        "projected_exit_cost_ratio",
        "exit_cost_buffer_score",
        "settlement_delay_hours",
        "settlement_delay_score",
        "liquidity_cost_buffer_score",
        "status",
        "reason_codes",
        *HARD_FLAG_FIELDS,
    ),
)
REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        *HARD_FLAG_FIELDS,
    ),
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
class ResearchMarketSettlementLiquidityCostBufferConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_SETTLEMENT_LIQUIDITY_COST_BUFFER_CONFIG_VERSION
    )
    pass_max_liquidity_cost_buffer_score: Decimal = Decimal("0.300000")
    watch_max_liquidity_cost_buffer_score: Decimal = Decimal("0.650000")
    settlement_cost_load_watch_ratio: Decimal = Decimal("0.200000")
    settlement_cost_load_block_ratio: Decimal = Decimal("0.500000")
    liquidity_buffer_gap_watch_ratio: Decimal = Decimal("0.150000")
    liquidity_buffer_gap_block_ratio: Decimal = Decimal("0.400000")
    exit_cost_buffer_watch_ratio: Decimal = Decimal("0.250000")
    exit_cost_buffer_block_ratio: Decimal = Decimal("0.600000")
    settlement_delay_watch_hours: Decimal = Decimal("24.000000")
    settlement_delay_block_hours: Decimal = Decimal("72.000000")
    settlement_cost_load_weight: Decimal = Decimal("0.300000")
    liquidity_buffer_gap_weight: Decimal = Decimal("0.300000")
    exit_cost_buffer_weight: Decimal = Decimal("0.250000")
    settlement_delay_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementLiquidityCostBufferConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_max_liquidity_cost_buffer_score",
            "watch_max_liquidity_cost_buffer_score",
            "settlement_cost_load_watch_ratio",
            "settlement_cost_load_block_ratio",
            "liquidity_buffer_gap_watch_ratio",
            "liquidity_buffer_gap_block_ratio",
            "exit_cost_buffer_watch_ratio",
            "exit_cost_buffer_block_ratio",
            "settlement_cost_load_weight",
            "liquidity_buffer_gap_weight",
            "exit_cost_buffer_weight",
            "settlement_delay_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("settlement_delay_watch_hours", "settlement_delay_block_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "pass_max_liquidity_cost_buffer_score",
            self.pass_max_liquidity_cost_buffer_score,
            "watch_max_liquidity_cost_buffer_score",
            self.watch_max_liquidity_cost_buffer_score,
        )
        _require_threshold_pair(
            "settlement_cost_load_watch_ratio",
            self.settlement_cost_load_watch_ratio,
            "settlement_cost_load_block_ratio",
            self.settlement_cost_load_block_ratio,
        )
        _require_threshold_pair(
            "liquidity_buffer_gap_watch_ratio",
            self.liquidity_buffer_gap_watch_ratio,
            "liquidity_buffer_gap_block_ratio",
            self.liquidity_buffer_gap_block_ratio,
        )
        _require_threshold_pair(
            "exit_cost_buffer_watch_ratio",
            self.exit_cost_buffer_watch_ratio,
            "exit_cost_buffer_block_ratio",
            self.exit_cost_buffer_block_ratio,
        )
        _require_threshold_pair(
            "settlement_delay_watch_hours",
            self.settlement_delay_watch_hours,
            "settlement_delay_block_hours",
            self.settlement_delay_block_hours,
        )
        _require_weights_total_one(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketSettlementLiquidityCostBufferCandidate(_FinalPublicDataclass):
    raw_candidate_id: str
    observed_at: datetime
    settlement_cost_ratio: Decimal
    liquidity_buffer_ratio: Decimal
    projected_exit_cost_ratio: Decimal
    settlement_delay_hours: Decimal
    sensitive_context: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementLiquidityCostBufferCandidate,
            "candidate",
        )
        _require_nonblank_string("raw_candidate_id", self.raw_candidate_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "settlement_cost_ratio",
            "liquidity_buffer_ratio",
            "projected_exit_cost_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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
            "sensitive_context",
            _normalize_optional_string("sensitive_context", self.sensitive_context),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchMarketSettlementLiquidityCostBufferRow(_FinalPublicDataclass):
    row_number: Decimal
    observed_at: datetime
    settlement_cost_ratio: Decimal
    settlement_cost_load_score: Decimal
    liquidity_buffer_ratio: Decimal
    liquidity_buffer_gap_ratio: Decimal
    liquidity_buffer_gap_score: Decimal
    projected_exit_cost_ratio: Decimal
    exit_cost_buffer_score: Decimal
    settlement_delay_hours: Decimal
    settlement_delay_score: Decimal
    liquidity_cost_buffer_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementLiquidityCostBufferRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "settlement_delay_hours",
            _normalize_nonnegative_decimal(
                "settlement_delay_hours",
                self.settlement_delay_hours,
            ),
        )
        for field_name in (
            "settlement_cost_ratio",
            "settlement_cost_load_score",
            "liquidity_buffer_ratio",
            "liquidity_buffer_gap_ratio",
            "liquidity_buffer_gap_score",
            "projected_exit_cost_ratio",
            "exit_cost_buffer_score",
            "settlement_delay_score",
            "liquidity_cost_buffer_score",
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
class ResearchMarketSettlementLiquidityCostBufferReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementLiquidityCostBufferReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketSettlementLiquidityCostBufferReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    settlement_cost_load_count: Decimal
    liquidity_buffer_gap_count: Decimal
    exit_cost_buffer_count: Decimal
    settlement_delay_pressure_count: Decimal
    mean_liquidity_cost_buffer_score: Decimal
    max_settlement_cost_ratio: Decimal
    min_liquidity_buffer_ratio: Decimal
    max_projected_exit_cost_ratio: Decimal
    max_settlement_delay_hours: Decimal
    status: str
    reason_code_counts: tuple[
        ResearchMarketSettlementLiquidityCostBufferReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketSettlementLiquidityCostBufferRow, ...]
    public_report_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementLiquidityCostBufferReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "settlement_cost_load_count",
            "liquidity_buffer_gap_count",
            "exit_cost_buffer_count",
            "settlement_delay_pressure_count",
            "mean_liquidity_cost_buffer_score",
            "max_settlement_cost_ratio",
            "min_liquidity_buffer_ratio",
            "max_projected_exit_cost_ratio",
            "max_settlement_delay_hours",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
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
    settlement_cost_ratio: Decimal
    settlement_cost_load_score: Decimal
    liquidity_buffer_ratio: Decimal
    liquidity_buffer_gap_ratio: Decimal
    liquidity_buffer_gap_score: Decimal
    projected_exit_cost_ratio: Decimal
    exit_cost_buffer_score: Decimal
    settlement_delay_hours: Decimal
    settlement_delay_score: Decimal
    liquidity_cost_buffer_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def build_research_market_settlement_liquidity_cost_buffer_report(
    candidates: Iterable[ResearchMarketSettlementLiquidityCostBufferCandidate],
    *,
    config: ResearchMarketSettlementLiquidityCostBufferConfig,
    generated_at: datetime,
) -> ResearchMarketSettlementLiquidityCostBufferReport:
    if type(config) is not ResearchMarketSettlementLiquidityCostBufferConfig:
        raise ValueError(
            "config must be a ResearchMarketSettlementLiquidityCostBufferConfig",
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
        "settlement_cost_load_count": _reason_count(
            rows,
            ("settlement_cost_load_watch", "settlement_cost_load_blocking"),
        ),
        "liquidity_buffer_gap_count": _reason_count(
            rows,
            ("liquidity_buffer_gap_watch", "liquidity_buffer_gap_blocking"),
        ),
        "exit_cost_buffer_count": _reason_count(
            rows,
            ("exit_cost_buffer_watch", "exit_cost_buffer_blocking"),
        ),
        "settlement_delay_pressure_count": _reason_count(
            rows,
            ("settlement_delay_pressure_watch", "settlement_delay_pressure_blocking"),
        ),
        "mean_liquidity_cost_buffer_score": _mean(
            tuple(row.liquidity_cost_buffer_score for row in rows),
        ),
        "max_settlement_cost_ratio": _max_decimal(
            tuple(row.settlement_cost_ratio for row in rows),
        ),
        "min_liquidity_buffer_ratio": _min_decimal(
            tuple(row.liquidity_buffer_ratio for row in rows),
        ),
        "max_projected_exit_cost_ratio": _max_decimal(
            tuple(row.projected_exit_cost_ratio for row in rows),
        ),
        "max_settlement_delay_hours": _max_decimal(
            tuple(row.settlement_delay_hours for row in rows),
        ),
        "status": _report_status(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
    }
    return ResearchMarketSettlementLiquidityCostBufferReport(
        **report_values,
        public_report_digest=_public_digest(_report_payload_without_digest(**report_values)),
    )


def research_market_settlement_liquidity_cost_buffer_report_payload(
    report: ResearchMarketSettlementLiquidityCostBufferReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketSettlementLiquidityCostBufferReport:
        raise ValueError(
            "report must be a ResearchMarketSettlementLiquidityCostBufferReport",
        )
    _validate_report(report)
    if report.public_report_digest != _expected_public_report_digest(report):
        raise ValueError("public_report_digest must match public report payload")
    payload = _report_payload_without_digest_from_report(report)
    payload["public_report_digest"] = report.public_report_digest
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    return validate_research_market_settlement_liquidity_cost_buffer_report_payload(
        ready,
    )


def research_market_settlement_liquidity_cost_buffer_digest(
    report: ResearchMarketSettlementLiquidityCostBufferReport,
) -> str:
    payload = research_market_settlement_liquidity_cost_buffer_report_payload(report)
    digest = payload.get("public_report_digest")
    if type(digest) is not str:
        raise ValueError("public_report_digest must be a string")
    return digest


def validate_research_market_settlement_liquidity_cost_buffer_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_non_json_public_values("payload", payload)
    _reject_unsafe_public_payload(_canonical_public_payload_json(payload))
    _require_payload_hard_flags(payload)
    _require_exact_payload_keys("payload", payload, REPORT_PAYLOAD_KEYS)
    provided_digest = payload.get("public_report_digest")
    _require_digest("public_report_digest", provided_digest)
    unsigned = dict(payload)
    unsigned.pop("public_report_digest", None)
    if provided_digest != _public_digest(unsigned):
        raise ValueError("public_report_digest must match public report payload")

    normalized = ResearchMarketSettlementLiquidityCostBufferReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_public_string(
            "config_version",
            payload["config_version"],
        ),
        candidate_count=_payload_decimal("candidate_count", payload["candidate_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        settlement_cost_load_count=_payload_decimal(
            "settlement_cost_load_count",
            payload["settlement_cost_load_count"],
        ),
        liquidity_buffer_gap_count=_payload_decimal(
            "liquidity_buffer_gap_count",
            payload["liquidity_buffer_gap_count"],
        ),
        exit_cost_buffer_count=_payload_decimal(
            "exit_cost_buffer_count",
            payload["exit_cost_buffer_count"],
        ),
        settlement_delay_pressure_count=_payload_decimal(
            "settlement_delay_pressure_count",
            payload["settlement_delay_pressure_count"],
        ),
        mean_liquidity_cost_buffer_score=_payload_decimal(
            "mean_liquidity_cost_buffer_score",
            payload["mean_liquidity_cost_buffer_score"],
        ),
        max_settlement_cost_ratio=_payload_decimal(
            "max_settlement_cost_ratio",
            payload["max_settlement_cost_ratio"],
        ),
        min_liquidity_buffer_ratio=_payload_decimal(
            "min_liquidity_buffer_ratio",
            payload["min_liquidity_buffer_ratio"],
        ),
        max_projected_exit_cost_ratio=_payload_decimal(
            "max_projected_exit_cost_ratio",
            payload["max_projected_exit_cost_ratio"],
        ),
        max_settlement_delay_hours=_payload_decimal(
            "max_settlement_delay_hours",
            payload["max_settlement_delay_hours"],
        ),
        status=_payload_member("status", payload["status"], STATUSES),
        reason_code_counts=tuple(
            _payload_reason_code_count(f"reason_code_counts[{index}]", value)
            for index, value in enumerate(
                _payload_list("reason_code_counts", payload["reason_code_counts"]),
            )
        ),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_CODES,
        ),
        rows=tuple(
            _payload_row(f"rows[{index}]", value)
            for index, value in enumerate(_payload_list("rows", payload["rows"]))
        ),
        public_report_digest=provided_digest,
        paper_only=_payload_hard_flag("paper_only", payload["paper_only"]),
        report_only=_payload_hard_flag("report_only", payload["report_only"]),
        readonly=_payload_hard_flag("readonly", payload["readonly"]),
    )
    expected = _json_ready(_report_payload_without_digest_from_report(normalized))
    if type(expected) is not dict:
        raise ValueError("report payload must be a JSON object")
    expected["public_report_digest"] = normalized.public_report_digest
    if payload != expected:
        raise ValueError("payload must use canonical report payload schema")
    return payload


def _row_draft(
    candidate: ResearchMarketSettlementLiquidityCostBufferCandidate,
    *,
    config: ResearchMarketSettlementLiquidityCostBufferConfig,
) -> _RowDraft:
    liquidity_buffer_gap_ratio = _positive_gap(
        candidate.settlement_cost_ratio,
        candidate.liquidity_buffer_ratio,
    )
    settlement_cost_load_score = _ratio_score(
        candidate.settlement_cost_ratio,
        config.settlement_cost_load_block_ratio,
    )
    liquidity_buffer_gap_score = _ratio_score(
        liquidity_buffer_gap_ratio,
        config.liquidity_buffer_gap_block_ratio,
    )
    exit_cost_buffer_score = _ratio_score(
        candidate.projected_exit_cost_ratio,
        config.exit_cost_buffer_block_ratio,
    )
    settlement_delay_score = _ratio_score(
        candidate.settlement_delay_hours,
        config.settlement_delay_block_hours,
    )
    liquidity_cost_buffer_score = _weighted_score(
        settlement_cost_load_score=settlement_cost_load_score,
        liquidity_buffer_gap_score=liquidity_buffer_gap_score,
        exit_cost_buffer_score=exit_cost_buffer_score,
        settlement_delay_score=settlement_delay_score,
        config=config,
    )
    status = _row_status(
        candidate=candidate,
        liquidity_buffer_gap_ratio=liquidity_buffer_gap_ratio,
        liquidity_cost_buffer_score=liquidity_cost_buffer_score,
        config=config,
    )
    return _RowDraft(
        observed_at=candidate.observed_at,
        settlement_cost_ratio=candidate.settlement_cost_ratio,
        settlement_cost_load_score=settlement_cost_load_score,
        liquidity_buffer_ratio=candidate.liquidity_buffer_ratio,
        liquidity_buffer_gap_ratio=liquidity_buffer_gap_ratio,
        liquidity_buffer_gap_score=liquidity_buffer_gap_score,
        projected_exit_cost_ratio=candidate.projected_exit_cost_ratio,
        exit_cost_buffer_score=exit_cost_buffer_score,
        settlement_delay_hours=candidate.settlement_delay_hours,
        settlement_delay_score=settlement_delay_score,
        liquidity_cost_buffer_score=liquidity_cost_buffer_score,
        status=status,
        reason_codes=_row_reason_codes(
            candidate=candidate,
            liquidity_buffer_gap_ratio=liquidity_buffer_gap_ratio,
            liquidity_cost_buffer_score=liquidity_cost_buffer_score,
            config=config,
        ),
    )


def _row_from_draft(
    *,
    row_number: Decimal,
    draft: _RowDraft,
) -> ResearchMarketSettlementLiquidityCostBufferRow:
    return ResearchMarketSettlementLiquidityCostBufferRow(
        row_number=row_number,
        observed_at=draft.observed_at,
        settlement_cost_ratio=draft.settlement_cost_ratio,
        settlement_cost_load_score=draft.settlement_cost_load_score,
        liquidity_buffer_ratio=draft.liquidity_buffer_ratio,
        liquidity_buffer_gap_ratio=draft.liquidity_buffer_gap_ratio,
        liquidity_buffer_gap_score=draft.liquidity_buffer_gap_score,
        projected_exit_cost_ratio=draft.projected_exit_cost_ratio,
        exit_cost_buffer_score=draft.exit_cost_buffer_score,
        settlement_delay_hours=draft.settlement_delay_hours,
        settlement_delay_score=draft.settlement_delay_score,
        liquidity_cost_buffer_score=draft.liquidity_cost_buffer_score,
        status=draft.status,
        reason_codes=draft.reason_codes,
    )


def _weighted_score(
    *,
    settlement_cost_load_score: Decimal,
    liquidity_buffer_gap_score: Decimal,
    exit_cost_buffer_score: Decimal,
    settlement_delay_score: Decimal,
    config: ResearchMarketSettlementLiquidityCostBufferConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            settlement_cost_load_score * config.settlement_cost_load_weight
            + liquidity_buffer_gap_score * config.liquidity_buffer_gap_weight
            + exit_cost_buffer_score * config.exit_cost_buffer_weight
            + settlement_delay_score * config.settlement_delay_weight
        )
    return _normalize_probability("liquidity_cost_buffer_score", score)


def _positive_gap(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        gap = left - right
    if gap <= ZERO:
        return ZERO
    return _normalize_probability("liquidity_buffer_gap_ratio", gap)


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
    candidate: ResearchMarketSettlementLiquidityCostBufferCandidate,
    liquidity_buffer_gap_ratio: Decimal,
    liquidity_cost_buffer_score: Decimal,
    config: ResearchMarketSettlementLiquidityCostBufferConfig,
) -> str:
    if (
        candidate.settlement_cost_ratio >= config.settlement_cost_load_block_ratio
        or liquidity_buffer_gap_ratio >= config.liquidity_buffer_gap_block_ratio
        or candidate.projected_exit_cost_ratio >= config.exit_cost_buffer_block_ratio
        or candidate.settlement_delay_hours >= config.settlement_delay_block_hours
        or liquidity_cost_buffer_score > config.watch_max_liquidity_cost_buffer_score
    ):
        return "block"
    if (
        candidate.settlement_cost_ratio >= config.settlement_cost_load_watch_ratio
        or liquidity_buffer_gap_ratio >= config.liquidity_buffer_gap_watch_ratio
        or candidate.projected_exit_cost_ratio >= config.exit_cost_buffer_watch_ratio
        or candidate.settlement_delay_hours >= config.settlement_delay_watch_hours
        or liquidity_cost_buffer_score > config.pass_max_liquidity_cost_buffer_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    candidate: ResearchMarketSettlementLiquidityCostBufferCandidate,
    liquidity_buffer_gap_ratio: Decimal,
    liquidity_cost_buffer_score: Decimal,
    config: ResearchMarketSettlementLiquidityCostBufferConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_threshold_code(
        codes,
        candidate.settlement_cost_ratio,
        config.settlement_cost_load_watch_ratio,
        config.settlement_cost_load_block_ratio,
        "settlement_cost_load_watch",
        "settlement_cost_load_blocking",
    )
    _append_threshold_code(
        codes,
        liquidity_buffer_gap_ratio,
        config.liquidity_buffer_gap_watch_ratio,
        config.liquidity_buffer_gap_block_ratio,
        "liquidity_buffer_gap_watch",
        "liquidity_buffer_gap_blocking",
    )
    _append_threshold_code(
        codes,
        candidate.projected_exit_cost_ratio,
        config.exit_cost_buffer_watch_ratio,
        config.exit_cost_buffer_block_ratio,
        "exit_cost_buffer_watch",
        "exit_cost_buffer_blocking",
    )
    _append_threshold_code(
        codes,
        candidate.settlement_delay_hours,
        config.settlement_delay_watch_hours,
        config.settlement_delay_block_hours,
        "settlement_delay_pressure_watch",
        "settlement_delay_pressure_blocking",
    )
    if liquidity_cost_buffer_score > config.watch_max_liquidity_cost_buffer_score:
        codes.append("composite_liquidity_cost_buffer_blocking")
    elif liquidity_cost_buffer_score > config.pass_max_liquidity_cost_buffer_score:
        codes.append("composite_liquidity_cost_buffer_watch")
    if not codes:
        return ("settlement_liquidity_cost_buffer_clear",)
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


def _report_status(rows: tuple[ResearchMarketSettlementLiquidityCostBufferRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketSettlementLiquidityCostBufferRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    if all(row.status == "pass" for row in rows):
        return ("settlement_liquidity_cost_buffer_report_clear",)
    codes: list[str] = []
    if _has_any_row_reason(
        rows,
        ("settlement_cost_load_watch", "settlement_cost_load_blocking"),
    ):
        codes.append("settlement_cost_load_detected")
    if _has_any_row_reason(
        rows,
        ("liquidity_buffer_gap_watch", "liquidity_buffer_gap_blocking"),
    ):
        codes.append("liquidity_buffer_gap_detected")
    if _has_any_row_reason(rows, ("exit_cost_buffer_watch", "exit_cost_buffer_blocking")):
        codes.append("exit_cost_buffer_detected")
    if _has_any_row_reason(
        rows,
        ("settlement_delay_pressure_watch", "settlement_delay_pressure_blocking"),
    ):
        codes.append("settlement_delay_pressure_detected")
    if _has_any_row_reason(
        rows,
        (
            "composite_liquidity_cost_buffer_watch",
            "composite_liquidity_cost_buffer_blocking",
        ),
    ):
        codes.append("composite_liquidity_cost_buffer_detected")
    return tuple(codes)


def _reason_code_counts(
    rows: tuple[ResearchMarketSettlementLiquidityCostBufferRow, ...],
) -> tuple[ResearchMarketSettlementLiquidityCostBufferReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketSettlementLiquidityCostBufferReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ONE,
            ),
        )
    counts = Counter(code for row in rows for code in row.reason_codes)
    return tuple(
        ResearchMarketSettlementLiquidityCostBufferReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_candidates(
    candidates: Iterable[ResearchMarketSettlementLiquidityCostBufferCandidate],
) -> tuple[ResearchMarketSettlementLiquidityCostBufferCandidate, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Iterable):
        raise ValueError("candidates must be an iterable")
    normalized = tuple(candidates)
    for row in normalized:
        if type(row) is not ResearchMarketSettlementLiquidityCostBufferCandidate:
            raise ValueError(
                "candidates must contain ResearchMarketSettlementLiquidityCostBufferCandidate",
            )
        _require_hard_flags("candidate", row)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketSettlementLiquidityCostBufferRow],
) -> tuple[ResearchMarketSettlementLiquidityCostBufferRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketSettlementLiquidityCostBufferRow:
            raise ValueError(
                "rows must contain ResearchMarketSettlementLiquidityCostBufferRow",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketSettlementLiquidityCostBufferReasonCodeCount],
) -> tuple[ResearchMarketSettlementLiquidityCostBufferReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketSettlementLiquidityCostBufferReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketSettlementLiquidityCostBufferReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row(row: ResearchMarketSettlementLiquidityCostBufferRow) -> None:
    if row.reason_codes == ("settlement_liquidity_cost_buffer_clear",):
        if row.status != "pass":
            raise ValueError("clear row must have pass status")
        return
    if row.status == "pass":
        raise ValueError("pass row must only use clear reason code")
    has_blocking = any(code.endswith("_blocking") for code in row.reason_codes)
    if has_blocking and row.status != "block":
        raise ValueError("blocking reason codes require block status")
    if not has_blocking and row.status != "watch":
        raise ValueError("watch reason codes require watch status")


def _validate_report(report: ResearchMarketSettlementLiquidityCostBufferReport) -> None:
    rows = tuple(report.rows)
    for index, row in enumerate(rows, start=1):
        if row.row_number != _count(index):
            raise ValueError("row_number must match canonical row order")
    expected_values = {
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "settlement_cost_load_count": _reason_count(
            rows,
            ("settlement_cost_load_watch", "settlement_cost_load_blocking"),
        ),
        "liquidity_buffer_gap_count": _reason_count(
            rows,
            ("liquidity_buffer_gap_watch", "liquidity_buffer_gap_blocking"),
        ),
        "exit_cost_buffer_count": _reason_count(
            rows,
            ("exit_cost_buffer_watch", "exit_cost_buffer_blocking"),
        ),
        "settlement_delay_pressure_count": _reason_count(
            rows,
            ("settlement_delay_pressure_watch", "settlement_delay_pressure_blocking"),
        ),
        "mean_liquidity_cost_buffer_score": _mean(
            tuple(row.liquidity_cost_buffer_score for row in rows),
        ),
        "max_settlement_cost_ratio": _max_decimal(
            tuple(row.settlement_cost_ratio for row in rows),
        ),
        "min_liquidity_buffer_ratio": _min_decimal(
            tuple(row.liquidity_buffer_ratio for row in rows),
        ),
        "max_projected_exit_cost_ratio": _max_decimal(
            tuple(row.projected_exit_cost_ratio for row in rows),
        ),
        "max_settlement_delay_hours": _max_decimal(
            tuple(row.settlement_delay_hours for row in rows),
        ),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    _require_hard_flags("report", report)


def _report_payload_without_digest_from_report(
    report: ResearchMarketSettlementLiquidityCostBufferReport,
) -> dict[str, Any]:
    return _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        settlement_cost_load_count=report.settlement_cost_load_count,
        liquidity_buffer_gap_count=report.liquidity_buffer_gap_count,
        exit_cost_buffer_count=report.exit_cost_buffer_count,
        settlement_delay_pressure_count=report.settlement_delay_pressure_count,
        mean_liquidity_cost_buffer_score=report.mean_liquidity_cost_buffer_score,
        max_settlement_cost_ratio=report.max_settlement_cost_ratio,
        min_liquidity_buffer_ratio=report.min_liquidity_buffer_ratio,
        max_projected_exit_cost_ratio=report.max_projected_exit_cost_ratio,
        max_settlement_delay_hours=report.max_settlement_delay_hours,
        status=report.status,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        rows=report.rows,
    )


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    candidate_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    settlement_cost_load_count: Decimal,
    liquidity_buffer_gap_count: Decimal,
    exit_cost_buffer_count: Decimal,
    settlement_delay_pressure_count: Decimal,
    mean_liquidity_cost_buffer_score: Decimal,
    max_settlement_cost_ratio: Decimal,
    min_liquidity_buffer_ratio: Decimal,
    max_projected_exit_cost_ratio: Decimal,
    max_settlement_delay_hours: Decimal,
    status: str,
    reason_code_counts: tuple[
        ResearchMarketSettlementLiquidityCostBufferReasonCodeCount,
        ...,
    ],
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchMarketSettlementLiquidityCostBufferRow, ...],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "candidate_count": candidate_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "settlement_cost_load_count": settlement_cost_load_count,
        "liquidity_buffer_gap_count": liquidity_buffer_gap_count,
        "exit_cost_buffer_count": exit_cost_buffer_count,
        "settlement_delay_pressure_count": settlement_delay_pressure_count,
        "mean_liquidity_cost_buffer_score": mean_liquidity_cost_buffer_score,
        "max_settlement_cost_ratio": max_settlement_cost_ratio,
        "min_liquidity_buffer_ratio": min_liquidity_buffer_ratio,
        "max_projected_exit_cost_ratio": max_projected_exit_cost_ratio,
        "max_settlement_delay_hours": max_settlement_delay_hours,
        "status": status,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _expected_public_report_digest(
    report: ResearchMarketSettlementLiquidityCostBufferReport,
) -> str:
    return _public_digest(_report_payload_without_digest_from_report(report))


def _public_digest(payload: dict[str, Any]) -> str:
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("public digest payload must be a JSON object")
    encoded = _canonical_public_payload_json(ready)
    _reject_unsafe_public_payload(encoded)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal values must use exact Decimal")
        if not value.is_finite():
            raise ValueError("Decimal values must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("datetime values must use exact datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int:
        raise ValueError("JSON numerics must use Decimal")
    if hasattr(value, "__dataclass_fields__"):
        return _json_ready(
            {
                field_name: getattr(value, field_name)
                for field_name in value.__dataclass_fields__
                if field_name
                not in {
                    "raw_candidate_id",
                    "sensitive_context",
                }
            },
        )
    raise ValueError(f"value is not JSON serializable: {type(value).__name__}")


def _canonical_public_payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _reject_non_json_public_values(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_non_json_public_values(f"{label}.{key}", item)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _reject_non_json_public_values(f"{label}[{index}]", item)
        return
    if type(value) in (str, bool) or value is None:
        return
    if type(value) is int or isinstance(value, (Decimal, float)):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    raise ValueError(f"{label} must contain only canonical JSON values")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    _require_payload_flag_object("payload", payload)
    _require_nested_payload_hard_flags("payload", payload)


def _require_nested_payload_hard_flags(label: str, value: object) -> None:
    if type(value) is dict:
        if any(field_name in value for field_name in HARD_FLAG_FIELDS):
            _require_payload_flag_object(label, value)
        for key, item in value.items():
            _require_nested_payload_hard_flags(f"{label}.{key}", item)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _require_nested_payload_hard_flags(f"{label}[{index}]", item)


def _require_payload_flag_object(label: str, value: dict[str, Any]) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_exact_payload_keys(
    label: str,
    value: object,
    expected_keys: frozenset[str],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} schema must be a dict")
    if frozenset(value) != expected_keys:
        raise ValueError(f"{label} schema keys must match")
    return value


def _payload_list(label: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a list")
    return value


def _payload_decimal(label: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{label} must be a Decimal-derived string")
    try:
        normalized = _quantize(Decimal(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label} must be a Decimal-derived string") from None
    if not normalized.is_finite() or str(normalized) != value:
        raise ValueError(f"{label} must use a canonical Decimal-derived string")
    return normalized


def _payload_datetime(label: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{label} must be a datetime string")
    try:
        normalized = _as_utc(label, datetime.fromisoformat(value))
    except ValueError:
        raise ValueError(f"{label} must be a canonical UTC datetime string") from None
    if normalized.isoformat() != value:
        raise ValueError(f"{label} must be a canonical UTC datetime string")
    return normalized


def _payload_public_string(label: str, value: object) -> str:
    _require_public_string(label, value)
    return value


def _payload_member(
    label: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    _require_member(label, value, allowed_values)
    return value


def _payload_hard_flag(label: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{label} must be True")
    return True


def _payload_reason_codes(
    label: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        label,
        _payload_list(label, value),
        allowed_reason_codes,
    )


def _payload_reason_code_count(
    label: str,
    value: object,
) -> ResearchMarketSettlementLiquidityCostBufferReasonCodeCount:
    payload = _require_exact_payload_keys(
        label,
        value,
        REASON_CODE_COUNT_PAYLOAD_KEYS,
    )
    return ResearchMarketSettlementLiquidityCostBufferReasonCodeCount(
        reason_code=_payload_member(
            f"{label}.reason_code",
            payload["reason_code"],
            REASON_CODES,
        ),
        count=_payload_decimal(f"{label}.count", payload["count"]),
        paper_only=_payload_hard_flag(
            f"{label}.paper_only",
            payload["paper_only"],
        ),
        report_only=_payload_hard_flag(
            f"{label}.report_only",
            payload["report_only"],
        ),
        readonly=_payload_hard_flag(f"{label}.readonly", payload["readonly"]),
    )


def _payload_row(
    label: str,
    value: object,
) -> ResearchMarketSettlementLiquidityCostBufferRow:
    payload = _require_exact_payload_keys(label, value, ROW_PAYLOAD_KEYS)
    return ResearchMarketSettlementLiquidityCostBufferRow(
        row_number=_payload_decimal(f"{label}.row_number", payload["row_number"]),
        observed_at=_payload_datetime(f"{label}.observed_at", payload["observed_at"]),
        settlement_cost_ratio=_payload_decimal(
            f"{label}.settlement_cost_ratio",
            payload["settlement_cost_ratio"],
        ),
        settlement_cost_load_score=_payload_decimal(
            f"{label}.settlement_cost_load_score",
            payload["settlement_cost_load_score"],
        ),
        liquidity_buffer_ratio=_payload_decimal(
            f"{label}.liquidity_buffer_ratio",
            payload["liquidity_buffer_ratio"],
        ),
        liquidity_buffer_gap_ratio=_payload_decimal(
            f"{label}.liquidity_buffer_gap_ratio",
            payload["liquidity_buffer_gap_ratio"],
        ),
        liquidity_buffer_gap_score=_payload_decimal(
            f"{label}.liquidity_buffer_gap_score",
            payload["liquidity_buffer_gap_score"],
        ),
        projected_exit_cost_ratio=_payload_decimal(
            f"{label}.projected_exit_cost_ratio",
            payload["projected_exit_cost_ratio"],
        ),
        exit_cost_buffer_score=_payload_decimal(
            f"{label}.exit_cost_buffer_score",
            payload["exit_cost_buffer_score"],
        ),
        settlement_delay_hours=_payload_decimal(
            f"{label}.settlement_delay_hours",
            payload["settlement_delay_hours"],
        ),
        settlement_delay_score=_payload_decimal(
            f"{label}.settlement_delay_score",
            payload["settlement_delay_score"],
        ),
        liquidity_cost_buffer_score=_payload_decimal(
            f"{label}.liquidity_cost_buffer_score",
            payload["liquidity_cost_buffer_score"],
        ),
        status=_payload_member(f"{label}.status", payload["status"], STATUSES),
        reason_codes=_payload_reason_codes(
            f"{label}.reason_codes",
            payload["reason_codes"],
            ROW_REASON_CODES,
        ),
        paper_only=_payload_hard_flag(
            f"{label}.paper_only",
            payload["paper_only"],
        ),
        report_only=_payload_hard_flag(
            f"{label}.report_only",
            payload["report_only"],
        ),
        readonly=_payload_hard_flag(f"{label}.readonly", payload["readonly"]),
    )


def _reject_unsafe_public_payload(encoded_payload: str) -> None:
    lowered = encoded_payload.lower()
    unsafe_fragments = (
        "raw_candidate_id",
        "candidate_id",
        "candidate_reference",
        "market_id",
        "market_slug",
        "market_question",
        "market_reference",
        "slug",
        "question",
        "source_id",
        "source_reference",
        "source_url",
        "source_text",
        "url",
        "dsn",
        "table_name",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "auth",
        "credential",
        "".join(("private", "_key")),
        "".join(("api", "_key")),
        "".join(("sec", "ret")),
        "network",
        "database",
        "persist",
        "live",
        "".join(("siz", "ing")),
        "execution",
        "postgres://",
        "mysql://",
        "http://",
        "https://",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError("unsafe public payload surface")


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _status_count(
    rows: tuple[ResearchMarketSettlementLiquidityCostBufferRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchMarketSettlementLiquidityCostBufferRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    reason_set = set(reason_codes)
    return _count(sum(1 for row in rows if any(code in reason_set for code in row.reason_codes)))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _has_any_row_reason(
    rows: tuple[ResearchMarketSettlementLiquidityCostBufferRow, ...],
    reason_codes: tuple[str, ...],
) -> bool:
    reason_set = set(reason_codes)
    return any(any(code in reason_set for code in row.reason_codes) for row in rows)


def _draft_sort_key(draft: _RowDraft) -> tuple[int, Decimal, datetime, Decimal, Decimal]:
    return (
        -STATUS_WEIGHT[draft.status],
        -draft.liquidity_cost_buffer_score,
        draft.observed_at,
        -draft.settlement_cost_ratio,
        -draft.liquidity_buffer_gap_ratio,
    )


def _row_sort_key(
    row: ResearchMarketSettlementLiquidityCostBufferRow,
) -> tuple[int, Decimal, datetime, Decimal, Decimal]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.liquidity_cost_buffer_score,
        row.observed_at,
        -row.settlement_cost_ratio,
        -row.liquidity_buffer_gap_ratio,
    )


def _normalize_reason_codes(
    name: str,
    reason_codes: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    for code in normalized:
        _require_member(name, code, allowed_reason_codes)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return normalized


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_optional_string(name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_nonblank_string(name, value)
    return value


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> None:
    _require_nonblank_string(name, value)
    _reject_unsafe_identifier(name, value)


def _require_nonblank_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_member(name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{name} must be one of: {', '.join(allowed_values)}")


def _require_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_name} must exceed {watch_name}")


def _require_weights_total_one(
    config: ResearchMarketSettlementLiquidityCostBufferConfig,
) -> None:
    total = _quantize(
        config.settlement_cost_load_weight
        + config.liquidity_buffer_gap_weight
        + config.exit_cost_buffer_weight
        + config.settlement_delay_weight,
    )
    if total != ONE:
        raise ValueError("liquidity cost buffer weights must total 1.000000")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be 64 lowercase hex characters")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be 64 lowercase hex characters")


def _reject_unsafe_identifier(name: str, value: str) -> None:
    lowered = value.lower()
    if any(
        fragment in lowered
        for fragment in (
            "candidate_id",
            "market_id",
            "market_slug",
            "question",
            "source_url",
            "source_text",
            "dsn",
            "table_name",
            "token",
            "wallet",
            "order",
            "trade",
            "recommend",
        )
    ):
        raise ValueError(f"{name} contains unsafe public surface")
