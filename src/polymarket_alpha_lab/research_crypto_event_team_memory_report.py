"""Pure report-only crypto event team memory readiness reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_CRYPTO_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION = (
    "research-crypto-event-team-memory-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")

_STATUS_PASS = "pass"
_STATUS_WATCH = "watch"
_STATUS_BLOCK = "block"
_STATUS_RANK = {_STATUS_BLOCK: 0, _STATUS_WATCH: 1, _STATUS_PASS: 2}

_READY_REASON = "crypto_event_team_memory_ready"
_NO_INPUTS_REASON = "crypto_event_team_memory_report_no_inputs"
_REPORT_PASS_REASON = "crypto_event_team_memory_report_pass"
_REPORT_WATCH_REASON = "crypto_event_team_memory_report_watch"
_REPORT_BLOCK_REASON = "crypto_event_team_memory_report_block"
_MEMORY_QUALITY_BLOCK_REASON = "memory_quality_block"
_MEMORY_RECENCY_BLOCK_REASON = "memory_recency_block"
_CASE_COVERAGE_BLOCK_REASON = "case_coverage_block"
_MEMORY_GAP_BLOCK_REASON = "memory_gap_block"
_SCREENING_SUPPORT_BLOCK_REASON = "screening_support_block"
_MEMORY_QUALITY_WATCH_REASON = "memory_quality_watch"
_MEMORY_RECENCY_WATCH_REASON = "memory_recency_watch"
_CASE_COVERAGE_WATCH_REASON = "case_coverage_watch"
_MEMORY_GAP_WATCH_REASON = "memory_gap_watch"
_SCREENING_SUPPORT_WATCH_REASON = "screening_support_watch"

_ROW_REASON_SEQUENCE = (
    _MEMORY_QUALITY_BLOCK_REASON,
    _MEMORY_RECENCY_BLOCK_REASON,
    _CASE_COVERAGE_BLOCK_REASON,
    _MEMORY_GAP_BLOCK_REASON,
    _SCREENING_SUPPORT_BLOCK_REASON,
    _MEMORY_QUALITY_WATCH_REASON,
    _MEMORY_RECENCY_WATCH_REASON,
    _CASE_COVERAGE_WATCH_REASON,
    _MEMORY_GAP_WATCH_REASON,
    _SCREENING_SUPPORT_WATCH_REASON,
    _READY_REASON,
)
_SUMMARY_REASON_SEQUENCE = (
    _REPORT_BLOCK_REASON,
    _REPORT_WATCH_REASON,
    _REPORT_PASS_REASON,
    _NO_INPUTS_REASON,
    _MEMORY_QUALITY_BLOCK_REASON,
    _MEMORY_RECENCY_BLOCK_REASON,
    _CASE_COVERAGE_BLOCK_REASON,
    _MEMORY_GAP_BLOCK_REASON,
    _SCREENING_SUPPORT_BLOCK_REASON,
    _MEMORY_QUALITY_WATCH_REASON,
    _MEMORY_RECENCY_WATCH_REASON,
    _CASE_COVERAGE_WATCH_REASON,
    _MEMORY_GAP_WATCH_REASON,
    _SCREENING_SUPPORT_WATCH_REASON,
    _READY_REASON,
)
_REASON_COUNT_SEQUENCE = _ROW_REASON_SEQUENCE
_BLOCK_REASONS = frozenset(
    (
        _MEMORY_QUALITY_BLOCK_REASON,
        _MEMORY_RECENCY_BLOCK_REASON,
        _CASE_COVERAGE_BLOCK_REASON,
        _MEMORY_GAP_BLOCK_REASON,
        _SCREENING_SUPPORT_BLOCK_REASON,
    ),
)

_UNSAFE_PUBLIC_FRAGMENTS = (
    "identifier",
    "condition",
    "slug",
    "source",
    "url",
    "http",
    "market",
    "wallet",
    "order",
    "trade",
    "live",
    "database",
    "network",
    "raw",
    "text",
)

__all__ = (
    "DEFAULT_RESEARCH_CRYPTO_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION",
    "ResearchCryptoEventTeamMemoryReasonCodeCount",
    "ResearchCryptoEventTeamMemoryReport",
    "ResearchCryptoEventTeamMemoryReportConfig",
    "ResearchCryptoEventTeamMemoryRow",
    "ResearchCryptoEventTeamMemorySignal",
    "build_research_crypto_event_team_memory_report",
    "research_crypto_event_team_memory_report_payload",
)


@dataclass(frozen=True)
class ResearchCryptoEventTeamMemoryReportConfig:
    config_version: str = DEFAULT_RESEARCH_CRYPTO_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
    pass_min_memory_quality_score: Decimal = Decimal("0.850000")
    watch_min_memory_quality_score: Decimal = Decimal("0.650000")
    pass_max_memory_age_seconds: Decimal = Decimal("86400.000000")
    watch_max_memory_age_seconds: Decimal = Decimal("604800.000000")
    pass_min_recent_case_coverage_ratio: Decimal = Decimal("0.800000")
    watch_min_recent_case_coverage_ratio: Decimal = Decimal("0.550000")
    watch_max_unresolved_memory_gap_count: Decimal = Decimal("1.000000")
    block_max_unresolved_memory_gap_count: Decimal = Decimal("3.000000")
    pass_min_screening_support_score: Decimal = Decimal("0.800000")
    watch_min_screening_support_score: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_min_memory_quality_score",
            "watch_min_memory_quality_score",
            "pass_min_recent_case_coverage_ratio",
            "watch_min_recent_case_coverage_ratio",
            "pass_min_screening_support_score",
            "watch_min_screening_support_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_max_memory_age_seconds",
            "watch_max_memory_age_seconds",
            "watch_max_unresolved_memory_gap_count",
            "block_max_unresolved_memory_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_memory_quality_score < self.watch_min_memory_quality_score:
            raise ValueError(
                "pass_min_memory_quality_score must be at least "
                "watch_min_memory_quality_score",
            )
        if self.pass_min_recent_case_coverage_ratio < (
            self.watch_min_recent_case_coverage_ratio
        ):
            raise ValueError(
                "pass_min_recent_case_coverage_ratio must be at least "
                "watch_min_recent_case_coverage_ratio",
            )
        if self.pass_min_screening_support_score < self.watch_min_screening_support_score:
            raise ValueError(
                "pass_min_screening_support_score must be at least "
                "watch_min_screening_support_score",
            )
        if self.pass_max_memory_age_seconds > self.watch_max_memory_age_seconds:
            raise ValueError(
                "pass_max_memory_age_seconds must not exceed "
                "watch_max_memory_age_seconds",
            )
        if self.watch_max_unresolved_memory_gap_count > (
            self.block_max_unresolved_memory_gap_count
        ):
            raise ValueError(
                "watch_max_unresolved_memory_gap_count must not exceed "
                "block_max_unresolved_memory_gap_count",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCryptoEventTeamMemorySignal:
    crypto_event_label: str
    specialist_memory_quality_score: Decimal
    latest_memory_age_seconds: Decimal
    recent_case_coverage_ratio: Decimal
    unresolved_memory_gap_count: Decimal
    screening_support_score: Decimal
    screened_case_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("crypto_event_label", self.crypto_event_label)
        for field_name in (
            "specialist_memory_quality_score",
            "recent_case_coverage_ratio",
            "screening_support_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_memory_age_seconds",
            "unresolved_memory_gap_count",
            "screened_case_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("memory signal", self)


@dataclass(frozen=True)
class ResearchCryptoEventTeamMemoryRow:
    crypto_event_label: str
    memory_status: str
    specialist_memory_quality_score: Decimal
    latest_memory_age_seconds: Decimal
    recent_case_coverage_ratio: Decimal
    unresolved_memory_gap_count: Decimal
    screening_support_score: Decimal
    screened_case_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("crypto_event_label", self.crypto_event_label)
        _require_status("memory_status", self.memory_status)
        for field_name in (
            "specialist_memory_quality_score",
            "recent_case_coverage_ratio",
            "screening_support_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_memory_age_seconds",
            "unresolved_memory_gap_count",
            "screened_case_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=_ROW_REASON_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchCryptoEventTeamMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchCryptoEventTeamMemoryReport:
    generated_at: datetime
    config_version: str
    report_status: str
    memory_quality_status: str
    memory_recency_status: str
    case_coverage_status: str
    memory_gap_status: str
    screening_support_status: str
    memory_signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_memory_quality_score: Decimal
    average_recent_case_coverage_ratio: Decimal
    unresolved_memory_gap_count: Decimal
    max_memory_age_seconds: Decimal
    screened_case_count: Decimal
    rows: tuple[ResearchCryptoEventTeamMemoryRow, ...]
    reason_code_counts: tuple[ResearchCryptoEventTeamMemoryReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "report_status",
            "memory_quality_status",
            "memory_recency_status",
            "case_coverage_status",
            "memory_gap_status",
            "screening_support_status",
        ):
            _require_status(field_name, getattr(self, field_name))
        for field_name in (
            "memory_signal_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_memory_gap_count",
            "max_memory_age_seconds",
            "screened_case_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_memory_quality_score",
            "average_recent_case_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(self.reason_codes, sequence=_SUMMARY_REASON_SEQUENCE),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _verify_report_digest(self)


def build_research_crypto_event_team_memory_report(
    signals: Iterable[ResearchCryptoEventTeamMemorySignal],
    *,
    config: ResearchCryptoEventTeamMemoryReportConfig,
    generated_at: datetime,
) -> ResearchCryptoEventTeamMemoryReport:
    if type(config) is not ResearchCryptoEventTeamMemoryReportConfig:
        raise ValueError("config must be ResearchCryptoEventTeamMemoryReportConfig")
    generated_at = _as_utc("generated_at", generated_at)
    rows: list[ResearchCryptoEventTeamMemoryRow] = []
    seen_labels: set[str] = set()

    for signal in tuple(signals):
        if type(signal) is not ResearchCryptoEventTeamMemorySignal:
            raise ValueError("signals must contain ResearchCryptoEventTeamMemorySignal")
        if signal.crypto_event_label in seen_labels:
            raise ValueError("crypto_event_label values must be unique")
        seen_labels.add(signal.crypto_event_label)
        reasons = _row_reason_codes(signal, config)
        rows.append(
            ResearchCryptoEventTeamMemoryRow(
                crypto_event_label=signal.crypto_event_label,
                memory_status=_status_from_reason_codes(reasons),
                specialist_memory_quality_score=signal.specialist_memory_quality_score,
                latest_memory_age_seconds=signal.latest_memory_age_seconds,
                recent_case_coverage_ratio=signal.recent_case_coverage_ratio,
                unresolved_memory_gap_count=signal.unresolved_memory_gap_count,
                screening_support_score=signal.screening_support_score,
                screened_case_count=signal.screened_case_count,
                reason_codes=reasons,
            ),
        )

    row_tuple = tuple(sorted(rows, key=_row_sort_key))
    report_values = _report_values(
        rows=row_tuple,
        config=config,
        generated_at=generated_at,
    )
    report_values["derived_validation_digest"] = _digest_payload(
        _json_ready(report_values),
    )
    return ResearchCryptoEventTeamMemoryReport(**report_values)


def research_crypto_event_team_memory_report_payload(
    report: ResearchCryptoEventTeamMemoryReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchCryptoEventTeamMemoryReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("public payload", report)
        _reject_public_numerics(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchCryptoEventTeamMemoryReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("public payload", _DictFlags(payload))
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numerics(payload)
    _verify_public_payload_digest(payload)
    return payload


def _report_values(
    *,
    rows: tuple[ResearchCryptoEventTeamMemoryRow, ...],
    config: ResearchCryptoEventTeamMemoryReportConfig,
    generated_at: datetime,
) -> dict[str, Any]:
    signal_count = _count_decimal(len(rows))
    pass_count = _count_decimal(sum(1 for row in rows if row.memory_status == _STATUS_PASS))
    watch_count = _count_decimal(
        sum(1 for row in rows if row.memory_status == _STATUS_WATCH),
    )
    block_count = _count_decimal(
        sum(1 for row in rows if row.memory_status == _STATUS_BLOCK),
    )
    average_quality = _safe_ratio(
        _q(sum((row.specialist_memory_quality_score for row in rows), _ZERO)),
        signal_count,
    )
    average_case_coverage = _safe_ratio(
        _q(sum((row.recent_case_coverage_ratio for row in rows), _ZERO)),
        signal_count,
    )
    unresolved_gap_count = _q(
        sum((row.unresolved_memory_gap_count for row in rows), _ZERO),
    )
    max_memory_age = max(
        (row.latest_memory_age_seconds for row in rows),
        default=_ZERO,
    )
    screened_case_count = _q(sum((row.screened_case_count for row in rows), _ZERO))
    reason_codes = _summary_reason_codes(rows)

    return {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _summary_status(rows),
        "memory_quality_status": _metric_status(
            rows,
            block_reason=_MEMORY_QUALITY_BLOCK_REASON,
            watch_reason=_MEMORY_QUALITY_WATCH_REASON,
        ),
        "memory_recency_status": _metric_status(
            rows,
            block_reason=_MEMORY_RECENCY_BLOCK_REASON,
            watch_reason=_MEMORY_RECENCY_WATCH_REASON,
        ),
        "case_coverage_status": _metric_status(
            rows,
            block_reason=_CASE_COVERAGE_BLOCK_REASON,
            watch_reason=_CASE_COVERAGE_WATCH_REASON,
        ),
        "memory_gap_status": _metric_status(
            rows,
            block_reason=_MEMORY_GAP_BLOCK_REASON,
            watch_reason=_MEMORY_GAP_WATCH_REASON,
        ),
        "screening_support_status": _metric_status(
            rows,
            block_reason=_SCREENING_SUPPORT_BLOCK_REASON,
            watch_reason=_SCREENING_SUPPORT_WATCH_REASON,
        ),
        "memory_signal_count": signal_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "average_memory_quality_score": average_quality,
        "average_recent_case_coverage_ratio": average_case_coverage,
        "unresolved_memory_gap_count": unresolved_gap_count,
        "max_memory_age_seconds": max_memory_age,
        "screened_case_count": screened_case_count,
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_reason_codes(
    signal: ResearchCryptoEventTeamMemorySignal,
    config: ResearchCryptoEventTeamMemoryReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if signal.specialist_memory_quality_score < config.watch_min_memory_quality_score:
        reasons.append(_MEMORY_QUALITY_BLOCK_REASON)
    elif signal.specialist_memory_quality_score < config.pass_min_memory_quality_score:
        reasons.append(_MEMORY_QUALITY_WATCH_REASON)

    if signal.latest_memory_age_seconds > config.watch_max_memory_age_seconds:
        reasons.append(_MEMORY_RECENCY_BLOCK_REASON)
    elif signal.latest_memory_age_seconds > config.pass_max_memory_age_seconds:
        reasons.append(_MEMORY_RECENCY_WATCH_REASON)

    if signal.recent_case_coverage_ratio < config.watch_min_recent_case_coverage_ratio:
        reasons.append(_CASE_COVERAGE_BLOCK_REASON)
    elif signal.recent_case_coverage_ratio < config.pass_min_recent_case_coverage_ratio:
        reasons.append(_CASE_COVERAGE_WATCH_REASON)

    if signal.unresolved_memory_gap_count >= config.block_max_unresolved_memory_gap_count:
        reasons.append(_MEMORY_GAP_BLOCK_REASON)
    elif signal.unresolved_memory_gap_count >= config.watch_max_unresolved_memory_gap_count:
        reasons.append(_MEMORY_GAP_WATCH_REASON)

    if signal.screening_support_score < config.watch_min_screening_support_score:
        reasons.append(_SCREENING_SUPPORT_BLOCK_REASON)
    elif signal.screening_support_score < config.pass_min_screening_support_score:
        reasons.append(_SCREENING_SUPPORT_WATCH_REASON)

    if not reasons:
        reasons.append(_READY_REASON)
    return tuple(reason for reason in _ROW_REASON_SEQUENCE if reason in reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASONS for reason_code in reason_codes):
        return _STATUS_BLOCK
    if reason_codes == (_READY_REASON,):
        return _STATUS_PASS
    return _STATUS_WATCH


def _summary_status(rows: tuple[ResearchCryptoEventTeamMemoryRow, ...]) -> str:
    if not rows:
        return _STATUS_BLOCK
    if any(row.memory_status == _STATUS_BLOCK for row in rows):
        return _STATUS_BLOCK
    if any(row.memory_status == _STATUS_WATCH for row in rows):
        return _STATUS_WATCH
    return _STATUS_PASS


def _metric_status(
    rows: tuple[ResearchCryptoEventTeamMemoryRow, ...],
    *,
    block_reason: str,
    watch_reason: str,
) -> str:
    if not rows:
        return _STATUS_BLOCK
    if any(block_reason in row.reason_codes for row in rows):
        return _STATUS_BLOCK
    if any(watch_reason in row.reason_codes for row in rows):
        return _STATUS_WATCH
    return _STATUS_PASS


def _summary_reason_codes(
    rows: tuple[ResearchCryptoEventTeamMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_NO_INPUTS_REASON,)
    reasons = set().union(*(row.reason_codes for row in rows))
    if _READY_REASON in reasons and len(reasons) > 1:
        reasons.remove(_READY_REASON)
    reasons.add(
        {
            _STATUS_BLOCK: _REPORT_BLOCK_REASON,
            _STATUS_WATCH: _REPORT_WATCH_REASON,
            _STATUS_PASS: _REPORT_PASS_REASON,
        }[_summary_status(rows)],
    )
    return tuple(reason for reason in _SUMMARY_REASON_SEQUENCE if reason in reasons)


def _reason_code_counts(
    rows: tuple[ResearchCryptoEventTeamMemoryRow, ...],
) -> tuple[ResearchCryptoEventTeamMemoryReasonCodeCount, ...]:
    signal_count = _count_decimal(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchCryptoEventTeamMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
            signal_ratio=_safe_ratio(_count_decimal(counts[reason_code]), signal_count),
        )
        for reason_code in _REASON_COUNT_SEQUENCE
        if reason_code in counts
    )


def _row_sort_key(row: ResearchCryptoEventTeamMemoryRow) -> tuple[object, ...]:
    return (
        _STATUS_RANK[row.memory_status],
        row.crypto_event_label,
        row.specialist_memory_quality_score,
        row.latest_memory_age_seconds,
        row.recent_case_coverage_ratio,
        row.unresolved_memory_gap_count,
        row.screening_support_score,
        row.screened_case_count,
    )


def _validate_row(row: ResearchCryptoEventTeamMemoryRow) -> None:
    if row.memory_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("memory_status does not match reason_codes status")


def _validate_report(report: ResearchCryptoEventTeamMemoryReport) -> None:
    rows = report.rows
    if report.memory_signal_count != _count_decimal(len(rows)):
        raise ValueError("memory_signal_count does not match rows")
    if report.pass_count != _count_decimal(
        sum(1 for row in rows if row.memory_status == _STATUS_PASS),
    ):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in rows if row.memory_status == _STATUS_WATCH),
    ):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _count_decimal(
        sum(1 for row in rows if row.memory_status == _STATUS_BLOCK),
    ):
        raise ValueError("block_count does not match rows")
    if report.average_memory_quality_score != _safe_ratio(
        _q(sum((row.specialist_memory_quality_score for row in rows), _ZERO)),
        report.memory_signal_count,
    ):
        raise ValueError("average_memory_quality_score does not match rows")
    if report.average_recent_case_coverage_ratio != _safe_ratio(
        _q(sum((row.recent_case_coverage_ratio for row in rows), _ZERO)),
        report.memory_signal_count,
    ):
        raise ValueError("average_recent_case_coverage_ratio does not match rows")
    if report.unresolved_memory_gap_count != _q(
        sum((row.unresolved_memory_gap_count for row in rows), _ZERO),
    ):
        raise ValueError("unresolved_memory_gap_count does not match rows")
    if report.max_memory_age_seconds != max(
        (row.latest_memory_age_seconds for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_memory_age_seconds does not match rows")
    if report.screened_case_count != _q(sum((row.screened_case_count for row in rows), _ZERO)):
        raise ValueError("screened_case_count does not match rows")
    if report.report_status != _summary_status(rows):
        raise ValueError("report_status does not match rows")
    expected_metric_statuses = {
        "memory_quality_status": _metric_status(
            rows,
            block_reason=_MEMORY_QUALITY_BLOCK_REASON,
            watch_reason=_MEMORY_QUALITY_WATCH_REASON,
        ),
        "memory_recency_status": _metric_status(
            rows,
            block_reason=_MEMORY_RECENCY_BLOCK_REASON,
            watch_reason=_MEMORY_RECENCY_WATCH_REASON,
        ),
        "case_coverage_status": _metric_status(
            rows,
            block_reason=_CASE_COVERAGE_BLOCK_REASON,
            watch_reason=_CASE_COVERAGE_WATCH_REASON,
        ),
        "memory_gap_status": _metric_status(
            rows,
            block_reason=_MEMORY_GAP_BLOCK_REASON,
            watch_reason=_MEMORY_GAP_WATCH_REASON,
        ),
        "screening_support_status": _metric_status(
            rows,
            block_reason=_SCREENING_SUPPORT_BLOCK_REASON,
            watch_reason=_SCREENING_SUPPORT_WATCH_REASON,
        ),
    }
    for field_name, expected_status in expected_metric_statuses.items():
        if getattr(report, field_name) != expected_status:
            raise ValueError(f"{field_name} does not match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes do not match rows")


def _normalize_rows(
    rows: tuple[ResearchCryptoEventTeamMemoryRow, ...],
) -> tuple[ResearchCryptoEventTeamMemoryRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchCryptoEventTeamMemoryRow:
            raise ValueError("rows must contain ResearchCryptoEventTeamMemoryRow")
    return rows


def _normalize_reason_code_counts(
    items: tuple[ResearchCryptoEventTeamMemoryReasonCodeCount, ...],
) -> tuple[ResearchCryptoEventTeamMemoryReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not ResearchCryptoEventTeamMemoryReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code count rows")
    return items


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a nonempty tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    normalized = tuple(reason_code for reason_code in sequence if reason_code in seen)
    if normalized != value:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_reason_code(field_name: str, value: object) -> str:
    value = _require_canonical_string(field_name, value)
    if value not in _SUMMARY_REASON_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    value = _require_canonical_string(field_name, value)
    if value not in _STATUS_RANK:
        raise ValueError(f"{field_name} must be a known status")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    value = _require_canonical_string(field_name, value)
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} must be an aggregate-safe label")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
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


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value > _ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _q(numerator / denominator)


def _q(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)):
        return value
    raise ValueError("value is not JSON serializable")


def _digest_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _verify_report_digest(report: ResearchCryptoEventTeamMemoryReport) -> None:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _verify_public_payload_digest(payload)


def _verify_public_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public payload value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_public_numerics(value: object) -> None:
    if type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")
