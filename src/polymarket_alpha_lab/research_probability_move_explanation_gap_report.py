"""Pure report-only probability move explanation gap report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_PROBABILITY_MOVE_EXPLANATION_GAP_CONFIG_VERSION = (
    "research-probability-move-explanation-gap-v0"
)

__all__ = (
    "DEFAULT_RESEARCH_PROBABILITY_MOVE_EXPLANATION_GAP_CONFIG_VERSION",
    "ResearchProbabilityMoveExplanationGapConfig",
    "ResearchProbabilityMoveExplanationGapInput",
    "ResearchProbabilityMoveExplanationGapReport",
    "ResearchProbabilityMoveExplanationGapRow",
    "build_research_probability_move_explanation_gap_report",
    "research_probability_move_explanation_gap_digest",
    "research_probability_move_explanation_gap_digest_payload",
    "research_probability_move_explanation_gap_report_to_payload",
)


STATUSES = frozenset(("pass", "watch", "block"))
STATUS_SEVERITY = {"block": 2, "watch": 1, "pass": 0}
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64)
PUBLIC_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "auth",
        "buy",
        "candidate",
        "condition",
        "database",
        "dsn",
        "event",
        "identifier",
        "live",
        "market",
        "order",
        "position",
        "question",
        "raw",
        "recommend",
        "sell",
        "sizing",
        "slug",
        "source",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
    ),
)

REASON_CODE_SEQUENCE = (
    "probability_move_explanation_gap_missing_inputs",
    "probability_move_explanation_gap_block",
    "probability_move_explanation_gap_watch",
    "probability_move_explanation_gap_pass",
    "probability_move_without_fresh_explanation_block",
    "probability_move_without_fresh_explanation_watch",
    "catalyst_pressure_unexplained_block",
    "catalyst_pressure_unexplained_watch",
    "liquidity_stress_unexplained_block",
    "liquidity_stress_unexplained_watch",
    "source_contradiction_unresolved_block",
    "source_contradiction_unresolved_watch",
)

PASS_ACTION = "maintain_public_explanation_monitoring"
WATCH_ACTION = "refresh_public_aggregate_explanations"
BLOCK_ACTION = "withhold_until_public_explanation_gap_closes"


@dataclass(frozen=True)
class ResearchProbabilityMoveExplanationGapConfig:
    config_version: str = DEFAULT_RESEARCH_PROBABILITY_MOVE_EXPLANATION_GAP_CONFIG_VERSION
    watch_large_move_threshold: Decimal = Decimal("0.075000")
    block_large_move_threshold: Decimal = Decimal("0.150000")
    watch_stale_explanation_ratio: Decimal = Decimal("0.400000")
    block_stale_explanation_ratio: Decimal = Decimal("0.800000")
    catalyst_pressure_watch_threshold: Decimal = Decimal("0.500000")
    catalyst_pressure_block_threshold: Decimal = Decimal("0.800000")
    liquidity_stress_watch_threshold: Decimal = Decimal("0.400000")
    liquidity_stress_block_threshold: Decimal = Decimal("0.800000")
    source_contradiction_watch_threshold: Decimal = Decimal("0.350000")
    source_contradiction_block_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchProbabilityMoveExplanationGapConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_large_move_threshold",
            "block_large_move_threshold",
            "watch_stale_explanation_ratio",
            "block_stale_explanation_ratio",
            "catalyst_pressure_watch_threshold",
            "catalyst_pressure_block_threshold",
            "liquidity_stress_watch_threshold",
            "liquidity_stress_block_threshold",
            "source_contradiction_watch_threshold",
            "source_contradiction_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "watch_large_move_threshold",
            self.watch_large_move_threshold,
            "block_large_move_threshold",
            self.block_large_move_threshold,
        )
        _require_less_than(
            "watch_stale_explanation_ratio",
            self.watch_stale_explanation_ratio,
            "block_stale_explanation_ratio",
            self.block_stale_explanation_ratio,
        )
        _require_less_than(
            "catalyst_pressure_watch_threshold",
            self.catalyst_pressure_watch_threshold,
            "catalyst_pressure_block_threshold",
            self.catalyst_pressure_block_threshold,
        )
        _require_less_than(
            "liquidity_stress_watch_threshold",
            self.liquidity_stress_watch_threshold,
            "liquidity_stress_block_threshold",
            self.liquidity_stress_block_threshold,
        )
        _require_less_than(
            "source_contradiction_watch_threshold",
            self.source_contradiction_watch_threshold,
            "source_contradiction_block_threshold",
            self.source_contradiction_block_threshold,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchProbabilityMoveExplanationGapInput:
    gap_key: str
    probability_move_abs: Decimal
    fresh_explanation_ratio: Decimal
    catalyst_pressure_score: Decimal
    liquidity_stress_score: Decimal
    source_contradiction_score: Decimal
    explanation_count: Decimal
    stale_explanation_count: Decimal
    observed_at: datetime
    public_context: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchProbabilityMoveExplanationGapInput, "input")
        _require_public_token("gap_key", self.gap_key)
        for field_name in (
            "probability_move_abs",
            "fresh_explanation_ratio",
            "catalyst_pressure_score",
            "liquidity_stress_score",
            "source_contradiction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("explanation_count", "stale_explanation_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_explanation_count > self.explanation_count:
            raise ValueError("stale_explanation_count must not exceed explanation_count")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_public_string("public_context", self.public_context)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchProbabilityMoveExplanationGapRow:
    gap_key: str
    observed_at: datetime
    probability_move_abs: Decimal
    move_pressure_score: Decimal
    fresh_explanation_ratio: Decimal
    stale_explanation_ratio: Decimal
    catalyst_pressure_score: Decimal
    liquidity_stress_score: Decimal
    source_contradiction_score: Decimal
    explanation_count: Decimal
    stale_explanation_count: Decimal
    gap_score: Decimal
    status: str
    explanation_action: str
    reason_codes: tuple[str, ...]
    public_context: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchProbabilityMoveExplanationGapRow, "row")
        _require_public_token("gap_key", self.gap_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "probability_move_abs",
            "move_pressure_score",
            "fresh_explanation_ratio",
            "stale_explanation_ratio",
            "catalyst_pressure_score",
            "liquidity_stress_score",
            "source_contradiction_score",
            "gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("explanation_count", "stale_explanation_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_explanation_count > self.explanation_count:
            raise ValueError("stale_explanation_count must not exceed explanation_count")
        _require_status(self.status)
        _require_action(self.explanation_action)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_public_string("public_context", self.public_context)
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchProbabilityMoveExplanationGapReport:
    generated_at: datetime
    config_version: str
    status: str
    gap_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    large_move_count: Decimal
    stale_evidence_count: Decimal
    catalyst_pressure_count: Decimal
    liquidity_stress_count: Decimal
    source_contradiction_count: Decimal
    average_gap_score: Decimal
    max_gap_score: Decimal
    rows: tuple[ResearchProbabilityMoveExplanationGapRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    reason_codes: tuple[str, ...]
    public_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchProbabilityMoveExplanationGapReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status(self.status)
        for field_name in (
            "gap_count",
            "pass_count",
            "watch_count",
            "block_count",
            "large_move_count",
            "stale_evidence_count",
            "catalyst_pressure_count",
            "liquidity_stress_count",
            "source_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_gap_score", "max_gap_score"):
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
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_digest(self.public_digest)
        _require_hard_flags("report", self)
        expected_digest = _public_digest_from_values(_report_values_without_digest(self))
        if self.public_digest != expected_digest:
            raise ValueError("public_digest must match report payload")
        _validate_report_consistency(self)


def build_research_probability_move_explanation_gap_report(
    inputs: Sequence[ResearchProbabilityMoveExplanationGapInput],
    *,
    generated_at: datetime,
    config: ResearchProbabilityMoveExplanationGapConfig | None = None,
) -> ResearchProbabilityMoveExplanationGapReport:
    if config is None:
        config = ResearchProbabilityMoveExplanationGapConfig()
    if type(config) is not ResearchProbabilityMoveExplanationGapConfig:
        raise ValueError("config must be ResearchProbabilityMoveExplanationGapConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(_row_from_input(item, config) for item in normalized_inputs)
    rows = _normalize_rows(rows)
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(reason_codes)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "gap_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "large_move_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.probability_move_abs >= config.watch_large_move_threshold
            ),
        ),
        "stale_evidence_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.stale_explanation_ratio >= config.watch_stale_explanation_ratio
            ),
        ),
        "catalyst_pressure_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.catalyst_pressure_score >= config.catalyst_pressure_watch_threshold
            ),
        ),
        "liquidity_stress_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.liquidity_stress_score >= config.liquidity_stress_watch_threshold
            ),
        ),
        "source_contradiction_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.source_contradiction_score
                >= config.source_contradiction_watch_threshold
            ),
        ),
        "average_gap_score": _average(tuple(row.gap_score for row in rows)),
        "max_gap_score": max((row.gap_score for row in rows), default=ZERO),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchProbabilityMoveExplanationGapReport(
        **values,
        public_digest=_public_digest_from_values(values),
    )


def research_probability_move_explanation_gap_report_to_payload(
    report: ResearchProbabilityMoveExplanationGapReport,
) -> dict[str, Any]:
    if type(report) is not ResearchProbabilityMoveExplanationGapReport:
        raise ValueError("report must be ResearchProbabilityMoveExplanationGapReport")
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def research_probability_move_explanation_gap_digest_payload(
    report: ResearchProbabilityMoveExplanationGapReport,
) -> dict[str, Any]:
    if type(report) is not ResearchProbabilityMoveExplanationGapReport:
        raise ValueError("report must be ResearchProbabilityMoveExplanationGapReport")
    payload = _json_ready(_report_values_without_digest(report))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    return payload


def research_probability_move_explanation_gap_digest(
    report: ResearchProbabilityMoveExplanationGapReport,
) -> str:
    return _public_digest_from_values(_report_values_without_digest(report))


def _row_from_input(
    item: ResearchProbabilityMoveExplanationGapInput,
    config: ResearchProbabilityMoveExplanationGapConfig,
) -> ResearchProbabilityMoveExplanationGapRow:
    stale_ratio = _stale_explanation_ratio(item)
    move_pressure = _move_pressure_score(item.probability_move_abs, config)
    gap_score = _gap_score(
        move_pressure=move_pressure,
        stale_explanation_ratio=stale_ratio,
        catalyst_pressure_score=item.catalyst_pressure_score,
        liquidity_stress_score=item.liquidity_stress_score,
        source_contradiction_score=item.source_contradiction_score,
    )
    status = _row_status(item, stale_ratio, config)
    return ResearchProbabilityMoveExplanationGapRow(
        gap_key=item.gap_key,
        observed_at=item.observed_at,
        probability_move_abs=item.probability_move_abs,
        move_pressure_score=move_pressure,
        fresh_explanation_ratio=item.fresh_explanation_ratio,
        stale_explanation_ratio=stale_ratio,
        catalyst_pressure_score=item.catalyst_pressure_score,
        liquidity_stress_score=item.liquidity_stress_score,
        source_contradiction_score=item.source_contradiction_score,
        explanation_count=item.explanation_count,
        stale_explanation_count=item.stale_explanation_count,
        gap_score=gap_score,
        status=status,
        explanation_action=_explanation_action(status),
        reason_codes=_row_reason_codes(item, stale_ratio, status, config),
        public_context=item.public_context,
    )


def _stale_explanation_ratio(
    item: ResearchProbabilityMoveExplanationGapInput,
) -> Decimal:
    freshness_gap = _clamp_probability(ONE - item.fresh_explanation_ratio)
    if item.explanation_count == ZERO:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        stale_ratio = item.stale_explanation_count / item.explanation_count
    return max(freshness_gap, _clamp_probability(stale_ratio))


def _move_pressure_score(
    probability_move_abs: Decimal,
    config: ResearchProbabilityMoveExplanationGapConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(probability_move_abs / config.block_large_move_threshold)


def _gap_score(
    *,
    move_pressure: Decimal,
    stale_explanation_ratio: Decimal,
    catalyst_pressure_score: Decimal,
    liquidity_stress_score: Decimal,
    source_contradiction_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(
            (
                move_pressure
                + stale_explanation_ratio
                + catalyst_pressure_score
                + liquidity_stress_score
                + source_contradiction_score
            )
            / FIVE,
        )


def _row_status(
    item: ResearchProbabilityMoveExplanationGapInput,
    stale_ratio: Decimal,
    config: ResearchProbabilityMoveExplanationGapConfig,
) -> str:
    if (
        _probability_move_without_fresh_explanation_block(item, stale_ratio, config)
        or item.catalyst_pressure_score >= config.catalyst_pressure_block_threshold
        or item.liquidity_stress_score >= config.liquidity_stress_block_threshold
        or item.source_contradiction_score
        >= config.source_contradiction_block_threshold
    ):
        return "block"
    if (
        _probability_move_without_fresh_explanation_watch(item, stale_ratio, config)
        or item.catalyst_pressure_score >= config.catalyst_pressure_watch_threshold
        or item.liquidity_stress_score >= config.liquidity_stress_watch_threshold
        or item.source_contradiction_score
        >= config.source_contradiction_watch_threshold
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchProbabilityMoveExplanationGapInput,
    stale_ratio: Decimal,
    status: str,
    config: ResearchProbabilityMoveExplanationGapConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"probability_move_explanation_gap_{status}"]
    if _probability_move_without_fresh_explanation_block(item, stale_ratio, config):
        reason_codes.append("probability_move_without_fresh_explanation_block")
    elif _probability_move_without_fresh_explanation_watch(item, stale_ratio, config):
        reason_codes.append("probability_move_without_fresh_explanation_watch")
    if item.catalyst_pressure_score >= config.catalyst_pressure_block_threshold:
        reason_codes.append("catalyst_pressure_unexplained_block")
    elif item.catalyst_pressure_score >= config.catalyst_pressure_watch_threshold:
        reason_codes.append("catalyst_pressure_unexplained_watch")
    if item.liquidity_stress_score >= config.liquidity_stress_block_threshold:
        reason_codes.append("liquidity_stress_unexplained_block")
    elif item.liquidity_stress_score >= config.liquidity_stress_watch_threshold:
        reason_codes.append("liquidity_stress_unexplained_watch")
    if item.source_contradiction_score >= config.source_contradiction_block_threshold:
        reason_codes.append("source_contradiction_unresolved_block")
    elif item.source_contradiction_score >= config.source_contradiction_watch_threshold:
        reason_codes.append("source_contradiction_unresolved_watch")
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _probability_move_without_fresh_explanation_block(
    item: ResearchProbabilityMoveExplanationGapInput,
    stale_ratio: Decimal,
    config: ResearchProbabilityMoveExplanationGapConfig,
) -> bool:
    return (
        item.probability_move_abs >= config.block_large_move_threshold
        and stale_ratio >= config.block_stale_explanation_ratio
    )


def _probability_move_without_fresh_explanation_watch(
    item: ResearchProbabilityMoveExplanationGapInput,
    stale_ratio: Decimal,
    config: ResearchProbabilityMoveExplanationGapConfig,
) -> bool:
    return (
        item.probability_move_abs >= config.watch_large_move_threshold
        and stale_ratio >= config.watch_stale_explanation_ratio
    )


def _explanation_action(status: str) -> str:
    if status == "block":
        return BLOCK_ACTION
    if status == "watch":
        return WATCH_ACTION
    return PASS_ACTION


def _report_status(rows: tuple[ResearchProbabilityMoveExplanationGapRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchProbabilityMoveExplanationGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("probability_move_explanation_gap_missing_inputs",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts = Counter(reason_codes)
    return tuple(
        (reason_code, _decimal_count(counts[reason_code]))
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _status_count(
    rows: tuple[ResearchProbabilityMoveExplanationGapRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row_consistency(row: ResearchProbabilityMoveExplanationGapRow) -> None:
    if row.status == "pass" and row.reason_codes != (
        "probability_move_explanation_gap_pass",
    ):
        raise ValueError("pass rows must expose only pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must expose watch reason codes")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must expose block reason codes")
    if row.explanation_action != _explanation_action(row.status):
        raise ValueError("explanation_action must match status")


def _validate_report_consistency(
    report: ResearchProbabilityMoveExplanationGapReport,
) -> None:
    if report.gap_count != _decimal_count(len(report.rows)):
        raise ValueError("gap_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_gap_score != _average(tuple(row.gap_score for row in report.rows)):
        raise ValueError("average_gap_score must match rows")
    if report.max_gap_score != max((row.gap_score for row in report.rows), default=ZERO):
        raise ValueError("max_gap_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_inputs(
    inputs: Sequence[ResearchProbabilityMoveExplanationGapInput],
) -> tuple[ResearchProbabilityMoveExplanationGapInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized: list[ResearchProbabilityMoveExplanationGapInput] = []
    for item in inputs:
        if type(item) is not ResearchProbabilityMoveExplanationGapInput:
            raise ValueError(
                "inputs must contain ResearchProbabilityMoveExplanationGapInput",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.gap_key))


def _normalize_rows(
    rows: Sequence[ResearchProbabilityMoveExplanationGapRow],
) -> tuple[ResearchProbabilityMoveExplanationGapRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchProbabilityMoveExplanationGapRow] = []
    for row in rows:
        if type(row) is not ResearchProbabilityMoveExplanationGapRow:
            raise ValueError("rows must contain ResearchProbabilityMoveExplanationGapRow")
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                -STATUS_SEVERITY[row.status],
                -row.gap_score,
                row.gap_key,
            ),
        ),
    )


def _normalize_reason_code_counts(
    value: Sequence[tuple[str, Decimal]],
) -> tuple[tuple[str, Decimal], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[tuple[str, Decimal]] = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts entries must be tuples")
        reason_code, count = item
        reason_code = _require_reason_code(reason_code)
        normalized.append(
            (reason_code, _require_nonnegative_decimal("reason_code_count", count)),
        )
    return tuple(
        (reason_code, count)
        for reason_code in REASON_CODE_SEQUENCE
        for existing_code, count in normalized
        if reason_code == existing_code
    )


def _normalize_reason_codes(
    value: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("reason_codes must be a sequence")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        reason_code = _require_reason_code(reason_code)
        if reason_code not in seen:
            seen.add(reason_code)
            normalized.append(reason_code)
    if not allow_empty and not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _require_reason_code(value: object) -> str:
    if type(value) is not str:
        raise ValueError("reason_code must be a string")
    if not PUBLIC_TOKEN_RE.fullmatch(value):
        raise ValueError("reason_code must be a public token")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError("reason_code must be supported")
    return value


def _require_status(value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError("status must be pass, watch, or block")


def _require_action(value: object) -> None:
    if type(value) is not str or value not in (PASS_ACTION, WATCH_ACTION, BLOCK_ACTION):
        raise ValueError("explanation_action must be supported")


def _require_public_token(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_TOKEN_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public token")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonblank public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_text(field_name, value)
    return value


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} must not contain unsafe public text")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe public text")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_less_than(
    lower_name: str,
    lower_value: Decimal,
    upper_name: str,
    upper_value: Decimal,
) -> None:
    if lower_value >= upper_value:
        raise ValueError(f"{upper_name} must be greater than {lower_name}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _clamp_probability(value: Decimal) -> Decimal:
    quantized = _quantize(value)
    if quantized < ZERO:
        return ZERO
    if quantized > ONE:
        return ONE
    return quantized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _require_digest(value: object) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError("public_digest must be a lowercase sha256 digest")


def _report_values_without_digest(
    report: ResearchProbabilityMoveExplanationGapReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("public_digest", None)
    return values


def _public_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        return _json_mapping_ready(value)
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _json_mapping_ready(value: Mapping[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        _reject_unsafe_payload_key(key)
        ready[key] = _json_ready(item)
    return ready


def _reject_unsafe_payload_key(key: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in ("wallet", "auth", "order", "trade")):
        raise ValueError("payload must not expose unsafe execution fields")


for _class in (
    ResearchProbabilityMoveExplanationGapConfig,
    ResearchProbabilityMoveExplanationGapInput,
    ResearchProbabilityMoveExplanationGapRow,
    ResearchProbabilityMoveExplanationGapReport,
):
    for _field in fields(_class):
        _reject_unsafe_payload_key(_field.name)
