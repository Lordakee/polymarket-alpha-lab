"""Pure report-only source-class reliability memory summary."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "ResearchSourceReliabilityMemoryConfig",
    "ResearchSourceReliabilityMemoryObservation",
    "ResearchSourceReliabilityMemoryReasonCodeCount",
    "ResearchSourceReliabilityMemoryReport",
    "ResearchSourceReliabilityMemoryRow",
    "STATUSES",
    "build_research_source_reliability_memory_report",
    "research_source_reliability_memory_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-source-reliability-memory-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
RATIO_QUANTUM = Decimal("0.000001")
NO_MEMORY_REASON_CODE = "no_reliability_memory"
PASS_REASON_CODE = "source_reliability_memory_pass"
WATCH_REASON_CODE = "source_reliability_memory_watch"
BLOCK_REASON_CODE = "source_reliability_memory_block"
SAFE_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")
SAFE_REASON_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_KEY_FRAGMENTS = (
    "source_name",
    "source_url",
    "source_ref",
    "source_text",
    "raw_source",
    "url",
)
UNSAFE_TEXT_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "source_url",
    "source_ref",
    "source_text",
    "source-name",
    "source-text",
    "raw-source",
    "raw_source",
    "wallet",
    "auth",
    "order",
    "trade",
    "live",
    "execution",
    "execute",
)


@dataclass(frozen=True)
class ResearchSourceReliabilityMemoryConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_memory_points: Decimal = Decimal("3")
    pass_reliability_floor: Decimal = Decimal("0.700000")
    block_reliability_floor: Decimal = Decimal("0.500000")
    stale_age_watch_seconds: Decimal = Decimal("86400")
    stale_age_block_seconds: Decimal = Decimal("604800")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceReliabilityMemoryConfig:
            raise TypeError(
                "ResearchSourceReliabilityMemoryConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceReliabilityMemoryConfig:
            raise ValueError(
                "config must be exactly ResearchSourceReliabilityMemoryConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_memory_points",
            _require_positive_whole_decimal(
                "min_memory_points",
                self.min_memory_points,
            ),
        )
        for field_name in ("pass_reliability_floor", "block_reliability_floor"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_age_watch_seconds", "stale_age_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_reliability_floor >= self.pass_reliability_floor:
            raise ValueError(
                "block_reliability_floor must be less than pass_reliability_floor",
            )
        if self.stale_age_watch_seconds >= self.stale_age_block_seconds:
            raise ValueError(
                "stale_age_watch_seconds must be less than stale_age_block_seconds",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceReliabilityMemoryObservation:
    source_class: str
    research_domain: str
    observed_at: datetime
    reliability_score: Decimal
    corroboration_success_rate: Decimal
    correction_rate: Decimal
    evidence_count: Decimal
    stale_age_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceReliabilityMemoryObservation:
            raise TypeError(
                "ResearchSourceReliabilityMemoryObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceReliabilityMemoryObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchSourceReliabilityMemoryObservation",
            )
        _require_public_identifier("source_class", self.source_class)
        _require_public_identifier("research_domain", self.research_domain)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "reliability_score",
            "corroboration_success_rate",
            "correction_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_count",
            _require_positive_whole_decimal("evidence_count", self.evidence_count),
        )
        object.__setattr__(
            self,
            "stale_age_seconds",
            _require_nonnegative_decimal("stale_age_seconds", self.stale_age_seconds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceReliabilityMemoryRow:
    source_class: str
    research_domain: str
    memory_point_count: Decimal
    first_observed_at: datetime
    latest_observed_at: datetime
    long_term_reliability_score: Decimal
    latest_reliability_score: Decimal
    corroboration_success_rate: Decimal
    correction_rate: Decimal
    evidence_count: Decimal
    latest_stale_age_seconds: Decimal
    evidence_weight: Decimal
    research_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    explanations: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceReliabilityMemoryRow:
            raise TypeError(
                "ResearchSourceReliabilityMemoryRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceReliabilityMemoryRow:
            raise ValueError("row must be exactly ResearchSourceReliabilityMemoryRow")
        _require_public_identifier("source_class", self.source_class)
        _require_public_identifier("research_domain", self.research_domain)
        object.__setattr__(
            self,
            "memory_point_count",
            _require_positive_whole_decimal(
                "memory_point_count",
                self.memory_point_count,
            ),
        )
        object.__setattr__(
            self,
            "first_observed_at",
            _as_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "long_term_reliability_score",
            "latest_reliability_score",
            "corroboration_success_rate",
            "correction_rate",
            "evidence_weight",
            "research_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_count",
            _require_positive_whole_decimal("evidence_count", self.evidence_count),
        )
        object.__setattr__(
            self,
            "latest_stale_age_seconds",
            _require_nonnegative_decimal(
                "latest_stale_age_seconds",
                self.latest_stale_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "explanations",
            _normalize_public_text_tuple("explanations", self.explanations),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceReliabilityMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceReliabilityMemoryReasonCodeCount:
            raise TypeError(
                "ResearchSourceReliabilityMemoryReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceReliabilityMemoryReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchSourceReliabilityMemoryReasonCodeCount",
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
class ResearchSourceReliabilityMemoryReport:
    generated_at: datetime
    config_version: str
    source_group_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_evidence_weight: Decimal | None
    average_research_priority_score: Decimal | None
    max_latest_stale_age_seconds: Decimal | None
    status: str
    rows: tuple[ResearchSourceReliabilityMemoryRow, ...]
    reason_code_counts: tuple[ResearchSourceReliabilityMemoryReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    explanations: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceReliabilityMemoryReport:
            raise TypeError(
                "ResearchSourceReliabilityMemoryReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceReliabilityMemoryReport:
            raise ValueError(
                "report must be exactly ResearchSourceReliabilityMemoryReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_group_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_evidence_weight",
            "average_research_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_latest_stale_age_seconds",
            _require_optional_nonnegative_decimal(
                "max_latest_stale_age_seconds",
                self.max_latest_stale_age_seconds,
            ),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "explanations",
            _normalize_public_text_tuple("explanations", self.explanations),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_source_reliability_memory_report(
    observations: Iterable[object],
    *,
    config: ResearchSourceReliabilityMemoryConfig,
    generated_at: datetime,
) -> ResearchSourceReliabilityMemoryReport:
    if type(config) is not ResearchSourceReliabilityMemoryConfig:
        raise ValueError("config must be a ResearchSourceReliabilityMemoryConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    memory_items = _normalize_observations(observations)
    for item in memory_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[tuple[str, str], list[ResearchSourceReliabilityMemoryObservation]] = {}
    for item in memory_items:
        grouped.setdefault((item.source_class, item.research_domain), []).append(item)

    rows = tuple(
        sorted(
            (
                _memory_row_from_observations(
                    source_class=source_class,
                    research_domain=research_domain,
                    observations=tuple(grouped[(source_class, research_domain)]),
                    config=config,
                )
                for source_class, research_domain in sorted(grouped)
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "source_group_count": _decimal_count(len(rows)),
        "observation_count": sum((row.memory_point_count for row in rows), ZERO),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_evidence_weight": _average_row_decimal(rows, "evidence_weight"),
        "average_research_priority_score": _average_row_decimal(
            rows,
            "research_priority_score",
        ),
        "max_latest_stale_age_seconds": _max_latest_stale_age_seconds(rows),
        "status": _summary_status(rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "explanations": _summary_explanations(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceReliabilityMemoryReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_reliability_memory_report_payload(
    report: ResearchSourceReliabilityMemoryReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceReliabilityMemoryReport:
        raise ValueError("report must be a ResearchSourceReliabilityMemoryReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    return payload


def _memory_row_from_observations(
    *,
    source_class: str,
    research_domain: str,
    observations: tuple[ResearchSourceReliabilityMemoryObservation, ...],
    config: ResearchSourceReliabilityMemoryConfig,
) -> ResearchSourceReliabilityMemoryRow:
    sorted_items = tuple(
        sorted(
            observations,
            key=lambda item: (
                item.observed_at,
                item.reliability_score,
                item.corroboration_success_rate,
                item.correction_rate,
                item.evidence_count,
                item.stale_age_seconds,
            ),
        ),
    )
    latest = sorted_items[-1]
    long_term_reliability = _average_decimal(
        tuple(item.reliability_score for item in sorted_items),
    )
    corroboration_success = _average_decimal(
        tuple(item.corroboration_success_rate for item in sorted_items),
    )
    correction_rate = _average_decimal(tuple(item.correction_rate for item in sorted_items))
    evidence_weight = _clamp_probability(
        ((long_term_reliability + corroboration_success) / TWO) - (correction_rate / TWO),
    )
    research_priority_score = _clamp_probability(ONE - evidence_weight)
    status = _row_status(
        memory_point_count=_decimal_count(len(sorted_items)),
        long_term_reliability_score=long_term_reliability,
        latest_stale_age_seconds=latest.stale_age_seconds,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        memory_point_count=_decimal_count(len(sorted_items)),
        long_term_reliability_score=long_term_reliability,
        latest_stale_age_seconds=latest.stale_age_seconds,
        input_reason_codes=tuple(
            reason_code for item in sorted_items for reason_code in item.reason_codes
        ),
        config=config,
    )
    return ResearchSourceReliabilityMemoryRow(
        source_class=source_class,
        research_domain=research_domain,
        memory_point_count=_decimal_count(len(sorted_items)),
        first_observed_at=sorted_items[0].observed_at,
        latest_observed_at=latest.observed_at,
        long_term_reliability_score=long_term_reliability,
        latest_reliability_score=latest.reliability_score,
        corroboration_success_rate=corroboration_success,
        correction_rate=correction_rate,
        evidence_count=sum((item.evidence_count for item in sorted_items), ZERO),
        latest_stale_age_seconds=latest.stale_age_seconds,
        evidence_weight=evidence_weight,
        research_priority_score=research_priority_score,
        status=status,
        reason_codes=reason_codes,
        explanations=_row_explanations(reason_codes),
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchSourceReliabilityMemoryObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized: list[ResearchSourceReliabilityMemoryObservation] = []
    for value in values:
        if type(value) is not ResearchSourceReliabilityMemoryObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceReliabilityMemoryObservation items",
            )
        normalized.append(value)
    return tuple(normalized)


def _row_status(
    *,
    memory_point_count: Decimal,
    long_term_reliability_score: Decimal,
    latest_stale_age_seconds: Decimal,
    config: ResearchSourceReliabilityMemoryConfig,
) -> str:
    if (
        memory_point_count < config.min_memory_points
        or long_term_reliability_score < config.block_reliability_floor
        or latest_stale_age_seconds >= config.stale_age_block_seconds
    ):
        return "block"
    if (
        long_term_reliability_score < config.pass_reliability_floor
        or latest_stale_age_seconds >= config.stale_age_watch_seconds
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    memory_point_count: Decimal,
    long_term_reliability_score: Decimal,
    latest_stale_age_seconds: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchSourceReliabilityMemoryConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if memory_point_count < config.min_memory_points:
        codes.append("insufficient_reliability_memory")
    if long_term_reliability_score < config.block_reliability_floor:
        codes.append("weak_long_term_reliability_block")
    elif long_term_reliability_score < config.pass_reliability_floor:
        codes.append("weak_long_term_reliability_watch")
    if latest_stale_age_seconds >= config.stale_age_block_seconds:
        codes.append("stale_source_memory_block")
    elif latest_stale_age_seconds >= config.stale_age_watch_seconds:
        codes.append("stale_source_memory_watch")
    codes.extend(f"input_{reason_code}" for reason_code in input_reason_codes)
    if status == "pass":
        codes.append(PASS_REASON_CODE)
    elif status == "watch":
        codes.append(WATCH_REASON_CODE)
    else:
        codes.append(BLOCK_REASON_CODE)
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _row_explanations(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if PASS_REASON_CODE in reason_codes:
        return ("Reliability memory supports normal evidence weighting.",)
    explanations: list[str] = []
    if "insufficient_reliability_memory" in reason_codes:
        explanations.append("Reliability memory is below the configured minimum.")
    if (
        "weak_long_term_reliability_block" in reason_codes
        or "weak_long_term_reliability_watch" in reason_codes
    ):
        explanations.append("Long-term reliability is below the configured floor.")
    if (
        "stale_source_memory_block" in reason_codes
        or "stale_source_memory_watch" in reason_codes
    ):
        explanations.append("Latest source-class memory is stale.")
    if not explanations:
        explanations.append("Reliability memory requires review.")
    return tuple(explanations)


def _summary_reason_codes(
    rows: tuple[ResearchSourceReliabilityMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_MEMORY_REASON_CODE,)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchSourceReliabilityMemoryRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_explanations(
    rows: tuple[ResearchSourceReliabilityMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("No reliability memory was supplied.",)
    status = _summary_status(rows)
    if status == "block":
        return ("At least one source class and domain is in block status.",)
    if status == "watch":
        return ("At least one source class and domain needs review.",)
    return ("All source classes and domains support current evidence weighting.",)


def _reason_code_counts(
    rows: tuple[ResearchSourceReliabilityMemoryRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceReliabilityMemoryReasonCodeCount, ...]:
    if not rows:
        counter = Counter({NO_MEMORY_REASON_CODE: 1})
    else:
        counter = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchSourceReliabilityMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_count(
    rows: tuple[ResearchSourceReliabilityMemoryRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_row_decimal(
    rows: tuple[ResearchSourceReliabilityMemoryRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    return _average_decimal(tuple(getattr(row, field_name) for row in rows))


def _max_latest_stale_age_seconds(
    rows: tuple[ResearchSourceReliabilityMemoryRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.latest_stale_age_seconds for row in rows)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / _decimal_count(len(values)))


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        value = ZERO
    if value > ONE:
        value = ONE
    return _quantize(value)


def _row_sort_key(row: ResearchSourceReliabilityMemoryRow) -> tuple[Decimal, str, str]:
    return (-row.research_priority_score, row.source_class, row.research_domain)


def _validate_row_consistency(row: ResearchSourceReliabilityMemoryRow) -> None:
    if row.latest_observed_at < row.first_observed_at:
        raise ValueError("latest_observed_at must be after first_observed_at")
    expected_priority = _clamp_probability(ONE - row.evidence_weight)
    if row.research_priority_score != expected_priority:
        raise ValueError("research_priority_score must match evidence_weight")
    expected_weight = _clamp_probability(
        ((row.long_term_reliability_score + row.corroboration_success_rate) / TWO)
        - (row.correction_rate / TWO),
    )
    if row.evidence_weight != expected_weight:
        raise ValueError("evidence_weight must match source reliability memory")
    if row.status == "pass" and PASS_REASON_CODE not in row.reason_codes:
        raise ValueError("pass rows must include pass reason code")
    if row.status == "watch" and WATCH_REASON_CODE not in row.reason_codes:
        raise ValueError("watch rows must include watch reason code")
    if row.status == "block" and BLOCK_REASON_CODE not in row.reason_codes:
        raise ValueError("block rows must include block reason code")


def _validate_report_consistency(report: ResearchSourceReliabilityMemoryReport) -> None:
    if report.source_group_count != _decimal_count(len(report.rows)):
        raise ValueError("source_group_count must match rows")
    if report.observation_count != sum(
        (row.memory_point_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_evidence_weight != _average_row_decimal(
        report.rows,
        "evidence_weight",
    ):
        raise ValueError("average_evidence_weight must match rows")
    if report.average_research_priority_score != _average_row_decimal(
        report.rows,
        "research_priority_score",
    ):
        raise ValueError("average_research_priority_score must match rows")
    if report.max_latest_stale_age_seconds != _max_latest_stale_age_seconds(report.rows):
        raise ValueError("max_latest_stale_age_seconds must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    expected_reason_codes = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.explanations != _summary_explanations(report.rows):
        raise ValueError("explanations must match rows")


def _normalize_rows(values: object) -> tuple[ResearchSourceReliabilityMemoryRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchSourceReliabilityMemoryRow] = []
    for value in values:
        if type(value) is not ResearchSourceReliabilityMemoryRow:
            raise ValueError("rows must contain ResearchSourceReliabilityMemoryRow items")
        normalized.append(value)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchSourceReliabilityMemoryReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchSourceReliabilityMemoryReasonCodeCount] = []
    for value in values:
        if type(value) is not ResearchSourceReliabilityMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceReliabilityMemoryReasonCodeCount items",
            )
        normalized.append(value)
    return tuple(normalized)


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


def _normalize_public_text_tuple(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_public_text(field_name, value))
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public identifier")
    _reject_unsafe_text(field_name, value)
    if any(character not in SAFE_IDENTIFIER_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain public reason codes")
    if any(character not in SAFE_REASON_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} must contain public reason codes")
    _reject_unsafe_text(field_name, value)


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain public text")
    _reject_unsafe_text(field_name, value)
    return value


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
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        field_value = getattr(value, field_name, None)
        if type(field_value) is not bool or field_value is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {_payload_value(key): _payload_value(item) for key, item in value.items()}
    return value


def _report_values_without_digest(
    report: ResearchSourceReliabilityMemoryReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _payload_value(dict(values))
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_key(label, field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
                allow_json_containers=True,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain mappings")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_key(label, key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (tuple, list)):
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain containers")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, str):
        _reject_unsafe_text(label, value)


def _reject_unsafe_key(label: str, key: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload key")


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload text")
