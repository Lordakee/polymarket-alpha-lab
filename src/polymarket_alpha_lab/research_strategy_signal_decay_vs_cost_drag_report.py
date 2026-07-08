"""Pure report-only signal decay versus cost drag report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_SIGNAL_DECAY_VS_COST_DRAG_REPORT_CONFIG_VERSION = (
    "research-strategy-signal-decay-vs-cost-drag-report-v0"
)
RESEARCH_STRATEGY_SIGNAL_DECAY_VS_COST_DRAG_STATUSES = (
    "pass",
    "watch",
    "block",
)

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
SECONDS_PER_HOUR = Decimal("3600")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_" + "id",
    "market_" + "id",
    "market_" + "slug",
    "candidate_ref",
    "market_ref",
    "ques" + "tion",
    "u" + "rl",
    "te" + "xt",
    "d" + "sn",
    "tab" + "le",
    "tok" + "en",
    "wal" + "let",
    "or" + "der",
    "trad" + "e",
    "li" + "ve",
    "pos" + "ition",
    "siz" + "ing",
    "private",
    "secret",
    "credential",
)

ROW_REASON_CODES = (
    "signal_decay_vs_cost_drag_pass",
    "evidence_age_block",
    "evidence_age_watch",
    "source_authority_block",
    "source_authority_watch",
    "market_movement_block",
    "market_movement_watch",
    "cost_drag_block",
    "cost_drag_watch",
    "liquidity_depth_block",
    "liquidity_depth_watch",
    "resolution_ambiguity_block",
    "resolution_ambiguity_watch",
)
REPORT_REASON_CODES = (
    "signal_decay_vs_cost_drag_report_block",
    "signal_decay_vs_cost_drag_report_empty",
    "signal_decay_vs_cost_drag_report_pass",
    "signal_decay_vs_cost_drag_report_watch",
    "evidence_age_review",
    "source_authority_review",
    "market_movement_review",
    "cost_drag_review",
    "liquidity_depth_review",
    "resolution_ambiguity_review",
)


@dataclass(frozen=True)
class ResearchStrategySignalDecayVsCostDragConfig:
    config_version: str
    evidence_age_hours_pass_ceiling: Decimal
    evidence_age_hours_watch_ceiling: Decimal
    source_authority_pass_floor: Decimal
    source_authority_watch_floor: Decimal
    market_movement_pass_ceiling: Decimal
    market_movement_watch_ceiling: Decimal
    cost_drag_pass_ceiling: Decimal
    cost_drag_watch_ceiling: Decimal
    liquidity_depth_pass_floor: Decimal
    liquidity_depth_watch_floor: Decimal
    resolution_ambiguity_pass_ceiling: Decimal
    resolution_ambiguity_watch_ceiling: Decimal
    age_decay_weight: Decimal
    authority_decay_weight: Decimal
    movement_decay_weight: Decimal
    spread_cost_weight: Decimal
    fee_cost_weight: Decimal
    slippage_cost_weight: Decimal
    liquidity_cost_weight: Decimal
    resolution_drag_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "evidence_age_hours_pass_ceiling",
            "evidence_age_hours_watch_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_authority_pass_floor",
            "source_authority_watch_floor",
            "market_movement_pass_ceiling",
            "market_movement_watch_ceiling",
            "cost_drag_pass_ceiling",
            "cost_drag_watch_ceiling",
            "liquidity_depth_pass_floor",
            "liquidity_depth_watch_floor",
            "resolution_ambiguity_pass_ceiling",
            "resolution_ambiguity_watch_ceiling",
            "age_decay_weight",
            "authority_decay_weight",
            "movement_decay_weight",
            "spread_cost_weight",
            "fee_cost_weight",
            "slippage_cost_weight",
            "liquidity_cost_weight",
            "resolution_drag_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_ceiling_pair(
            "evidence_age_hours",
            self.evidence_age_hours_pass_ceiling,
            self.evidence_age_hours_watch_ceiling,
        )
        _require_floor_pair(
            "source_authority",
            self.source_authority_pass_floor,
            self.source_authority_watch_floor,
        )
        _require_ceiling_pair(
            "market_movement",
            self.market_movement_pass_ceiling,
            self.market_movement_watch_ceiling,
        )
        _require_ceiling_pair(
            "cost_drag",
            self.cost_drag_pass_ceiling,
            self.cost_drag_watch_ceiling,
        )
        _require_floor_pair(
            "liquidity_depth",
            self.liquidity_depth_pass_floor,
            self.liquidity_depth_watch_floor,
        )
        _require_ceiling_pair(
            "resolution_ambiguity",
            self.resolution_ambiguity_pass_ceiling,
            self.resolution_ambiguity_watch_ceiling,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategySignalDecayVsCostDragInput:
    candidate_ref: str
    market_ref: str
    evidence_observed_at: datetime
    source_authority_score: Decimal
    market_probability_at_evidence: Decimal
    current_market_probability: Decimal
    spread_probability_cost: Decimal
    fee_probability_cost: Decimal
    slippage_probability_cost: Decimal
    liquidity_depth_score: Decimal
    resolution_ambiguity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_ref", "market_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        for field_name in (
            "source_authority_score",
            "market_probability_at_evidence",
            "current_market_probability",
            "spread_probability_cost",
            "fee_probability_cost",
            "slippage_probability_cost",
            "liquidity_depth_score",
            "resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategySignalDecayVsCostDragReasonCodeCount:
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
class ResearchStrategySignalDecayVsCostDragRow:
    candidate_ref: str
    market_ref: str
    evidence_observed_at: datetime
    evidence_age_hours: Decimal
    source_authority_score: Decimal
    market_probability_at_evidence: Decimal
    current_market_probability: Decimal
    market_movement_probability: Decimal
    spread_probability_cost: Decimal
    fee_probability_cost: Decimal
    slippage_probability_cost: Decimal
    direct_cost_drag_probability: Decimal
    liquidity_depth_score: Decimal
    resolution_ambiguity_score: Decimal
    signal_decay_score: Decimal
    cost_drag_score: Decimal
    decay_cost_gap: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_ref", "market_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        for field_name in (
            "evidence_age_hours",
            "decay_cost_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        if self.evidence_age_hours < ZERO:
            raise ValueError("evidence_age_hours must be nonnegative")
        for field_name in (
            "source_authority_score",
            "market_probability_at_evidence",
            "current_market_probability",
            "market_movement_probability",
            "spread_probability_cost",
            "fee_probability_cost",
            "slippage_probability_cost",
            "direct_cost_drag_probability",
            "liquidity_depth_score",
            "resolution_ambiguity_score",
            "signal_decay_score",
            "cost_drag_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategySignalDecayVsCostDragReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_signal_decay_score: Decimal
    mean_cost_drag_score: Decimal
    mean_decay_cost_gap: Decimal
    mean_evidence_age_hours: Decimal
    mean_market_movement_probability: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategySignalDecayVsCostDragReasonCodeCount, ...]
    rows: tuple[ResearchStrategySignalDecayVsCostDragRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_signal_decay_score",
            "mean_cost_drag_score",
            "mean_evidence_age_hours",
            "mean_market_movement_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_decay_cost_gap",
            _normalize_decimal("mean_decay_cost_gap", self.mean_decay_cost_gap),
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


def build_research_strategy_signal_decay_vs_cost_drag_report(
    inputs: Iterable[ResearchStrategySignalDecayVsCostDragInput],
    *,
    config: ResearchStrategySignalDecayVsCostDragConfig,
    generated_at: datetime,
) -> ResearchStrategySignalDecayVsCostDragReport:
    if type(config) is not ResearchStrategySignalDecayVsCostDragConfig:
        raise ValueError("config must be a ResearchStrategySignalDecayVsCostDragConfig")
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
    return ResearchStrategySignalDecayVsCostDragReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_signal_decay_score=_mean(tuple(row.signal_decay_score for row in rows)),
        mean_cost_drag_score=_mean(tuple(row.cost_drag_score for row in rows)),
        mean_decay_cost_gap=_mean(tuple(row.decay_cost_gap for row in rows)),
        mean_evidence_age_hours=_mean(tuple(row.evidence_age_hours for row in rows)),
        mean_market_movement_probability=_mean(
            tuple(row.market_movement_probability for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_signal_decay_vs_cost_drag_report_payload(
    report: ResearchStrategySignalDecayVsCostDragReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategySignalDecayVsCostDragReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _public_report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategySignalDecayVsCostDragReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _public_report_payload(
    report: ResearchStrategySignalDecayVsCostDragReport,
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
    row: ResearchStrategySignalDecayVsCostDragRow,
) -> dict[str, Any]:
    payload = asdict(row)
    for field_name in ("candidate_ref", "market_ref"):
        payload.pop(field_name, None)
    payload.pop("derived_validation_digest", None)
    payload["row_number"] = _count(row_number)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    return public_payload


def _row_from_input(
    value: ResearchStrategySignalDecayVsCostDragInput,
    *,
    config: ResearchStrategySignalDecayVsCostDragConfig,
    generated_at: datetime,
) -> ResearchStrategySignalDecayVsCostDragRow:
    observed_at = _as_utc("evidence_observed_at", value.evidence_observed_at)
    if observed_at > generated_at:
        raise ValueError("evidence_observed_at must not be after generated_at")
    evidence_age_hours = _age_hours(observed_at, generated_at)
    market_movement_probability = _abs_decimal(
        _subtract_decimal(value.current_market_probability, value.market_probability_at_evidence),
    )
    direct_cost_drag_probability = _sum_decimals(
        (
            value.spread_probability_cost,
            value.fee_probability_cost,
            value.slippage_probability_cost,
        ),
    )
    signal_decay_score = _signal_decay_score(
        value=value,
        evidence_age_hours=evidence_age_hours,
        market_movement_probability=market_movement_probability,
        config=config,
    )
    cost_drag_score = _cost_drag_score(
        value=value,
        config=config,
    )
    decay_cost_gap = _subtract_decimal(signal_decay_score, cost_drag_score)
    return ResearchStrategySignalDecayVsCostDragRow(
        candidate_ref=value.candidate_ref,
        market_ref=value.market_ref,
        evidence_observed_at=observed_at,
        evidence_age_hours=evidence_age_hours,
        source_authority_score=value.source_authority_score,
        market_probability_at_evidence=value.market_probability_at_evidence,
        current_market_probability=value.current_market_probability,
        market_movement_probability=market_movement_probability,
        spread_probability_cost=value.spread_probability_cost,
        fee_probability_cost=value.fee_probability_cost,
        slippage_probability_cost=value.slippage_probability_cost,
        direct_cost_drag_probability=direct_cost_drag_probability,
        liquidity_depth_score=value.liquidity_depth_score,
        resolution_ambiguity_score=value.resolution_ambiguity_score,
        signal_decay_score=signal_decay_score,
        cost_drag_score=cost_drag_score,
        decay_cost_gap=decay_cost_gap,
        status=_row_status(
            value=value,
            evidence_age_hours=evidence_age_hours,
            market_movement_probability=market_movement_probability,
            direct_cost_drag_probability=direct_cost_drag_probability,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            value=value,
            evidence_age_hours=evidence_age_hours,
            market_movement_probability=market_movement_probability,
            direct_cost_drag_probability=direct_cost_drag_probability,
            config=config,
        ),
    )


def _signal_decay_score(
    *,
    value: ResearchStrategySignalDecayVsCostDragInput,
    evidence_age_hours: Decimal,
    market_movement_probability: Decimal,
    config: ResearchStrategySignalDecayVsCostDragConfig,
) -> Decimal:
    age_decay = _multiply_decimal(
        _clamp_probability(
            _divide_decimal(
                evidence_age_hours,
                config.evidence_age_hours_watch_ceiling,
            ),
        ),
        config.age_decay_weight,
    )
    authority_decay = _multiply_decimal(
        _subtract_decimal(ONE, value.source_authority_score),
        config.authority_decay_weight,
    )
    movement_decay = _multiply_decimal(
        _clamp_probability(
            _divide_decimal(market_movement_probability, config.market_movement_watch_ceiling),
        ),
        config.movement_decay_weight,
    )
    return _clamp_probability(_sum_decimals((age_decay, authority_decay, movement_decay)))


def _cost_drag_score(
    *,
    value: ResearchStrategySignalDecayVsCostDragInput,
    config: ResearchStrategySignalDecayVsCostDragConfig,
) -> Decimal:
    weighted_direct_cost = _sum_decimals(
        (
            _multiply_decimal(value.spread_probability_cost, config.spread_cost_weight),
            _multiply_decimal(value.fee_probability_cost, config.fee_cost_weight),
            _multiply_decimal(
                value.slippage_probability_cost,
                config.slippage_cost_weight,
            ),
        ),
    )
    liquidity_drag = _multiply_decimal(
        _subtract_decimal(ONE, value.liquidity_depth_score),
        config.liquidity_cost_weight,
    )
    resolution_drag = _multiply_decimal(
        value.resolution_ambiguity_score,
        config.resolution_drag_weight,
    )
    return _clamp_probability(
        _sum_decimals((weighted_direct_cost, liquidity_drag, resolution_drag)),
    )


def _row_status(
    *,
    value: ResearchStrategySignalDecayVsCostDragInput,
    evidence_age_hours: Decimal,
    market_movement_probability: Decimal,
    direct_cost_drag_probability: Decimal,
    config: ResearchStrategySignalDecayVsCostDragConfig,
) -> str:
    if (
        evidence_age_hours > config.evidence_age_hours_watch_ceiling
        or value.source_authority_score < config.source_authority_watch_floor
        or market_movement_probability > config.market_movement_watch_ceiling
        or direct_cost_drag_probability > config.cost_drag_watch_ceiling
        or value.liquidity_depth_score < config.liquidity_depth_watch_floor
        or value.resolution_ambiguity_score > config.resolution_ambiguity_watch_ceiling
    ):
        return "block"
    if (
        evidence_age_hours > config.evidence_age_hours_pass_ceiling
        or value.source_authority_score < config.source_authority_pass_floor
        or market_movement_probability > config.market_movement_pass_ceiling
        or direct_cost_drag_probability > config.cost_drag_pass_ceiling
        or value.liquidity_depth_score < config.liquidity_depth_pass_floor
        or value.resolution_ambiguity_score > config.resolution_ambiguity_pass_ceiling
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    value: ResearchStrategySignalDecayVsCostDragInput,
    evidence_age_hours: Decimal,
    market_movement_probability: Decimal,
    direct_cost_drag_probability: Decimal,
    config: ResearchStrategySignalDecayVsCostDragConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if evidence_age_hours > config.evidence_age_hours_watch_ceiling:
        codes.append("evidence_age_block")
    elif evidence_age_hours > config.evidence_age_hours_pass_ceiling:
        codes.append("evidence_age_watch")
    if value.source_authority_score < config.source_authority_watch_floor:
        codes.append("source_authority_block")
    elif value.source_authority_score < config.source_authority_pass_floor:
        codes.append("source_authority_watch")
    if market_movement_probability > config.market_movement_watch_ceiling:
        codes.append("market_movement_block")
    elif market_movement_probability > config.market_movement_pass_ceiling:
        codes.append("market_movement_watch")
    if direct_cost_drag_probability > config.cost_drag_watch_ceiling:
        codes.append("cost_drag_block")
    elif direct_cost_drag_probability > config.cost_drag_pass_ceiling:
        codes.append("cost_drag_watch")
    if value.liquidity_depth_score < config.liquidity_depth_watch_floor:
        codes.append("liquidity_depth_block")
    elif value.liquidity_depth_score < config.liquidity_depth_pass_floor:
        codes.append("liquidity_depth_watch")
    if value.resolution_ambiguity_score > config.resolution_ambiguity_watch_ceiling:
        codes.append("resolution_ambiguity_block")
    elif value.resolution_ambiguity_score > config.resolution_ambiguity_pass_ceiling:
        codes.append("resolution_ambiguity_watch")
    if not codes:
        codes.append("signal_decay_vs_cost_drag_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(rows: tuple[ResearchStrategySignalDecayVsCostDragRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategySignalDecayVsCostDragRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("signal_decay_vs_cost_drag_report_empty",)
    report_status = _report_status(rows)
    codes = [f"signal_decay_vs_cost_drag_report_{report_status}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    if any(code.startswith("evidence_age_") for code in row_codes):
        codes.append("evidence_age_review")
    if any(code.startswith("source_authority_") for code in row_codes):
        codes.append("source_authority_review")
    if any(code.startswith("market_movement_") for code in row_codes):
        codes.append("market_movement_review")
    if any(code.startswith("cost_drag_") for code in row_codes):
        codes.append("cost_drag_review")
    if any(code.startswith("liquidity_depth_") for code in row_codes):
        codes.append("liquidity_depth_review")
    if any(code.startswith("resolution_ambiguity_") for code in row_codes):
        codes.append("resolution_ambiguity_review")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategySignalDecayVsCostDragRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.decay_cost_gap,
        -row.signal_decay_score,
        -row.cost_drag_score,
        -row.market_movement_probability,
        row.candidate_ref,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategySignalDecayVsCostDragInput],
) -> tuple[ResearchStrategySignalDecayVsCostDragInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategySignalDecayVsCostDragInput:
            raise ValueError(
                "inputs must contain ResearchStrategySignalDecayVsCostDragInput values",
            )
        _require_hard_flags("input", value)
        if value.candidate_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate candidate_ref values")
        seen_refs.add(value.candidate_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategySignalDecayVsCostDragRow],
) -> tuple[ResearchStrategySignalDecayVsCostDragRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategySignalDecayVsCostDragRow:
            raise ValueError(
                "rows must contain ResearchStrategySignalDecayVsCostDragRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.candidate_ref in seen_refs:
            raise ValueError("rows must not contain duplicate candidate_ref values")
        seen_refs.add(row.candidate_ref)
    return normalized


def _validate_row_consistency(row: ResearchStrategySignalDecayVsCostDragRow) -> None:
    expected_direct_cost = _sum_decimals(
        (
            row.spread_probability_cost,
            row.fee_probability_cost,
            row.slippage_probability_cost,
        ),
    )
    if row.direct_cost_drag_probability != expected_direct_cost:
        raise ValueError("direct_cost_drag_probability does not match cost inputs")
    expected_movement = _abs_decimal(
        _subtract_decimal(row.current_market_probability, row.market_probability_at_evidence),
    )
    if row.market_movement_probability != expected_movement:
        raise ValueError("market_movement_probability does not match row inputs")
    expected_gap = _subtract_decimal(row.signal_decay_score, row.cost_drag_score)
    if row.decay_cost_gap != expected_gap:
        raise ValueError("decay_cost_gap does not match row inputs")
    if row.status == "pass" and row.reason_codes != ("signal_decay_vs_cost_drag_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(report: ResearchStrategySignalDecayVsCostDragReport) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.input_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match input_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_signal_decay_score != _mean(tuple(row.signal_decay_score for row in report.rows)):
        raise ValueError("mean_signal_decay_score must match rows")
    if report.mean_cost_drag_score != _mean(tuple(row.cost_drag_score for row in report.rows)):
        raise ValueError("mean_cost_drag_score must match rows")
    if report.mean_decay_cost_gap != _mean(tuple(row.decay_cost_gap for row in report.rows)):
        raise ValueError("mean_decay_cost_gap must match rows")
    if report.mean_evidence_age_hours != _mean(tuple(row.evidence_age_hours for row in report.rows)):
        raise ValueError("mean_evidence_age_hours must match rows")
    if report.mean_market_movement_probability != _mean(
        tuple(row.market_movement_probability for row in report.rows),
    ):
        raise ValueError("mean_market_movement_probability must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(report: ResearchStrategySignalDecayVsCostDragReport) -> None:
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


def _status_count(
    rows: tuple[ResearchStrategySignalDecayVsCostDragRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategySignalDecayVsCostDragRow, ...],
) -> tuple[ResearchStrategySignalDecayVsCostDragReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategySignalDecayVsCostDragReasonCodeCount(
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
    value: Iterable[ResearchStrategySignalDecayVsCostDragReasonCodeCount],
) -> tuple[ResearchStrategySignalDecayVsCostDragReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategySignalDecayVsCostDragReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategySignalDecayVsCostDragReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _age_hours(started_at: datetime, finished_at: datetime) -> Decimal:
    delta = finished_at - started_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = _divide_decimal(Decimal(delta.microseconds), Decimal("1000000"))
    return _divide_decimal(_sum_decimals((seconds, microseconds)), SECONDS_PER_HOUR)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _subtract_decimal(ZERO, value)
    return _quantize(value)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    if value > ONE:
        return ONE.quantize(RATIO_QUANTUM)
    return _quantize(value)


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


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
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
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_SIGNAL_DECAY_VS_COST_DRAG_STATUSES
    ):
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    _require_canonical_public_string(name, value)
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


def _require_canonical_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical public string")


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


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SIGNAL_DECAY_VS_COST_DRAG_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_SIGNAL_DECAY_VS_COST_DRAG_STATUSES",
    "ResearchStrategySignalDecayVsCostDragConfig",
    "ResearchStrategySignalDecayVsCostDragInput",
    "ResearchStrategySignalDecayVsCostDragReasonCodeCount",
    "ResearchStrategySignalDecayVsCostDragRow",
    "ResearchStrategySignalDecayVsCostDragReport",
    "build_research_strategy_signal_decay_vs_cost_drag_report",
    "research_strategy_signal_decay_vs_cost_drag_report_payload",
)
