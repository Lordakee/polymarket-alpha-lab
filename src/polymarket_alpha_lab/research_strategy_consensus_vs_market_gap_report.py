"""Pure consensus-vs-market gap triage report for manual review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_CONSENSUS_VS_MARKET_GAP_REPORT_CONFIG_VERSION = (
    "research-strategy-consensus-vs-market-gap-report-v0"
)
RESEARCH_STRATEGY_CONSENSUS_VS_MARKET_GAP_STATUSES = (
    "pass",
    "watch",
    "block",
)

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wal" + "let",
    "or" + "der",
    "li" + "ve",
    "trad" + "e",
    "trad" + "ing",
    "data" + "base",
    "net" + "work",
    "persist",
    "signing",
    "mutation",
    "b" + "uy",
    "se" + "ll",
    "reco" + "mmendation",
    "siz" + "ing",
)

GAP_DIRECTIONS = (
    "market_below_consensus_band",
    "market_above_consensus_band",
    "within_consensus_band",
)
ROW_REASON_CODES = (
    "confidence_haircut_block",
    "confidence_haircut_watch",
    "confidence_score_block",
    "confidence_score_watch",
    "consensus_band_width_block",
    "consensus_band_width_watch",
    "consensus_vs_market_gap_pass",
    "gap_after_haircuts_block",
    "gap_after_haircuts_watch",
    "total_cost_haircut_block",
    "total_cost_haircut_watch",
    "within_consensus_band_block",
)
REPORT_REASON_CODES = (
    "confidence_haircut_review",
    "confidence_score_review",
    "consensus_band_width_review",
    "consensus_vs_market_gap_report_block",
    "consensus_vs_market_gap_report_empty",
    "consensus_vs_market_gap_report_pass",
    "consensus_vs_market_gap_report_watch",
    "gap_after_haircuts_review",
    "total_cost_haircut_review",
)


@dataclass(frozen=True)
class ResearchStrategyConsensusVsMarketGapConfig:
    config_version: str
    gap_after_haircuts_pass_floor: Decimal
    gap_after_haircuts_watch_floor: Decimal
    confidence_score_pass_floor: Decimal
    confidence_score_watch_floor: Decimal
    total_cost_haircut_pass_ceiling: Decimal
    total_cost_haircut_watch_ceiling: Decimal
    confidence_haircut_pass_ceiling: Decimal
    confidence_haircut_watch_ceiling: Decimal
    consensus_band_width_pass_ceiling: Decimal
    consensus_band_width_watch_ceiling: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "gap_after_haircuts_pass_floor",
            "gap_after_haircuts_watch_floor",
            "confidence_score_pass_floor",
            "confidence_score_watch_floor",
            "total_cost_haircut_pass_ceiling",
            "total_cost_haircut_watch_ceiling",
            "confidence_haircut_pass_ceiling",
            "confidence_haircut_watch_ceiling",
            "consensus_band_width_pass_ceiling",
            "consensus_band_width_watch_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "gap_after_haircuts",
            self.gap_after_haircuts_pass_floor,
            self.gap_after_haircuts_watch_floor,
        )
        _require_floor_pair(
            "confidence_score",
            self.confidence_score_pass_floor,
            self.confidence_score_watch_floor,
        )
        _require_ceiling_pair(
            "total_cost_haircut",
            self.total_cost_haircut_pass_ceiling,
            self.total_cost_haircut_watch_ceiling,
        )
        _require_ceiling_pair(
            "confidence_haircut",
            self.confidence_haircut_pass_ceiling,
            self.confidence_haircut_watch_ceiling,
        )
        _require_ceiling_pair(
            "consensus_band_width",
            self.consensus_band_width_pass_ceiling,
            self.consensus_band_width_watch_ceiling,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyConsensusVsMarketGapInput:
    candidate_id: str
    market_id: str
    market_slug: str
    observed_at: datetime
    consensus_lower_probability: Decimal
    consensus_upper_probability: Decimal
    market_probability: Decimal
    fee_probability_haircut: Decimal
    spread_probability_haircut: Decimal
    slippage_probability_haircut: Decimal
    confidence_probability_haircut: Decimal
    specialist_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_id", "market_slug"):
            _require_raw_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "consensus_lower_probability",
            "consensus_upper_probability",
            "market_probability",
            "fee_probability_haircut",
            "spread_probability_haircut",
            "slippage_probability_haircut",
            "confidence_probability_haircut",
            "specialist_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.consensus_upper_probability < self.consensus_lower_probability:
            raise ValueError(
                "consensus_upper_probability must be at least consensus_lower_probability",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyConsensusVsMarketGapReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
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
class ResearchStrategyConsensusVsMarketGapRow:
    candidate_id: str
    market_id: str
    market_slug: str
    observed_at: datetime
    consensus_lower_probability: Decimal
    consensus_upper_probability: Decimal
    consensus_band_width: Decimal
    market_probability: Decimal
    fee_probability_haircut: Decimal
    spread_probability_haircut: Decimal
    slippage_probability_haircut: Decimal
    total_cost_haircut: Decimal
    confidence_probability_haircut: Decimal
    specialist_confidence_score: Decimal
    market_probability_after_haircuts: Decimal
    consensus_gap_after_haircuts: Decimal
    gap_direction: str
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_id", "market_slug"):
            _require_raw_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "consensus_lower_probability",
            "consensus_upper_probability",
            "consensus_band_width",
            "market_probability",
            "fee_probability_haircut",
            "spread_probability_haircut",
            "slippage_probability_haircut",
            "total_cost_haircut",
            "confidence_probability_haircut",
            "specialist_confidence_score",
            "market_probability_after_haircuts",
            "consensus_gap_after_haircuts",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_gap_direction("gap_direction", self.gap_direction)
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
class ResearchStrategyConsensusVsMarketGapReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_consensus_gap_after_haircuts: Decimal
    mean_total_cost_haircut: Decimal
    mean_confidence_haircut: Decimal
    minimum_specialist_confidence_score: Decimal
    widest_consensus_band_width: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyConsensusVsMarketGapReasonCodeCount, ...]
    rows: tuple[ResearchStrategyConsensusVsMarketGapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("source_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_consensus_gap_after_haircuts",
            "mean_total_cost_haircut",
            "mean_confidence_haircut",
            "minimum_specialist_confidence_score",
            "widest_consensus_band_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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


def build_research_strategy_consensus_vs_market_gap_report(
    inputs: Iterable[ResearchStrategyConsensusVsMarketGapInput],
    *,
    config: ResearchStrategyConsensusVsMarketGapConfig,
    generated_at: datetime,
) -> ResearchStrategyConsensusVsMarketGapReport:
    if type(config) is not ResearchStrategyConsensusVsMarketGapConfig:
        raise ValueError("config must be a ResearchStrategyConsensusVsMarketGapConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyConsensusVsMarketGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_consensus_gap_after_haircuts=_mean(
            tuple(row.consensus_gap_after_haircuts for row in rows),
        ),
        mean_total_cost_haircut=_mean(tuple(row.total_cost_haircut for row in rows)),
        mean_confidence_haircut=_mean(
            tuple(row.confidence_probability_haircut for row in rows),
        ),
        minimum_specialist_confidence_score=_min_decimal(
            tuple(row.specialist_confidence_score for row in rows),
        ),
        widest_consensus_band_width=_max_decimal(
            tuple(row.consensus_band_width for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows, config=config),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_consensus_vs_market_gap_report_payload(
    report: ResearchStrategyConsensusVsMarketGapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyConsensusVsMarketGapReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _public_report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyConsensusVsMarketGapReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _public_report_payload(
    report: ResearchStrategyConsensusVsMarketGapReport,
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
    row: ResearchStrategyConsensusVsMarketGapRow,
) -> dict[str, Any]:
    payload = asdict(row)
    for field_name in ("candidate_id", "market_id", "market_slug"):
        payload.pop(field_name, None)
    payload.pop("derived_validation_digest", None)
    payload["row_number"] = _count(row_number)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    return public_payload


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


def _row_from_input(
    value: ResearchStrategyConsensusVsMarketGapInput,
    *,
    config: ResearchStrategyConsensusVsMarketGapConfig,
    generated_at: datetime,
) -> ResearchStrategyConsensusVsMarketGapRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    consensus_band_width = _subtract_decimal(
        value.consensus_upper_probability,
        value.consensus_lower_probability,
    )
    total_cost_haircut = _sum_decimals(
        (
            value.fee_probability_haircut,
            value.spread_probability_haircut,
            value.slippage_probability_haircut,
        ),
    )
    market_after_haircuts, consensus_gap, gap_direction = _market_gap_after_haircuts(
        consensus_lower_probability=value.consensus_lower_probability,
        consensus_upper_probability=value.consensus_upper_probability,
        market_probability=value.market_probability,
        total_cost_haircut=total_cost_haircut,
        confidence_haircut=value.confidence_probability_haircut,
    )
    return ResearchStrategyConsensusVsMarketGapRow(
        candidate_id=value.candidate_id,
        market_id=value.market_id,
        market_slug=value.market_slug,
        observed_at=observed_at,
        consensus_lower_probability=value.consensus_lower_probability,
        consensus_upper_probability=value.consensus_upper_probability,
        consensus_band_width=consensus_band_width,
        market_probability=value.market_probability,
        fee_probability_haircut=value.fee_probability_haircut,
        spread_probability_haircut=value.spread_probability_haircut,
        slippage_probability_haircut=value.slippage_probability_haircut,
        total_cost_haircut=total_cost_haircut,
        confidence_probability_haircut=value.confidence_probability_haircut,
        specialist_confidence_score=value.specialist_confidence_score,
        market_probability_after_haircuts=market_after_haircuts,
        consensus_gap_after_haircuts=consensus_gap,
        gap_direction=gap_direction,
        status=_row_status(
            consensus_band_width=consensus_band_width,
            consensus_gap_after_haircuts=consensus_gap,
            gap_direction=gap_direction,
            total_cost_haircut=total_cost_haircut,
            value=value,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            consensus_band_width=consensus_band_width,
            consensus_gap_after_haircuts=consensus_gap,
            gap_direction=gap_direction,
            total_cost_haircut=total_cost_haircut,
            value=value,
            config=config,
        ),
    )


def _market_gap_after_haircuts(
    *,
    consensus_lower_probability: Decimal,
    consensus_upper_probability: Decimal,
    market_probability: Decimal,
    total_cost_haircut: Decimal,
    confidence_haircut: Decimal,
) -> tuple[Decimal, Decimal, str]:
    haircut = _sum_decimals((total_cost_haircut, confidence_haircut))
    if market_probability < consensus_lower_probability:
        adjusted_market = _min_probability(_sum_decimals((market_probability, haircut)))
        return (
            adjusted_market,
            _max_decimal_value(
                ZERO.quantize(RATIO_QUANTUM),
                _subtract_decimal(consensus_lower_probability, adjusted_market),
            ),
            "market_below_consensus_band",
        )
    if market_probability > consensus_upper_probability:
        adjusted_market = _max_decimal_value(
            ZERO.quantize(RATIO_QUANTUM),
            _subtract_decimal(market_probability, haircut),
        )
        return (
            adjusted_market,
            _max_decimal_value(
                ZERO.quantize(RATIO_QUANTUM),
                _subtract_decimal(adjusted_market, consensus_upper_probability),
            ),
            "market_above_consensus_band",
        )
    return (
        market_probability,
        ZERO.quantize(RATIO_QUANTUM),
        "within_consensus_band",
    )


def _row_status(
    *,
    consensus_band_width: Decimal,
    consensus_gap_after_haircuts: Decimal,
    gap_direction: str,
    total_cost_haircut: Decimal,
    value: ResearchStrategyConsensusVsMarketGapInput,
    config: ResearchStrategyConsensusVsMarketGapConfig,
) -> str:
    if (
        gap_direction == "within_consensus_band"
        or consensus_gap_after_haircuts < config.gap_after_haircuts_watch_floor
        or total_cost_haircut > config.total_cost_haircut_watch_ceiling
        or value.confidence_probability_haircut > config.confidence_haircut_watch_ceiling
        or value.specialist_confidence_score < config.confidence_score_watch_floor
        or consensus_band_width > config.consensus_band_width_watch_ceiling
    ):
        return "block"
    if (
        consensus_gap_after_haircuts < config.gap_after_haircuts_pass_floor
        or total_cost_haircut > config.total_cost_haircut_pass_ceiling
        or value.confidence_probability_haircut > config.confidence_haircut_pass_ceiling
        or value.specialist_confidence_score < config.confidence_score_pass_floor
        or consensus_band_width > config.consensus_band_width_pass_ceiling
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    consensus_band_width: Decimal,
    consensus_gap_after_haircuts: Decimal,
    gap_direction: str,
    total_cost_haircut: Decimal,
    value: ResearchStrategyConsensusVsMarketGapInput,
    config: ResearchStrategyConsensusVsMarketGapConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if value.confidence_probability_haircut > config.confidence_haircut_watch_ceiling:
        codes.append("confidence_haircut_block")
    if value.specialist_confidence_score < config.confidence_score_watch_floor:
        codes.append("confidence_score_block")
    if consensus_gap_after_haircuts < config.gap_after_haircuts_watch_floor:
        codes.append("gap_after_haircuts_block")
    if gap_direction == "within_consensus_band":
        codes.append("within_consensus_band_block")
    if total_cost_haircut > config.total_cost_haircut_watch_ceiling:
        codes.append("total_cost_haircut_block")
    if consensus_band_width > config.consensus_band_width_watch_ceiling:
        codes.append("consensus_band_width_block")
    if codes:
        return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)
    if value.confidence_probability_haircut > config.confidence_haircut_pass_ceiling:
        codes.append("confidence_haircut_watch")
    if value.specialist_confidence_score < config.confidence_score_pass_floor:
        codes.append("confidence_score_watch")
    if consensus_gap_after_haircuts < config.gap_after_haircuts_pass_floor:
        codes.append("gap_after_haircuts_watch")
    if total_cost_haircut > config.total_cost_haircut_pass_ceiling:
        codes.append("total_cost_haircut_watch")
    if consensus_band_width > config.consensus_band_width_pass_ceiling:
        codes.append("consensus_band_width_watch")
    if not codes:
        codes.append("consensus_vs_market_gap_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(rows: tuple[ResearchStrategyConsensusVsMarketGapRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyConsensusVsMarketGapRow, ...],
    *,
    config: ResearchStrategyConsensusVsMarketGapConfig,
) -> tuple[str, ...]:
    if not rows:
        return ("consensus_vs_market_gap_report_empty",)
    report_status = _report_status(rows)
    codes = [f"consensus_vs_market_gap_report_{report_status}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    if any(row.confidence_probability_haircut > config.confidence_haircut_pass_ceiling for row in rows):
        codes.append("confidence_haircut_review")
    if any(row.specialist_confidence_score < config.confidence_score_pass_floor for row in rows):
        codes.append("confidence_score_review")
    if any(row.consensus_gap_after_haircuts < config.gap_after_haircuts_pass_floor for row in rows):
        codes.append("gap_after_haircuts_review")
    if any(row.total_cost_haircut >= config.total_cost_haircut_pass_ceiling for row in rows):
        codes.append("total_cost_haircut_review")
    if any(row.consensus_band_width > config.consensus_band_width_pass_ceiling for row in rows):
        codes.append("consensus_band_width_review")
    if "within_consensus_band_block" in row_codes and "gap_after_haircuts_review" not in codes:
        codes.append("gap_after_haircuts_review")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategyConsensusVsMarketGapRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.consensus_gap_after_haircuts,
        -row.total_cost_haircut,
        row.specialist_confidence_score,
        row.consensus_band_width,
        row.candidate_id,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyConsensusVsMarketGapInput],
) -> tuple[ResearchStrategyConsensusVsMarketGapInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_candidate_ids: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyConsensusVsMarketGapInput:
            raise ValueError(
                "inputs must contain ResearchStrategyConsensusVsMarketGapInput values",
            )
        _require_hard_flags("input", value)
        if value.candidate_id in seen_candidate_ids:
            raise ValueError("inputs must not contain duplicate candidate_id values")
        seen_candidate_ids.add(value.candidate_id)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyConsensusVsMarketGapRow],
) -> tuple[ResearchStrategyConsensusVsMarketGapRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_candidate_ids: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyConsensusVsMarketGapRow:
            raise ValueError(
                "rows must contain ResearchStrategyConsensusVsMarketGapRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.candidate_id in seen_candidate_ids:
            raise ValueError("rows must not contain duplicate candidate_id values")
        seen_candidate_ids.add(row.candidate_id)
    return normalized


def _validate_row_consistency(row: ResearchStrategyConsensusVsMarketGapRow) -> None:
    if row.consensus_upper_probability < row.consensus_lower_probability:
        raise ValueError("consensus_upper_probability must match lower probability")
    expected_band_width = _subtract_decimal(
        row.consensus_upper_probability,
        row.consensus_lower_probability,
    )
    if row.consensus_band_width != expected_band_width:
        raise ValueError("consensus_band_width does not match probability band")
    expected_cost = _sum_decimals(
        (
            row.fee_probability_haircut,
            row.spread_probability_haircut,
            row.slippage_probability_haircut,
        ),
    )
    if row.total_cost_haircut != expected_cost:
        raise ValueError("total_cost_haircut does not match cost haircuts")
    (
        expected_market_after_haircuts,
        expected_consensus_gap,
        expected_gap_direction,
    ) = _market_gap_after_haircuts(
        consensus_lower_probability=row.consensus_lower_probability,
        consensus_upper_probability=row.consensus_upper_probability,
        market_probability=row.market_probability,
        total_cost_haircut=row.total_cost_haircut,
        confidence_haircut=row.confidence_probability_haircut,
    )
    if row.market_probability_after_haircuts != expected_market_after_haircuts:
        raise ValueError("market_probability_after_haircuts does not match row inputs")
    if row.consensus_gap_after_haircuts != expected_consensus_gap:
        raise ValueError("consensus_gap_after_haircuts does not match row inputs")
    if row.gap_direction != expected_gap_direction:
        raise ValueError("gap_direction does not match row inputs")
    if row.status == "pass" and row.reason_codes != ("consensus_vs_market_gap_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(report: ResearchStrategyConsensusVsMarketGapReport) -> None:
    if report.source_row_count != _count(len(report.rows)):
        raise ValueError("source_row_count must match rows")
    if report.source_row_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match source_row_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_consensus_gap_after_haircuts != _mean(
        tuple(row.consensus_gap_after_haircuts for row in report.rows),
    ):
        raise ValueError("mean_consensus_gap_after_haircuts must match rows")
    if report.mean_total_cost_haircut != _mean(
        tuple(row.total_cost_haircut for row in report.rows),
    ):
        raise ValueError("mean_total_cost_haircut must match rows")
    if report.mean_confidence_haircut != _mean(
        tuple(row.confidence_probability_haircut for row in report.rows),
    ):
        raise ValueError("mean_confidence_haircut must match rows")
    if report.minimum_specialist_confidence_score != _min_decimal(
        tuple(row.specialist_confidence_score for row in report.rows),
    ):
        raise ValueError("minimum_specialist_confidence_score must match rows")
    if report.widest_consensus_band_width != _max_decimal(
        tuple(row.consensus_band_width for row in report.rows),
    ):
        raise ValueError("widest_consensus_band_width must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(report: ResearchStrategyConsensusVsMarketGapReport) -> None:
    _verify_digest(report)
    _validate_report_consistency(report)
    for row in report.rows:
        _verify_digest(row)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    _verify_public_payload_digest("payload", payload)
    rows = payload.get("rows")
    if rows is None:
        return
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_public_payload_digest(f"payload.rows[{index}]", row)


def _verify_public_payload_digest(label: str, payload: dict[str, Any]) -> None:
    provided = payload.get("derived_validation_digest")
    _require_digest(f"{label}.derived_validation_digest", provided)
    expected = _public_payload_digest(payload)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _status_count(
    rows: tuple[ResearchStrategyConsensusVsMarketGapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyConsensusVsMarketGapRow, ...],
) -> tuple[ResearchStrategyConsensusVsMarketGapReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyConsensusVsMarketGapReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            input_ratio=_divide_decimal(_count(count), denominator),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_reason_code_counts(
    value: Iterable[ResearchStrategyConsensusVsMarketGapReasonCodeCount],
) -> tuple[ResearchStrategyConsensusVsMarketGapReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategyConsensusVsMarketGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyConsensusVsMarketGapReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return min(values).quantize(RATIO_QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return max(values).quantize(RATIO_QUANTUM)


def _max_decimal_value(left: Decimal, right: Decimal) -> Decimal:
    return max(left, right).quantize(RATIO_QUANTUM)


def _min_probability(value: Decimal) -> Decimal:
    return min(value, ONE).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_floor_pair(name: str, pass_floor: Decimal, watch_floor: Decimal) -> None:
    if pass_floor < watch_floor:
        raise ValueError(f"{name}_pass_floor must be at least {name}_watch_floor")


def _require_ceiling_pair(
    name: str,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> None:
    if watch_ceiling < pass_ceiling:
        raise ValueError(f"{name}_watch_ceiling must be at least {name}_pass_ceiling")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_STRATEGY_CONSENSUS_VS_MARKET_GAP_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_gap_direction(name: str, value: object) -> None:
    if type(value) is not str or value not in GAP_DIRECTIONS:
        raise ValueError(f"{name} must be a supported gap direction")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    _require_public_string(name, value)
    if value not in ROW_REASON_CODES and value not in REPORT_REASON_CODES:
        raise ValueError(f"{name} is not supported")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for reason_code in value:
        _require_reason_code(name, reason_code)
        if reason_code not in supported:
            raise ValueError(f"{name} contains an unsupported reason code")
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must not contain duplicates")
    return value


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical public string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} has unsafe public text")


def _require_raw_identifier(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical string")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _apply_or_verify_digest(value: object) -> None:
    provided = getattr(value, "derived_validation_digest")
    if provided:
        _verify_digest(value)
    else:
        object.__setattr__(value, "derived_validation_digest", _digest_for(value))


def _verify_digest(value: object) -> None:
    provided = getattr(value, "derived_validation_digest")
    _require_digest("derived_validation_digest", provided)
    if provided != _digest_for(value):
        raise ValueError("derived_validation_digest does not match payload")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _digest_for(value: object) -> str:
    payload = asdict(value)
    payload.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value.quantize(RATIO_QUANTUM))
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        return value
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal-derived strings")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if any(fragment in key.lower() for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and any(
        fragment in value.lower() for fragment in _UNSAFE_PUBLIC_FRAGMENTS
    ):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CONSENSUS_VS_MARKET_GAP_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_CONSENSUS_VS_MARKET_GAP_STATUSES",
    "ResearchStrategyConsensusVsMarketGapConfig",
    "ResearchStrategyConsensusVsMarketGapInput",
    "ResearchStrategyConsensusVsMarketGapReasonCodeCount",
    "ResearchStrategyConsensusVsMarketGapRow",
    "ResearchStrategyConsensusVsMarketGapReport",
    "build_research_strategy_consensus_vs_market_gap_report",
    "research_strategy_consensus_vs_market_gap_report_payload",
)
