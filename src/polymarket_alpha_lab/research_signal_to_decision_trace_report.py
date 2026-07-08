"""Pure report reducer for research signal-to-decision trace audits."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_SIGNAL_TO_DECISION_TRACE_REPORT_CONFIG_VERSION",
    "ResearchSignalToDecisionTraceConfig",
    "ResearchSignalToDecisionTraceInputRow",
    "ResearchSignalToDecisionTraceReasonCodeCount",
    "ResearchSignalToDecisionTraceReport",
    "ResearchSignalToDecisionTraceRow",
    "build_research_signal_to_decision_trace_report",
    "research_signal_to_decision_trace_digest",
    "research_signal_to_decision_trace_report_payload",
)


DEFAULT_RESEARCH_SIGNAL_TO_DECISION_TRACE_REPORT_CONFIG_VERSION = (
    "research-signal-to-decision-trace-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_WEIGHT = {
    STATUS_BLOCK: Decimal("2.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("0.000000"),
}

REASON_PREFIX = "research_signal_to_decision_trace_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
COST_DRAG_BLOCK_REASON = f"{REASON_PREFIX}cost_drag_block"
COST_DRAG_WATCH_REASON = f"{REASON_PREFIX}cost_drag_watch"
EVIDENCE_MISSING_BLOCK_REASON = f"{REASON_PREFIX}evidence_missing_block"
EVIDENCE_GAP_WATCH_REASON = f"{REASON_PREFIX}evidence_gap_watch"
EVIDENCE_QUALITY_BLOCK_REASON = f"{REASON_PREFIX}evidence_quality_block"
EVIDENCE_QUALITY_WATCH_REASON = f"{REASON_PREFIX}evidence_quality_watch"
HUMAN_REVIEW_BLOCK_REASON = f"{REASON_PREFIX}human_review_block"
MODEL_DISAGREEMENT_BLOCK_REASON = f"{REASON_PREFIX}model_disagreement_block"
MODEL_DISAGREEMENT_WATCH_REASON = f"{REASON_PREFIX}model_disagreement_watch"
MODEL_MISSING_BLOCK_REASON = f"{REASON_PREFIX}model_missing_block"
MODEL_GAP_WATCH_REASON = f"{REASON_PREFIX}model_gap_watch"
SIGNAL_AGE_WATCH_REASON = f"{REASON_PREFIX}signal_age_watch"
SIGNAL_STRENGTH_BLOCK_REASON = f"{REASON_PREFIX}signal_strength_block"
SIGNAL_STRENGTH_WATCH_REASON = f"{REASON_PREFIX}signal_strength_watch"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    COST_DRAG_BLOCK_REASON,
    COST_DRAG_WATCH_REASON,
    EVIDENCE_MISSING_BLOCK_REASON,
    EVIDENCE_GAP_WATCH_REASON,
    EVIDENCE_QUALITY_BLOCK_REASON,
    EVIDENCE_QUALITY_WATCH_REASON,
    HUMAN_REVIEW_BLOCK_REASON,
    MODEL_DISAGREEMENT_BLOCK_REASON,
    MODEL_DISAGREEMENT_WATCH_REASON,
    MODEL_MISSING_BLOCK_REASON,
    MODEL_GAP_WATCH_REASON,
    SIGNAL_AGE_WATCH_REASON,
    SIGNAL_STRENGTH_BLOCK_REASON,
    SIGNAL_STRENGTH_WATCH_REASON,
    PASS_REASON,
)
REASON_CODE_INDEX = {
    reason_code: index for index, reason_code in enumerate(REASON_CODE_SEQUENCE)
}

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "\x63andidate",
    "\x6darket",
    "\x73lug",
    "\x71uestion",
    "\x73ource",
    "\x72ef",
    "\x75rl",
    "\x74ext",
    "\x64sn",
    "\x74able",
    "\x74oken",
    "\x61uth",
    "\x77allet",
    "\x6frder",
    "\x74rade",
    "\x74rading",
    "\x70osition",
    "\x62uy",
    "\x73ell",
    "\x72ecommendation",
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
class ResearchSignalToDecisionTraceConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_SIGNAL_TO_DECISION_TRACE_REPORT_CONFIG_VERSION
    max_signal_age_seconds: Decimal = Decimal("86400.000000")
    min_signal_strength: Decimal = Decimal("0.600000")
    watch_signal_strength: Decimal = Decimal("0.500000")
    min_evidence_count: Decimal = Decimal("2.000000")
    min_evidence_quality: Decimal = Decimal("0.700000")
    watch_evidence_quality: Decimal = Decimal("0.500000")
    min_model_count: Decimal = Decimal("2.000000")
    max_model_disagreement_watch: Decimal = Decimal("0.200000")
    max_model_disagreement_block: Decimal = Decimal("0.400000")
    max_cost_drag_watch: Decimal = Decimal("0.020000")
    max_cost_drag_block: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSignalToDecisionTraceConfig, "config")
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_signal_age_seconds",
            _require_nonnegative_decimal(
                "max_signal_age_seconds",
                self.max_signal_age_seconds,
            ),
        )
        for field_name in ("min_evidence_count", "min_model_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_signal_strength",
            "watch_signal_strength",
            "min_evidence_quality",
            "watch_evidence_quality",
            "max_model_disagreement_watch",
            "max_model_disagreement_block",
            "max_cost_drag_watch",
            "max_cost_drag_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_signal_strength > self.min_signal_strength:
            raise ValueError("watch_signal_strength must not exceed min_signal_strength")
        if self.watch_evidence_quality > self.min_evidence_quality:
            raise ValueError("watch_evidence_quality must not exceed min_evidence_quality")
        if self.max_model_disagreement_watch > self.max_model_disagreement_block:
            raise ValueError(
                "max_model_disagreement_watch must not exceed paired limit",
            )
        if self.max_cost_drag_watch > self.max_cost_drag_block:
            raise ValueError("max_cost_drag_watch must not exceed paired limit")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSignalToDecisionTraceInputRow(_FinalPublicDataclass):
    trace_key: str
    signal_label: str
    observed_at: datetime
    signal_strength: Decimal
    evidence_count: Decimal
    evidence_quality: Decimal
    model_count: Decimal
    model_disagreement: Decimal
    cost_drag: Decimal
    human_review_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSignalToDecisionTraceInputRow, "input row")
        _require_public_string("trace_key", self.trace_key)
        _require_public_string("signal_label", self.signal_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("evidence_count", "model_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "signal_strength",
            "evidence_quality",
            "model_disagreement",
            "cost_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.human_review_ready) is not bool:
            raise ValueError("human_review_ready must be a bool")
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchSignalToDecisionTraceRow(_FinalPublicDataclass):
    trace_key: str
    signal_label: str
    observed_at: datetime
    signal_age_seconds: Decimal
    signal_strength: Decimal
    evidence_count: Decimal
    evidence_quality: Decimal
    model_count: Decimal
    model_disagreement: Decimal
    cost_drag: Decimal
    audit_score: Decimal
    decision_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSignalToDecisionTraceRow, "row")
        _require_public_string("trace_key", self.trace_key)
        _require_public_string("signal_label", self.signal_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "signal_age_seconds",
            _require_nonnegative_decimal("signal_age_seconds", self.signal_age_seconds),
        )
        for field_name in ("evidence_count", "model_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "signal_strength",
            "evidence_quality",
            "model_disagreement",
            "cost_drag",
            "audit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("decision_status", self.decision_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSignalToDecisionTraceReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    trace_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSignalToDecisionTraceReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "trace_ratio",
            _require_ratio_decimal("trace_ratio", self.trace_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchSignalToDecisionTraceReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    trace_count: Decimal
    pass_trace_count: Decimal
    watch_trace_count: Decimal
    block_trace_count: Decimal
    evidence_gap_count: Decimal
    model_disagreement_count: Decimal
    cost_drag_count: Decimal
    human_review_block_count: Decimal
    average_audit_score: Decimal
    minimum_audit_score: Decimal
    rows: tuple[ResearchSignalToDecisionTraceRow, ...]
    reason_code_counts: tuple[ResearchSignalToDecisionTraceReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSignalToDecisionTraceReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("report_status", self.report_status)
        for field_name in (
            "trace_count",
            "pass_trace_count",
            "watch_trace_count",
            "block_trace_count",
            "evidence_gap_count",
            "model_disagreement_count",
            "cost_drag_count",
            "human_review_block_count",
            "average_audit_score",
            "minimum_audit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchSignalToDecisionTraceConfig,
    ResearchSignalToDecisionTraceInputRow,
    ResearchSignalToDecisionTraceReasonCodeCount,
    ResearchSignalToDecisionTraceReport,
    ResearchSignalToDecisionTraceRow,
)


def build_research_signal_to_decision_trace_report(
    input_rows: list[ResearchSignalToDecisionTraceInputRow]
    | tuple[ResearchSignalToDecisionTraceInputRow, ...],
    *,
    config: ResearchSignalToDecisionTraceConfig | None = None,
    generated_at: datetime,
) -> ResearchSignalToDecisionTraceReport:
    cfg = config or ResearchSignalToDecisionTraceConfig()
    if type(cfg) is not ResearchSignalToDecisionTraceConfig:
        raise ValueError("config must be a ResearchSignalToDecisionTraceConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows)
    built_rows = tuple(_build_row(row, config=cfg, generated_at=report_time) for row in rows)
    ranked_rows = tuple(sorted(built_rows, key=_row_sort_key))
    trace_count = _count(len(ranked_rows))
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            ResearchSignalToDecisionTraceReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                trace_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    report_status = _report_status(tuple(row.decision_status for row in ranked_rows))
    return ResearchSignalToDecisionTraceReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        report_status=report_status,
        trace_count=trace_count,
        pass_trace_count=_status_count(ranked_rows, STATUS_PASS),
        watch_trace_count=_status_count(ranked_rows, STATUS_WATCH),
        block_trace_count=_status_count(ranked_rows, STATUS_BLOCK),
        evidence_gap_count=_count(
            sum(1 for row in ranked_rows if _has_reason_prefix(row, "evidence_")),
        ),
        model_disagreement_count=_count(
            sum(
                1
                for row in ranked_rows
                if MODEL_DISAGREEMENT_BLOCK_REASON in row.reason_codes
                or MODEL_DISAGREEMENT_WATCH_REASON in row.reason_codes
            ),
        ),
        cost_drag_count=_count(
            sum(
                1
                for row in ranked_rows
                if COST_DRAG_BLOCK_REASON in row.reason_codes
                or COST_DRAG_WATCH_REASON in row.reason_codes
            ),
        ),
        human_review_block_count=_count(
            sum(1 for row in ranked_rows if HUMAN_REVIEW_BLOCK_REASON in row.reason_codes),
        ),
        average_audit_score=_ratio(
            _sum_decimal(row.audit_score for row in ranked_rows),
            trace_count,
        ),
        minimum_audit_score=min((row.audit_score for row in ranked_rows), default=ZERO),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_signal_to_decision_trace_report_payload(
    report: ResearchSignalToDecisionTraceReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSignalToDecisionTraceReport:
        raise ValueError("report must be a ResearchSignalToDecisionTraceReport")
    _reject_unsafe_public_payload("report", report)
    _require_payload_safe_value("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_signal_to_decision_trace_digest(
    report: ResearchSignalToDecisionTraceReport,
) -> dict[str, Any]:
    payload = research_signal_to_decision_trace_report_payload(report)
    return {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "report_status": payload["report_status"],
        "trace_count": payload["trace_count"],
        "pass_trace_count": payload["pass_trace_count"],
        "watch_trace_count": payload["watch_trace_count"],
        "block_trace_count": payload["block_trace_count"],
        "average_audit_score": payload["average_audit_score"],
        "minimum_audit_score": payload["minimum_audit_score"],
        "reason_codes": payload["reason_codes"],
        "rows": [
            {
                "trace_key": row["trace_key"],
                "signal_label": row["signal_label"],
                "decision_status": row["decision_status"],
                "audit_score": row["audit_score"],
                "reason_codes": row["reason_codes"],
            }
            for row in payload["rows"]
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


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


def _build_row(
    row: ResearchSignalToDecisionTraceInputRow,
    *,
    config: ResearchSignalToDecisionTraceConfig,
    generated_at: datetime,
) -> ResearchSignalToDecisionTraceRow:
    signal_age_seconds = _age_seconds(row.observed_at, generated_at)
    reason_codes = _row_reason_codes(
        row,
        config=config,
        signal_age_seconds=signal_age_seconds,
    )
    return ResearchSignalToDecisionTraceRow(
        trace_key=row.trace_key,
        signal_label=row.signal_label,
        observed_at=row.observed_at,
        signal_age_seconds=signal_age_seconds,
        signal_strength=row.signal_strength,
        evidence_count=row.evidence_count,
        evidence_quality=row.evidence_quality,
        model_count=row.model_count,
        model_disagreement=row.model_disagreement,
        cost_drag=row.cost_drag,
        audit_score=_audit_score(row, config=config),
        decision_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSignalToDecisionTraceInputRow,
    *,
    config: ResearchSignalToDecisionTraceConfig,
    signal_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if row.cost_drag >= config.max_cost_drag_block:
        reason_codes.append(COST_DRAG_BLOCK_REASON)
    elif row.cost_drag > config.max_cost_drag_watch:
        reason_codes.append(COST_DRAG_WATCH_REASON)
    if row.evidence_count == ZERO:
        reason_codes.append(EVIDENCE_MISSING_BLOCK_REASON)
    elif row.evidence_count < config.min_evidence_count:
        reason_codes.append(EVIDENCE_GAP_WATCH_REASON)
    if row.evidence_quality < config.watch_evidence_quality:
        reason_codes.append(EVIDENCE_QUALITY_BLOCK_REASON)
    elif row.evidence_quality < config.min_evidence_quality:
        reason_codes.append(EVIDENCE_QUALITY_WATCH_REASON)
    if row.human_review_ready is False:
        reason_codes.append(HUMAN_REVIEW_BLOCK_REASON)
    if row.model_disagreement >= config.max_model_disagreement_block:
        reason_codes.append(MODEL_DISAGREEMENT_BLOCK_REASON)
    elif row.model_disagreement > config.max_model_disagreement_watch:
        reason_codes.append(MODEL_DISAGREEMENT_WATCH_REASON)
    if row.model_count == ZERO:
        reason_codes.append(MODEL_MISSING_BLOCK_REASON)
    elif row.model_count < config.min_model_count:
        reason_codes.append(MODEL_GAP_WATCH_REASON)
    if signal_age_seconds > config.max_signal_age_seconds:
        reason_codes.append(SIGNAL_AGE_WATCH_REASON)
    if row.signal_strength < config.watch_signal_strength:
        reason_codes.append(SIGNAL_STRENGTH_BLOCK_REASON)
    elif row.signal_strength < config.min_signal_strength:
        reason_codes.append(SIGNAL_STRENGTH_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _audit_score(
    row: ResearchSignalToDecisionTraceInputRow,
    *,
    config: ResearchSignalToDecisionTraceConfig,
) -> Decimal:
    scores = (
        row.signal_strength,
        row.evidence_quality,
        _ratio(row.evidence_count, config.min_evidence_count),
        _ratio(row.model_count, config.min_model_count),
        _clamp_ratio(ONE - row.model_disagreement),
        _clamp_ratio(ONE - row.cost_drag),
        ONE if row.human_review_ready else ZERO,
    )
    return _ratio(_sum_decimal(scores), _count(len(scores)))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return STATUS_BLOCK
    if STATUS_BLOCK in statuses:
        return STATUS_BLOCK
    if STATUS_WATCH in statuses:
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchSignalToDecisionTraceRow, ...],
) -> tuple[ResearchSignalToDecisionTraceReasonCodeCount, ...]:
    if not rows:
        return ()
    row_count = _count(len(rows))
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchSignalToDecisionTraceReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            trace_ratio=_ratio(_count(count), row_count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (REASON_CODE_INDEX[item[0]], item[0]),
        )
    )


def _normalize_input_rows(
    rows: list[ResearchSignalToDecisionTraceInputRow]
    | tuple[ResearchSignalToDecisionTraceInputRow, ...],
) -> tuple[ResearchSignalToDecisionTraceInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    values = tuple(rows)
    seen_trace_keys: set[str] = set()
    for row in values:
        if type(row) is not ResearchSignalToDecisionTraceInputRow:
            raise ValueError(
                "input rows must contain ResearchSignalToDecisionTraceInputRow values",
            )
        _require_hard_flags("input row", row)
        if row.trace_key in seen_trace_keys:
            raise ValueError("input rows must not contain duplicate trace_key values")
        seen_trace_keys.add(row.trace_key)
    return values


def _normalize_rows(
    rows: tuple[ResearchSignalToDecisionTraceRow, ...],
) -> tuple[ResearchSignalToDecisionTraceRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_trace_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSignalToDecisionTraceRow:
            raise ValueError("rows must contain ResearchSignalToDecisionTraceRow values")
        _require_hard_flags("row", row)
        if row.trace_key in seen_trace_keys:
            raise ValueError("rows must not contain duplicate trace_key values")
        seen_trace_keys.add(row.trace_key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchSignalToDecisionTraceReasonCodeCount, ...],
) -> tuple[ResearchSignalToDecisionTraceReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSignalToDecisionTraceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSignalToDecisionTraceReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate values")
        seen_codes.add(row.reason_code)
    expected = tuple(
        sorted(rows, key=lambda item: (REASON_CODE_INDEX[item.reason_code], item.reason_code)),
    )
    if rows != expected:
        raise ValueError("reason_code_counts must use canonical sequence")
    return rows


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    normalized = tuple(
        sorted(reason_codes, key=lambda item: (REASON_CODE_INDEX[item], item)),
    )
    if reason_codes != normalized:
        raise ValueError("reason_codes must use canonical sequence")
    return normalized


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    expected = tuple(sorted(reason_codes, key=lambda item: REASON_CODE_INDEX[item]))
    if reason_codes != expected:
        raise ValueError("reason_codes must use canonical sequence")
    return reason_codes


def _validate_row(row: ResearchSignalToDecisionTraceRow) -> None:
    if PASS_REASON in row.reason_codes and len(row.reason_codes) != 1:
        raise ValueError("reason_codes must match row inputs")
    if row.decision_status != _row_status(row.reason_codes):
        raise ValueError("decision_status must match reason_codes")


def _validate_report(report: ResearchSignalToDecisionTraceReport) -> None:
    rows = report.rows
    if report.trace_count != _count(len(rows)):
        raise ValueError("trace_count must match rows")
    if report.pass_trace_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_trace_count must match rows")
    if report.watch_trace_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_trace_count must match rows")
    if report.block_trace_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_trace_count must match rows")
    if report.evidence_gap_count != _count(
        sum(1 for row in rows if _has_reason_prefix(row, "evidence_")),
    ):
        raise ValueError("evidence_gap_count must match rows")
    if report.model_disagreement_count != _count(
        sum(
            1
            for row in rows
            if MODEL_DISAGREEMENT_BLOCK_REASON in row.reason_codes
            or MODEL_DISAGREEMENT_WATCH_REASON in row.reason_codes
        ),
    ):
        raise ValueError("model_disagreement_count must match rows")
    if report.cost_drag_count != _count(
        sum(
            1
            for row in rows
            if COST_DRAG_BLOCK_REASON in row.reason_codes
            or COST_DRAG_WATCH_REASON in row.reason_codes
        ),
    ):
        raise ValueError("cost_drag_count must match rows")
    if report.human_review_block_count != _count(
        sum(1 for row in rows if HUMAN_REVIEW_BLOCK_REASON in row.reason_codes),
    ):
        raise ValueError("human_review_block_count must match rows")
    if report.average_audit_score != _ratio(
        _sum_decimal(row.audit_score for row in rows),
        report.trace_count,
    ):
        raise ValueError("average_audit_score must match rows")
    if report.minimum_audit_score != min(
        (row.audit_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("minimum_audit_score must match rows")
    if report.report_status != _report_status(tuple(row.decision_status for row in rows)):
        raise ValueError("report_status must match rows")
    expected_reason_code_counts = _reason_code_counts(rows)
    expected_reason_codes = tuple(row.reason_code for row in expected_reason_code_counts)
    if not rows:
        expected_reason_code_counts = (
            ResearchSignalToDecisionTraceReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                trace_ratio=ONE,
            ),
        )
        expected_reason_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")


def _has_reason_prefix(row: ResearchSignalToDecisionTraceRow, suffix: str) -> bool:
    return any(
        reason_code.startswith(f"{REASON_PREFIX}{suffix}")
        for reason_code in row.reason_codes
    )


def _row_sort_key(
    row: ResearchSignalToDecisionTraceRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.decision_status],
        row.audit_score,
        row.trace_key,
        row.signal_label,
    )


def _status_count(
    rows: tuple[ResearchSignalToDecisionTraceRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.decision_status == status))


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - observed_at).total_seconds()))
    age_seconds = _quantize(seconds)
    if age_seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return age_seconds


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_ratio(_quantize(numerator / denominator))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as decimal_context:
        decimal_context.prec = 64
        decimal_context.rounding = ROUND_HALF_EVEN
        return value.quantize(QUANTUM)


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        _rebuild_public_dataclass(label, value)
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            _require_public_string(label, value)
        return
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains unsupported value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed payload revalidation") from exc


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_safe_value("JSON value", value)
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (bool, str):
        return value
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, (list, dict, set)):
        raise ValueError("JSON value must come from public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains unsupported dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(path or label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return normalized


def _require_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_reason_code(field_name: str, value: str) -> None:
    if value not in REASON_CODE_INDEX:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
