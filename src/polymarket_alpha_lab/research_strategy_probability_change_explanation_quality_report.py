"""Pure Phase 1 probability-change explanation quality report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_PROBABILITY_CHANGE_EXPLANATION_QUALITY_REPORT_CONFIG_VERSION = (
    "research-strategy-probability-change-explanation-quality-report-v0"
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_CHANGE_EXPLANATION_QUALITY_REPORT_CONFIG_VERSION",
    "ResearchStrategyProbabilityChangeExplanationQualityConfig",
    "ResearchStrategyProbabilityChangeExplanationQualityInput",
    "ResearchStrategyProbabilityChangeExplanationQualityReasonCodeCount",
    "ResearchStrategyProbabilityChangeExplanationQualityReport",
    "ResearchStrategyProbabilityChangeExplanationQualityRow",
    "build_research_strategy_probability_change_explanation_quality_report",
    "research_strategy_probability_change_explanation_quality_digest",
    "research_strategy_probability_change_explanation_quality_digest_payload",
    "research_strategy_probability_change_explanation_quality_report_payload",
)


PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
STATUS_SEVERITY = {BLOCK_STATUS: 2, WATCH_STATUS: 1, PASS_STATUS: 0}
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FOUR = Decimal("4.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

_BLOCKED_TEXT_PARTS = (
    ("can", "didate"),
    ("mar", "ket"),
    ("sl", "ug"),
    ("ques", "tion"),
    ("u", "rl"),
    ("so", "urce"),
    ("d", "sn"),
    ("ta", "ble"),
    ("to", "ken"),
    ("wal", "let"),
    ("or", "der"),
    ("tr", "ade"),
    ("b", "uy"),
    ("s", "ell"),
    ("re", "commend"),
    ("siz", "ing"),
    ("data", "base"),
    ("net", "work"),
    ("au", "th"),
    ("li", "ve"),
    ("r", "aw"),
)

REASON_CODE_SEQUENCE = (
    "probability_change_explanation_quality_missing_inputs",
    "probability_change_explanation_quality_block",
    "probability_change_explanation_quality_watch",
    "probability_change_explanation_quality_pass",
    "large_probability_change_quality_gap_block",
    "large_probability_change_quality_gap_watch",
    "explanation_completeness_low_block",
    "explanation_completeness_low_watch",
    "evidence_linkage_low_block",
    "evidence_linkage_low_watch",
    "cost_context_missing_block",
    "cost_context_missing_watch",
    "settlement_rule_clarity_low_block",
    "settlement_rule_clarity_low_watch",
)


@dataclass(frozen=True)
class ResearchStrategyProbabilityChangeExplanationQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_PROBABILITY_CHANGE_EXPLANATION_QUALITY_REPORT_CONFIG_VERSION
    )
    watch_probability_change_threshold: Decimal = Decimal("0.050000")
    block_probability_change_threshold: Decimal = Decimal("0.100000")
    watch_explanation_completeness: Decimal = Decimal("0.800000")
    block_explanation_completeness: Decimal = Decimal("0.600000")
    watch_evidence_linkage: Decimal = Decimal("0.750000")
    block_evidence_linkage: Decimal = Decimal("0.500000")
    watch_cost_context_coverage: Decimal = Decimal("0.750000")
    block_cost_context_coverage: Decimal = Decimal("0.450000")
    watch_settlement_rule_clarity: Decimal = Decimal("0.800000")
    block_settlement_rule_clarity: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityChangeExplanationQualityConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_probability_change_threshold",
            "block_probability_change_threshold",
            "watch_explanation_completeness",
            "block_explanation_completeness",
            "watch_evidence_linkage",
            "block_evidence_linkage",
            "watch_cost_context_coverage",
            "block_cost_context_coverage",
            "watch_settlement_rule_clarity",
            "block_settlement_rule_clarity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "watch_probability_change_threshold",
            self.watch_probability_change_threshold,
            "block_probability_change_threshold",
            self.block_probability_change_threshold,
        )
        _require_falling_threshold(
            "explanation_completeness",
            self.watch_explanation_completeness,
            self.block_explanation_completeness,
        )
        _require_falling_threshold(
            "evidence_linkage",
            self.watch_evidence_linkage,
            self.block_evidence_linkage,
        )
        _require_falling_threshold(
            "cost_context_coverage",
            self.watch_cost_context_coverage,
            self.block_cost_context_coverage,
        )
        _require_falling_threshold(
            "settlement_rule_clarity",
            self.watch_settlement_rule_clarity,
            self.block_settlement_rule_clarity,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityChangeExplanationQualityInput:
    quality_key: str
    probability_change_abs: Decimal
    explanation_completeness_score: Decimal
    evidence_linkage_score: Decimal
    cost_context_coverage_score: Decimal
    settlement_rule_clarity_score: Decimal
    explanation_observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityChangeExplanationQualityInput,
            "input",
        )
        _require_public_key("quality_key", self.quality_key)
        for field_name in (
            "probability_change_abs",
            "explanation_completeness_score",
            "evidence_linkage_score",
            "cost_context_coverage_score",
            "settlement_rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "explanation_observed_at",
            _as_utc("explanation_observed_at", self.explanation_observed_at),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityChangeExplanationQualityRow:
    rank: Decimal
    quality_key: str
    explanation_observed_at: datetime
    probability_change_abs: Decimal
    explanation_completeness_score: Decimal
    evidence_linkage_score: Decimal
    cost_context_coverage_score: Decimal
    settlement_rule_clarity_score: Decimal
    quality_score: Decimal
    deficiency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityChangeExplanationQualityRow,
            "row",
        )
        object.__setattr__(self, "rank", _require_nonnegative_decimal("rank", self.rank))
        _require_public_key("quality_key", self.quality_key)
        object.__setattr__(
            self,
            "explanation_observed_at",
            _as_utc("explanation_observed_at", self.explanation_observed_at),
        )
        for field_name in (
            "probability_change_abs",
            "explanation_completeness_score",
            "evidence_linkage_score",
            "cost_context_coverage_score",
            "settlement_rule_clarity_score",
            "quality_score",
            "deficiency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityChangeExplanationQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityChangeExplanationQualityReasonCodeCount,
            "reason_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code(self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_count", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityChangeExplanationQualityReport:
    generated_at: datetime
    config_version: str
    status: str
    quality_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    large_probability_change_count: Decimal
    explanation_completeness_gap_count: Decimal
    evidence_linkage_gap_count: Decimal
    cost_context_gap_count: Decimal
    settlement_rule_clarity_gap_count: Decimal
    average_probability_change_abs: Decimal
    average_quality_score: Decimal
    max_deficiency_score: Decimal
    rows: tuple[ResearchStrategyProbabilityChangeExplanationQualityRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyProbabilityChangeExplanationQualityReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityChangeExplanationQualityReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status(self.status)
        for field_name in (
            "quality_count",
            "pass_count",
            "watch_count",
            "block_count",
            "large_probability_change_count",
            "explanation_completeness_gap_count",
            "evidence_linkage_gap_count",
            "cost_context_gap_count",
            "settlement_rule_clarity_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_probability_change_abs",
            "average_quality_score",
            "max_deficiency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
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
                allow_empty=False,
            ),
        )
        _require_digest_or_empty(self.public_payload_digest)
        _require_hard_flags("report", self)
        expected_digest = _public_digest_from_values(_report_values_without_digest(self))
        if self.public_payload_digest:
            if self.public_payload_digest != expected_digest:
                raise ValueError("public_payload_digest must match report payload")
        else:
            object.__setattr__(self, "public_payload_digest", expected_digest)
        _validate_report_consistency(self)


def build_research_strategy_probability_change_explanation_quality_report(
    inputs: Sequence[ResearchStrategyProbabilityChangeExplanationQualityInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyProbabilityChangeExplanationQualityConfig | None = None,
) -> ResearchStrategyProbabilityChangeExplanationQualityReport:
    if config is None:
        config = ResearchStrategyProbabilityChangeExplanationQualityConfig()
    if type(config) is not ResearchStrategyProbabilityChangeExplanationQualityConfig:
        raise ValueError(
            "config must be ResearchStrategyProbabilityChangeExplanationQualityConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(inputs)
    for item in items:
        if item.explanation_observed_at > generated_at:
            raise ValueError("explanation_observed_at must not be after generated_at")
    rows = _rank_rows(tuple(_row_from_input(item, config) for item in items))
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "quality_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, PASS_STATUS),
        "watch_count": _status_count(rows, WATCH_STATUS),
        "block_count": _status_count(rows, BLOCK_STATUS),
        "large_probability_change_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.probability_change_abs >= config.watch_probability_change_threshold
            ),
        ),
        "explanation_completeness_gap_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.explanation_completeness_score
                <= config.watch_explanation_completeness
            ),
        ),
        "evidence_linkage_gap_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.evidence_linkage_score <= config.watch_evidence_linkage
            ),
        ),
        "cost_context_gap_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.cost_context_coverage_score <= config.watch_cost_context_coverage
            ),
        ),
        "settlement_rule_clarity_gap_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.settlement_rule_clarity_score
                <= config.watch_settlement_rule_clarity
            ),
        ),
        "average_probability_change_abs": _average(
            tuple(row.probability_change_abs for row in rows),
        ),
        "average_quality_score": _average(tuple(row.quality_score for row in rows)),
        "max_deficiency_score": max(
            (row.deficiency_score for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyProbabilityChangeExplanationQualityReport(
        **values,
        public_payload_digest=_public_digest_from_values(values),
    )


def research_strategy_probability_change_explanation_quality_report_payload(
    report: ResearchStrategyProbabilityChangeExplanationQualityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyProbabilityChangeExplanationQualityReport:
        raise ValueError(
            "report must be ResearchStrategyProbabilityChangeExplanationQualityReport",
        )
    _require_hard_flags("report", report)
    if report.public_payload_digest != research_strategy_probability_change_explanation_quality_digest(
        report,
    ):
        raise ValueError("public_payload_digest must match report payload")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def research_strategy_probability_change_explanation_quality_digest_payload(
    report: ResearchStrategyProbabilityChangeExplanationQualityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyProbabilityChangeExplanationQualityReport:
        raise ValueError(
            "report must be ResearchStrategyProbabilityChangeExplanationQualityReport",
        )
    payload = _json_ready(_report_values_without_digest(report))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return payload


def research_strategy_probability_change_explanation_quality_digest(
    report: ResearchStrategyProbabilityChangeExplanationQualityReport,
) -> str:
    if type(report) is not ResearchStrategyProbabilityChangeExplanationQualityReport:
        raise ValueError(
            "report must be ResearchStrategyProbabilityChangeExplanationQualityReport",
        )
    return _public_digest_from_values(_report_values_without_digest(report))


def _row_from_input(
    item: ResearchStrategyProbabilityChangeExplanationQualityInput,
    config: ResearchStrategyProbabilityChangeExplanationQualityConfig,
) -> ResearchStrategyProbabilityChangeExplanationQualityRow:
    quality_score = _quality_score(item)
    deficiency_score = _clamp_probability(ONE - quality_score)
    reason_codes = _row_reason_codes(
        item=item,
        quality_score=quality_score,
        config=config,
    )
    return ResearchStrategyProbabilityChangeExplanationQualityRow(
        rank=ONE,
        quality_key=item.quality_key,
        explanation_observed_at=item.explanation_observed_at,
        probability_change_abs=item.probability_change_abs,
        explanation_completeness_score=item.explanation_completeness_score,
        evidence_linkage_score=item.evidence_linkage_score,
        cost_context_coverage_score=item.cost_context_coverage_score,
        settlement_rule_clarity_score=item.settlement_rule_clarity_score,
        quality_score=quality_score,
        deficiency_score=deficiency_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _quality_score(
    item: ResearchStrategyProbabilityChangeExplanationQualityInput,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(
            (
                item.explanation_completeness_score
                + item.evidence_linkage_score
                + item.cost_context_coverage_score
                + item.settlement_rule_clarity_score
            )
            / FOUR,
        )


def _row_reason_codes(
    *,
    item: ResearchStrategyProbabilityChangeExplanationQualityInput,
    quality_score: Decimal,
    config: ResearchStrategyProbabilityChangeExplanationQualityConfig,
) -> tuple[str, ...]:
    detail_codes: list[str] = []
    _append_low_score_reason(
        detail_codes,
        score=item.explanation_completeness_score,
        block_threshold=config.block_explanation_completeness,
        watch_threshold=config.watch_explanation_completeness,
        block_reason="explanation_completeness_low_block",
        watch_reason="explanation_completeness_low_watch",
    )
    _append_low_score_reason(
        detail_codes,
        score=item.evidence_linkage_score,
        block_threshold=config.block_evidence_linkage,
        watch_threshold=config.watch_evidence_linkage,
        block_reason="evidence_linkage_low_block",
        watch_reason="evidence_linkage_low_watch",
    )
    _append_low_score_reason(
        detail_codes,
        score=item.cost_context_coverage_score,
        block_threshold=config.block_cost_context_coverage,
        watch_threshold=config.watch_cost_context_coverage,
        block_reason="cost_context_missing_block",
        watch_reason="cost_context_missing_watch",
    )
    _append_low_score_reason(
        detail_codes,
        score=item.settlement_rule_clarity_score,
        block_threshold=config.block_settlement_rule_clarity,
        watch_threshold=config.watch_settlement_rule_clarity,
        block_reason="settlement_rule_clarity_low_block",
        watch_reason="settlement_rule_clarity_low_watch",
    )
    status = _status_from_reason_codes(tuple(detail_codes))
    reason_codes = [f"probability_change_explanation_quality_{status}"]
    if (
        item.probability_change_abs >= config.block_probability_change_threshold
        and status == BLOCK_STATUS
    ):
        reason_codes.append("large_probability_change_quality_gap_block")
    elif (
        item.probability_change_abs >= config.watch_probability_change_threshold
        and status != PASS_STATUS
        and quality_score < ONE
    ):
        reason_codes.append("large_probability_change_quality_gap_watch")
    reason_codes.extend(detail_codes)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        allow_empty=False,
    )


def _append_low_score_reason(
    reason_codes: list[str],
    *,
    score: Decimal,
    block_threshold: Decimal,
    watch_threshold: Decimal,
    block_reason: str,
    watch_reason: str,
) -> None:
    if score <= block_threshold:
        reason_codes.append(block_reason)
    elif score <= watch_threshold:
        reason_codes.append(watch_reason)


def _rank_rows(
    rows: tuple[ResearchStrategyProbabilityChangeExplanationQualityRow, ...],
) -> tuple[ResearchStrategyProbabilityChangeExplanationQualityRow, ...]:
    return tuple(
        ResearchStrategyProbabilityChangeExplanationQualityRow(
            rank=_decimal_count(index),
            quality_key=row.quality_key,
            explanation_observed_at=row.explanation_observed_at,
            probability_change_abs=row.probability_change_abs,
            explanation_completeness_score=row.explanation_completeness_score,
            evidence_linkage_score=row.evidence_linkage_score,
            cost_context_coverage_score=row.cost_context_coverage_score,
            settlement_rule_clarity_score=row.settlement_rule_clarity_score,
            quality_score=row.quality_score,
            deficiency_score=row.deficiency_score,
            status=row.status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_sort_key(
    row: ResearchStrategyProbabilityChangeExplanationQualityRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        -STATUS_SEVERITY[row.status],
        -row.deficiency_score,
        -row.probability_change_abs,
        row.quality_key,
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return BLOCK_STATUS
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _report_status(
    rows: tuple[ResearchStrategyProbabilityChangeExplanationQualityRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchStrategyProbabilityChangeExplanationQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("probability_change_explanation_quality_missing_inputs",)
    seen: set[str] = set()
    codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in seen:
                seen.add(reason_code)
    codes.extend(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen)
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyProbabilityChangeExplanationQualityReasonCodeCount, ...]:
    counts = Counter(reason_codes)
    return tuple(
        ResearchStrategyProbabilityChangeExplanationQualityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _status_count(
    rows: tuple[ResearchStrategyProbabilityChangeExplanationQualityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(sum(values, ZERO) / Decimal(len(values)))


def _validate_row_consistency(
    row: ResearchStrategyProbabilityChangeExplanationQualityRow,
) -> None:
    expected_quality = _clamp_probability(
        (
            row.explanation_completeness_score
            + row.evidence_linkage_score
            + row.cost_context_coverage_score
            + row.settlement_rule_clarity_score
        )
        / FOUR,
    )
    if row.quality_score != expected_quality:
        raise ValueError("quality_score must match row fields")
    if row.deficiency_score != _clamp_probability(ONE - row.quality_score):
        raise ValueError("deficiency_score must match quality_score")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == PASS_STATUS and row.reason_codes != (
        "probability_change_explanation_quality_pass",
    ):
        raise ValueError("pass rows must expose only pass reason code")


def _validate_report_consistency(
    report: ResearchStrategyProbabilityChangeExplanationQualityReport,
) -> None:
    rows = report.rows
    if report.quality_count != _decimal_count(len(rows)):
        raise ValueError("quality_count must match rows")
    if report.pass_count != _status_count(rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    if report.average_probability_change_abs != _average(
        tuple(row.probability_change_abs for row in rows),
    ):
        raise ValueError("average_probability_change_abs must match rows")
    if report.average_quality_score != _average(tuple(row.quality_score for row in rows)):
        raise ValueError("average_quality_score must match rows")
    if report.max_deficiency_score != max(
        (row.deficiency_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_deficiency_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_inputs(
    value: Sequence[ResearchStrategyProbabilityChangeExplanationQualityInput],
) -> tuple[ResearchStrategyProbabilityChangeExplanationQualityInput, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("inputs must be a sequence")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyProbabilityChangeExplanationQualityInput:
            raise ValueError(
                "inputs must contain explanation quality input values",
            )
        _require_hard_flags("input", row)
        if row.quality_key in seen:
            raise ValueError("quality_key values must not repeat")
        seen.add(row.quality_key)
    return rows


def _normalize_rows(
    value: Sequence[ResearchStrategyProbabilityChangeExplanationQualityRow],
) -> tuple[ResearchStrategyProbabilityChangeExplanationQualityRow, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("rows must be a sequence")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategyProbabilityChangeExplanationQualityRow:
            raise ValueError("rows must contain explanation quality row values")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    if tuple(row.rank for row in rows) != tuple(
        _decimal_count(index) for index in range(1, len(rows) + 1)
    ):
        raise ValueError("rows must use sequential ranks")
    return rows


def _normalize_reason_code_counts(
    value: Sequence[ResearchStrategyProbabilityChangeExplanationQualityReasonCodeCount],
) -> tuple[ResearchStrategyProbabilityChangeExplanationQualityReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    rows = tuple(value)
    seen: set[str] = set()
    expected = tuple(sorted(rows, key=lambda row: _reason_code_rank(row.reason_code)))
    if rows != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    for row in rows:
        if type(row) is not ResearchStrategyProbabilityChangeExplanationQualityReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not repeat")
        seen.add(row.reason_code)
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in value:
        reason_code = _require_reason_code(reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not repeat")
        seen.add(reason_code)
        normalized.append(reason_code)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    expected = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen
    )
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return tuple(normalized)


def _require_reason_code(value: object) -> str:
    if type(value) is not str:
        raise ValueError("reason_code must be a string")
    if not PUBLIC_KEY_RE.fullmatch(value):
        raise ValueError("reason_code must be a public key")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError("reason_code is not supported")
    return value


def _reason_code_rank(reason_code: str) -> int:
    return REASON_CODE_SEQUENCE.index(reason_code)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_key(field_name: str, value: object) -> str:
    value = _require_public_string(field_name, value)
    if not PUBLIC_KEY_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public key")
    _reject_blocked_text(field_name, value)
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    _reject_blocked_text(field_name, value)
    return value


def _reject_blocked_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    for parts in _BLOCKED_TEXT_PARTS:
        if "".join(parts) in lowered:
            raise ValueError(f"{field_name} contains restricted text")


def _require_status(value: object) -> str:
    if type(value) is not str:
        raise ValueError("status must be a string")
    if value not in STATUSES:
        raise ValueError("status must be pass, watch, or block")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamp_probability(value: Decimal) -> Decimal:
    value = _quantize(value)
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _require_less_than(
    left_name: str,
    left: Decimal,
    right_name: str,
    right: Decimal,
) -> None:
    if left >= right:
        raise ValueError(f"{left_name} must be less than {right_name}")


def _require_falling_threshold(label: str, watch: Decimal, block: Decimal) -> None:
    if watch <= block:
        raise ValueError(f"{label} watch threshold must exceed block threshold")


def _require_digest_or_empty(value: object) -> str:
    if type(value) is not str:
        raise ValueError("public_payload_digest must be a string")
    if value and not DIGEST_RE.fullmatch(value):
        raise ValueError("public_payload_digest must be a SHA-256 hex digest")
    return value


def _public_digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _report_values_without_digest(
    report: ResearchStrategyProbabilityChangeExplanationQualityReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("public_payload_digest", None)
    return values


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value type: {type(value).__name__}")
