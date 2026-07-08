"""Pure report-only market-event information asymmetry watch report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_CONFIG_VERSION = (
    "research-market-event-information-asymmetry-watch-report-v0"
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
RISK_COMPONENT_COUNT = Decimal("5")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "information_asymmetry_empty_input"
PASS_REASON = "information_asymmetry_pass"
WATCH_REASON = "information_asymmetry_watch"
BLOCK_REASON = "information_asymmetry_block"
FRESHNESS_WATCH_REASON = "evidence_freshness_gap_watch"
FRESHNESS_BLOCK_REASON = "evidence_freshness_gap_block"
COVERAGE_WATCH_REASON = "source_class_coverage_gap_watch"
COVERAGE_BLOCK_REASON = "source_class_coverage_gap_block"
BOOK_MOVEMENT_WATCH_REASON = "book_movement_unexplained_by_evidence_watch"
BOOK_MOVEMENT_BLOCK_REASON = "book_movement_unexplained_by_evidence_block"
CONTRADICTION_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_pressure_block"
MANUAL_REVIEW_WATCH_REASON = "manual_review_urgency_watch"
MANUAL_REVIEW_BLOCK_REASON = "manual_review_urgency_block"

REASON_CODE_PRIORITY = (
    EMPTY_REASON,
    FRESHNESS_BLOCK_REASON,
    COVERAGE_BLOCK_REASON,
    BOOK_MOVEMENT_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    MANUAL_REVIEW_BLOCK_REASON,
    BLOCK_REASON,
    FRESHNESS_WATCH_REASON,
    COVERAGE_WATCH_REASON,
    BOOK_MOVEMENT_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    MANUAL_REVIEW_WATCH_REASON,
    WATCH_REASON,
    PASS_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)
BLOCK_REASONS = frozenset(
    (
        EMPTY_REASON,
        FRESHNESS_BLOCK_REASON,
        COVERAGE_BLOCK_REASON,
        BOOK_MOVEMENT_BLOCK_REASON,
        CONTRADICTION_BLOCK_REASON,
        MANUAL_REVIEW_BLOCK_REASON,
        BLOCK_REASON,
    ),
)
WATCH_REASONS = frozenset(
    (
        FRESHNESS_WATCH_REASON,
        COVERAGE_WATCH_REASON,
        BOOK_MOVEMENT_WATCH_REASON,
        CONTRADICTION_WATCH_REASON,
        MANUAL_REVIEW_WATCH_REASON,
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
    "source_ref",
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
)


@dataclass(frozen=True)
class ResearchMarketEventInformationAsymmetryWatchReportConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    max_pass_evidence_freshness_gap_hours: Decimal = Decimal("4.000000")
    max_watch_evidence_freshness_gap_hours: Decimal = Decimal("24.000000")
    risk_full_evidence_freshness_gap_hours: Decimal = Decimal("26.666667")
    max_pass_source_class_coverage_gap: Decimal = Decimal("0.250000")
    max_watch_source_class_coverage_gap: Decimal = Decimal("0.500000")
    max_pass_unexplained_book_movement_ratio: Decimal = Decimal("0.100000")
    max_watch_unexplained_book_movement_ratio: Decimal = Decimal("0.300000")
    max_pass_contradiction_pressure_score: Decimal = Decimal("0.200000")
    max_watch_contradiction_pressure_score: Decimal = Decimal("0.500000")
    max_pass_manual_review_urgency_score: Decimal = Decimal("0.200000")
    max_watch_manual_review_urgency_score: Decimal = Decimal("0.600000")
    watch_information_asymmetry_risk_score: Decimal = Decimal("0.300000")
    block_information_asymmetry_risk_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketEventInformationAsymmetryWatchReportConfig:
            raise ValueError(
                "config must be a "
                "ResearchMarketEventInformationAsymmetryWatchReportConfig",
            )
        _require_text("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "max_pass_evidence_freshness_gap_hours",
            "max_watch_evidence_freshness_gap_hours",
            "risk_full_evidence_freshness_gap_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_source_class_coverage_gap",
            "max_watch_source_class_coverage_gap",
            "max_pass_unexplained_book_movement_ratio",
            "max_watch_unexplained_book_movement_ratio",
            "max_pass_contradiction_pressure_score",
            "max_watch_contradiction_pressure_score",
            "max_pass_manual_review_urgency_score",
            "max_watch_manual_review_urgency_score",
            "watch_information_asymmetry_risk_score",
            "block_information_asymmetry_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketEventInformationAsymmetryWatchObservation:
    aggregate_key: str
    evidence_freshness_gap_hours: Decimal
    required_source_class_count: Decimal
    observed_source_class_count: Decimal
    book_movement_ratio: Decimal
    evidence_attribution_ratio: Decimal
    contradiction_pressure_score: Decimal
    manual_review_urgency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketEventInformationAsymmetryWatchObservation:
            raise ValueError(
                "observation must be a "
                "ResearchMarketEventInformationAsymmetryWatchObservation",
            )
        _require_private_aggregate_key("aggregate_key", self.aggregate_key)
        object.__setattr__(
            self,
            "evidence_freshness_gap_hours",
            _normalize_nonnegative_decimal(
                "evidence_freshness_gap_hours",
                self.evidence_freshness_gap_hours,
            ),
        )
        object.__setattr__(
            self,
            "required_source_class_count",
            _normalize_positive_count(
                "required_source_class_count",
                self.required_source_class_count,
            ),
        )
        object.__setattr__(
            self,
            "observed_source_class_count",
            _normalize_nonnegative_count(
                "observed_source_class_count",
                self.observed_source_class_count,
            ),
        )
        for field_name in (
            "book_movement_ratio",
            "evidence_attribution_ratio",
            "contradiction_pressure_score",
            "manual_review_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.observed_source_class_count > self.required_source_class_count:
            raise ValueError(
                "observed_source_class_count must not exceed "
                "required_source_class_count",
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketEventInformationAsymmetryWatchReportRow:
    aggregate_row_number: Decimal
    aggregate_key_hash: str
    evidence_freshness_gap_hours: Decimal
    required_source_class_count: Decimal
    observed_source_class_count: Decimal
    source_class_coverage_gap: Decimal
    book_movement_ratio: Decimal
    evidence_attribution_ratio: Decimal
    unexplained_book_movement_ratio: Decimal
    contradiction_pressure_score: Decimal
    manual_review_urgency_score: Decimal
    information_asymmetry_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketEventInformationAsymmetryWatchReportRow:
            raise ValueError(
                "row must be a "
                "ResearchMarketEventInformationAsymmetryWatchReportRow",
            )
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_count(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        _require_sha256_reference("aggregate_key_hash", self.aggregate_key_hash)
        object.__setattr__(
            self,
            "evidence_freshness_gap_hours",
            _normalize_nonnegative_decimal(
                "evidence_freshness_gap_hours",
                self.evidence_freshness_gap_hours,
            ),
        )
        object.__setattr__(
            self,
            "required_source_class_count",
            _normalize_positive_count(
                "required_source_class_count",
                self.required_source_class_count,
            ),
        )
        object.__setattr__(
            self,
            "observed_source_class_count",
            _normalize_nonnegative_count(
                "observed_source_class_count",
                self.observed_source_class_count,
            ),
        )
        for field_name in (
            "source_class_coverage_gap",
            "book_movement_ratio",
            "evidence_attribution_ratio",
            "unexplained_book_movement_ratio",
            "contradiction_pressure_score",
            "manual_review_urgency_score",
            "information_asymmetry_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchMarketEventInformationAsymmetryWatchReportReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if (
            type(self)
            is not ResearchMarketEventInformationAsymmetryWatchReportReasonCodeCount
        ):
            raise ValueError(
                "reason code count must be a "
                "ResearchMarketEventInformationAsymmetryWatchReportReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REASON_CODE_PRIORITY)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketEventInformationAsymmetryWatchReport:
    generated_at: datetime
    config_version: str
    aggregate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_evidence_freshness_gap_hours: Decimal | None
    max_source_class_coverage_gap: Decimal | None
    max_unexplained_book_movement_ratio: Decimal | None
    max_contradiction_pressure_score: Decimal | None
    max_manual_review_urgency_score: Decimal | None
    average_manual_review_urgency_score: Decimal | None
    average_information_asymmetry_risk_score: Decimal | None
    status: str
    rows: tuple[ResearchMarketEventInformationAsymmetryWatchReportRow, ...]
    reason_code_counts: tuple[
        ResearchMarketEventInformationAsymmetryWatchReportReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketEventInformationAsymmetryWatchReport:
            raise ValueError(
                "report must be a ResearchMarketEventInformationAsymmetryWatchReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in (
            "aggregate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_evidence_freshness_gap_hours",
            "max_source_class_coverage_gap",
            "max_unexplained_book_movement_ratio",
            "max_contradiction_pressure_score",
            "max_manual_review_urgency_score",
            "average_manual_review_urgency_score",
            "average_information_asymmetry_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_member("status", self.status, STATUSES)
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
        _require_hard_flags("report", self)
        _validate_report(self)
        _set_or_validate_public_digest(self)
        _reject_unsafe_public_payload("report", _payload_value(self))

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_event_information_asymmetry_watch_report_public_payload(
            self,
        )


def build_research_market_event_information_asymmetry_watch_report(
    observations: Iterable[ResearchMarketEventInformationAsymmetryWatchObservation],
    *,
    generated_at: datetime,
    config: ResearchMarketEventInformationAsymmetryWatchReportConfig,
) -> ResearchMarketEventInformationAsymmetryWatchReport:
    if type(config) is not ResearchMarketEventInformationAsymmetryWatchReportConfig:
        raise ValueError(
            "config must be a "
            "ResearchMarketEventInformationAsymmetryWatchReportConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    row_numbers = {
        item.aggregate_key: _count(index)
        for index, item in enumerate(normalized_observations, start=1)
    }
    rows = tuple(
        sorted(
            (
                _row_for_observation(
                    item,
                    aggregate_row_number=row_numbers[item.aggregate_key],
                    config=config,
                )
                for item in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketEventInformationAsymmetryWatchReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        aggregate_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        max_evidence_freshness_gap_hours=_max_decimal(
            row.evidence_freshness_gap_hours for row in rows
        ),
        max_source_class_coverage_gap=_max_decimal(
            row.source_class_coverage_gap for row in rows
        ),
        max_unexplained_book_movement_ratio=_max_decimal(
            row.unexplained_book_movement_ratio for row in rows
        ),
        max_contradiction_pressure_score=_max_decimal(
            row.contradiction_pressure_score for row in rows
        ),
        max_manual_review_urgency_score=_max_decimal(
            row.manual_review_urgency_score for row in rows
        ),
        average_manual_review_urgency_score=_average_decimal(
            row.manual_review_urgency_score for row in rows
        ),
        average_information_asymmetry_risk_score=_average_decimal(
            row.information_asymmetry_risk_score for row in rows
        ),
        status=_status_from_reason_codes(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_event_information_asymmetry_watch_report_public_payload(
    value: ResearchMarketEventInformationAsymmetryWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchMarketEventInformationAsymmetryWatchReport:
        _validate_report(value)
        _validate_public_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchMarketEventInformationAsymmetryWatchReport "
            "or dict",
        )
    validate_research_market_event_information_asymmetry_watch_report_public_payload(
        payload,
    )
    return dict(payload)


def validate_research_market_event_information_asymmetry_watch_report_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numeric_scalars(payload)
    _validate_payload_public_digest(payload)


def research_market_event_information_asymmetry_watch_report_public_digest(
    value: ResearchMarketEventInformationAsymmetryWatchReport | dict[str, Any],
) -> str:
    payload = research_market_event_information_asymmetry_watch_report_public_payload(
        value,
    )
    public_digest = payload.get("public_digest")
    _require_sha256_digest("public_digest", public_digest)
    return public_digest


def _row_for_observation(
    item: ResearchMarketEventInformationAsymmetryWatchObservation,
    *,
    aggregate_row_number: Decimal,
    config: ResearchMarketEventInformationAsymmetryWatchReportConfig,
) -> ResearchMarketEventInformationAsymmetryWatchReportRow:
    source_class_coverage_gap = _source_class_coverage_gap(
        item.required_source_class_count,
        item.observed_source_class_count,
    )
    unexplained_book_movement_ratio = _unexplained_book_movement_ratio(
        item.book_movement_ratio,
        item.evidence_attribution_ratio,
    )
    information_asymmetry_risk_score = _information_asymmetry_risk_score(
        evidence_freshness_gap_hours=item.evidence_freshness_gap_hours,
        source_class_coverage_gap=source_class_coverage_gap,
        unexplained_book_movement_ratio=unexplained_book_movement_ratio,
        contradiction_pressure_score=item.contradiction_pressure_score,
        manual_review_urgency_score=item.manual_review_urgency_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        evidence_freshness_gap_hours=item.evidence_freshness_gap_hours,
        source_class_coverage_gap=source_class_coverage_gap,
        unexplained_book_movement_ratio=unexplained_book_movement_ratio,
        contradiction_pressure_score=item.contradiction_pressure_score,
        manual_review_urgency_score=item.manual_review_urgency_score,
        information_asymmetry_risk_score=information_asymmetry_risk_score,
        config=config,
    )
    return ResearchMarketEventInformationAsymmetryWatchReportRow(
        aggregate_row_number=aggregate_row_number,
        aggregate_key_hash=_aggregate_key_hash(item.aggregate_key),
        evidence_freshness_gap_hours=item.evidence_freshness_gap_hours,
        required_source_class_count=item.required_source_class_count,
        observed_source_class_count=item.observed_source_class_count,
        source_class_coverage_gap=source_class_coverage_gap,
        book_movement_ratio=item.book_movement_ratio,
        evidence_attribution_ratio=item.evidence_attribution_ratio,
        unexplained_book_movement_ratio=unexplained_book_movement_ratio,
        contradiction_pressure_score=item.contradiction_pressure_score,
        manual_review_urgency_score=item.manual_review_urgency_score,
        information_asymmetry_risk_score=information_asymmetry_risk_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    evidence_freshness_gap_hours: Decimal,
    source_class_coverage_gap: Decimal,
    unexplained_book_movement_ratio: Decimal,
    contradiction_pressure_score: Decimal,
    manual_review_urgency_score: Decimal,
    information_asymmetry_risk_score: Decimal,
    config: ResearchMarketEventInformationAsymmetryWatchReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if evidence_freshness_gap_hours > config.max_watch_evidence_freshness_gap_hours:
        reasons.append(FRESHNESS_BLOCK_REASON)
    elif evidence_freshness_gap_hours > config.max_pass_evidence_freshness_gap_hours:
        reasons.append(FRESHNESS_WATCH_REASON)

    if source_class_coverage_gap > config.max_watch_source_class_coverage_gap:
        reasons.append(COVERAGE_BLOCK_REASON)
    elif source_class_coverage_gap > config.max_pass_source_class_coverage_gap:
        reasons.append(COVERAGE_WATCH_REASON)

    if (
        unexplained_book_movement_ratio
        > config.max_watch_unexplained_book_movement_ratio
    ):
        reasons.append(BOOK_MOVEMENT_BLOCK_REASON)
    elif (
        unexplained_book_movement_ratio
        > config.max_pass_unexplained_book_movement_ratio
    ):
        reasons.append(BOOK_MOVEMENT_WATCH_REASON)

    if contradiction_pressure_score > config.max_watch_contradiction_pressure_score:
        reasons.append(CONTRADICTION_BLOCK_REASON)
    elif contradiction_pressure_score > config.max_pass_contradiction_pressure_score:
        reasons.append(CONTRADICTION_WATCH_REASON)

    if manual_review_urgency_score > config.max_watch_manual_review_urgency_score:
        reasons.append(MANUAL_REVIEW_BLOCK_REASON)
    elif manual_review_urgency_score > config.max_pass_manual_review_urgency_score:
        reasons.append(MANUAL_REVIEW_WATCH_REASON)

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
    return _normalize_reason_codes("reason_codes", reasons)


def _report_reason_codes(
    rows: tuple[ResearchMarketEventInformationAsymmetryWatchReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    if all(row.status == "pass" for row in rows):
        return (PASS_REASON,)
    reasons = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != PASS_REASON
    )
    return _normalize_reason_codes("reason_codes", reasons)


def _reason_code_counts(
    rows: tuple[ResearchMarketEventInformationAsymmetryWatchReportRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketEventInformationAsymmetryWatchReportReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketEventInformationAsymmetryWatchReportReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchMarketEventInformationAsymmetryWatchReportReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODE_PRIORITY.index(item[0]),
        )
    )


def _normalize_observations(
    value: Iterable[ResearchMarketEventInformationAsymmetryWatchObservation],
) -> tuple[ResearchMarketEventInformationAsymmetryWatchObservation, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(value)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen: set[str] = set()
    for item in observations:
        if type(item) is not ResearchMarketEventInformationAsymmetryWatchObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketEventInformationAsymmetryWatchObservation values",
            )
        _require_hard_flags("observation", item)
        if item.aggregate_key in seen:
            raise ValueError("aggregate_key values must be unique")
        seen.add(item.aggregate_key)
    return tuple(sorted(observations, key=lambda item: item.aggregate_key))


def _normalize_rows(
    value: Iterable[ResearchMarketEventInformationAsymmetryWatchReportRow],
) -> tuple[ResearchMarketEventInformationAsymmetryWatchReportRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchMarketEventInformationAsymmetryWatchReportRow:
            raise ValueError(
                "rows must contain "
                "ResearchMarketEventInformationAsymmetryWatchReportRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status, risk, and row number")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchMarketEventInformationAsymmetryWatchReportReasonCodeCount],
) -> tuple[ResearchMarketEventInformationAsymmetryWatchReportReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in counts:
        if (
            type(count)
            is not ResearchMarketEventInformationAsymmetryWatchReportReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketEventInformationAsymmetryWatchReportReasonCodeCount "
                "values",
            )
        _require_hard_flags("reason_code_count", count)
    expected = tuple(
        sorted(counts, key=lambda row: REASON_CODE_PRIORITY.index(row.reason_code)),
    )
    if counts != expected:
        raise ValueError("reason_code_counts must be sorted by reason_code priority")
    return counts


def _validate_config(
    config: ResearchMarketEventInformationAsymmetryWatchReportConfig,
) -> None:
    if (
        config.max_pass_evidence_freshness_gap_hours
        >= config.max_watch_evidence_freshness_gap_hours
    ):
        raise ValueError(
            "max_pass_evidence_freshness_gap_hours must be less than "
            "max_watch_evidence_freshness_gap_hours",
        )
    if (
        config.max_watch_evidence_freshness_gap_hours
        > config.risk_full_evidence_freshness_gap_hours
    ):
        raise ValueError(
            "max_watch_evidence_freshness_gap_hours must not exceed "
            "risk_full_evidence_freshness_gap_hours",
        )
    if (
        config.max_pass_source_class_coverage_gap
        >= config.max_watch_source_class_coverage_gap
    ):
        raise ValueError(
            "max_pass_source_class_coverage_gap must be less than "
            "max_watch_source_class_coverage_gap",
        )
    if (
        config.max_pass_unexplained_book_movement_ratio
        >= config.max_watch_unexplained_book_movement_ratio
    ):
        raise ValueError(
            "max_pass_unexplained_book_movement_ratio must be less than "
            "max_watch_unexplained_book_movement_ratio",
        )
    if (
        config.max_pass_contradiction_pressure_score
        >= config.max_watch_contradiction_pressure_score
    ):
        raise ValueError(
            "max_pass_contradiction_pressure_score must be less than "
            "max_watch_contradiction_pressure_score",
        )
    if (
        config.max_pass_manual_review_urgency_score
        >= config.max_watch_manual_review_urgency_score
    ):
        raise ValueError(
            "max_pass_manual_review_urgency_score must be less than "
            "max_watch_manual_review_urgency_score",
        )
    if (
        config.watch_information_asymmetry_risk_score
        >= config.block_information_asymmetry_risk_score
    ):
        raise ValueError(
            "watch_information_asymmetry_risk_score must be less than "
            "block_information_asymmetry_risk_score",
        )


def _validate_row(row: ResearchMarketEventInformationAsymmetryWatchReportRow) -> None:
    if row.observed_source_class_count > row.required_source_class_count:
        raise ValueError(
            "observed_source_class_count must not exceed required_source_class_count",
        )
    if row.source_class_coverage_gap != _source_class_coverage_gap(
        row.required_source_class_count,
        row.observed_source_class_count,
    ):
        raise ValueError("source_class_coverage_gap must match source class counts")
    if row.unexplained_book_movement_ratio != _unexplained_book_movement_ratio(
        row.book_movement_ratio,
        row.evidence_attribution_ratio,
    ):
        raise ValueError(
            "unexplained_book_movement_ratio must match book and evidence ratios",
        )
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must only carry pass reason")


def _validate_report(
    report: ResearchMarketEventInformationAsymmetryWatchReport,
) -> None:
    _require_hard_flags("report", report)
    if report.aggregate_count != _count(len(report.rows)):
        raise ValueError("aggregate_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("report reason_codes must match rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("report status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")
    if report.max_evidence_freshness_gap_hours != _max_decimal(
        row.evidence_freshness_gap_hours for row in report.rows
    ):
        raise ValueError("max_evidence_freshness_gap_hours must match rows")
    if report.max_source_class_coverage_gap != _max_decimal(
        row.source_class_coverage_gap for row in report.rows
    ):
        raise ValueError("max_source_class_coverage_gap must match rows")
    if report.max_unexplained_book_movement_ratio != _max_decimal(
        row.unexplained_book_movement_ratio for row in report.rows
    ):
        raise ValueError("max_unexplained_book_movement_ratio must match rows")
    if report.max_contradiction_pressure_score != _max_decimal(
        row.contradiction_pressure_score for row in report.rows
    ):
        raise ValueError("max_contradiction_pressure_score must match rows")
    if report.max_manual_review_urgency_score != _max_decimal(
        row.manual_review_urgency_score for row in report.rows
    ):
        raise ValueError("max_manual_review_urgency_score must match rows")
    if report.average_manual_review_urgency_score != _average_decimal(
        row.manual_review_urgency_score for row in report.rows
    ):
        raise ValueError("average_manual_review_urgency_score must match rows")
    if report.average_information_asymmetry_risk_score != _average_decimal(
        row.information_asymmetry_risk_score for row in report.rows
    ):
        raise ValueError(
            "average_information_asymmetry_risk_score must match rows",
        )


def _row_sort_key(
    row: ResearchMarketEventInformationAsymmetryWatchReportRow,
) -> tuple[int, Decimal, Decimal]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.information_asymmetry_risk_score,
        row.aggregate_row_number,
    )


def _status_count(
    rows: tuple[ResearchMarketEventInformationAsymmetryWatchReportRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if any(reason in BLOCK_REASONS for reason in reason_codes):
        return "block"
    if any(reason in WATCH_REASONS for reason in reason_codes):
        return "watch"
    return "pass"


def _source_class_coverage_gap(
    required_source_class_count: Decimal,
    observed_source_class_count: Decimal,
) -> Decimal:
    if observed_source_class_count > required_source_class_count:
        raise ValueError(
            "observed_source_class_count must not exceed required_source_class_count",
        )
    with localcontext(DECIMAL_CONTEXT):
        return (
            (required_source_class_count - observed_source_class_count)
            / required_source_class_count
        ).quantize(VALUE_QUANTUM)


def _unexplained_book_movement_ratio(
    book_movement_ratio: Decimal,
    evidence_attribution_ratio: Decimal,
) -> Decimal:
    if evidence_attribution_ratio >= book_movement_ratio:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (book_movement_ratio - evidence_attribution_ratio).quantize(
            VALUE_QUANTUM,
        )


def _information_asymmetry_risk_score(
    *,
    evidence_freshness_gap_hours: Decimal,
    source_class_coverage_gap: Decimal,
    unexplained_book_movement_ratio: Decimal,
    contradiction_pressure_score: Decimal,
    manual_review_urgency_score: Decimal,
    config: ResearchMarketEventInformationAsymmetryWatchReportConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        freshness_pressure = (
            evidence_freshness_gap_hours / config.risk_full_evidence_freshness_gap_hours
        ).quantize(VALUE_QUANTUM)
        if freshness_pressure > ONE:
            freshness_pressure = ONE
        return (
            (
                freshness_pressure
                + source_class_coverage_gap
                + unexplained_book_movement_ratio
                + contradiction_pressure_score
                + manual_review_urgency_score
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


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_text(field_name: str, value: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")


def _require_private_aggregate_key(field_name: str, value: str) -> None:
    _require_text(field_name, value)


def _require_member(field_name: str, value: str, allowed_values: Iterable[str]) -> None:
    allowed = tuple(allowed_values)
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
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
        _require_member("reason_code", reason_code, REASON_CODES)
    reason_set = set(reason_codes)
    return tuple(
        reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in reason_set
    )


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        flag_value = getattr(value, flag_name)
        if type(flag_value) is not bool or flag_value is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _aggregate_key_hash(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _require_sha256_reference(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 reference")
    if not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 reference")
    _require_sha256_digest(field_name, value.removeprefix("sha256:"))


def _set_or_validate_public_digest(
    report: ResearchMarketEventInformationAsymmetryWatchReport,
) -> None:
    payload = _payload_value(report)
    expected = _digest_payload(payload)
    if report.public_digest == "":
        object.__setattr__(report, "public_digest", expected)
        return
    _require_sha256_digest("public_digest", report.public_digest)
    if report.public_digest != expected:
        raise ValueError("public_digest must match report fields")


def _validate_public_digest(
    report: ResearchMarketEventInformationAsymmetryWatchReport,
) -> None:
    _require_sha256_digest("public_digest", report.public_digest)
    expected = _digest_payload(_payload_value(report))
    if report.public_digest != expected:
        raise ValueError("public_digest must match report fields")


def _validate_payload_public_digest(payload: dict[str, Any]) -> None:
    public_digest = payload.get("public_digest")
    _require_sha256_digest("public_digest", public_digest)
    expected = _digest_payload(payload)
    if public_digest != expected:
        raise ValueError("public_digest must match public payload")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _digest_payload(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload["public_digest"] = ""
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
    if isinstance(value, (Decimal, int, float)) and type(value) is not bool:
        raise ValueError("public payload must use Decimal strings")
    if type(value) in (str, bool) or value is None:
        return
    raise ValueError("public payload contains unsupported value")
