"""Pure report-only strategy event cluster correlation digest."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_STRATEGY_EVENT_CLUSTER_CORRELATION_DIGEST_CONFIG_VERSION = (
    "strategy-event-cluster-correlation-digest-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
DEFAULT_MAX_CLUSTER_EXPOSURE_SHARE = Decimal("0.500000")
DEFAULT_MAX_EVENT_CORRELATION = Decimal("0.700000")
DEFAULT_MAX_CONDITION_CORRELATION = Decimal("0.800000")
DEFAULT_MIN_WATCH_CLUSTER_SIZE = Decimal("2")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}

CLEAR_REASON = "cluster_correlation_clear"
EMPTY_REASON = "event_cluster_correlation_digest_empty"
EVENT_OVERLAP_REASON = "event_cluster_overlap"
CONDITION_OVERLAP_REASON = "condition_cluster_overlap"
EXPOSURE_REASON = "cluster_exposure_share_high"
EVENT_CORRELATION_REASON = "event_correlation_high"
CONDITION_CORRELATION_REASON = "condition_correlation_high"

ROW_REASON_PRIORITY = (
    EXPOSURE_REASON,
    CONDITION_CORRELATION_REASON,
    CONDITION_OVERLAP_REASON,
    EVENT_OVERLAP_REASON,
    EVENT_CORRELATION_REASON,
    CLEAR_REASON,
)
REPORT_REASON_PRIORITY = (
    EXPOSURE_REASON,
    EVENT_CORRELATION_REASON,
    CONDITION_CORRELATION_REASON,
    CONDITION_OVERLAP_REASON,
    EVENT_OVERLAP_REASON,
)
SENSITIVE_FRAGMENTS = (
    "api" + "_key",
    "bear" + "er",
    "private" + "_key",
    "sec" + "ret",
    "sk" + "_",
    "tok" + "en",
    "wall" + "et",
)


__all__ = (
    "DEFAULT_STRATEGY_EVENT_CLUSTER_CORRELATION_DIGEST_CONFIG_VERSION",
    "StrategyEventClusterCorrelationDigestConfig",
    "StrategyEventClusterCorrelationDigestReport",
    "StrategyEventClusterCorrelationDigestRow",
    "StrategyEventClusterCorrelationSignal",
    "build_strategy_event_cluster_correlation_digest",
    "strategy_event_cluster_correlation_digest_payload",
)


@dataclass(frozen=True)
class StrategyEventClusterCorrelationDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_EVENT_CLUSTER_CORRELATION_DIGEST_CONFIG_VERSION
    )
    max_cluster_exposure_share: Decimal = DEFAULT_MAX_CLUSTER_EXPOSURE_SHARE
    max_event_correlation: Decimal = DEFAULT_MAX_EVENT_CORRELATION
    max_condition_correlation: Decimal = DEFAULT_MAX_CONDITION_CORRELATION
    min_watch_cluster_size: Decimal = DEFAULT_MIN_WATCH_CLUSTER_SIZE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyEventClusterCorrelationDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_cluster_exposure_share",
            "max_event_correlation",
            "max_condition_correlation",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_watch_cluster_size",
            _normalize_positive_whole_decimal(
                "min_watch_cluster_size",
                self.min_watch_cluster_size,
            ),
        )
        _reject_sensitive_text("config_version", self.config_version)
        require_paper_only_flags("StrategyEventClusterCorrelationDigestConfig", self)


@dataclass(frozen=True)
class StrategyEventClusterCorrelationSignal:
    candidate_reference: str = field(repr=False)
    event_key: str = field(repr=False)
    condition_id: str = field(repr=False)
    signal_key: str = field(repr=False)
    paper_exposure: Decimal
    signal_strength: Decimal
    event_correlation: Decimal
    condition_correlation: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyEventClusterCorrelationSignal, "signal")
        for field_name in (
            "candidate_reference",
            "event_key",
            "condition_id",
            "signal_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "paper_exposure",
            _normalize_nonnegative_decimal("paper_exposure", self.paper_exposure),
        )
        for field_name in (
            "signal_strength",
            "event_correlation",
            "condition_correlation",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        for reason_code in self.reason_codes:
            _reject_sensitive_text("reason_codes", reason_code)
        require_paper_only_flags("StrategyEventClusterCorrelationSignal", self)


@dataclass(frozen=True)
class StrategyEventClusterCorrelationDigestRow:
    cluster_rank: Decimal
    redacted_event_key: str
    redacted_candidate_references: tuple[str, ...]
    redacted_condition_ids: tuple[str, ...]
    candidate_count: Decimal
    condition_count: Decimal
    signal_count: Decimal
    paper_exposure: Decimal
    total_paper_exposure: Decimal
    exposure_share: Decimal
    mean_signal_strength: Decimal
    max_event_correlation: Decimal
    max_condition_correlation: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyEventClusterCorrelationDigestRow, "row")
        object.__setattr__(
            self,
            "cluster_rank",
            _normalize_positive_whole_decimal("cluster_rank", self.cluster_rank),
        )
        _require_redacted_value(
            "redacted_event_key",
            self.redacted_event_key,
            "event_ref_",
        )
        object.__setattr__(
            self,
            "redacted_candidate_references",
            _normalize_redacted_tuple(
                "redacted_candidate_references",
                self.redacted_candidate_references,
                "candidate_ref_",
            ),
        )
        object.__setattr__(
            self,
            "redacted_condition_ids",
            _normalize_redacted_tuple(
                "redacted_condition_ids",
                self.redacted_condition_ids,
                "condition_ref_",
            ),
        )
        for field_name in (
            "candidate_count",
            "condition_count",
            "signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "paper_exposure",
            "total_paper_exposure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "exposure_share",
            "mean_signal_strength",
            "max_event_correlation",
            "max_condition_correlation",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("StrategyEventClusterCorrelationDigestRow", self)


@dataclass(frozen=True)
class StrategyEventClusterCorrelationDigestReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    cluster_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    total_paper_exposure: Decimal
    max_cluster_exposure_share: Decimal
    max_event_correlation: Decimal
    max_condition_correlation: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyEventClusterCorrelationDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyEventClusterCorrelationDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "signal_count",
            "cluster_count",
            "blocked_count",
            "watch_count",
            "pass_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "total_paper_exposure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_cluster_exposure_share",
            "max_event_correlation",
            "max_condition_correlation",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _reject_sensitive_text("config_version", self.config_version)
        _validate_report(self)
        require_paper_only_flags("StrategyEventClusterCorrelationDigestReport", self)


def build_strategy_event_cluster_correlation_digest(
    signals: Iterable[StrategyEventClusterCorrelationSignal],
    *,
    config: StrategyEventClusterCorrelationDigestConfig,
    generated_at: datetime,
) -> StrategyEventClusterCorrelationDigestReport:
    if type(config) is not StrategyEventClusterCorrelationDigestConfig:
        raise ValueError(
            "config must be a StrategyEventClusterCorrelationDigestConfig",
        )
    require_paper_only_flags("StrategyEventClusterCorrelationDigestConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    for signal in normalized_signals:
        if signal.observed_at > generated_at_utc:
            raise ValueError("generated_at must not precede observed_at")
    total_paper_exposure = _sum_decimal(
        signal.paper_exposure for signal in normalized_signals
    )
    grouped = _event_groups(normalized_signals)
    cluster_total = len(grouped)
    preliminary_rows = tuple(
        _row_from_group(
            cluster_signals,
            total_paper_exposure=total_paper_exposure,
            cluster_total=cluster_total,
            config=config,
        )
        for cluster_signals in grouped
    )
    sorted_rows = tuple(sorted(preliminary_rows, key=_row_sort_key))
    rows = tuple(
        StrategyEventClusterCorrelationDigestRow(
            cluster_rank=_count_decimal(index),
            redacted_event_key=row.redacted_event_key,
            redacted_candidate_references=row.redacted_candidate_references,
            redacted_condition_ids=row.redacted_condition_ids,
            candidate_count=row.candidate_count,
            condition_count=row.condition_count,
            signal_count=row.signal_count,
            paper_exposure=row.paper_exposure,
            total_paper_exposure=row.total_paper_exposure,
            exposure_share=row.exposure_share,
            mean_signal_strength=row.mean_signal_strength,
            max_event_correlation=row.max_event_correlation,
            max_condition_correlation=row.max_condition_correlation,
            observed_at=row.observed_at,
            status=row.status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted_rows, start=1)
    )
    return StrategyEventClusterCorrelationDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        signal_count=_count_decimal(len(normalized_signals)),
        cluster_count=_count_decimal(len(rows)),
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        total_paper_exposure=total_paper_exposure,
        max_cluster_exposure_share=_max_row_decimal(rows, "exposure_share"),
        max_event_correlation=_max_row_decimal(rows, "max_event_correlation"),
        max_condition_correlation=_max_row_decimal(rows, "max_condition_correlation"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_event_cluster_correlation_digest_payload(
    report: StrategyEventClusterCorrelationDigestReport,
) -> dict[str, Any]:
    if type(report) is not StrategyEventClusterCorrelationDigestReport:
        raise ValueError(
            "report must be a StrategyEventClusterCorrelationDigestReport",
        )
    require_paper_only_flags("StrategyEventClusterCorrelationDigestReport", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_group(
    signals: tuple[StrategyEventClusterCorrelationSignal, ...],
    *,
    total_paper_exposure: Decimal,
    cluster_total: int,
    config: StrategyEventClusterCorrelationDigestConfig,
) -> StrategyEventClusterCorrelationDigestRow:
    paper_exposure = _sum_decimal(signal.paper_exposure for signal in signals)
    exposure_share = _safe_ratio(paper_exposure, total_paper_exposure)
    max_event_correlation = max((signal.event_correlation for signal in signals), default=ZERO)
    max_condition_correlation = max(
        (signal.condition_correlation for signal in signals),
        default=ZERO,
    )
    reason_codes = _row_reason_codes(
        signals,
        exposure_share=exposure_share,
        cluster_total=cluster_total,
        max_event_correlation=max_event_correlation,
        max_condition_correlation=max_condition_correlation,
        config=config,
    )
    return StrategyEventClusterCorrelationDigestRow(
        cluster_rank=ONE,
        redacted_event_key=_redact_reference("event_ref_", signals[0].event_key),
        redacted_candidate_references=_redacted_unique_values(
            "candidate_ref_",
            tuple(signal.candidate_reference for signal in signals),
        ),
        redacted_condition_ids=_redacted_unique_values(
            "condition_ref_",
            tuple(signal.condition_id for signal in signals),
        ),
        candidate_count=_count_decimal(
            len({signal.candidate_reference for signal in signals}),
        ),
        condition_count=_count_decimal(len({signal.condition_id for signal in signals})),
        signal_count=_count_decimal(len(signals)),
        paper_exposure=paper_exposure,
        total_paper_exposure=total_paper_exposure,
        exposure_share=exposure_share,
        mean_signal_strength=_mean_decimal(
            tuple(signal.signal_strength for signal in signals),
        ),
        max_event_correlation=max_event_correlation,
        max_condition_correlation=max_condition_correlation,
        observed_at=max(signal.observed_at for signal in signals),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    signals: tuple[StrategyEventClusterCorrelationSignal, ...],
    *,
    exposure_share: Decimal,
    cluster_total: int,
    max_event_correlation: Decimal,
    max_condition_correlation: Decimal,
    config: StrategyEventClusterCorrelationDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    signal_count = _count_decimal(len(signals))
    condition_count = _count_decimal(len({signal.condition_id for signal in signals}))
    if (
        cluster_total > 1
        and exposure_share > config.max_cluster_exposure_share
        and len(signals) > 1
    ):
        codes.append(EXPOSURE_REASON)
    if max_condition_correlation >= config.max_condition_correlation:
        codes.append(CONDITION_CORRELATION_REASON)
    if condition_count < signal_count and signal_count >= config.min_watch_cluster_size:
        codes.append(CONDITION_OVERLAP_REASON)
    if signal_count >= config.min_watch_cluster_size:
        codes.append(EVENT_OVERLAP_REASON)
    if max_event_correlation >= config.max_event_correlation:
        codes.append(EVENT_CORRELATION_REASON)
    if not codes:
        codes.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_PRIORITY if reason in codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        EXPOSURE_REASON in reason_codes
        or EVENT_CORRELATION_REASON in reason_codes
        or CONDITION_CORRELATION_REASON in reason_codes
    ):
        return BLOCKED_STATUS
    if EVENT_OVERLAP_REASON in reason_codes or CONDITION_OVERLAP_REASON in reason_codes:
        return WATCH_STATUS
    return PASS_STATUS


def _report_status(
    rows: tuple[StrategyEventClusterCorrelationDigestRow, ...],
) -> str:
    if any(row.status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[StrategyEventClusterCorrelationDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    blocked_reasons = tuple(
        reason
        for reason in (EXPOSURE_REASON, EVENT_CORRELATION_REASON, CONDITION_CORRELATION_REASON)
        if reason in observed
    )
    if blocked_reasons:
        return blocked_reasons
    watch_reasons = tuple(
        reason
        for reason in (CONDITION_OVERLAP_REASON, EVENT_OVERLAP_REASON)
        if reason in observed
    )
    if watch_reasons:
        return watch_reasons
    return (CLEAR_REASON,)


def _event_groups(
    signals: tuple[StrategyEventClusterCorrelationSignal, ...],
) -> tuple[tuple[StrategyEventClusterCorrelationSignal, ...], ...]:
    event_keys = tuple(sorted({signal.event_key for signal in signals}))
    return tuple(
        tuple(signal for signal in signals if signal.event_key == event_key)
        for event_key in event_keys
    )


def _normalize_signals(
    signals: Iterable[StrategyEventClusterCorrelationSignal],
) -> tuple[StrategyEventClusterCorrelationSignal, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Iterable):
        raise ValueError("signals must be an iterable")
    normalized = tuple(signals)
    seen_signal_keys: set[str] = set()
    for signal in normalized:
        if isinstance(signal, (str, bytes)):
            raise ValueError("signals must be an iterable of signals")
        if type(signal) is not StrategyEventClusterCorrelationSignal:
            raise ValueError("signals must contain StrategyEventClusterCorrelationSignal")
        require_paper_only_flags("StrategyEventClusterCorrelationSignal", signal)
        signal_identity = "|".join(
            (signal.event_key, signal.condition_id, signal.candidate_reference, signal.signal_key),
        )
        if signal_identity in seen_signal_keys:
            raise ValueError("signals must be unique")
        seen_signal_keys.add(signal_identity)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[StrategyEventClusterCorrelationDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyEventClusterCorrelationDigestRow:
            raise ValueError("rows must contain StrategyEventClusterCorrelationDigestRow")
        require_paper_only_flags("StrategyEventClusterCorrelationDigestRow", row)
    return normalized


def _validate_row(row: StrategyEventClusterCorrelationDigestRow) -> None:
    if row.candidate_count != _count_decimal(len(row.redacted_candidate_references)):
        raise ValueError("candidate_count must match redacted references")
    if row.condition_count != _count_decimal(len(row.redacted_condition_ids)):
        raise ValueError("condition_count must match redacted condition ids")
    if row.signal_count < row.candidate_count:
        raise ValueError("signal_count must cover candidate_count")
    if row.signal_count < row.condition_count:
        raise ValueError("signal_count must cover condition_count")
    if row.paper_exposure > row.total_paper_exposure and row.total_paper_exposure != ZERO:
        raise ValueError("paper_exposure must not exceed total_paper_exposure")
    if row.exposure_share != _safe_ratio(row.paper_exposure, row.total_paper_exposure):
        raise ValueError("exposure_share must match exposure totals")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if CLEAR_REASON in row.reason_codes and len(row.reason_codes) > 1:
        raise ValueError("reason_codes must not mix clear and finding reasons")


def _validate_report(report: StrategyEventClusterCorrelationDigestReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if report.signal_count != _sum_decimal(row.signal_count for row in report.rows):
        raise ValueError("signal_count must match rows")
    if report.cluster_count != _count_decimal(len(report.rows)):
        raise ValueError("cluster_count must match rows")
    if report.blocked_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.cluster_count != (
        report.blocked_count + report.watch_count + report.pass_count
    ):
        raise ValueError("cluster_count must match status counts")
    if report.total_paper_exposure != _sum_decimal(
        row.paper_exposure for row in report.rows
    ):
        raise ValueError("total_paper_exposure must match rows")
    if report.max_cluster_exposure_share != _max_row_decimal(report.rows, "exposure_share"):
        raise ValueError("max_cluster_exposure_share must match rows")
    if report.max_event_correlation != _max_row_decimal(
        report.rows,
        "max_event_correlation",
    ):
        raise ValueError("max_event_correlation must match rows")
    if report.max_condition_correlation != _max_row_decimal(
        report.rows,
        "max_condition_correlation",
    ):
        raise ValueError("max_condition_correlation must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_sort_key(
    row: StrategyEventClusterCorrelationDigestRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        -row.exposure_share,
        -row.max_event_correlation,
        -row.max_condition_correlation,
        row.redacted_event_key,
    )


def _status_count(
    rows: tuple[StrategyEventClusterCorrelationDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _max_row_decimal(
    rows: tuple[StrategyEventClusterCorrelationDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    return max(getattr(row, field_name) for row in rows)


def _redacted_unique_values(prefix: str, values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({_redact_reference(prefix, value) for value in values}))


def _redact_reference(prefix: str, value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{digest}"


def _normalize_redacted_tuple(
    field_name: str,
    value: object,
    prefix: str,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(value)
    if not normalized:
        raise ValueError(f"{field_name} is required")
    if normalized != tuple(sorted(normalized)):
        raise ValueError(f"{field_name} must be sorted deterministically")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    for item in normalized:
        _require_redacted_value(field_name, item, prefix)
    return normalized


def _require_redacted_value(field_name: str, value: object, prefix: str) -> None:
    _require_canonical_string(field_name, value)
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be redacted")
    _reject_sensitive_text(field_name, value)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} is required")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        _reject_sensitive_text(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _reject_sensitive_text(field_name: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in SENSITIVE_FRAGMENTS):
            raise ValueError(f"{field_name} contains sensitive material")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized < ONE:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized.quantize(COUNT_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be exactly Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return _quantize_decimal(ZERO)
    return _normalize_probability("ratio", numerator / denominator)


def _mean_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _quantize_decimal(ZERO)
    return _quantize_decimal(_sum_decimal(values) / Decimal(len(values)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal(total)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _payload_value(getattr(value, item.name))
            for item in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("payload contains unsupported value")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")
