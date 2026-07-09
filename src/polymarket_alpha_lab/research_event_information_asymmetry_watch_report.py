"""Pure report-only event-category information asymmetry watch reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_WATCH_CONFIG_VERSION = (
    "research-event-information-asymmetry-watch-report-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RISK_COMPONENT_COUNT = Decimal("4")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

EMPTY_REASON = "information_asymmetry_empty_input"
PASS_REASON = "information_asymmetry_pass"
WATCH_REASON = "information_asymmetry_watch"
BLOCK_REASON = "information_asymmetry_block"
SOURCE_COVERAGE_WATCH_REASON = "source_coverage_gap_watch"
SOURCE_COVERAGE_BLOCK_REASON = "source_coverage_gap_block"
UPDATE_LATENCY_WATCH_REASON = "update_latency_watch"
UPDATE_LATENCY_BLOCK_REASON = "update_latency_block"
CONTRADICTION_WATCH_REASON = "contradiction_rate_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_rate_block"
SPECIALIST_CONFIDENCE_WATCH_REASON = "specialist_confidence_gap_watch"
SPECIALIST_CONFIDENCE_BLOCK_REASON = "specialist_confidence_gap_block"

REASON_CODE_PRIORITY = (
    EMPTY_REASON,
    SOURCE_COVERAGE_BLOCK_REASON,
    UPDATE_LATENCY_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    SPECIALIST_CONFIDENCE_BLOCK_REASON,
    BLOCK_REASON,
    SOURCE_COVERAGE_WATCH_REASON,
    UPDATE_LATENCY_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    SPECIALIST_CONFIDENCE_WATCH_REASON,
    WATCH_REASON,
    PASS_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)
BLOCK_REASONS = frozenset(
    (
        EMPTY_REASON,
        SOURCE_COVERAGE_BLOCK_REASON,
        UPDATE_LATENCY_BLOCK_REASON,
        CONTRADICTION_BLOCK_REASON,
        SPECIALIST_CONFIDENCE_BLOCK_REASON,
        BLOCK_REASON,
    ),
)
WATCH_REASONS = frozenset(
    (
        SOURCE_COVERAGE_WATCH_REASON,
        UPDATE_LATENCY_WATCH_REASON,
        CONTRADICTION_WATCH_REASON,
        SPECIALIST_CONFIDENCE_WATCH_REASON,
        WATCH_REASON,
    ),
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "candidate_reference",
    "raw_candidate",
    "raw_id",
    "market_id",
    "market_slug",
    "market_question",
    "question_text",
    "source_url",
    "source_text",
    "source_reference",
    "http://",
    "https://",
    "://",
    "dsn",
    "table",
    "token",
    "private_key",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "sizing",
    "recommend",
    "advice",
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_WATCH_CONFIG_VERSION",
    "STATUSES",
    "ResearchEventInformationAsymmetryWatchConfig",
    "ResearchEventInformationAsymmetryWatchObservation",
    "ResearchEventInformationAsymmetryWatchRow",
    "ResearchEventInformationAsymmetryWatchReasonCodeCount",
    "ResearchEventInformationAsymmetryWatchReport",
    "build_research_event_information_asymmetry_watch_report",
    "research_event_information_asymmetry_watch_report_payload",
    "research_event_information_asymmetry_watch_report_digest",
    "validate_research_event_information_asymmetry_watch_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__bases__ != (_FinalPublicDataclass,):
            raise TypeError("public dataclasses do not support subclassing")
        if not cls.__name__.startswith("ResearchEventInformationAsymmetryWatch"):
            raise TypeError("public dataclasses do not support subclassing")


@dataclass(frozen=True)
class ResearchEventInformationAsymmetryWatchConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_WATCH_CONFIG_VERSION
    )
    max_pass_source_coverage_gap: Decimal = Decimal("0.250000")
    max_watch_source_coverage_gap: Decimal = Decimal("0.500000")
    max_pass_update_latency_hours: Decimal = Decimal("4.000000")
    max_watch_update_latency_hours: Decimal = Decimal("24.000000")
    risk_full_update_latency_hours: Decimal = Decimal("24.000000")
    max_pass_contradiction_rate: Decimal = Decimal("0.200000")
    max_watch_contradiction_rate: Decimal = Decimal("0.500000")
    max_pass_specialist_confidence_gap: Decimal = Decimal("0.200000")
    max_watch_specialist_confidence_gap: Decimal = Decimal("0.600000")
    watch_information_asymmetry_risk_score: Decimal = Decimal("0.300000")
    block_information_asymmetry_risk_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventInformationAsymmetryWatchConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_WATCH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "max_pass_source_coverage_gap",
            "max_watch_source_coverage_gap",
            "max_pass_contradiction_rate",
            "max_watch_contradiction_rate",
            "max_pass_specialist_confidence_gap",
            "max_watch_specialist_confidence_gap",
            "watch_information_asymmetry_risk_score",
            "block_information_asymmetry_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_update_latency_hours",
            "max_watch_update_latency_hours",
            "risk_full_update_latency_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventInformationAsymmetryWatchObservation(_FinalPublicDataclass):
    event_category: str
    source_coverage_ratio: Decimal
    update_latency_hours: Decimal
    contradiction_rate: Decimal
    specialist_confidence_score: Decimal
    analysis_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventInformationAsymmetryWatchObservation,
            "observation",
        )
        for field_name in ("event_category", "analysis_version"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_coverage_ratio",
            "contradiction_rate",
            "specialist_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "update_latency_hours",
            _require_nonnegative_decimal(
                "update_latency_hours",
                self.update_latency_hours,
            ),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventInformationAsymmetryWatchRow(_FinalPublicDataclass):
    rank: Decimal
    event_category: str
    source_coverage_ratio: Decimal
    source_coverage_gap: Decimal
    update_latency_hours: Decimal
    update_latency_pressure: Decimal
    contradiction_rate: Decimal
    specialist_confidence_score: Decimal
    specialist_confidence_gap: Decimal
    information_asymmetry_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    analysis_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventInformationAsymmetryWatchRow, "row")
        object.__setattr__(self, "rank", _require_positive_count("rank", self.rank))
        for field_name in ("event_category", "analysis_version"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "update_latency_hours",
            _require_nonnegative_decimal(
                "update_latency_hours",
                self.update_latency_hours,
            ),
        )
        for field_name in (
            "source_coverage_ratio",
            "source_coverage_gap",
            "update_latency_pressure",
            "contradiction_rate",
            "specialist_confidence_score",
            "specialist_confidence_gap",
            "information_asymmetry_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventInformationAsymmetryWatchReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventInformationAsymmetryWatchReasonCodeCount,
            "reason_code_count",
        )
        if self.reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
        object.__setattr__(self, "count", _require_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventInformationAsymmetryWatchReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_source_coverage_gap: Decimal | None
    max_update_latency_hours: Decimal | None
    max_contradiction_rate: Decimal | None
    min_specialist_confidence_score: Decimal | None
    average_information_asymmetry_risk_score: Decimal | None
    status: str
    rows: tuple[ResearchEventInformationAsymmetryWatchRow, ...]
    reason_code_counts: tuple[
        ResearchEventInformationAsymmetryWatchReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventInformationAsymmetryWatchReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_INFORMATION_ASYMMETRY_WATCH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "category_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_source_coverage_gap",
            "max_contradiction_rate",
            "min_specialist_confidence_score",
            "average_information_asymmetry_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_update_latency_hours",
            _require_optional_nonnegative_decimal(
                "max_update_latency_hours",
                self.max_update_latency_hours,
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
            _require_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _set_or_validate_derived_validation_digest(self)
        _reject_unsafe_public_payload("report", _payload_value(self))

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_information_asymmetry_watch_report_payload(self)


def build_research_event_information_asymmetry_watch_report(
    observations: Iterable[ResearchEventInformationAsymmetryWatchObservation],
    *,
    generated_at: datetime,
    config: ResearchEventInformationAsymmetryWatchConfig,
) -> ResearchEventInformationAsymmetryWatchReport:
    """Build a deterministic local report-only information asymmetry snapshot."""

    if type(config) is not ResearchEventInformationAsymmetryWatchConfig:
        raise ValueError("config must be a ResearchEventInformationAsymmetryWatchConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    ranks = {
        item.event_category: _count(index)
        for index, item in enumerate(normalized_observations, start=1)
    }
    rows = tuple(
        sorted(
            (
                _row_for_observation(
                    item,
                    rank=ranks[item.event_category],
                    config=config,
                )
                for item in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchEventInformationAsymmetryWatchReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        category_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, STATUS_PASS)),
        watch_count=_count(_status_count(rows, STATUS_WATCH)),
        block_count=_count(_status_count(rows, STATUS_BLOCK)),
        max_source_coverage_gap=_max_decimal(
            row.source_coverage_gap for row in rows
        ),
        max_update_latency_hours=_max_decimal(
            row.update_latency_hours for row in rows
        ),
        max_contradiction_rate=_max_decimal(row.contradiction_rate for row in rows),
        min_specialist_confidence_score=_min_decimal(
            row.specialist_confidence_score for row in rows
        ),
        average_information_asymmetry_risk_score=_average_decimal(
            row.information_asymmetry_risk_score for row in rows
        ),
        status=_status_from_reason_codes(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_event_information_asymmetry_watch_report_payload(
    value: ResearchEventInformationAsymmetryWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchEventInformationAsymmetryWatchReport:
        _validate_report(value)
        _validate_derived_validation_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchEventInformationAsymmetryWatchReport or dict",
        )
    validate_research_event_information_asymmetry_watch_report_payload(payload)
    return dict(payload)


def validate_research_event_information_asymmetry_watch_report_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numeric_scalars(payload)
    _validate_payload_derived_validation_digest(payload)


def research_event_information_asymmetry_watch_report_digest(
    value: ResearchEventInformationAsymmetryWatchReport | dict[str, Any],
) -> str:
    payload = research_event_information_asymmetry_watch_report_payload(value)
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    return digest


def _row_for_observation(
    item: ResearchEventInformationAsymmetryWatchObservation,
    *,
    rank: Decimal,
    config: ResearchEventInformationAsymmetryWatchConfig,
) -> ResearchEventInformationAsymmetryWatchRow:
    source_coverage_gap = _source_coverage_gap(item.source_coverage_ratio)
    update_latency_pressure = _update_latency_pressure(
        item.update_latency_hours,
        config,
    )
    specialist_confidence_gap = _specialist_confidence_gap(
        item.specialist_confidence_score,
    )
    risk_score = _information_asymmetry_risk_score(
        source_coverage_gap=source_coverage_gap,
        update_latency_pressure=update_latency_pressure,
        contradiction_rate=item.contradiction_rate,
        specialist_confidence_gap=specialist_confidence_gap,
    )
    reason_codes = _row_reason_codes(
        source_coverage_gap=source_coverage_gap,
        update_latency_hours=item.update_latency_hours,
        contradiction_rate=item.contradiction_rate,
        specialist_confidence_gap=specialist_confidence_gap,
        information_asymmetry_risk_score=risk_score,
        config=config,
    )
    return ResearchEventInformationAsymmetryWatchRow(
        rank=rank,
        event_category=item.event_category,
        source_coverage_ratio=item.source_coverage_ratio,
        source_coverage_gap=source_coverage_gap,
        update_latency_hours=item.update_latency_hours,
        update_latency_pressure=update_latency_pressure,
        contradiction_rate=item.contradiction_rate,
        specialist_confidence_score=item.specialist_confidence_score,
        specialist_confidence_gap=specialist_confidence_gap,
        information_asymmetry_risk_score=risk_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        analysis_version=item.analysis_version,
    )


def _row_reason_codes(
    *,
    source_coverage_gap: Decimal,
    update_latency_hours: Decimal,
    contradiction_rate: Decimal,
    specialist_confidence_gap: Decimal,
    information_asymmetry_risk_score: Decimal,
    config: ResearchEventInformationAsymmetryWatchConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source_coverage_gap > config.max_watch_source_coverage_gap:
        reasons.append(SOURCE_COVERAGE_BLOCK_REASON)
    elif source_coverage_gap > config.max_pass_source_coverage_gap:
        reasons.append(SOURCE_COVERAGE_WATCH_REASON)

    if update_latency_hours > config.max_watch_update_latency_hours:
        reasons.append(UPDATE_LATENCY_BLOCK_REASON)
    elif update_latency_hours > config.max_pass_update_latency_hours:
        reasons.append(UPDATE_LATENCY_WATCH_REASON)

    if contradiction_rate > config.max_watch_contradiction_rate:
        reasons.append(CONTRADICTION_BLOCK_REASON)
    elif contradiction_rate > config.max_pass_contradiction_rate:
        reasons.append(CONTRADICTION_WATCH_REASON)

    if specialist_confidence_gap > config.max_watch_specialist_confidence_gap:
        reasons.append(SPECIALIST_CONFIDENCE_BLOCK_REASON)
    elif specialist_confidence_gap > config.max_pass_specialist_confidence_gap:
        reasons.append(SPECIALIST_CONFIDENCE_WATCH_REASON)

    if (
        any(reason in BLOCK_REASONS for reason in reasons)
        or information_asymmetry_risk_score
        >= config.block_information_asymmetry_risk_score
    ):
        reasons.append(BLOCK_REASON)
    elif (
        any(reason in WATCH_REASONS for reason in reasons)
        or information_asymmetry_risk_score
        >= config.watch_information_asymmetry_risk_score
    ):
        reasons.append(WATCH_REASON)
    else:
        reasons.append(PASS_REASON)
    return _require_reason_codes("reason_codes", reasons)


def _report_reason_codes(
    rows: tuple[ResearchEventInformationAsymmetryWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    if all(row.status == STATUS_PASS for row in rows):
        return (PASS_REASON,)
    return _require_reason_codes(
        "reason_codes",
        tuple(
            reason
            for row in rows
            for reason in row.reason_codes
            if reason != PASS_REASON
        ),
    )


def _reason_code_counts(
    rows: tuple[ResearchEventInformationAsymmetryWatchRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventInformationAsymmetryWatchReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventInformationAsymmetryWatchReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEventInformationAsymmetryWatchReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODE_PRIORITY.index(item[0]),
        )
    )


def _normalize_observations(
    value: Iterable[ResearchEventInformationAsymmetryWatchObservation],
) -> tuple[ResearchEventInformationAsymmetryWatchObservation, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(value)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen: set[str] = set()
    for item in observations:
        if type(item) is not ResearchEventInformationAsymmetryWatchObservation:
            raise ValueError(
                "observations must contain "
                "ResearchEventInformationAsymmetryWatchObservation values",
            )
        _require_hard_flags("observation", item)
        if item.event_category in seen:
            raise ValueError("event_category values must be unique")
        seen.add(item.event_category)
    return tuple(sorted(observations, key=lambda item: item.event_category))


def _normalize_rows(
    value: Iterable[ResearchEventInformationAsymmetryWatchRow],
) -> tuple[ResearchEventInformationAsymmetryWatchRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchEventInformationAsymmetryWatchRow:
            raise ValueError(
                "rows must contain ResearchEventInformationAsymmetryWatchRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status, risk, and rank")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchEventInformationAsymmetryWatchReasonCodeCount],
) -> tuple[ResearchEventInformationAsymmetryWatchReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in counts:
        if type(count) is not ResearchEventInformationAsymmetryWatchReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventInformationAsymmetryWatchReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    expected = tuple(
        sorted(counts, key=lambda row: REASON_CODE_PRIORITY.index(row.reason_code)),
    )
    if counts != expected:
        raise ValueError("reason_code_counts must be sorted by reason_code priority")
    return counts


def _validate_config(config: ResearchEventInformationAsymmetryWatchConfig) -> None:
    if config.max_pass_source_coverage_gap >= config.max_watch_source_coverage_gap:
        raise ValueError(
            "max_pass_source_coverage_gap must be less than "
            "max_watch_source_coverage_gap",
        )
    if config.max_pass_update_latency_hours >= config.max_watch_update_latency_hours:
        raise ValueError(
            "max_pass_update_latency_hours must be less than "
            "max_watch_update_latency_hours",
        )
    if config.max_watch_update_latency_hours > config.risk_full_update_latency_hours:
        raise ValueError(
            "max_watch_update_latency_hours must not exceed "
            "risk_full_update_latency_hours",
        )
    if config.max_pass_contradiction_rate >= config.max_watch_contradiction_rate:
        raise ValueError(
            "max_pass_contradiction_rate must be less than "
            "max_watch_contradiction_rate",
        )
    if (
        config.max_pass_specialist_confidence_gap
        >= config.max_watch_specialist_confidence_gap
    ):
        raise ValueError(
            "max_pass_specialist_confidence_gap must be less than "
            "max_watch_specialist_confidence_gap",
        )
    if (
        config.watch_information_asymmetry_risk_score
        >= config.block_information_asymmetry_risk_score
    ):
        raise ValueError(
            "watch_information_asymmetry_risk_score must be less than "
            "block_information_asymmetry_risk_score",
        )


def _validate_row(row: ResearchEventInformationAsymmetryWatchRow) -> None:
    if row.source_coverage_gap != _source_coverage_gap(row.source_coverage_ratio):
        raise ValueError("source_coverage_gap must match source_coverage_ratio")
    if row.specialist_confidence_gap != _specialist_confidence_gap(
        row.specialist_confidence_score,
    ):
        raise ValueError(
            "specialist_confidence_gap must match specialist_confidence_score",
        )
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row status must match reason_codes")
    if row.status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must only carry pass reason")


def _validate_report(report: ResearchEventInformationAsymmetryWatchReport) -> None:
    _require_hard_flags("report", report)
    if report.category_count != _count(len(report.rows)):
        raise ValueError("category_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("report status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")
    if report.max_source_coverage_gap != _max_decimal(
        row.source_coverage_gap for row in report.rows
    ):
        raise ValueError("max_source_coverage_gap must match rows")
    if report.max_update_latency_hours != _max_decimal(
        row.update_latency_hours for row in report.rows
    ):
        raise ValueError("max_update_latency_hours must match rows")
    if report.max_contradiction_rate != _max_decimal(
        row.contradiction_rate for row in report.rows
    ):
        raise ValueError("max_contradiction_rate must match rows")
    if report.min_specialist_confidence_score != _min_decimal(
        row.specialist_confidence_score for row in report.rows
    ):
        raise ValueError("min_specialist_confidence_score must match rows")
    if report.average_information_asymmetry_risk_score != _average_decimal(
        row.information_asymmetry_risk_score for row in report.rows
    ):
        raise ValueError(
            "average_information_asymmetry_risk_score must match rows",
        )


def _row_sort_key(
    row: ResearchEventInformationAsymmetryWatchRow,
) -> tuple[int, Decimal, Decimal]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[row.status],
        -row.information_asymmetry_risk_score,
        row.rank,
    )


def _status_count(
    rows: tuple[ResearchEventInformationAsymmetryWatchRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if any(reason in BLOCK_REASONS for reason in reason_codes):
        return STATUS_BLOCK
    if any(reason in WATCH_REASONS for reason in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _source_coverage_gap(source_coverage_ratio: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (ONE - source_coverage_ratio).quantize(VALUE_QUANTUM)


def _update_latency_pressure(
    update_latency_hours: Decimal,
    config: ResearchEventInformationAsymmetryWatchConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        pressure = (
            update_latency_hours / config.risk_full_update_latency_hours
        ).quantize(VALUE_QUANTUM)
    if pressure > ONE:
        return ONE
    return pressure


def _specialist_confidence_gap(specialist_confidence_score: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (ONE - specialist_confidence_score).quantize(VALUE_QUANTUM)


def _information_asymmetry_risk_score(
    *,
    source_coverage_gap: Decimal,
    update_latency_pressure: Decimal,
    contradiction_rate: Decimal,
    specialist_confidence_gap: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            (
                source_coverage_gap
                + update_latency_pressure
                + contradiction_rate
                + specialist_confidence_gap
            )
            / RISK_COMPONENT_COUNT
        ).quantize(VALUE_QUANTUM)


def _average_decimal(values: Iterable[Decimal]) -> Decimal | None:
    rows = tuple(values)
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return (sum(rows, ZERO) / Decimal(len(rows))).quantize(VALUE_QUANTUM)


def _max_decimal(values: Iterable[Decimal]) -> Decimal | None:
    rows = tuple(values)
    return max(rows) if rows else None


def _min_decimal(values: Iterable[Decimal]) -> Decimal | None:
    rows = tuple(values)
    return min(rows) if rows else None


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANTUM)


def _require_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_optional_ratio_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_reason_codes(
    field_name: str,
    value: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
    reason_set = set(reason_codes)
    return tuple(
        reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in reason_set
    )


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        flag_value = getattr(value, flag_name)
        if type(flag_value) is not bool or flag_value is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _set_or_validate_derived_validation_digest(
    report: ResearchEventInformationAsymmetryWatchReport,
) -> None:
    payload = _payload_value(report)
    expected = _digest_payload(payload)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_derived_validation_digest(
    report: ResearchEventInformationAsymmetryWatchReport,
) -> None:
    _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    expected = _digest_payload(_payload_value(report))
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_payload_derived_validation_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    expected = _digest_payload(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest must match public payload")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _digest_payload(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload["derived_validation_digest"] = ""
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in sorted(value.items())}
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {value!r}")


def _reject_unsafe_public_payload(context: str, value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_public_text(context, str(key))
            _reject_unsafe_public_payload(context, item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(context, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(context, value)
        return
    if type(value) in (bool, int, float, Decimal) or value is None:
        return
    raise ValueError(f"{context} contains unsupported public payload value")


def _reject_unsafe_public_text(context: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {context}")


def _reject_public_numeric_scalars(value: Any) -> None:
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_scalars(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_scalars(item)
        return
    if type(value) in (str, bool) or value is None:
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError("public payload must use Decimal strings")
    raise ValueError("public payload contains unsupported value")
