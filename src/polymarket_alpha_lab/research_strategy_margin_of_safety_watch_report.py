"""Report-only margin-of-safety watch status for strategy research candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_MARGIN_OF_SAFETY_WATCH_REPORT_CONFIG_VERSION = (
    "research-strategy-margin-of-safety-watch-report-v1"
)
RESEARCH_STRATEGY_MARGIN_OF_SAFETY_WATCH_STATUSES = ("pass", "watch", "block")

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
NEGATIVE_ONE = Decimal("-1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_PRIVATE_ROW_FIELDS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "source_url",
    "source_text",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "auth",
    "buy",
    "candidate",
    "database",
    "dsn",
    "live",
    "market",
    "order",
    "question",
    "recommend",
    "sell",
    "sizing",
    "slug",
    "table",
    "text",
    "token",
    "trade",
    "url",
    "wallet",
)
_PUBLIC_REPORT_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_model_edge_probability",
        "mean_total_uncertainty_probability",
        "mean_adjusted_margin_of_safety_probability",
        "min_evidence_strength_score",
        "max_resolution_ambiguity_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PUBLIC_ROW_FIELDS = frozenset(
    (
        "observed_at",
        "model_edge_probability",
        "cost_drag_probability",
        "confidence_haircut_probability",
        "liquidity_uncertainty_probability",
        "evidence_strength_score",
        "resolution_ambiguity_score",
        "total_uncertainty_probability",
        "adjusted_margin_of_safety_probability",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
        "row_number",
        "derived_validation_digest",
    ),
)
_PUBLIC_REASON_CODE_COUNT_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "input_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PUBLIC_REPORT_DECIMAL_FIELDS = (
    "input_count",
    "pass_count",
    "watch_count",
    "block_count",
    "mean_model_edge_probability",
    "mean_total_uncertainty_probability",
    "mean_adjusted_margin_of_safety_probability",
    "min_evidence_strength_score",
    "max_resolution_ambiguity_score",
)
_PUBLIC_ROW_DECIMAL_FIELDS = (
    "model_edge_probability",
    "cost_drag_probability",
    "confidence_haircut_probability",
    "liquidity_uncertainty_probability",
    "evidence_strength_score",
    "resolution_ambiguity_score",
    "total_uncertainty_probability",
    "adjusted_margin_of_safety_probability",
    "row_number",
)

ROW_REASON_CODES = (
    "adjusted_margin_block",
    "adjusted_margin_watch",
    "confidence_haircut_block",
    "confidence_haircut_watch",
    "cost_drag_block",
    "cost_drag_watch",
    "evidence_strength_block",
    "evidence_strength_watch",
    "liquidity_uncertainty_block",
    "liquidity_uncertainty_watch",
    "margin_of_safety_pass",
    "resolution_ambiguity_block",
    "resolution_ambiguity_watch",
)
REPORT_REASON_CODES = (
    "adjusted_margin_review",
    "confidence_haircut_review",
    "cost_drag_review",
    "evidence_strength_review",
    "liquidity_uncertainty_review",
    "margin_of_safety_report_block",
    "margin_of_safety_report_empty",
    "margin_of_safety_report_pass",
    "margin_of_safety_report_watch",
    "resolution_ambiguity_review",
)


@dataclass(frozen=True)
class ResearchStrategyMarginOfSafetyWatchConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MARGIN_OF_SAFETY_WATCH_REPORT_CONFIG_VERSION
    )
    pass_adjusted_margin_floor: Decimal = Decimal("0.050000")
    watch_adjusted_margin_floor: Decimal = Decimal("0.020000")
    pass_cost_drag_ceiling: Decimal = Decimal("0.030000")
    watch_cost_drag_ceiling: Decimal = Decimal("0.080000")
    pass_confidence_haircut_ceiling: Decimal = Decimal("0.050000")
    watch_confidence_haircut_ceiling: Decimal = Decimal("0.150000")
    pass_liquidity_uncertainty_ceiling: Decimal = Decimal("0.100000")
    watch_liquidity_uncertainty_ceiling: Decimal = Decimal("0.250000")
    pass_evidence_strength_floor: Decimal = Decimal("0.700000")
    watch_evidence_strength_floor: Decimal = Decimal("0.450000")
    pass_resolution_ambiguity_ceiling: Decimal = Decimal("0.100000")
    watch_resolution_ambiguity_ceiling: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyMarginOfSafetyWatchConfig:
            raise TypeError(
                "ResearchStrategyMarginOfSafetyWatchConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyMarginOfSafetyWatchConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyMarginOfSafetyWatchConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MARGIN_OF_SAFETY_WATCH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_adjusted_margin_floor",
            "watch_adjusted_margin_floor",
            "pass_cost_drag_ceiling",
            "watch_cost_drag_ceiling",
            "pass_confidence_haircut_ceiling",
            "watch_confidence_haircut_ceiling",
            "pass_liquidity_uncertainty_ceiling",
            "watch_liquidity_uncertainty_ceiling",
            "pass_evidence_strength_floor",
            "watch_evidence_strength_floor",
            "pass_resolution_ambiguity_ceiling",
            "watch_resolution_ambiguity_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "adjusted_margin",
            self.pass_adjusted_margin_floor,
            self.watch_adjusted_margin_floor,
        )
        _require_ceiling_pair(
            "cost_drag",
            self.pass_cost_drag_ceiling,
            self.watch_cost_drag_ceiling,
        )
        _require_ceiling_pair(
            "confidence_haircut",
            self.pass_confidence_haircut_ceiling,
            self.watch_confidence_haircut_ceiling,
        )
        _require_ceiling_pair(
            "liquidity_uncertainty",
            self.pass_liquidity_uncertainty_ceiling,
            self.watch_liquidity_uncertainty_ceiling,
        )
        _require_floor_pair(
            "evidence_strength",
            self.pass_evidence_strength_floor,
            self.watch_evidence_strength_floor,
        )
        _require_ceiling_pair(
            "resolution_ambiguity",
            self.pass_resolution_ambiguity_ceiling,
            self.watch_resolution_ambiguity_ceiling,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyMarginOfSafetyWatchInput:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    observed_at: datetime
    model_edge_probability: Decimal
    cost_drag_probability: Decimal
    confidence_haircut_probability: Decimal
    liquidity_uncertainty_probability: Decimal
    evidence_strength_score: Decimal
    resolution_ambiguity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyMarginOfSafetyWatchInput:
            raise TypeError(
                "ResearchStrategyMarginOfSafetyWatchInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyMarginOfSafetyWatchInput:
            raise ValueError(
                "input must be exactly ResearchStrategyMarginOfSafetyWatchInput",
            )
        for field_name in _PRIVATE_ROW_FIELDS:
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "model_edge_probability",
            _normalize_signed_probability(
                "model_edge_probability",
                self.model_edge_probability,
            ),
        )
        for field_name in (
            "cost_drag_probability",
            "confidence_haircut_probability",
            "liquidity_uncertainty_probability",
            "evidence_strength_score",
            "resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyMarginOfSafetyWatchReasonCodeCount:
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
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyMarginOfSafetyWatchRow:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    observed_at: datetime
    model_edge_probability: Decimal
    cost_drag_probability: Decimal
    confidence_haircut_probability: Decimal
    liquidity_uncertainty_probability: Decimal
    evidence_strength_score: Decimal
    resolution_ambiguity_score: Decimal
    total_uncertainty_probability: Decimal
    adjusted_margin_of_safety_probability: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyMarginOfSafetyWatchRow:
            raise TypeError(
                "ResearchStrategyMarginOfSafetyWatchRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyMarginOfSafetyWatchRow:
            raise ValueError("row must be exactly ResearchStrategyMarginOfSafetyWatchRow")
        for field_name in _PRIVATE_ROW_FIELDS:
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "model_edge_probability",
            _normalize_signed_probability(
                "model_edge_probability",
                self.model_edge_probability,
            ),
        )
        for field_name in (
            "cost_drag_probability",
            "confidence_haircut_probability",
            "liquidity_uncertainty_probability",
            "evidence_strength_score",
            "resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_uncertainty_probability",
            _normalize_nonnegative_decimal(
                "total_uncertainty_probability",
                self.total_uncertainty_probability,
            ),
        )
        object.__setattr__(
            self,
            "adjusted_margin_of_safety_probability",
            _normalize_decimal(
                "adjusted_margin_of_safety_probability",
                self.adjusted_margin_of_safety_probability,
            ),
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
class ResearchStrategyMarginOfSafetyWatchReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_model_edge_probability: Decimal
    mean_total_uncertainty_probability: Decimal
    mean_adjusted_margin_of_safety_probability: Decimal
    min_evidence_strength_score: Decimal
    max_resolution_ambiguity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyMarginOfSafetyWatchReasonCodeCount, ...]
    rows: tuple[ResearchStrategyMarginOfSafetyWatchRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyMarginOfSafetyWatchReport:
            raise TypeError(
                "ResearchStrategyMarginOfSafetyWatchReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyMarginOfSafetyWatchReport:
            raise ValueError(
                "report must be exactly ResearchStrategyMarginOfSafetyWatchReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_model_edge_probability",
            "mean_adjusted_margin_of_safety_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_total_uncertainty_probability",
            "min_evidence_strength_score",
            "max_resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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
        _validate_report_consistency(self)
        _apply_or_verify_report_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        _verify_report_integrity(self)
        return _public_report_payload(self)


def build_research_strategy_margin_of_safety_watch_report(
    inputs: Iterable[ResearchStrategyMarginOfSafetyWatchInput],
    *,
    config: ResearchStrategyMarginOfSafetyWatchConfig,
    generated_at: datetime,
) -> ResearchStrategyMarginOfSafetyWatchReport:
    if type(config) is not ResearchStrategyMarginOfSafetyWatchConfig:
        raise ValueError("config must be a ResearchStrategyMarginOfSafetyWatchConfig")
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
    return ResearchStrategyMarginOfSafetyWatchReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_model_edge_probability=_mean(
            tuple(row.model_edge_probability for row in rows),
        ),
        mean_total_uncertainty_probability=_mean(
            tuple(row.total_uncertainty_probability for row in rows),
        ),
        mean_adjusted_margin_of_safety_probability=_mean(
            tuple(row.adjusted_margin_of_safety_probability for row in rows),
        ),
        min_evidence_strength_score=_min_or_zero(
            tuple(row.evidence_strength_score for row in rows),
        ),
        max_resolution_ambiguity_score=_max_or_zero(
            tuple(row.resolution_ambiguity_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_margin_of_safety_watch_report_payload(
    report: ResearchStrategyMarginOfSafetyWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyMarginOfSafetyWatchReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _public_report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyMarginOfSafetyWatchReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def validate_research_strategy_margin_of_safety_watch_public_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return research_strategy_margin_of_safety_watch_report_payload(payload)


def research_strategy_margin_of_safety_watch_report_digest(
    report: ResearchStrategyMarginOfSafetyWatchReport,
) -> str:
    if type(report) is not ResearchStrategyMarginOfSafetyWatchReport:
        raise ValueError("report must be a ResearchStrategyMarginOfSafetyWatchReport")
    _verify_report_integrity(report)
    return report.derived_validation_digest


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
    value: ResearchStrategyMarginOfSafetyWatchInput,
    *,
    config: ResearchStrategyMarginOfSafetyWatchConfig,
    generated_at: datetime,
) -> ResearchStrategyMarginOfSafetyWatchRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    total_uncertainty = _sum_decimals(
        (
            value.cost_drag_probability,
            value.confidence_haircut_probability,
            value.liquidity_uncertainty_probability,
            value.resolution_ambiguity_score,
        ),
    )
    adjusted_margin = _subtract_decimal(value.model_edge_probability, total_uncertainty)
    return ResearchStrategyMarginOfSafetyWatchRow(
        candidate_id=value.candidate_id,
        market_id=value.market_id,
        market_slug=value.market_slug,
        market_question=value.market_question,
        source_url=value.source_url,
        source_text=value.source_text,
        observed_at=observed_at,
        model_edge_probability=value.model_edge_probability,
        cost_drag_probability=value.cost_drag_probability,
        confidence_haircut_probability=value.confidence_haircut_probability,
        liquidity_uncertainty_probability=value.liquidity_uncertainty_probability,
        evidence_strength_score=value.evidence_strength_score,
        resolution_ambiguity_score=value.resolution_ambiguity_score,
        total_uncertainty_probability=total_uncertainty,
        adjusted_margin_of_safety_probability=adjusted_margin,
        status=_row_status(
            adjusted_margin_of_safety_probability=adjusted_margin,
            value=value,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            adjusted_margin_of_safety_probability=adjusted_margin,
            value=value,
            config=config,
        ),
    )


def _row_status(
    *,
    adjusted_margin_of_safety_probability: Decimal,
    value: ResearchStrategyMarginOfSafetyWatchInput,
    config: ResearchStrategyMarginOfSafetyWatchConfig,
) -> str:
    if (
        adjusted_margin_of_safety_probability < config.watch_adjusted_margin_floor
        or value.cost_drag_probability > config.watch_cost_drag_ceiling
        or value.confidence_haircut_probability > config.watch_confidence_haircut_ceiling
        or value.liquidity_uncertainty_probability
        > config.watch_liquidity_uncertainty_ceiling
        or value.evidence_strength_score < config.watch_evidence_strength_floor
        or value.resolution_ambiguity_score > config.watch_resolution_ambiguity_ceiling
    ):
        return "block"
    if (
        adjusted_margin_of_safety_probability < config.pass_adjusted_margin_floor
        or value.cost_drag_probability > config.pass_cost_drag_ceiling
        or value.confidence_haircut_probability > config.pass_confidence_haircut_ceiling
        or value.liquidity_uncertainty_probability
        > config.pass_liquidity_uncertainty_ceiling
        or value.evidence_strength_score < config.pass_evidence_strength_floor
        or value.resolution_ambiguity_score > config.pass_resolution_ambiguity_ceiling
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    adjusted_margin_of_safety_probability: Decimal,
    value: ResearchStrategyMarginOfSafetyWatchInput,
    config: ResearchStrategyMarginOfSafetyWatchConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if adjusted_margin_of_safety_probability < config.watch_adjusted_margin_floor:
        codes.append("adjusted_margin_block")
    elif adjusted_margin_of_safety_probability < config.pass_adjusted_margin_floor:
        codes.append("adjusted_margin_watch")
    if value.cost_drag_probability > config.watch_cost_drag_ceiling:
        codes.append("cost_drag_block")
    elif value.cost_drag_probability > config.pass_cost_drag_ceiling:
        codes.append("cost_drag_watch")
    if value.confidence_haircut_probability > config.watch_confidence_haircut_ceiling:
        codes.append("confidence_haircut_block")
    elif value.confidence_haircut_probability > config.pass_confidence_haircut_ceiling:
        codes.append("confidence_haircut_watch")
    if value.liquidity_uncertainty_probability > config.watch_liquidity_uncertainty_ceiling:
        codes.append("liquidity_uncertainty_block")
    elif value.liquidity_uncertainty_probability > config.pass_liquidity_uncertainty_ceiling:
        codes.append("liquidity_uncertainty_watch")
    if value.evidence_strength_score < config.watch_evidence_strength_floor:
        codes.append("evidence_strength_block")
    elif value.evidence_strength_score < config.pass_evidence_strength_floor:
        codes.append("evidence_strength_watch")
    if value.resolution_ambiguity_score > config.watch_resolution_ambiguity_ceiling:
        codes.append("resolution_ambiguity_block")
    elif value.resolution_ambiguity_score > config.pass_resolution_ambiguity_ceiling:
        codes.append("resolution_ambiguity_watch")
    if not codes:
        codes.append("margin_of_safety_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(rows: tuple[ResearchStrategyMarginOfSafetyWatchRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyMarginOfSafetyWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("margin_of_safety_report_empty",)
    report_status = _report_status(rows)
    codes = [f"margin_of_safety_report_{report_status}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    if any(code.startswith("adjusted_margin_") for code in row_codes):
        codes.append("adjusted_margin_review")
    if any(code.startswith("cost_drag_") for code in row_codes):
        codes.append("cost_drag_review")
    if any(code.startswith("confidence_haircut_") for code in row_codes):
        codes.append("confidence_haircut_review")
    if any(code.startswith("liquidity_uncertainty_") for code in row_codes):
        codes.append("liquidity_uncertainty_review")
    if any(code.startswith("evidence_strength_") for code in row_codes):
        codes.append("evidence_strength_review")
    if any(code.startswith("resolution_ambiguity_") for code in row_codes):
        codes.append("resolution_ambiguity_review")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategyMarginOfSafetyWatchRow,
) -> tuple[int, Decimal, Decimal, Decimal, datetime, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.adjusted_margin_of_safety_probability,
        row.evidence_strength_score,
        -row.resolution_ambiguity_score,
        row.observed_at,
        row.candidate_id,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyMarginOfSafetyWatchInput],
) -> tuple[ResearchStrategyMarginOfSafetyWatchInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyMarginOfSafetyWatchInput:
            raise ValueError(
                "inputs must contain ResearchStrategyMarginOfSafetyWatchInput values",
            )
        _require_hard_flags("input", value)
        if value.candidate_id in seen_refs:
            raise ValueError("inputs must not contain duplicate candidate_id values")
        seen_refs.add(value.candidate_id)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyMarginOfSafetyWatchRow],
) -> tuple[ResearchStrategyMarginOfSafetyWatchRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyMarginOfSafetyWatchRow:
            raise ValueError(
                "rows must contain ResearchStrategyMarginOfSafetyWatchRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.candidate_id in seen_refs:
            raise ValueError("rows must not contain duplicate candidate_id values")
        seen_refs.add(row.candidate_id)
    return normalized


def _validate_row_consistency(row: ResearchStrategyMarginOfSafetyWatchRow) -> None:
    expected_uncertainty = _sum_decimals(
        (
            row.cost_drag_probability,
            row.confidence_haircut_probability,
            row.liquidity_uncertainty_probability,
            row.resolution_ambiguity_score,
        ),
    )
    if row.total_uncertainty_probability != expected_uncertainty:
        raise ValueError("total_uncertainty_probability must match row inputs")
    expected_margin = _subtract_decimal(
        row.model_edge_probability,
        row.total_uncertainty_probability,
    )
    if row.adjusted_margin_of_safety_probability != expected_margin:
        raise ValueError(
            "adjusted_margin_of_safety_probability must match row inputs",
        )
    if row.status == "pass" and row.reason_codes != ("margin_of_safety_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchStrategyMarginOfSafetyWatchReport,
) -> None:
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
    if report.mean_model_edge_probability != _mean(
        tuple(row.model_edge_probability for row in report.rows),
    ):
        raise ValueError("mean_model_edge_probability must match rows")
    if report.mean_total_uncertainty_probability != _mean(
        tuple(row.total_uncertainty_probability for row in report.rows),
    ):
        raise ValueError("mean_total_uncertainty_probability must match rows")
    if report.mean_adjusted_margin_of_safety_probability != _mean(
        tuple(row.adjusted_margin_of_safety_probability for row in report.rows),
    ):
        raise ValueError("mean_adjusted_margin_of_safety_probability must match rows")
    if report.min_evidence_strength_score != _min_or_zero(
        tuple(row.evidence_strength_score for row in report.rows),
    ):
        raise ValueError("min_evidence_strength_score must match rows")
    if report.max_resolution_ambiguity_score != _max_or_zero(
        tuple(row.resolution_ambiguity_score for row in report.rows),
    ):
        raise ValueError("max_resolution_ambiguity_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(report: ResearchStrategyMarginOfSafetyWatchReport) -> None:
    _validate_report_consistency(report)
    _verify_report_digest(report)
    for row in report.rows:
        _verify_digest(row)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    _verify_public_report_schema(payload)
    _verify_public_payload_digest("payload", payload)
    rows = payload.get("rows")
    for index, row in enumerate(rows):
        _verify_public_payload_digest(f"payload.rows[{index}]", row)


def _verify_public_report_schema(payload: dict[str, Any]) -> None:
    _require_public_field_set("payload", payload, _PUBLIC_REPORT_FIELDS)
    _require_hard_flags("payload", _DictFlags(payload))
    _require_public_datetime_string("payload.generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_STRATEGY_MARGIN_OF_SAFETY_WATCH_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    decimal_values = {
        field_name: _require_public_decimal_string(
            f"payload.{field_name}",
            payload[field_name],
        )
        for field_name in _PUBLIC_REPORT_DECIMAL_FIELDS
    }
    _require_status("payload.status", payload["status"])
    _require_public_reason_codes(
        "payload.reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        _verify_public_row_schema(index, row)
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("payload.reason_code_counts must be a list")
    for index, row in enumerate(reason_code_counts):
        _verify_public_reason_code_count_schema(index, row)
    if decimal_values["input_count"] != _count(len(rows)):
        raise ValueError("payload.input_count must match rows")
    row_statuses = tuple(row["status"] for row in rows)
    if decimal_values["pass_count"] != _count(
        sum(1 for status in row_statuses if status == "pass"),
    ):
        raise ValueError("payload.pass_count must match rows")
    if decimal_values["watch_count"] != _count(
        sum(1 for status in row_statuses if status == "watch"),
    ):
        raise ValueError("payload.watch_count must match rows")
    if decimal_values["block_count"] != _count(
        sum(1 for status in row_statuses if status == "block"),
    ):
        raise ValueError("payload.block_count must match rows")
    if payload["status"] != _public_report_status(row_statuses):
        raise ValueError("payload.status must match rows")


def _verify_public_row_schema(index: int, row: object) -> None:
    if type(row) is not dict:
        raise ValueError("payload.rows must contain JSON objects")
    _require_public_field_set(f"payload.rows[{index}]", row, _PUBLIC_ROW_FIELDS)
    _require_hard_flags(f"payload.rows[{index}]", _DictFlags(row))
    _require_public_datetime_string(f"payload.rows[{index}].observed_at", row["observed_at"])
    for field_name in _PUBLIC_ROW_DECIMAL_FIELDS:
        _require_public_decimal_string(f"payload.rows[{index}].{field_name}", row[field_name])
    _require_status(f"payload.rows[{index}].status", row["status"])
    _require_public_reason_codes(
        f"payload.rows[{index}].reason_codes",
        row["reason_codes"],
        ROW_REASON_CODES,
    )


def _verify_public_reason_code_count_schema(index: int, row: object) -> None:
    if type(row) is not dict:
        raise ValueError("payload.reason_code_counts must contain JSON objects")
    _require_public_field_set(
        f"payload.reason_code_counts[{index}]",
        row,
        _PUBLIC_REASON_CODE_COUNT_FIELDS,
    )
    _require_hard_flags(f"payload.reason_code_counts[{index}]", _DictFlags(row))
    _require_reason_code(
        f"payload.reason_code_counts[{index}].reason_code",
        row["reason_code"],
    )
    _require_public_decimal_string(f"payload.reason_code_counts[{index}].count", row["count"])
    _require_public_decimal_string(
        f"payload.reason_code_counts[{index}].input_ratio",
        row["input_ratio"],
    )


def _public_report_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _require_public_field_set(
    label: str,
    payload: dict[str, Any],
    expected_fields: frozenset[str],
) -> None:
    if frozenset(payload) != expected_fields:
        raise ValueError(f"unexpected public payload field in {label}")


def _require_public_datetime_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a datetime string") from exc
    _as_utc(name, parsed)


def _require_public_reason_codes(
    name: str,
    value: object,
    supported: tuple[str, ...],
) -> None:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list")
    _normalize_reason_codes(name, tuple(value), supported)


def _require_public_decimal_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite")
    quantized = _quantize(parsed)
    if str(quantized) != value:
        raise ValueError(f"{name} must be a canonical Decimal string")
    return quantized


def _verify_public_payload_digest(label: str, payload: dict[str, Any]) -> None:
    provided = payload.get("derived_validation_digest")
    _require_digest(f"{label}.derived_validation_digest", provided)
    expected = _public_payload_digest(payload)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _status_count(
    rows: tuple[ResearchStrategyMarginOfSafetyWatchRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyMarginOfSafetyWatchRow, ...],
) -> tuple[ResearchStrategyMarginOfSafetyWatchReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyMarginOfSafetyWatchReasonCodeCount(
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
    value: Iterable[ResearchStrategyMarginOfSafetyWatchReasonCodeCount],
) -> tuple[ResearchStrategyMarginOfSafetyWatchReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategyMarginOfSafetyWatchReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyMarginOfSafetyWatchReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _public_report_payload(
    report: ResearchStrategyMarginOfSafetyWatchReport,
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
    row: ResearchStrategyMarginOfSafetyWatchRow,
) -> dict[str, Any]:
    payload = asdict(row)
    for field_name in _PRIVATE_ROW_FIELDS:
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


def _report_digest_for(report: ResearchStrategyMarginOfSafetyWatchReport) -> str:
    payload = asdict(report)
    payload["rows"] = [
        _public_row_payload(index, row)
        for index, row in enumerate(report.rows, start=1)
    ]
    payload.pop("derived_validation_digest", None)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _public_payload_digest(public_payload)


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


def _min_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return min(values).quantize(RATIO_QUANTUM)


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return max(values).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_signed_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < NEGATIVE_ONE or normalized > ONE:
        raise ValueError(f"{name} must be between -1 and 1")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
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
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_MARGIN_OF_SAFETY_WATCH_STATUSES
    ):
        raise ValueError(f"{name} must be pass, watch, or block")


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


def _require_private_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical string")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
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


def _apply_or_verify_report_digest(
    report: ResearchStrategyMarginOfSafetyWatchReport,
) -> None:
    provided = report.derived_validation_digest
    if provided:
        _verify_report_digest(report)
    else:
        object.__setattr__(report, "derived_validation_digest", _report_digest_for(report))


def _verify_report_digest(report: ResearchStrategyMarginOfSafetyWatchReport) -> None:
    provided = report.derived_validation_digest
    _require_digest("derived_validation_digest", provided)
    if provided != _report_digest_for(report):
        raise ValueError("derived_validation_digest does not match public payload")


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
    if type(value) is str:
        lowered = value.lower()
        if "://" in lowered or any(
            fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS
        ):
            raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MARGIN_OF_SAFETY_WATCH_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_MARGIN_OF_SAFETY_WATCH_STATUSES",
    "ResearchStrategyMarginOfSafetyWatchConfig",
    "ResearchStrategyMarginOfSafetyWatchInput",
    "ResearchStrategyMarginOfSafetyWatchReasonCodeCount",
    "ResearchStrategyMarginOfSafetyWatchRow",
    "ResearchStrategyMarginOfSafetyWatchReport",
    "build_research_strategy_margin_of_safety_watch_report",
    "research_strategy_margin_of_safety_watch_report_digest",
    "research_strategy_margin_of_safety_watch_report_payload",
    "validate_research_strategy_margin_of_safety_watch_public_payload",
)
