"""Pure Phase 1 probability and evidence strength alignment report."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_STRATEGY_PROBABILITY_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION = (
    "research-strategy-probability-source-alignment-report-v0"
)

STATUSES = ("pass", "watch", "block")
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    BLOCK_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}

EMPTY_REASON_CODE = "empty_probability_source_alignment_inputs"
REPORT_PASS_REASON_CODE = "probability_source_alignment_pass"
REPORT_WATCH_REASON_CODE = "probability_source_alignment_watch"
REPORT_BLOCK_REASON_CODE = "probability_source_alignment_block"
PROBABILITY_ALIGNED_REASON_CODE = "probability_evidence_aligned"
ROW_REASON_CODES = (
    "probability_evidence_gap_block",
    "probability_evidence_gap_watch",
    PROBABILITY_ALIGNED_REASON_CODE,
    "source_confidence_low_block",
    "source_confidence_low_watch",
    "evidence_recency_block",
    "evidence_recency_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "calibration_support_low_block",
    "calibration_support_low_watch",
    "manual_review_urgency_block",
    "manual_review_urgency_watch",
)
REPORT_REASON_CODES = (
    REPORT_PASS_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_BLOCK_REASON_CODE,
    *ROW_REASON_CODES,
    EMPTY_REASON_CODE,
)
ROW_REASON_SEQUENCE = (
    (
        "probability_evidence_gap_block",
        "probability_evidence_gap_watch",
        PROBABILITY_ALIGNED_REASON_CODE,
    ),
    ("source_confidence_low_block", "source_confidence_low_watch"),
    ("evidence_recency_block", "evidence_recency_watch"),
    ("contradiction_pressure_block", "contradiction_pressure_watch"),
    ("calibration_support_low_block", "calibration_support_low_watch"),
    ("manual_review_urgency_block", "manual_review_urgency_watch"),
)


@dataclass(frozen=True)
class ResearchStrategyProbabilitySourceAlignmentConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_PROBABILITY_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION
    )
    watch_alignment_gap: Decimal = Decimal("0.100000")
    block_alignment_gap: Decimal = Decimal("0.250000")
    watch_source_confidence: Decimal = Decimal("0.700000")
    block_source_confidence: Decimal = Decimal("0.400000")
    watch_evidence_age_seconds: Decimal = Decimal("7200")
    block_evidence_age_seconds: Decimal = Decimal("21600")
    watch_contradiction_pressure: Decimal = Decimal("0.250000")
    block_contradiction_pressure: Decimal = Decimal("0.600000")
    watch_calibration_support: Decimal = Decimal("0.600000")
    block_calibration_support: Decimal = Decimal("0.400000")
    watch_manual_review_urgency: Decimal = Decimal("0.400000")
    block_manual_review_urgency: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_alignment_gap",
            "block_alignment_gap",
            "watch_source_confidence",
            "block_source_confidence",
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
            "watch_calibration_support",
            "block_calibration_support",
            "watch_manual_review_urgency",
            "block_manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_evidence_age_seconds", "block_evidence_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_rising_threshold(
            "alignment_gap",
            self.watch_alignment_gap,
            self.block_alignment_gap,
        )
        _require_falling_threshold(
            "source_confidence",
            self.watch_source_confidence,
            self.block_source_confidence,
        )
        _require_rising_threshold(
            "evidence_age_seconds",
            self.watch_evidence_age_seconds,
            self.block_evidence_age_seconds,
        )
        _require_rising_threshold(
            "contradiction_pressure",
            self.watch_contradiction_pressure,
            self.block_contradiction_pressure,
        )
        _require_falling_threshold(
            "calibration_support",
            self.watch_calibration_support,
            self.block_calibration_support,
        )
        _require_rising_threshold(
            "manual_review_urgency",
            self.watch_manual_review_urgency,
            self.block_manual_review_urgency,
        )
        require_paper_only_flags(
            "ResearchStrategyProbabilitySourceAlignmentConfig",
            self,
        )


@dataclass(frozen=True)
class ResearchStrategyProbabilitySourceAlignmentInput:
    forecast_probability: Decimal
    evidence_strength_score: Decimal
    source_confidence: Decimal
    evidence_observed_at: datetime
    contradiction_pressure: Decimal
    calibration_support_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "forecast_probability",
            "evidence_strength_score",
            "source_confidence",
            "contradiction_pressure",
            "calibration_support_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        require_paper_only_flags(
            "ResearchStrategyProbabilitySourceAlignmentInput",
            self,
        )


@dataclass(frozen=True)
class ResearchStrategyProbabilitySourceAlignmentRow:
    rank: Decimal
    status: str
    forecast_probability: Decimal
    evidence_strength_score: Decimal
    source_confidence: Decimal
    evidence_observed_at: datetime
    evidence_age_seconds: Decimal
    evidence_recency_score: Decimal
    contradiction_pressure: Decimal
    calibration_support_score: Decimal
    alignment_gap: Decimal
    manual_review_urgency: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "forecast_probability",
            "evidence_strength_score",
            "source_confidence",
            "evidence_recency_score",
            "contradiction_pressure",
            "calibration_support_score",
            "alignment_gap",
            "manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _normalize_nonnegative_count(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_row_reason_code_sequence(self.reason_codes)
        _validate_row(self)
        require_paper_only_flags("ResearchStrategyProbabilitySourceAlignmentRow", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilitySourceAlignmentReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        require_paper_only_flags(
            "ResearchStrategyProbabilitySourceAlignmentReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class ResearchStrategyProbabilitySourceAlignmentReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_forecast_probability: Decimal
    average_evidence_strength_score: Decimal
    average_source_confidence: Decimal
    average_contradiction_pressure: Decimal
    average_calibration_support_score: Decimal
    average_manual_review_urgency: Decimal
    max_manual_review_urgency: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyProbabilitySourceAlignmentReasonCodeCount, ...]
    rows: tuple[ResearchStrategyProbabilitySourceAlignmentRow, ...]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_forecast_probability",
            "average_evidence_strength_score",
            "average_source_confidence",
            "average_contradiction_pressure",
            "average_calibration_support_score",
            "average_manual_review_urgency",
            "max_manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_report_reason_code_sequence(self.reason_codes)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("ResearchStrategyProbabilitySourceAlignmentReport", self)
        expected_digest = _report_public_payload_digest(self)
        if self.public_payload_digest:
            object.__setattr__(
                self,
                "public_payload_digest",
                _normalize_sha256("public_payload_digest", self.public_payload_digest),
            )
            if self.public_payload_digest != expected_digest:
                raise ValueError("public_payload_digest must match report fields")
        else:
            object.__setattr__(self, "public_payload_digest", expected_digest)


def build_research_strategy_probability_source_alignment_report(
    observations: tuple[ResearchStrategyProbabilitySourceAlignmentInput, ...]
    | list[ResearchStrategyProbabilitySourceAlignmentInput],
    *,
    config: ResearchStrategyProbabilitySourceAlignmentConfig,
    generated_at: datetime,
) -> ResearchStrategyProbabilitySourceAlignmentReport:
    if type(config) is not ResearchStrategyProbabilitySourceAlignmentConfig:
        raise ValueError(
            "config must be a ResearchStrategyProbabilitySourceAlignmentConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(observations, generated_at=generated_at_utc)
    rows = _rank_rows(
        tuple(_build_row(row, config=config, generated_at=generated_at_utc) for row in inputs),
    )
    return ResearchStrategyProbabilitySourceAlignmentReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_count(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        average_forecast_probability=_average_field(rows, "forecast_probability"),
        average_evidence_strength_score=_average_field(rows, "evidence_strength_score"),
        average_source_confidence=_average_field(rows, "source_confidence"),
        average_contradiction_pressure=_average_field(rows, "contradiction_pressure"),
        average_calibration_support_score=_average_field(
            rows,
            "calibration_support_score",
        ),
        average_manual_review_urgency=_average_field(rows, "manual_review_urgency"),
        max_manual_review_urgency=_max_field(rows, "manual_review_urgency"),
        status=_status_rollup(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_strategy_probability_source_alignment_report_payload(
    report: ResearchStrategyProbabilitySourceAlignmentReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyProbabilitySourceAlignmentReport:
        raise ValueError("report must be a ResearchStrategyProbabilitySourceAlignmentReport")
    require_paper_only_flags("report", report)
    _validate_report_public_payload_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
    return payload


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
    row: ResearchStrategyProbabilitySourceAlignmentInput,
    *,
    config: ResearchStrategyProbabilitySourceAlignmentConfig,
    generated_at: datetime,
) -> ResearchStrategyProbabilitySourceAlignmentRow:
    evidence_age_seconds = _age_seconds(row.evidence_observed_at, generated_at)
    evidence_recency_score = _remaining_ratio(
        evidence_age_seconds,
        config.block_evidence_age_seconds,
    )
    alignment_gap = _abs_decimal(row.forecast_probability - row.evidence_strength_score)
    manual_review_urgency = _manual_review_urgency(row, alignment_gap=alignment_gap)
    reason_codes = _row_reason_codes(
        alignment_gap=alignment_gap,
        source_confidence=row.source_confidence,
        evidence_age_seconds=evidence_age_seconds,
        contradiction_pressure=row.contradiction_pressure,
        calibration_support_score=row.calibration_support_score,
        manual_review_urgency=manual_review_urgency,
        config=config,
    )
    return ResearchStrategyProbabilitySourceAlignmentRow(
        rank=COUNT_QUANTUM,
        status=_status_from_reason_codes(reason_codes),
        forecast_probability=row.forecast_probability,
        evidence_strength_score=row.evidence_strength_score,
        source_confidence=row.source_confidence,
        evidence_observed_at=row.evidence_observed_at,
        evidence_age_seconds=evidence_age_seconds,
        evidence_recency_score=evidence_recency_score,
        contradiction_pressure=row.contradiction_pressure,
        calibration_support_score=row.calibration_support_score,
        alignment_gap=alignment_gap,
        manual_review_urgency=manual_review_urgency,
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[ResearchStrategyProbabilitySourceAlignmentRow, ...],
) -> tuple[ResearchStrategyProbabilitySourceAlignmentRow, ...]:
    return tuple(
        ResearchStrategyProbabilitySourceAlignmentRow(
            rank=_count(index),
            status=row.status,
            forecast_probability=row.forecast_probability,
            evidence_strength_score=row.evidence_strength_score,
            source_confidence=row.source_confidence,
            evidence_observed_at=row.evidence_observed_at,
            evidence_age_seconds=row.evidence_age_seconds,
            evidence_recency_score=row.evidence_recency_score,
            contradiction_pressure=row.contradiction_pressure,
            calibration_support_score=row.calibration_support_score,
            alignment_gap=row.alignment_gap,
            manual_review_urgency=row.manual_review_urgency,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_reason_codes(
    *,
    alignment_gap: Decimal,
    source_confidence: Decimal,
    evidence_age_seconds: Decimal,
    contradiction_pressure: Decimal,
    calibration_support_score: Decimal,
    manual_review_urgency: Decimal,
    config: ResearchStrategyProbabilitySourceAlignmentConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if alignment_gap >= config.block_alignment_gap:
        reason_codes.append("probability_evidence_gap_block")
    elif alignment_gap >= config.watch_alignment_gap:
        reason_codes.append("probability_evidence_gap_watch")
    else:
        reason_codes.append(PROBABILITY_ALIGNED_REASON_CODE)
    if source_confidence <= config.block_source_confidence:
        reason_codes.append("source_confidence_low_block")
    elif source_confidence <= config.watch_source_confidence:
        reason_codes.append("source_confidence_low_watch")
    if evidence_age_seconds >= config.block_evidence_age_seconds:
        reason_codes.append("evidence_recency_block")
    elif evidence_age_seconds >= config.watch_evidence_age_seconds:
        reason_codes.append("evidence_recency_watch")
    if contradiction_pressure >= config.block_contradiction_pressure:
        reason_codes.append("contradiction_pressure_block")
    elif contradiction_pressure >= config.watch_contradiction_pressure:
        reason_codes.append("contradiction_pressure_watch")
    if calibration_support_score <= config.block_calibration_support:
        reason_codes.append("calibration_support_low_block")
    elif calibration_support_score <= config.watch_calibration_support:
        reason_codes.append("calibration_support_low_watch")
    if manual_review_urgency >= config.block_manual_review_urgency:
        reason_codes.append("manual_review_urgency_block")
    elif manual_review_urgency >= config.watch_manual_review_urgency:
        reason_codes.append("manual_review_urgency_watch")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _manual_review_urgency(
    row: ResearchStrategyProbabilitySourceAlignmentInput,
    *,
    alignment_gap: Decimal,
) -> Decimal:
    return _normalize_probability(
        "manual_review_urgency",
        max(
            alignment_gap,
            ONE - row.source_confidence,
            row.contradiction_pressure,
            ONE - row.calibration_support_score,
        ),
    )


def _normalize_inputs(
    value: tuple[ResearchStrategyProbabilitySourceAlignmentInput, ...]
    | list[ResearchStrategyProbabilitySourceAlignmentInput],
    *,
    generated_at: datetime,
) -> tuple[ResearchStrategyProbabilitySourceAlignmentInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategyProbabilitySourceAlignmentInput:
            raise ValueError(
                "observations must contain ResearchStrategyProbabilitySourceAlignmentInput values",
            )
        require_paper_only_flags("observation", row)
        if row.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be after generated_at")
    return rows


def _normalize_rows(
    value: tuple[ResearchStrategyProbabilitySourceAlignmentRow, ...],
) -> tuple[ResearchStrategyProbabilitySourceAlignmentRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategyProbabilitySourceAlignmentRow:
            raise ValueError("rows must contain probability alignment row values")
        require_paper_only_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    if tuple(row.rank for row in rows) != tuple(
        _count(index) for index in range(1, len(rows) + 1)
    ):
        raise ValueError("rows must use sequential ranks")
    return rows


def _normalize_reason_code_counts(
    value: tuple[ResearchStrategyProbabilitySourceAlignmentReasonCodeCount, ...],
) -> tuple[ResearchStrategyProbabilitySourceAlignmentReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    expected = tuple(sorted(rows, key=lambda row: _row_reason_rank(row.reason_code)))
    if rows != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    for row in rows:
        if type(row) is not ResearchStrategyProbabilitySourceAlignmentReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        require_paper_only_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(row.reason_code)
    return rows


def _reason_code_counts(
    rows: tuple[ResearchStrategyProbabilitySourceAlignmentRow, ...],
) -> tuple[ResearchStrategyProbabilitySourceAlignmentReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyProbabilitySourceAlignmentReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in counter
    )


def _validate_row(row: ResearchStrategyProbabilitySourceAlignmentRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    expected_gap = _abs_decimal(row.forecast_probability - row.evidence_strength_score)
    if row.alignment_gap != expected_gap:
        raise ValueError("alignment_gap must match probability fields")
    expected_urgency = _normalize_probability(
        "manual_review_urgency",
        max(
            row.alignment_gap,
            ONE - row.source_confidence,
            row.contradiction_pressure,
            ONE - row.calibration_support_score,
        ),
    )
    if row.manual_review_urgency != expected_urgency:
        raise ValueError("manual_review_urgency must match row fields")


def _validate_report(report: ResearchStrategyProbabilitySourceAlignmentReport) -> None:
    rows = report.rows
    if report.observation_count != _count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _status_count(rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    for field_name in (
        "forecast_probability",
        "evidence_strength_score",
        "source_confidence",
        "contradiction_pressure",
        "calibration_support_score",
        "manual_review_urgency",
    ):
        report_field_name = (
            f"average_{field_name}"
            if field_name != "manual_review_urgency"
            else "average_manual_review_urgency"
        )
        if getattr(report, report_field_name) != _average_field(rows, field_name):
            raise ValueError(f"{report_field_name} must match rows")
    if report.max_manual_review_urgency != _max_field(rows, "manual_review_urgency"):
        raise ValueError("max_manual_review_urgency must match rows")
    if report.status != _status_rollup(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _validate_report_public_payload_digest(
    report: ResearchStrategyProbabilitySourceAlignmentReport,
) -> None:
    _normalize_sha256("public_payload_digest", report.public_payload_digest)
    if report.public_payload_digest != _report_public_payload_digest(report):
        raise ValueError("public_payload_digest must match report fields")


def _report_public_payload_digest(
    report: ResearchStrategyProbabilitySourceAlignmentReport,
) -> str:
    payload = asdict(report)
    payload.pop("public_payload_digest", None)
    ready = _json_ready(payload)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _status_count(
    rows: tuple[ResearchStrategyProbabilitySourceAlignmentRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_field(
    rows: tuple[ResearchStrategyProbabilitySourceAlignmentRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            field_name,
            sum((getattr(row, field_name) for row in rows), ZERO) / Decimal(len(rows)),
        )


def _max_field(
    rows: tuple[ResearchStrategyProbabilitySourceAlignmentRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _status_rollup(
    rows: tuple[ResearchStrategyProbabilitySourceAlignmentRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return BLOCK_STATUS
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchStrategyProbabilitySourceAlignmentRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    status = _status_rollup(rows)
    codes = [_report_status_reason_code(status)]
    for reason_code in ROW_REASON_CODES:
        if any(reason_code in row.reason_codes for row in rows):
            codes.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _report_status_reason_code(status: str) -> str:
    if status == BLOCK_STATUS:
        return REPORT_BLOCK_REASON_CODE
    if status == WATCH_STATUS:
        return REPORT_WATCH_REASON_CODE
    return REPORT_PASS_REASON_CODE


def _row_sort_key(
    row: ResearchStrategyProbabilitySourceAlignmentRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, datetime]:
    return (
        STATUS_WEIGHT[row.status],
        -row.manual_review_urgency,
        -row.alignment_gap,
        -row.contradiction_pressure,
        row.source_confidence,
        row.calibration_support_score,
        row.evidence_observed_at,
    )


def _row_reason_rank(reason_code: str) -> int:
    return ROW_REASON_CODES.index(reason_code)


def _require_row_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    expected = tuple(
        reason_code
        for group in ROW_REASON_SEQUENCE
        for reason_code in group
        if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    gap_reasons = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code
        in (
            "probability_evidence_gap_block",
            "probability_evidence_gap_watch",
            PROBABILITY_ALIGNED_REASON_CODE,
        )
    )
    if len(gap_reasons) != 1:
        raise ValueError("reason_codes must include exactly one probability reason")


def _require_report_reason_code_sequence(reason_codes: tuple[str, ...]) -> None:
    if reason_codes == (EMPTY_REASON_CODE,):
        return
    expected = tuple(
        reason_code for reason_code in REPORT_REASON_CODES if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    codes = tuple(value)
    if len(codes) != len(set(codes)):
        raise ValueError(f"{name} must not contain duplicates")
    for code in codes:
        _require_member(name, code, allowed)
    return codes


def _age_seconds(older_at: datetime, newer_at: datetime) -> Decimal:
    older = _as_utc("evidence_observed_at", older_at)
    newer = _as_utc("generated_at", newer_at)
    if older > newer:
        raise ValueError("evidence_observed_at must not be after generated_at")
    delta = newer - older
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _normalize_nonnegative_count("evidence_age_seconds", seconds)


def _remaining_ratio(value: Decimal, limit: Decimal) -> Decimal:
    if limit <= ZERO:
        raise ValueError("ratio limit must be positive")
    if value >= limit:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("remaining_ratio", ONE - (value / limit))


def _require_rising_threshold(name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value > block_value:
        raise ValueError(f"watch_{name} must not exceed block_{name}")


def _require_falling_threshold(name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value < block_value:
        raise ValueError(f"watch_{name} must not be below block_{name}")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a nonblank trimmed string")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}")


def _normalize_probability(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{name} must be a whole count")
    return decimal.quantize(COUNT_QUANTUM)


def _normalize_positive_count(name: str, value: object) -> Decimal:
    count = _normalize_nonnegative_count(name, value)
    if count <= ZERO:
        raise ValueError(f"{name} must be positive")
    return count


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative integer")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    return -value if value < ZERO else value


def _normalize_sha256(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a sha256 string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 string")
    return value


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION",
    "ResearchStrategyProbabilitySourceAlignmentConfig",
    "ResearchStrategyProbabilitySourceAlignmentInput",
    "ResearchStrategyProbabilitySourceAlignmentReasonCodeCount",
    "ResearchStrategyProbabilitySourceAlignmentReport",
    "ResearchStrategyProbabilitySourceAlignmentRow",
    "build_research_strategy_probability_source_alignment_report",
    "research_strategy_probability_source_alignment_report_payload",
)
