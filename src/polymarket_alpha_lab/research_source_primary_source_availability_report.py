"""Pure in-memory primary source availability report for strategy review."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_SOURCE_PRIMARY_SOURCE_AVAILABILITY_REPORT_CONFIG_VERSION = (
    "research-source-primary-source-availability-report-v0"
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
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}

PASS_REASON = "primary_source_availability_pass"
WATCH_REASON = "primary_source_availability_watch"
BLOCK_REASON = "primary_source_availability_block"
EMPTY_REASON = "no_primary_source_scopes"
MISSING_PRIMARY_REASON = "missing_primary_source"
STALE_WATCH_REASON = "stale_primary_source_watch"
STALE_BLOCK_REASON = "stale_primary_source_block"
AUTHORITY_WATCH_REASON = "authority_score_watch"
AUTHORITY_BLOCK_REASON = "authority_score_block"
CORROBORATION_WATCH_REASON = "corroboration_gap_watch"
CORROBORATION_BLOCK_REASON = "corroboration_gap_block"
ACCESSIBILITY_WATCH_REASON = "accessibility_watch"
ACCESSIBILITY_BLOCK_REASON = "accessibility_block"

STATUS_REASON_CODES = (PASS_REASON, WATCH_REASON, BLOCK_REASON)
DETAIL_REASON_CODES = (
    ACCESSIBILITY_BLOCK_REASON,
    ACCESSIBILITY_WATCH_REASON,
    AUTHORITY_BLOCK_REASON,
    AUTHORITY_WATCH_REASON,
    CORROBORATION_BLOCK_REASON,
    CORROBORATION_WATCH_REASON,
    MISSING_PRIMARY_REASON,
    STALE_BLOCK_REASON,
    STALE_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON, PASS_REASON, *DETAIL_REASON_CODES)
ROW_REASON_CODES = (*STATUS_REASON_CODES, *DETAIL_REASON_CODES)
REASON_CODE_SET = frozenset((*REPORT_REASON_CODES, *ROW_REASON_CODES))

UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "candidate_id",
    "candidate-id",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "slug",
    "question",
    "raw_url",
    "raw-url",
    "url",
    "source_text",
    "source-text",
    "text",
    "dsn",
    "table",
    "token",
    "api_key",
    "secret",
    "password",
    "credential",
    "bearer",
    "authentication",
    "authorization",
    "database",
    "network",
    "file_path",
    "file-path",
    "filesystem",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
    "recommendation",
    "execution",
    "execute",
    "http://",
    "https://",
    "www.",
)
AUTH_SURFACE_PATTERN = re.compile(r"(?<![a-z0-9])auth(?![a-z0-9])")

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_PRIMARY_SOURCE_AVAILABILITY_REPORT_CONFIG_VERSION",
    "ResearchSourcePrimarySourceAvailabilityConfig",
    "ResearchSourcePrimarySourceAvailabilitySignal",
    "ResearchSourcePrimarySourceAvailabilityRow",
    "ResearchSourcePrimarySourceAvailabilityReport",
    "build_research_source_primary_source_availability_report",
    "research_source_primary_source_availability_report_digest",
    "research_source_primary_source_availability_report_payload",
    "validate_research_source_primary_source_availability_report_digest",
)


@dataclass(frozen=True)
class ResearchSourcePrimarySourceAvailabilityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_PRIMARY_SOURCE_AVAILABILITY_REPORT_CONFIG_VERSION
    )
    max_fresh_age_seconds: Decimal = Decimal("3600.000000")
    block_stale_age_seconds: Decimal = Decimal("10800.000000")
    authority_watch_threshold: Decimal = Decimal("0.700000")
    authority_block_threshold: Decimal = Decimal("0.400000")
    minimum_corroborating_source_count: Decimal = Decimal("2.000000")
    access_watch_threshold: Decimal = Decimal("0.800000")
    access_block_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourcePrimarySourceAvailabilityConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchSourcePrimarySourceAvailabilityConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_PRIMARY_SOURCE_AVAILABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "max_fresh_age_seconds",
            _normalize_positive_decimal(
                "max_fresh_age_seconds",
                self.max_fresh_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "block_stale_age_seconds",
            _normalize_positive_decimal(
                "block_stale_age_seconds",
                self.block_stale_age_seconds,
            ),
        )
        for field_name in (
            "authority_watch_threshold",
            "authority_block_threshold",
            "access_watch_threshold",
            "access_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_corroborating_source_count",
            _normalize_positive_count(
                "minimum_corroborating_source_count",
                self.minimum_corroborating_source_count,
            ),
        )
        if self.block_stale_age_seconds <= self.max_fresh_age_seconds:
            raise ValueError(
                "block_stale_age_seconds must exceed max_fresh_age_seconds",
            )
        _require_watch_block_threshold_pair(
            "authority_watch_threshold",
            self.authority_watch_threshold,
            "authority_block_threshold",
            self.authority_block_threshold,
        )
        _require_watch_block_threshold_pair(
            "access_watch_threshold",
            self.access_watch_threshold,
            "access_block_threshold",
            self.access_block_threshold,
        )
        require_paper_only_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchSourcePrimarySourceAvailabilitySignal:
    review_scope: str
    primary_source_available: bool
    latest_primary_evidence_at: datetime | None
    primary_evidence_count: Decimal
    authority_score: Decimal
    corroborating_source_count: Decimal
    access_success_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourcePrimarySourceAvailabilitySignal does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "signal",
            self,
            ResearchSourcePrimarySourceAvailabilitySignal,
        )
        object.__setattr__(
            self,
            "review_scope",
            _require_safe_public_string("review_scope", self.review_scope),
        )
        if type(self.primary_source_available) is not bool:
            raise ValueError("primary_source_available must be a bool")
        object.__setattr__(
            self,
            "latest_primary_evidence_at",
            _optional_utc(
                "latest_primary_evidence_at",
                self.latest_primary_evidence_at,
            ),
        )
        object.__setattr__(
            self,
            "primary_evidence_count",
            _normalize_count("primary_evidence_count", self.primary_evidence_count),
        )
        for field_name in ("authority_score", "access_success_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroborating_source_count",
            _normalize_count(
                "corroborating_source_count",
                self.corroborating_source_count,
            ),
        )
        require_paper_only_flags("signal", self)
        _reject_unsafe_public_surface("signal", self)


@dataclass(frozen=True)
class ResearchSourcePrimarySourceAvailabilityRow:
    review_scope: str
    primary_source_available: bool
    latest_primary_evidence_at: datetime | None
    primary_evidence_count: Decimal
    authority_score: Decimal
    corroborating_source_count: Decimal
    access_success_ratio: Decimal
    primary_evidence_age_seconds: Decimal | None
    freshness_score: Decimal
    corroboration_score: Decimal
    strategy_review_readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourcePrimarySourceAvailabilityRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourcePrimarySourceAvailabilityRow)
        object.__setattr__(
            self,
            "review_scope",
            _require_safe_public_string("review_scope", self.review_scope),
        )
        if type(self.primary_source_available) is not bool:
            raise ValueError("primary_source_available must be a bool")
        object.__setattr__(
            self,
            "latest_primary_evidence_at",
            _optional_utc(
                "latest_primary_evidence_at",
                self.latest_primary_evidence_at,
            ),
        )
        object.__setattr__(
            self,
            "primary_evidence_count",
            _normalize_count("primary_evidence_count", self.primary_evidence_count),
        )
        for field_name in (
            "authority_score",
            "access_success_ratio",
            "freshness_score",
            "corroboration_score",
            "strategy_review_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroborating_source_count",
            _normalize_count(
                "corroborating_source_count",
                self.corroborating_source_count,
            ),
        )
        object.__setattr__(
            self,
            "primary_evidence_age_seconds",
            _optional_nonnegative_decimal(
                "primary_evidence_age_seconds",
                self.primary_evidence_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        require_paper_only_flags("row", self)
        _reject_unsafe_public_surface("row", self)
        _set_or_validate_digest(self, "row")


@dataclass(frozen=True)
class ResearchSourcePrimarySourceAvailabilityReport:
    generated_at: datetime
    config_version: str
    review_scope_count: Decimal
    available_primary_source_count: Decimal
    fresh_primary_source_count: Decimal
    authoritative_primary_source_count: Decimal
    corroborated_primary_source_count: Decimal
    accessible_primary_source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    lowest_strategy_review_readiness_score: Decimal
    highest_primary_evidence_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourcePrimarySourceAvailabilityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourcePrimarySourceAvailabilityReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourcePrimarySourceAvailabilityReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_PRIMARY_SOURCE_AVAILABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "review_scope_count",
            "available_primary_source_count",
            "fresh_primary_source_count",
            "authoritative_primary_source_count",
            "corroborated_primary_source_count",
            "accessible_primary_source_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "lowest_strategy_review_readiness_score",
            _normalize_ratio(
                "lowest_strategy_review_readiness_score",
                self.lowest_strategy_review_readiness_score,
            ),
        )
        object.__setattr__(
            self,
            "highest_primary_evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "highest_primary_evidence_age_seconds",
                self.highest_primary_evidence_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        require_paper_only_flags("report", self)
        _reject_unsafe_public_surface("report", self)
        _set_or_validate_digest(self, "report")


def build_research_source_primary_source_availability_report(
    signals: Iterable[ResearchSourcePrimarySourceAvailabilitySignal],
    *,
    config: ResearchSourcePrimarySourceAvailabilityConfig | None = None,
    generated_at: datetime,
) -> ResearchSourcePrimarySourceAvailabilityReport:
    normalized_config = (
        ResearchSourcePrimarySourceAvailabilityConfig()
        if config is None
        else _require_config(config)
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (
                _row_from_signal(
                    signal,
                    config=normalized_config,
                    generated_at=generated_at_utc,
                )
                for signal in normalized_signals
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchSourcePrimarySourceAvailabilityReport(
        generated_at=generated_at_utc,
        config_version=normalized_config.config_version,
        review_scope_count=_decimal_from_int(len(rows)),
        available_primary_source_count=_decimal_from_int(
            sum(1 for row in rows if row.primary_source_available),
        ),
        fresh_primary_source_count=_row_condition_count(
            rows,
            _row_has_fresh_primary_source,
        ),
        authoritative_primary_source_count=_row_condition_count(
            rows,
            _row_has_authoritative_primary_source,
        ),
        corroborated_primary_source_count=_row_condition_count(
            rows,
            _row_has_corroborated_primary_source,
        ),
        accessible_primary_source_count=_row_condition_count(
            rows,
            _row_has_accessible_primary_source,
        ),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        lowest_strategy_review_readiness_score=min(
            (row.strategy_review_readiness_score for row in rows),
            default=ZERO,
        ),
        highest_primary_evidence_age_seconds=max(
            (
                row.primary_evidence_age_seconds
                for row in rows
                if row.primary_evidence_age_seconds is not None
            ),
            default=ZERO,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_primary_source_availability_report_payload(
    report: ResearchSourcePrimarySourceAvailabilityReport,
) -> "FrozenJsonObject":
    _require_exact_type("report", report, ResearchSourcePrimarySourceAvailabilityReport)
    require_paper_only_flags("report", report)
    validate_research_source_primary_source_availability_report_digest(report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_surface("payload", payload)
    return _freeze_json_object(payload)


def research_source_primary_source_availability_report_digest(
    report: ResearchSourcePrimarySourceAvailabilityReport,
) -> str:
    _require_exact_type("report", report, ResearchSourcePrimarySourceAvailabilityReport)
    require_paper_only_flags("report", report)
    return _derived_validation_digest(report, "report")


def validate_research_source_primary_source_availability_report_digest(
    report: ResearchSourcePrimarySourceAvailabilityReport,
) -> bool:
    _require_exact_type("report", report, ResearchSourcePrimarySourceAvailabilityReport)
    require_paper_only_flags("report", report)
    _require_digest("derived_validation_digest", report.derived_validation_digest)
    expected = research_source_primary_source_availability_report_digest(report)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match payload")
    return True


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


def _require_config(
    config: ResearchSourcePrimarySourceAvailabilityConfig,
) -> ResearchSourcePrimarySourceAvailabilityConfig:
    _require_exact_type("config", config, ResearchSourcePrimarySourceAvailabilityConfig)
    require_paper_only_flags("config", config)
    _reject_unsafe_public_surface("config", config)
    return config


def _normalize_signals(
    signals: Iterable[ResearchSourcePrimarySourceAvailabilitySignal],
) -> tuple[ResearchSourcePrimarySourceAvailabilitySignal, ...]:
    if isinstance(signals, (str, bytes, dict)):
        raise ValueError("signals must be an iterable of availability signals")
    normalized = tuple(signals)
    seen_review_scopes: set[str] = set()
    for signal in normalized:
        _require_exact_type("signal", signal, ResearchSourcePrimarySourceAvailabilitySignal)
        require_paper_only_flags("signal", signal)
        _reject_unsafe_public_surface("signal", signal)
        if signal.review_scope in seen_review_scopes:
            raise ValueError("review_scope values must be unique")
        seen_review_scopes.add(signal.review_scope)
    return normalized


def _row_from_signal(
    signal: ResearchSourcePrimarySourceAvailabilitySignal,
    *,
    config: ResearchSourcePrimarySourceAvailabilityConfig,
    generated_at: datetime,
) -> ResearchSourcePrimarySourceAvailabilityRow:
    if signal.latest_primary_evidence_at is not None:
        if signal.latest_primary_evidence_at > generated_at:
            raise ValueError("latest_primary_evidence_at must not be after generated_at")
        primary_evidence_age_seconds = _duration_seconds(
            signal.latest_primary_evidence_at,
            generated_at,
        )
    else:
        primary_evidence_age_seconds = None
    freshness_score = _freshness_score(
        signal,
        primary_evidence_age_seconds=primary_evidence_age_seconds,
        config=config,
    )
    corroboration_score = _corroboration_score(signal, config=config)
    reason_codes = _row_reason_codes(
        signal,
        primary_evidence_age_seconds=primary_evidence_age_seconds,
        config=config,
    )
    status = _status_from_detail_reasons(reason_codes)
    return ResearchSourcePrimarySourceAvailabilityRow(
        review_scope=signal.review_scope,
        primary_source_available=signal.primary_source_available,
        latest_primary_evidence_at=signal.latest_primary_evidence_at,
        primary_evidence_count=signal.primary_evidence_count,
        authority_score=signal.authority_score,
        corroborating_source_count=signal.corroborating_source_count,
        access_success_ratio=signal.access_success_ratio,
        primary_evidence_age_seconds=primary_evidence_age_seconds,
        freshness_score=freshness_score,
        corroboration_score=corroboration_score,
        strategy_review_readiness_score=_strategy_review_readiness_score(
            signal,
            freshness_score=freshness_score,
            corroboration_score=corroboration_score,
        ),
        status=status,
        reason_codes=(
            _status_reason_for_status(status),
            *reason_codes,
        ),
    )


def _freshness_score(
    signal: ResearchSourcePrimarySourceAvailabilitySignal,
    *,
    primary_evidence_age_seconds: Decimal | None,
    config: ResearchSourcePrimarySourceAvailabilityConfig,
) -> Decimal:
    if (
        not signal.primary_source_available
        or signal.primary_evidence_count == ZERO
        or primary_evidence_age_seconds is None
    ):
        return ZERO
    if primary_evidence_age_seconds <= config.max_fresh_age_seconds:
        return ONE
    if primary_evidence_age_seconds >= config.block_stale_age_seconds:
        return ZERO
    return _normalize_ratio(
        "freshness_score",
        ONE - (primary_evidence_age_seconds / config.block_stale_age_seconds),
    )


def _corroboration_score(
    signal: ResearchSourcePrimarySourceAvailabilitySignal,
    *,
    config: ResearchSourcePrimarySourceAvailabilityConfig,
) -> Decimal:
    if not signal.primary_source_available:
        return ZERO
    return _normalize_ratio(
        "corroboration_score",
        min(
            ONE,
            signal.corroborating_source_count
            / config.minimum_corroborating_source_count,
        ),
    )


def _strategy_review_readiness_score(
    signal: ResearchSourcePrimarySourceAvailabilitySignal,
    *,
    freshness_score: Decimal,
    corroboration_score: Decimal,
) -> Decimal:
    availability_score = ONE if signal.primary_source_available else ZERO
    return _normalize_ratio(
        "strategy_review_readiness_score",
        (
            availability_score
            + freshness_score
            + signal.authority_score
            + corroboration_score
            + signal.access_success_ratio
        )
        / Decimal("5"),
    )


def _row_reason_codes(
    signal: ResearchSourcePrimarySourceAvailabilitySignal,
    *,
    primary_evidence_age_seconds: Decimal | None,
    config: ResearchSourcePrimarySourceAvailabilityConfig,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    source_missing = (
        not signal.primary_source_available
        or signal.primary_evidence_count == ZERO
        or primary_evidence_age_seconds is None
    )
    if source_missing:
        detail_reasons.append(MISSING_PRIMARY_REASON)
    else:
        if primary_evidence_age_seconds >= config.block_stale_age_seconds:
            detail_reasons.append(STALE_BLOCK_REASON)
        elif primary_evidence_age_seconds > config.max_fresh_age_seconds:
            detail_reasons.append(STALE_WATCH_REASON)

    if signal.authority_score < config.authority_block_threshold:
        detail_reasons.append(AUTHORITY_BLOCK_REASON)
    elif signal.authority_score < config.authority_watch_threshold:
        detail_reasons.append(AUTHORITY_WATCH_REASON)

    if signal.corroborating_source_count == ZERO:
        detail_reasons.append(CORROBORATION_BLOCK_REASON)
    elif signal.corroborating_source_count < config.minimum_corroborating_source_count:
        detail_reasons.append(CORROBORATION_WATCH_REASON)

    if signal.access_success_ratio < config.access_block_threshold:
        detail_reasons.append(ACCESSIBILITY_BLOCK_REASON)
    elif signal.access_success_ratio < config.access_watch_threshold:
        detail_reasons.append(ACCESSIBILITY_WATCH_REASON)

    return tuple(sorted(detail_reasons))


def _status_from_detail_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(_is_block_detail_reason(reason_code) for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _status_reason_for_status(status: str) -> str:
    if status == STATUS_BLOCK:
        return BLOCK_REASON
    if status == STATUS_WATCH:
        return WATCH_REASON
    if status == STATUS_PASS:
        return PASS_REASON
    raise ValueError("status must be one of: pass, watch, block")


def _is_block_detail_reason(reason_code: str) -> bool:
    return reason_code == MISSING_PRIMARY_REASON or reason_code.endswith("_block")


def _report_status(
    rows: tuple[ResearchSourcePrimarySourceAvailabilityRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchSourcePrimarySourceAvailabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    detail_reasons = sorted(
        {
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code not in STATUS_REASON_CODES
        },
    )
    if detail_reasons:
        return tuple(detail_reasons)
    return (PASS_REASON,)


def _row_condition_count(
    rows: tuple[ResearchSourcePrimarySourceAvailabilityRow, ...],
    predicate: Any,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if predicate(row)))


def _row_has_fresh_primary_source(
    row: ResearchSourcePrimarySourceAvailabilityRow,
) -> bool:
    return (
        row.primary_source_available
        and MISSING_PRIMARY_REASON not in row.reason_codes
        and STALE_BLOCK_REASON not in row.reason_codes
        and STALE_WATCH_REASON not in row.reason_codes
    )


def _row_has_authoritative_primary_source(
    row: ResearchSourcePrimarySourceAvailabilityRow,
) -> bool:
    return (
        row.primary_source_available
        and AUTHORITY_BLOCK_REASON not in row.reason_codes
        and AUTHORITY_WATCH_REASON not in row.reason_codes
    )


def _row_has_corroborated_primary_source(
    row: ResearchSourcePrimarySourceAvailabilityRow,
) -> bool:
    return (
        row.primary_source_available
        and CORROBORATION_BLOCK_REASON not in row.reason_codes
        and CORROBORATION_WATCH_REASON not in row.reason_codes
    )


def _row_has_accessible_primary_source(
    row: ResearchSourcePrimarySourceAvailabilityRow,
) -> bool:
    return (
        row.primary_source_available
        and ACCESSIBILITY_BLOCK_REASON not in row.reason_codes
        and ACCESSIBILITY_WATCH_REASON not in row.reason_codes
    )


def _status_count(
    rows: tuple[ResearchSourcePrimarySourceAvailabilityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourcePrimarySourceAvailabilityRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_review_scopes: set[str] = set()
    for row in normalized:
        _require_exact_type("row", row, ResearchSourcePrimarySourceAvailabilityRow)
        require_paper_only_flags("row", row)
        if row.review_scope in seen_review_scopes:
            raise ValueError("rows review_scope values must be unique")
        seen_review_scopes.add(row.review_scope)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _row_sort_key(
    row: ResearchSourcePrimarySourceAvailabilityRow,
) -> tuple[int, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        row.strategy_review_readiness_score,
        row.review_scope,
    )


def _validate_row_consistency(
    row: ResearchSourcePrimarySourceAvailabilityRow,
) -> None:
    expected_status_reason = _status_reason_for_status(row.status)
    if row.reason_codes[0] != expected_status_reason:
        raise ValueError("reason_codes must begin with the matching status reason")
    if row.reason_codes[0] == PASS_REASON and len(row.reason_codes) != 1:
        raise ValueError("pass reason_codes must stand alone")
    if row.reason_codes[0] != PASS_REASON and len(row.reason_codes) == 1:
        raise ValueError("watch or block reason_codes require detail reasons")
    detail_reasons = row.reason_codes[1:]
    if row.status != _status_from_detail_reasons(detail_reasons):
        raise ValueError("status must match reason_codes")
    if (
        row.latest_primary_evidence_at is None
        and row.primary_evidence_age_seconds is not None
    ):
        raise ValueError(
            "primary_evidence_age_seconds must match latest_primary_evidence_at",
        )
    if (
        row.latest_primary_evidence_at is not None
        and row.primary_evidence_age_seconds is None
    ):
        raise ValueError(
            "primary_evidence_age_seconds must match latest_primary_evidence_at",
        )
    if not row.primary_source_available and row.freshness_score != ZERO:
        raise ValueError("freshness_score must be zero when primary source is absent")


def _validate_report_consistency(
    report: ResearchSourcePrimarySourceAvailabilityReport,
) -> None:
    for row in report.rows:
        if row.latest_primary_evidence_at is None:
            if row.primary_evidence_age_seconds is not None:
                raise ValueError(
                    "primary_evidence_age_seconds must match latest_primary_evidence_at",
                )
            continue
        expected_age_seconds = _duration_seconds(
            row.latest_primary_evidence_at,
            report.generated_at,
        )
        if row.primary_evidence_age_seconds != expected_age_seconds:
            raise ValueError("primary_evidence_age_seconds must match generated_at")

    expected_values = {
        "review_scope_count": _decimal_from_int(len(report.rows)),
        "available_primary_source_count": _decimal_from_int(
            sum(1 for row in report.rows if row.primary_source_available),
        ),
        "fresh_primary_source_count": _row_condition_count(
            report.rows,
            _row_has_fresh_primary_source,
        ),
        "authoritative_primary_source_count": _row_condition_count(
            report.rows,
            _row_has_authoritative_primary_source,
        ),
        "corroborated_primary_source_count": _row_condition_count(
            report.rows,
            _row_has_corroborated_primary_source,
        ),
        "accessible_primary_source_count": _row_condition_count(
            report.rows,
            _row_has_accessible_primary_source,
        ),
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
        "lowest_strategy_review_readiness_score": min(
            (row.strategy_review_readiness_score for row in report.rows),
            default=ZERO,
        ),
        "highest_primary_evidence_age_seconds": max(
            (
                row.primary_evidence_age_seconds
                for row in report.rows
                if row.primary_evidence_age_seconds is not None
            ),
            default=ZERO,
        ),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes("reason_codes", value)
    if reason_codes[0] not in STATUS_REASON_CODES:
        raise ValueError("row reason_codes must begin with a status reason")
    return reason_codes


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes("reason_codes", value)
    if any(reason_code in (WATCH_REASON, BLOCK_REASON) for reason_code in reason_codes):
        raise ValueError("report reason_codes must not contain row status reasons")
    return reason_codes


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must not be empty")
    seen_reason_codes: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen_reason_codes:
            raise ValueError(f"{name} values must be unique")
        seen_reason_codes.add(reason_code)
    return reason_codes


def _set_or_validate_digest(value: object, label: str) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    if current_digest == "":
        object.__setattr__(
            value,
            "derived_validation_digest",
            _derived_validation_digest(value, label),
        )
        return
    _require_digest("derived_validation_digest", current_digest)
    if current_digest != _derived_validation_digest(value, label):
        raise ValueError("derived_validation_digest does not match payload")


def _derived_validation_digest(value: object, label: str) -> str:
    ready_value = _json_ready_without_digest(value)
    _reject_unsafe_public_surface(f"{label} digest payload", ready_value)
    canonical_payload = json.dumps(
        ready_value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    ready = json_ready_no_floats(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    ready.pop("derived_validation_digest", None)
    return ready


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    started_at_utc = _as_utc("started_at", started_at)
    finished_at_utc = _as_utc("finished_at", finished_at)
    if finished_at_utc < started_at_utc:
        raise ValueError("duration seconds must be nonnegative")
    delta = finished_at_utc - started_at_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize(seconds)


def _decimal_from_int(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_count(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_count(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return _quantize_field(name, decimal_value)


def _optional_nonnegative_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(name, value)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize_field(name, decimal_value)


def _normalize_ratio(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize_field(name, decimal_value)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize_field(name: str, value: Decimal) -> Decimal:
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


def _optional_utc(name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(name, value)


def _require_exact_type(name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_canonical_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    return value


def _require_safe_public_string(name: str, value: object) -> str:
    normalized = _require_canonical_string(name, value)
    _reject_unsafe_public_string(name, normalized)
    return normalized


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be one of: pass, watch, block")


def _require_reason_code(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if value not in REASON_CODE_SET:
        raise ValueError(f"{name} must be a known reason code")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a 64-character hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be lowercase hex")


def _require_watch_block_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if watch_value <= block_value:
        raise ValueError(f"{watch_name} must exceed {block_name}")


def _reject_unsafe_public_surface(label: str, payload: object) -> None:
    for key, value in _iter_public_items(payload):
        _reject_unsafe_public_string(f"{label}.{key}", key)
        if type(value) is str:
            _reject_unsafe_public_string(f"{label}.{key}", value)


def _reject_unsafe_public_string(name: str, value: str) -> None:
    lowered_value = value.lower()
    if AUTH_SURFACE_PATTERN.search(lowered_value) or any(
        fragment in lowered_value for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS
    ):
        raise ValueError(f"{name} exposes unsafe public surface")


def _iter_public_items(payload: object) -> tuple[tuple[str, object], ...]:
    if is_dataclass(payload) and not isinstance(payload, type):
        return _iter_public_items(asdict(payload))
    if isinstance(payload, dict):
        items: list[tuple[str, object]] = []
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append((key, value))
            items.extend(_iter_public_items(value))
        return tuple(items)
    if isinstance(payload, (list, tuple)):
        items = []
        for value in payload:
            items.extend(_iter_public_items(value))
        return tuple(items)
    return ()
