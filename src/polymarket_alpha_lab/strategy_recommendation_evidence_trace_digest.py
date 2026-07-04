"""Phase 1 evidence trace digest for strategy candidates."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_EVIDENCE_TRACE_DIGEST_CONFIG_VERSION",
    "StrategyRecommendationEvidenceTraceDigestConfig",
    "StrategyRecommendationEvidenceTraceDigestInput",
    "StrategyRecommendationEvidenceTraceDigestReasonCodeCount",
    "StrategyRecommendationEvidenceTraceDigestReport",
    "StrategyRecommendationEvidenceTraceDigestRow",
    "build_strategy_recommendation_evidence_trace_digest_report",
    "strategy_recommendation_evidence_trace_digest_payload",
)


DEFAULT_STRATEGY_RECOMMENDATION_EVIDENCE_TRACE_DIGEST_CONFIG_VERSION = (
    "strategy-recommendation-evidence-trace-digest-v0"
)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

INPUT_REASON_CODES = ("evidence_trace_input",)
ROW_REASON_CODES = (
    "evidence_trace_source_trace_missing",
    "evidence_trace_traceable_sources_below_minimum",
    "evidence_trace_source_family_diversity_below_minimum",
    "evidence_trace_stale_evidence",
    "evidence_trace_conflict_notes_missing",
    "evidence_trace_ready",
)
REPORT_REASON_CODES = (
    "evidence_trace_digest_empty",
    "evidence_trace_digest_ready",
    "evidence_trace_digest_watch",
    "evidence_trace_digest_blocked",
    "evidence_trace_traceability_gaps_present",
    "evidence_trace_freshness_gaps_present",
    "evidence_trace_conflict_note_gaps_present",
)
READINESS_STATUSES = ("research_ready", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")
STATUS_WEIGHT = {
    "blocked": Decimal("2"),
    "watch": Decimal("1"),
    "research_ready": Decimal("0"),
}
SENSITIVE_TEXT_MARKERS = (
    "://",
    "secret",
    "token",
    "credential",
)
FLAG_NAMES = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class StrategyRecommendationEvidenceTraceDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_EVIDENCE_TRACE_DIGEST_CONFIG_VERSION
    )
    min_traceable_source_count: Decimal = Decimal("2")
    min_source_family_count: Decimal = Decimal("2")
    max_evidence_age_hours: Decimal = Decimal("24")
    require_conflict_notes: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_traceable_source_count",
            "min_source_family_count",
            "max_evidence_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        _require_bool("require_conflict_notes", self.require_conflict_notes)
        require_paper_only_flags(
            "StrategyRecommendationEvidenceTraceDigestConfig",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationEvidenceTraceDigestInput:
    candidate_reference: str
    evidence_reference: str
    source_family: str
    observed_at: datetime
    source_trace_present: bool
    conflict_flagged: bool
    conflict_note_present: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "candidate_reference",
            _redact_reference(
                "candidate_reference",
                self.candidate_reference,
                "candidate_ref",
            ),
        )
        object.__setattr__(
            self,
            "evidence_reference",
            _redact_reference(
                "evidence_reference",
                self.evidence_reference,
                "evidence_ref",
            ),
        )
        _require_canonical_string("source_family", self.source_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_bool("source_trace_present", self.source_trace_present)
        _require_bool("conflict_flagged", self.conflict_flagged)
        _require_bool("conflict_note_present", self.conflict_note_present)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        require_paper_only_flags(
            "StrategyRecommendationEvidenceTraceDigestInput",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationEvidenceTraceDigestRow:
    redacted_candidate_reference: str
    evidence_count: Decimal
    traceable_source_count: Decimal
    fresh_traceable_source_count: Decimal
    stale_source_count: Decimal
    source_family_count: Decimal
    conflict_flagged_evidence_count: Decimal
    conflict_note_count: Decimal
    traceability_ratio: Decimal
    source_family_ratio: Decimal
    freshness_ratio: Decimal
    latest_observed_at: datetime
    oldest_observed_at: datetime
    source_families: tuple[str, ...]
    redacted_evidence_references: tuple[str, ...]
    readiness_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_reference(
            "redacted_candidate_reference",
            self.redacted_candidate_reference,
            "candidate_ref",
        )
        for field_name in (
            "evidence_count",
            "traceable_source_count",
            "fresh_traceable_source_count",
            "stale_source_count",
            "source_family_count",
            "conflict_flagged_evidence_count",
            "conflict_note_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "traceability_ratio",
            "source_family_ratio",
            "freshness_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "oldest_observed_at",
            _as_utc("oldest_observed_at", self.oldest_observed_at),
        )
        object.__setattr__(
            self,
            "source_families",
            _normalize_string_tuple("source_families", self.source_families),
        )
        object.__setattr__(
            self,
            "redacted_evidence_references",
            _normalize_redacted_reference_tuple(
                "redacted_evidence_references",
                self.redacted_evidence_references,
                "evidence_ref",
            ),
        )
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("evidence trace digest row", self)
        require_paper_only_flags(
            "StrategyRecommendationEvidenceTraceDigestRow",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationEvidenceTraceDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        require_paper_only_flags(
            "StrategyRecommendationEvidenceTraceDigestReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationEvidenceTraceDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    candidate_count: Decimal
    research_ready_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    traceability_gap_candidate_count: Decimal
    stale_candidate_count: Decimal
    missing_conflict_note_candidate_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyRecommendationEvidenceTraceDigestReasonCodeCount, ...]
    rows: tuple[StrategyRecommendationEvidenceTraceDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "candidate_count",
            "research_ready_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
            "traceability_gap_candidate_count",
            "stale_candidate_count",
            "missing_conflict_note_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("evidence trace digest report", self)
        require_paper_only_flags(
            "StrategyRecommendationEvidenceTraceDigestReport",
            self,
        )


def build_strategy_recommendation_evidence_trace_digest_report(
    records: Iterable[StrategyRecommendationEvidenceTraceDigestInput],
    *,
    config: StrategyRecommendationEvidenceTraceDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationEvidenceTraceDigestReport:
    if type(config) is not StrategyRecommendationEvidenceTraceDigestConfig:
        raise ValueError(
            "config must be a StrategyRecommendationEvidenceTraceDigestConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(records, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _candidate_row(candidate_reference, candidate_rows, config, generated_at_utc)
                for candidate_reference, candidate_rows in _candidate_groups(input_rows)
            ),
            key=_row_sort_key,
        ),
    )
    return StrategyRecommendationEvidenceTraceDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(input_rows)),
        candidate_count=_count(len(rows)),
        research_ready_candidate_count=_status_count(rows, "research_ready"),
        watch_candidate_count=_status_count(rows, "watch"),
        blocked_candidate_count=_status_count(rows, "blocked"),
        traceability_gap_candidate_count=_traceability_gap_count(rows),
        stale_candidate_count=_reason_count(rows, "evidence_trace_stale_evidence"),
        missing_conflict_note_candidate_count=_reason_count(
            rows,
            "evidence_trace_conflict_notes_missing",
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_recommendation_evidence_trace_digest_payload(
    report: StrategyRecommendationEvidenceTraceDigestReport | dict[str, Any],
) -> dict[str, Any]:
    reject_unsafe_surface_fields("evidence trace digest payload", report)
    _reject_payload_public_values("evidence trace digest payload", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    reject_unsafe_surface_fields("evidence trace digest payload", payload)
    _reject_payload_public_values("evidence trace digest payload", payload)
    return payload


def _candidate_row(
    candidate_reference: str,
    rows: tuple[StrategyRecommendationEvidenceTraceDigestInput, ...],
    config: StrategyRecommendationEvidenceTraceDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationEvidenceTraceDigestRow:
    fresh_traceable_rows = tuple(
        row
        for row in rows
        if row.source_trace_present
        and _age_hours(generated_at, row.observed_at) <= config.max_evidence_age_hours
    )
    traceable_rows = tuple(row for row in rows if row.source_trace_present)
    stale_count = _count(
        sum(
            1
            for row in rows
            if _age_hours(generated_at, row.observed_at) > config.max_evidence_age_hours
        ),
    )
    fresh_families = tuple(sorted({row.source_family for row in fresh_traceable_rows}))
    conflict_flagged_count = _count(sum(1 for row in rows if row.conflict_flagged))
    conflict_note_count = _count(
        sum(1 for row in rows if row.conflict_flagged and row.conflict_note_present),
    )
    reason_codes = _row_reason_codes(
        rows=rows,
        fresh_traceable_source_count=_count(len(fresh_traceable_rows)),
        source_family_count=_count(len(fresh_families)),
        stale_source_count=stale_count,
        conflict_flagged_evidence_count=conflict_flagged_count,
        conflict_note_count=conflict_note_count,
        config=config,
    )
    return StrategyRecommendationEvidenceTraceDigestRow(
        redacted_candidate_reference=candidate_reference,
        evidence_count=_count(len(rows)),
        traceable_source_count=_count(len(traceable_rows)),
        fresh_traceable_source_count=_count(len(fresh_traceable_rows)),
        stale_source_count=stale_count,
        source_family_count=_count(len(fresh_families)),
        conflict_flagged_evidence_count=conflict_flagged_count,
        conflict_note_count=conflict_note_count,
        traceability_ratio=_capped_ratio(
            _count(len(fresh_traceable_rows)),
            config.min_traceable_source_count,
        ),
        source_family_ratio=_capped_ratio(
            _count(len(fresh_families)),
            config.min_source_family_count,
        ),
        freshness_ratio=_capped_ratio(_count(len(fresh_traceable_rows)), _count(len(traceable_rows))),
        latest_observed_at=max(row.observed_at for row in rows),
        oldest_observed_at=min(row.observed_at for row in rows),
        source_families=fresh_families,
        redacted_evidence_references=tuple(sorted(row.evidence_reference for row in rows)),
        readiness_status=_readiness_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    rows: tuple[StrategyRecommendationEvidenceTraceDigestInput, ...],
    fresh_traceable_source_count: Decimal,
    source_family_count: Decimal,
    stale_source_count: Decimal,
    conflict_flagged_evidence_count: Decimal,
    conflict_note_count: Decimal,
    config: StrategyRecommendationEvidenceTraceDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if any(not row.source_trace_present for row in rows):
        codes.append("evidence_trace_source_trace_missing")
    if fresh_traceable_source_count < config.min_traceable_source_count:
        codes.append("evidence_trace_traceable_sources_below_minimum")
    if source_family_count < config.min_source_family_count:
        codes.append("evidence_trace_source_family_diversity_below_minimum")
    if stale_source_count > ZERO_COUNT:
        codes.append("evidence_trace_stale_evidence")
    if (
        config.require_conflict_notes
        and conflict_flagged_evidence_count > conflict_note_count
    ):
        codes.append("evidence_trace_conflict_notes_missing")
    if not codes:
        codes.append("evidence_trace_ready")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _readiness_status(reason_codes: tuple[str, ...]) -> str:
    blocked_codes = {
        "evidence_trace_traceable_sources_below_minimum",
        "evidence_trace_source_family_diversity_below_minimum",
        "evidence_trace_conflict_notes_missing",
    }
    if any(reason_code in blocked_codes for reason_code in reason_codes):
        return "blocked"
    if reason_codes != ("evidence_trace_ready",):
        return "watch"
    return "research_ready"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationEvidenceTraceDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("evidence_trace_digest_empty",)
    codes: list[str] = [f"evidence_trace_digest_{_report_status(rows)}"]
    if any(_has_traceability_gap(row) for row in rows):
        codes.append("evidence_trace_traceability_gaps_present")
    if any("evidence_trace_stale_evidence" in row.reason_codes for row in rows):
        codes.append("evidence_trace_freshness_gaps_present")
    if any("evidence_trace_conflict_notes_missing" in row.reason_codes for row in rows):
        codes.append("evidence_trace_conflict_note_gaps_present")
    if codes == ["evidence_trace_digest_pass"]:
        return ("evidence_trace_digest_ready",)
    if codes[0] == "evidence_trace_digest_pass":
        codes[0] = "evidence_trace_digest_ready"
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _report_status(rows: tuple[StrategyRecommendationEvidenceTraceDigestRow, ...]) -> str:
    if any(row.readiness_status == "blocked" for row in rows):
        return "blocked"
    if any(row.readiness_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _candidate_groups(
    rows: tuple[StrategyRecommendationEvidenceTraceDigestInput, ...],
) -> tuple[tuple[str, tuple[StrategyRecommendationEvidenceTraceDigestInput, ...]], ...]:
    candidate_references = tuple(dict.fromkeys(row.candidate_reference for row in rows))
    return tuple(
        (
            candidate_reference,
            tuple(row for row in rows if row.candidate_reference == candidate_reference),
        )
        for candidate_reference in candidate_references
    )


def _normalize_inputs(
    records: Iterable[StrategyRecommendationEvidenceTraceDigestInput],
    generated_at: datetime,
) -> tuple[StrategyRecommendationEvidenceTraceDigestInput, ...]:
    if isinstance(records, (str, bytes)):
        raise ValueError("records must be an iterable")
    try:
        rows = tuple(records)
    except TypeError as exc:
        raise ValueError("records must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationEvidenceTraceDigestInput:
            raise ValueError(
                "records must contain StrategyRecommendationEvidenceTraceDigestInput values",
            )
        require_paper_only_flags("record", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (row.candidate_reference, row.evidence_reference)
        if key in seen:
            raise ValueError("records must not contain duplicate evidence values")
        seen.add(key)
    return rows


def _normalize_rows(
    value: Iterable[StrategyRecommendationEvidenceTraceDigestRow],
) -> tuple[StrategyRecommendationEvidenceTraceDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not StrategyRecommendationEvidenceTraceDigestRow:
            raise ValueError("rows must contain StrategyRecommendationEvidenceTraceDigestRow values")
        require_paper_only_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    value: Iterable[StrategyRecommendationEvidenceTraceDigestReasonCodeCount],
) -> tuple[StrategyRecommendationEvidenceTraceDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in counts:
        if type(count) is not StrategyRecommendationEvidenceTraceDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "StrategyRecommendationEvidenceTraceDigestReasonCodeCount values",
            )
        require_paper_only_flags("reason code count", count)
    return tuple(sorted(counts, key=_reason_code_count_sort_key))


def _validate_row(row: StrategyRecommendationEvidenceTraceDigestRow) -> None:
    if row.traceable_source_count > row.evidence_count:
        raise ValueError("traceable_source_count must not exceed evidence_count")
    if row.fresh_traceable_source_count > row.traceable_source_count:
        raise ValueError(
            "fresh_traceable_source_count must not exceed traceable_source_count",
        )
    if row.stale_source_count > row.evidence_count:
        raise ValueError("stale_source_count must not exceed evidence_count")
    if row.source_family_count > row.fresh_traceable_source_count:
        raise ValueError(
            "source_family_count must not exceed fresh_traceable_source_count",
        )
    if row.conflict_note_count > row.conflict_flagged_evidence_count:
        raise ValueError(
            "conflict_note_count must not exceed conflict_flagged_evidence_count",
        )
    if row.evidence_count != _count(len(row.redacted_evidence_references)):
        raise ValueError("evidence_count must match redacted_evidence_references")
    if row.source_family_count != _count(len(row.source_families)):
        raise ValueError("source_family_count must match source_families")
    if row.latest_observed_at < row.oldest_observed_at:
        raise ValueError("latest_observed_at must not be before oldest_observed_at")
    if row.readiness_status != _readiness_status(row.reason_codes):
        raise ValueError("readiness_status must match reason_codes")


def _validate_report(report: StrategyRecommendationEvidenceTraceDigestReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.research_ready_candidate_count != _status_count(rows, "research_ready"):
        raise ValueError("research_ready_candidate_count must match rows")
    if report.watch_candidate_count != _status_count(rows, "watch"):
        raise ValueError("watch_candidate_count must match rows")
    if report.blocked_candidate_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_candidate_count must match rows")
    if report.traceability_gap_candidate_count != _traceability_gap_count(rows):
        raise ValueError("traceability_gap_candidate_count must match rows")
    if report.stale_candidate_count != _reason_count(rows, "evidence_trace_stale_evidence"):
        raise ValueError("stale_candidate_count must match rows")
    if report.missing_conflict_note_candidate_count != _reason_count(
        rows,
        "evidence_trace_conflict_notes_missing",
    ):
        raise ValueError("missing_conflict_note_candidate_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")


def _status_count(
    rows: tuple[StrategyRecommendationEvidenceTraceDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.readiness_status == status))


def _traceability_gap_count(
    rows: tuple[StrategyRecommendationEvidenceTraceDigestRow, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if _has_traceability_gap(row)))


def _reason_count(
    rows: tuple[StrategyRecommendationEvidenceTraceDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[StrategyRecommendationEvidenceTraceDigestRow, ...],
) -> tuple[StrategyRecommendationEvidenceTraceDigestReasonCodeCount, ...]:
    if not rows:
        return ()
    counter = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    counts = tuple(
        StrategyRecommendationEvidenceTraceDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in counter.items()
    )
    return tuple(sorted(counts, key=_reason_code_count_sort_key))


def _has_traceability_gap(row: StrategyRecommendationEvidenceTraceDigestRow) -> bool:
    traceability_reasons = {
        "evidence_trace_source_trace_missing",
        "evidence_trace_traceable_sources_below_minimum",
        "evidence_trace_source_family_diversity_below_minimum",
    }
    return any(reason_code in traceability_reasons for reason_code in row.reason_codes)


def _row_sort_key(row: StrategyRecommendationEvidenceTraceDigestRow) -> tuple[Any, ...]:
    return (
        -STATUS_WEIGHT[row.readiness_status],
        row.traceability_ratio,
        row.source_family_ratio,
        -row.stale_source_count,
        row.redacted_candidate_reference,
        row.latest_observed_at,
        row.redacted_evidence_references,
        row.reason_codes,
    )


def _reason_code_count_sort_key(
    count: StrategyRecommendationEvidenceTraceDigestReasonCodeCount,
) -> tuple[Decimal, str]:
    return (-count.count, count.reason_code)


def _age_hours(generated_at: datetime, observed_at: datetime) -> Decimal:
    age_seconds = Decimal(str((generated_at - observed_at).total_seconds()))
    with localcontext(DECIMAL_CONTEXT):
        return (age_seconds / Decimal("3600")).quantize(RATIO_QUANTUM)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ONE_RATIO
    if numerator >= denominator:
        return ONE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("ratio", numerator / denominator)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason_code for reason_code in allowed if reason_code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    items = tuple(value)
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must be unique")
    if tuple(sorted(items)) != items:
        raise ValueError(f"{field_name} must be sorted")
    return items


def _normalize_redacted_reference_tuple(
    field_name: str,
    value: object,
    prefix: str,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    items = tuple(value)
    for item in items:
        _require_redacted_reference(field_name, item, prefix)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must be unique")
    if tuple(sorted(items)) != items:
        raise ValueError(f"{field_name} must be sorted")
    return items


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _redact_reference(field_name: str, value: object, prefix: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    digest = sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _require_redacted_reference(field_name: str, value: object, prefix: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if not value.startswith(f"{prefix}_"):
        raise ValueError(f"{field_name} must be redacted")
    _reject_unsafe_text(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(field_name, value)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _reject_payload_public_values(label: str, value: object, pointer: str = "") -> None:
    if type(value) in (int, float):
        raise ValueError(f"{pointer or label} must use Decimal string values")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{pointer or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{pointer or label} must be UTC-aware")
    if isinstance(value, str):
        _reject_payload_text(pointer or label, value)
    if isinstance(value, dict):
        _require_payload_flags(value)
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_pointer = key if not pointer else f"{pointer}.{key}"
            _reject_payload_public_values(label, item, item_pointer)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_pointer = f"{pointer}[{index}]" if pointer else f"{label}[{index}]"
            _reject_payload_public_values(label, item, item_pointer)


def _require_payload_flags(value: dict[Any, Any]) -> None:
    for flag_name in FLAG_NAMES:
        if value.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _reject_payload_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(marker in normalized for marker in SENSITIVE_TEXT_MARKERS):
        raise ValueError(f"{field_name} contains unsafe text")
    _reject_unsafe_text(field_name, value)
