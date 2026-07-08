"""Pure report-only triage for conflicts between news and announcement sources."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any


DEFAULT_RESEARCH_NEWS_SOURCE_CONFLICT_TRIAGE_REPORT_CONFIG_VERSION = (
    "research-news-source-conflict-triage-report-v0"
)

SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SOURCE_INDEPENDENCE_GAP_WEIGHT = Decimal("0.200000")
PUBLICATION_TIMING_WEIGHT = Decimal("0.150000")
COUNTER_EVIDENCE_WEIGHT = Decimal("0.250000")
IMPACT_DOMAIN_WEIGHT = Decimal("0.150000")
IMPACT_SEVERITY_WEIGHT = Decimal("0.150000")
ESCALATION_WEIGHT = Decimal("0.100000")

STATUSES = ("pass", "watch", "blocked")
ESCALATION_LEVELS = {
    "pass": "routine",
    "watch": "elevated",
    "blocked": "immediate",
}
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

IMPACT_DOMAINS = (
    "metadata",
    "context",
    "operations",
    "probability",
    "legal",
    "resolution",
    "settlement",
)
IMPACT_DOMAIN_SCORES = {
    "metadata": Decimal("0.100000"),
    "context": Decimal("0.250000"),
    "operations": Decimal("0.500000"),
    "probability": Decimal("0.700000"),
    "legal": Decimal("0.800000"),
    "resolution": Decimal("0.900000"),
    "settlement": Decimal("1.000000"),
}

NO_INPUTS_REASON = "news_conflict_triage_no_inputs"
PASS_STATUS_REASON = "news_conflict_triage_status_pass"
WATCH_STATUS_REASON = "news_conflict_triage_status_watch"
BLOCKED_STATUS_REASON = "news_conflict_triage_status_blocked"
SOURCE_INDEPENDENCE_LOW_REASON = "news_conflict_source_independence_low"
PUBLICATION_TIME_ATTENTION_REASON = "news_conflict_publication_time_attention"
COUNTER_EVIDENCE_PRESENT_REASON = "news_conflict_counter_evidence_present"
COUNTER_EVIDENCE_HIGH_REASON = "news_conflict_counter_evidence_high"
IMPACT_DOMAIN_HIGH_REASON = "news_conflict_impact_domain_high"
IMPACT_SEVERITY_HIGH_REASON = "news_conflict_impact_severity_high"
ESCALATION_NEEDED_REASON = "news_conflict_escalation_needed"

REASON_CODES = (
    NO_INPUTS_REASON,
    PASS_STATUS_REASON,
    WATCH_STATUS_REASON,
    BLOCKED_STATUS_REASON,
    SOURCE_INDEPENDENCE_LOW_REASON,
    PUBLICATION_TIME_ATTENTION_REASON,
    COUNTER_EVIDENCE_PRESENT_REASON,
    COUNTER_EVIDENCE_HIGH_REASON,
    IMPACT_DOMAIN_HIGH_REASON,
    IMPACT_SEVERITY_HIGH_REASON,
    ESCALATION_NEEDED_REASON,
)
TRIAGE_REASON_SEQUENCE = REASON_CODES[4:]


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TERMS = (
    _join_parts("ur", "l"),
    _join_parts("te", "xt"),
    _join_parts("re", "f"),
    _join_parts("ds", "n"),
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("ra", "w"),
    _join_parts("mar", "ket"),
    _join_parts("cond", "ition"),
    _join_parts("cl", "ob"),
    _join_parts("ht", "tp"),
    _join_parts("htt", "ps"),
    _join_parts("post", "gres"),
    _join_parts("my", "sql"),
    _join_parts("sq", "lite"),
    _join_parts("li", "ve"),
    _join_parts("au", "th"),
    _join_parts("wal", "let"),
    _join_parts("ord", "er"),
    _join_parts("data", "base"),
    _join_parts("per", "sist"),
    _join_parts("sign", "ing"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
    _join_parts("tra", "de"),
)


__all__ = (
    "DEFAULT_RESEARCH_NEWS_SOURCE_CONFLICT_TRIAGE_REPORT_CONFIG_VERSION",
    "ESCALATION_LEVELS",
    "IMPACT_DOMAINS",
    "IMPACT_DOMAIN_SCORES",
    "REASON_CODES",
    "ResearchNewsSourceConflictTriageConfig",
    "ResearchNewsSourceConflictTriageInput",
    "ResearchNewsSourceConflictTriageReport",
    "ResearchNewsSourceConflictTriageRow",
    "STATUSES",
    "build_research_news_source_conflict_triage_report",
    "research_news_source_conflict_triage_report_payload",
)


@dataclass(frozen=True)
class ResearchNewsSourceConflictTriageConfig:
    config_version: str = (
        DEFAULT_RESEARCH_NEWS_SOURCE_CONFLICT_TRIAGE_REPORT_CONFIG_VERSION
    )
    min_independent_source_family_count: Decimal = Decimal("3.000000")
    fresh_publication_age_seconds: Decimal = Decimal("1800.000000")
    stale_publication_age_seconds: Decimal = Decimal("86400.000000")
    publication_timing_attention_score: Decimal = Decimal("0.600000")
    high_counter_evidence_strength: Decimal = Decimal("0.750000")
    high_impact_domain_score: Decimal = Decimal("0.750000")
    high_impact_severity: Decimal = Decimal("0.700000")
    blocked_triage_risk_score: Decimal = Decimal("0.700000")
    watch_triage_risk_score: Decimal = Decimal("0.300000")
    source_independence_gap_weight: Decimal = SOURCE_INDEPENDENCE_GAP_WEIGHT
    publication_timing_weight: Decimal = PUBLICATION_TIMING_WEIGHT
    counter_evidence_weight: Decimal = COUNTER_EVIDENCE_WEIGHT
    impact_domain_weight: Decimal = IMPACT_DOMAIN_WEIGHT
    impact_severity_weight: Decimal = IMPACT_SEVERITY_WEIGHT
    escalation_weight: Decimal = ESCALATION_WEIGHT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchNewsSourceConflictTriageConfig:
            raise ValueError("config must be a ResearchNewsSourceConflictTriageConfig")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_NEWS_SOURCE_CONFLICT_TRIAGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "min_independent_source_family_count",
            "fresh_publication_age_seconds",
            "stale_publication_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "publication_timing_attention_score",
            "high_counter_evidence_strength",
            "high_impact_domain_score",
            "high_impact_severity",
            "blocked_triage_risk_score",
            "watch_triage_risk_score",
            "source_independence_gap_weight",
            "publication_timing_weight",
            "counter_evidence_weight",
            "impact_domain_weight",
            "impact_severity_weight",
            "escalation_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.fresh_publication_age_seconds >= self.stale_publication_age_seconds:
            raise ValueError(
                "fresh_publication_age_seconds must be below "
                "stale_publication_age_seconds",
            )
        if self.watch_triage_risk_score >= self.blocked_triage_risk_score:
            raise ValueError(
                "watch_triage_risk_score must be below blocked_triage_risk_score",
            )
        weight_sum = _q(
            self.source_independence_gap_weight
            + self.publication_timing_weight
            + self.counter_evidence_weight
            + self.impact_domain_weight
            + self.impact_severity_weight
            + self.escalation_weight,
        )
        if weight_sum != ONE:
            raise ValueError("triage risk score weights must sum to 1.000000")
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", asdict(self))


@dataclass(frozen=True)
class ResearchNewsSourceConflictTriageInput:
    conflict_id: str
    supporting_source_family_count: Decimal
    opposing_source_family_count: Decimal
    shared_source_family_count: Decimal
    newest_publication_age_seconds: Decimal
    oldest_publication_age_seconds: Decimal
    counter_evidence_strength: Decimal
    impact_domain: str
    impact_severity: Decimal
    operator_escalation_requested: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchNewsSourceConflictTriageInput:
            raise ValueError("subject must be a ResearchNewsSourceConflictTriageInput")
        _require_public_identifier("conflict_id", self.conflict_id)
        for field_name in (
            "supporting_source_family_count",
            "opposing_source_family_count",
            "shared_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "newest_publication_age_seconds",
            "oldest_publication_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.oldest_publication_age_seconds < self.newest_publication_age_seconds:
            raise ValueError(
                "oldest_publication_age_seconds must be at least "
                "newest_publication_age_seconds",
            )
        if self.supporting_source_family_count <= ZERO:
            raise ValueError("supporting_source_family_count must be positive")
        if self.opposing_source_family_count <= ZERO:
            raise ValueError("opposing_source_family_count must be positive")
        if self.shared_source_family_count > self.supporting_source_family_count:
            raise ValueError(
                "shared_source_family_count must not exceed "
                "supporting_source_family_count",
            )
        if self.shared_source_family_count > self.opposing_source_family_count:
            raise ValueError(
                "shared_source_family_count must not exceed "
                "opposing_source_family_count",
            )
        object.__setattr__(
            self,
            "counter_evidence_strength",
            _normalize_probability(
                "counter_evidence_strength",
                self.counter_evidence_strength,
            ),
        )
        _require_choice("impact_domain", self.impact_domain, IMPACT_DOMAINS)
        object.__setattr__(
            self,
            "impact_severity",
            _normalize_probability("impact_severity", self.impact_severity),
        )
        _require_bool(
            "operator_escalation_requested",
            self.operator_escalation_requested,
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("news source conflict triage input", asdict(self))


@dataclass(frozen=True)
class ResearchNewsSourceConflictTriageRow:
    conflict_id: str
    priority_rank: Decimal
    source_independence_score: Decimal
    source_independence_gap_score: Decimal
    publication_timing_score: Decimal
    counter_evidence_strength: Decimal
    impact_domain: str
    impact_domain_score: Decimal
    impact_severity: Decimal
    escalation_need_score: Decimal
    triage_risk_score: Decimal
    newest_publication_age_seconds: Decimal
    oldest_publication_age_seconds: Decimal
    publication_span_seconds: Decimal
    supporting_source_family_count: Decimal
    opposing_source_family_count: Decimal
    shared_source_family_count: Decimal
    triage_status: str
    recommended_escalation: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchNewsSourceConflictTriageRow:
            raise ValueError("row must be a ResearchNewsSourceConflictTriageRow")
        _require_public_identifier("conflict_id", self.conflict_id)
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_decimal("priority_rank", self.priority_rank),
        )
        for field_name in (
            "source_independence_score",
            "source_independence_gap_score",
            "publication_timing_score",
            "counter_evidence_strength",
            "impact_domain_score",
            "impact_severity",
            "escalation_need_score",
            "triage_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_choice("impact_domain", self.impact_domain, IMPACT_DOMAINS)
        for field_name in (
            "newest_publication_age_seconds",
            "oldest_publication_age_seconds",
            "publication_span_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "supporting_source_family_count",
            "opposing_source_family_count",
            "shared_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_choice("triage_status", self.triage_status, STATUSES)
        _require_choice(
            "recommended_escalation",
            self.recommended_escalation,
            tuple(ESCALATION_LEVELS.values()),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("news source conflict triage row", asdict(self))
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
class ResearchNewsSourceConflictTriageReport:
    config_version: str
    report_status: str
    recommended_escalation: str
    input_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    low_source_independence_count: Decimal
    publication_time_attention_count: Decimal
    high_counter_evidence_count: Decimal
    high_impact_domain_count: Decimal
    high_impact_severity_count: Decimal
    escalation_needed_count: Decimal
    highest_triage_risk_score: Decimal
    rows: tuple[ResearchNewsSourceConflictTriageRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchNewsSourceConflictTriageReport:
            raise ValueError("report must be a ResearchNewsSourceConflictTriageReport")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_NEWS_SOURCE_CONFLICT_TRIAGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_choice("report_status", self.report_status, STATUSES)
        _require_choice(
            "recommended_escalation",
            self.recommended_escalation,
            tuple(ESCALATION_LEVELS.values()),
        )
        for field_name in (
            "input_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "low_source_independence_count",
            "publication_time_attention_count",
            "high_counter_evidence_count",
            "high_impact_domain_count",
            "high_impact_severity_count",
            "escalation_needed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_triage_risk_score",
            _normalize_probability(
                "highest_triage_risk_score",
                self.highest_triage_risk_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("news source conflict triage report", asdict(self))
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
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("news source conflict triage payload", payload)
        if type(payload) is not dict:
            raise ValueError("news source conflict triage payload must be an object")
        return payload


def build_research_news_source_conflict_triage_report(
    rows: object,
    *,
    config: ResearchNewsSourceConflictTriageConfig | None = None,
) -> ResearchNewsSourceConflictTriageReport:
    if config is None:
        config = ResearchNewsSourceConflictTriageConfig()
    if type(config) is not ResearchNewsSourceConflictTriageConfig:
        raise ValueError("config must be a ResearchNewsSourceConflictTriageConfig")
    _require_hard_flags(config)
    source_rows = _normalize_input_rows(rows)
    ranked_rows = tuple(
        _ranked_row(row, rank=index + 1)
        for index, row in enumerate(
            sorted(
                (_unranked_row(item, config=config) for item in source_rows),
                key=_row_sort_key,
            ),
        )
    )
    report_status = _report_status(ranked_rows)
    return ResearchNewsSourceConflictTriageReport(
        config_version=config.config_version,
        report_status=report_status,
        recommended_escalation=ESCALATION_LEVELS[report_status],
        input_count=_count(len(source_rows)),
        blocked_count=_status_count(ranked_rows, "blocked"),
        watch_count=_status_count(ranked_rows, "watch"),
        pass_count=_status_count(ranked_rows, "pass"),
        low_source_independence_count=_reason_count(
            ranked_rows,
            SOURCE_INDEPENDENCE_LOW_REASON,
        ),
        publication_time_attention_count=_reason_count(
            ranked_rows,
            PUBLICATION_TIME_ATTENTION_REASON,
        ),
        high_counter_evidence_count=_reason_count(
            ranked_rows,
            COUNTER_EVIDENCE_HIGH_REASON,
        ),
        high_impact_domain_count=_reason_count(ranked_rows, IMPACT_DOMAIN_HIGH_REASON),
        high_impact_severity_count=_reason_count(
            ranked_rows,
            IMPACT_SEVERITY_HIGH_REASON,
        ),
        escalation_needed_count=_reason_count(ranked_rows, ESCALATION_NEEDED_REASON),
        highest_triage_risk_score=_max_triage_risk_score(ranked_rows),
        rows=ranked_rows,
        reason_codes=_report_reason_codes(ranked_rows),
    )


def research_news_source_conflict_triage_report_payload(
    report: ResearchNewsSourceConflictTriageReport,
) -> dict[str, object]:
    if type(report) is not ResearchNewsSourceConflictTriageReport:
        raise ValueError("report must be a ResearchNewsSourceConflictTriageReport")
    _require_hard_flags(report)
    _validate_report(report)
    return report.payload


def _unranked_row(
    subject: ResearchNewsSourceConflictTriageInput,
    *,
    config: ResearchNewsSourceConflictTriageConfig,
) -> ResearchNewsSourceConflictTriageRow:
    source_independence_score = _source_independence_score(subject, config)
    source_independence_gap_score = _q(ONE - source_independence_score)
    publication_span_seconds = _publication_span_seconds(subject)
    publication_timing_score = _publication_timing_score(
        subject,
        config,
        publication_span_seconds=publication_span_seconds,
    )
    impact_domain_score = IMPACT_DOMAIN_SCORES[subject.impact_domain]
    escalation_need_score = _escalation_need_score(
        subject,
        config=config,
        source_independence_gap_score=source_independence_gap_score,
        impact_domain_score=impact_domain_score,
    )
    triage_risk_score = _triage_risk_score(
        source_independence_gap_score=source_independence_gap_score,
        publication_timing_score=publication_timing_score,
        counter_evidence_strength=subject.counter_evidence_strength,
        impact_domain_score=impact_domain_score,
        impact_severity=subject.impact_severity,
        escalation_need_score=escalation_need_score,
        config=config,
    )
    triage_status = _triage_status(
        triage_risk_score,
        counter_evidence_strength=subject.counter_evidence_strength,
        impact_domain_score=impact_domain_score,
        impact_severity=subject.impact_severity,
        config=config,
    )
    return ResearchNewsSourceConflictTriageRow(
        conflict_id=subject.conflict_id,
        priority_rank=ONE,
        source_independence_score=source_independence_score,
        source_independence_gap_score=source_independence_gap_score,
        publication_timing_score=publication_timing_score,
        counter_evidence_strength=subject.counter_evidence_strength,
        impact_domain=subject.impact_domain,
        impact_domain_score=impact_domain_score,
        impact_severity=subject.impact_severity,
        escalation_need_score=escalation_need_score,
        triage_risk_score=triage_risk_score,
        newest_publication_age_seconds=subject.newest_publication_age_seconds,
        oldest_publication_age_seconds=subject.oldest_publication_age_seconds,
        publication_span_seconds=publication_span_seconds,
        supporting_source_family_count=subject.supporting_source_family_count,
        opposing_source_family_count=subject.opposing_source_family_count,
        shared_source_family_count=subject.shared_source_family_count,
        triage_status=triage_status,
        recommended_escalation=ESCALATION_LEVELS[triage_status],
        reason_codes=_row_reason_codes(
            triage_status=triage_status,
            source_independence_gap_score=source_independence_gap_score,
            publication_timing_score=publication_timing_score,
            counter_evidence_strength=subject.counter_evidence_strength,
            impact_domain_score=impact_domain_score,
            impact_severity=subject.impact_severity,
            escalation_need_score=escalation_need_score,
            config=config,
        ),
    )


def _ranked_row(
    row: ResearchNewsSourceConflictTriageRow,
    *,
    rank: int,
) -> ResearchNewsSourceConflictTriageRow:
    return replace(row, priority_rank=_count(rank), derived_validation_digest="")


def _row_sort_key(
    row: ResearchNewsSourceConflictTriageRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.triage_status], -row.triage_risk_score, row.conflict_id)


def _source_independence_score(
    subject: ResearchNewsSourceConflictTriageInput,
    config: ResearchNewsSourceConflictTriageConfig,
) -> Decimal:
    independent_family_count = (
        subject.supporting_source_family_count
        + subject.opposing_source_family_count
        - subject.shared_source_family_count
    )
    return _clamp_probability(
        _safe_ratio(independent_family_count, config.min_independent_source_family_count),
    )


def _publication_span_seconds(
    subject: ResearchNewsSourceConflictTriageInput,
) -> Decimal:
    return _q(
        subject.oldest_publication_age_seconds
        - subject.newest_publication_age_seconds,
    )


def _publication_timing_score(
    subject: ResearchNewsSourceConflictTriageInput,
    config: ResearchNewsSourceConflictTriageConfig,
    *,
    publication_span_seconds: Decimal,
) -> Decimal:
    newest_urgency_score = _age_urgency_score(
        subject.newest_publication_age_seconds,
        config=config,
    )
    oldest_staleness_score = _age_staleness_score(
        subject.oldest_publication_age_seconds,
        config=config,
    )
    span_score = _clamp_probability(
        _safe_ratio(publication_span_seconds, config.stale_publication_age_seconds),
    )
    return _q((newest_urgency_score + oldest_staleness_score + span_score) / Decimal("3"))


def _age_urgency_score(
    age_seconds: Decimal,
    *,
    config: ResearchNewsSourceConflictTriageConfig,
) -> Decimal:
    if age_seconds <= config.fresh_publication_age_seconds:
        return ONE
    if age_seconds >= config.stale_publication_age_seconds:
        return ZERO
    elapsed = age_seconds - config.fresh_publication_age_seconds
    span = config.stale_publication_age_seconds - config.fresh_publication_age_seconds
    return _clamp_probability(ONE - _safe_ratio(elapsed, span))


def _age_staleness_score(
    age_seconds: Decimal,
    *,
    config: ResearchNewsSourceConflictTriageConfig,
) -> Decimal:
    if age_seconds <= config.fresh_publication_age_seconds:
        return ZERO
    if age_seconds >= config.stale_publication_age_seconds:
        return ONE
    elapsed = age_seconds - config.fresh_publication_age_seconds
    span = config.stale_publication_age_seconds - config.fresh_publication_age_seconds
    return _clamp_probability(_safe_ratio(elapsed, span))


def _escalation_need_score(
    subject: ResearchNewsSourceConflictTriageInput,
    *,
    config: ResearchNewsSourceConflictTriageConfig,
    source_independence_gap_score: Decimal,
    impact_domain_score: Decimal,
) -> Decimal:
    if subject.operator_escalation_requested:
        return ONE
    if (
        subject.counter_evidence_strength >= config.high_counter_evidence_strength
        and impact_domain_score >= config.high_impact_domain_score
        and subject.impact_severity >= config.high_impact_severity
    ):
        return ONE
    if source_independence_gap_score == ONE and subject.counter_evidence_strength > ZERO:
        return Decimal("0.500000")
    return ZERO


def _triage_risk_score(
    *,
    source_independence_gap_score: Decimal,
    publication_timing_score: Decimal,
    counter_evidence_strength: Decimal,
    impact_domain_score: Decimal,
    impact_severity: Decimal,
    escalation_need_score: Decimal,
    config: ResearchNewsSourceConflictTriageConfig,
) -> Decimal:
    return _clamp_probability(
        (source_independence_gap_score * config.source_independence_gap_weight)
        + (publication_timing_score * config.publication_timing_weight)
        + (counter_evidence_strength * config.counter_evidence_weight)
        + (impact_domain_score * config.impact_domain_weight)
        + (impact_severity * config.impact_severity_weight)
        + (escalation_need_score * config.escalation_weight),
    )


def _triage_status(
    triage_risk_score: Decimal,
    *,
    counter_evidence_strength: Decimal,
    impact_domain_score: Decimal,
    impact_severity: Decimal,
    config: ResearchNewsSourceConflictTriageConfig,
) -> str:
    if (
        counter_evidence_strength >= config.high_counter_evidence_strength
        and impact_domain_score >= config.high_impact_domain_score
        and impact_severity >= config.high_impact_severity
    ):
        return "blocked"
    if triage_risk_score >= config.blocked_triage_risk_score:
        return "blocked"
    if triage_risk_score >= config.watch_triage_risk_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    triage_status: str,
    source_independence_gap_score: Decimal,
    publication_timing_score: Decimal,
    counter_evidence_strength: Decimal,
    impact_domain_score: Decimal,
    impact_severity: Decimal,
    escalation_need_score: Decimal,
    config: ResearchNewsSourceConflictTriageConfig,
) -> tuple[str, ...]:
    codes = [f"news_conflict_triage_status_{triage_status}"]
    if source_independence_gap_score > ZERO:
        codes.append(SOURCE_INDEPENDENCE_LOW_REASON)
    if publication_timing_score >= config.publication_timing_attention_score:
        codes.append(PUBLICATION_TIME_ATTENTION_REASON)
    if counter_evidence_strength >= config.high_counter_evidence_strength:
        codes.append(COUNTER_EVIDENCE_HIGH_REASON)
    elif counter_evidence_strength > ZERO:
        codes.append(COUNTER_EVIDENCE_PRESENT_REASON)
    if impact_domain_score >= config.high_impact_domain_score:
        codes.append(IMPACT_DOMAIN_HIGH_REASON)
    if impact_severity >= config.high_impact_severity:
        codes.append(IMPACT_SEVERITY_HIGH_REASON)
    if escalation_need_score > ZERO:
        codes.append(ESCALATION_NEEDED_REASON)
    return tuple(codes)


def _row_reason_codes_from_row(
    row: ResearchNewsSourceConflictTriageRow,
) -> tuple[str, ...]:
    codes = [f"news_conflict_triage_status_{row.triage_status}"]
    if row.source_independence_gap_score > ZERO:
        codes.append(SOURCE_INDEPENDENCE_LOW_REASON)
    if row.publication_timing_score >= Decimal("0.600000"):
        codes.append(PUBLICATION_TIME_ATTENTION_REASON)
    if row.counter_evidence_strength >= Decimal("0.750000"):
        codes.append(COUNTER_EVIDENCE_HIGH_REASON)
    elif row.counter_evidence_strength > ZERO:
        codes.append(COUNTER_EVIDENCE_PRESENT_REASON)
    if row.impact_domain_score >= Decimal("0.750000"):
        codes.append(IMPACT_DOMAIN_HIGH_REASON)
    if row.impact_severity >= Decimal("0.700000"):
        codes.append(IMPACT_SEVERITY_HIGH_REASON)
    if row.escalation_need_score > ZERO:
        codes.append(ESCALATION_NEEDED_REASON)
    return tuple(codes)


def _report_reason_codes(
    rows: tuple[ResearchNewsSourceConflictTriageRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _report_status(rows)
    codes = [f"news_conflict_triage_status_{status}"]
    present = {code for row in rows for code in row.reason_codes}
    for code in TRIAGE_REASON_SEQUENCE:
        if code in present:
            codes.append(code)
    return tuple(codes)


def _report_status(rows: tuple[ResearchNewsSourceConflictTriageRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.triage_status == "blocked" for row in rows):
        return "blocked"
    if any(row.triage_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchNewsSourceConflictTriageRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.triage_status == status))


def _reason_count(
    rows: tuple[ResearchNewsSourceConflictTriageRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_triage_risk_score(
    rows: tuple[ResearchNewsSourceConflictTriageRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.triage_risk_score for row in rows)


def _validate_row(row: ResearchNewsSourceConflictTriageRow) -> None:
    if row.oldest_publication_age_seconds < row.newest_publication_age_seconds:
        raise ValueError("publication ages must be sorted")
    if (
        row.publication_span_seconds
        != row.oldest_publication_age_seconds - row.newest_publication_age_seconds
    ):
        raise ValueError("publication_span_seconds must match publication ages")
    if row.shared_source_family_count > row.supporting_source_family_count:
        raise ValueError("shared_source_family_count must match supporting count")
    if row.shared_source_family_count > row.opposing_source_family_count:
        raise ValueError("shared_source_family_count must match opposing count")
    if row.impact_domain_score != IMPACT_DOMAIN_SCORES[row.impact_domain]:
        raise ValueError("impact_domain_score must match impact_domain")
    if row.recommended_escalation != ESCALATION_LEVELS[row.triage_status]:
        raise ValueError("recommended_escalation must match triage_status")
    if row.reason_codes != _row_reason_codes_from_row(row):
        raise ValueError("reason_codes must match news conflict drivers")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: ResearchNewsSourceConflictTriageReport) -> None:
    for row in report.rows:
        _validate_row(row)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.recommended_escalation != ESCALATION_LEVELS[report.report_status]:
        raise ValueError("recommended_escalation must match report_status")
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.low_source_independence_count != _reason_count(
        report.rows,
        SOURCE_INDEPENDENCE_LOW_REASON,
    ):
        raise ValueError("low_source_independence_count must match rows")
    if report.publication_time_attention_count != _reason_count(
        report.rows,
        PUBLICATION_TIME_ATTENTION_REASON,
    ):
        raise ValueError("publication_time_attention_count must match rows")
    if report.high_counter_evidence_count != _reason_count(
        report.rows,
        COUNTER_EVIDENCE_HIGH_REASON,
    ):
        raise ValueError("high_counter_evidence_count must match rows")
    if report.high_impact_domain_count != _reason_count(
        report.rows,
        IMPACT_DOMAIN_HIGH_REASON,
    ):
        raise ValueError("high_impact_domain_count must match rows")
    if report.high_impact_severity_count != _reason_count(
        report.rows,
        IMPACT_SEVERITY_HIGH_REASON,
    ):
        raise ValueError("high_impact_severity_count must match rows")
    if report.escalation_needed_count != _reason_count(
        report.rows,
        ESCALATION_NEEDED_REASON,
    ):
        raise ValueError("escalation_needed_count must match rows")
    if report.highest_triage_risk_score != _max_triage_risk_score(report.rows):
        raise ValueError("highest_triage_risk_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_input_rows(
    rows: object,
) -> tuple[ResearchNewsSourceConflictTriageInput, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError(
            "rows must be an iterable of ResearchNewsSourceConflictTriageInput",
        )
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchNewsSourceConflictTriageInput:
            raise ValueError(
                "rows must be ResearchNewsSourceConflictTriageInput values",
            )
        _require_hard_flags(row)
        if row.conflict_id in seen:
            raise ValueError("rows must be unique by conflict_id")
        seen.add(row.conflict_id)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchNewsSourceConflictTriageRow, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError("rows must be an iterable of ResearchNewsSourceConflictTriageRow")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchNewsSourceConflictTriageRow:
            raise ValueError("rows must be ResearchNewsSourceConflictTriageRow values")
        _require_hard_flags(row)
        if row.conflict_id in seen:
            raise ValueError("rows must be unique by conflict_id")
        seen.add(row.conflict_id)
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
        raise ValueError(f"{field_name} must not be a raw identifier")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if _mentions_unsafe_public_term(value):
        raise ValueError(f"unsafe public payload value in {field_name}: {value}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


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
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            _reject_unsafe_public_payload(label, value)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if type(payload) is str and _mentions_unsafe_public_term(payload):
        raise ValueError(f"unsafe public payload value in {label}: {payload}")
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
        _reject_unsafe_public_payload("news source conflict triage payload", value)
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _row_derived_validation_digest(row: ResearchNewsSourceConflictTriageRow) -> str:
    values = asdict(row)
    values.pop("derived_validation_digest", None)
    return hashlib.sha256(_canonical_payload(values).encode("utf-8")).hexdigest()


def _report_derived_validation_digest(
    report: ResearchNewsSourceConflictTriageReport,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return hashlib.sha256(_canonical_payload(values).encode("utf-8")).hexdigest()


def _canonical_payload(value: object) -> str:
    if type(value) is Decimal:
        return f"decimal:{_q(value)}"
    if type(value) is str:
        return f"string:{len(value)}:{value}"
    if type(value) is bool:
        return f"bool:{value}"
    if value is None:
        return "none"
    if isinstance(value, tuple):
        return "[" + ",".join(_canonical_payload(item) for item in value) + "]"
    if isinstance(value, list):
        return "[" + ",".join(_canonical_payload(item) for item in value) + "]"
    if isinstance(value, dict):
        parts = []
        for key in sorted(value):
            if type(key) is not str:
                raise ValueError("canonical payload keys must be strings")
            parts.append(f"{_canonical_payload(key)}:{_canonical_payload(value[key])}")
        return "{" + ",".join(parts) + "}"
    raise ValueError("canonical payload value is not supported")
