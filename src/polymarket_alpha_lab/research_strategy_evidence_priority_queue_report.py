"""Pure public evidence priority queue readiness reporting."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_PRIORITY_QUEUE_REPORT_CONFIG_VERSION",
    "ResearchStrategyEvidencePriorityQueueConfig",
    "ResearchStrategyEvidencePriorityQueueGap",
    "ResearchStrategyEvidencePriorityQueueReasonCodeCount",
    "ResearchStrategyEvidencePriorityQueueReport",
    "ResearchStrategyEvidencePriorityQueueRow",
    "build_research_strategy_evidence_priority_queue_report",
    "research_strategy_evidence_priority_queue_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_EVIDENCE_PRIORITY_QUEUE_REPORT_CONFIG_VERSION = (
    "research-strategy-evidence-priority-queue-report-v0"
)
PUBLIC_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchStrategyEvidencePriorityQueueConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVIDENCE_PRIORITY_QUEUE_REPORT_CONFIG_VERSION
    )
    stale_gap_age_hours: Decimal = Decimal("24.000000")
    block_gap_age_hours: Decimal = Decimal("72.000000")
    low_coverage_score: Decimal = Decimal("0.500000")
    watch_review_pressure: Decimal = Decimal("0.350000")
    block_review_pressure: Decimal = Decimal("0.700000")
    watch_priority_score: Decimal = Decimal("0.350000")
    block_priority_score: Decimal = Decimal("0.700000")
    unresolved_review_block_count: Decimal = Decimal("3.000000")
    urgency_weight: Decimal = Decimal("0.450000")
    review_pressure_weight: Decimal = Decimal("0.350000")
    coverage_gap_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidencePriorityQueueConfig, "config")
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVIDENCE_PRIORITY_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "stale_gap_age_hours",
            "block_gap_age_hours",
            "unresolved_review_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "low_coverage_score",
            "watch_review_pressure",
            "block_review_pressure",
            "watch_priority_score",
            "block_priority_score",
            "urgency_weight",
            "review_pressure_weight",
            "coverage_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_gap_age_hours >= self.block_gap_age_hours:
            raise ValueError("stale_gap_age_hours must be below block_gap_age_hours")
        if self.watch_review_pressure >= self.block_review_pressure:
            raise ValueError("watch_review_pressure must be below block_review_pressure")
        if self.watch_priority_score >= self.block_priority_score:
            raise ValueError("watch_priority_score must be below block_priority_score")
        weight_sum = _quantize(
            self.urgency_weight
            + self.review_pressure_weight
            + self.coverage_gap_weight,
        )
        if weight_sum != ONE:
            raise ValueError("weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEvidencePriorityQueueGap(_FinalDataclass):
    public_gap_label: str
    evidence_gap_code: str
    gap_age_hours: Decimal
    evidence_coverage_score: Decimal
    review_pressure_score: Decimal
    unresolved_review_count: Decimal
    upstream_status: str = "pass"
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidencePriorityQueueGap, "gap")
        _require_public_label("public_gap_label", self.public_gap_label)
        _require_reason_code("evidence_gap_code", self.evidence_gap_code)
        object.__setattr__(
            self,
            "gap_age_hours",
            _require_nonnegative_decimal("gap_age_hours", self.gap_age_hours),
        )
        for field_name in ("evidence_coverage_score", "review_pressure_score"):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_review_count",
            _require_nonnegative_whole_decimal(
                "unresolved_review_count",
                self.unresolved_review_count,
            ),
        )
        _require_status("upstream_status", self.upstream_status)
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
                allow_empty=True,
            ),
        )
        _require_hard_flags("gap", self)


@dataclass(frozen=True)
class ResearchStrategyEvidencePriorityQueueRow(_FinalDataclass):
    queue_rank: Decimal
    public_gap_label: str
    evidence_gap_code: str
    gap_age_hours: Decimal
    evidence_coverage_score: Decimal
    review_pressure_score: Decimal
    unresolved_review_count: Decimal
    upstream_status: str
    gap_age_pressure_score: Decimal
    coverage_gap_score: Decimal
    urgency_score: Decimal
    review_load_score: Decimal
    priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidencePriorityQueueRow, "row")
        object.__setattr__(
            self,
            "queue_rank",
            _require_positive_whole_decimal("queue_rank", self.queue_rank),
        )
        _require_public_label("public_gap_label", self.public_gap_label)
        _require_reason_code("evidence_gap_code", self.evidence_gap_code)
        object.__setattr__(
            self,
            "gap_age_hours",
            _require_nonnegative_decimal("gap_age_hours", self.gap_age_hours),
        )
        for field_name in (
            "evidence_coverage_score",
            "review_pressure_score",
            "gap_age_pressure_score",
            "coverage_gap_score",
            "urgency_score",
            "review_load_score",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_review_count",
            _require_nonnegative_whole_decimal(
                "unresolved_review_count",
                self.unresolved_review_count,
            ),
        )
        _require_status("upstream_status", self.upstream_status)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        expected_digest = _payload_digest(_row_payload(self, include_digest=False))
        if self.validation_digest == "":
            object.__setattr__(self, "validation_digest", expected_digest)
        elif self.validation_digest != expected_digest:
            raise ValueError("validation_digest must match row payload")


@dataclass(frozen=True)
class ResearchStrategyEvidencePriorityQueueReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEvidencePriorityQueueReasonCodeCount,
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
class ResearchStrategyEvidencePriorityQueueReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    status: str
    gap_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_priority_score: Decimal | None
    max_priority_score: Decimal | None
    rows: tuple[ResearchStrategyEvidencePriorityQueueRow, ...]
    reason_code_counts: tuple[ResearchStrategyEvidencePriorityQueueReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidencePriorityQueueReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in ("gap_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_priority_score", "max_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_unit_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _payload_digest(_report_payload(self, include_digest=False))
        if self.validation_digest == "":
            object.__setattr__(self, "validation_digest", expected_digest)
        elif self.validation_digest != expected_digest:
            raise ValueError("validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_evidence_priority_queue_report_payload(self)


def build_research_strategy_evidence_priority_queue_report(
    evidence_gaps: Iterable[object],
    *,
    config: ResearchStrategyEvidencePriorityQueueConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategyEvidencePriorityQueueReport:
    cfg = config or ResearchStrategyEvidencePriorityQueueConfig()
    if type(cfg) is not ResearchStrategyEvidencePriorityQueueConfig:
        raise ValueError(
            "config must be a ResearchStrategyEvidencePriorityQueueConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    gaps = _normalize_gap_inputs(evidence_gaps)
    ranked_rows = _rank_rows(
        tuple(_row_from_gap(gap, config=cfg, queue_rank=ONE) for gap in gaps),
    )
    reason_codes = _summary_reason_codes(ranked_rows)
    return ResearchStrategyEvidencePriorityQueueReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=_summary_status(ranked_rows),
        gap_count=_decimal_count(len(ranked_rows)),
        pass_count=_decimal_count(_status_count(ranked_rows, "pass")),
        watch_count=_decimal_count(_status_count(ranked_rows, "watch")),
        block_count=_decimal_count(_status_count(ranked_rows, "block")),
        average_priority_score=_average_optional(
            tuple(row.priority_score for row in ranked_rows),
        ),
        max_priority_score=max((row.priority_score for row in ranked_rows), default=None),
        rows=ranked_rows,
        reason_code_counts=_reason_code_counts(ranked_rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_evidence_priority_queue_report_payload(
    report: ResearchStrategyEvidencePriorityQueueReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyEvidencePriorityQueueReport:
        raise ValueError("report must be a ResearchStrategyEvidencePriorityQueueReport")
    _require_hard_flags("report", report)
    payload = _report_payload(report, include_digest=True)
    _reject_unsafe_public_payload("report_payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_gap(
    gap: ResearchStrategyEvidencePriorityQueueGap,
    *,
    config: ResearchStrategyEvidencePriorityQueueConfig,
    queue_rank: Decimal,
) -> ResearchStrategyEvidencePriorityQueueRow:
    gap_age_pressure_score = _bounded_ratio(
        gap.gap_age_hours,
        config.block_gap_age_hours,
    )
    coverage_gap_score = _inverse_unit(gap.evidence_coverage_score)
    urgency_score = _quantize((gap_age_pressure_score + coverage_gap_score) / Decimal("2"))
    review_load_score = max(
        gap.review_pressure_score,
        _bounded_ratio(gap.unresolved_review_count, config.unresolved_review_block_count),
    )
    priority_score = _quantize(
        (urgency_score * config.urgency_weight)
        + (review_load_score * config.review_pressure_weight)
        + (coverage_gap_score * config.coverage_gap_weight),
    )
    status = _row_status(
        gap,
        config=config,
        priority_score=priority_score,
    )
    return ResearchStrategyEvidencePriorityQueueRow(
        queue_rank=queue_rank,
        public_gap_label=gap.public_gap_label,
        evidence_gap_code=gap.evidence_gap_code,
        gap_age_hours=gap.gap_age_hours,
        evidence_coverage_score=gap.evidence_coverage_score,
        review_pressure_score=gap.review_pressure_score,
        unresolved_review_count=gap.unresolved_review_count,
        upstream_status=gap.upstream_status,
        gap_age_pressure_score=gap_age_pressure_score,
        coverage_gap_score=coverage_gap_score,
        urgency_score=urgency_score,
        review_load_score=review_load_score,
        priority_score=priority_score,
        status=status,
        reason_codes=_row_reason_codes(gap, status=status, config=config),
    )


def _rank_rows(
    rows: tuple[ResearchStrategyEvidencePriorityQueueRow, ...],
) -> tuple[ResearchStrategyEvidencePriorityQueueRow, ...]:
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            -row.priority_score,
            _status_rank(row.status),
            row.public_gap_label,
        ),
    )
    return tuple(
        ResearchStrategyEvidencePriorityQueueRow(
            queue_rank=_decimal_count(index),
            public_gap_label=row.public_gap_label,
            evidence_gap_code=row.evidence_gap_code,
            gap_age_hours=row.gap_age_hours,
            evidence_coverage_score=row.evidence_coverage_score,
            review_pressure_score=row.review_pressure_score,
            unresolved_review_count=row.unresolved_review_count,
            upstream_status=row.upstream_status,
            gap_age_pressure_score=row.gap_age_pressure_score,
            coverage_gap_score=row.coverage_gap_score,
            urgency_score=row.urgency_score,
            review_load_score=row.review_load_score,
            priority_score=row.priority_score,
            status=row.status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted_rows, start=1)
    )


def _row_status(
    gap: ResearchStrategyEvidencePriorityQueueGap,
    *,
    config: ResearchStrategyEvidencePriorityQueueConfig,
    priority_score: Decimal,
) -> str:
    if gap.upstream_status == "block":
        return "block"
    if gap.gap_age_hours >= config.block_gap_age_hours:
        return "block"
    if gap.review_pressure_score >= config.block_review_pressure:
        return "block"
    if gap.unresolved_review_count >= config.unresolved_review_block_count:
        return "block"
    if priority_score >= config.block_priority_score:
        return "block"
    if gap.upstream_status == "watch":
        return "watch"
    if gap.gap_age_hours >= config.stale_gap_age_hours:
        return "watch"
    if gap.review_pressure_score >= config.watch_review_pressure:
        return "watch"
    if gap.evidence_coverage_score < config.low_coverage_score:
        return "watch"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    gap: ResearchStrategyEvidencePriorityQueueGap,
    *,
    status: str,
    config: ResearchStrategyEvidencePriorityQueueConfig,
) -> tuple[str, ...]:
    reason_codes = {f"evidence_priority_{status}", f"upstream_status_{gap.upstream_status}"}
    if gap.gap_age_hours >= config.block_gap_age_hours:
        reason_codes.add("evidence_gap_age_block")
    elif gap.gap_age_hours >= config.stale_gap_age_hours:
        reason_codes.add("evidence_gap_age_watch")
    else:
        reason_codes.add("evidence_gap_age_low")
    if gap.evidence_coverage_score < config.low_coverage_score:
        reason_codes.add(
            "coverage_gap_block" if status == "block" else "coverage_gap_watch",
        )
    else:
        reason_codes.add("coverage_gap_low")
    if (
        gap.review_pressure_score >= config.block_review_pressure
        or gap.unresolved_review_count >= config.unresolved_review_block_count
    ):
        reason_codes.add("review_pressure_block")
    elif gap.review_pressure_score >= config.watch_review_pressure:
        reason_codes.add("review_pressure_watch")
    else:
        reason_codes.add("review_pressure_low")
    for reason_code in gap.upstream_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _normalize_gap_inputs(
    evidence_gaps: Iterable[object],
) -> tuple[ResearchStrategyEvidencePriorityQueueGap, ...]:
    if isinstance(evidence_gaps, (str, bytes)):
        raise ValueError("evidence_gaps must be an iterable")
    try:
        values = tuple(evidence_gaps)
    except TypeError as exc:
        raise ValueError("evidence_gaps must be an iterable") from exc
    return tuple(_coerce_gap_input(value) for value in values)


def _coerce_gap_input(value: object) -> ResearchStrategyEvidencePriorityQueueGap:
    if type(value) is ResearchStrategyEvidencePriorityQueueGap:
        _require_hard_flags("gap", value)
        return value
    if type(value) is ResearchStrategyEvidencePriorityQueueRow:
        _require_hard_flags("row", value)
        return ResearchStrategyEvidencePriorityQueueGap(
            public_gap_label=value.public_gap_label,
            evidence_gap_code=value.evidence_gap_code,
            gap_age_hours=value.gap_age_hours,
            evidence_coverage_score=value.evidence_coverage_score,
            review_pressure_score=value.review_pressure_score,
            unresolved_review_count=value.unresolved_review_count,
            upstream_status=value.upstream_status,
            upstream_reason_codes=tuple(
                reason_code.removeprefix("input_")
                for reason_code in value.reason_codes
                if reason_code.startswith("input_")
            ),
            paper_only=value.paper_only,
            report_only=value.report_only,
            readonly=value.readonly,
        )
    _reject_unsafe_supplied_public_fields(value)
    _require_hard_flags("gap", value)
    return ResearchStrategyEvidencePriorityQueueGap(
        public_gap_label=_field_value(value, "public_gap_label"),
        evidence_gap_code=_field_value(value, "evidence_gap_code"),
        gap_age_hours=_field_value(value, "gap_age_hours"),
        evidence_coverage_score=_field_value(value, "evidence_coverage_score"),
        review_pressure_score=_field_value(value, "review_pressure_score"),
        unresolved_review_count=_field_value(value, "unresolved_review_count"),
        upstream_status=_field_value(value, "upstream_status", default="pass"),
        upstream_reason_codes=_field_value(
            value,
            "upstream_reason_codes",
            default=(),
        ),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchStrategyEvidencePriorityQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_evidence_gaps",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchStrategyEvidencePriorityQueueRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategyEvidencePriorityQueueRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyEvidencePriorityQueueReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyEvidencePriorityQueueReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchStrategyEvidencePriorityQueueReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(rows: tuple[ResearchStrategyEvidencePriorityQueueRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_optional(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyEvidencePriorityQueueRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchStrategyEvidencePriorityQueueRow] = []
    for row in rows:
        if type(row) is not ResearchStrategyEvidencePriorityQueueRow:
            raise ValueError("rows must contain ResearchStrategyEvidencePriorityQueueRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(normalized)


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchStrategyEvidencePriorityQueueReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchStrategyEvidencePriorityQueueReasonCodeCount] = []
    seen: set[str] = set()
    for value in values:
        if type(value) is not ResearchStrategyEvidencePriorityQueueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEvidencePriorityQueueReasonCodeCount",
            )
        if value.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(value.reason_code)
        normalized.append(value)
    return tuple(sorted(normalized, key=lambda item: item.reason_code))


def _validate_report_consistency(
    report: ResearchStrategyEvidencePriorityQueueReport,
) -> None:
    rows = report.rows
    if report.gap_count != _decimal_count(len(rows)):
        raise ValueError("gap_count must match rows")
    for status in PUBLIC_STATUSES:
        field_name = f"{status}_count"
        if getattr(report, field_name) != _decimal_count(_status_count(rows, status)):
            raise ValueError(f"{field_name} must match rows")
    if report.status != _summary_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.average_priority_score != _average_optional(
        tuple(row.priority_score for row in rows),
    ):
        raise ValueError("average_priority_score must match rows")
    if report.max_priority_score != max((row.priority_score for row in rows), default=None):
        raise ValueError("max_priority_score must match rows")


def _report_payload(
    report: ResearchStrategyEvidencePriorityQueueReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    if include_digest:
        payload["validation_digest"] = report.validation_digest
    else:
        payload.pop("validation_digest", None)
    return payload


def _row_payload(
    row: ResearchStrategyEvidencePriorityQueueRow,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = _json_ready(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    if include_digest:
        payload["validation_digest"] = row.validation_digest
    else:
        payload.pop("validation_digest", None)
    return payload


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("value is not JSON-ready")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _reject_unsafe_supplied_public_fields(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name) and getattr(value, field.name) is not None:
                raise ValueError("unsafe public fields are not allowed")
    for field_name in _unsafe_public_field_names():
        if _field_value(value, field_name, default=None) is not None:
            raise ValueError("unsafe public fields are not allowed")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{current_path}.{key} has unsafe public field")
            _reject_unsafe_public_payload(label, item, key if not path else f"{path}.{key}")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"{current_path} has unsafe public value")


def _unsafe_public_field_names() -> tuple[str, ...]:
    return (
        "candidate" + "_id",
        "market" + "_id",
        "market" + "_slug",
        "slug",
        "question",
        "url",
        "source" + "_text",
        "dsn",
        "ta" + "ble",
        "to" + "ken",
        "wal" + "let",
        "or" + "der",
        "tra" + "de",
    )


def _unsafe_public_value_fragments() -> tuple[str, ...]:
    return (
        *_unsafe_public_field_names(),
        "://" ,
        "?" ,
        "b" + "uy",
        "se" + "ll",
        "reco" + "mmend",
        "siz" + "ing",
        "au" + "th",
        "li" + "ve",
        "data" + "base",
    )


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _unsafe_public_value_fragments())


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_unit_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_unit_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} must avoid unsafe public terms")


def _require_public_label(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    if ":" in value or "/" in value or "\\" in value:
        raise ValueError(f"{field_name} must avoid unsafe public terms")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    if value != value.lower() or not value.replace("_", "").isalnum():
        raise ValueError(f"{field_name} must contain lowercase reason codes")


def _require_status(field_name: str, value: object) -> None:
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


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


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name, default=None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    if numerator <= ZERO:
        return ZERO
    ratio = numerator / denominator
    if ratio >= ONE:
        return ONE
    return _quantize(ratio)


def _inverse_unit(value: Decimal) -> Decimal:
    return _quantize(ONE - value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _status_rank(status: str) -> int:
    return {"block": 0, "watch": 1, "pass": 2}[status]
