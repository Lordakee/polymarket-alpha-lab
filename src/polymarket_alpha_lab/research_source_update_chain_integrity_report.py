"""Report-only integrity checks for research source update chains."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats


DEFAULT_RESEARCH_SOURCE_UPDATE_CHAIN_INTEGRITY_CONFIG_VERSION = (
    "research-source-update-chain-integrity-report-v1"
)

DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_RANK = {
    STATUS_BLOCK: 0,
    STATUS_WATCH: 1,
    STATUS_PASS: 2,
}

PASS_REASON = "source_update_chain_pass"
WATCH_REASON = "source_update_chain_watch"
BLOCK_REASON = "source_update_chain_block"
EMPTY_REASON = "source_update_chain_empty_block"
SEQUENCE_WATCH_REASON = "update_sequence_incomplete_watch"
SEQUENCE_BLOCK_REASON = "update_sequence_incomplete_block"
AUTHORITY_WATCH_REASON = "authority_continuity_broken_watch"
AUTHORITY_BLOCK_REASON = "authority_continuity_broken_block"
FRESHNESS_WATCH_REASON = "source_update_stale_watch"
FRESHNESS_BLOCK_REASON = "source_update_stale_block"
CONTRADICTION_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_pressure_block"
EXTRACTION_WATCH_REASON = "extraction_confidence_watch"
EXTRACTION_BLOCK_REASON = "extraction_confidence_block"
MANUAL_WATCH_REASON = "manual_verification_gap_watch"
MANUAL_BLOCK_REASON = "manual_verification_gap_block"

STATUS_REASONS = (PASS_REASON, WATCH_REASON, BLOCK_REASON)
REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    EMPTY_REASON,
    SEQUENCE_WATCH_REASON,
    SEQUENCE_BLOCK_REASON,
    AUTHORITY_WATCH_REASON,
    AUTHORITY_BLOCK_REASON,
    FRESHNESS_WATCH_REASON,
    FRESHNESS_BLOCK_REASON,
    CONTRADICTION_WATCH_REASON,
    CONTRADICTION_BLOCK_REASON,
    EXTRACTION_WATCH_REASON,
    EXTRACTION_BLOCK_REASON,
    MANUAL_WATCH_REASON,
    MANUAL_BLOCK_REASON,
)
REASON_CODE_SET = frozenset(REASON_CODES)

PRIVATE_PUBLIC_PAYLOAD_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_UPDATE_CHAIN_INTEGRITY_CONFIG_VERSION",
    "ResearchSourceUpdateChainIntegrityConfig",
    "ResearchSourceUpdateChainObservation",
    "ResearchSourceUpdateChainIntegrityRow",
    "ResearchSourceUpdateChainIntegrityReasonCodeCount",
    "ResearchSourceUpdateChainIntegrityReport",
    "build_research_source_update_chain_integrity_report",
    "research_source_update_chain_integrity_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceUpdateChainIntegrityConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_UPDATE_CHAIN_INTEGRITY_CONFIG_VERSION
    freshness_watch_after_seconds: Decimal = Decimal("86400")
    freshness_block_after_seconds: Decimal = Decimal("259200")
    sequence_watch_below_ratio: Decimal = Decimal("0.950000")
    sequence_block_below_ratio: Decimal = Decimal("0.500000")
    contradiction_watch_at_ratio: Decimal = Decimal("0.250000")
    contradiction_block_at_ratio: Decimal = Decimal("0.750000")
    extraction_watch_below_ratio: Decimal = Decimal("0.800000")
    extraction_block_below_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceUpdateChainIntegrityConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_UPDATE_CHAIN_INTEGRITY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "freshness_watch_after_seconds",
            "freshness_block_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "sequence_watch_below_ratio",
            "sequence_block_below_ratio",
            "contradiction_watch_at_ratio",
            "contradiction_block_at_ratio",
            "extraction_watch_below_ratio",
            "extraction_block_below_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.freshness_block_after_seconds <= self.freshness_watch_after_seconds:
            raise ValueError(
                "freshness_block_after_seconds must exceed freshness_watch_after_seconds",
            )
        if self.sequence_block_below_ratio > self.sequence_watch_below_ratio:
            raise ValueError(
                "sequence_block_below_ratio must not exceed sequence_watch_below_ratio",
            )
        if self.contradiction_block_at_ratio < self.contradiction_watch_at_ratio:
            raise ValueError(
                "contradiction_block_at_ratio must not be below "
                "contradiction_watch_at_ratio",
            )
        if self.extraction_block_below_ratio > self.extraction_watch_below_ratio:
            raise ValueError(
                "extraction_block_below_ratio must not exceed "
                "extraction_watch_below_ratio",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceUpdateChainObservation:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    update_chain_id: str
    authority_family: str
    authority_sequence_position: Decimal
    expected_previous_update_count: Decimal
    observed_previous_update_count: Decimal
    expected_next_update_count: Decimal
    observed_next_update_count: Decimal
    previous_authority_family: str | None
    source_observed_at: datetime
    contradiction_pressure: Decimal
    extraction_confidence: Decimal
    manual_verification_count: Decimal
    required_manual_verification_count: Decimal
    raw_source_url: str
    raw_source_text: str
    source_dsn: str
    source_table_name: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceUpdateChainObservation, "observation")
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "update_chain_id",
            "authority_family",
            "raw_source_url",
            "raw_source_text",
            "source_dsn",
            "source_table_name",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        if self.previous_authority_family is not None:
            _require_public_string(
                "previous_authority_family",
                self.previous_authority_family,
            )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "authority_sequence_position",
            _positive_count_decimal(
                "authority_sequence_position",
                self.authority_sequence_position,
            ),
        )
        for field_name in (
            "expected_previous_update_count",
            "observed_previous_update_count",
            "expected_next_update_count",
            "observed_next_update_count",
            "manual_verification_count",
            "required_manual_verification_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_pressure",
            "extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_observation(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceUpdateChainIntegrityRow:
    update_chain_id: str
    authority_family: str
    sequence_completeness_ratio: Decimal
    authority_continuity_ratio: Decimal
    freshness_age_seconds: Decimal
    contradiction_pressure: Decimal
    extraction_confidence: Decimal
    manual_verification_coverage_ratio: Decimal
    integrity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceUpdateChainIntegrityRow, "row")
        for field_name in ("update_chain_id", "authority_family"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "sequence_completeness_ratio",
            "authority_continuity_ratio",
            "contradiction_pressure",
            "extraction_confidence",
            "manual_verification_coverage_ratio",
            "integrity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_age_seconds",
            _nonnegative_decimal("freshness_age_seconds", self.freshness_age_seconds),
        )
        _require_choice("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _set_or_validate_digest(self, "row")


@dataclass(frozen=True)
class ResearchSourceUpdateChainIntegrityReasonCodeCount:
    reason_code: str
    row_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceUpdateChainIntegrityReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "row_count",
            _count_decimal("row_count", self.row_count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchSourceUpdateChainIntegrityReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    incomplete_sequence_count: Decimal
    authority_break_count: Decimal
    stale_update_count: Decimal
    contradiction_pressure_count: Decimal
    low_extraction_confidence_count: Decimal
    manual_verification_gap_count: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceUpdateChainIntegrityRow, ...]
    reason_code_counts: tuple[ResearchSourceUpdateChainIntegrityReasonCodeCount, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceUpdateChainIntegrityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_UPDATE_CHAIN_INTEGRITY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_choice("status", self.status, STATUSES)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "incomplete_sequence_count",
            "authority_break_count",
            "stale_update_count",
            "contradiction_pressure_count",
            "low_extraction_confidence_count",
            "manual_verification_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _set_or_validate_digest(self, "report")


def build_research_source_update_chain_integrity_report(
    observations: Iterable[ResearchSourceUpdateChainObservation],
    *,
    config: ResearchSourceUpdateChainIntegrityConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceUpdateChainIntegrityReport:
    report_config = config or ResearchSourceUpdateChainIntegrityConfig()
    if type(report_config) is not ResearchSourceUpdateChainIntegrityConfig:
        raise ValueError("config must be exactly ResearchSourceUpdateChainIntegrityConfig")
    _require_hard_flags("config", report_config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=report_config,
                    generated_at=generated_at_utc,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _decimal_from_int(len(rows))
    reason_codes = _report_reason_codes(rows)
    return ResearchSourceUpdateChainIntegrityReport(
        generated_at=generated_at_utc,
        config_version=report_config.config_version,
        status=_report_status(rows),
        row_count=row_count,
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        incomplete_sequence_count=_row_metric_count(
            row.sequence_completeness_ratio < ONE for row in rows
        ),
        authority_break_count=_row_metric_count(
            row.authority_continuity_ratio < ONE for row in rows
        ),
        stale_update_count=_row_reason_count(rows, FRESHNESS_WATCH_REASON)
        + _row_reason_count(rows, FRESHNESS_BLOCK_REASON),
        contradiction_pressure_count=_row_reason_count(rows, CONTRADICTION_WATCH_REASON)
        + _row_reason_count(rows, CONTRADICTION_BLOCK_REASON),
        low_extraction_confidence_count=_row_reason_count(rows, EXTRACTION_WATCH_REASON)
        + _row_reason_count(rows, EXTRACTION_BLOCK_REASON),
        manual_verification_gap_count=_row_reason_count(rows, MANUAL_WATCH_REASON)
        + _row_reason_count(rows, MANUAL_BLOCK_REASON),
        reason_codes=reason_codes,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def research_source_update_chain_integrity_report_payload(
    report: ResearchSourceUpdateChainIntegrityReport,
) -> "FrozenJsonObject":
    if type(report) is not ResearchSourceUpdateChainIntegrityReport:
        raise ValueError(
            "report must be exactly ResearchSourceUpdateChainIntegrityReport",
        )
    _require_hard_flags("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_public_payload_private_surfaces("payload", payload)
    return _freeze_json_object(payload)


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _row_from_observation(
    observation: ResearchSourceUpdateChainObservation,
    *,
    config: ResearchSourceUpdateChainIntegrityConfig,
    generated_at: datetime,
) -> ResearchSourceUpdateChainIntegrityRow:
    if observation.source_observed_at > generated_at:
        raise ValueError("source_observed_at must not be after generated_at")
    freshness_age_seconds = _duration_seconds(
        observation.source_observed_at,
        generated_at,
    )
    sequence_completeness_ratio = _sequence_completeness_ratio(observation)
    authority_continuity_ratio = _authority_continuity_ratio(observation)
    manual_verification_coverage_ratio = _manual_verification_coverage_ratio(observation)
    reason_codes = _row_reason_codes(
        sequence_completeness_ratio=sequence_completeness_ratio,
        authority_continuity_ratio=authority_continuity_ratio,
        freshness_age_seconds=freshness_age_seconds,
        contradiction_pressure=observation.contradiction_pressure,
        extraction_confidence=observation.extraction_confidence,
        manual_verification_coverage_ratio=manual_verification_coverage_ratio,
        config=config,
    )
    return ResearchSourceUpdateChainIntegrityRow(
        update_chain_id=observation.update_chain_id,
        authority_family=observation.authority_family,
        sequence_completeness_ratio=sequence_completeness_ratio,
        authority_continuity_ratio=authority_continuity_ratio,
        freshness_age_seconds=freshness_age_seconds,
        contradiction_pressure=observation.contradiction_pressure,
        extraction_confidence=observation.extraction_confidence,
        manual_verification_coverage_ratio=manual_verification_coverage_ratio,
        integrity_score=_integrity_score(
            sequence_completeness_ratio=sequence_completeness_ratio,
            contradiction_pressure=observation.contradiction_pressure,
            extraction_confidence=observation.extraction_confidence,
            manual_verification_coverage_ratio=manual_verification_coverage_ratio,
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _sequence_completeness_ratio(
    observation: ResearchSourceUpdateChainObservation,
) -> Decimal:
    expected_total = (
        observation.expected_previous_update_count + observation.expected_next_update_count
    )
    observed_total = (
        observation.observed_previous_update_count + observation.observed_next_update_count
    )
    if expected_total == ZERO:
        return ONE
    observed_floor = max(observed_total, ONE)
    return _bounded_ratio(observed_floor / expected_total)


def _authority_continuity_ratio(
    observation: ResearchSourceUpdateChainObservation,
) -> Decimal:
    if observation.previous_authority_family is None:
        return ONE
    if observation.previous_authority_family == observation.authority_family:
        return ONE
    return ZERO


def _manual_verification_coverage_ratio(
    observation: ResearchSourceUpdateChainObservation,
) -> Decimal:
    if observation.required_manual_verification_count == ZERO:
        return ONE
    return _bounded_ratio(
        observation.manual_verification_count
        / observation.required_manual_verification_count,
    )


def _integrity_score(
    *,
    sequence_completeness_ratio: Decimal,
    contradiction_pressure: Decimal,
    extraction_confidence: Decimal,
    manual_verification_coverage_ratio: Decimal,
) -> Decimal:
    contradiction_quality = ONE - contradiction_pressure
    score = (
        sequence_completeness_ratio * Decimal("0.400000")
        + contradiction_quality * Decimal("0.200000")
        + extraction_confidence * Decimal("0.200000")
        + manual_verification_coverage_ratio * Decimal("0.100000")
        + Decimal("0.100000")
    )
    return _bounded_ratio(score)


def _row_reason_codes(
    *,
    sequence_completeness_ratio: Decimal,
    authority_continuity_ratio: Decimal,
    freshness_age_seconds: Decimal,
    contradiction_pressure: Decimal,
    extraction_confidence: Decimal,
    manual_verification_coverage_ratio: Decimal,
    config: ResearchSourceUpdateChainIntegrityConfig,
) -> tuple[str, ...]:
    severities: list[str] = []
    detail_bases: list[str] = []
    if sequence_completeness_ratio < config.sequence_block_below_ratio:
        severities.append(STATUS_BLOCK)
        detail_bases.append("sequence")
    elif sequence_completeness_ratio < config.sequence_watch_below_ratio:
        severities.append(STATUS_WATCH)
        detail_bases.append("sequence")
    if authority_continuity_ratio < ONE:
        severities.append(STATUS_WATCH)
        detail_bases.append("authority")
    if freshness_age_seconds >= config.freshness_block_after_seconds:
        severities.append(STATUS_BLOCK)
        detail_bases.append("freshness")
    elif freshness_age_seconds >= config.freshness_watch_after_seconds:
        severities.append(STATUS_WATCH)
        detail_bases.append("freshness")
    if contradiction_pressure >= config.contradiction_block_at_ratio:
        severities.append(STATUS_BLOCK)
        detail_bases.append("contradiction")
    elif contradiction_pressure >= config.contradiction_watch_at_ratio:
        severities.append(STATUS_WATCH)
        detail_bases.append("contradiction")
    if extraction_confidence < config.extraction_block_below_ratio:
        severities.append(STATUS_BLOCK)
        detail_bases.append("extraction")
    elif extraction_confidence < config.extraction_watch_below_ratio:
        severities.append(STATUS_WATCH)
        detail_bases.append("extraction")
    if manual_verification_coverage_ratio == ZERO:
        severities.append(STATUS_BLOCK)
        detail_bases.append("manual")
    elif manual_verification_coverage_ratio < ONE:
        severities.append(STATUS_WATCH)
        detail_bases.append("manual")

    status = _status_from_severities(severities)
    if status == STATUS_PASS:
        return (PASS_REASON,)
    status_reason = BLOCK_REASON if status == STATUS_BLOCK else WATCH_REASON
    return (status_reason, *tuple(_detail_reason(base, status) for base in detail_bases))


def _status_from_severities(severities: list[str]) -> str:
    if STATUS_BLOCK in severities:
        return STATUS_BLOCK
    if STATUS_WATCH in severities:
        return STATUS_WATCH
    return STATUS_PASS


def _detail_reason(base: str, status: str) -> str:
    suffix = "block" if status == STATUS_BLOCK else "watch"
    reason_by_base = {
        ("sequence", "watch"): SEQUENCE_WATCH_REASON,
        ("sequence", "block"): SEQUENCE_BLOCK_REASON,
        ("authority", "watch"): AUTHORITY_WATCH_REASON,
        ("authority", "block"): AUTHORITY_BLOCK_REASON,
        ("freshness", "watch"): FRESHNESS_WATCH_REASON,
        ("freshness", "block"): FRESHNESS_BLOCK_REASON,
        ("contradiction", "watch"): CONTRADICTION_WATCH_REASON,
        ("contradiction", "block"): CONTRADICTION_BLOCK_REASON,
        ("extraction", "watch"): EXTRACTION_WATCH_REASON,
        ("extraction", "block"): EXTRACTION_BLOCK_REASON,
        ("manual", "watch"): MANUAL_WATCH_REASON,
        ("manual", "block"): MANUAL_BLOCK_REASON,
    }
    return reason_by_base[(base, suffix)]


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] in (BLOCK_REASON, EMPTY_REASON):
        return STATUS_BLOCK
    if reason_codes[0] == WATCH_REASON:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchSourceUpdateChainIntegrityRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchSourceUpdateChainIntegrityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in codes:
                codes.append(reason_code)
    return tuple(sorted(codes, key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in (BLOCK_REASON, EMPTY_REASON):
        return (0, reason_code)
    if reason_code == WATCH_REASON:
        return (1, reason_code)
    if reason_code == PASS_REASON:
        return (3, reason_code)
    return (2, reason_code)


def _normalize_observations(
    observations: Iterable[ResearchSourceUpdateChainObservation],
) -> tuple[ResearchSourceUpdateChainObservation, ...]:
    if isinstance(observations, (str, bytes, dict)):
        raise ValueError("observations must be an iterable of observations")
    normalized = tuple(observations)
    seen_update_chain_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not ResearchSourceUpdateChainObservation:
            raise ValueError(
                "observations must contain ResearchSourceUpdateChainObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.update_chain_id in seen_update_chain_ids:
            raise ValueError("update_chain_id values must be unique")
        seen_update_chain_ids.add(observation.update_chain_id)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceUpdateChainIntegrityRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_update_chain_ids: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchSourceUpdateChainIntegrityRow:
            raise ValueError("rows must contain ResearchSourceUpdateChainIntegrityRow")
        _require_hard_flags("row", row)
        if row.update_chain_id in seen_update_chain_ids:
            raise ValueError("rows update_chain_id values must be unique")
        seen_update_chain_ids.add(row.update_chain_id)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchSourceUpdateChainIntegrityReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen_reason_codes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchSourceUpdateChainIntegrityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceUpdateChainIntegrityReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _row_sort_key(row: ResearchSourceUpdateChainIntegrityRow) -> tuple[int, Decimal, str]:
    return (
        STATUS_SORT_RANK[row.status],
        -row.freshness_age_seconds,
        row.update_chain_id,
    )


def _reason_code_counts(
    rows: tuple[ResearchSourceUpdateChainIntegrityRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceUpdateChainIntegrityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceUpdateChainIntegrityReasonCodeCount(
                reason_code=EMPTY_REASON,
                row_count=ZERO,
            ),
        )
    counts: dict[str, Decimal] = {}
    for reason_code in report_reason_codes:
        counts[reason_code] = ZERO
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchSourceUpdateChainIntegrityReasonCodeCount(
            reason_code=reason_code,
            row_count=count,
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ResearchSourceUpdateChainIntegrityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _row_reason_count(
    rows: tuple[ResearchSourceUpdateChainIntegrityRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_from_int(
        sum(1 for row in rows if reason_code in row.reason_codes),
    )


def _row_metric_count(values: Iterable[bool]) -> Decimal:
    return _decimal_from_int(sum(1 for value in values if value))


def _validate_observation(observation: ResearchSourceUpdateChainObservation) -> None:
    if observation.observed_previous_update_count > observation.expected_previous_update_count:
        raise ValueError(
            "observed_previous_update_count must not exceed "
            "expected_previous_update_count",
        )
    if observation.observed_next_update_count > observation.expected_next_update_count:
        raise ValueError(
            "observed_next_update_count must not exceed expected_next_update_count",
        )
    if (
        observation.manual_verification_count
        > observation.required_manual_verification_count
    ):
        raise ValueError(
            "manual_verification_count must not exceed "
            "required_manual_verification_count",
        )


def _validate_row(row: ResearchSourceUpdateChainIntegrityRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must only include the pass reason")
    if row.status != STATUS_PASS and len(row.reason_codes) == 1:
        raise ValueError("watch or block rows require detail reasons")


def _validate_report(report: ResearchSourceUpdateChainIntegrityReport) -> None:
    expected_values = {
        "row_count": _decimal_from_int(len(report.rows)),
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
        "incomplete_sequence_count": _row_metric_count(
            row.sequence_completeness_ratio < ONE for row in report.rows
        ),
        "authority_break_count": _row_metric_count(
            row.authority_continuity_ratio < ONE for row in report.rows
        ),
        "stale_update_count": _row_reason_count(report.rows, FRESHNESS_WATCH_REASON)
        + _row_reason_count(report.rows, FRESHNESS_BLOCK_REASON),
        "contradiction_pressure_count": _row_reason_count(
            report.rows,
            CONTRADICTION_WATCH_REASON,
        )
        + _row_reason_count(report.rows, CONTRADICTION_BLOCK_REASON),
        "low_extraction_confidence_count": _row_reason_count(
            report.rows,
            EXTRACTION_WATCH_REASON,
        )
        + _row_reason_count(report.rows, EXTRACTION_BLOCK_REASON),
        "manual_verification_gap_count": _row_reason_count(
            report.rows,
            MANUAL_WATCH_REASON,
        )
        + _row_reason_count(report.rows, MANUAL_BLOCK_REASON),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")


def _normalize_reason_codes(
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        if allow_empty:
            return ()
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    if reason_codes[0] not in (*STATUS_REASONS, EMPTY_REASON):
        raise ValueError("reason_codes must begin with a status reason")
    if reason_codes[0] == PASS_REASON and len(reason_codes) != 1:
        raise ValueError("pass reason_codes must stand alone")
    if reason_codes[0] != PASS_REASON and reason_codes[0] != EMPTY_REASON:
        if len(reason_codes) == 1:
            raise ValueError("watch or block reason_codes require detail reasons")
    if reason_codes[0] == EMPTY_REASON and len(reason_codes) != 1:
        raise ValueError("empty reason_codes must stand alone")
    return reason_codes


def _set_or_validate_digest(value: object, label: str) -> None:
    current_digest = getattr(value, "validation_digest")
    if current_digest == "":
        object.__setattr__(
            value,
            "validation_digest",
            _validation_digest(value, label),
        )
        return
    _require_digest("validation_digest", current_digest)
    if current_digest != _validation_digest(value, label):
        raise ValueError("validation_digest does not match payload")


def _validation_digest(value: object, label: str) -> str:
    ready_value = _json_ready_without_digest(value)
    if type(ready_value) is dict:
        _reject_public_payload_private_surfaces(f"{label} digest payload", ready_value)
    canonical_payload = json.dumps(
        ready_value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    ready = json_ready_no_floats(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    ready.pop("validation_digest", None)
    return ready


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_public_payload_private_surfaces(label: str, payload: object) -> None:
    for key, value in _iter_public_payload_items(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in PRIVATE_PUBLIC_PAYLOAD_FRAGMENTS):
            raise ValueError(f"private public payload field in {label}: {key}")
        if type(value) is str:
            normalized_value = value.lower()
            if any(
                fragment in normalized_value
                for fragment in ("://", "token", "wallet", "order", "trade", " live")
            ):
                raise ValueError(f"private public payload value in {label}: {key}")


def _iter_public_payload_items(value: object) -> tuple[tuple[str, object], ...]:
    if isinstance(value, dict):
        items: list[tuple[str, object]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append((key, item))
            items.extend(_iter_public_payload_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_payload_items(item))
        return tuple(items)
    return ()


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    start = _as_utc("started_at", started_at)
    finish = _as_utc("finished_at", finished_at)
    if finish < start:
        raise ValueError("duration seconds must be nonnegative")
    delta = finish - start
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize(seconds)


def _decimal_from_int(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _positive_count_decimal(name: str, value: object) -> Decimal:
    normalized = _count_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _count_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _bounded_ratio(value: Decimal) -> Decimal:
    return _ratio_decimal("ratio", min(max(_quantize(value), ZERO), ONE))


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be quantizable") from exc


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_choice(name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        joined_choices = ", ".join(choices)
        raise ValueError(f"{name} must be one of: {joined_choices}")


def _require_reason_code(name: str, value: object) -> None:
    _require_public_string(name, value)
    if value not in REASON_CODE_SET:
        raise ValueError(f"{name} must be a known reason code")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a 64-character hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be lowercase hex")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
