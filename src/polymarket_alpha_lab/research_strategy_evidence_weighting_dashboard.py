"""Deterministic public dashboard for caller-supplied research signals.

The module is side-effect free. It accepts typed signal rows and returns a
report-only public weighting view with redacted row keys.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "ResearchStrategyEvidenceSignal",
    "ResearchStrategyEvidenceWeightingConfig",
    "ResearchStrategyEvidenceWeightingReasonCodeCount",
    "ResearchStrategyEvidenceWeightingReport",
    "ResearchStrategyEvidenceWeightingRow",
    "build_research_strategy_evidence_weighting_dashboard",
    "research_strategy_evidence_weighting_dashboard_digest",
    "research_strategy_evidence_weighting_dashboard_payload",
)


DEFAULT_RESEARCH_STRATEGY_EVIDENCE_WEIGHTING_CONFIG_VERSION = (
    "research-strategy-evidence-weighting-dashboard-v0"
)
STATUSES = ("pass", "watch", "block")
PASS_REASON = "research_strategy_evidence_weighting_pass"
WATCH_WEIGHT_REASON = "research_strategy_evidence_weighting_watch_weight"
BLOCK_WEIGHT_REASON = "research_strategy_evidence_weighting_block_weight"
HIGH_CONFLICT_REASON = "research_strategy_evidence_weighting_high_conflict"
STALE_SIGNAL_REASON = "research_strategy_evidence_weighting_stale_signal"
LOW_SOURCE_RELIABILITY_REASON = (
    "research_strategy_evidence_weighting_low_source_reliability"
)
LOW_TEAM_CONFIDENCE_REASON = (
    "research_strategy_evidence_weighting_low_team_confidence"
)
NO_INPUTS_REASON = "research_strategy_evidence_weighting_no_inputs"
ROW_REASON_CODE_SEQUENCE = (
    BLOCK_WEIGHT_REASON,
    HIGH_CONFLICT_REASON,
    WATCH_WEIGHT_REASON,
    STALE_SIGNAL_REASON,
    LOW_SOURCE_RELIABILITY_REASON,
    LOW_TEAM_CONFIDENCE_REASON,
    PASS_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    BLOCK_WEIGHT_REASON,
    HIGH_CONFLICT_REASON,
    WATCH_WEIGHT_REASON,
    STALE_SIGNAL_REASON,
    LOW_SOURCE_RELIABILITY_REASON,
    LOW_TEAM_CONFIDENCE_REASON,
    PASS_REASON,
)
ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class ResearchStrategyEvidenceWeightingConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_EVIDENCE_WEIGHTING_CONFIG_VERSION
    evidence_strength_weight: Decimal = Decimal("0.300000")
    source_reliability_weight: Decimal = Decimal("0.250000")
    conflict_resistance_weight: Decimal = Decimal("0.100000")
    freshness_weight: Decimal = Decimal("0.150000")
    team_confidence_weight: Decimal = Decimal("0.200000")
    pass_weight_threshold: Decimal = Decimal("0.750000")
    watch_weight_threshold: Decimal = Decimal("0.500000")
    max_conflict_rate: Decimal = Decimal("0.700000")
    stale_freshness_threshold: Decimal = Decimal("0.250000")
    low_source_reliability_threshold: Decimal = Decimal("0.350000")
    low_team_confidence_threshold: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceWeightingConfig:
            raise TypeError(
                "ResearchStrategyEvidenceWeightingConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceWeightingConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "evidence_strength_weight",
            "source_reliability_weight",
            "conflict_resistance_weight",
            "freshness_weight",
            "team_confidence_weight",
            "pass_weight_threshold",
            "watch_weight_threshold",
            "max_conflict_rate",
            "stale_freshness_threshold",
            "low_source_reliability_threshold",
            "low_team_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        weight_sum = _quantize(
            self.evidence_strength_weight
            + self.source_reliability_weight
            + self.conflict_resistance_weight
            + self.freshness_weight
            + self.team_confidence_weight,
        )
        if weight_sum != ONE:
            raise ValueError("component weights must sum to 1")
        if self.pass_weight_threshold <= self.watch_weight_threshold:
            raise ValueError("pass_weight_threshold must exceed watch_weight_threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyEvidenceSignal:
    research_key: str
    evidence_strength: Decimal
    source_reliability: Decimal
    conflict_rate: Decimal
    freshness_score: Decimal
    team_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceSignal:
            raise TypeError(
                "ResearchStrategyEvidenceSignal does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceSignal, "signal")
        _require_public_string("research_key", self.research_key)
        for field_name in (
            "evidence_strength",
            "source_reliability",
            "conflict_rate",
            "freshness_score",
            "team_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceWeightingRow:
    public_research_digest: str
    evidence_strength: Decimal
    source_reliability: Decimal
    conflict_rate: Decimal
    freshness_score: Decimal
    team_confidence: Decimal
    evidence_weight: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceWeightingRow:
            raise TypeError(
                "ResearchStrategyEvidenceWeightingRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceWeightingRow, "row")
        _require_digest("public_research_digest", self.public_research_digest)
        for field_name in (
            "evidence_strength",
            "source_reliability",
            "conflict_rate",
            "freshness_score",
            "team_confidence",
            "evidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, row=True),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyEvidenceWeightingReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceWeightingReasonCodeCount:
            raise TypeError(
                "ResearchStrategyEvidenceWeightingReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEvidenceWeightingReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_probability_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyEvidenceWeightingReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_evidence_strength: Decimal
    average_source_reliability: Decimal
    average_conflict_rate: Decimal
    average_freshness_score: Decimal
    average_team_confidence: Decimal
    average_evidence_weight: Decimal
    status: str
    rows: tuple[ResearchStrategyEvidenceWeightingRow, ...]
    reason_code_counts: tuple[ResearchStrategyEvidenceWeightingReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    public_report_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceWeightingReport:
            raise TypeError(
                "ResearchStrategyEvidenceWeightingReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceWeightingReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _reject_unsafe_string("config_version", self.config_version)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_evidence_strength",
            "average_source_reliability",
            "average_conflict_rate",
            "average_freshness_score",
            "average_team_confidence",
            "average_evidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, row=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest(self)
        if self.public_report_digest == "":
            object.__setattr__(self, "public_report_digest", expected_digest)
        else:
            _require_digest("public_report_digest", self.public_report_digest)
            if self.public_report_digest != expected_digest:
                raise ValueError("public_report_digest must match report")
        _reject_unsafe_public_payload("report", _payload_value(self))


def build_research_strategy_evidence_weighting_dashboard(
    signals: Iterable[object],
    *,
    config: ResearchStrategyEvidenceWeightingConfig,
    generated_at: datetime,
) -> ResearchStrategyEvidenceWeightingReport:
    if type(config) is not ResearchStrategyEvidenceWeightingConfig:
        raise ValueError("config must be a ResearchStrategyEvidenceWeightingConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    signal_rows = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (_row_from_signal(signal, config=config) for signal in signal_rows),
            key=lambda row: row.public_research_digest,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchStrategyEvidenceWeightingReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        row_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_evidence_strength=_average(
            tuple(row.evidence_strength for row in rows),
        ),
        average_source_reliability=_average(
            tuple(row.source_reliability for row in rows),
        ),
        average_conflict_rate=_average(tuple(row.conflict_rate for row in rows)),
        average_freshness_score=_average(tuple(row.freshness_score for row in rows)),
        average_team_confidence=_average(tuple(row.team_confidence for row in rows)),
        average_evidence_weight=_average(tuple(row.evidence_weight for row in rows)),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_evidence_weighting_dashboard_payload(
    report: ResearchStrategyEvidenceWeightingReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyEvidenceWeightingReport:
        raise ValueError("report must be a ResearchStrategyEvidenceWeightingReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report", payload)
    return payload


def research_strategy_evidence_weighting_dashboard_digest(
    report: ResearchStrategyEvidenceWeightingReport,
) -> str:
    if type(report) is not ResearchStrategyEvidenceWeightingReport:
        raise ValueError("report must be a ResearchStrategyEvidenceWeightingReport")
    _require_hard_flags("report", report)
    expected_digest = _report_digest(report)
    if report.public_report_digest != expected_digest:
        raise ValueError("public_report_digest must match report")
    return expected_digest


def _row_from_signal(
    signal: ResearchStrategyEvidenceSignal,
    *,
    config: ResearchStrategyEvidenceWeightingConfig,
) -> ResearchStrategyEvidenceWeightingRow:
    evidence_weight = _evidence_weight(signal, config)
    reason_codes = _row_reason_codes(
        evidence_weight=evidence_weight,
        source_reliability=signal.source_reliability,
        conflict_rate=signal.conflict_rate,
        freshness_score=signal.freshness_score,
        team_confidence=signal.team_confidence,
        config=config,
    )
    return ResearchStrategyEvidenceWeightingRow(
        public_research_digest=_public_digest(signal.research_key),
        evidence_strength=signal.evidence_strength,
        source_reliability=signal.source_reliability,
        conflict_rate=signal.conflict_rate,
        freshness_score=signal.freshness_score,
        team_confidence=signal.team_confidence,
        evidence_weight=evidence_weight,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _normalize_signals(signals: Iterable[object]) -> tuple[ResearchStrategyEvidenceSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        values = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchStrategyEvidenceSignal:
            raise ValueError("signals must contain ResearchStrategyEvidenceSignal rows")
        _require_hard_flags("signal", value)
    return values


def _evidence_weight(
    signal: ResearchStrategyEvidenceSignal,
    config: ResearchStrategyEvidenceWeightingConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        weight = (
            signal.evidence_strength * config.evidence_strength_weight
            + signal.source_reliability * config.source_reliability_weight
            + (ONE - signal.conflict_rate) * config.conflict_resistance_weight
            + signal.freshness_score * config.freshness_weight
            + signal.team_confidence * config.team_confidence_weight
        )
    return _quantize(weight)


def _row_reason_codes(
    *,
    evidence_weight: Decimal,
    source_reliability: Decimal,
    conflict_rate: Decimal,
    freshness_score: Decimal,
    team_confidence: Decimal,
    config: ResearchStrategyEvidenceWeightingConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if evidence_weight < config.watch_weight_threshold:
        reason_codes.append(BLOCK_WEIGHT_REASON)
    if conflict_rate >= config.max_conflict_rate:
        reason_codes.append(HIGH_CONFLICT_REASON)
    if evidence_weight < config.pass_weight_threshold and evidence_weight >= config.watch_weight_threshold:
        reason_codes.append(WATCH_WEIGHT_REASON)
    if freshness_score <= config.stale_freshness_threshold:
        reason_codes.append(STALE_SIGNAL_REASON)
    if source_reliability <= config.low_source_reliability_threshold:
        reason_codes.append(LOW_SOURCE_RELIABILITY_REASON)
    if team_confidence <= config.low_team_confidence_threshold:
        reason_codes.append(LOW_TEAM_CONFIDENCE_REASON)
    if not reason_codes:
        return (PASS_REASON,)
    return tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_WEIGHT_REASON in reason_codes or HIGH_CONFLICT_REASON in reason_codes:
        return "block"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _summary_reason_codes(
    rows: tuple[ResearchStrategyEvidenceWeightingRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    if present == {PASS_REASON}:
        return (PASS_REASON,)
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in present and reason_code != PASS_REASON
    )


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if NO_INPUTS_REASON in reason_codes:
        return "block"
    if BLOCK_WEIGHT_REASON in reason_codes or HIGH_CONFLICT_REASON in reason_codes:
        return "block"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _reason_code_counts(
    rows: tuple[ResearchStrategyEvidenceWeightingRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyEvidenceWeightingReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyEvidenceWeightingReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=_decimal_count(1),
                row_ratio=ONE.quantize(QUANTUM),
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    row_count = Decimal(len(rows))
    return tuple(
        ResearchStrategyEvidenceWeightingReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            row_ratio=_quantize(Decimal(counts[reason_code]) / row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_rows(
    rows: tuple[ResearchStrategyEvidenceWeightingRow, ...],
) -> tuple[ResearchStrategyEvidenceWeightingRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyEvidenceWeightingRow:
            raise ValueError("rows must contain ResearchStrategyEvidenceWeightingRow")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.public_research_digest))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by public_research_digest")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyEvidenceWeightingReasonCodeCount, ...],
) -> tuple[ResearchStrategyEvidenceWeightingReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategyEvidenceWeightingReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEvidenceWeightingReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    expected = tuple(
        reason_code
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in {count.reason_code for count in counts}
    )
    if tuple(count.reason_code for count in counts) != expected:
        raise ValueError("reason_code_counts must follow report reason sequence")
    return counts


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    *,
    row: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    sequence = ROW_REASON_CODE_SEQUENCE if row else REPORT_REASON_CODE_SEQUENCE
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, sequence)
    expected = tuple(reason_code for reason_code in sequence if reason_code in reason_codes)
    if expected != reason_codes:
        raise ValueError(f"{field_name} must be unique and sorted")
    if row and PASS_REASON in reason_codes and reason_codes != (PASS_REASON,):
        raise ValueError(f"{field_name} cannot mix pass with review reasons")
    if not row and PASS_REASON in reason_codes and reason_codes != (PASS_REASON,):
        raise ValueError(f"{field_name} cannot mix pass with review reasons")
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    return reason_codes


def _validate_row_consistency(row: ResearchStrategyEvidenceWeightingRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use pass reason")


def _validate_report_consistency(report: ResearchStrategyEvidenceWeightingReport) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_evidence_strength != _average(tuple(row.evidence_strength for row in rows)):
        raise ValueError("average_evidence_strength must match rows")
    if report.average_source_reliability != _average(tuple(row.source_reliability for row in rows)):
        raise ValueError("average_source_reliability must match rows")
    if report.average_conflict_rate != _average(tuple(row.conflict_rate for row in rows)):
        raise ValueError("average_conflict_rate must match rows")
    if report.average_freshness_score != _average(tuple(row.freshness_score for row in rows)):
        raise ValueError("average_freshness_score must match rows")
    if report.average_team_confidence != _average(tuple(row.team_confidence for row in rows)):
        raise ValueError("average_team_confidence must match rows")
    if report.average_evidence_weight != _average(tuple(row.evidence_weight for row in rows)):
        raise ValueError("average_evidence_weight must match rows")
    expected_reason_codes = _summary_reason_codes(rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    expected_reason_counts = _reason_code_counts(rows, report.reason_codes)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchStrategyEvidenceWeightingRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        result = sum(values, ZERO) / Decimal(len(values))
    return _quantize(result)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _payload_value(value: object, *, omit_report_digest: bool = False) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload decimal value must be exact")
        if not value.is_finite() or not value.same_quantum(QUANTUM):
            raise ValueError("payload decimal value must use six places")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("payload datetime value must be exact")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchStrategyEvidenceSignal,
            ResearchStrategyEvidenceWeightingConfig,
            ResearchStrategyEvidenceWeightingReasonCodeCount,
            ResearchStrategyEvidenceWeightingReport,
            ResearchStrategyEvidenceWeightingRow,
        ):
            raise ValueError("payload must use supported dataclasses")
        return {
            field.name: _payload_value(
                getattr(value, field.name),
                omit_report_digest=omit_report_digest,
            )
            for field in fields(value)
            if not (
                omit_report_digest
                and type(value) is ResearchStrategyEvidenceWeightingReport
                and field.name == "public_report_digest"
            )
        }
    if isinstance(value, tuple):
        return [
            _payload_value(item, omit_report_digest=omit_report_digest)
            for item in value
        ]
    if isinstance(value, list):
        return [
            _payload_value(item, omit_report_digest=omit_report_digest)
            for item in value
        ]
    if type(value) is dict:
        return {
            str(key): _payload_value(item, omit_report_digest=omit_report_digest)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload value is not supported")


def _report_digest(report: ResearchStrategyEvidenceWeightingReport) -> str:
    payload = _payload_value(report, omit_report_digest=True)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return "sha256:" + sha256(encoded.encode("utf-8")).hexdigest()[:16]


def _public_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must support six-place quantization") from exc


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty and trimmed")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _require_digest(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 digest")
    suffix = value.removeprefix("sha256:")
    if len(suffix) not in (12, 16):
        raise ValueError(f"{field_name} must be a supported sha256 digest")
    if any(char not in "0123456789abcdef" for char in suffix):
        raise ValueError(f"{field_name} must be lowercase hex")
    return value


def _require_status(field_name: str, value: object) -> str:
    _require_member(field_name, value, STATUSES)
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _field_value(value: object, field_name: str) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, str):
        _reject_unsafe_string(label, value)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_string(label, str(key))
            _reject_unsafe_public_payload(label, item)
        return
    if value is None or type(value) in (bool,):
        return
    if isinstance(value, (Decimal, datetime)):
        return


def _reject_unsafe_string(label: str, value: str) -> None:
    lowered = value.lower()
    unsafe_fragments = (
        _join_parts("can", "didate"),
        _join_parts("mar", "ket"),
        _join_parts("slu", "g"),
        _join_parts("ques", "tion"),
        _join_parts("ur", "l"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("tok", "en"),
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("pos", "ition"),
        _join_parts("bu", "y"),
        _join_parts("sel", "l"),
        _join_parts("reco", "mmend"),
        _join_parts("://"),
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{label} contains unsafe public value")


def _join_parts(*parts: str) -> str:
    return "".join(parts)
