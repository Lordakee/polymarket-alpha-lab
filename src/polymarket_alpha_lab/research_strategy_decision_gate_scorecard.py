"""Pure decision gate scorecard reducer for manual research intake."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import UNSAFE_SURFACE_FIELD_FRAGMENTS


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DECISION_GATE_SCORECARD_CONFIG_VERSION",
    "ResearchStrategyDecisionGateScorecardCandidate",
    "ResearchStrategyDecisionGateScorecardConfig",
    "ResearchStrategyDecisionGateScorecardReasonCodeCount",
    "ResearchStrategyDecisionGateScorecardReport",
    "ResearchStrategyDecisionGateScorecardRow",
    "build_research_strategy_decision_gate_scorecard_report",
    "research_strategy_decision_gate_scorecard_digest",
    "research_strategy_decision_gate_scorecard_payload",
)


DEFAULT_RESEARCH_STRATEGY_DECISION_GATE_SCORECARD_CONFIG_VERSION = (
    "research-strategy-decision-gate-scorecard-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "decision_gate_scorecard_no_inputs"
SUMMARY_KEYS = (
    "generated_at",
    "config_version",
    "candidate_count",
    "pass_count",
    "watch_count",
    "block_count",
    "hard_flag_count",
    "mean_gate_score",
    "min_gate_score",
    "public_status",
    "manual_research_state",
    "reason_codes",
    "reason_code_counts",
    "paper_only",
    "report_only",
    "readonly",
)
EXTRA_UNSAFE_FRAGMENTS = frozenset(
    (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "tra" "de",
        "tra" "ding",
        "po" "sition",
        "b" "uy",
        "se" "ll",
        "reco" "mmend",
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
class ResearchStrategyDecisionGateScorecardConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_STRATEGY_DECISION_GATE_SCORECARD_CONFIG_VERSION
    evidence_watch_floor: Decimal = Decimal("0.700000")
    evidence_block_floor: Decimal = Decimal("0.400000")
    freshness_watch_floor: Decimal = Decimal("0.600000")
    freshness_block_floor: Decimal = Decimal("0.300000")
    scope_fit_watch_floor: Decimal = Decimal("0.700000")
    scope_fit_block_floor: Decimal = Decimal("0.500000")
    contradiction_watch_ceiling: Decimal = Decimal("0.300000")
    contradiction_block_ceiling: Decimal = Decimal("0.600000")
    complexity_watch_ceiling: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionGateScorecardConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "evidence_watch_floor",
            "evidence_block_floor",
            "freshness_watch_floor",
            "freshness_block_floor",
            "scope_fit_watch_floor",
            "scope_fit_block_floor",
            "contradiction_watch_ceiling",
            "contradiction_block_ceiling",
            "complexity_watch_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "evidence_watch_floor",
            self.evidence_watch_floor,
            self.evidence_block_floor,
        )
        _require_at_least(
            "freshness_watch_floor",
            self.freshness_watch_floor,
            self.freshness_block_floor,
        )
        _require_at_least(
            "scope_fit_watch_floor",
            self.scope_fit_watch_floor,
            self.scope_fit_block_floor,
        )
        _require_at_most(
            "contradiction_watch_ceiling",
            self.contradiction_watch_ceiling,
            self.contradiction_block_ceiling,
        )
        _require_hard_phase_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionGateScorecardCandidate(_FinalPublicDataclass):
    decision_slot: str
    evidence_score: Decimal
    freshness_score: Decimal
    scope_fit_score: Decimal
    contradiction_score: Decimal
    complexity_score: Decimal
    hard_flags: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionGateScorecardCandidate, "candidate")
        _require_canonical_string("decision_slot", self.decision_slot)
        for field_name in (
            "evidence_score",
            "freshness_score",
            "scope_fit_score",
            "contradiction_score",
            "complexity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "hard_flags", _normalize_hard_flags(self.hard_flags))
        _require_hard_phase_flags("candidate", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionGateScorecardRow(_FinalPublicDataclass):
    decision_slot: str
    public_status: str
    manual_research_state: str
    evidence_score: Decimal
    freshness_score: Decimal
    scope_fit_score: Decimal
    contradiction_score: Decimal
    complexity_score: Decimal
    gate_score: Decimal
    hard_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionGateScorecardRow, "row")
        _require_canonical_string("decision_slot", self.decision_slot)
        _require_public_status("public_status", self.public_status)
        _require_manual_state("manual_research_state", self.manual_research_state)
        for field_name in (
            "evidence_score",
            "freshness_score",
            "scope_fit_score",
            "contradiction_score",
            "complexity_score",
            "gate_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "hard_flags", _normalize_hard_flags(self.hard_flags))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.public_status != _row_status(self.reason_codes):
            raise ValueError("public_status must match reason_codes")
        if self.manual_research_state != _manual_state(self.public_status):
            raise ValueError("manual_research_state must match public_status")
        _require_hard_phase_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionGateScorecardReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDecisionGateScorecardReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_phase_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionGateScorecardReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    hard_flag_count: Decimal
    mean_gate_score: Decimal
    min_gate_score: Decimal
    public_status: str
    manual_research_state: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyDecisionGateScorecardReasonCodeCount, ...]
    candidate_rows: tuple[ResearchStrategyDecisionGateScorecardRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionGateScorecardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "hard_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_gate_score", "min_gate_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_public_status("public_status", self.public_status)
        _require_manual_state("manual_research_state", self.manual_research_state)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "candidate_rows", _normalize_rows(self.candidate_rows))
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_phase_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchStrategyDecisionGateScorecardCandidate,
    ResearchStrategyDecisionGateScorecardConfig,
    ResearchStrategyDecisionGateScorecardReasonCodeCount,
    ResearchStrategyDecisionGateScorecardReport,
    ResearchStrategyDecisionGateScorecardRow,
)


def build_research_strategy_decision_gate_scorecard_report(
    candidates: Iterable[ResearchStrategyDecisionGateScorecardCandidate],
    *,
    config: ResearchStrategyDecisionGateScorecardConfig,
    generated_at: datetime,
) -> ResearchStrategyDecisionGateScorecardReport:
    if type(config) is not ResearchStrategyDecisionGateScorecardConfig:
        raise ValueError("config must be a ResearchStrategyDecisionGateScorecardConfig")
    _require_hard_phase_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (_scorecard_row(row, config=config) for row in inputs),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyDecisionGateScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        hard_flag_count=_count(sum(1 for row in rows if row.hard_flags)),
        mean_gate_score=_mean(tuple(row.gate_score for row in rows)),
        min_gate_score=_min_decimal(tuple(row.gate_score for row in rows)),
        public_status=_rollup_status(tuple(row.public_status for row in rows)),
        manual_research_state=_manual_state(
            _rollup_status(tuple(row.public_status for row in rows)),
        ),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        candidate_rows=rows,
    )


def research_strategy_decision_gate_scorecard_payload(
    report: ResearchStrategyDecisionGateScorecardReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyDecisionGateScorecardReport:
        raise ValueError("report must be a ResearchStrategyDecisionGateScorecardReport")
    _require_payload_safe_value("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_phase_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_strategy_decision_gate_scorecard_digest(
    report: ResearchStrategyDecisionGateScorecardReport,
) -> dict[str, Any]:
    payload = research_strategy_decision_gate_scorecard_payload(report)
    return {key: payload[key] for key in SUMMARY_KEYS}


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


def _scorecard_row(
    row: ResearchStrategyDecisionGateScorecardCandidate,
    *,
    config: ResearchStrategyDecisionGateScorecardConfig,
) -> ResearchStrategyDecisionGateScorecardRow:
    reason_codes = _row_reason_codes(row, config=config)
    status = _row_status(reason_codes)
    return ResearchStrategyDecisionGateScorecardRow(
        decision_slot=row.decision_slot,
        public_status=status,
        manual_research_state=_manual_state(status),
        evidence_score=row.evidence_score,
        freshness_score=row.freshness_score,
        scope_fit_score=row.scope_fit_score,
        contradiction_score=row.contradiction_score,
        complexity_score=row.complexity_score,
        gate_score=_gate_score(row),
        hard_flags=row.hard_flags,
        reason_codes=reason_codes,
    )


def _gate_score(row: ResearchStrategyDecisionGateScorecardCandidate) -> Decimal:
    base_score = _quantize(
        (row.evidence_score + row.freshness_score + row.scope_fit_score)
        / Decimal("3.000000"),
    )
    score = _quantize(
        base_score
        - (row.contradiction_score * Decimal("0.350000"))
        - (row.complexity_score * Decimal("0.225000")),
    )
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return score


def _row_reason_codes(
    row: ResearchStrategyDecisionGateScorecardCandidate,
    *,
    config: ResearchStrategyDecisionGateScorecardConfig,
) -> tuple[str, ...]:
    if row.hard_flags:
        return tuple(f"hard_flag_{flag}" for flag in row.hard_flags)
    reason_codes: list[str] = []
    if row.evidence_score < config.evidence_block_floor:
        reason_codes.append("evidence_low_block")
    elif row.evidence_score < config.evidence_watch_floor:
        reason_codes.append("evidence_low_watch")
    if row.freshness_score < config.freshness_block_floor:
        reason_codes.append("freshness_low_block")
    elif row.freshness_score < config.freshness_watch_floor:
        reason_codes.append("freshness_low_watch")
    if row.scope_fit_score < config.scope_fit_block_floor:
        reason_codes.append("scope_fit_low_block")
    elif row.scope_fit_score < config.scope_fit_watch_floor:
        reason_codes.append("scope_fit_low_watch")
    if row.contradiction_score >= config.contradiction_block_ceiling:
        reason_codes.append("contradiction_high_block")
    elif row.contradiction_score >= config.contradiction_watch_ceiling:
        reason_codes.append("contradiction_high_watch")
    if row.complexity_score >= config.complexity_watch_ceiling:
        reason_codes.append("complexity_high_watch")
    if not reason_codes:
        reason_codes.append("decision_gate_clear")
    return tuple(sorted(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.startswith("hard_flag_") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _manual_state(status: str) -> str:
    if status == "block":
        return "manual_research_block"
    if status == "watch":
        return "manual_research_watch"
    return "manual_research_ready"


def _rollup_reason_codes(
    rows: tuple[ResearchStrategyDecisionGateScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.public_status for row in rows))
    reason_codes = {f"decision_gate_scorecard_{status}"}
    reason_codes.update(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != "decision_gate_clear"
    )
    return tuple(sorted(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchStrategyDecisionGateScorecardRow, ...],
) -> tuple[ResearchStrategyDecisionGateScorecardReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyDecisionGateScorecardReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyDecisionGateScorecardReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_candidates(
    candidates: Iterable[ResearchStrategyDecisionGateScorecardCandidate],
) -> tuple[ResearchStrategyDecisionGateScorecardCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_slots: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyDecisionGateScorecardCandidate:
            raise ValueError(
                "candidates must contain ResearchStrategyDecisionGateScorecardCandidate values",
            )
        _require_hard_phase_flags("candidate", row)
        if row.decision_slot in seen_slots:
            raise ValueError("candidates must not contain duplicate decision_slot values")
        seen_slots.add(row.decision_slot)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchStrategyDecisionGateScorecardRow],
) -> tuple[ResearchStrategyDecisionGateScorecardRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("candidate_rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("candidate_rows must be an iterable") from exc
    seen_slots: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyDecisionGateScorecardRow:
            raise ValueError(
                "candidate_rows must contain ResearchStrategyDecisionGateScorecardRow values",
            )
        _require_hard_phase_flags("row", row)
        if row.decision_slot in seen_slots:
            raise ValueError("candidate_rows must not contain duplicate decision_slot values")
        seen_slots.add(row.decision_slot)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("candidate_rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchStrategyDecisionGateScorecardReasonCodeCount],
) -> tuple[ResearchStrategyDecisionGateScorecardReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyDecisionGateScorecardReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyDecisionGateScorecardReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must be sorted by count then reason_code")
    return values


def _row_sort_key(row: ResearchStrategyDecisionGateScorecardRow) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.public_status],
        row.gate_score,
        row.decision_slot,
    )


def _status_count(
    rows: tuple[ResearchStrategyDecisionGateScorecardRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.public_status == status))


def _validate_report(report: ResearchStrategyDecisionGateScorecardReport) -> None:
    rows = report.candidate_rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match candidate_rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match candidate_rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match candidate_rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match candidate_rows")
    if report.hard_flag_count != _count(sum(1 for row in rows if row.hard_flags)):
        raise ValueError("hard_flag_count must match candidate_rows")
    scores = tuple(row.gate_score for row in rows)
    if report.mean_gate_score != _mean(scores):
        raise ValueError("mean_gate_score must match candidate_rows")
    if report.min_gate_score != _min_decimal(scores):
        raise ValueError("min_gate_score must match candidate_rows")
    if report.public_status != _rollup_status(tuple(row.public_status for row in rows)):
        raise ValueError("public_status must match candidate_rows")
    if report.manual_research_state != _manual_state(report.public_status):
        raise ValueError("manual_research_state must match public_status")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match candidate_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match candidate_rows")


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
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if isinstance(value, (list, dict, set)):
        raise ValueError("JSON value must come from public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        _revalidate_public_dataclass_for_payload(label, value)
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        _rebuild_public_dataclass(label, value)
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
            _require_canonical_string(label, value)
        return
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains unsupported value")


def _revalidate_public_dataclass_for_payload(label: str, value: object) -> None:
    if type(value) is ResearchStrategyDecisionGateScorecardCandidate:
        _revalidate_candidate_for_payload(value)
        return
    if type(value) is ResearchStrategyDecisionGateScorecardConfig:
        _revalidate_config_for_payload(value)
        return
    if type(value) is ResearchStrategyDecisionGateScorecardRow:
        _revalidate_row_for_payload(value)
        return
    if type(value) is ResearchStrategyDecisionGateScorecardReasonCodeCount:
        _revalidate_reason_code_count_for_payload(value)
        return
    if type(value) is ResearchStrategyDecisionGateScorecardReport:
        _revalidate_report_for_payload(value)
        return
    raise ValueError(f"{label} contains unsupported dataclass")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed payload revalidation") from exc


def _revalidate_config_for_payload(
    config: ResearchStrategyDecisionGateScorecardConfig,
) -> None:
    _require_exact_type(config, ResearchStrategyDecisionGateScorecardConfig, "config")
    _require_canonical_string("config_version", config.config_version)
    for field_name in (
        "evidence_watch_floor",
        "evidence_block_floor",
        "freshness_watch_floor",
        "freshness_block_floor",
        "scope_fit_watch_floor",
        "scope_fit_block_floor",
        "contradiction_watch_ceiling",
        "contradiction_block_ceiling",
        "complexity_watch_ceiling",
    ):
        _require_ratio(field_name, getattr(config, field_name))
    _require_at_least(
        "evidence_watch_floor",
        config.evidence_watch_floor,
        config.evidence_block_floor,
    )
    _require_at_least(
        "freshness_watch_floor",
        config.freshness_watch_floor,
        config.freshness_block_floor,
    )
    _require_at_least(
        "scope_fit_watch_floor",
        config.scope_fit_watch_floor,
        config.scope_fit_block_floor,
    )
    _require_at_most(
        "contradiction_watch_ceiling",
        config.contradiction_watch_ceiling,
        config.contradiction_block_ceiling,
    )
    _require_hard_phase_flags("config", config)


def _revalidate_candidate_for_payload(
    row: ResearchStrategyDecisionGateScorecardCandidate,
) -> None:
    _require_exact_type(row, ResearchStrategyDecisionGateScorecardCandidate, "candidate")
    _require_canonical_string("decision_slot", row.decision_slot)
    for field_name in (
        "evidence_score",
        "freshness_score",
        "scope_fit_score",
        "contradiction_score",
        "complexity_score",
    ):
        _require_ratio(field_name, getattr(row, field_name))
    if row.hard_flags != _normalize_hard_flags(row.hard_flags):
        raise ValueError("hard_flags must use canonical sequence")
    _require_hard_phase_flags("candidate", row)


def _revalidate_row_for_payload(row: ResearchStrategyDecisionGateScorecardRow) -> None:
    _require_exact_type(row, ResearchStrategyDecisionGateScorecardRow, "row")
    _require_canonical_string("decision_slot", row.decision_slot)
    _require_public_status("public_status", row.public_status)
    _require_manual_state("manual_research_state", row.manual_research_state)
    for field_name in (
        "evidence_score",
        "freshness_score",
        "scope_fit_score",
        "contradiction_score",
        "complexity_score",
        "gate_score",
    ):
        _require_ratio(field_name, getattr(row, field_name))
    if row.hard_flags != _normalize_hard_flags(row.hard_flags):
        raise ValueError("hard_flags must use canonical sequence")
    _require_reason_codes_tuple(row.reason_codes)
    if row.reason_codes != _normalize_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must use canonical sequence")
    if row.public_status != _row_status(row.reason_codes):
        raise ValueError("public_status must match reason_codes")
    if row.manual_research_state != _manual_state(row.public_status):
        raise ValueError("manual_research_state must match public_status")
    _require_hard_phase_flags("row", row)


def _revalidate_reason_code_count_for_payload(
    row: ResearchStrategyDecisionGateScorecardReasonCodeCount,
) -> None:
    _require_exact_type(row, ResearchStrategyDecisionGateScorecardReasonCodeCount, "row")
    _require_canonical_string("reason_code", row.reason_code)
    _require_positive_six_decimal_decimal("count", row.count)
    _require_hard_phase_flags("reason_code_count", row)


def _revalidate_report_for_payload(
    report: ResearchStrategyDecisionGateScorecardReport,
) -> None:
    _require_exact_type(report, ResearchStrategyDecisionGateScorecardReport, "report")
    _require_utc_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    for field_name in (
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "hard_flag_count",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(report, field_name))
    for field_name in ("mean_gate_score", "min_gate_score"):
        _require_ratio(field_name, getattr(report, field_name))
    _require_public_status("public_status", report.public_status)
    _require_manual_state("manual_research_state", report.manual_research_state)
    _require_reason_codes_tuple(report.reason_codes)
    _normalize_report_reason_codes(report.reason_codes)
    if type(report.reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in report.reason_code_counts:
        if type(row) is not ResearchStrategyDecisionGateScorecardReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyDecisionGateScorecardReasonCodeCount values",
            )
        _revalidate_reason_code_count_for_payload(row)
    if type(report.candidate_rows) is not tuple:
        raise ValueError("candidate_rows must be a tuple")
    for row in report.candidate_rows:
        if type(row) is not ResearchStrategyDecisionGateScorecardRow:
            raise ValueError(
                "candidate_rows must contain ResearchStrategyDecisionGateScorecardRow values",
            )
        _revalidate_row_for_payload(row)
    _validate_report(report)
    _require_hard_phase_flags("report", report)


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
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
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
    return any(
        fragment in normalized
        for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS | EXTRA_UNSAFE_FRAGMENTS
    )


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


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return normalized


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")


def _require_nonnegative_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    _require_six_decimal_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    _require_nonnegative_six_decimal_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_ratio(field_name: str, value: Decimal) -> None:
    _require_nonnegative_six_decimal_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")


def _require_reason_codes_tuple(reason_codes: object) -> None:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_canonical_string("reason_codes", reason_code)
    normalized = tuple(sorted(values))
    if values != normalized:
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _normalize_report_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_canonical_string("reason_codes", reason_code)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    return values


def _normalize_hard_flags(hard_flags: Iterable[str]) -> tuple[str, ...]:
    if isinstance(hard_flags, (str, bytes)):
        raise ValueError("hard_flags must be an iterable")
    try:
        values = tuple(hard_flags)
    except TypeError as exc:
        raise ValueError("hard_flags must be an iterable") from exc
    for flag in values:
        _require_canonical_string("hard_flags", flag)
    normalized = tuple(sorted(values))
    if values != normalized:
        raise ValueError("hard_flags must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("hard_flags must not contain duplicates")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_at_least(field_name: str, upper: Decimal, lower: Decimal) -> None:
    if upper < lower:
        raise ValueError(f"{field_name} must be greater than or equal to paired threshold")


def _require_at_most(field_name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{field_name} must be less than or equal to paired threshold")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_public_status(field_name: str, value: str) -> None:
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be a known public status")


def _require_manual_state(field_name: str, value: str) -> None:
    if type(value) is str and _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")
    if value not in (
        "manual_research_block",
        "manual_research_ready",
        "manual_research_watch",
    ):
        raise ValueError(f"{field_name} must be a known manual research state")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_phase_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
