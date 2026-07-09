"""Pure report-only resolution cost balance report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_RESOLUTION_COST_BALANCE_REPORT_CONFIG_VERSION = (
    "research-strategy-resolution-cost-balance-report-v0"
)
RESEARCH_STRATEGY_RESOLUTION_COST_BALANCE_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_REASON_CODES = (
    "credible_edge_block",
    "credible_edge_watch",
    "evidence_confidence_block",
    "evidence_confidence_watch",
    "fee_spread_haircut_block",
    "fee_spread_haircut_watch",
    "resolution_ambiguity_block",
    "resolution_ambiguity_watch",
    "resolution_cost_balance_pass",
    "review_latency_block",
    "review_latency_watch",
)
REPORT_REASON_CODES = (
    "credible_edge_review",
    "evidence_confidence_review",
    "fee_spread_haircut_review",
    "resolution_ambiguity_review",
    "resolution_cost_balance_report_block",
    "resolution_cost_balance_report_empty",
    "resolution_cost_balance_report_pass",
    "resolution_cost_balance_report_watch",
    "review_latency_review",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_ref",
    "candidate_id",
    "market_ref",
    "market_id",
    "market_slug",
    "market_question",
    "question",
    "source_url",
    "source_text",
    "source_dsn",
    "dsn",
    "table_name",
    "token",
    "api_key",
    "credential",
    "secret",
    "private",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "trad" + "e",
    "trad" + "ing",
    "li" + "ve",
    "data" + "base",
    "net" + "work",
    "b" + "uy",
    "se" + "ll",
    "reco" + "mmendation",
    "siz" + "ing",
    "://",
)


@dataclass(frozen=True)
class ResearchStrategyResolutionCostBalanceConfig:
    config_version: str
    credible_edge_pass_floor: Decimal
    credible_edge_watch_floor: Decimal
    resolution_ambiguity_pass_ceiling: Decimal
    resolution_ambiguity_watch_ceiling: Decimal
    review_latency_pass_ceiling: Decimal
    review_latency_watch_ceiling: Decimal
    fee_spread_haircut_pass_ceiling: Decimal
    fee_spread_haircut_watch_ceiling: Decimal
    evidence_confidence_pass_floor: Decimal
    evidence_confidence_watch_floor: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionCostBalanceConfig:
            raise TypeError("config must be exactly ResearchStrategyResolutionCostBalanceConfig")
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "credible_edge_pass_floor",
            "credible_edge_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_ambiguity_pass_ceiling",
            "resolution_ambiguity_watch_ceiling",
            "review_latency_pass_ceiling",
            "review_latency_watch_ceiling",
            "fee_spread_haircut_pass_ceiling",
            "fee_spread_haircut_watch_ceiling",
            "evidence_confidence_pass_floor",
            "evidence_confidence_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "credible_edge",
            self.credible_edge_pass_floor,
            self.credible_edge_watch_floor,
        )
        _require_ceiling_pair(
            "resolution_ambiguity",
            self.resolution_ambiguity_pass_ceiling,
            self.resolution_ambiguity_watch_ceiling,
        )
        _require_ceiling_pair(
            "review_latency",
            self.review_latency_pass_ceiling,
            self.review_latency_watch_ceiling,
        )
        _require_ceiling_pair(
            "fee_spread_haircut",
            self.fee_spread_haircut_pass_ceiling,
            self.fee_spread_haircut_watch_ceiling,
        )
        _require_floor_pair(
            "evidence_confidence",
            self.evidence_confidence_pass_floor,
            self.evidence_confidence_watch_floor,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionCostBalanceInput:
    candidate_ref: str
    market_ref: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    observed_at: datetime
    expected_edge: Decimal
    resolution_ambiguity_score: Decimal
    review_latency_score: Decimal
    fee_haircut: Decimal
    spread_haircut: Decimal
    evidence_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionCostBalanceInput:
            raise TypeError("input must be exactly ResearchStrategyResolutionCostBalanceInput")
        for field_name in (
            "candidate_ref",
            "market_ref",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
        ):
            _require_nonempty_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "expected_edge",
            _normalize_probability("expected_edge", self.expected_edge),
        )
        for field_name in (
            "resolution_ambiguity_score",
            "review_latency_score",
            "fee_haircut",
            "spread_haircut",
            "evidence_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionCostBalanceReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionCostBalanceReasonCodeCount:
            raise TypeError(
                "reason count must be exactly "
                "ResearchStrategyResolutionCostBalanceReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionCostBalanceRow:
    candidate_ref: str
    market_ref: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    observed_at: datetime
    expected_edge: Decimal
    resolution_ambiguity_score: Decimal
    resolution_ambiguity_haircut: Decimal
    review_latency_score: Decimal
    review_latency_haircut: Decimal
    fee_haircut: Decimal
    spread_haircut: Decimal
    fee_spread_haircut: Decimal
    pre_confidence_edge: Decimal
    evidence_confidence_score: Decimal
    confidence_adjusted_edge: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionCostBalanceRow:
            raise TypeError("row must be exactly ResearchStrategyResolutionCostBalanceRow")
        for field_name in (
            "candidate_ref",
            "market_ref",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
        ):
            _require_nonempty_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_edge",
            "resolution_ambiguity_score",
            "review_latency_score",
            "fee_haircut",
            "spread_haircut",
            "fee_spread_haircut",
            "evidence_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_ambiguity_haircut",
            "review_latency_haircut",
            "pre_confidence_edge",
            "confidence_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyResolutionCostBalanceReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_expected_edge: Decimal
    mean_fee_spread_haircut: Decimal
    mean_confidence_adjusted_edge: Decimal
    mean_evidence_confidence_score: Decimal
    max_resolution_ambiguity_score: Decimal
    max_review_latency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyResolutionCostBalanceReasonCodeCount, ...]
    rows: tuple[ResearchStrategyResolutionCostBalanceRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionCostBalanceReport:
            raise TypeError("report must be exactly ResearchStrategyResolutionCostBalanceReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in ("source_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_expected_edge",
            "mean_fee_spread_haircut",
            "mean_evidence_confidence_score",
            "max_resolution_ambiguity_score",
            "max_review_latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_confidence_adjusted_edge",
            _normalize_decimal(
                "mean_confidence_adjusted_edge",
                self.mean_confidence_adjusted_edge,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_research_strategy_resolution_cost_balance_report(
    inputs: Iterable[ResearchStrategyResolutionCostBalanceInput],
    *,
    config: ResearchStrategyResolutionCostBalanceConfig,
    generated_at: datetime,
) -> ResearchStrategyResolutionCostBalanceReport:
    if type(config) is not ResearchStrategyResolutionCostBalanceConfig:
        raise ValueError("config must be a ResearchStrategyResolutionCostBalanceConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(value, config=config, generated_at=generated_at_utc)
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyResolutionCostBalanceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_expected_edge=_mean(tuple(row.expected_edge for row in rows)),
        mean_fee_spread_haircut=_mean(tuple(row.fee_spread_haircut for row in rows)),
        mean_confidence_adjusted_edge=_mean(
            tuple(row.confidence_adjusted_edge for row in rows),
        ),
        mean_evidence_confidence_score=_mean(
            tuple(row.evidence_confidence_score for row in rows),
        ),
        max_resolution_ambiguity_score=_max_decimal(
            tuple(row.resolution_ambiguity_score for row in rows),
        ),
        max_review_latency_score=_max_decimal(
            tuple(row.review_latency_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_resolution_cost_balance_report_payload(
    report: ResearchStrategyResolutionCostBalanceReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyResolutionCostBalanceReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _public_report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        if "derived_validation_digest" not in report:
            raise ValueError("derived_validation_digest must be populated")
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyResolutionCostBalanceReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _public_report_payload(
    report: ResearchStrategyResolutionCostBalanceReport,
) -> dict[str, Any]:
    payload = asdict(report)
    payload["rows"] = [
        _public_row_payload(index, row)
        for index, row in enumerate(report.rows, start=1)
    ]
    payload.pop("derived_validation_digest", None)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    _verify_public_payload_integrity(public_payload)
    return public_payload


def _public_row_payload(
    row_number: int,
    row: ResearchStrategyResolutionCostBalanceRow,
) -> dict[str, Any]:
    payload = asdict(row)
    for field_name in (
        "candidate_ref",
        "market_ref",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
    ):
        payload.pop(field_name, None)
    payload.pop("derived_validation_digest", None)
    payload["row_number"] = _count(row_number)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    return public_payload


def _row_from_input(
    value: ResearchStrategyResolutionCostBalanceInput,
    *,
    config: ResearchStrategyResolutionCostBalanceConfig,
    generated_at: datetime,
) -> ResearchStrategyResolutionCostBalanceRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    resolution_ambiguity_haircut = _multiply_decimal(
        value.expected_edge,
        value.resolution_ambiguity_score,
    )
    review_latency_haircut = _multiply_decimal(
        value.expected_edge,
        value.review_latency_score,
    )
    fee_spread_haircut = _sum_decimals((value.fee_haircut, value.spread_haircut))
    pre_confidence_edge = _subtract_decimal(
        value.expected_edge,
        _sum_decimals(
            (
                resolution_ambiguity_haircut,
                review_latency_haircut,
                fee_spread_haircut,
            ),
        ),
    )
    confidence_adjusted_edge = _multiply_decimal(
        pre_confidence_edge,
        value.evidence_confidence_score,
    )
    return ResearchStrategyResolutionCostBalanceRow(
        candidate_ref=value.candidate_ref,
        market_ref=value.market_ref,
        market_slug=value.market_slug,
        market_question=value.market_question,
        source_url=value.source_url,
        source_text=value.source_text,
        observed_at=observed_at,
        expected_edge=value.expected_edge,
        resolution_ambiguity_score=value.resolution_ambiguity_score,
        resolution_ambiguity_haircut=resolution_ambiguity_haircut,
        review_latency_score=value.review_latency_score,
        review_latency_haircut=review_latency_haircut,
        fee_haircut=value.fee_haircut,
        spread_haircut=value.spread_haircut,
        fee_spread_haircut=fee_spread_haircut,
        pre_confidence_edge=pre_confidence_edge,
        evidence_confidence_score=value.evidence_confidence_score,
        confidence_adjusted_edge=confidence_adjusted_edge,
        status=_row_status(
            confidence_adjusted_edge=confidence_adjusted_edge,
            fee_spread_haircut=fee_spread_haircut,
            value=value,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            confidence_adjusted_edge=confidence_adjusted_edge,
            fee_spread_haircut=fee_spread_haircut,
            value=value,
            config=config,
        ),
    )


def _row_status(
    *,
    confidence_adjusted_edge: Decimal,
    fee_spread_haircut: Decimal,
    value: ResearchStrategyResolutionCostBalanceInput,
    config: ResearchStrategyResolutionCostBalanceConfig,
) -> str:
    if (
        confidence_adjusted_edge < config.credible_edge_watch_floor
        or value.resolution_ambiguity_score > config.resolution_ambiguity_watch_ceiling
        or value.review_latency_score > config.review_latency_watch_ceiling
        or fee_spread_haircut > config.fee_spread_haircut_watch_ceiling
        or value.evidence_confidence_score < config.evidence_confidence_watch_floor
    ):
        return "block"
    if (
        confidence_adjusted_edge < config.credible_edge_pass_floor
        or value.resolution_ambiguity_score > config.resolution_ambiguity_pass_ceiling
        or value.review_latency_score > config.review_latency_pass_ceiling
        or fee_spread_haircut > config.fee_spread_haircut_pass_ceiling
        or value.evidence_confidence_score < config.evidence_confidence_pass_floor
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    confidence_adjusted_edge: Decimal,
    fee_spread_haircut: Decimal,
    value: ResearchStrategyResolutionCostBalanceInput,
    config: ResearchStrategyResolutionCostBalanceConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if confidence_adjusted_edge < config.credible_edge_watch_floor:
        codes.append("credible_edge_block")
    elif confidence_adjusted_edge < config.credible_edge_pass_floor:
        codes.append("credible_edge_watch")
    if value.evidence_confidence_score < config.evidence_confidence_watch_floor:
        codes.append("evidence_confidence_block")
    elif value.evidence_confidence_score < config.evidence_confidence_pass_floor:
        codes.append("evidence_confidence_watch")
    if fee_spread_haircut > config.fee_spread_haircut_watch_ceiling:
        codes.append("fee_spread_haircut_block")
    elif fee_spread_haircut > config.fee_spread_haircut_pass_ceiling:
        codes.append("fee_spread_haircut_watch")
    if value.resolution_ambiguity_score > config.resolution_ambiguity_watch_ceiling:
        codes.append("resolution_ambiguity_block")
    elif value.resolution_ambiguity_score > config.resolution_ambiguity_pass_ceiling:
        codes.append("resolution_ambiguity_watch")
    if value.review_latency_score > config.review_latency_watch_ceiling:
        codes.append("review_latency_block")
    elif value.review_latency_score > config.review_latency_pass_ceiling:
        codes.append("review_latency_watch")
    if not codes:
        codes.append("resolution_cost_balance_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(rows: tuple[ResearchStrategyResolutionCostBalanceRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyResolutionCostBalanceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_cost_balance_report_empty",)
    codes: list[str] = []
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    if any(code.startswith("credible_edge_") for code in row_codes):
        codes.append("credible_edge_review")
    if any(code.startswith("evidence_confidence_") for code in row_codes):
        codes.append("evidence_confidence_review")
    if any(code.startswith("fee_spread_haircut_") for code in row_codes):
        codes.append("fee_spread_haircut_review")
    if any(code.startswith("resolution_ambiguity_") for code in row_codes):
        codes.append("resolution_ambiguity_review")
    codes.append(f"resolution_cost_balance_report_{_report_status(rows)}")
    if any(code.startswith("review_latency_") for code in row_codes):
        codes.append("review_latency_review")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyResolutionCostBalanceRow, ...],
) -> tuple[ResearchStrategyResolutionCostBalanceReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    total = _count(len(rows))
    values = []
    for reason_code, count in counts.items():
        values.append(
            ResearchStrategyResolutionCostBalanceReasonCodeCount(
                reason_code=reason_code,
                count=_count_decimal(count),
                input_ratio=_divide_decimal(count, total) if total != ZERO else ZERO,
            ),
        )
    return tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyResolutionCostBalanceInput],
) -> tuple[ResearchStrategyResolutionCostBalanceInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyResolutionCostBalanceInput:
            raise ValueError(
                "inputs must contain ResearchStrategyResolutionCostBalanceInput",
            )
        _require_hard_flags("input", value)
        if value.candidate_ref in seen:
            raise ValueError("duplicate candidate_ref")
        seen.add(value.candidate_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyResolutionCostBalanceRow],
) -> tuple[ResearchStrategyResolutionCostBalanceRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyResolutionCostBalanceRow:
            raise ValueError("rows must contain ResearchStrategyResolutionCostBalanceRow")
        _require_hard_flags("row", row)
        _verify_dataclass_digest(row)
        _validate_row_consistency(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchStrategyResolutionCostBalanceReasonCodeCount],
) -> tuple[ResearchStrategyResolutionCostBalanceReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for item in normalized:
        if type(item) is not ResearchStrategyResolutionCostBalanceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyResolutionCostBalanceReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _row_sort_key(row: ResearchStrategyResolutionCostBalanceRow) -> tuple[object, ...]:
    status_rank = {"block": 0, "watch": 1, "pass": 2}
    return (
        status_rank[row.status],
        row.confidence_adjusted_edge,
        row.candidate_ref,
    )


def _status_count(
    rows: tuple[ResearchStrategyResolutionCostBalanceRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(ONE for row in rows if row.status == status))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _normalize_decimal("mean", ZERO)
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _normalize_decimal("max", ZERO)
    return max(values)


def _validate_row_consistency(row: ResearchStrategyResolutionCostBalanceRow) -> None:
    if row.resolution_ambiguity_haircut != _multiply_decimal(
        row.expected_edge,
        row.resolution_ambiguity_score,
    ):
        raise ValueError("resolution_ambiguity_haircut mismatch")
    if row.review_latency_haircut != _multiply_decimal(
        row.expected_edge,
        row.review_latency_score,
    ):
        raise ValueError("review_latency_haircut mismatch")
    if row.fee_spread_haircut != _sum_decimals((row.fee_haircut, row.spread_haircut)):
        raise ValueError("fee_spread_haircut mismatch")
    expected_pre_confidence_edge = _subtract_decimal(
        row.expected_edge,
        _sum_decimals(
            (
                row.resolution_ambiguity_haircut,
                row.review_latency_haircut,
                row.fee_spread_haircut,
            ),
        ),
    )
    if row.pre_confidence_edge != expected_pre_confidence_edge:
        raise ValueError("pre_confidence_edge mismatch")
    if row.confidence_adjusted_edge != _multiply_decimal(
        row.pre_confidence_edge,
        row.evidence_confidence_score,
    ):
        raise ValueError("confidence_adjusted_edge mismatch")
    if row.status == "pass" and row.reason_codes != ("resolution_cost_balance_pass",):
        raise ValueError("pass rows must use pass reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must include a block reason code")
    if row.status == "watch" and any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("watch rows must not include block reason codes")


def _validate_report_consistency(report: ResearchStrategyResolutionCostBalanceReport) -> None:
    rows = report.rows
    if report.source_row_count != _count(len(rows)):
        raise ValueError("source_row_count mismatch")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count mismatch")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count mismatch")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count mismatch")
    if report.mean_expected_edge != _mean(tuple(row.expected_edge for row in rows)):
        raise ValueError("mean_expected_edge mismatch")
    if report.mean_fee_spread_haircut != _mean(
        tuple(row.fee_spread_haircut for row in rows),
    ):
        raise ValueError("mean_fee_spread_haircut mismatch")
    if report.mean_confidence_adjusted_edge != _mean(
        tuple(row.confidence_adjusted_edge for row in rows),
    ):
        raise ValueError("mean_confidence_adjusted_edge mismatch")
    if report.mean_evidence_confidence_score != _mean(
        tuple(row.evidence_confidence_score for row in rows),
    ):
        raise ValueError("mean_evidence_confidence_score mismatch")
    if report.max_resolution_ambiguity_score != _max_decimal(
        tuple(row.resolution_ambiguity_score for row in rows),
    ):
        raise ValueError("max_resolution_ambiguity_score mismatch")
    if report.max_review_latency_score != _max_decimal(
        tuple(row.review_latency_score for row in rows),
    ):
        raise ValueError("max_review_latency_score mismatch")
    if report.status != _report_status(rows):
        raise ValueError("status mismatch")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes mismatch")
    if report.reason_code_counts != _reason_code_counts_from_rows(rows):
        raise ValueError("reason_code_counts mismatch")


def _verify_report_integrity(report: ResearchStrategyResolutionCostBalanceReport) -> None:
    _verify_dataclass_digest(report)
    _validate_report_consistency(report)


def _apply_or_verify_digest(value: object) -> None:
    digest = getattr(value, "derived_validation_digest", None)
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _dataclass_digest(value)
    if digest == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _verify_dataclass_digest(value: object) -> None:
    digest = getattr(value, "derived_validation_digest", None)
    if type(digest) is not str or digest == "":
        raise ValueError("derived_validation_digest must be populated")
    if digest != _dataclass_digest(value):
        raise ValueError("derived_validation_digest mismatch")


def _dataclass_digest(value: object) -> str:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    payload = asdict(value)
    payload.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _public_payload_digest(payload: dict[str, Any]) -> str:
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _verify_public_payload_integrity(value: object) -> None:
    if isinstance(value, dict):
        if "derived_validation_digest" in value:
            digest = value["derived_validation_digest"]
            if type(digest) is not str or digest == "":
                raise ValueError("derived_validation_digest must be populated")
            if digest != _public_payload_digest(value):
                raise ValueError("derived_validation_digest mismatch")
        for item in value.values():
            _verify_public_payload_integrity(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _verify_public_payload_integrity(item)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_canonical_public_string(name: str, value: object) -> None:
    text = _require_nonempty_string(name, value)
    if text.strip() != text or any(character.isspace() for character in text):
        raise ValueError(f"{name} must be canonical")


def _require_nonempty_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value == "" or value.strip() == "":
        raise ValueError(f"{name} must be non-empty")
    return value


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_STRATEGY_RESOLUTION_COST_BALANCE_REPORT_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str or value not in ROW_REASON_CODES:
        raise ValueError(f"{name} must be a supported reason code")


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{name} must be an iterable")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    for value in normalized:
        if type(value) is not str or value not in allowed:
            raise ValueError(f"{name} has an unsupported reason code")
    return tuple(sorted(dict.fromkeys(normalized)))


def _require_floor_pair(name: str, pass_floor: Decimal, watch_floor: Decimal) -> None:
    if pass_floor < watch_floor:
        raise ValueError(f"{name}_pass_floor must be >= {name}_watch_floor")


def _require_ceiling_pair(name: str, pass_ceiling: Decimal, watch_ceiling: Decimal) -> None:
    if pass_ceiling > watch_ceiling:
        raise ValueError(f"{name}_pass_ceiling must be <= {name}_watch_ceiling")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole number")
    return _count_decimal(decimal_value)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(RATIO_QUANTUM)


def _count_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _sum_decimals(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
        return total.quantize(RATIO_QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(RATIO_QUANTUM)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(RATIO_QUANTUM)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return (left / right).quantize(RATIO_QUANTUM)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) in (int, float):
        raise ValueError("JSON value must use Decimal-derived string values")
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"{label} has unsafe value")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_RESOLUTION_COST_BALANCE_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_RESOLUTION_COST_BALANCE_REPORT_STATUSES",
    "ResearchStrategyResolutionCostBalanceConfig",
    "ResearchStrategyResolutionCostBalanceInput",
    "ResearchStrategyResolutionCostBalanceReasonCodeCount",
    "ResearchStrategyResolutionCostBalanceRow",
    "ResearchStrategyResolutionCostBalanceReport",
    "build_research_strategy_resolution_cost_balance_report",
    "research_strategy_resolution_cost_balance_report_payload",
)
