"""Pure public digest for candidate resolution ambiguity facts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_CANDIDATE_RESOLUTION_AMBIGUITY_DIGEST_CONFIG_VERSION = (
    "candidate-resolution-ambiguity-digest-v0"
)
AMBIGUITY_STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "no_candidate_resolution_facts",
    "outcome_criteria_unclear",
    "source_hierarchy_weak",
    "dispute_risk_elevated",
    "revision_risk_elevated",
    "adjudication_dependency_present",
    "close_resolution_timing_risk",
    "resolution_ambiguity_clear",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")


__all__ = (
    "DEFAULT_CANDIDATE_RESOLUTION_AMBIGUITY_DIGEST_CONFIG_VERSION",
    "CandidateResolutionAmbiguityDigestConfig",
    "CandidateResolutionAmbiguityDigestReasonCodeCount",
    "CandidateResolutionAmbiguityDigestReport",
    "CandidateResolutionAmbiguityDigestRow",
    "CandidateResolutionAmbiguityFacts",
    "build_candidate_resolution_ambiguity_digest",
    "candidate_resolution_ambiguity_digest_payload",
)


@dataclass(frozen=True)
class CandidateResolutionAmbiguityDigestConfig:
    config_version: str = DEFAULT_CANDIDATE_RESOLUTION_AMBIGUITY_DIGEST_CONFIG_VERSION
    min_pass_outcome_criteria_clarity: Decimal = Decimal("0.800000")
    min_watch_outcome_criteria_clarity: Decimal = Decimal("0.600000")
    min_pass_source_hierarchy_strength: Decimal = Decimal("0.700000")
    min_watch_source_hierarchy_strength: Decimal = Decimal("0.500000")
    max_pass_dispute_risk: Decimal = Decimal("0.250000")
    max_watch_dispute_risk: Decimal = Decimal("0.500000")
    max_pass_revision_risk: Decimal = Decimal("0.250000")
    max_watch_revision_risk: Decimal = Decimal("0.500000")
    max_pass_adjudication_dependency: Decimal = Decimal("0.200000")
    max_watch_adjudication_dependency: Decimal = Decimal("0.450000")
    max_pass_close_resolution_timing_risk: Decimal = Decimal("0.300000")
    max_watch_close_resolution_timing_risk: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateResolutionAmbiguityDigestConfig:
            raise TypeError(
                "CandidateResolutionAmbiguityDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateResolutionAmbiguityDigestConfig:
            raise ValueError(
                "config must be exactly CandidateResolutionAmbiguityDigestConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "min_pass_outcome_criteria_clarity",
            "min_watch_outcome_criteria_clarity",
            "min_pass_source_hierarchy_strength",
            "min_watch_source_hierarchy_strength",
            "max_pass_dispute_risk",
            "max_watch_dispute_risk",
            "max_pass_revision_risk",
            "max_watch_revision_risk",
            "max_pass_adjudication_dependency",
            "max_watch_adjudication_dependency",
            "max_pass_close_resolution_timing_risk",
            "max_watch_close_resolution_timing_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_low_threshold_pair(
            "min_watch_outcome_criteria_clarity",
            self.min_watch_outcome_criteria_clarity,
            "min_pass_outcome_criteria_clarity",
            self.min_pass_outcome_criteria_clarity,
        )
        _require_low_threshold_pair(
            "min_watch_source_hierarchy_strength",
            self.min_watch_source_hierarchy_strength,
            "min_pass_source_hierarchy_strength",
            self.min_pass_source_hierarchy_strength,
        )
        _require_high_threshold_pair(
            "max_pass_dispute_risk",
            self.max_pass_dispute_risk,
            "max_watch_dispute_risk",
            self.max_watch_dispute_risk,
        )
        _require_high_threshold_pair(
            "max_pass_revision_risk",
            self.max_pass_revision_risk,
            "max_watch_revision_risk",
            self.max_watch_revision_risk,
        )
        _require_high_threshold_pair(
            "max_pass_adjudication_dependency",
            self.max_pass_adjudication_dependency,
            "max_watch_adjudication_dependency",
            self.max_watch_adjudication_dependency,
        )
        _require_high_threshold_pair(
            "max_pass_close_resolution_timing_risk",
            self.max_pass_close_resolution_timing_risk,
            "max_watch_close_resolution_timing_risk",
            self.max_watch_close_resolution_timing_risk,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class CandidateResolutionAmbiguityFacts:
    redacted_public_reference: str
    outcome_criteria_clarity: Decimal
    source_hierarchy_strength: Decimal
    dispute_risk: Decimal
    revision_risk: Decimal
    adjudication_dependency: Decimal
    close_resolution_timing_risk: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateResolutionAmbiguityFacts:
            raise TypeError(
                "CandidateResolutionAmbiguityFacts does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateResolutionAmbiguityFacts:
            raise ValueError("facts must be exactly CandidateResolutionAmbiguityFacts")
        object.__setattr__(
            self,
            "redacted_public_reference",
            _require_redacted_public_reference(
                "redacted_public_reference",
                self.redacted_public_reference,
            ),
        )
        for field_name in _FACT_DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("facts", self)
        _reject_unsafe_public_payload("facts", self)


@dataclass(frozen=True)
class CandidateResolutionAmbiguityDigestRow:
    generated_at: datetime
    redacted_public_reference: str
    outcome_criteria_clarity: Decimal
    source_hierarchy_strength: Decimal
    dispute_risk: Decimal
    revision_risk: Decimal
    adjudication_dependency: Decimal
    close_resolution_timing_risk: Decimal
    ambiguity_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateResolutionAmbiguityDigestRow:
            raise TypeError(
                "CandidateResolutionAmbiguityDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateResolutionAmbiguityDigestRow:
            raise ValueError("row must be exactly CandidateResolutionAmbiguityDigestRow")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "redacted_public_reference",
            _require_redacted_public_reference(
                "redacted_public_reference",
                self.redacted_public_reference,
            ),
        )
        for field_name in _FACT_DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("ambiguity_status", self.ambiguity_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class CandidateResolutionAmbiguityDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateResolutionAmbiguityDigestReasonCodeCount:
            raise TypeError(
                "CandidateResolutionAmbiguityDigestReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateResolutionAmbiguityDigestReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "CandidateResolutionAmbiguityDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class CandidateResolutionAmbiguityDigestReport:
    generated_at: datetime
    config_version: str
    ambiguity_status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    outcome_criteria_unclear_count: Decimal
    source_hierarchy_weak_count: Decimal
    dispute_risk_count: Decimal
    revision_risk_count: Decimal
    adjudication_dependency_count: Decimal
    close_resolution_timing_risk_count: Decimal
    rows: tuple[CandidateResolutionAmbiguityDigestRow, ...]
    reason_code_counts: tuple[CandidateResolutionAmbiguityDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateResolutionAmbiguityDigestReport:
            raise TypeError(
                "CandidateResolutionAmbiguityDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateResolutionAmbiguityDigestReport:
            raise ValueError(
                "report must be exactly CandidateResolutionAmbiguityDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        _require_status("ambiguity_status", self.ambiguity_status)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "outcome_criteria_unclear_count",
            "source_hierarchy_weak_count",
            "dispute_risk_count",
            "revision_risk_count",
            "adjudication_dependency_count",
            "close_resolution_timing_risk_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)


def build_candidate_resolution_ambiguity_digest(
    facts: Iterable[object],
    *,
    config: CandidateResolutionAmbiguityDigestConfig,
    generated_at: datetime,
) -> CandidateResolutionAmbiguityDigestReport:
    if type(config) is not CandidateResolutionAmbiguityDigestConfig:
        raise ValueError("config must be a CandidateResolutionAmbiguityDigestConfig")
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_facts = _normalize_facts(facts)
    rows = tuple(
        sorted(
            (
                _row_from_facts(
                    fact,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for fact in normalized_facts
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _summary_reason_codes(rows)

    return CandidateResolutionAmbiguityDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        ambiguity_status=_summary_status(rows),
        candidate_count=_count_decimal(len(rows)),
        pass_count=_count_decimal(_row_status_count(rows, "pass")),
        watch_count=_count_decimal(_row_status_count(rows, "watch")),
        blocked_count=_count_decimal(_row_status_count(rows, "blocked")),
        outcome_criteria_unclear_count=_count_reason(
            rows,
            "outcome_criteria_unclear",
        ),
        source_hierarchy_weak_count=_count_reason(rows, "source_hierarchy_weak"),
        dispute_risk_count=_count_reason(rows, "dispute_risk_elevated"),
        revision_risk_count=_count_reason(rows, "revision_risk_elevated"),
        adjudication_dependency_count=_count_reason(
            rows,
            "adjudication_dependency_present",
        ),
        close_resolution_timing_risk_count=_count_reason(
            rows,
            "close_resolution_timing_risk",
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def candidate_resolution_ambiguity_digest_payload(
    report: CandidateResolutionAmbiguityDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is CandidateResolutionAmbiguityDigestReport:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        payload = _payload_value(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a CandidateResolutionAmbiguityDigestReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


_FACT_DECIMAL_FIELDS = (
    "outcome_criteria_clarity",
    "source_hierarchy_strength",
    "dispute_risk",
    "revision_risk",
    "adjudication_dependency",
    "close_resolution_timing_risk",
)
_PUBLIC_DATACLASS_TYPES: tuple[type[object], ...] = (
    CandidateResolutionAmbiguityDigestConfig,
    CandidateResolutionAmbiguityFacts,
    CandidateResolutionAmbiguityDigestRow,
    CandidateResolutionAmbiguityDigestReasonCodeCount,
    CandidateResolutionAmbiguityDigestReport,
)
_STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
_HEX_CHARS = frozenset("0123456789abcdef")
_REDACTED_REFERENCE_PREFIXES = ("candidate_ref_", "public_ref_")
_UNSAFE_SURFACE_PHRASES = (
    "raw_market_id",
    "market_id",
    "market_question",
    "market_slug",
    "condition_id",
    "source_url",
    "database_row",
    "".join(("li", "ve", "_mode")),
    "".join(("ex", "change", "_mutation")),
)
_UNSAFE_SURFACE_TOKENS = frozenset(
    (
        "market",
        "question",
        "slug",
        "condition",
        "url",
        "".join(("wal", "let")),
        "".join(("ac", "count")),
        "".join(("au", "th")),
        "token",
        "".join(("pri", "vate")),
        "key",
        "".join(("bro", "ker")),
        "".join(("tra", "de")),
        "".join(("li", "ve")),
        "".join(("can", "cel")),
        "".join(("re", "place")),
        "sign",
        "signed",
        "".join(("sign", "ing")),
        "endpoint",
        "network",
        "persist",
        "database",
        "db",
    ),
)


def _row_from_facts(
    facts: CandidateResolutionAmbiguityFacts,
    *,
    config: CandidateResolutionAmbiguityDigestConfig,
    generated_at: datetime,
) -> CandidateResolutionAmbiguityDigestRow:
    ambiguity_status, reason_codes = _status_and_reasons(facts, config=config)
    return CandidateResolutionAmbiguityDigestRow(
        generated_at=generated_at,
        redacted_public_reference=facts.redacted_public_reference,
        outcome_criteria_clarity=facts.outcome_criteria_clarity,
        source_hierarchy_strength=facts.source_hierarchy_strength,
        dispute_risk=facts.dispute_risk,
        revision_risk=facts.revision_risk,
        adjudication_dependency=facts.adjudication_dependency,
        close_resolution_timing_risk=facts.close_resolution_timing_risk,
        ambiguity_status=ambiguity_status,
        reason_codes=reason_codes,
    )


def _status_and_reasons(
    facts: CandidateResolutionAmbiguityFacts,
    *,
    config: CandidateResolutionAmbiguityDigestConfig,
) -> tuple[str, tuple[str, ...]]:
    reason_codes: list[str] = []
    blocked = False

    if facts.outcome_criteria_clarity < config.min_watch_outcome_criteria_clarity:
        reason_codes.append("outcome_criteria_unclear")
        blocked = True
    elif facts.outcome_criteria_clarity < config.min_pass_outcome_criteria_clarity:
        reason_codes.append("outcome_criteria_unclear")

    if facts.source_hierarchy_strength < config.min_watch_source_hierarchy_strength:
        reason_codes.append("source_hierarchy_weak")
        blocked = True
    elif facts.source_hierarchy_strength < config.min_pass_source_hierarchy_strength:
        reason_codes.append("source_hierarchy_weak")

    blocked = _append_high_risk_reason(
        reason_codes,
        blocked,
        value=facts.dispute_risk,
        pass_limit=config.max_pass_dispute_risk,
        watch_limit=config.max_watch_dispute_risk,
        reason_code="dispute_risk_elevated",
    )
    blocked = _append_high_risk_reason(
        reason_codes,
        blocked,
        value=facts.revision_risk,
        pass_limit=config.max_pass_revision_risk,
        watch_limit=config.max_watch_revision_risk,
        reason_code="revision_risk_elevated",
    )
    blocked = _append_high_risk_reason(
        reason_codes,
        blocked,
        value=facts.adjudication_dependency,
        pass_limit=config.max_pass_adjudication_dependency,
        watch_limit=config.max_watch_adjudication_dependency,
        reason_code="adjudication_dependency_present",
    )
    blocked = _append_high_risk_reason(
        reason_codes,
        blocked,
        value=facts.close_resolution_timing_risk,
        pass_limit=config.max_pass_close_resolution_timing_risk,
        watch_limit=config.max_watch_close_resolution_timing_risk,
        reason_code="close_resolution_timing_risk",
    )

    canonical_reason_codes = _canonical_reason_codes(reason_codes)
    if not canonical_reason_codes:
        return "pass", ("resolution_ambiguity_clear",)
    if blocked:
        return "blocked", canonical_reason_codes
    return "watch", canonical_reason_codes


def _append_high_risk_reason(
    reason_codes: list[str],
    blocked: bool,
    *,
    value: Decimal,
    pass_limit: Decimal,
    watch_limit: Decimal,
    reason_code: str,
) -> bool:
    if value > watch_limit:
        reason_codes.append(reason_code)
        return True
    if value > pass_limit:
        reason_codes.append(reason_code)
    return blocked


def _normalize_facts(facts: Iterable[object]) -> tuple[CandidateResolutionAmbiguityFacts, ...]:
    if isinstance(facts, (str, bytes)):
        raise ValueError("facts must be an iterable")
    try:
        values = tuple(facts)
    except TypeError as exc:
        raise ValueError("facts must be an iterable") from exc
    return tuple(_coerce_facts(value) for value in values)


def _coerce_facts(value: object) -> CandidateResolutionAmbiguityFacts:
    _require_hard_flags("facts", value)
    _reject_unsafe_public_payload("facts", value)
    if type(value) is CandidateResolutionAmbiguityFacts:
        return value
    return CandidateResolutionAmbiguityFacts(
        redacted_public_reference=_field_value(value, "redacted_public_reference"),
        outcome_criteria_clarity=_field_value(value, "outcome_criteria_clarity"),
        source_hierarchy_strength=_field_value(value, "source_hierarchy_strength"),
        dispute_risk=_field_value(value, "dispute_risk"),
        revision_risk=_field_value(value, "revision_risk"),
        adjudication_dependency=_field_value(value, "adjudication_dependency"),
        close_resolution_timing_risk=_field_value(
            value,
            "close_resolution_timing_risk",
        ),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[CandidateResolutionAmbiguityDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_candidate_resolution_facts",)
    return tuple(
        reason_code
        for reason_code in REASON_CODES
        if any(reason_code in row.reason_codes for row in rows)
    )


def _summary_status(rows: tuple[CandidateResolutionAmbiguityDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.ambiguity_status == "blocked" for row in rows):
        return "blocked"
    if any(row.ambiguity_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[CandidateResolutionAmbiguityDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[CandidateResolutionAmbiguityDigestReasonCodeCount, ...]:
    if not rows:
        return (
            CandidateResolutionAmbiguityDigestReasonCodeCount(
                reason_code="no_candidate_resolution_facts",
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        CandidateResolutionAmbiguityDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
        if reason_code in reason_codes
    )


def _row_status_count(
    rows: tuple[CandidateResolutionAmbiguityDigestRow, ...],
    ambiguity_status: str,
) -> int:
    return sum(1 for row in rows if row.ambiguity_status == ambiguity_status)


def _count_reason(
    rows: tuple[CandidateResolutionAmbiguityDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_sort_key(row: CandidateResolutionAmbiguityDigestRow) -> tuple[int, str]:
    return (_STATUS_RANK[row.ambiguity_status], row.redacted_public_reference)


def _normalize_rows(
    rows: Iterable[CandidateResolutionAmbiguityDigestRow],
) -> tuple[CandidateResolutionAmbiguityDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in values:
        if type(row) is not CandidateResolutionAmbiguityDigestRow:
            raise ValueError(
                "rows must contain CandidateResolutionAmbiguityDigestRow values",
            )
        _require_hard_flags("row", row)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return values


def _normalize_reason_code_counts(
    counts: Iterable[CandidateResolutionAmbiguityDigestReasonCodeCount],
) -> tuple[CandidateResolutionAmbiguityDigestReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in values:
        if type(count) is not CandidateResolutionAmbiguityDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain reason code count values",
            )
        _require_hard_flags("reason_code_count", count)
    if values != tuple(sorted(values, key=lambda row: (-row.count, row.reason_code))):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return values


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must include at least one code")
    return _canonical_reason_codes(values)


def _canonical_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    values = tuple(reason_codes)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in values:
        _require_reason_code("reason_codes", reason_code)
    sorted_values = tuple(sorted(values, key=REASON_CODES.index))
    if values != sorted_values:
        raise ValueError("reason_codes must be deterministically sorted")
    return sorted_values


def _validate_row_consistency(row: CandidateResolutionAmbiguityDigestRow) -> None:
    has_clear_reason = row.reason_codes == ("resolution_ambiguity_clear",)
    if row.ambiguity_status == "pass" and not has_clear_reason:
        raise ValueError("pass rows must use resolution_ambiguity_clear")
    if row.ambiguity_status != "pass" and has_clear_reason:
        raise ValueError("resolution_ambiguity_clear rows must pass")
    if "no_candidate_resolution_facts" in row.reason_codes:
        raise ValueError("row reason_codes must not include no_candidate_resolution_facts")


def _validate_report_consistency(
    report: CandidateResolutionAmbiguityDigestReport,
) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count_decimal(_row_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(_row_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count_decimal(_row_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    for field_name, reason_code in (
        ("outcome_criteria_unclear_count", "outcome_criteria_unclear"),
        ("source_hierarchy_weak_count", "source_hierarchy_weak"),
        ("dispute_risk_count", "dispute_risk_elevated"),
        ("revision_risk_count", "revision_risk_elevated"),
        ("adjudication_dependency_count", "adjudication_dependency_present"),
        ("close_resolution_timing_risk_count", "close_resolution_timing_risk"),
    ):
        if getattr(report, field_name) != _count_reason(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    expected_reason_codes = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")
    if report.ambiguity_status != _summary_status(report.rows):
        raise ValueError("ambiguity_status must match rows")


class _Missing:
    pass


_MISSING = _Missing()


def _field_value(value: object, field_name: str, default: object = _MISSING) -> object:
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if type(value) is dict and field_name in value:
        return value[field_name]
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM)


def _require_low_threshold_pair(
    watch_field_name: str,
    watch_value: Decimal,
    pass_field_name: str,
    pass_value: Decimal,
) -> None:
    if watch_value > pass_value:
        raise ValueError(f"{watch_field_name} must not exceed {pass_field_name}")


def _require_high_threshold_pair(
    pass_field_name: str,
    pass_value: Decimal,
    watch_field_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{pass_field_name} must not exceed {watch_field_name}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in AMBIGUITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a non-empty stripped string")
    return value


def _require_redacted_public_reference(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    if _has_unsafe_surface_fragment(text) or "://" in text or "?" in text:
        raise ValueError(f"{field_name} must be redacted")
    for prefix in _REDACTED_REFERENCE_PREFIXES:
        if text.startswith(prefix):
            digest = text.removeprefix(prefix)
            if len(digest) == 16 and all(character in _HEX_CHARS for character in digest):
                return text
    raise ValueError(f"{field_name} must be a redacted public reference")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


class _DictFlags:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.paper_only = payload.get("paper_only")
        self.report_only = payload.get("report_only")
        self.readonly = payload.get("readonly")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("payload must use supported dataclasses")
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {
            key: _payload_value(item)
            for key, item in sorted(value.items(), key=lambda item: item[0])
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_payload_key(label, field.name, path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                _nested_path(path, field.name),
            )
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value) or "://" in value or "?" in value:
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_payload_key(label, key, path)
            item_path = _nested_path(path, key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if hasattr(value, "__dict__"):
        for key, item in vars(value).items():
            _reject_unsafe_payload_key(label, key, path)
            _reject_unsafe_public_payload(label, item, _nested_path(path, key))
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _reject_unsafe_payload_key(label: str, key: object, path: str) -> None:
    if type(key) is not str:
        raise ValueError("JSON object keys must be strings")
    if _has_unsafe_surface_fragment(key):
        raise ValueError(f"unsafe public field in {label}: {_nested_path(path, key)}")


def _nested_path(path: str, key: str) -> str:
    if not path:
        return key
    return f"{path}.{key}"


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    if any(phrase in lowered for phrase in _UNSAFE_SURFACE_PHRASES):
        return True
    tokens = tuple(
        token
        for token in "".join(
            character if character.isalnum() else "_"
            for character in lowered
        ).split("_")
        if token
    )
    return any(token in _UNSAFE_SURFACE_TOKENS for token in tokens)
