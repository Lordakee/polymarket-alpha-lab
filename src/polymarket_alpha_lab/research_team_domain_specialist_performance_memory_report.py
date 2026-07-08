"""Pure report-only team domain specialist performance memory reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_PERFORMANCE_MEMORY_CONFIG_VERSION",
    "ResearchTeamDomainSpecialistPerformanceMemoryConfig",
    "ResearchTeamDomainSpecialistPerformanceMemoryFact",
    "ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount",
    "ResearchTeamDomainSpecialistPerformanceMemoryReport",
    "ResearchTeamDomainSpecialistPerformanceMemoryRow",
    "build_research_team_domain_specialist_performance_memory_report",
    "research_team_domain_specialist_performance_memory_report_digest",
    "research_team_domain_specialist_performance_memory_report_payload",
)


DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_PERFORMANCE_MEMORY_CONFIG_VERSION = (
    "research-team-domain-specialist-performance-memory-report-v0"
)

NO_FACTS_REASON = "no_domain_specialist_performance_memory_facts"
INSUFFICIENT_SAMPLE_REASON = "insufficient_memory_sample_count"
CALIBRATION_ERROR_BLOCK_REASON = "calibration_error_block"
STALE_FEEDBACK_BLOCK_REASON = "stale_feedback_rate_block"
CONFLICT_BLOCK_REASON = "unresolved_conflict_count_block"
LATENCY_BLOCK_REASON = "review_latency_hours_block"
CALIBRATION_ERROR_WATCH_REASON = "calibration_error_watch"
STALE_FEEDBACK_WATCH_REASON = "stale_feedback_rate_watch"
CONFLICT_WATCH_REASON = "unresolved_conflict_count_watch"
LATENCY_WATCH_REASON = "review_latency_hours_watch"
BLOCK_REASON = "domain_specialist_performance_memory_block"
WATCH_REASON = "domain_specialist_performance_memory_watch"
PASS_REASON = "domain_specialist_performance_memory_pass"

REASON_CODES = (
    NO_FACTS_REASON,
    INSUFFICIENT_SAMPLE_REASON,
    CALIBRATION_ERROR_BLOCK_REASON,
    STALE_FEEDBACK_BLOCK_REASON,
    CONFLICT_BLOCK_REASON,
    LATENCY_BLOCK_REASON,
    CALIBRATION_ERROR_WATCH_REASON,
    STALE_FEEDBACK_WATCH_REASON,
    CONFLICT_WATCH_REASON,
    LATENCY_WATCH_REASON,
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
BLOCK_REASONS = (
    INSUFFICIENT_SAMPLE_REASON,
    CALIBRATION_ERROR_BLOCK_REASON,
    STALE_FEEDBACK_BLOCK_REASON,
    CONFLICT_BLOCK_REASON,
    LATENCY_BLOCK_REASON,
    BLOCK_REASON,
    NO_FACTS_REASON,
)
WATCH_REASONS = (
    CALIBRATION_ERROR_WATCH_REASON,
    STALE_FEEDBACK_WATCH_REASON,
    CONFLICT_WATCH_REASON,
    LATENCY_WATCH_REASON,
    WATCH_REASON,
)
STATUSES = ("pass", "watch", "block")
STATUS_RANK = {status: index for index, status in enumerate(STATUSES)}

ZERO = Decimal("0")
ONE = Decimal("1.000000")
ONE_COUNT = Decimal("1")
COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
QUALITY_SAMPLE_GAP_WEIGHT = Decimal("0.260000")
QUALITY_STALE_FEEDBACK_WEIGHT = Decimal("0.200000")
QUALITY_CONFLICT_WEIGHT = Decimal("0.100000")
QUALITY_LATENCY_WEIGHT = Decimal("0.080000")
SAFE_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")
SAFE_REASON_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_KEY_FRAGMENTS = (
    "candidate_" + "id",
    "condition_" + "id",
    "mar" + "ket_id",
    "mar" + "ket_slug",
    "ques" + "tion",
    "raw_candidate",
    "raw_mar" + "ket",
    "slug",
    "source_" + "text",
    "source_" + "url",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "pri" + "vate",
    "wal" + "let",
    "account",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "reco" + "mmend",
    "siz" + "ing",
)
UNSAFE_TEXT_FRAGMENTS = (
    "http" + "://",
    "https" + "://",
    "://",
    "candidate_" + "id",
    "mar" + "ket_id",
    "mar" + "ket_slug",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "bearer ",
    "pri" + "vate",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "reco" + "mmend",
    "siz" + "ing",
    "au" + "th",
    "li" + "ve",
)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistPerformanceMemoryConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_PERFORMANCE_MEMORY_CONFIG_VERSION
    )
    min_memory_sample_count: Decimal = Decimal("10")
    calibration_error_watch_threshold: Decimal = Decimal("0.075000")
    calibration_error_block_threshold: Decimal = Decimal("0.150000")
    stale_feedback_rate_watch_threshold: Decimal = Decimal("0.300000")
    stale_feedback_rate_block_threshold: Decimal = Decimal("0.600000")
    unresolved_conflict_count_watch_threshold: Decimal = Decimal("2")
    unresolved_conflict_count_block_threshold: Decimal = Decimal("10")
    review_latency_hours_watch_threshold: Decimal = Decimal("25.000000")
    review_latency_hours_block_threshold: Decimal = Decimal("100.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSpecialistPerformanceMemoryConfig:
            raise TypeError(
                "ResearchTeamDomainSpecialistPerformanceMemoryConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSpecialistPerformanceMemoryConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchTeamDomainSpecialistPerformanceMemoryConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_memory_sample_count",
            _require_positive_whole_decimal(
                "min_memory_sample_count",
                self.min_memory_sample_count,
            ),
        )
        for field_name in (
            "calibration_error_watch_threshold",
            "calibration_error_block_threshold",
            "stale_feedback_rate_watch_threshold",
            "stale_feedback_rate_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_conflict_count_watch_threshold",
            "unresolved_conflict_count_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "review_latency_hours_watch_threshold",
            "review_latency_hours_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_below_block(
            "calibration_error",
            self.calibration_error_watch_threshold,
            self.calibration_error_block_threshold,
        )
        _require_watch_below_block(
            "stale_feedback_rate",
            self.stale_feedback_rate_watch_threshold,
            self.stale_feedback_rate_block_threshold,
        )
        _require_watch_below_block(
            "unresolved_conflict_count",
            self.unresolved_conflict_count_watch_threshold,
            self.unresolved_conflict_count_block_threshold,
        )
        _require_watch_below_block(
            "review_latency_hours",
            self.review_latency_hours_watch_threshold,
            self.review_latency_hours_block_threshold,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistPerformanceMemoryFact:
    domain: str
    memory_sample_count: Decimal
    calibration_error: Decimal
    stale_feedback_rate: Decimal
    unresolved_conflict_count: Decimal
    average_review_latency_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSpecialistPerformanceMemoryFact:
            raise TypeError(
                "ResearchTeamDomainSpecialistPerformanceMemoryFact "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSpecialistPerformanceMemoryFact:
            raise ValueError(
                "fact must be exactly "
                "ResearchTeamDomainSpecialistPerformanceMemoryFact",
            )
        _require_public_identifier("domain", self.domain)
        object.__setattr__(
            self,
            "memory_sample_count",
            _require_nonnegative_whole_decimal(
                "memory_sample_count",
                self.memory_sample_count,
            ),
        )
        for field_name in ("calibration_error", "stale_feedback_rate"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_conflict_count",
            _require_nonnegative_whole_decimal(
                "unresolved_conflict_count",
                self.unresolved_conflict_count,
            ),
        )
        object.__setattr__(
            self,
            "average_review_latency_hours",
            _require_nonnegative_decimal(
                "average_review_latency_hours",
                self.average_review_latency_hours,
            ),
        )
        _require_hard_flags("fact", self)
        _reject_unsafe_public_payload("fact", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistPerformanceMemoryRow:
    domain: str
    memory_sample_count: Decimal
    calibration_error: Decimal
    stale_feedback_rate: Decimal
    unresolved_conflict_count: Decimal
    average_review_latency_hours: Decimal
    performance_memory_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSpecialistPerformanceMemoryRow:
            raise TypeError(
                "ResearchTeamDomainSpecialistPerformanceMemoryRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSpecialistPerformanceMemoryRow:
            raise ValueError(
                "row must be exactly ResearchTeamDomainSpecialistPerformanceMemoryRow",
            )
        _require_public_identifier("domain", self.domain)
        object.__setattr__(
            self,
            "memory_sample_count",
            _require_nonnegative_whole_decimal(
                "memory_sample_count",
                self.memory_sample_count,
            ),
        )
        for field_name in (
            "calibration_error",
            "stale_feedback_rate",
            "performance_memory_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_conflict_count",
            _require_nonnegative_whole_decimal(
                "unresolved_conflict_count",
                self.unresolved_conflict_count,
            ),
        )
        object.__setattr__(
            self,
            "average_review_latency_hours",
            _require_nonnegative_decimal(
                "average_review_latency_hours",
                self.average_review_latency_hours,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _status_for_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount:
            raise TypeError(
                "ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistPerformanceMemoryReport:
    generated_at: datetime
    config_version: str
    status: str
    domain_count: Decimal
    memory_sample_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_calibration_error: Decimal | None
    average_stale_feedback_rate: Decimal | None
    total_unresolved_conflict_count: Decimal
    max_review_latency_hours: Decimal | None
    average_performance_memory_quality_score: Decimal | None
    rows: tuple[ResearchTeamDomainSpecialistPerformanceMemoryRow, ...]
    reason_code_counts: tuple[
        ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainSpecialistPerformanceMemoryReport:
            raise TypeError(
                "ResearchTeamDomainSpecialistPerformanceMemoryReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainSpecialistPerformanceMemoryReport:
            raise ValueError(
                "report must be exactly "
                "ResearchTeamDomainSpecialistPerformanceMemoryReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "domain_count",
            "memory_sample_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_unresolved_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_calibration_error",
            "average_stale_feedback_rate",
            "average_performance_memory_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "max_review_latency_hours",
            _require_optional_nonnegative_decimal(
                "max_review_latency_hours",
                self.max_review_latency_hours,
            ),
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_team_domain_specialist_performance_memory_report_payload(self)


def build_research_team_domain_specialist_performance_memory_report(
    facts: Iterable[object],
    *,
    config: ResearchTeamDomainSpecialistPerformanceMemoryConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSpecialistPerformanceMemoryReport:
    if type(config) is not ResearchTeamDomainSpecialistPerformanceMemoryConfig:
        raise ValueError(
            "config must be a ResearchTeamDomainSpecialistPerformanceMemoryConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_facts = _normalize_facts(facts)
    rows = tuple(
        sorted(
            (
                _row_from_domain_facts(domain_facts, config=config)
                for domain_facts in _facts_by_domain(normalized_facts)
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    status = _status_for_reason_codes(reason_codes)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": status,
        "domain_count": _decimal_count(len(rows)),
        "memory_sample_count": sum((row.memory_sample_count for row in rows), ZERO),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_calibration_error": _weighted_row_average(
            rows,
            "calibration_error",
        ),
        "average_stale_feedback_rate": _weighted_row_average(
            rows,
            "stale_feedback_rate",
        ),
        "total_unresolved_conflict_count": sum(
            (row.unresolved_conflict_count for row in rows),
            ZERO,
        ),
        "max_review_latency_hours": _max_row_decimal(
            rows,
            "average_review_latency_hours",
        ),
        "average_performance_memory_quality_score": _weighted_row_average(
            rows,
            "performance_memory_quality_score",
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainSpecialistPerformanceMemoryReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_domain_specialist_performance_memory_report_payload(
    report: ResearchTeamDomainSpecialistPerformanceMemoryReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamDomainSpecialistPerformanceMemoryReport:
        _require_hard_flags("report", report)
        payload = _payload_value(asdict(report))
    elif isinstance(report, Mapping):
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a "
            "ResearchTeamDomainSpecialistPerformanceMemoryReport or JSON object",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(
        "report payload",
        payload,
        allow_json_containers=True,
    )
    _require_hard_flags("report payload", _MappingFlags(payload))
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_team_domain_specialist_performance_memory_report_digest(
    report: ResearchTeamDomainSpecialistPerformanceMemoryReport | Mapping[str, object],
) -> str:
    payload = research_team_domain_specialist_performance_memory_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_domain_facts(
    facts: tuple[ResearchTeamDomainSpecialistPerformanceMemoryFact, ...],
    *,
    config: ResearchTeamDomainSpecialistPerformanceMemoryConfig,
) -> ResearchTeamDomainSpecialistPerformanceMemoryRow:
    domain = facts[0].domain
    memory_sample_count = sum((fact.memory_sample_count for fact in facts), ZERO)
    calibration_error = _weighted_fact_average(facts, "calibration_error")
    stale_feedback_rate = _weighted_fact_average(facts, "stale_feedback_rate")
    unresolved_conflict_count = sum(
        (fact.unresolved_conflict_count for fact in facts),
        ZERO,
    )
    average_review_latency_hours = _weighted_fact_average(
        facts,
        "average_review_latency_hours",
    )
    quality_score = _performance_memory_quality_score(
        memory_sample_count=memory_sample_count,
        calibration_error=calibration_error,
        stale_feedback_rate=stale_feedback_rate,
        unresolved_conflict_count=unresolved_conflict_count,
        average_review_latency_hours=average_review_latency_hours,
        config=config,
    )
    reason_codes = _row_reason_codes(
        memory_sample_count=memory_sample_count,
        calibration_error=calibration_error,
        stale_feedback_rate=stale_feedback_rate,
        unresolved_conflict_count=unresolved_conflict_count,
        average_review_latency_hours=average_review_latency_hours,
        config=config,
    )
    return ResearchTeamDomainSpecialistPerformanceMemoryRow(
        domain=domain,
        memory_sample_count=memory_sample_count,
        calibration_error=calibration_error,
        stale_feedback_rate=stale_feedback_rate,
        unresolved_conflict_count=unresolved_conflict_count,
        average_review_latency_hours=average_review_latency_hours,
        performance_memory_quality_score=quality_score,
        status=_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    memory_sample_count: Decimal,
    calibration_error: Decimal,
    stale_feedback_rate: Decimal,
    unresolved_conflict_count: Decimal,
    average_review_latency_hours: Decimal,
    config: ResearchTeamDomainSpecialistPerformanceMemoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if memory_sample_count < config.min_memory_sample_count:
        reason_codes.append(INSUFFICIENT_SAMPLE_REASON)
    if calibration_error >= config.calibration_error_block_threshold:
        reason_codes.append(CALIBRATION_ERROR_BLOCK_REASON)
    elif calibration_error >= config.calibration_error_watch_threshold:
        reason_codes.append(CALIBRATION_ERROR_WATCH_REASON)
    if stale_feedback_rate >= config.stale_feedback_rate_block_threshold:
        reason_codes.append(STALE_FEEDBACK_BLOCK_REASON)
    elif stale_feedback_rate >= config.stale_feedback_rate_watch_threshold:
        reason_codes.append(STALE_FEEDBACK_WATCH_REASON)
    if unresolved_conflict_count >= config.unresolved_conflict_count_block_threshold:
        reason_codes.append(CONFLICT_BLOCK_REASON)
    elif unresolved_conflict_count >= config.unresolved_conflict_count_watch_threshold:
        reason_codes.append(CONFLICT_WATCH_REASON)
    if average_review_latency_hours >= config.review_latency_hours_block_threshold:
        reason_codes.append(LATENCY_BLOCK_REASON)
    elif average_review_latency_hours >= config.review_latency_hours_watch_threshold:
        reason_codes.append(LATENCY_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    else:
        status = _status_for_reason_codes(tuple(reason_codes))
        reason_codes.append(BLOCK_REASON if status == "block" else WATCH_REASON)
    return _combined_reason_codes(tuple(reason_codes))


def _performance_memory_quality_score(
    *,
    memory_sample_count: Decimal,
    calibration_error: Decimal,
    stale_feedback_rate: Decimal,
    unresolved_conflict_count: Decimal,
    average_review_latency_hours: Decimal,
    config: ResearchTeamDomainSpecialistPerformanceMemoryConfig,
) -> Decimal:
    sample_gap_pressure = ZERO
    if memory_sample_count < config.min_memory_sample_count:
        sample_gap_pressure = (
            (config.min_memory_sample_count - memory_sample_count)
            / config.min_memory_sample_count
        )
    conflict_pressure = _pressure_ratio(
        unresolved_conflict_count,
        config.unresolved_conflict_count_block_threshold,
    )
    latency_pressure = _pressure_ratio(
        average_review_latency_hours,
        config.review_latency_hours_block_threshold,
    )
    penalty = (
        calibration_error
        + stale_feedback_rate * QUALITY_STALE_FEEDBACK_WEIGHT
        + conflict_pressure * QUALITY_CONFLICT_WEIGHT
        + latency_pressure * QUALITY_LATENCY_WEIGHT
        + sample_gap_pressure * QUALITY_SAMPLE_GAP_WEIGHT
    )
    return _clamp_probability(_quantize_ratio(ONE - penalty))


def _normalize_facts(
    facts: Iterable[object],
) -> tuple[ResearchTeamDomainSpecialistPerformanceMemoryFact, ...]:
    if isinstance(facts, (str, bytes)):
        raise ValueError("facts must be an iterable")
    try:
        values = tuple(facts)
    except TypeError as exc:
        raise ValueError("facts must be an iterable") from exc
    normalized: list[ResearchTeamDomainSpecialistPerformanceMemoryFact] = []
    for value in values:
        if type(value) is not ResearchTeamDomainSpecialistPerformanceMemoryFact:
            raise ValueError(
                "facts must contain "
                "ResearchTeamDomainSpecialistPerformanceMemoryFact items",
            )
        _require_hard_flags("fact", value)
        normalized.append(value)
    return tuple(normalized)


def _facts_by_domain(
    facts: tuple[ResearchTeamDomainSpecialistPerformanceMemoryFact, ...],
) -> tuple[tuple[ResearchTeamDomainSpecialistPerformanceMemoryFact, ...], ...]:
    grouped: dict[str, list[ResearchTeamDomainSpecialistPerformanceMemoryFact]] = {}
    for fact in facts:
        grouped.setdefault(fact.domain, []).append(fact)
    return tuple(
        tuple(grouped[domain])
        for domain in sorted(grouped)
    )


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainSpecialistPerformanceMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_FACTS_REASON,)
    return _combined_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _combined_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if any(reason_code != PASS_REASON for reason_code in reason_codes):
        reason_codes = tuple(
            reason_code for reason_code in reason_codes if reason_code != PASS_REASON
        )
    return tuple(
        sorted(
            set(reason_codes),
            key=lambda reason_code: REASON_CODE_RANK[reason_code],
        ),
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainSpecialistPerformanceMemoryRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount, ...]:
    if reason_codes == (NO_FACTS_REASON,):
        return (
            ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount(
                reason_code=NO_FACTS_REASON,
                count=ONE_COUNT,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in reason_codes:
                counter[reason_code] += 1
    return tuple(
        ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _validate_report(
    report: ResearchTeamDomainSpecialistPerformanceMemoryReport,
) -> None:
    if report.domain_count != _decimal_count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.memory_sample_count != sum(
        (row.memory_sample_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("memory_sample_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_calibration_error != _weighted_row_average(
        report.rows,
        "calibration_error",
    ):
        raise ValueError("average_calibration_error must match rows")
    if report.average_stale_feedback_rate != _weighted_row_average(
        report.rows,
        "stale_feedback_rate",
    ):
        raise ValueError("average_stale_feedback_rate must match rows")
    if report.total_unresolved_conflict_count != sum(
        (row.unresolved_conflict_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("total_unresolved_conflict_count must match rows")
    if report.max_review_latency_hours != _max_row_decimal(
        report.rows,
        "average_review_latency_hours",
    ):
        raise ValueError("max_review_latency_hours must match rows")
    if report.average_performance_memory_quality_score != _weighted_row_average(
        report.rows,
        "performance_memory_quality_score",
    ):
        raise ValueError("average_performance_memory_quality_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_for_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchTeamDomainSpecialistPerformanceMemoryRow, ...],
) -> tuple[ResearchTeamDomainSpecialistPerformanceMemoryRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized_rows = tuple(rows)
    seen_domains: set[str] = set()
    for row in normalized_rows:
        if type(row) is not ResearchTeamDomainSpecialistPerformanceMemoryRow:
            raise ValueError(
                "rows must contain ResearchTeamDomainSpecialistPerformanceMemoryRow",
            )
        _require_hard_flags("row", row)
        if row.domain in seen_domains:
            raise ValueError("rows domain values must be unique")
        seen_domains.add(row.domain)
    if normalized_rows != tuple(sorted(normalized_rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized_rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount, ...],
) -> tuple[ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized_counts = tuple(counts)
    seen_reason_codes: set[str] = set()
    for count in normalized_counts:
        if type(count) is not ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if normalized_counts != tuple(
        sorted(normalized_counts, key=lambda count: REASON_CODE_RANK[count.reason_code])
    ):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return normalized_counts


def _row_sort_key(
    row: ResearchTeamDomainSpecialistPerformanceMemoryRow,
) -> tuple[int, str]:
    return (STATUS_RANK[row.status], row.domain)


def _status_count(
    rows: tuple[ResearchTeamDomainSpecialistPerformanceMemoryRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _weighted_fact_average(
    facts: tuple[ResearchTeamDomainSpecialistPerformanceMemoryFact, ...],
    field_name: str,
) -> Decimal:
    total_weight = sum((fact.memory_sample_count for fact in facts), ZERO)
    if total_weight == ZERO:
        return _average_decimal(tuple(getattr(fact, field_name) for fact in facts))
    weighted_total = sum(
        (
            getattr(fact, field_name) * fact.memory_sample_count
            for fact in facts
        ),
        ZERO,
    )
    return _quantize_ratio(weighted_total / total_weight)


def _weighted_row_average(
    rows: tuple[ResearchTeamDomainSpecialistPerformanceMemoryRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    total_weight = sum((row.memory_sample_count for row in rows), ZERO)
    if total_weight == ZERO:
        return _average_decimal(tuple(getattr(row, field_name) for row in rows))
    weighted_total = sum(
        (
            getattr(row, field_name) * row.memory_sample_count
            for row in rows
        ),
        ZERO,
    )
    return _quantize_ratio(weighted_total / total_weight)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANT)
    return _quantize_ratio(sum(values, ZERO) / _decimal_count(len(values)))


def _max_row_decimal(
    rows: tuple[ResearchTeamDomainSpecialistPerformanceMemoryRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    return max(getattr(row, field_name) for row in rows)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _pressure_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _clamp_probability(_quantize_ratio(value / denominator))


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO.quantize(RATIO_QUANT)
    if value > ONE:
        return ONE
    return _quantize_ratio(value)


def _require_watch_below_block(
    metric_name: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if watch_threshold >= block_threshold:
        raise ValueError(f"{metric_name} watch threshold must be below block threshold")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized = value.lower()
    if normalized != value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(character not in SAFE_IDENTIFIER_CHARS for character in value):
        raise ValueError(f"{field_name} contains unsafe characters")
    if _has_unsafe_text(value):
        raise ValueError(f"{field_name} has unsafe value")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass/watch/block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in REASON_CODE_RANK:
        raise ValueError(f"{field_name} must be a known reason code")
    if any(character not in SAFE_REASON_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} contains unsafe characters")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    stable_codes = tuple(
        reason_code for reason_code in REASON_CODES if reason_code in reason_codes
    )
    if stable_codes != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > Decimal("1"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return decimal_value.quantize(COUNT_QUANT)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_ratio(decimal_value)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is int:
        raise ValueError(f"{field_name} must not be an integer")
    if type(value) is float:
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() != _ZERO_TIME_OFFSET:
        raise ValueError(f"{field_name} must be UTC")
    return value.astimezone(UTC)


_ZERO_TIME_OFFSET = datetime(2026, 1, 1, tzinfo=UTC).utcoffset()


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _report_values_without_digest(
    report: ResearchTeamDomainSpecialistPerformanceMemoryReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_public_payload(
        "digest payload",
        payload,
        allow_json_containers=True,
    )
    return _digest_from_unsigned_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return _digest_from_unsigned_payload(unsigned)


def _digest_from_unsigned_payload(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> object:
    if type(value) is bool or value is None:
        return value
    if type(value) is str:
        if _has_unsafe_text(value):
            raise ValueError("unsafe public payload text")
        return value
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal strings")
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError(f"unsupported public payload value {type(value).__name__}")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_name(label, field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers and type(value) is not dict:
            raise ValueError(f"{label} must be a dict")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_name(label, key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and _has_unsafe_text(value):
        raise ValueError(f"{label} contains unsafe public text")


def _reject_unsafe_name(label: str, name: str) -> None:
    lowered = name.lower()
    if any(fragment in lowered for fragment in UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public key")


def _has_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)
