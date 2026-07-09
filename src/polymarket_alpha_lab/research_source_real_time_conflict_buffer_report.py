"""Pure report-only buffer for sanitized real-time source conflicts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_REAL_TIME_CONFLICT_BUFFER_REPORT_CONFIG_VERSION = (
    "research-source-real-time-conflict-buffer-report-v0"
)

SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

AUTHORITY_TIERS = ("official", "primary", "independent", "unverified")
AUTHORITY_TIER_SCORES = {
    "official": Decimal("1.000000"),
    "primary": Decimal("0.800000"),
    "independent": Decimal("0.500000"),
    "unverified": Decimal("0.200000"),
}

NO_INPUTS_REASON = "real_time_conflict_buffer_no_inputs"
PASS_STATUS_REASON = "real_time_conflict_buffer_status_pass"
WATCH_STATUS_REASON = "real_time_conflict_buffer_status_watch"
BLOCKED_STATUS_REASON = "real_time_conflict_buffer_status_block"
STALE_REASON = "real_time_conflict_update_stale"
WEAK_AUTHORITY_REASON = "real_time_conflict_authority_weak"
LOW_CORROBORATION_REASON = "real_time_conflict_corroboration_low"
HIGH_PRESSURE_REASON = "real_time_conflict_pressure_high"
LOW_EXTRACTION_REASON = "real_time_conflict_extraction_low"

REASON_CODES = (
    NO_INPUTS_REASON,
    PASS_STATUS_REASON,
    WATCH_STATUS_REASON,
    BLOCKED_STATUS_REASON,
    STALE_REASON,
    WEAK_AUTHORITY_REASON,
    LOW_CORROBORATION_REASON,
    HIGH_PRESSURE_REASON,
    LOW_EXTRACTION_REASON,
)
BUFFER_REASON_SEQUENCE = REASON_CODES[4:]


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TERMS = (
    _join_parts("candi", "date"),
    _join_parts("ra", "w"),
    _join_parts("mar", "ket"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("u", "rl"),
    _join_parts("te", "xt"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("siz", "ing"),
    _join_parts("recommen", "dation"),
    _join_parts("ht", "tp"),
    _join_parts("htt", "ps"),
    _join_parts("au", "th"),
    _join_parts("li", "ve"),
    _join_parts("cl", "ob"),
    _join_parts("cond", "ition"),
    _join_parts("data", "base"),
)


__all__ = (
    "AUTHORITY_TIERS",
    "AUTHORITY_TIER_SCORES",
    "DEFAULT_RESEARCH_SOURCE_REAL_TIME_CONFLICT_BUFFER_REPORT_CONFIG_VERSION",
    "REASON_CODES",
    "STATUSES",
    "ResearchSourceRealTimeConflictBufferConfig",
    "ResearchSourceRealTimeConflictBufferInput",
    "ResearchSourceRealTimeConflictBufferReport",
    "ResearchSourceRealTimeConflictBufferRow",
    "build_research_source_real_time_conflict_buffer_report",
    "research_source_real_time_conflict_buffer_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceRealTimeConflictBufferConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_REAL_TIME_CONFLICT_BUFFER_REPORT_CONFIG_VERSION
    )
    fresh_update_age_seconds: Decimal = Decimal("300.000000")
    stale_update_age_seconds: Decimal = Decimal("3600.000000")
    min_corroborating_family_count: Decimal = Decimal("3.000000")
    weak_authority_score: Decimal = Decimal("0.500000")
    high_contradiction_pressure: Decimal = Decimal("0.700000")
    low_extraction_confidence: Decimal = Decimal("0.600000")
    watch_buffer_risk_score: Decimal = Decimal("0.350000")
    blocked_buffer_risk_score: Decimal = Decimal("0.700000")
    recency_weight: Decimal = Decimal("0.250000")
    authority_weight: Decimal = Decimal("0.200000")
    corroboration_weight: Decimal = Decimal("0.200000")
    contradiction_weight: Decimal = Decimal("0.250000")
    extraction_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRealTimeConflictBufferConfig:
            raise ValueError("config must be a ResearchSourceRealTimeConflictBufferConfig")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_REAL_TIME_CONFLICT_BUFFER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "fresh_update_age_seconds",
            "stale_update_age_seconds",
            "min_corroborating_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "weak_authority_score",
            "high_contradiction_pressure",
            "low_extraction_confidence",
            "watch_buffer_risk_score",
            "blocked_buffer_risk_score",
            "recency_weight",
            "authority_weight",
            "corroboration_weight",
            "contradiction_weight",
            "extraction_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.fresh_update_age_seconds >= self.stale_update_age_seconds:
            raise ValueError(
                "fresh_update_age_seconds must be below stale_update_age_seconds",
            )
        if self.watch_buffer_risk_score >= self.blocked_buffer_risk_score:
            raise ValueError(
                "watch_buffer_risk_score must be below blocked_buffer_risk_score",
            )
        weight_sum = _q(
            self.recency_weight
            + self.authority_weight
            + self.corroboration_weight
            + self.contradiction_weight
            + self.extraction_weight,
        )
        if weight_sum != ONE:
            raise ValueError("buffer risk score weights must sum to 1.000000")
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", asdict(self))


@dataclass(frozen=True)
class ResearchSourceRealTimeConflictBufferInput:
    conflict_key: str
    update_age_seconds: Decimal
    authority_tier: str
    corroborating_family_count: Decimal
    contradicting_family_count: Decimal
    contradiction_pressure: Decimal
    extraction_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRealTimeConflictBufferInput:
            raise ValueError("subject must be a ResearchSourceRealTimeConflictBufferInput")
        _require_public_identifier("conflict_key", self.conflict_key)
        object.__setattr__(
            self,
            "update_age_seconds",
            _normalize_nonnegative_decimal(
                "update_age_seconds",
                self.update_age_seconds,
            ),
        )
        _require_choice("authority_tier", self.authority_tier, AUTHORITY_TIERS)
        for field_name in (
            "corroborating_family_count",
            "contradicting_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_pressure",
            _normalize_probability(
                "contradiction_pressure",
                self.contradiction_pressure,
            ),
        )
        object.__setattr__(
            self,
            "extraction_confidence",
            _normalize_probability(
                "extraction_confidence",
                self.extraction_confidence,
            ),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("real time conflict buffer input", asdict(self))


@dataclass(frozen=True)
class ResearchSourceRealTimeConflictBufferRow:
    conflict_key: str
    priority_rank: Decimal
    update_age_seconds: Decimal
    recency_risk_score: Decimal
    authority_tier: str
    authority_score: Decimal
    authority_risk_score: Decimal
    corroborating_family_count: Decimal
    contradicting_family_count: Decimal
    corroboration_score: Decimal
    corroboration_gap_score: Decimal
    contradiction_pressure: Decimal
    extraction_confidence: Decimal
    extraction_gap_score: Decimal
    buffer_risk_score: Decimal
    buffer_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRealTimeConflictBufferRow:
            raise ValueError("row must be a ResearchSourceRealTimeConflictBufferRow")
        _require_public_identifier("conflict_key", self.conflict_key)
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_decimal("priority_rank", self.priority_rank),
        )
        object.__setattr__(
            self,
            "update_age_seconds",
            _normalize_nonnegative_decimal(
                "update_age_seconds",
                self.update_age_seconds,
            ),
        )
        for field_name in (
            "recency_risk_score",
            "authority_score",
            "authority_risk_score",
            "corroboration_score",
            "corroboration_gap_score",
            "contradiction_pressure",
            "extraction_confidence",
            "extraction_gap_score",
            "buffer_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_choice("authority_tier", self.authority_tier, AUTHORITY_TIERS)
        for field_name in (
            "corroborating_family_count",
            "contradicting_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_choice("buffer_status", self.buffer_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("real time conflict buffer row", asdict(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_derived_validation_digest(self.derived_validation_digest),
            )
        _validate_row(self)


@dataclass(frozen=True)
class ResearchSourceRealTimeConflictBufferReport:
    config_version: str
    report_status: str
    input_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_update_count: Decimal
    weak_authority_count: Decimal
    low_corroboration_count: Decimal
    high_contradiction_count: Decimal
    low_extraction_confidence_count: Decimal
    highest_buffer_risk_score: Decimal
    rows: tuple[ResearchSourceRealTimeConflictBufferRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRealTimeConflictBufferReport:
            raise ValueError("report must be a ResearchSourceRealTimeConflictBufferReport")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_REAL_TIME_CONFLICT_BUFFER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_choice("report_status", self.report_status, STATUSES)
        for field_name in (
            "input_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_update_count",
            "weak_authority_count",
            "low_corroboration_count",
            "high_contradiction_count",
            "low_extraction_confidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_buffer_risk_score",
            _normalize_probability(
                "highest_buffer_risk_score",
                self.highest_buffer_risk_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("real time conflict buffer report", asdict(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_derived_validation_digest(self.derived_validation_digest),
            )
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("real time conflict buffer payload", payload)
        if type(payload) is not dict:
            raise ValueError("real time conflict buffer payload must be an object")
        return payload


def build_research_source_real_time_conflict_buffer_report(
    rows: object,
    *,
    config: ResearchSourceRealTimeConflictBufferConfig | None = None,
) -> ResearchSourceRealTimeConflictBufferReport:
    if config is None:
        config = ResearchSourceRealTimeConflictBufferConfig()
    if type(config) is not ResearchSourceRealTimeConflictBufferConfig:
        raise ValueError("config must be a ResearchSourceRealTimeConflictBufferConfig")
    _require_hard_flags(config)
    input_rows = _normalize_input_rows(rows)
    ranked_rows = tuple(
        _ranked_row(row, rank=index + 1)
        for index, row in enumerate(
            sorted(
                (_unranked_row(item, config=config) for item in input_rows),
                key=_row_sort_key,
            ),
        )
    )
    report_status = _report_status(ranked_rows)
    return ResearchSourceRealTimeConflictBufferReport(
        config_version=config.config_version,
        report_status=report_status,
        input_count=_count(len(input_rows)),
        blocked_count=_status_count(ranked_rows, "block"),
        watch_count=_status_count(ranked_rows, "watch"),
        pass_count=_status_count(ranked_rows, "pass"),
        stale_update_count=_reason_count(ranked_rows, STALE_REASON),
        weak_authority_count=_reason_count(ranked_rows, WEAK_AUTHORITY_REASON),
        low_corroboration_count=_reason_count(ranked_rows, LOW_CORROBORATION_REASON),
        high_contradiction_count=_reason_count(ranked_rows, HIGH_PRESSURE_REASON),
        low_extraction_confidence_count=_reason_count(
            ranked_rows,
            LOW_EXTRACTION_REASON,
        ),
        highest_buffer_risk_score=_max_buffer_risk_score(ranked_rows),
        rows=ranked_rows,
        reason_codes=_report_reason_codes(ranked_rows),
    )


def research_source_real_time_conflict_buffer_report_payload(
    report: ResearchSourceRealTimeConflictBufferReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourceRealTimeConflictBufferReport:
        raise ValueError("report must be a ResearchSourceRealTimeConflictBufferReport")
    _require_hard_flags(report)
    _validate_report(report)
    return report.public_payload


def _unranked_row(
    subject: ResearchSourceRealTimeConflictBufferInput,
    *,
    config: ResearchSourceRealTimeConflictBufferConfig,
) -> ResearchSourceRealTimeConflictBufferRow:
    recency_risk_score = _recency_risk_score(subject.update_age_seconds, config)
    authority_score = AUTHORITY_TIER_SCORES[subject.authority_tier]
    authority_risk_score = _q(ONE - authority_score)
    corroboration_score = _clamp_probability(
        _safe_ratio(
            subject.corroborating_family_count,
            config.min_corroborating_family_count,
        ),
    )
    corroboration_gap_score = _q(ONE - corroboration_score)
    extraction_gap_score = _q(ONE - subject.extraction_confidence)
    buffer_risk_score = _buffer_risk_score(
        recency_risk_score=recency_risk_score,
        authority_risk_score=authority_risk_score,
        corroboration_gap_score=corroboration_gap_score,
        contradiction_pressure=subject.contradiction_pressure,
        extraction_gap_score=extraction_gap_score,
        config=config,
    )
    buffer_status = _buffer_status(buffer_risk_score, config=config)
    return ResearchSourceRealTimeConflictBufferRow(
        conflict_key=subject.conflict_key,
        priority_rank=ONE,
        update_age_seconds=subject.update_age_seconds,
        recency_risk_score=recency_risk_score,
        authority_tier=subject.authority_tier,
        authority_score=authority_score,
        authority_risk_score=authority_risk_score,
        corroborating_family_count=subject.corroborating_family_count,
        contradicting_family_count=subject.contradicting_family_count,
        corroboration_score=corroboration_score,
        corroboration_gap_score=corroboration_gap_score,
        contradiction_pressure=subject.contradiction_pressure,
        extraction_confidence=subject.extraction_confidence,
        extraction_gap_score=extraction_gap_score,
        buffer_risk_score=buffer_risk_score,
        buffer_status=buffer_status,
        reason_codes=_row_reason_codes(
            buffer_status=buffer_status,
            recency_risk_score=recency_risk_score,
            authority_score=authority_score,
            corroboration_gap_score=corroboration_gap_score,
            contradiction_pressure=subject.contradiction_pressure,
            extraction_confidence=subject.extraction_confidence,
            config=config,
        ),
    )


def _ranked_row(
    row: ResearchSourceRealTimeConflictBufferRow,
    *,
    rank: int,
) -> ResearchSourceRealTimeConflictBufferRow:
    return replace(row, priority_rank=_count(rank), derived_validation_digest="")


def _row_sort_key(
    row: ResearchSourceRealTimeConflictBufferRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.buffer_status], -row.buffer_risk_score, row.conflict_key)


def _recency_risk_score(
    age_seconds: Decimal,
    config: ResearchSourceRealTimeConflictBufferConfig,
) -> Decimal:
    if age_seconds <= config.fresh_update_age_seconds:
        return ZERO
    if age_seconds >= config.stale_update_age_seconds:
        return ONE
    elapsed = age_seconds - config.fresh_update_age_seconds
    span = config.stale_update_age_seconds - config.fresh_update_age_seconds
    return _clamp_probability(_safe_ratio(elapsed, span))


def _buffer_risk_score(
    *,
    recency_risk_score: Decimal,
    authority_risk_score: Decimal,
    corroboration_gap_score: Decimal,
    contradiction_pressure: Decimal,
    extraction_gap_score: Decimal,
    config: ResearchSourceRealTimeConflictBufferConfig,
) -> Decimal:
    return _clamp_probability(
        (recency_risk_score * config.recency_weight)
        + (authority_risk_score * config.authority_weight)
        + (corroboration_gap_score * config.corroboration_weight)
        + (contradiction_pressure * config.contradiction_weight)
        + (extraction_gap_score * config.extraction_weight),
    )


def _buffer_status(
    buffer_risk_score: Decimal,
    *,
    config: ResearchSourceRealTimeConflictBufferConfig,
) -> str:
    if buffer_risk_score >= config.blocked_buffer_risk_score:
        return "block"
    if buffer_risk_score >= config.watch_buffer_risk_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    buffer_status: str,
    recency_risk_score: Decimal,
    authority_score: Decimal,
    corroboration_gap_score: Decimal,
    contradiction_pressure: Decimal,
    extraction_confidence: Decimal,
    config: ResearchSourceRealTimeConflictBufferConfig,
) -> tuple[str, ...]:
    codes = [f"real_time_conflict_buffer_status_{buffer_status}"]
    if recency_risk_score == ONE:
        codes.append(STALE_REASON)
    if authority_score <= config.weak_authority_score:
        codes.append(WEAK_AUTHORITY_REASON)
    if corroboration_gap_score > ZERO:
        codes.append(LOW_CORROBORATION_REASON)
    if contradiction_pressure >= config.high_contradiction_pressure:
        codes.append(HIGH_PRESSURE_REASON)
    if extraction_confidence < config.low_extraction_confidence:
        codes.append(LOW_EXTRACTION_REASON)
    return tuple(codes)


def _report_reason_codes(
    rows: tuple[ResearchSourceRealTimeConflictBufferRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _report_status(rows)
    codes = [f"real_time_conflict_buffer_status_{status}"]
    present = {code for row in rows for code in row.reason_codes}
    for code in BUFFER_REASON_SEQUENCE:
        if code in present:
            codes.append(code)
    return tuple(codes)


def _report_status(rows: tuple[ResearchSourceRealTimeConflictBufferRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.buffer_status == "block" for row in rows):
        return "block"
    if any(row.buffer_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchSourceRealTimeConflictBufferRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.buffer_status == status))


def _reason_count(
    rows: tuple[ResearchSourceRealTimeConflictBufferRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_buffer_risk_score(
    rows: tuple[ResearchSourceRealTimeConflictBufferRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.buffer_risk_score for row in rows)


def _validate_row(row: ResearchSourceRealTimeConflictBufferRow) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")
    if row.authority_score != AUTHORITY_TIER_SCORES[row.authority_tier]:
        raise ValueError("authority_score must match authority_tier")
    if row.authority_risk_score != _q(ONE - row.authority_score):
        raise ValueError("authority_risk_score must match authority_score")
    if row.corroboration_gap_score != _q(ONE - row.corroboration_score):
        raise ValueError("corroboration_gap_score must match corroboration_score")
    if row.extraction_gap_score != _q(ONE - row.extraction_confidence):
        raise ValueError("extraction_gap_score must match extraction_confidence")
    status_reason = f"real_time_conflict_buffer_status_{row.buffer_status}"
    if not row.reason_codes or row.reason_codes[0] != status_reason:
        raise ValueError("reason_codes must start with buffer_status")


def _validate_report(report: ResearchSourceRealTimeConflictBufferReport) -> None:
    for row in report.rows:
        _validate_row(row)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "block"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.stale_update_count != _reason_count(report.rows, STALE_REASON):
        raise ValueError("stale_update_count must match rows")
    if report.weak_authority_count != _reason_count(report.rows, WEAK_AUTHORITY_REASON):
        raise ValueError("weak_authority_count must match rows")
    if report.low_corroboration_count != _reason_count(
        report.rows,
        LOW_CORROBORATION_REASON,
    ):
        raise ValueError("low_corroboration_count must match rows")
    if report.high_contradiction_count != _reason_count(
        report.rows,
        HIGH_PRESSURE_REASON,
    ):
        raise ValueError("high_contradiction_count must match rows")
    if report.low_extraction_confidence_count != _reason_count(
        report.rows,
        LOW_EXTRACTION_REASON,
    ):
        raise ValueError("low_extraction_confidence_count must match rows")
    if report.highest_buffer_risk_score != _max_buffer_risk_score(report.rows):
        raise ValueError("highest_buffer_risk_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_input_rows(
    rows: object,
) -> tuple[ResearchSourceRealTimeConflictBufferInput, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError(
            "rows must be an iterable of ResearchSourceRealTimeConflictBufferInput",
        )
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchSourceRealTimeConflictBufferInput:
            raise ValueError(
                "rows must be ResearchSourceRealTimeConflictBufferInput values",
            )
        _require_hard_flags(row)
        if row.conflict_key in seen:
            raise ValueError("rows must be unique by conflict_key")
        seen.add(row.conflict_key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceRealTimeConflictBufferRow, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError("rows must be an iterable of ResearchSourceRealTimeConflictBufferRow")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchSourceRealTimeConflictBufferRow:
            raise ValueError("rows must be ResearchSourceRealTimeConflictBufferRow values")
        _require_hard_flags(row)
        if row.conflict_key in seen:
            raise ValueError("rows must be unique by conflict_key")
        seen.add(row.conflict_key)
    expected_ranks = tuple(_count(index + 1) for index in range(len(normalized)))
    actual_ranks = tuple(row.priority_rank for row in normalized)
    if actual_ranks != expected_ranks:
        raise ValueError("priority_rank must match row sequence")
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < SCORE_QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return _q(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_derived_validation_digest(value: object) -> str:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest") from exc
    return value


def _normalize_reason_codes(values: object, *, allow_empty: bool) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not hasattr(values, "__iter__"):
        raise ValueError("reason_codes must contain supported reason codes")
    reason_codes = tuple(values)
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for code in reason_codes:
        _require_choice("reason_codes", code, REASON_CODES)
    expected = tuple(code for code in REASON_CODES if code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    return reason_codes


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _q(Decimal(value))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _q(numerator / denominator)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _clamp_probability(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return _q(value)


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_public_identifier(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if value.lower().startswith("0x"):
        raise ValueError(f"{field_name} must not be a low-level identifier")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if _mentions_unsafe_public_term(value):
        raise ValueError(f"unsafe public payload value in {field_name}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if hasattr(payload, "__dataclass_fields__") and not isinstance(payload, type):
        _reject_unsafe_public_payload(label, asdict(payload))
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _mentions_unsafe_public_term(key):
                raise ValueError(f"unsafe public payload key in {label}")
            _reject_unsafe_public_payload(label, value)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if type(payload) is str and _mentions_unsafe_public_term(payload):
        raise ValueError(f"unsafe public payload value in {label}")
    if type(payload) in (int, float):
        raise ValueError("public payload numeric values must be Decimal strings")


def _mentions_unsafe_public_term(value: str) -> bool:
    words = _public_words(value.lower())
    if "://" in value:
        return True
    return any(term in words for term in UNSAFE_PUBLIC_TERMS)


def _public_words(value: str) -> tuple[str, ...]:
    words: list[str] = []
    current: list[str] = []
    for character in value:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            words.append("".join(current))
            current = []
    if current:
        words.append("".join(current))
    return tuple(words)


def _payload_value(value: Any) -> Any:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal strings")
    if type(value) is Decimal:
        return str(_q(value))
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        _reject_unsafe_public_payload("real time conflict buffer payload", value)
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _row_derived_validation_digest(
    row: ResearchSourceRealTimeConflictBufferRow,
) -> str:
    values = asdict(row)
    values.pop("derived_validation_digest", None)
    return _json_sha256(_payload_value(values))


def _report_derived_validation_digest(
    report: ResearchSourceRealTimeConflictBufferReport,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _json_sha256(_payload_value(values))


def _json_sha256(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
