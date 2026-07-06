"""Pure in-memory research packet information quality scoring report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_INFORMATION_QUALITY_SCORE_CONFIG_VERSION = (
    "research-packet-information-quality-score-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
STATUSES = (STATUS_BLOCKED, STATUS_WATCH, STATUS_PASS)
STATUS_SORT_WEIGHT = {STATUS_BLOCKED: Decimal("0"), STATUS_WATCH: Decimal("1"), STATUS_PASS: Decimal("2")}

CLEAR_REASON = "research_packet_information_quality_clear"
NO_SOURCE_EVIDENCE_REASON = "no_source_evidence"
CONTRADICTION_RISK_REASON = "contradiction_risk_elevated"
EVIDENCE_TRACEABILITY_REASON = "evidence_traceability_weak"
OFFICIAL_SOURCE_COVERAGE_REASON = "official_source_coverage_thin"
RESOLUTION_CRITERIA_UNCLEAR_REASON = "resolution_criteria_unclear"
SOURCE_DIVERSITY_THIN_REASON = "source_diversity_thin"
SOURCE_RECENCY_STALE_REASON = "source_recency_stale"

PROBLEM_REASON_CODES = (
    CONTRADICTION_RISK_REASON,
    EVIDENCE_TRACEABILITY_REASON,
    OFFICIAL_SOURCE_COVERAGE_REASON,
    RESOLUTION_CRITERIA_UNCLEAR_REASON,
    SOURCE_DIVERSITY_THIN_REASON,
    SOURCE_RECENCY_STALE_REASON,
)
ROW_REASON_CODES = (CLEAR_REASON, *PROBLEM_REASON_CODES)
REPORT_REASON_CODES = (NO_SOURCE_EVIDENCE_REASON, CLEAR_REASON, *PROBLEM_REASON_CODES)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE_COUNT = Decimal("1").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
HALF_RATIO = Decimal("0.5").quantize(RATIO_QUANTUM)
ONE_RATIO = Decimal("1").quantize(RATIO_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
DIGEST_HEX_LENGTH = 64


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("or", "der"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sign", "ing"),
        _join_parts("muta", "tion"),
        _join_parts("bu", "y"),
        _join_parts("se", "ll"),
        _join_parts("tra", "de"),
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
class ResearchPacketInformationQualityScoreConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_PACKET_INFORMATION_QUALITY_SCORE_CONFIG_VERSION
    fresh_source_max_age_seconds: Decimal = Decimal("3600.000000")
    usable_source_max_age_seconds: Decimal = Decimal("86400.000000")
    min_official_source_count: Decimal = Decimal("1")
    min_source_family_count: Decimal = Decimal("2")
    min_traceable_source_count: Decimal = Decimal("2")
    min_resolution_criteria_characters: Decimal = Decimal("40")
    pass_quality_score: Decimal = Decimal("0.800000")
    watch_quality_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchPacketInformationQualityScoreConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_PACKET_INFORMATION_QUALITY_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "fresh_source_max_age_seconds",
            _require_positive_seconds(
                "fresh_source_max_age_seconds",
                self.fresh_source_max_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "usable_source_max_age_seconds",
            _require_positive_seconds(
                "usable_source_max_age_seconds",
                self.usable_source_max_age_seconds,
            ),
        )
        if self.fresh_source_max_age_seconds > self.usable_source_max_age_seconds:
            raise ValueError(
                "fresh_source_max_age_seconds must be less than or equal to "
                "usable_source_max_age_seconds",
            )
        for field_name in (
            "min_official_source_count",
            "min_source_family_count",
            "min_traceable_source_count",
            "min_resolution_criteria_characters",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pass_quality_score", "watch_quality_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_quality_score > self.pass_quality_score:
            raise ValueError("watch_quality_score must be less than or equal to pass_quality_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketInformationQualitySourceEvidence(_FinalPublicDataclass):
    packet_id: str
    market_slug: str
    event_title: str
    resolution_criteria: str
    source_id: str
    source_name: str
    source_family: str
    source_reference: str
    source_published_at: datetime
    observed_at: datetime
    is_official_source: bool
    supports_resolution_criteria: bool
    supports_current_outcome: bool
    contradicts_packet: bool
    evidence_quote: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchPacketInformationQualitySourceEvidence,
            "source evidence",
        )
        for field_name in (
            "packet_id",
            "market_slug",
            "event_title",
            "resolution_criteria",
            "source_id",
            "source_name",
            "source_family",
            "source_reference",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_optional_canonical_string("evidence_quote", self.evidence_quote)
        object.__setattr__(
            self,
            "source_published_at",
            _as_utc("source_published_at", self.source_published_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "is_official_source",
            "supports_resolution_criteria",
            "supports_current_outcome",
            "contradicts_packet",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("source evidence", self)


@dataclass(frozen=True)
class ResearchPacketInformationQualityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    packet_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchPacketInformationQualityReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, PROBLEM_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "packet_ratio",
            _require_ratio_decimal("packet_ratio", self.packet_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchPacketInformationQualityScoreRow(_FinalPublicDataclass):
    packet_id: str
    market_slug: str
    event_title: str
    resolution_criteria: str
    latest_source_published_at: datetime
    newest_source_age_seconds: Decimal
    source_count: Decimal
    official_source_count: Decimal
    source_family_count: Decimal
    traceable_source_count: Decimal
    criteria_support_source_count: Decimal
    outcome_support_source_count: Decimal
    contradiction_source_count: Decimal
    source_recency_score: Decimal
    official_source_coverage_score: Decimal
    source_diversity_score: Decimal
    contradiction_risk_score: Decimal
    resolution_criteria_clarity_score: Decimal
    evidence_traceability_score: Decimal
    information_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    source_references: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchPacketInformationQualityScoreRow, "row")
        for field_name in (
            "packet_id",
            "market_slug",
            "event_title",
            "resolution_criteria",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_source_published_at",
            _as_utc("latest_source_published_at", self.latest_source_published_at),
        )
        object.__setattr__(
            self,
            "newest_source_age_seconds",
            _require_nonnegative_seconds(
                "newest_source_age_seconds",
                self.newest_source_age_seconds,
            ),
        )
        for field_name in (
            "source_count",
            "official_source_count",
            "source_family_count",
            "traceable_source_count",
            "criteria_support_source_count",
            "outcome_support_source_count",
            "contradiction_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_recency_score",
            "official_source_coverage_score",
            "source_diversity_score",
            "contradiction_risk_score",
            "resolution_criteria_clarity_score",
            "evidence_traceability_score",
            "information_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
                clear_reasons=(CLEAR_REASON,),
            ),
        )
        object.__setattr__(
            self,
            "source_references",
            _normalize_string_tuple("source_references", self.source_references),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchPacketInformationQualityScoreReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    fresh_source_max_age_seconds: Decimal
    usable_source_max_age_seconds: Decimal
    min_official_source_count: Decimal
    min_source_family_count: Decimal
    min_traceable_source_count: Decimal
    min_resolution_criteria_characters: Decimal
    pass_quality_score: Decimal
    watch_quality_score: Decimal
    status: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_information_quality_score: Decimal
    average_source_recency_score: Decimal
    average_official_source_coverage_score: Decimal
    average_source_diversity_score: Decimal
    average_contradiction_risk_score: Decimal
    average_resolution_criteria_clarity_score: Decimal
    average_evidence_traceability_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchPacketInformationQualityReasonCodeCount, ...]
    rows: tuple[ResearchPacketInformationQualityScoreRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchPacketInformationQualityScoreReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_PACKET_INFORMATION_QUALITY_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "fresh_source_max_age_seconds",
            _require_positive_seconds(
                "fresh_source_max_age_seconds",
                self.fresh_source_max_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "usable_source_max_age_seconds",
            _require_positive_seconds(
                "usable_source_max_age_seconds",
                self.usable_source_max_age_seconds,
            ),
        )
        if self.fresh_source_max_age_seconds > self.usable_source_max_age_seconds:
            raise ValueError(
                "fresh_source_max_age_seconds must be less than or equal to "
                "usable_source_max_age_seconds",
            )
        for field_name in (
            "min_official_source_count",
            "min_source_family_count",
            "min_traceable_source_count",
            "min_resolution_criteria_characters",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pass_quality_score", "watch_quality_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_quality_score > self.pass_quality_score:
            raise ValueError("watch_quality_score must be less than or equal to pass_quality_score")
        _require_member("status", self.status, STATUSES)
        for field_name in ("packet_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_information_quality_score",
            "average_source_recency_score",
            "average_official_source_coverage_score",
            "average_source_diversity_score",
            "average_contradiction_risk_score",
            "average_resolution_criteria_clarity_score",
            "average_evidence_traceability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
                clear_reasons=(NO_SOURCE_EVIDENCE_REASON, CLEAR_REASON),
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        _validate_report_consistency(self)
        _require_derived_validation_digest(self)
        _require_hard_flags("report", self)


def build_research_packet_information_quality_score_report(
    source_evidence: list[ResearchPacketInformationQualitySourceEvidence]
    | tuple[ResearchPacketInformationQualitySourceEvidence, ...],
    *,
    config: ResearchPacketInformationQualityScoreConfig,
    generated_at: datetime,
) -> ResearchPacketInformationQualityScoreReport:
    if type(config) is not ResearchPacketInformationQualityScoreConfig:
        raise ValueError("config must be a ResearchPacketInformationQualityScoreConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_rows = _normalize_source_evidence(source_evidence)
    _reject_future_evidence_times(evidence_rows, generated_at_utc)
    grouped = _group_evidence_by_packet(evidence_rows)
    rows = tuple(
        sorted(
            (
                _score_packet_rows(packet_rows, config=config, generated_at=generated_at_utc)
                for packet_rows in grouped
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    status = _report_status(rows)
    packet_count = _decimal_count(len(rows))
    pass_count = _count_status(rows, STATUS_PASS)
    watch_count = _count_status(rows, STATUS_WATCH)
    blocked_count = _count_status(rows, STATUS_BLOCKED)
    reason_code_counts = _reason_code_counts(reason_codes, rows)
    derived_validation_digest = _derived_validation_digest_from_fields(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        fresh_source_max_age_seconds=config.fresh_source_max_age_seconds,
        usable_source_max_age_seconds=config.usable_source_max_age_seconds,
        min_official_source_count=config.min_official_source_count,
        min_source_family_count=config.min_source_family_count,
        min_traceable_source_count=config.min_traceable_source_count,
        min_resolution_criteria_characters=config.min_resolution_criteria_characters,
        pass_quality_score=config.pass_quality_score,
        watch_quality_score=config.watch_quality_score,
        status=status,
        packet_count=packet_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        average_information_quality_score=_average_row_score(rows, "information_quality_score"),
        average_source_recency_score=_average_row_score(rows, "source_recency_score"),
        average_official_source_coverage_score=_average_row_score(
            rows,
            "official_source_coverage_score",
        ),
        average_source_diversity_score=_average_row_score(rows, "source_diversity_score"),
        average_contradiction_risk_score=_average_row_score(
            rows,
            "contradiction_risk_score",
        ),
        average_resolution_criteria_clarity_score=_average_row_score(
            rows,
            "resolution_criteria_clarity_score",
        ),
        average_evidence_traceability_score=_average_row_score(
            rows,
            "evidence_traceability_score",
        ),
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=rows,
    )

    return ResearchPacketInformationQualityScoreReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        fresh_source_max_age_seconds=config.fresh_source_max_age_seconds,
        usable_source_max_age_seconds=config.usable_source_max_age_seconds,
        min_official_source_count=config.min_official_source_count,
        min_source_family_count=config.min_source_family_count,
        min_traceable_source_count=config.min_traceable_source_count,
        min_resolution_criteria_characters=config.min_resolution_criteria_characters,
        pass_quality_score=config.pass_quality_score,
        watch_quality_score=config.watch_quality_score,
        status=status,
        packet_count=packet_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        average_information_quality_score=_average_row_score(rows, "information_quality_score"),
        average_source_recency_score=_average_row_score(rows, "source_recency_score"),
        average_official_source_coverage_score=_average_row_score(
            rows,
            "official_source_coverage_score",
        ),
        average_source_diversity_score=_average_row_score(rows, "source_diversity_score"),
        average_contradiction_risk_score=_average_row_score(
            rows,
            "contradiction_risk_score",
        ),
        average_resolution_criteria_clarity_score=_average_row_score(
            rows,
            "resolution_criteria_clarity_score",
        ),
        average_evidence_traceability_score=_average_row_score(
            rows,
            "evidence_traceability_score",
        ),
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=derived_validation_digest,
    )


def research_packet_information_quality_score_payload(
    report: ResearchPacketInformationQualityScoreReport | dict[str, Any],
) -> dict[str, Any]:
    label = "research packet information quality score payload"
    if type(report) is ResearchPacketInformationQualityScoreReport:
        _require_hard_flags("report", report)
        ready = _json_ready_no_floats(report)
        if not isinstance(ready, dict):
            raise ValueError("report payload must be a JSON object")
        _require_payload_flags(label, ready)
        _reject_payload_flag_downgrades(label, ready)
        _reject_unsafe_public_payload(label, ready)
        _require_payload_digest_if_present(ready)
        return ready
    if isinstance(report, dict):
        _require_payload_flags(label, report)
        _reject_payload_flag_downgrades(label, report)
        _reject_unsafe_public_payload(label, report)
        ready = _json_ready_no_floats(report)
        if not isinstance(ready, dict):
            raise ValueError("report payload must be a JSON object")
        _require_payload_flags(label, ready)
        _reject_payload_flag_downgrades(label, ready)
        _reject_unsafe_public_payload(label, ready)
        _require_payload_digest_if_present(ready)
        return ready
    raise ValueError("report must be a ResearchPacketInformationQualityScoreReport")


def _score_packet_rows(
    packet_rows: tuple[ResearchPacketInformationQualitySourceEvidence, ...],
    *,
    config: ResearchPacketInformationQualityScoreConfig,
    generated_at: datetime,
) -> ResearchPacketInformationQualityScoreRow:
    packet_id = packet_rows[0].packet_id
    market_slug = packet_rows[0].market_slug
    event_title = packet_rows[0].event_title
    resolution_criteria = packet_rows[0].resolution_criteria
    for evidence in packet_rows:
        if evidence.market_slug != market_slug:
            raise ValueError("market_slug must be stable within packet_id")
        if evidence.event_title != event_title:
            raise ValueError("event_title must be stable within packet_id")
        if evidence.resolution_criteria != resolution_criteria:
            raise ValueError("resolution_criteria must be stable within packet_id")

    latest_source_published_at = max(row.source_published_at for row in packet_rows)
    newest_source_age_seconds = _age_seconds(latest_source_published_at, generated_at)
    source_count = _decimal_count(len(packet_rows))
    official_source_count = _decimal_count(sum(1 for row in packet_rows if row.is_official_source))
    source_family_count = _decimal_count(len({row.source_family for row in packet_rows}))
    traceable_source_count = _decimal_count(sum(1 for row in packet_rows if _is_traceable(row)))
    criteria_support_source_count = _decimal_count(
        sum(1 for row in packet_rows if row.supports_resolution_criteria),
    )
    outcome_support_source_count = _decimal_count(
        sum(1 for row in packet_rows if row.supports_current_outcome),
    )
    contradiction_source_count = _decimal_count(
        sum(1 for row in packet_rows if row.contradicts_packet),
    )
    source_recency_score = _source_recency_score(
        newest_source_age_seconds,
        config=config,
    )
    official_source_coverage_score = _score_count(
        official_source_count,
        config.min_official_source_count,
    )
    source_diversity_score = _score_count(
        source_family_count,
        config.min_source_family_count,
    )
    contradiction_risk_score = _contradiction_risk_score(
        contradiction_source_count,
        source_count,
    )
    resolution_criteria_clarity_score = _resolution_criteria_clarity_score(
        resolution_criteria,
        criteria_support_source_count,
        config=config,
    )
    evidence_traceability_score = _score_count(
        traceable_source_count,
        config.min_traceable_source_count,
    )
    information_quality_score = _average_decimal(
        (
            source_recency_score,
            official_source_coverage_score,
            source_diversity_score,
            contradiction_risk_score,
            resolution_criteria_clarity_score,
            evidence_traceability_score,
        ),
    )
    reason_codes = _row_reason_codes(
        source_recency_score=source_recency_score,
        official_source_coverage_score=official_source_coverage_score,
        source_diversity_score=source_diversity_score,
        contradiction_source_count=contradiction_source_count,
        resolution_criteria_clarity_score=resolution_criteria_clarity_score,
        evidence_traceability_score=evidence_traceability_score,
    )

    return ResearchPacketInformationQualityScoreRow(
        packet_id=packet_id,
        market_slug=market_slug,
        event_title=event_title,
        resolution_criteria=resolution_criteria,
        latest_source_published_at=latest_source_published_at,
        newest_source_age_seconds=newest_source_age_seconds,
        source_count=source_count,
        official_source_count=official_source_count,
        source_family_count=source_family_count,
        traceable_source_count=traceable_source_count,
        criteria_support_source_count=criteria_support_source_count,
        outcome_support_source_count=outcome_support_source_count,
        contradiction_source_count=contradiction_source_count,
        source_recency_score=source_recency_score,
        official_source_coverage_score=official_source_coverage_score,
        source_diversity_score=source_diversity_score,
        contradiction_risk_score=contradiction_risk_score,
        resolution_criteria_clarity_score=resolution_criteria_clarity_score,
        evidence_traceability_score=evidence_traceability_score,
        information_quality_score=information_quality_score,
        status=_row_status(
            information_quality_score=information_quality_score,
            contradiction_source_count=contradiction_source_count,
            config=config,
        ),
        reason_codes=reason_codes,
        source_references=tuple(sorted({row.source_reference for row in packet_rows})),
    )


def _normalize_source_evidence(
    value: object,
) -> tuple[ResearchPacketInformationQualitySourceEvidence, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("source_evidence must be a list or tuple")
    rows = tuple(value)
    seen_source_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketInformationQualitySourceEvidence:
            raise ValueError(
                "source_evidence must contain "
                "ResearchPacketInformationQualitySourceEvidence values",
            )
        _require_hard_flags("source evidence", row)
        if row.source_id in seen_source_ids:
            raise ValueError("duplicate source_id values are not allowed")
        seen_source_ids.add(row.source_id)
    return rows


def _group_evidence_by_packet(
    rows: tuple[ResearchPacketInformationQualitySourceEvidence, ...],
) -> tuple[tuple[ResearchPacketInformationQualitySourceEvidence, ...], ...]:
    packet_ids = tuple(sorted({row.packet_id for row in rows}))
    return tuple(
        tuple(sorted((row for row in rows if row.packet_id == packet_id), key=_evidence_sort_key))
        for packet_id in packet_ids
    )


def _reject_future_evidence_times(
    rows: tuple[ResearchPacketInformationQualitySourceEvidence, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        for field_name in ("source_published_at", "observed_at"):
            value = getattr(row, field_name)
            if value > generated_at:
                raise ValueError(f"future {field_name} values are not allowed")


def _source_recency_score(
    newest_source_age_seconds: Decimal,
    *,
    config: ResearchPacketInformationQualityScoreConfig,
) -> Decimal:
    if newest_source_age_seconds <= config.fresh_source_max_age_seconds:
        return ONE_RATIO
    if newest_source_age_seconds <= config.usable_source_max_age_seconds:
        return HALF_RATIO
    return ZERO_RATIO


def _score_count(actual: Decimal, required: Decimal) -> Decimal:
    if required <= ZERO_COUNT:
        raise ValueError("required count must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(actual / required)


def _contradiction_risk_score(contradiction_count: Decimal, source_count: Decimal) -> Decimal:
    if source_count <= ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE_RATIO - (contradiction_count / source_count))


def _resolution_criteria_clarity_score(
    resolution_criteria: str,
    criteria_support_source_count: Decimal,
    *,
    config: ResearchPacketInformationQualityScoreConfig,
) -> Decimal:
    criteria_length = _decimal_count(len(resolution_criteria))
    if (
        criteria_length >= config.min_resolution_criteria_characters
        and criteria_support_source_count > ZERO_COUNT
    ):
        return ONE_RATIO
    return ZERO_RATIO


def _row_reason_codes(
    *,
    source_recency_score: Decimal,
    official_source_coverage_score: Decimal,
    source_diversity_score: Decimal,
    contradiction_source_count: Decimal,
    resolution_criteria_clarity_score: Decimal,
    evidence_traceability_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if contradiction_source_count > ZERO_COUNT:
        reasons.append(CONTRADICTION_RISK_REASON)
    if evidence_traceability_score < ONE_RATIO:
        reasons.append(EVIDENCE_TRACEABILITY_REASON)
    if official_source_coverage_score < ONE_RATIO:
        reasons.append(OFFICIAL_SOURCE_COVERAGE_REASON)
    if resolution_criteria_clarity_score < ONE_RATIO:
        reasons.append(RESOLUTION_CRITERIA_UNCLEAR_REASON)
    if source_diversity_score < ONE_RATIO:
        reasons.append(SOURCE_DIVERSITY_THIN_REASON)
    if source_recency_score < ONE_RATIO:
        reasons.append(SOURCE_RECENCY_STALE_REASON)
    if not reasons:
        return (CLEAR_REASON,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        ROW_REASON_CODES,
        clear_reasons=(CLEAR_REASON,),
    )


def _row_status(
    *,
    information_quality_score: Decimal,
    contradiction_source_count: Decimal,
    config: ResearchPacketInformationQualityScoreConfig,
) -> str:
    if contradiction_source_count > ZERO_COUNT:
        return STATUS_BLOCKED
    if information_quality_score >= config.pass_quality_score:
        return STATUS_PASS
    if information_quality_score >= config.watch_quality_score:
        return STATUS_WATCH
    return STATUS_BLOCKED


def _report_reason_codes(
    rows: tuple[ResearchPacketInformationQualityScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_SOURCE_EVIDENCE_REASON,)
    reasons: list[str] = []
    for reason_code in PROBLEM_REASON_CODES:
        if any(reason_code in row.reason_codes for row in rows):
            reasons.append(reason_code)
    if not reasons:
        return (CLEAR_REASON,)
    return tuple(reasons)


def _report_status(rows: tuple[ResearchPacketInformationQualityScoreRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchPacketInformationQualityScoreRow, ...],
) -> tuple[ResearchPacketInformationQualityReasonCodeCount, ...]:
    if not rows or reason_codes in ((NO_SOURCE_EVIDENCE_REASON,), (CLEAR_REASON,)):
        return ()
    packet_count = _decimal_count(len(rows))
    counts: list[ResearchPacketInformationQualityReasonCodeCount] = []
    for reason_code in PROBLEM_REASON_CODES:
        if reason_code not in reason_codes:
            continue
        count = _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))
        if count > ZERO_COUNT:
            counts.append(
                ResearchPacketInformationQualityReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    packet_ratio=_ratio(count, packet_count),
                ),
            )
    return tuple(counts)


def _normalize_report_rows(
    value: object,
) -> tuple[ResearchPacketInformationQualityScoreRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_packet_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketInformationQualityScoreRow:
            raise ValueError("rows must contain ResearchPacketInformationQualityScoreRow values")
        _require_hard_flags("row", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("rows must not contain duplicate packet_id values")
        seen_packet_ids.add(row.packet_id)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchPacketInformationQualityReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not ResearchPacketInformationQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchPacketInformationQualityReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_reason_codes.add(count.reason_code)
    expected_order = tuple(
        reason_code for reason_code in PROBLEM_REASON_CODES if reason_code in seen_reason_codes
    )
    if tuple(count.reason_code for count in counts) != expected_order:
        raise ValueError("reason_code_counts must be deterministic")
    return counts


def _validate_row_consistency(row: ResearchPacketInformationQualityScoreRow) -> None:
    if row.source_count <= ZERO_COUNT:
        raise ValueError("source_count must be positive")
    for field_name in (
        "official_source_count",
        "source_family_count",
        "traceable_source_count",
        "criteria_support_source_count",
        "outcome_support_source_count",
        "contradiction_source_count",
    ):
        if getattr(row, field_name) > row.source_count:
            raise ValueError(f"{field_name} must be less than or equal to source_count")
    expected_score = _average_decimal(
        (
            row.source_recency_score,
            row.official_source_coverage_score,
            row.source_diversity_score,
            row.contradiction_risk_score,
            row.resolution_criteria_clarity_score,
            row.evidence_traceability_score,
        ),
    )
    if row.information_quality_score != expected_score:
        raise ValueError("information_quality_score must equal the scoring component average")
    if row.reason_codes != _row_reason_codes(
        source_recency_score=row.source_recency_score,
        official_source_coverage_score=row.official_source_coverage_score,
        source_diversity_score=row.source_diversity_score,
        contradiction_source_count=row.contradiction_source_count,
        resolution_criteria_clarity_score=row.resolution_criteria_clarity_score,
        evidence_traceability_score=row.evidence_traceability_score,
    ):
        raise ValueError("reason_codes must match row scores")
    if row.source_references != tuple(sorted(row.source_references)):
        raise ValueError("source_references must be deterministic")


def _validate_report_consistency(report: ResearchPacketInformationQualityScoreReport) -> None:
    expected_counts = {
        "packet_count": _decimal_count(len(report.rows)),
        "pass_count": _count_status(report.rows, STATUS_PASS),
        "watch_count": _count_status(report.rows, STATUS_WATCH),
        "blocked_count": _count_status(report.rows, STATUS_BLOCKED),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_averages = {
        "average_information_quality_score": _average_row_score(
            report.rows,
            "information_quality_score",
        ),
        "average_source_recency_score": _average_row_score(report.rows, "source_recency_score"),
        "average_official_source_coverage_score": _average_row_score(
            report.rows,
            "official_source_coverage_score",
        ),
        "average_source_diversity_score": _average_row_score(
            report.rows,
            "source_diversity_score",
        ),
        "average_contradiction_risk_score": _average_row_score(
            report.rows,
            "contradiction_risk_score",
        ),
        "average_resolution_criteria_clarity_score": _average_row_score(
            report.rows,
            "resolution_criteria_clarity_score",
        ),
        "average_evidence_traceability_score": _average_row_score(
            report.rows,
            "evidence_traceability_score",
        ),
    }
    for field_name, expected in expected_averages.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")
    expected_reason_code_counts = _reason_code_counts(report.reason_codes, report.rows)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    for row in report.rows:
        expected_status = _row_status(
            information_quality_score=row.information_quality_score,
            contradiction_source_count=row.contradiction_source_count,
            config=ResearchPacketInformationQualityScoreConfig(
                config_version=report.config_version,
                fresh_source_max_age_seconds=report.fresh_source_max_age_seconds,
                usable_source_max_age_seconds=report.usable_source_max_age_seconds,
                min_official_source_count=report.min_official_source_count,
                min_source_family_count=report.min_source_family_count,
                min_traceable_source_count=report.min_traceable_source_count,
                min_resolution_criteria_characters=report.min_resolution_criteria_characters,
                pass_quality_score=report.pass_quality_score,
                watch_quality_score=report.watch_quality_score,
            ),
        )
        if row.status != expected_status:
            raise ValueError("row status must match report thresholds")


def _require_derived_validation_digest(report: ResearchPacketInformationQualityScoreReport) -> None:
    digest = _require_digest_string(report.derived_validation_digest)
    expected = _derived_validation_digest_from_fields(
        generated_at=report.generated_at,
        config_version=report.config_version,
        fresh_source_max_age_seconds=report.fresh_source_max_age_seconds,
        usable_source_max_age_seconds=report.usable_source_max_age_seconds,
        min_official_source_count=report.min_official_source_count,
        min_source_family_count=report.min_source_family_count,
        min_traceable_source_count=report.min_traceable_source_count,
        min_resolution_criteria_characters=report.min_resolution_criteria_characters,
        pass_quality_score=report.pass_quality_score,
        watch_quality_score=report.watch_quality_score,
        status=report.status,
        packet_count=report.packet_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        average_information_quality_score=report.average_information_quality_score,
        average_source_recency_score=report.average_source_recency_score,
        average_official_source_coverage_score=report.average_official_source_coverage_score,
        average_source_diversity_score=report.average_source_diversity_score,
        average_contradiction_risk_score=report.average_contradiction_risk_score,
        average_resolution_criteria_clarity_score=(
            report.average_resolution_criteria_clarity_score
        ),
        average_evidence_traceability_score=report.average_evidence_traceability_score,
        reason_codes=report.reason_codes,
        reason_code_counts=report.reason_code_counts,
        rows=report.rows,
    )
    if digest != expected:
        raise ValueError("derived_validation_digest does not match report contents")


def _derived_validation_digest_from_fields(
    *,
    generated_at: datetime,
    config_version: str,
    fresh_source_max_age_seconds: Decimal,
    usable_source_max_age_seconds: Decimal,
    min_official_source_count: Decimal,
    min_source_family_count: Decimal,
    min_traceable_source_count: Decimal,
    min_resolution_criteria_characters: Decimal,
    pass_quality_score: Decimal,
    watch_quality_score: Decimal,
    status: str,
    packet_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    average_information_quality_score: Decimal,
    average_source_recency_score: Decimal,
    average_official_source_coverage_score: Decimal,
    average_source_diversity_score: Decimal,
    average_contradiction_risk_score: Decimal,
    average_resolution_criteria_clarity_score: Decimal,
    average_evidence_traceability_score: Decimal,
    reason_codes: tuple[str, ...],
    reason_code_counts: tuple[ResearchPacketInformationQualityReasonCodeCount, ...],
    rows: tuple[ResearchPacketInformationQualityScoreRow, ...],
) -> str:
    return _digest_public_payload(
        {
            "generated_at": generated_at,
            "config_version": config_version,
            "fresh_source_max_age_seconds": fresh_source_max_age_seconds,
            "usable_source_max_age_seconds": usable_source_max_age_seconds,
            "min_official_source_count": min_official_source_count,
            "min_source_family_count": min_source_family_count,
            "min_traceable_source_count": min_traceable_source_count,
            "min_resolution_criteria_characters": min_resolution_criteria_characters,
            "pass_quality_score": pass_quality_score,
            "watch_quality_score": watch_quality_score,
            "status": status,
            "packet_count": packet_count,
            "pass_count": pass_count,
            "watch_count": watch_count,
            "blocked_count": blocked_count,
            "average_information_quality_score": average_information_quality_score,
            "average_source_recency_score": average_source_recency_score,
            "average_official_source_coverage_score": average_official_source_coverage_score,
            "average_source_diversity_score": average_source_diversity_score,
            "average_contradiction_risk_score": average_contradiction_risk_score,
            "average_resolution_criteria_clarity_score": (
                average_resolution_criteria_clarity_score
            ),
            "average_evidence_traceability_score": average_evidence_traceability_score,
            "reason_codes": reason_codes,
            "reason_code_counts": reason_code_counts,
            "rows": rows,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )


def _digest_public_payload(payload: object) -> str:
    ready = _json_ready_no_floats(payload)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_payload_digest_if_present(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        return
    supplied = _require_digest_string(payload["derived_validation_digest"])
    digest_payload = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    expected = _digest_public_payload(digest_payload)
    if supplied != expected:
        raise ValueError("derived_validation_digest does not match payload contents")


def _require_digest_string(value: object) -> str:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != DIGEST_HEX_LENGTH:
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hexadecimal")
    return value


def _average_row_score(
    rows: tuple[ResearchPacketInformationQualityScoreRow, ...],
    field_name: str,
) -> Decimal:
    return _average_decimal(tuple(getattr(row, field_name) for row in rows))


def _count_status(rows: tuple[ResearchPacketInformationQualityScoreRow, ...], status: str) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(sum(values, ZERO_RATIO) / _decimal_count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO_RATIO:
        return ZERO_RATIO
    if value >= ONE_RATIO:
        return ONE_RATIO
    return _quantize_ratio(value)


def _decimal_count(value: object) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _quantize_seconds(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SECONDS_QUANTUM)


def _age_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        (delta.days * 86400 * 1000000)
        + (delta.seconds * 1000000)
        + delta.microseconds
    )
    return _require_nonnegative_seconds(
        "age_seconds",
        _quantize_seconds(Decimal(total_microseconds) / Decimal("1000000")),
    )


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(COUNT_QUANTUM)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_count_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_count_decimal(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_ratio(_require_decimal(field_name, value))
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _quantize_seconds(_require_decimal(field_name, value))
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    normalized = _quantize_seconds(_require_decimal(field_name, value))
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not have leading or trailing whitespace")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _require_optional_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value and value.strip() != value:
        raise ValueError(f"{field_name} must not have leading or trailing whitespace")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(_require_canonical_string(field_name, item) for item in value)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
    *,
    clear_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member(field_name, code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(code in clear_reasons for code in codes) and len(codes) > 1:
        raise ValueError(f"{field_name} must not mix clear and problem reasons")
    expected = tuple(code for code in allowed if code in codes)
    if codes != expected:
        raise ValueError(f"{field_name} must be deterministic")
    return codes


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_payload_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for flag_name in ("paper_only", "report_only", "readonly"):
            if flag_name in value and value[flag_name] is not True:
                raise ValueError(f"{flag_name} must be True for {label}")
        for item in value.values():
            _reject_payload_flag_downgrades(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_payload_flag_downgrades(label, item)


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for key in _iter_public_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public surface field in {label}: {key}")
    for value in _iter_public_strings(payload):
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public surface value in {label}: {value}")
    _reject_public_numeric_scalars(payload)


def _iter_public_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_public_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_public_keys(item))
        return tuple(keys)
    return ()


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if type(value) is str:
        return (value,)
    if isinstance(value, dict):
        strings: list[str] = []
        for item in value.values():
            strings.extend(_iter_public_strings(item))
        return tuple(strings)
    if isinstance(value, (list, tuple)):
        strings = []
        for item in value:
            strings.extend(_iter_public_strings(item))
        return tuple(strings)
    return ()


def _reject_public_numeric_scalars(value: object) -> None:
    if type(value) in (bool, str) or value is None:
        return
    if type(value) in (float, int):
        raise ValueError("public numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_scalars(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_scalars(item)


def _json_ready_no_floats(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_no_floats(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("generated_at" if type(value) is datetime else "datetime", value).isoformat()
    if type(value) is bool:
        return value
    if type(value) in (float, int):
        raise ValueError("public numeric values must be Decimal strings")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            ready[key] = _json_ready_no_floats(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_no_floats(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _is_traceable(row: ResearchPacketInformationQualitySourceEvidence) -> bool:
    return bool(row.source_reference and row.evidence_quote)


def _evidence_sort_key(
    row: ResearchPacketInformationQualitySourceEvidence,
) -> tuple[str, str, str]:
    return (row.packet_id, row.source_family, row.source_id)


def _row_sort_key(row: ResearchPacketInformationQualityScoreRow) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_SORT_WEIGHT[row.status],
        ZERO_RATIO - row.information_quality_score,
        row.packet_id,
    )


__all__ = (
    "DEFAULT_RESEARCH_PACKET_INFORMATION_QUALITY_SCORE_CONFIG_VERSION",
    "ResearchPacketInformationQualityReasonCodeCount",
    "ResearchPacketInformationQualityScoreConfig",
    "ResearchPacketInformationQualityScoreReport",
    "ResearchPacketInformationQualityScoreRow",
    "ResearchPacketInformationQualitySourceEvidence",
    "build_research_packet_information_quality_score_report",
    "research_packet_information_quality_score_payload",
)
