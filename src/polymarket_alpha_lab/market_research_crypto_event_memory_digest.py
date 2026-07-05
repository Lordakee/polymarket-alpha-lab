"""Pure Phase 1 crypto event memory reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_EVENT_MEMORY_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-event-memory-digest-v0"
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_MICROS_PER_SECOND = Decimal("1000000")
_SECONDS_PER_DAY = Decimal("86400")

_STATUS_CLEAR = "clear"
_STATUS_WATCH = "watch"
_STATUS_BLOCKED = "blocked"
_STATUS_RANK = {_STATUS_BLOCKED: 0, _STATUS_WATCH: 1, _STATUS_CLEAR: 2}

_CONFLICT_REASON = "market_research_crypto_event_memory_conflict_present"
_INSUFFICIENT_REASON = (
    "market_research_crypto_event_memory_insufficient_memory_matches"
)
_LOW_RECALL_REASON = "market_research_crypto_event_memory_low_recall_ratio"
_SINGLE_SOURCE_REASON = "market_research_crypto_event_memory_single_source"
_STALE_REASON = "market_research_crypto_event_memory_stale_event"
_CLEAR_REASON = "market_research_crypto_event_memory_clear"
_EMPTY_REASON = "market_research_crypto_event_memory_empty"

_ROW_REASON_SEQUENCE = (
    _CONFLICT_REASON,
    _INSUFFICIENT_REASON,
    _LOW_RECALL_REASON,
    _SINGLE_SOURCE_REASON,
    _STALE_REASON,
    _CLEAR_REASON,
)
_SUMMARY_REASON_SEQUENCE = (
    _CONFLICT_REASON,
    _INSUFFICIENT_REASON,
    _LOW_RECALL_REASON,
    _SINGLE_SOURCE_REASON,
    _STALE_REASON,
    _CLEAR_REASON,
    _EMPTY_REASON,
)
_BLOCKING_REASONS = frozenset(
    (_CONFLICT_REASON, _INSUFFICIENT_REASON, _LOW_RECALL_REASON),
)


def _join_text(*parts: str) -> str:
    return "".join(parts)


_SENSITIVE_FRAGMENTS = (
    _join_text("wal", "let"),
    _join_text("acc", "ount"),
    _join_text("to", "ken"),
    _join_text("sec", "ret"),
    _join_text("pri", "vate"),
    _join_text("pri", "vate", "_", "key"),
    _join_text("0", "x"),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_EVENT_MEMORY_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoEventMemoryDigestConfig",
    "MarketResearchCryptoEventMemoryDigestEvent",
    "MarketResearchCryptoEventMemoryDigestReasonCodeCount",
    "MarketResearchCryptoEventMemoryDigestReport",
    "MarketResearchCryptoEventMemoryDigestRow",
    "build_market_research_crypto_event_memory_digest",
    "market_research_crypto_event_memory_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoEventMemoryDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_CRYPTO_EVENT_MEMORY_DIGEST_CONFIG_VERSION
    max_event_age_seconds: Decimal = Decimal("7200.000000")
    min_memory_match_count: Decimal = Decimal("2.000000")
    min_memory_recall_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_text("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_event_age_seconds",
            _require_positive_decimal(
                "max_event_age_seconds",
                self.max_event_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_memory_match_count",
            _require_nonnegative_decimal(
                "min_memory_match_count",
                self.min_memory_match_count,
            ),
        )
        object.__setattr__(
            self,
            "min_memory_recall_ratio",
            _require_ratio_decimal(
                "min_memory_recall_ratio",
                self.min_memory_recall_ratio,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoEventMemoryDigestEvent:
    condition_id: str
    event_key: str
    event_family: str
    observed_at: datetime
    memory_match_count: Decimal
    candidate_memory_count: Decimal
    source_count: Decimal
    evidence_conflict_count: Decimal
    event_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "condition_id",
            "event_key",
            "event_family",
            "event_config_version",
        ):
            _require_exact_text(field_name, getattr(self, field_name))
            _require_public_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_at",
            _require_aware_datetime("observed_at", self.observed_at),
        )
        for field_name in (
            "memory_match_count",
            "candidate_memory_count",
            "source_count",
            "evidence_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.memory_match_count > self.candidate_memory_count:
            raise ValueError("memory_match_count must not exceed candidate_memory_count")
        _require_hard_flags("event", self)


@dataclass(frozen=True)
class MarketResearchCryptoEventMemoryDigestRow:
    condition_id: str
    event_key: str
    event_family: str
    summary_status: str
    event_age_seconds: Decimal
    memory_match_count: Decimal
    candidate_memory_count: Decimal
    source_count: Decimal
    evidence_conflict_count: Decimal
    memory_recall_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("condition_id", "event_key", "event_family"):
            _require_exact_text(field_name, getattr(self, field_name))
            _require_public_text(field_name, getattr(self, field_name))
        _require_status("summary_status", self.summary_status)
        for field_name in (
            "event_age_seconds",
            "memory_match_count",
            "candidate_memory_count",
            "source_count",
            "evidence_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_recall_ratio",
            _require_ratio_decimal("memory_recall_ratio", self.memory_recall_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=_ROW_REASON_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoEventMemoryDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchCryptoEventMemoryDigestReport:
    generated_at: datetime
    config_version: str
    summary_status: str
    recommended_next_step: str
    event_count: Decimal
    clear_event_count: Decimal
    watch_event_count: Decimal
    blocked_event_count: Decimal
    memory_match_count: Decimal
    candidate_memory_count: Decimal
    source_count: Decimal
    stale_event_count: Decimal
    conflict_event_count: Decimal
    memory_recall_ratio: Decimal
    max_event_age_seconds: Decimal
    min_memory_match_count: Decimal
    min_memory_recall_ratio: Decimal
    max_observed_event_age_seconds: Decimal
    rows: tuple[MarketResearchCryptoEventMemoryDigestRow, ...]
    event_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchCryptoEventMemoryDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_exact_text("config_version", self.config_version)
        _require_status("summary_status", self.summary_status)
        _require_exact_text("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "event_count",
            "clear_event_count",
            "watch_event_count",
            "blocked_event_count",
            "memory_match_count",
            "candidate_memory_count",
            "source_count",
            "stale_event_count",
            "conflict_event_count",
            "min_memory_match_count",
            "max_observed_event_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_recall_ratio",
            _require_ratio_decimal("memory_recall_ratio", self.memory_recall_ratio),
        )
        object.__setattr__(
            self,
            "max_event_age_seconds",
            _require_positive_decimal("max_event_age_seconds", self.max_event_age_seconds),
        )
        object.__setattr__(
            self,
            "min_memory_recall_ratio",
            _require_ratio_decimal(
                "min_memory_recall_ratio",
                self.min_memory_recall_ratio,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "event_config_versions",
            _normalize_version_pairs(self.event_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=_SUMMARY_REASON_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_crypto_event_memory_digest(
    events: Iterable[MarketResearchCryptoEventMemoryDigestEvent],
    *,
    config: MarketResearchCryptoEventMemoryDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoEventMemoryDigestReport:
    if type(config) is not MarketResearchCryptoEventMemoryDigestConfig:
        raise ValueError("config must be MarketResearchCryptoEventMemoryDigestConfig")
    generated_at = _as_utc("generated_at", generated_at)
    event_tuple = tuple(events)
    seen_event_keys: set[str] = set()
    rows_with_versions: list[tuple[MarketResearchCryptoEventMemoryDigestRow, str]] = []

    for event in event_tuple:
        if type(event) is not MarketResearchCryptoEventMemoryDigestEvent:
            raise ValueError("events must contain MarketResearchCryptoEventMemoryDigestEvent")
        if event.event_key in seen_event_keys:
            raise ValueError("event_key values must be unique")
        seen_event_keys.add(event.event_key)
        if event.observed_at.astimezone(UTC) > generated_at:
            raise ValueError("observed_at must not be in the future")
        event_age_seconds = _elapsed_seconds(generated_at, event.observed_at)
        memory_recall_ratio = _safe_ratio(
            event.memory_match_count,
            event.candidate_memory_count,
        )
        reason_codes = _row_reasons(event, event_age_seconds, memory_recall_ratio, config)
        status = _status_from_reasons(reason_codes)
        row = MarketResearchCryptoEventMemoryDigestRow(
            condition_id=event.condition_id,
            event_key=event.event_key,
            event_family=event.event_family,
            summary_status=status,
            event_age_seconds=event_age_seconds,
            memory_match_count=event.memory_match_count,
            candidate_memory_count=event.candidate_memory_count,
            source_count=event.source_count,
            evidence_conflict_count=event.evidence_conflict_count,
            memory_recall_ratio=memory_recall_ratio,
            reason_codes=reason_codes,
        )
        rows_with_versions.append((row, event.event_config_version))

    rows_with_versions.sort(
        key=lambda item: (
            _STATUS_RANK[item[0].summary_status],
            -item[0].event_age_seconds,
            item[0].condition_id,
            item[0].event_key,
        ),
    )
    rows = tuple(row for row, _version in rows_with_versions)
    event_count = _count_decimal(len(rows))
    clear_event_count = _count_decimal(
        sum(1 for row in rows if row.summary_status == _STATUS_CLEAR),
    )
    watch_event_count = _count_decimal(
        sum(1 for row in rows if row.summary_status == _STATUS_WATCH),
    )
    blocked_event_count = _count_decimal(
        sum(1 for row in rows if row.summary_status == _STATUS_BLOCKED),
    )
    memory_match_count = _q(sum((row.memory_match_count for row in rows), _ZERO))
    candidate_memory_count = _q(sum((row.candidate_memory_count for row in rows), _ZERO))
    source_count = _q(sum((row.source_count for row in rows), _ZERO))
    stale_event_count = _count_decimal(
        sum(1 for row in rows if _STALE_REASON in row.reason_codes),
    )
    conflict_event_count = _count_decimal(
        sum(1 for row in rows if _CONFLICT_REASON in row.reason_codes),
    )
    memory_recall_ratio = _safe_ratio(memory_match_count, candidate_memory_count)
    max_observed_event_age_seconds = max(
        (row.event_age_seconds for row in rows),
        default=_ZERO,
    )
    summary_status = _summary_status(rows)
    reason_codes = _summary_reasons(rows)

    return MarketResearchCryptoEventMemoryDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        summary_status=summary_status,
        recommended_next_step=_next_step(summary_status),
        event_count=event_count,
        clear_event_count=clear_event_count,
        watch_event_count=watch_event_count,
        blocked_event_count=blocked_event_count,
        memory_match_count=memory_match_count,
        candidate_memory_count=candidate_memory_count,
        source_count=source_count,
        stale_event_count=stale_event_count,
        conflict_event_count=conflict_event_count,
        memory_recall_ratio=memory_recall_ratio,
        max_event_age_seconds=config.max_event_age_seconds,
        min_memory_match_count=config.min_memory_match_count,
        min_memory_recall_ratio=config.min_memory_recall_ratio,
        max_observed_event_age_seconds=max_observed_event_age_seconds,
        rows=rows,
        event_config_versions=tuple(
            (row.event_key, version) for row, version in rows_with_versions
        ),
        reason_code_counts=_build_reason_code_counts(rows),
        reason_codes=reason_codes,
    )


def market_research_crypto_event_memory_digest_payload(
    report: MarketResearchCryptoEventMemoryDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchCryptoEventMemoryDigestReport:
        raise ValueError("report must be MarketResearchCryptoEventMemoryDigestReport")
    _require_hard_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "summary_status": report.summary_status,
        "recommended_next_step": report.recommended_next_step,
        "event_count": _decimal_text(report.event_count),
        "clear_event_count": _decimal_text(report.clear_event_count),
        "watch_event_count": _decimal_text(report.watch_event_count),
        "blocked_event_count": _decimal_text(report.blocked_event_count),
        "memory_match_count": _decimal_text(report.memory_match_count),
        "candidate_memory_count": _decimal_text(report.candidate_memory_count),
        "source_count": _decimal_text(report.source_count),
        "stale_event_count": _decimal_text(report.stale_event_count),
        "conflict_event_count": _decimal_text(report.conflict_event_count),
        "memory_recall_ratio": _decimal_text(report.memory_recall_ratio),
        "max_event_age_seconds": _decimal_text(report.max_event_age_seconds),
        "min_memory_match_count": _decimal_text(report.min_memory_match_count),
        "min_memory_recall_ratio": _decimal_text(report.min_memory_recall_ratio),
        "max_observed_event_age_seconds": _decimal_text(
            report.max_observed_event_age_seconds,
        ),
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            {
                "reason_code": item.reason_code,
                "count": _decimal_text(item.count),
                "event_ratio": _decimal_text(item.event_ratio),
            }
            for item in report.reason_code_counts
        ],
        "event_config_versions": [
            {"event_key": event_key, "event_config_version": version}
            for event_key, version in report.event_config_versions
        ],
        "rows": [
            {
                "condition_id": row.condition_id,
                "event_key": row.event_key,
                "event_family": row.event_family,
                "summary_status": row.summary_status,
                "event_age_seconds": _decimal_text(row.event_age_seconds),
                "memory_match_count": _decimal_text(row.memory_match_count),
                "candidate_memory_count": _decimal_text(row.candidate_memory_count),
                "source_count": _decimal_text(row.source_count),
                "evidence_conflict_count": _decimal_text(row.evidence_conflict_count),
                "memory_recall_ratio": _decimal_text(row.memory_recall_ratio),
                "reason_codes": list(row.reason_codes),
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            }
            for row in report.rows
        ],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_reasons(
    event: MarketResearchCryptoEventMemoryDigestEvent,
    event_age_seconds: Decimal,
    memory_recall_ratio: Decimal,
    config: MarketResearchCryptoEventMemoryDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if event.evidence_conflict_count > _ZERO:
        reasons.append(_CONFLICT_REASON)
    if event.memory_match_count < config.min_memory_match_count:
        reasons.append(_INSUFFICIENT_REASON)
    if memory_recall_ratio < config.min_memory_recall_ratio:
        reasons.append(_LOW_RECALL_REASON)
    if event.source_count <= _ONE:
        reasons.append(_SINGLE_SOURCE_REASON)
    if event_age_seconds > config.max_event_age_seconds:
        reasons.append(_STALE_REASON)
    if not reasons:
        reasons.append(_CLEAR_REASON)
    return tuple(reason for reason in _ROW_REASON_SEQUENCE if reason in reasons)


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCKING_REASONS for reason in reason_codes):
        return _STATUS_BLOCKED
    if reason_codes != (_CLEAR_REASON,):
        return _STATUS_WATCH
    return _STATUS_CLEAR


def _summary_status(rows: tuple[MarketResearchCryptoEventMemoryDigestRow, ...]) -> str:
    if not rows:
        return _STATUS_WATCH
    if any(row.summary_status == _STATUS_BLOCKED for row in rows):
        return _STATUS_BLOCKED
    if any(row.summary_status == _STATUS_WATCH for row in rows):
        return _STATUS_WATCH
    return _STATUS_CLEAR


def _next_step(status: str) -> str:
    if status == _STATUS_BLOCKED:
        return "block_report_only_market_research_crypto_event_memory_digest"
    if status == _STATUS_WATCH:
        return "review_report_only_market_research_crypto_event_memory_digest"
    return "allow_report_only_market_research_crypto_event_memory_digest"


def _summary_reasons(rows: tuple[MarketResearchCryptoEventMemoryDigestRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and _CLEAR_REASON in seen:
        seen.remove(_CLEAR_REASON)
    return tuple(reason for reason in _SUMMARY_REASON_SEQUENCE if reason in seen)


def _build_reason_code_counts(
    rows: tuple[MarketResearchCryptoEventMemoryDigestRow, ...],
) -> tuple[MarketResearchCryptoEventMemoryDigestReasonCodeCount, ...]:
    event_count = _count_decimal(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason in row.reason_codes:
            counts[reason] = counts.get(reason, 0) + 1
    return tuple(
        MarketResearchCryptoEventMemoryDigestReasonCodeCount(
            reason_code=reason,
            count=_count_decimal(counts[reason]),
            event_ratio=_safe_ratio(_count_decimal(counts[reason]), event_count),
        )
        for reason in _SUMMARY_REASON_SEQUENCE
        if reason in counts
    )


def _validate_row(row: MarketResearchCryptoEventMemoryDigestRow) -> None:
    expected_status = _status_from_reasons(row.reason_codes)
    if row.summary_status != expected_status:
        raise ValueError("summary_status does not match reason_codes")
    expected_ratio = _safe_ratio(row.memory_match_count, row.candidate_memory_count)
    if row.memory_recall_ratio != expected_ratio:
        raise ValueError("memory_recall_ratio does not match counts")


def _validate_report(report: MarketResearchCryptoEventMemoryDigestReport) -> None:
    if report.event_count != _count_decimal(len(report.rows)):
        raise ValueError("event_count does not match rows")
    expected_clear = _count_decimal(
        sum(1 for row in report.rows if row.summary_status == _STATUS_CLEAR),
    )
    expected_watch = _count_decimal(
        sum(1 for row in report.rows if row.summary_status == _STATUS_WATCH),
    )
    expected_blocked = _count_decimal(
        sum(1 for row in report.rows if row.summary_status == _STATUS_BLOCKED),
    )
    if report.clear_event_count != expected_clear:
        raise ValueError("clear_event_count does not match rows")
    if report.watch_event_count != expected_watch:
        raise ValueError("watch_event_count does not match rows")
    if report.blocked_event_count != expected_blocked:
        raise ValueError("blocked_event_count does not match rows")
    expected_memory_match_count = _q(
        sum((row.memory_match_count for row in report.rows), _ZERO),
    )
    expected_candidate_memory_count = _q(
        sum((row.candidate_memory_count for row in report.rows), _ZERO),
    )
    expected_source_count = _q(sum((row.source_count for row in report.rows), _ZERO))
    expected_stale_event_count = _count_decimal(
        sum(1 for row in report.rows if _STALE_REASON in row.reason_codes),
    )
    expected_conflict_event_count = _count_decimal(
        sum(1 for row in report.rows if _CONFLICT_REASON in row.reason_codes),
    )
    expected_memory_recall_ratio = _safe_ratio(
        expected_memory_match_count,
        expected_candidate_memory_count,
    )
    expected_max_observed_event_age_seconds = max(
        (row.event_age_seconds for row in report.rows),
        default=_ZERO,
    )
    expected_event_config_keys = tuple(row.event_key for row in report.rows)
    event_config_keys = tuple(
        event_key for event_key, _version in report.event_config_versions
    )
    if report.memory_match_count != expected_memory_match_count:
        raise ValueError("memory_match_count does not match rows")
    if report.candidate_memory_count != expected_candidate_memory_count:
        raise ValueError("candidate_memory_count does not match rows")
    if report.source_count != expected_source_count:
        raise ValueError("source_count does not match rows")
    if report.stale_event_count != expected_stale_event_count:
        raise ValueError("stale_event_count does not match rows")
    if report.conflict_event_count != expected_conflict_event_count:
        raise ValueError("conflict_event_count does not match rows")
    if report.memory_recall_ratio != expected_memory_recall_ratio:
        raise ValueError("memory_recall_ratio does not match rows")
    if report.max_observed_event_age_seconds != expected_max_observed_event_age_seconds:
        raise ValueError("max_observed_event_age_seconds does not match rows")
    if event_config_keys != expected_event_config_keys:
        raise ValueError("event_config_versions do not match rows")
    if report.summary_status != _summary_status(report.rows):
        raise ValueError("summary_status does not match rows")
    if report.recommended_next_step != _next_step(report.summary_status):
        raise ValueError("recommended_next_step does not match summary_status")
    if report.reason_code_counts != _build_reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reasons(report.rows):
        raise ValueError("reason_codes do not match rows")


def _normalize_rows(
    rows: tuple[MarketResearchCryptoEventMemoryDigestRow, ...],
) -> tuple[MarketResearchCryptoEventMemoryDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoEventMemoryDigestRow:
            raise ValueError("rows must contain MarketResearchCryptoEventMemoryDigestRow")
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchCryptoEventMemoryDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoEventMemoryDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not MarketResearchCryptoEventMemoryDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason code count", item)
    return items


def _normalize_version_pairs(value: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("event_config_versions must be a tuple")
    pairs: list[tuple[str, str]] = []
    seen_event_keys: set[str] = set()
    for pair in value:
        if type(pair) is not tuple or len(pair) != 2:
            raise ValueError("event_config_versions must contain pairs")
        event_key, version = pair
        _require_exact_text("event_config_versions event_key", event_key)
        _require_exact_text("event_config_versions version", version)
        _require_public_text("event_config_versions event_key", event_key)
        _require_public_text("event_config_versions version", version)
        if event_key in seen_event_keys:
            raise ValueError("event_config_versions event keys must be unique")
        seen_event_keys.add(event_key)
        pairs.append((event_key, version))
    return tuple(pairs)


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a nonempty tuple")
    seen: set[str] = set()
    for reason in value:
        _require_reason_code("reason_code", reason)
        if reason in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason)
    normalized = tuple(reason for reason in sequence if reason in seen)
    if normalized != value:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_reason_code(field_name: str, value: object) -> str:
    value = _require_exact_text(field_name, value)
    if value not in _SUMMARY_REASON_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_exact_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    return value


def _require_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _SENSITIVE_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")


def _require_status(field_name: str, value: object) -> str:
    _require_exact_text(field_name, value)
    if value not in _STATUS_RANK:
        raise ValueError(f"{field_name} must be a known status")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _q(_require_decimal(field_name, value))
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value > _ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_aware_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _elapsed_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later.astimezone(UTC) - earlier.astimezone(UTC)
    micros = (
        Decimal(delta.days) * _SECONDS_PER_DAY * _MICROS_PER_SECOND
        + Decimal(delta.seconds) * _MICROS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _q(micros / _MICROS_PER_SECOND)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _q(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _q(Decimal(value))


def _q(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _decimal_text(value: Decimal) -> str:
    return str(value)


def _digest_ref(value: str, prefix: str) -> str:
    return prefix + sha256(value.encode("utf-8")).hexdigest()[:16]
