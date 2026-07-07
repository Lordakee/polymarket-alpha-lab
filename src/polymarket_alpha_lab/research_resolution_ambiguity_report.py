"""Pure read-only report for resolution ambiguity in prediction-market research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MINUTES_PER_SECOND = Decimal("60.000000")
DECIMAL_CONTEXT_PRECISION = 28

EVIDENCE_KINDS = (
    "adjudicator_statement",
    "market_snapshot",
    "official_rules",
    "primary_source",
    "secondary_source",
)
ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "adjudication_dependency_high",
    "adjudication_dependency_low",
    "adjudication_dependency_watch",
    "evidence_conflict_high",
    "evidence_conflict_low",
    "evidence_conflict_watch",
    "near_resolution_window",
    "no_resolution_evidence",
    "outside_near_resolution_window",
    "resolution_ambiguity_blocked",
    "resolution_ambiguity_pass",
    "resolution_ambiguity_watch",
    "settlement_rules_clear",
    "settlement_rules_opaque",
    "settlement_rules_watch",
)


@dataclass(frozen=True)
class ResearchResolutionAmbiguityConfig:
    config_version: str
    near_resolution_window_minutes: Decimal
    pass_max_risk_score: Decimal
    watch_max_risk_score: Decimal
    rule_ambiguity_weight: Decimal
    adjudication_dependency_weight: Decimal
    evidence_conflict_weight: Decimal
    near_resolution_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "near_resolution_window_minutes",
            _normalize_positive_decimal(
                "near_resolution_window_minutes",
                self.near_resolution_window_minutes,
            ),
        )
        for field_name in ("pass_max_risk_score", "watch_max_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.pass_max_risk_score > self.watch_max_risk_score:
            raise ValueError("pass_max_risk_score must be <= watch_max_risk_score")
        for field_name in (
            "rule_ambiguity_weight",
            "adjudication_dependency_weight",
            "evidence_conflict_weight",
            "near_resolution_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_weights_total_one(self)
        require_paper_only_flags("ResearchResolutionAmbiguityConfig", self)
        reject_unsafe_surface_fields("resolution ambiguity config", self)


@dataclass(frozen=True)
class ResearchResolutionAmbiguityEvidence:
    event_ref: str
    evidence_ref: str
    evidence_kind: str
    observed_at: datetime
    resolution_at: datetime
    settlement_rule_clarity: Decimal
    adjudication_dependency: Decimal
    evidence_conflict: Decimal
    market_question: str | None = None
    market_slug: str | None = None
    market_id: str | None = None
    source_url: str | None = None
    source_text: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("event_ref", "evidence_ref"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("evidence_kind", self.evidence_kind, EVIDENCE_KINDS)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolution_at",
            _as_utc("resolution_at", self.resolution_at),
        )
        if self.resolution_at <= self.observed_at:
            raise ValueError("resolution_at must be after observed_at")
        for field_name in (
            "settlement_rule_clarity",
            "adjudication_dependency",
            "evidence_conflict",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "market_question",
            "market_slug",
            "market_id",
            "source_url",
            "source_text",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_string(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("ResearchResolutionAmbiguityEvidence", self)
        reject_unsafe_surface_fields("resolution ambiguity evidence", self)


@dataclass(frozen=True)
class ResearchResolutionAmbiguityRow:
    row_number: Decimal
    event_ref: str
    evidence_count: Decimal
    minutes_to_resolution: Decimal
    rule_ambiguity_score: Decimal
    adjudication_dependency_score: Decimal
    evidence_conflict_score: Decimal
    near_resolution_score: Decimal
    resolution_risk_score: Decimal
    status: str
    evidence_refs: tuple[str, ...]
    evidence_kinds: tuple[str, ...]
    reason_codes: tuple[str, ...]
    rule_ambiguity_weight: Decimal
    adjudication_dependency_weight: Decimal
    evidence_conflict_weight: Decimal
    near_resolution_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "row_number",
            _normalize_nonnegative_count("row_number", self.row_number),
        )
        _require_canonical_string("event_ref", self.event_ref)
        object.__setattr__(
            self,
            "evidence_count",
            _normalize_nonnegative_count("evidence_count", self.evidence_count),
        )
        object.__setattr__(
            self,
            "minutes_to_resolution",
            _normalize_nonnegative_decimal(
                "minutes_to_resolution",
                self.minutes_to_resolution,
            ),
        )
        for field_name in (
            "rule_ambiguity_score",
            "adjudication_dependency_score",
            "evidence_conflict_score",
            "near_resolution_score",
            "resolution_risk_score",
            "rule_ambiguity_weight",
            "adjudication_dependency_weight",
            "evidence_conflict_weight",
            "near_resolution_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_string_tuple("evidence_refs", self.evidence_refs),
        )
        object.__setattr__(
            self,
            "evidence_kinds",
            _normalize_evidence_kinds(self.evidence_kinds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_row_weights_total_one(self)
        _validate_row(self)
        require_paper_only_flags("ResearchResolutionAmbiguityRow", self)
        reject_unsafe_surface_fields("resolution ambiguity row", self)


@dataclass(frozen=True)
class ResearchResolutionAmbiguityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        require_paper_only_flags("ResearchResolutionAmbiguityReasonCodeCount", self)
        reject_unsafe_surface_fields("resolution ambiguity reason code count", self)


@dataclass(frozen=True)
class ResearchResolutionAmbiguityReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_risk_score: Decimal | None
    status: str
    rows: tuple[ResearchResolutionAmbiguityRow, ...]
    reason_code_counts: tuple[ResearchResolutionAmbiguityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.average_risk_score is not None:
            object.__setattr__(
                self,
                "average_risk_score",
                _normalize_probability("average_risk_score", self.average_risk_score),
            )
        _require_member("status", self.status, REPORT_STATUSES)
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
        _validate_report(self)
        require_paper_only_flags("ResearchResolutionAmbiguityReport", self)
        reject_unsafe_surface_fields("resolution ambiguity report", self)


def build_research_resolution_ambiguity_report(
    evidence_rows: Iterable[object],
    *,
    config: ResearchResolutionAmbiguityConfig,
    generated_at: datetime,
) -> ResearchResolutionAmbiguityReport:
    if type(config) is not ResearchResolutionAmbiguityConfig:
        raise ValueError("config must be a ResearchResolutionAmbiguityConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence_rows(evidence_rows)
    for item in evidence_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must be <= generated_at")
        if item.resolution_at <= generated_at_utc:
            raise ValueError("resolution_at must be after generated_at")

    grouped: dict[str, list[ResearchResolutionAmbiguityEvidence]] = {}
    for item in evidence_items:
        grouped.setdefault(item.event_ref, []).append(item)

    rows = tuple(
        _score_event(
            row_number=_decimal_count(index),
            event_ref=event_ref,
            evidence_rows=tuple(grouped[event_ref]),
            config=config,
            generated_at=generated_at_utc,
        )
        for index, event_ref in enumerate(sorted(grouped), start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    counted_reason_codes = _all_reason_codes(rows)
    return ResearchResolutionAmbiguityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_decimal_count(len(rows)),
        evidence_count=_decimal_count(len(evidence_items)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "blocked")),
        average_risk_score=_average_risk_score(rows),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, counted_reason_codes),
        reason_codes=reason_codes,
    )


def research_resolution_ambiguity_report_payload(
    report: ResearchResolutionAmbiguityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionAmbiguityReport:
        raise ValueError("report must be a ResearchResolutionAmbiguityReport")
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "event_count": report.event_count,
            "evidence_count": report.evidence_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "blocked_count": report.blocked_count,
            "average_risk_score": report.average_risk_score,
            "status": report.status,
            "rows": tuple(_row_payload(row) for row in report.rows),
            "reason_code_counts": tuple(
                {
                    "reason_code": item.reason_code,
                    "count": item.count,
                }
                for item in report.reason_code_counts
            ),
            "reason_codes": report.reason_codes,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("resolution ambiguity public payload", payload)
    return payload


def _score_event(
    *,
    row_number: Decimal,
    event_ref: str,
    evidence_rows: tuple[ResearchResolutionAmbiguityEvidence, ...],
    config: ResearchResolutionAmbiguityConfig,
    generated_at: datetime,
) -> ResearchResolutionAmbiguityRow:
    evidence_count = _decimal_count(len(evidence_rows))
    rule_ambiguity_score = _rule_ambiguity_score(evidence_rows)
    adjudication_dependency_score = _max_probability(
        row.adjudication_dependency for row in evidence_rows
    )
    evidence_conflict_score = _max_probability(row.evidence_conflict for row in evidence_rows)
    minutes_to_resolution = _minutes_to_resolution(evidence_rows, generated_at)
    near_resolution_score = _near_resolution_score(minutes_to_resolution, config)
    resolution_risk_score = _weighted_risk_score(
        rule_ambiguity_score=rule_ambiguity_score,
        adjudication_dependency_score=adjudication_dependency_score,
        evidence_conflict_score=evidence_conflict_score,
        near_resolution_score=near_resolution_score,
        rule_ambiguity_weight=config.rule_ambiguity_weight,
        adjudication_dependency_weight=config.adjudication_dependency_weight,
        evidence_conflict_weight=config.evidence_conflict_weight,
        near_resolution_weight=config.near_resolution_weight,
    )
    status = _row_status(resolution_risk_score, config)
    return ResearchResolutionAmbiguityRow(
        row_number=row_number,
        event_ref=event_ref,
        evidence_count=evidence_count,
        minutes_to_resolution=minutes_to_resolution,
        rule_ambiguity_score=rule_ambiguity_score,
        adjudication_dependency_score=adjudication_dependency_score,
        evidence_conflict_score=evidence_conflict_score,
        near_resolution_score=near_resolution_score,
        resolution_risk_score=resolution_risk_score,
        status=status,
        evidence_refs=tuple(sorted(row.evidence_ref for row in evidence_rows)),
        evidence_kinds=tuple(sorted({row.evidence_kind for row in evidence_rows})),
        reason_codes=_row_reason_codes(
            rule_ambiguity_score=rule_ambiguity_score,
            adjudication_dependency_score=adjudication_dependency_score,
            evidence_conflict_score=evidence_conflict_score,
            near_resolution_score=near_resolution_score,
            status=status,
        ),
        rule_ambiguity_weight=config.rule_ambiguity_weight,
        adjudication_dependency_weight=config.adjudication_dependency_weight,
        evidence_conflict_weight=config.evidence_conflict_weight,
        near_resolution_weight=config.near_resolution_weight,
    )


def _row_payload(row: ResearchResolutionAmbiguityRow) -> dict[str, object]:
    require_paper_only_flags("row", row)
    return {
        "row_number": row.row_number,
        "evidence_count": row.evidence_count,
        "minutes_to_resolution": row.minutes_to_resolution,
        "rule_ambiguity_score": row.rule_ambiguity_score,
        "adjudication_dependency_score": row.adjudication_dependency_score,
        "evidence_conflict_score": row.evidence_conflict_score,
        "near_resolution_score": row.near_resolution_score,
        "resolution_risk_score": row.resolution_risk_score,
        "status": row.status,
        "evidence_kinds": row.evidence_kinds,
        "reason_codes": row.reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _rule_ambiguity_score(
    evidence_rows: tuple[ResearchResolutionAmbiguityEvidence, ...],
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        clarity = sum((row.settlement_rule_clarity for row in evidence_rows), ZERO)
        average_clarity = clarity / _decimal_count(len(evidence_rows))
    return _normalize_probability("rule_ambiguity_score", ONE - average_clarity)


def _max_probability(values: Iterable[Decimal]) -> Decimal:
    return max(values, default=ZERO).quantize(SCORE_QUANT)


def _minutes_to_resolution(
    evidence_rows: tuple[ResearchResolutionAmbiguityEvidence, ...],
    generated_at: datetime,
) -> Decimal:
    resolution_at = min(row.resolution_at for row in evidence_rows)
    seconds = Decimal(str((resolution_at - generated_at).total_seconds()))
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        minutes = seconds / MINUTES_PER_SECOND
    return _normalize_nonnegative_decimal("minutes_to_resolution", minutes)


def _near_resolution_score(
    minutes_to_resolution: Decimal,
    config: ResearchResolutionAmbiguityConfig,
) -> Decimal:
    if minutes_to_resolution >= config.near_resolution_window_minutes:
        return ZERO
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        score = (config.near_resolution_window_minutes - minutes_to_resolution) / (
            config.near_resolution_window_minutes
        )
    return _normalize_probability("near_resolution_score", score)


def _weighted_risk_score(
    *,
    rule_ambiguity_score: Decimal,
    adjudication_dependency_score: Decimal,
    evidence_conflict_score: Decimal,
    near_resolution_score: Decimal,
    rule_ambiguity_weight: Decimal,
    adjudication_dependency_weight: Decimal,
    evidence_conflict_weight: Decimal,
    near_resolution_weight: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        score = (
            rule_ambiguity_score * rule_ambiguity_weight
            + adjudication_dependency_score * adjudication_dependency_weight
            + evidence_conflict_score * evidence_conflict_weight
            + near_resolution_score * near_resolution_weight
        )
    return _normalize_probability("resolution_risk_score", score)


def _row_status(
    resolution_risk_score: Decimal,
    config: ResearchResolutionAmbiguityConfig,
) -> str:
    if resolution_risk_score <= config.pass_max_risk_score:
        return "pass"
    if resolution_risk_score <= config.watch_max_risk_score:
        return "watch"
    return "blocked"


def _row_reason_codes(
    *,
    rule_ambiguity_score: Decimal,
    adjudication_dependency_score: Decimal,
    evidence_conflict_score: Decimal,
    near_resolution_score: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes = [
        _band_reason(
            rule_ambiguity_score,
            low="settlement_rules_clear",
            watch="settlement_rules_watch",
            high="settlement_rules_opaque",
        ),
        _band_reason(
            adjudication_dependency_score,
            low="adjudication_dependency_low",
            watch="adjudication_dependency_watch",
            high="adjudication_dependency_high",
        ),
        _band_reason(
            evidence_conflict_score,
            low="evidence_conflict_low",
            watch="evidence_conflict_watch",
            high="evidence_conflict_high",
        ),
        (
            "near_resolution_window"
            if near_resolution_score > ZERO
            else "outside_near_resolution_window"
        ),
        f"resolution_ambiguity_{status}",
    ]
    return tuple(sorted(reason_codes))


def _band_reason(value: Decimal, *, low: str, watch: str, high: str) -> str:
    if value <= Decimal("0.250000"):
        return low
    if value >= Decimal("0.750000"):
        return high
    return watch


def _summary_reason_codes(
    rows: tuple[ResearchResolutionAmbiguityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_evidence",)
    return tuple(sorted({f"resolution_ambiguity_{row.status}" for row in rows}))


def _all_reason_codes(
    rows: tuple[ResearchResolutionAmbiguityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_evidence",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchResolutionAmbiguityRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(rows: tuple[ResearchResolutionAmbiguityRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_risk_score(
    rows: tuple[ResearchResolutionAmbiguityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        average = sum((row.resolution_risk_score for row in rows), ZERO) / _decimal_count(
            len(rows),
        )
    return _normalize_probability("average_risk_score", average)


def _reason_code_counts(
    rows: tuple[ResearchResolutionAmbiguityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchResolutionAmbiguityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchResolutionAmbiguityReasonCodeCount(
                reason_code="no_resolution_evidence",
                count=_decimal_count(1),
            ),
        )
    return tuple(
        ResearchResolutionAmbiguityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
        )
        for reason_code in reason_codes
    )


def _validate_row(row: ResearchResolutionAmbiguityRow) -> None:
    expected_score = _weighted_risk_score(
        rule_ambiguity_score=row.rule_ambiguity_score,
        adjudication_dependency_score=row.adjudication_dependency_score,
        evidence_conflict_score=row.evidence_conflict_score,
        near_resolution_score=row.near_resolution_score,
        rule_ambiguity_weight=row.rule_ambiguity_weight,
        adjudication_dependency_weight=row.adjudication_dependency_weight,
        evidence_conflict_weight=row.evidence_conflict_weight,
        near_resolution_weight=row.near_resolution_weight,
    )
    if row.resolution_risk_score != expected_score:
        raise ValueError("resolution_risk_score must match component scores")
    if row.evidence_count != _decimal_count(len(row.evidence_refs)):
        raise ValueError("evidence_count must match evidence_refs")
    if row.reason_codes != _row_reason_codes(
        rule_ambiguity_score=row.rule_ambiguity_score,
        adjudication_dependency_score=row.adjudication_dependency_score,
        evidence_conflict_score=row.evidence_conflict_score,
        near_resolution_score=row.near_resolution_score,
        status=row.status,
    ):
        raise ValueError("reason_codes must match row scores")


def _validate_report(report: ResearchResolutionAmbiguityReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.evidence_count != sum((row.evidence_count for row in report.rows), ZERO):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_risk_score != _average_risk_score(report.rows):
        raise ValueError("average_risk_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, _all_reason_codes(report.rows)):
        raise ValueError("reason_code_counts must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")


def _normalize_evidence_rows(
    evidence_rows: Iterable[object],
) -> tuple[ResearchResolutionAmbiguityEvidence, ...]:
    if isinstance(evidence_rows, (str, bytes)):
        raise ValueError("evidence_rows must be an iterable")
    try:
        rows = tuple(evidence_rows)
    except TypeError as exc:
        raise ValueError("evidence_rows must be an iterable") from exc
    return tuple(_coerce_evidence_row(row) for row in rows)


def _coerce_evidence_row(row: object) -> ResearchResolutionAmbiguityEvidence:
    if type(row) is ResearchResolutionAmbiguityEvidence:
        return row
    return ResearchResolutionAmbiguityEvidence(
        event_ref=_field_value(row, "event_ref"),
        evidence_ref=_field_value(row, "evidence_ref"),
        evidence_kind=_field_value(row, "evidence_kind"),
        observed_at=_field_value(row, "observed_at"),
        resolution_at=_field_value(row, "resolution_at"),
        settlement_rule_clarity=_field_value(row, "settlement_rule_clarity"),
        adjudication_dependency=_field_value(row, "adjudication_dependency"),
        evidence_conflict=_field_value(row, "evidence_conflict"),
        market_question=_field_value(row, "market_question", default=None),
        market_slug=_field_value(row, "market_slug", default=None),
        market_id=_field_value(row, "market_id", default=None),
        source_url=_field_value(row, "source_url", default=None),
        source_text=_field_value(row, "source_text", default=None),
        paper_only=_field_value(row, "paper_only", default=True),
        report_only=_field_value(row, "report_only", default=True),
        readonly=_field_value(row, "readonly", default=True),
    )


_MISSING = object()


def _field_value(row: object, field_name: str, *, default: object = _MISSING) -> Any:
    if hasattr(row, field_name):
        return getattr(row, field_name)
    if default is _MISSING:
        raise ValueError(f"{field_name} is required")
    return default


def _normalize_rows(rows: object) -> tuple[ResearchResolutionAmbiguityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain ResearchResolutionAmbiguityRow values")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain ResearchResolutionAmbiguityRow values") from exc
    for row in normalized:
        if type(row) is not ResearchResolutionAmbiguityRow:
            raise ValueError("rows must contain ResearchResolutionAmbiguityRow values")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchResolutionAmbiguityReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for row in normalized:
        if type(row) is not ResearchResolutionAmbiguityReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code counts")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    normalized = _normalize_string_tuple(field_name, values)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for value in normalized:
        _require_member(field_name, value, REASON_CODES)
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)
    return normalized


def _normalize_evidence_kinds(values: object) -> tuple[str, ...]:
    normalized = _normalize_string_tuple("evidence_kinds", values)
    if not normalized:
        raise ValueError("evidence_kinds must not be empty")
    for value in normalized:
        _require_member("evidence_kinds", value, EVIDENCE_KINDS)
    if normalized != tuple(sorted(set(normalized))):
        raise ValueError("evidence_kinds must be sorted and unique")
    return normalized


def _normalize_string_tuple(field_name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        normalized = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    for value in normalized:
        _require_canonical_string(field_name, value)
    return normalized


def _normalize_optional_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain a canonical string")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return decimal_value.quantize(SCORE_QUANT)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(COUNT_QUANT)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_weights_total_one(config: ResearchResolutionAmbiguityConfig) -> None:
    total = (
        config.rule_ambiguity_weight
        + config.adjudication_dependency_weight
        + config.evidence_conflict_weight
        + config.near_resolution_weight
    ).quantize(SCORE_QUANT)
    if total != ONE:
        raise ValueError("rule_ambiguity_weight must be part of weights totaling 1.000000")


def _require_row_weights_total_one(row: ResearchResolutionAmbiguityRow) -> None:
    total = (
        row.rule_ambiguity_weight
        + row.adjudication_dependency_weight
        + row.evidence_conflict_weight
        + row.near_resolution_weight
    ).quantize(SCORE_QUANT)
    if total != ONE:
        raise ValueError("rule_ambiguity_weight must be part of weights totaling 1.000000")


__all__ = (
    "EVIDENCE_KINDS",
    "REASON_CODES",
    "REPORT_STATUSES",
    "ROW_STATUSES",
    "ResearchResolutionAmbiguityConfig",
    "ResearchResolutionAmbiguityEvidence",
    "ResearchResolutionAmbiguityReasonCodeCount",
    "ResearchResolutionAmbiguityReport",
    "ResearchResolutionAmbiguityRow",
    "build_research_resolution_ambiguity_report",
    "research_resolution_ambiguity_report_payload",
)
