"""Pure readiness scoring for caller-supplied research candidates.

The module is deterministic and side-effect free. Callers provide typed research
candidates; the policy returns report-only scores, statuses, and reason codes.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from contextvars import ContextVar
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchStrategyReadinessCandidate",
    "ResearchStrategyReadinessReasonCodeCount",
    "ResearchStrategyReadinessScoreConfig",
    "ResearchStrategyReadinessScoreReport",
    "ResearchStrategyReadinessScoreRow",
    "build_research_strategy_readiness_score_report",
    "research_strategy_readiness_score_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-strategy-readiness-score-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_PASS_READINESS_SCORE = Decimal("0.750000")
DEFAULT_WATCH_READINESS_SCORE = Decimal("0.500000")


class _Missing:
    pass


_MISSING = _Missing()


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
class ResearchStrategyReadinessScoreConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_readiness_score: Decimal = DEFAULT_PASS_READINESS_SCORE
    watch_readiness_score: Decimal = DEFAULT_WATCH_READINESS_SCORE
    evidence_quality_weight: Decimal = Decimal("0.250000")
    probability_calibration_weight: Decimal = Decimal("0.200000")
    cost_friction_weight: Decimal = Decimal("0.150000")
    settlement_ambiguity_weight: Decimal = Decimal("0.150000")
    team_consensus_weight: Decimal = Decimal("0.150000")
    memory_coverage_weight: Decimal = Decimal("0.100000")
    cost_friction_watch: Decimal = Decimal("0.500000")
    cost_friction_block: Decimal = Decimal("0.800000")
    settlement_ambiguity_watch: Decimal = Decimal("0.400000")
    settlement_ambiguity_block: Decimal = Decimal("0.700000")
    team_consensus_watch: Decimal = Decimal("0.500000")
    memory_coverage_watch: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReadinessScoreConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pass_readiness_score",
            "watch_readiness_score",
            "evidence_quality_weight",
            "probability_calibration_weight",
            "cost_friction_weight",
            "settlement_ambiguity_weight",
            "team_consensus_weight",
            "memory_coverage_weight",
            "cost_friction_watch",
            "cost_friction_block",
            "settlement_ambiguity_watch",
            "settlement_ambiguity_block",
            "team_consensus_watch",
            "memory_coverage_watch",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_readiness_score <= self.watch_readiness_score:
            raise ValueError("pass_readiness_score must be greater than watch_readiness_score")
        if self.cost_friction_block < self.cost_friction_watch:
            raise ValueError("cost_friction_block must be at least cost_friction_watch")
        if self.settlement_ambiguity_block < self.settlement_ambiguity_watch:
            raise ValueError(
                "settlement_ambiguity_block must be at least settlement_ambiguity_watch",
            )
        weight_sum = _quantize(
            self.evidence_quality_weight
            + self.probability_calibration_weight
            + self.cost_friction_weight
            + self.settlement_ambiguity_weight
            + self.team_consensus_weight
            + self.memory_coverage_weight,
        )
        if weight_sum != ONE:
            raise ValueError("readiness score weights must sum to 1")
        _require_hard_flags("config", self)


_SCORE_ROW_CONSISTENCY_CONFIG: ContextVar[
    ResearchStrategyReadinessScoreConfig | None
] = ContextVar("_SCORE_ROW_CONSISTENCY_CONFIG", default=None)


@dataclass(frozen=True)
class ResearchStrategyReadinessCandidate(_FinalPublicDataclass):
    candidate_id: str
    evidence_quality_score: Decimal
    probability_calibration_score: Decimal
    cost_friction_score: Decimal
    settlement_ambiguity_score: Decimal
    team_consensus_score: Decimal
    memory_coverage_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReadinessCandidate, "candidate")
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "evidence_quality_score",
            "probability_calibration_score",
            "cost_friction_score",
            "settlement_ambiguity_score",
            "team_consensus_score",
            "memory_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchStrategyReadinessScoreRow(_FinalPublicDataclass):
    candidate_id: str
    evidence_quality_score: Decimal
    probability_calibration_score: Decimal
    cost_friction_score: Decimal
    settlement_ambiguity_score: Decimal
    team_consensus_score: Decimal
    memory_coverage_score: Decimal
    readiness_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReadinessScoreRow, "row")
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "evidence_quality_score",
            "probability_calibration_score",
            "cost_friction_score",
            "settlement_ambiguity_score",
            "team_consensus_score",
            "memory_coverage_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_score_row_consistency(
            self,
            config=_SCORE_ROW_CONSISTENCY_CONFIG.get(),
        )


@dataclass(frozen=True)
class ResearchStrategyReadinessReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyReadinessReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyReadinessScoreReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal | None
    status: str
    rows: tuple[ResearchStrategyReadinessScoreRow, ...]
    reason_code_counts: tuple[ResearchStrategyReadinessReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReadinessScoreReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_readiness_score",
            _require_optional_probability_decimal(
                "average_readiness_score",
                self.average_readiness_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", _public_payload_value(self))


def build_research_strategy_readiness_score_report(
    candidates: Iterable[object],
    *,
    config: ResearchStrategyReadinessScoreConfig,
    generated_at: datetime,
) -> ResearchStrategyReadinessScoreReport:
    if type(config) is not ResearchStrategyReadinessScoreConfig:
        raise ValueError("config must be a ResearchStrategyReadinessScoreConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidate_items = _normalize_candidates(candidates)
    for item in candidate_items:
        _reject_future_observed_at(item, generated_at_utc)

    rows = tuple(
        sorted(
            (
                _score_row_from_candidate(item, config=config)
                for item in candidate_items
            ),
            key=lambda row: row.candidate_id,
        ),
    )
    _reject_duplicate_candidate_ids(rows)
    reason_codes = _summary_reason_codes(rows)

    return ResearchStrategyReadinessScoreReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_readiness_score=_average_readiness_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_readiness_score_report_payload(
    report: ResearchStrategyReadinessScoreReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyReadinessScoreReport:
        raise ValueError("report must be a ResearchStrategyReadinessScoreReport")
    _require_hard_flags("report", report)
    payload = _public_payload_value(report)
    _reject_unsafe_public_payload("report payload", payload)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def _score_row_from_candidate(
    candidate: ResearchStrategyReadinessCandidate,
    *,
    config: ResearchStrategyReadinessScoreConfig,
) -> ResearchStrategyReadinessScoreRow:
    readiness_score = _readiness_score(candidate, config=config)
    status = _row_status(
        candidate=candidate,
        readiness_score=readiness_score,
        config=config,
    )
    token = _SCORE_ROW_CONSISTENCY_CONFIG.set(config)
    try:
        return ResearchStrategyReadinessScoreRow(
            candidate_id=candidate.candidate_id,
            evidence_quality_score=candidate.evidence_quality_score,
            probability_calibration_score=candidate.probability_calibration_score,
            cost_friction_score=candidate.cost_friction_score,
            settlement_ambiguity_score=candidate.settlement_ambiguity_score,
            team_consensus_score=candidate.team_consensus_score,
            memory_coverage_score=candidate.memory_coverage_score,
            readiness_score=readiness_score,
            observed_at=candidate.observed_at,
            status=status,
            reason_codes=_row_reason_codes(
                candidate=candidate,
                status=status,
                config=config,
            ),
        )
    finally:
        _SCORE_ROW_CONSISTENCY_CONFIG.reset(token)


def _readiness_score(
    candidate: ResearchStrategyReadinessCandidate,
    *,
    config: ResearchStrategyReadinessScoreConfig,
) -> Decimal:
    raw_score = (
        candidate.evidence_quality_score * config.evidence_quality_weight
        + candidate.probability_calibration_score
        * config.probability_calibration_weight
        + (ONE - candidate.cost_friction_score) * config.cost_friction_weight
        + (ONE - candidate.settlement_ambiguity_score)
        * config.settlement_ambiguity_weight
        + candidate.team_consensus_score * config.team_consensus_weight
        + candidate.memory_coverage_score * config.memory_coverage_weight
    )
    return _quantize(max(ZERO, min(ONE, raw_score)))


def _row_status(
    *,
    candidate: ResearchStrategyReadinessCandidate,
    readiness_score: Decimal,
    config: ResearchStrategyReadinessScoreConfig,
) -> str:
    if candidate.cost_friction_score >= config.cost_friction_block:
        return "block"
    if candidate.settlement_ambiguity_score >= config.settlement_ambiguity_block:
        return "block"
    if readiness_score < config.watch_readiness_score:
        return "block"
    if readiness_score < config.pass_readiness_score:
        return "watch"
    if candidate.cost_friction_score >= config.cost_friction_watch:
        return "watch"
    if candidate.settlement_ambiguity_score >= config.settlement_ambiguity_watch:
        return "watch"
    if candidate.team_consensus_score < config.team_consensus_watch:
        return "watch"
    if candidate.memory_coverage_score < config.memory_coverage_watch:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    candidate: ResearchStrategyReadinessCandidate,
    status: str,
    config: ResearchStrategyReadinessScoreConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"strategy_readiness_{status}"}
    reason_codes.add(
        _score_reason(
            "evidence_quality",
            candidate.evidence_quality_score,
            watch_score=config.watch_readiness_score,
            pass_score=config.pass_readiness_score,
        ),
    )
    reason_codes.add(
        _score_reason(
            "probability_calibration",
            candidate.probability_calibration_score,
            watch_score=config.watch_readiness_score,
            pass_score=config.pass_readiness_score,
        ),
    )
    reason_codes.add(
        _risk_reason(
            "cost_friction",
            candidate.cost_friction_score,
            watch_score=config.cost_friction_watch,
            block_score=config.cost_friction_block,
        ),
    )
    reason_codes.add(
        _risk_reason(
            "settlement_ambiguity",
            candidate.settlement_ambiguity_score,
            watch_score=config.settlement_ambiguity_watch,
            block_score=config.settlement_ambiguity_block,
        ),
    )
    reason_codes.add(
        "team_consensus_strong"
        if candidate.team_consensus_score >= config.team_consensus_watch
        else "team_consensus_watch",
    )
    reason_codes.add(
        "memory_coverage_strong"
        if candidate.memory_coverage_score >= config.memory_coverage_watch
        else "memory_coverage_watch",
    )
    for reason_code in candidate.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _score_reason(
    prefix: str,
    value: Decimal,
    *,
    watch_score: Decimal,
    pass_score: Decimal,
) -> str:
    if value < watch_score:
        return f"{prefix}_block"
    if value < pass_score:
        return f"{prefix}_watch"
    return f"{prefix}_strong"


def _risk_reason(
    prefix: str,
    value: Decimal,
    *,
    watch_score: Decimal,
    block_score: Decimal,
) -> str:
    if value >= block_score:
        return f"{prefix}_block"
    if value >= watch_score:
        return f"{prefix}_watch"
    return f"low_{prefix}"


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[ResearchStrategyReadinessCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        values = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    return tuple(_coerce_candidate(value) for value in values)


def _coerce_candidate(value: object) -> ResearchStrategyReadinessCandidate:
    if type(value) is ResearchStrategyReadinessCandidate:
        _require_hard_flags("candidate", value)
        return value
    _require_hard_flags("candidate", value)
    return ResearchStrategyReadinessCandidate(
        candidate_id=_field_value(value, "candidate_id"),
        evidence_quality_score=_field_value(value, "evidence_quality_score"),
        probability_calibration_score=_field_value(
            value,
            "probability_calibration_score",
        ),
        cost_friction_score=_field_value(value, "cost_friction_score"),
        settlement_ambiguity_score=_field_value(value, "settlement_ambiguity_score"),
        team_consensus_score=_field_value(value, "team_consensus_score"),
        memory_coverage_score=_field_value(value, "memory_coverage_score"),
        observed_at=_field_value(value, "observed_at"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _reject_future_observed_at(
    item: ResearchStrategyReadinessCandidate,
    generated_at: datetime,
) -> None:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")


def _reject_duplicate_candidate_ids(
    rows: tuple[ResearchStrategyReadinessScoreRow, ...],
) -> None:
    if len({row.candidate_id for row in rows}) != len(rows):
        raise ValueError("candidate_id values must be unique")


def _summary_reason_codes(
    rows: tuple[ResearchStrategyReadinessScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_research_candidates",)
    if all(row.status == "pass" for row in rows):
        return ("strategy_readiness_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_research_candidates",):
        return "block"
    if "strategy_readiness_block" in reason_codes:
        return "block"
    if "strategy_readiness_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategyReadinessScoreRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyReadinessReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyReadinessReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchStrategyReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_readiness_score(
    rows: tuple[ResearchStrategyReadinessScoreRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.readiness_score for row in rows), ZERO) / Decimal(len(rows)))


def _status_count(rows: tuple[ResearchStrategyReadinessScoreRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchStrategyReadinessScoreRow, ...],
) -> tuple[ResearchStrategyReadinessScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyReadinessScoreRow:
            raise ValueError("rows must contain ResearchStrategyReadinessScoreRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.candidate_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by candidate_id")
    _reject_duplicate_candidate_ids(rows)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyReadinessReasonCodeCount, ...],
) -> tuple[ResearchStrategyReadinessReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategyReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyReadinessReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_score_row_consistency(
    row: ResearchStrategyReadinessScoreRow,
    *,
    config: ResearchStrategyReadinessScoreConfig | None,
) -> None:
    expected_status_code = f"strategy_readiness_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    pass_readiness_score = (
        config.pass_readiness_score
        if config is not None
        else DEFAULT_PASS_READINESS_SCORE
    )
    watch_readiness_score = (
        config.watch_readiness_score
        if config is not None
        else DEFAULT_WATCH_READINESS_SCORE
    )
    if row.status == "pass" and row.readiness_score < pass_readiness_score:
        raise ValueError("readiness_score must support pass status")
    if row.status == "watch" and row.readiness_score < watch_readiness_score:
        raise ValueError("readiness_score must support watch status")


def _validate_report_consistency(report: ResearchStrategyReadinessScoreReport) -> None:
    if report.candidate_count != _decimal_count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_readiness_score != _average_readiness_score(report.rows):
        raise ValueError("average_readiness_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _public_payload_value(value: object) -> object:
    payload = _payload_value(value)
    if not isinstance(payload, dict):
        return payload
    rows = payload.get("rows")
    if isinstance(rows, list):
        public_rows: list[object] = []
        for index, row in enumerate(rows, start=1):
            if isinstance(row, dict):
                public_row = dict(row)
                public_row.pop("candidate_id", None)
                public_row["row_index"] = str(index)
                public_rows.append(public_row)
            else:
                public_rows.append(row)
        payload["rows"] = public_rows
    return payload


def _reject_unsafe_public_payload(field_name: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field_name} contains a non-string key")
            if key == "candidate_id":
                raise ValueError(f"{field_name} contains candidate_id")
            _reject_unsafe_public_payload(field_name, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(field_name, item)
        return
    if type(value) in (str, bool) or value is None:
        return
    raise ValueError(f"{field_name} contains an unsafe public value")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed_characters = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if not all(character in allowed_characters for character in value):
        raise ValueError(f"{field_name} must use lowercase snake case")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, flag_name):
            raise ValueError(f"{field_name}.{flag_name} is required")
        if type(getattr(value, flag_name)) is not bool:
            raise ValueError(f"{flag_name} must be a bool")
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")
