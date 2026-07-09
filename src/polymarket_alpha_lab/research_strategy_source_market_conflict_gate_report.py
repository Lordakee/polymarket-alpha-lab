"""Pure report-only source-vs-market conflict gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_SOURCE_MARKET_CONFLICT_GATE_REPORT_CONFIG_VERSION = (
    "research-strategy-source-market-conflict-gate-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_AUTH_PUBLIC_TERM_RE = re.compile(r"(?:^|[^a-z0-9])auth(?:[^a-z0-9]|$)")
_GATE_STATUSES = frozenset(("pass", "watch", "block"))
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_DERIVED_DIGEST_FIELD = "derived_validation_digest"
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_REASON_CODE_SEQUENCE = (
    "probability_gap_watch",
    "probability_gap_block",
    "conflict_score_watch",
    "conflict_score_block",
    "evidence_freshness_block",
    "market_move_watch",
    "market_move_block",
    "liquidity_quality_watch",
    "cost_drag_watch",
    "cost_drag_block",
    "specialist_memory_confidence_watch",
    "source_market_conflict_pass",
    "source_market_conflict_empty",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_TERMS = (
    "://",
    "?",
    "@",
    "=",
    "api" "_" "key",
    _join_parts("auth", "key"),
    _join_parts("auth", "token"),
    _join_parts("author", "ization"),
    "credential",
    _join_parts("bro", "ker"),
    _join_parts("can", "cel"),
    _join_parts("candidate", "_", "id"),
    _join_parts("d", "s", "n"),
    _join_parts("data", "base", "_", "url"),
    _join_parts("li", "ve"),
    _join_parts("mar", "ket", "_", "id"),
    _join_parts("mar", "ket", "_", "slug"),
    _join_parts("or", "der"),
    _join_parts("private", "_", "key"),
    _join_parts("que", "stion"),
    _join_parts("raw", "_", "candidate"),
    _join_parts("raw", "_", "mar", "ket"),
    _join_parts("raw", "_", "source"),
    _join_parts("re", "commend"),
    _join_parts("secret"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "url"),
    _join_parts("sub", "mit"),
    _join_parts("table", "_", "name"),
    _join_parts("tok", "en"),
    _join_parts("tra", "de"),
    _join_parts("wal", "let"),
    _join_parts("execut"),
)


@dataclass(frozen=True)
class ResearchStrategySourceMarketConflictGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_SOURCE_MARKET_CONFLICT_GATE_REPORT_CONFIG_VERSION
    )
    watch_conflict_score: Decimal = Decimal("0.350000")
    block_conflict_score: Decimal = Decimal("0.650000")
    watch_probability_gap: Decimal = Decimal("0.120000")
    block_probability_gap: Decimal = Decimal("0.250000")
    max_evidence_age_seconds: Decimal = Decimal("7200.000000")
    market_move_watch_threshold: Decimal = Decimal("0.250000")
    market_move_block_threshold: Decimal = Decimal("0.550000")
    liquidity_quality_floor: Decimal = Decimal("0.400000")
    cost_drag_watch_threshold: Decimal = Decimal("0.120000")
    cost_drag_block_threshold: Decimal = Decimal("0.250000")
    memory_confidence_floor: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceMarketConflictGateConfig:
            raise TypeError(
                "ResearchStrategySourceMarketConflictGateConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySourceMarketConflictGateConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchStrategySourceMarketConflictGateConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_MARKET_CONFLICT_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _require_positive_decimal(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        for field_name in (
            "watch_conflict_score",
            "block_conflict_score",
            "watch_probability_gap",
            "block_probability_gap",
            "market_move_watch_threshold",
            "market_move_block_threshold",
            "liquidity_quality_floor",
            "cost_drag_watch_threshold",
            "cost_drag_block_threshold",
            "memory_confidence_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_conflict_score <= self.watch_conflict_score:
            raise ValueError("block_conflict_score must exceed watch_conflict_score")
        if self.block_probability_gap <= self.watch_probability_gap:
            raise ValueError("block_probability_gap must exceed watch_probability_gap")
        if self.market_move_block_threshold <= self.market_move_watch_threshold:
            raise ValueError(
                "market_move_block_threshold must exceed "
                "market_move_watch_threshold",
            )
        if self.cost_drag_block_threshold <= self.cost_drag_watch_threshold:
            raise ValueError(
                "cost_drag_block_threshold must exceed cost_drag_watch_threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategySourceMarketConflictGateInputRow:
    review_label: str
    source_probability: Decimal
    market_implied_probability: Decimal
    evidence_authority_score: Decimal
    evidence_freshness_score: Decimal
    market_move_score: Decimal
    liquidity_quality_score: Decimal
    cost_drag_score: Decimal
    specialist_memory_confidence: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceMarketConflictGateInputRow:
            raise TypeError(
                "ResearchStrategySourceMarketConflictGateInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySourceMarketConflictGateInputRow:
            raise ValueError(
                "input row must be exactly "
                "ResearchStrategySourceMarketConflictGateInputRow",
            )
        _require_public_identifier("review_label", self.review_label)
        for field_name in (
            "source_probability",
            "market_implied_probability",
            "evidence_authority_score",
            "evidence_freshness_score",
            "market_move_score",
            "liquidity_quality_score",
            "cost_drag_score",
            "specialist_memory_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input row", self)
        _reject_unsafe_public_payload("input row", self)


@dataclass(frozen=True)
class ResearchStrategySourceMarketConflictPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceMarketConflictPublicPayloadItem:
            raise TypeError(
                "ResearchStrategySourceMarketConflictPublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySourceMarketConflictPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchStrategySourceMarketConflictPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchStrategySourceMarketConflictGateRow:
    review_label: str
    observed_at: datetime
    source_probability: Decimal
    market_implied_probability: Decimal
    probability_gap: Decimal
    evidence_authority_score: Decimal
    evidence_freshness_score: Decimal
    market_move_score: Decimal
    liquidity_quality_score: Decimal
    cost_drag_score: Decimal
    specialist_memory_confidence: Decimal
    conflict_score: Decimal
    manual_review_required: bool
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceMarketConflictGateRow:
            raise TypeError(
                "ResearchStrategySourceMarketConflictGateRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySourceMarketConflictGateRow:
            raise ValueError("row must be exactly ResearchStrategySourceMarketConflictGateRow")
        _require_public_identifier("review_label", self.review_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_probability",
            "market_implied_probability",
            "probability_gap",
            "evidence_authority_score",
            "evidence_freshness_score",
            "market_move_score",
            "liquidity_quality_score",
            "cost_drag_score",
            "specialist_memory_confidence",
            "conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.manual_review_required) is not bool:
            raise ValueError("manual_review_required must be a bool")
        _require_gate_status("gate_status", self.gate_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategySourceMarketConflictGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_probability_gap: Decimal
    max_probability_gap: Decimal
    average_conflict_score: Decimal
    max_conflict_score: Decimal
    average_cost_drag_score: Decimal
    max_cost_drag_score: Decimal
    rows: tuple[ResearchStrategySourceMarketConflictGateRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchStrategySourceMarketConflictPublicPayloadItem, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceMarketConflictGateReport:
            raise TypeError(
                "ResearchStrategySourceMarketConflictGateReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategySourceMarketConflictGateReport:
            raise ValueError(
                "report must be exactly "
                "ResearchStrategySourceMarketConflictGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_MARKET_CONFLICT_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_gate_status("gate_status", self.gate_status)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_probability_gap",
            "max_probability_gap",
            "average_conflict_score",
            "max_conflict_score",
            "average_cost_drag_score",
            "max_cost_drag_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _report_derived_validation_digest(self):
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_source_market_conflict_gate_report_payload(self)


def build_research_strategy_source_market_conflict_gate_report(
    rows: Sequence[ResearchStrategySourceMarketConflictGateInputRow],
    *,
    generated_at: datetime,
    config: ResearchStrategySourceMarketConflictGateConfig
    | None = None,
    public_payload: Sequence[ResearchStrategySourceMarketConflictPublicPayloadItem] = (),
) -> ResearchStrategySourceMarketConflictGateReport:
    cfg = config or ResearchStrategySourceMarketConflictGateConfig()
    if type(cfg) is not ResearchStrategySourceMarketConflictGateConfig:
        raise ValueError(
            "config must be exactly ResearchStrategySourceMarketConflictGateConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = tuple(rows)
    seen_labels: set[str] = set()
    output_rows: list[ResearchStrategySourceMarketConflictGateRow] = []
    for input_row in input_rows:
        if type(input_row) is not ResearchStrategySourceMarketConflictGateInputRow:
            raise ValueError(
                "rows must contain exactly "
                "ResearchStrategySourceMarketConflictGateInputRow values",
            )
        if input_row.review_label in seen_labels:
            raise ValueError("review_label values must be duplicate-free")
        seen_labels.add(input_row.review_label)
        if input_row.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be in the future")
        output_rows.append(_row_from_input(input_row, generated_at_utc, cfg))
    normalized_rows = tuple(sorted(output_rows, key=_row_sort_key))
    reason_codes = _aggregate_reason_codes(normalized_rows)
    if not normalized_rows:
        reason_codes = ("source_market_conflict_empty",)
    return ResearchStrategySourceMarketConflictGateReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        gate_status=_report_status(normalized_rows),
        input_count=_count_decimal(len(normalized_rows)),
        pass_count=_count_decimal(
            sum(1 for row in normalized_rows if row.gate_status == "pass"),
        ),
        watch_count=_count_decimal(
            sum(1 for row in normalized_rows if row.gate_status == "watch"),
        ),
        block_count=_count_decimal(
            sum(1 for row in normalized_rows if row.gate_status == "block"),
        ),
        average_probability_gap=_average(row.probability_gap for row in normalized_rows),
        max_probability_gap=_max_or_zero(row.probability_gap for row in normalized_rows),
        average_conflict_score=_average(row.conflict_score for row in normalized_rows),
        max_conflict_score=_max_or_zero(row.conflict_score for row in normalized_rows),
        average_cost_drag_score=_average(row.cost_drag_score for row in normalized_rows),
        max_cost_drag_score=_max_or_zero(row.cost_drag_score for row in normalized_rows),
        rows=normalized_rows,
        reason_codes=reason_codes,
        public_payload=tuple(public_payload),
    )


def research_strategy_source_market_conflict_gate_report_payload(
    report: ResearchStrategySourceMarketConflictGateReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategySourceMarketConflictGateReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_payload_values("payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_payload_values("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _MappingFlags(payload))
        return payload
    raise ValueError(
        "report must be a ResearchStrategySourceMarketConflictGateReport",
    )


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, Any]

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
    input_row: ResearchStrategySourceMarketConflictGateInputRow,
    generated_at: datetime,
    config: ResearchStrategySourceMarketConflictGateConfig,
) -> ResearchStrategySourceMarketConflictGateRow:
    probability_gap = _quantize(abs(input_row.source_probability - input_row.market_implied_probability))
    conflict_score = _conflict_score(input_row, probability_gap)
    reason_codes = _row_reason_codes(input_row, probability_gap, conflict_score, generated_at, config)
    gate_status = _gate_status(reason_codes, conflict_score, config)
    if gate_status == "pass":
        reason_codes = ("source_market_conflict_pass",)
    return ResearchStrategySourceMarketConflictGateRow(
        review_label=input_row.review_label,
        observed_at=input_row.observed_at,
        source_probability=input_row.source_probability,
        market_implied_probability=input_row.market_implied_probability,
        probability_gap=probability_gap,
        evidence_authority_score=input_row.evidence_authority_score,
        evidence_freshness_score=input_row.evidence_freshness_score,
        market_move_score=input_row.market_move_score,
        liquidity_quality_score=input_row.liquidity_quality_score,
        cost_drag_score=input_row.cost_drag_score,
        specialist_memory_confidence=input_row.specialist_memory_confidence,
        conflict_score=conflict_score,
        manual_review_required=gate_status != "pass",
        gate_status=gate_status,
        reason_codes=reason_codes,
    )


def _conflict_score(
    input_row: ResearchStrategySourceMarketConflictGateInputRow,
    probability_gap: Decimal,
) -> Decimal:
    evidence_strength = _quantize(
        (
            input_row.evidence_authority_score
            + input_row.evidence_freshness_score
            + input_row.specialist_memory_confidence
        )
        / Decimal("3"),
    )
    probability_pressure = probability_gap * evidence_strength
    market_pressure = (
        input_row.market_move_score
        * input_row.liquidity_quality_score
        * Decimal("0.400000")
    )
    friction_pressure = (
        max(input_row.cost_drag_score, _ONE - input_row.liquidity_quality_score)
        * Decimal("0.200000")
    )
    return _normalize_ratio(
        probability_pressure + market_pressure + friction_pressure,
    )


def _row_reason_codes(
    input_row: ResearchStrategySourceMarketConflictGateInputRow,
    probability_gap: Decimal,
    conflict_score: Decimal,
    generated_at: datetime,
    config: ResearchStrategySourceMarketConflictGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if probability_gap >= config.block_probability_gap:
        reason_codes.append("probability_gap_block")
    elif probability_gap >= config.watch_probability_gap:
        reason_codes.append("probability_gap_watch")
    if conflict_score >= config.block_conflict_score:
        reason_codes.append("conflict_score_block")
    elif conflict_score >= config.watch_conflict_score:
        reason_codes.append("conflict_score_watch")
    if _seconds_between(input_row.observed_at, generated_at) > config.max_evidence_age_seconds:
        reason_codes.append("evidence_freshness_block")
    if input_row.market_move_score >= config.market_move_block_threshold:
        reason_codes.append("market_move_block")
    elif input_row.market_move_score >= config.market_move_watch_threshold:
        reason_codes.append("market_move_watch")
    if input_row.liquidity_quality_score < config.liquidity_quality_floor:
        reason_codes.append("liquidity_quality_watch")
    if input_row.cost_drag_score >= config.cost_drag_block_threshold:
        reason_codes.append("cost_drag_block")
    elif input_row.cost_drag_score >= config.cost_drag_watch_threshold:
        reason_codes.append("cost_drag_watch")
    if input_row.specialist_memory_confidence < config.memory_confidence_floor:
        reason_codes.append("specialist_memory_confidence_watch")
    return _normalize_reason_codes(tuple(reason_codes))


def _gate_status(
    reason_codes: tuple[str, ...],
    conflict_score: Decimal,
    config: ResearchStrategySourceMarketConflictGateConfig,
) -> str:
    if conflict_score >= config.block_conflict_score or any(code.endswith("_block") for code in reason_codes):
        return "block"
    if conflict_score >= config.watch_conflict_score or reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchStrategySourceMarketConflictGateRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.gate_status == "block" for row in rows):
        return "block"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _aggregate_reason_codes(
    rows: tuple[ResearchStrategySourceMarketConflictGateRow, ...],
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        tuple(code for row in rows for code in row.reason_codes),
    )


def _validate_row_consistency(row: ResearchStrategySourceMarketConflictGateRow) -> None:
    expected_gap = _quantize(abs(row.source_probability - row.market_implied_probability))
    if row.probability_gap != expected_gap:
        raise ValueError("probability_gap must match source and market probabilities")
    if row.manual_review_required is not (row.gate_status != "pass"):
        raise ValueError("manual_review_required must match gate_status")
    if row.gate_status == "pass" and row.reason_codes != ("source_market_conflict_pass",):
        raise ValueError("pass rows must use the pass reason code")


def _validate_report_consistency(
    report: ResearchStrategySourceMarketConflictGateReport,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    input_count = _count_decimal(len(report.rows))
    pass_count = _count_decimal(sum(1 for row in report.rows if row.gate_status == "pass"))
    watch_count = _count_decimal(sum(1 for row in report.rows if row.gate_status == "watch"))
    block_count = _count_decimal(sum(1 for row in report.rows if row.gate_status == "block"))
    expected_values = {
        "input_count": input_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "average_probability_gap": _average(row.probability_gap for row in report.rows),
        "max_probability_gap": _max_or_zero(row.probability_gap for row in report.rows),
        "average_conflict_score": _average(row.conflict_score for row in report.rows),
        "max_conflict_score": _max_or_zero(row.conflict_score for row in report.rows),
        "average_cost_drag_score": _average(row.cost_drag_score for row in report.rows),
        "max_cost_drag_score": _max_or_zero(row.cost_drag_score for row in report.rows),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match report rows")
    if report.gate_status != _report_status(report.rows):
        raise ValueError("gate_status must match report rows")
    expected_reason_codes = _aggregate_reason_codes(report.rows)
    if not report.rows:
        expected_reason_codes = ("source_market_conflict_empty",)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report rows")


def _row_sort_key(row: ResearchStrategySourceMarketConflictGateRow) -> tuple[int, Decimal, str]:
    return (_STATUS_RANK[row.gate_status], -row.conflict_score, row.review_label)


def _normalize_rows(
    rows: Sequence[ResearchStrategySourceMarketConflictGateRow],
) -> tuple[ResearchStrategySourceMarketConflictGateRow, ...]:
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategySourceMarketConflictGateRow:
            raise ValueError(
                "rows must contain exactly ResearchStrategySourceMarketConflictGateRow "
                "values",
            )
    return normalized


def _normalize_public_payload(
    public_payload: Sequence[ResearchStrategySourceMarketConflictPublicPayloadItem],
) -> tuple[ResearchStrategySourceMarketConflictPublicPayloadItem, ...]:
    normalized = tuple(public_payload)
    seen_keys: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchStrategySourceMarketConflictPublicPayloadItem:
            raise ValueError(
                "public_payload must contain exactly "
                "ResearchStrategySourceMarketConflictPublicPayloadItem values",
            )
        if item.key in seen_keys:
            raise ValueError("public_payload keys must be duplicate-free")
        seen_keys.add(item.key)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if _contains_unsafe_public_term(reason_code):
            raise ValueError("reason_code has unsafe public payload")
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code is not supported")
        if reason_code not in seen:
            seen.add(reason_code)
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=_reason_code_rank))


def _reason_code_rank(reason_code: str) -> int:
    return _REASON_CODE_SEQUENCE.index(reason_code)


def _average(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(items, _ZERO) / Decimal(len(items)))


def _max_or_zero(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return _quantize(max(items))


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _seconds_between(started_at: datetime, finished_at: datetime) -> Decimal:
    delta = finished_at - started_at
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(Decimal(str(delta.total_seconds())))


def _require_public_identifier(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    if _contains_unsafe_public_term(value):
        raise ValueError(f"{name} has unsafe public payload")
    return value


def _require_public_text(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if _contains_unsafe_public_term(value):
        raise ValueError(f"{name} has unsafe public payload")
    return value


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _normalize_ratio(value: Decimal) -> Decimal:
    return min(_ONE, max(_ZERO, _quantize(value)))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT)


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_gate_status(name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in _GATE_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_hard_flags(name: str, value: object) -> None:
    for flag_name in _FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{name} {flag_name} must be True")


def _require_sha256_digest(name: str, value: str) -> None:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a SHA-256 digest")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _contains_unsafe_public_term(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _contains_unsafe_public_term(value):
        raise ValueError(f"{label} has unsafe public payload")


def _reject_payload_values(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_payload_values(label, asdict(value), path)
        return
    if type(value) is bool:
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{path or label} contains numeric value")
    if type(value) is str:
        if _contains_unsafe_public_term(value):
            raise ValueError(f"{path or label} has unsafe public payload")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in _FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_payload_values(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_payload_values(label, item, item_path)


def _contains_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    if _AUTH_PUBLIC_TERM_RE.search(lowered):
        return True
    normalized = _separator_normalize_public_text(lowered)
    compact = _compact_public_text(lowered)
    for term in _UNSAFE_PUBLIC_TERMS:
        lowered_term = term.lower()
        normalized_term = _separator_normalize_public_text(lowered_term)
        compact_term = _compact_public_text(lowered_term)
        if lowered_term in lowered:
            return True
        if normalized_term and normalized_term in normalized:
            return True
        if compact_term and compact_term in compact:
            return True
    return False


def _separator_normalize_public_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _compact_public_text(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must use exact Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must use exact datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON value contains numeric value")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _report_derived_validation_digest(
    report: ResearchStrategySourceMarketConflictGateReport,
) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload[_DERIVED_DIGEST_FIELD] = ""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SOURCE_MARKET_CONFLICT_GATE_REPORT_CONFIG_VERSION",
    "ResearchStrategySourceMarketConflictGateConfig",
    "ResearchStrategySourceMarketConflictGateInputRow",
    "ResearchStrategySourceMarketConflictGateReport",
    "ResearchStrategySourceMarketConflictGateRow",
    "ResearchStrategySourceMarketConflictPublicPayloadItem",
    "build_research_strategy_source_market_conflict_gate_report",
    "research_strategy_source_market_conflict_gate_report_payload",
)
