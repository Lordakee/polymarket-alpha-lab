"""Pure report-only risk tiering for caller-supplied information sources.

The module is deterministic and side-effect free. Callers provide typed source
quality observations; the report exposes only aggregate scores, tiers, and
reason codes suitable for public payloads.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchInformationSourceRiskTierConfig",
    "ResearchInformationSourceRiskTierReasonCodeCount",
    "ResearchInformationSourceRiskTierReport",
    "ResearchInformationSourceRiskTierRow",
    "ResearchInformationSourceRiskTierSource",
    "build_research_information_source_risk_tier_report",
    "research_information_source_risk_tier_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-information-source-risk-tier-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_PASS_SOURCE_SCORE = Decimal("0.750000")
DEFAULT_WATCH_SOURCE_SCORE = Decimal("0.500000")
DEFAULT_BLOCK_COMPONENT_FLOOR = Decimal("0.250000")
PUBLIC_FORBIDDEN_KEY_FRAGMENTS = (
    "url",
    "text",
    "ref",
    "dsn",
    "table",
    "token",
    "market",
    "candidate",
)
PUBLIC_FORBIDDEN_VALUE_FRAGMENTS = (
    "://",
    "url=",
    "dsn=",
    "token=",
    "market-",
    "candidate-",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchInformationSourceRiskTierConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_source_score: Decimal = DEFAULT_PASS_SOURCE_SCORE
    watch_source_score: Decimal = DEFAULT_WATCH_SOURCE_SCORE
    block_component_floor: Decimal = DEFAULT_BLOCK_COMPONENT_FLOOR
    reliability_weight: Decimal = Decimal("0.300000")
    independence_weight: Decimal = Decimal("0.200000")
    timeliness_weight: Decimal = Decimal("0.200000")
    verifiability_weight: Decimal = Decimal("0.200000")
    rebuttal_coverage_weight: Decimal = Decimal("0.100000")
    stale_age_seconds: Decimal = Decimal("86400")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationSourceRiskTierConfig:
            raise TypeError(
                "ResearchInformationSourceRiskTierConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationSourceRiskTierConfig:
            raise ValueError(
                "config must be exactly ResearchInformationSourceRiskTierConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_source_score",
            "watch_source_score",
            "block_component_floor",
            "reliability_weight",
            "independence_weight",
            "timeliness_weight",
            "verifiability_weight",
            "rebuttal_coverage_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_source_score <= self.watch_source_score:
            raise ValueError("pass_source_score must be greater than watch_source_score")
        if self.watch_source_score <= self.block_component_floor:
            raise ValueError(
                "watch_source_score must be greater than block_component_floor",
            )
        weight_sum = _quantize(
            self.reliability_weight
            + self.independence_weight
            + self.timeliness_weight
            + self.verifiability_weight
            + self.rebuttal_coverage_weight,
        )
        if weight_sum != ONE:
            raise ValueError("component weights must sum to 1")
        object.__setattr__(
            self,
            "stale_age_seconds",
            _require_positive_decimal("stale_age_seconds", self.stale_age_seconds),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchInformationSourceRiskTierSource:
    source_key: str
    reliability_score: Decimal
    independence_score: Decimal
    timeliness_score: Decimal
    verifiability_score: Decimal
    rebuttal_coverage_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationSourceRiskTierSource:
            raise TypeError(
                "ResearchInformationSourceRiskTierSource does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationSourceRiskTierSource:
            raise ValueError(
                "source must be exactly ResearchInformationSourceRiskTierSource",
            )
        _require_private_source_key("source_key", self.source_key)
        for field_name in _COMPONENT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("source", self)


@dataclass(frozen=True)
class ResearchInformationSourceRiskTierRow:
    source_sequence: Decimal
    reliability_score: Decimal
    independence_score: Decimal
    timeliness_score: Decimal
    verifiability_score: Decimal
    rebuttal_coverage_score: Decimal
    component_floor_score: Decimal
    source_score: Decimal
    source_risk_score: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationSourceRiskTierRow:
            raise TypeError(
                "ResearchInformationSourceRiskTierRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationSourceRiskTierRow:
            raise ValueError("row must be exactly ResearchInformationSourceRiskTierRow")
        object.__setattr__(
            self,
            "source_sequence",
            _require_positive_whole_decimal("source_sequence", self.source_sequence),
        )
        for field_name in (
            *_COMPONENT_FIELDS,
            "component_floor_score",
            "source_score",
            "source_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchInformationSourceRiskTierReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationSourceRiskTierReasonCodeCount:
            raise TypeError(
                "ResearchInformationSourceRiskTierReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationSourceRiskTierReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchInformationSourceRiskTierReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchInformationSourceRiskTierReport:
    generated_at: datetime
    config_version: str
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_source_score: Decimal | None
    average_source_risk_score: Decimal | None
    status: str
    rows: tuple[ResearchInformationSourceRiskTierRow, ...]
    reason_code_counts: tuple[ResearchInformationSourceRiskTierReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationSourceRiskTierReport:
            raise TypeError(
                "ResearchInformationSourceRiskTierReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationSourceRiskTierReport:
            raise ValueError(
                "report must be exactly ResearchInformationSourceRiskTierReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("source_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_source_score", "average_source_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
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
        _require_hard_flags("report", self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_information_source_risk_tier_report_payload(self)


_COMPONENT_FIELDS = (
    "reliability_score",
    "independence_score",
    "timeliness_score",
    "verifiability_score",
    "rebuttal_coverage_score",
)


def build_research_information_source_risk_tier_report(
    sources: Iterable[object],
    *,
    config: ResearchInformationSourceRiskTierConfig,
    generated_at: datetime,
) -> ResearchInformationSourceRiskTierReport:
    if type(config) is not ResearchInformationSourceRiskTierConfig:
        raise ValueError("config must be a ResearchInformationSourceRiskTierConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_items = _normalize_sources(sources)
    for source in source_items:
        _reject_future_observed_at(source, generated_at_utc)

    rows = tuple(
        _row_from_source(
            source_sequence=_decimal_count(index),
            source=source,
            config=config,
            generated_at=generated_at_utc,
        )
        for index, source in enumerate(sorted(source_items, key=lambda item: item.source_key), 1)
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchInformationSourceRiskTierReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_source_score=_average_source_score(rows),
        average_source_risk_score=_average_source_risk_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_information_source_risk_tier_report_payload(
    report: ResearchInformationSourceRiskTierReport,
) -> dict[str, Any]:
    if type(report) is not ResearchInformationSourceRiskTierReport:
        raise ValueError("report must be a ResearchInformationSourceRiskTierReport")
    _require_hard_flags("report", report)
    payload = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "source_count": _decimal_payload(report.source_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "average_source_score": _optional_decimal_payload(report.average_source_score),
        "average_source_risk_score": _optional_decimal_payload(
            report.average_source_risk_score,
        ),
        "status": report.status,
        "rows": [_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            {
                "reason_code": item.reason_code,
                "count": _decimal_payload(item.count),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            }
            for item in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_public_payload(
        "research_information_source_risk_tier_report_payload",
        payload,
    )
    return payload


def _row_from_source(
    *,
    source_sequence: Decimal,
    source: ResearchInformationSourceRiskTierSource,
    config: ResearchInformationSourceRiskTierConfig,
    generated_at: datetime,
) -> ResearchInformationSourceRiskTierRow:
    source_score = _source_score(source, config)
    source_risk_score = _quantize(ONE - source_score)
    component_floor_score = min(getattr(source, field_name) for field_name in _COMPONENT_FIELDS)
    source_age_seconds = _age_seconds(generated_at, source.observed_at)
    status = _source_status(
        source_score=source_score,
        component_floor_score=component_floor_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        source=source,
        source_score=source_score,
        component_floor_score=component_floor_score,
        source_age_seconds=source_age_seconds,
        status=status,
        config=config,
    )
    return ResearchInformationSourceRiskTierRow(
        source_sequence=source_sequence,
        reliability_score=source.reliability_score,
        independence_score=source.independence_score,
        timeliness_score=source.timeliness_score,
        verifiability_score=source.verifiability_score,
        rebuttal_coverage_score=source.rebuttal_coverage_score,
        component_floor_score=component_floor_score,
        source_score=source_score,
        source_risk_score=source_risk_score,
        observed_at=source.observed_at,
        source_age_seconds=source_age_seconds,
        status=status,
        reason_codes=reason_codes,
    )


def _source_score(
    source: ResearchInformationSourceRiskTierSource,
    config: ResearchInformationSourceRiskTierConfig,
) -> Decimal:
    return _quantize(
        (source.reliability_score * config.reliability_weight)
        + (source.independence_score * config.independence_weight)
        + (source.timeliness_score * config.timeliness_weight)
        + (source.verifiability_score * config.verifiability_weight)
        + (source.rebuttal_coverage_score * config.rebuttal_coverage_weight),
    )


def _source_status(
    *,
    source_score: Decimal,
    component_floor_score: Decimal,
    config: ResearchInformationSourceRiskTierConfig,
) -> str:
    if component_floor_score <= config.block_component_floor:
        return "block"
    if source_score < config.watch_source_score:
        return "block"
    if source_score < config.pass_source_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    source: ResearchInformationSourceRiskTierSource,
    source_score: Decimal,
    component_floor_score: Decimal,
    source_age_seconds: Decimal,
    status: str,
    config: ResearchInformationSourceRiskTierConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"information_source_risk_tier_{status}"}
    if source_score >= config.pass_source_score:
        reason_codes.add("strong_composite_source_score")
    elif source_score >= config.watch_source_score:
        reason_codes.add("watch_composite_source_score")
    else:
        reason_codes.add("weak_composite_source_score")
    if component_floor_score <= config.block_component_floor:
        reason_codes.add("critical_component_floor")
    if source_age_seconds >= config.stale_age_seconds:
        reason_codes.add("stale_source_observation")
    else:
        reason_codes.add("fresh_source_observation")
    for field_name in _COMPONENT_FIELDS:
        if getattr(source, field_name) < config.watch_source_score:
            reason_codes.add(f"weak_{field_name}")
    for reason_code in source.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _normalize_sources(
    sources: Iterable[object],
) -> tuple[ResearchInformationSourceRiskTierSource, ...]:
    if isinstance(sources, (str, bytes)):
        raise ValueError("sources must be an iterable")
    try:
        values = tuple(sources)
    except TypeError as exc:
        raise ValueError("sources must be an iterable") from exc
    return tuple(_coerce_source(value) for value in values)


def _coerce_source(value: object) -> ResearchInformationSourceRiskTierSource:
    if type(value) is ResearchInformationSourceRiskTierSource:
        _require_hard_flags("source", value)
        return value
    _require_hard_flags("source", value)
    return ResearchInformationSourceRiskTierSource(
        source_key=_field_value(value, "source_key"),
        reliability_score=_field_value(value, "reliability_score"),
        independence_score=_field_value(value, "independence_score"),
        timeliness_score=_field_value(value, "timeliness_score"),
        verifiability_score=_field_value(value, "verifiability_score"),
        rebuttal_coverage_score=_field_value(value, "rebuttal_coverage_score"),
        observed_at=_field_value(value, "observed_at"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchInformationSourceRiskTierRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_information_sources",)
    if any(row.status == "block" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if all(row.status == "pass" for row in rows):
        return ("information_source_risk_tier_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_information_sources",):
        return "block"
    if "information_source_risk_tier_block" in reason_codes:
        return "block"
    if "information_source_risk_tier_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchInformationSourceRiskTierRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchInformationSourceRiskTierReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchInformationSourceRiskTierReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchInformationSourceRiskTierReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_source_score(
    rows: tuple[ResearchInformationSourceRiskTierRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average_decimal(tuple(row.source_score for row in rows))


def _average_source_risk_score(
    rows: tuple[ResearchInformationSourceRiskTierRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average_decimal(tuple(row.source_risk_score for row in rows))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _reject_future_observed_at(
    source: ResearchInformationSourceRiskTierSource,
    generated_at: datetime,
) -> None:
    if source.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")


def _status_count(
    rows: tuple[ResearchInformationSourceRiskTierRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchInformationSourceRiskTierRow, ...],
) -> tuple[ResearchInformationSourceRiskTierRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchInformationSourceRiskTierRow:
            raise ValueError(
                "rows must contain ResearchInformationSourceRiskTierRow values",
            )
        _require_hard_flags("row", row)
    expected = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.source_sequence for row in rows) != expected:
        raise ValueError("rows must use consecutive source_sequence values")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchInformationSourceRiskTierReasonCodeCount, ...],
) -> tuple[ResearchInformationSourceRiskTierReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchInformationSourceRiskTierReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchInformationSourceRiskTierReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchInformationSourceRiskTierRow) -> None:
    if row.component_floor_score != min(
        getattr(row, field_name) for field_name in _COMPONENT_FIELDS
    ):
        raise ValueError("component_floor_score must match component scores")
    if row.source_risk_score != _quantize(ONE - row.source_score):
        raise ValueError("source_risk_score must match source_score")
    if row.status == "pass" and row.source_score < DEFAULT_PASS_SOURCE_SCORE:
        raise ValueError("source_score must support pass status")
    if row.status == "watch" and (
        row.source_score < DEFAULT_WATCH_SOURCE_SCORE
        or row.source_score >= DEFAULT_PASS_SOURCE_SCORE
    ):
        raise ValueError("source_score must support watch status")
    if row.status == "block" and (
        row.source_score >= DEFAULT_WATCH_SOURCE_SCORE
        and row.component_floor_score > DEFAULT_BLOCK_COMPONENT_FLOOR
    ):
        raise ValueError("source_score must support block status")


def _validate_report_consistency(
    report: ResearchInformationSourceRiskTierReport,
) -> None:
    if report.source_count != _decimal_count(len(report.rows)):
        raise ValueError("source_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_source_score != _average_source_score(report.rows):
        raise ValueError("average_source_score must match rows")
    if report.average_source_risk_score != _average_source_risk_score(report.rows):
        raise ValueError("average_source_risk_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _row_payload(row: ResearchInformationSourceRiskTierRow) -> dict[str, Any]:
    _require_hard_flags("row", row)
    return {
        "source_sequence": _decimal_payload(row.source_sequence),
        "reliability_score": _decimal_payload(row.reliability_score),
        "independence_score": _decimal_payload(row.independence_score),
        "timeliness_score": _decimal_payload(row.timeliness_score),
        "verifiability_score": _decimal_payload(row.verifiability_score),
        "rebuttal_coverage_score": _decimal_payload(row.rebuttal_coverage_score),
        "component_floor_score": _decimal_payload(row.component_floor_score),
        "source_score": _decimal_payload(row.source_score),
        "source_risk_score": _decimal_payload(row.source_risk_score),
        "observed_at": row.observed_at.isoformat(),
        "source_age_seconds": _decimal_payload(row.source_age_seconds),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


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


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return str(_require_decimal("payload decimal", value))


def _optional_decimal_payload(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_payload(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_private_source_key(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in PUBLIC_FORBIDDEN_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe private identifiers")


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


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")
    lowered = value.lower()
    if any(fragment in lowered for fragment in PUBLIC_FORBIDDEN_KEY_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe public terms")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public payload keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in PUBLIC_FORBIDDEN_KEY_FRAGMENTS):
                raise ValueError(f"{label} public payload contains unsafe key")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        lowered_value = value.lower()
        if any(
            fragment in lowered_value for fragment in PUBLIC_FORBIDDEN_VALUE_FRAGMENTS
        ):
            raise ValueError(f"{label} public payload contains unsafe value")
