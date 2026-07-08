"""Pure report-only resolution latency monitor for research follow-up."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_RESOLUTION_LATENCY_MONITOR_CONFIG_VERSION",
    "ResearchResolutionLatencyMonitorConfig",
    "ResearchResolutionLatencyMonitorObservation",
    "ResearchResolutionLatencyMonitorReasonCodeCount",
    "ResearchResolutionLatencyMonitorReport",
    "ResearchResolutionLatencyMonitorRow",
    "build_research_resolution_latency_monitor_report",
    "research_resolution_latency_monitor_digest",
    "research_resolution_latency_monitor_report_payload",
)


DEFAULT_RESEARCH_RESOLUTION_LATENCY_MONITOR_CONFIG_VERSION = (
    "research-resolution-latency-monitor-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
NO_INPUTS_REASON = "resolution_latency_monitor_no_inputs"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_SENSITIVE_INPUT_FIELDS = frozenset(
    (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
    ),
)
_UNSAFE_PUBLIC_KEYS = _SENSITIVE_INPUT_FIELDS | frozenset(
    (
        "auth",
        "dsn",
        "order",
        "position",
        "private_key",
        "recommendation",
        "recommended_action",
        "table",
        "token",
        "trade",
        "wallet",
    ),
)
_UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "://",
    "auth",
    "buy",
    "dsn",
    "market",
    "order",
    "position",
    "raw_candidate",
    "recommend",
    "sell",
    "source",
    "table",
    "token",
    "trade",
    "wallet",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchResolutionLatencyMonitorConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_RESOLUTION_LATENCY_MONITOR_CONFIG_VERSION
    watch_after_seconds: Decimal = Decimal("86400.000000")
    block_after_seconds: Decimal = Decimal("259200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionLatencyMonitorConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_after_seconds",
            _normalize_nonnegative_decimal(
                "watch_after_seconds",
                self.watch_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "block_after_seconds",
            _normalize_nonnegative_decimal(
                "block_after_seconds",
                self.block_after_seconds,
            ),
        )
        _require_at_most(
            "watch_after_seconds",
            self.watch_after_seconds,
            self.block_after_seconds,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchResolutionLatencyMonitorObservation(_FinalPublicDataclass):
    public_event_ref: str
    expected_end_at: datetime
    confirmed_at: datetime | None = None
    review_completed_at: datetime | None = None
    raw_candidate_id: str | None = None
    market_id: str | None = None
    market_slug: str | None = None
    market_question: str | None = None
    source_ref: str | None = None
    source_url: str | None = None
    source_text: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionLatencyMonitorObservation,
            "observation",
        )
        _require_public_ref("public_event_ref", self.public_event_ref)
        object.__setattr__(
            self,
            "expected_end_at",
            _as_utc("expected_end_at", self.expected_end_at),
        )
        object.__setattr__(
            self,
            "confirmed_at",
            _as_optional_utc("confirmed_at", self.confirmed_at),
        )
        object.__setattr__(
            self,
            "review_completed_at",
            _as_optional_utc("review_completed_at", self.review_completed_at),
        )
        for field_name in _SENSITIVE_INPUT_FIELDS:
            _require_optional_string(field_name, getattr(self, field_name))
        _require_observation_sequence(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchResolutionLatencyMonitorRow(_FinalPublicDataclass):
    public_event_ref: str
    expected_end_at: datetime
    confirmed_at: datetime | None
    review_completed_at: datetime | None
    delay_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionLatencyMonitorRow, "row")
        _require_public_ref("public_event_ref", self.public_event_ref)
        object.__setattr__(
            self,
            "expected_end_at",
            _as_utc("expected_end_at", self.expected_end_at),
        )
        object.__setattr__(
            self,
            "confirmed_at",
            _as_optional_utc("confirmed_at", self.confirmed_at),
        )
        object.__setattr__(
            self,
            "review_completed_at",
            _as_optional_utc("review_completed_at", self.review_completed_at),
        )
        object.__setattr__(
            self,
            "delay_seconds",
            _normalize_nonnegative_decimal("delay_seconds", self.delay_seconds),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchResolutionLatencyMonitorReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionLatencyMonitorReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchResolutionLatencyMonitorReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_delay_seconds: Decimal
    max_delay_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchResolutionLatencyMonitorReasonCodeCount, ...]
    rows: tuple[ResearchResolutionLatencyMonitorRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionLatencyMonitorReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "mean_delay_seconds",
            "max_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchResolutionLatencyMonitorConfig,
    ResearchResolutionLatencyMonitorObservation,
    ResearchResolutionLatencyMonitorReasonCodeCount,
    ResearchResolutionLatencyMonitorReport,
    ResearchResolutionLatencyMonitorRow,
)


def build_research_resolution_latency_monitor_report(
    observations: Iterable[ResearchResolutionLatencyMonitorObservation],
    *,
    config: ResearchResolutionLatencyMonitorConfig,
    generated_at: datetime,
) -> ResearchResolutionLatencyMonitorReport:
    if type(config) is not ResearchResolutionLatencyMonitorConfig:
        raise ValueError("config must be a ResearchResolutionLatencyMonitorConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in items
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchResolutionLatencyMonitorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_delay_seconds=_mean(tuple(row.delay_seconds for row in rows)),
        max_delay_seconds=_max_decimal(tuple(row.delay_seconds for row in rows)),
        status=_rollup_status(tuple(row.status for row in rows)),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def research_resolution_latency_monitor_report_payload(
    report: ResearchResolutionLatencyMonitorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionLatencyMonitorReport:
        raise ValueError("report must be a ResearchResolutionLatencyMonitorReport")
    _require_hard_flags("report", report)
    _require_payload_safe_value("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_resolution_latency_monitor_digest(
    report: ResearchResolutionLatencyMonitorReport,
) -> dict[str, Any]:
    payload = research_resolution_latency_monitor_report_payload(report)
    digest = {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "candidate_count": payload["candidate_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "mean_delay_seconds": payload["mean_delay_seconds"],
        "max_delay_seconds": payload["max_delay_seconds"],
        "status": payload["status"],
        "reason_codes": payload["reason_codes"],
        "reason_code_counts": payload["reason_code_counts"],
        "paper_only": payload["paper_only"],
        "report_only": payload["report_only"],
        "readonly": payload["readonly"],
    }
    _reject_unsafe_public_payload("digest", digest)
    return digest


def _row_from_observation(
    observation: ResearchResolutionLatencyMonitorObservation,
    *,
    config: ResearchResolutionLatencyMonitorConfig,
    generated_at: datetime,
) -> ResearchResolutionLatencyMonitorRow:
    _reject_future_datetimes(observation, generated_at)
    final_at = observation.review_completed_at or generated_at
    delay_seconds = _age_seconds(
        start_at=observation.expected_end_at,
        end_at=final_at,
        field_name="expected_end_at",
    )
    reason_codes = _row_reason_codes(
        observation,
        delay_seconds=delay_seconds,
        config=config,
    )
    return ResearchResolutionLatencyMonitorRow(
        public_event_ref=observation.public_event_ref,
        expected_end_at=observation.expected_end_at,
        confirmed_at=observation.confirmed_at,
        review_completed_at=observation.review_completed_at,
        delay_seconds=delay_seconds,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: ResearchResolutionLatencyMonitorObservation,
    *,
    delay_seconds: Decimal,
    config: ResearchResolutionLatencyMonitorConfig,
) -> tuple[str, ...]:
    if observation.review_completed_at is not None:
        if delay_seconds >= config.block_after_seconds:
            return ("resolution_review_completed_block",)
        if delay_seconds >= config.watch_after_seconds:
            return ("resolution_review_completed_watch",)
        return ("resolution_review_completed_pass",)
    if observation.confirmed_at is not None:
        if delay_seconds >= config.block_after_seconds:
            return ("review_completion_missing_block",)
        if delay_seconds >= config.watch_after_seconds:
            return ("review_completion_missing_watch",)
        return ("review_completion_pending_pass",)
    if delay_seconds >= config.block_after_seconds:
        return ("outcome_confirmation_missing_block",)
    if delay_seconds >= config.watch_after_seconds:
        return ("outcome_confirmation_missing_watch",)
    return ("outcome_confirmation_pending_pass",)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionLatencyMonitorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [f"resolution_latency_monitor_{status}"]
    row_reason_codes = sorted({reason_code for row in rows for reason_code in row.reason_codes})
    reason_codes.extend(row_reason_codes)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchResolutionLatencyMonitorRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchResolutionLatencyMonitorReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchResolutionLatencyMonitorReasonCodeCount(
                reason_code=report_reason_codes[0],
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchResolutionLatencyMonitorReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_observations(
    observations: Iterable[ResearchResolutionLatencyMonitorObservation],
) -> tuple[ResearchResolutionLatencyMonitorObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_refs: set[str] = set()
    for item in values:
        if type(item) is not ResearchResolutionLatencyMonitorObservation:
            raise ValueError(
                "observations must contain ResearchResolutionLatencyMonitorObservation values",
            )
        _require_hard_flags("observation", item)
        if item.public_event_ref in seen_refs:
            raise ValueError("observations must not contain duplicate public_event_ref values")
        seen_refs.add(item.public_event_ref)
    return values


def _normalize_rows(
    rows: Iterable[ResearchResolutionLatencyMonitorRow],
) -> tuple[ResearchResolutionLatencyMonitorRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in values:
        if type(row) is not ResearchResolutionLatencyMonitorRow:
            raise ValueError("rows must contain ResearchResolutionLatencyMonitorRow values")
        _require_hard_flags("row", row)
        if row.public_event_ref in seen_refs:
            raise ValueError("rows must not contain duplicate public_event_ref values")
        seen_refs.add(row.public_event_ref)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchResolutionLatencyMonitorReasonCodeCount],
) -> tuple[ResearchResolutionLatencyMonitorReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchResolutionLatencyMonitorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchResolutionLatencyMonitorReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must be sorted by count then reason_code")
    return values


def _validate_report(report: ResearchResolutionLatencyMonitorReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    delays = tuple(row.delay_seconds for row in rows)
    if report.mean_delay_seconds != _mean(delays):
        raise ValueError("mean_delay_seconds must match rows")
    if report.max_delay_seconds != _max_decimal(delays):
        raise ValueError("max_delay_seconds must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchResolutionLatencyMonitorRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _row_sort_key(row: ResearchResolutionLatencyMonitorRow) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.delay_seconds,
        row.public_event_ref,
    )


def _reject_future_datetimes(
    observation: ResearchResolutionLatencyMonitorObservation,
    generated_at: datetime,
) -> None:
    if observation.expected_end_at > generated_at:
        raise ValueError("expected_end_at must not be after generated_at")
    if observation.confirmed_at is not None and observation.confirmed_at > generated_at:
        raise ValueError("confirmed_at must not be after generated_at")
    if (
        observation.review_completed_at is not None
        and observation.review_completed_at > generated_at
    ):
        raise ValueError("review_completed_at must not be after generated_at")


def _require_observation_sequence(
    observation: ResearchResolutionLatencyMonitorObservation,
) -> None:
    if (
        observation.confirmed_at is not None
        and observation.confirmed_at < observation.expected_end_at
    ):
        raise ValueError("confirmed_at must not be before expected_end_at")
    if (
        observation.review_completed_at is not None
        and observation.review_completed_at < observation.expected_end_at
    ):
        raise ValueError("review_completed_at must not be before expected_end_at")
    if (
        observation.confirmed_at is not None
        and observation.review_completed_at is not None
        and observation.review_completed_at < observation.confirmed_at
    ):
        raise ValueError("review_completed_at must not be before confirmed_at")


def _age_seconds(*, start_at: datetime, end_at: datetime, field_name: str) -> Decimal:
    start_utc = _as_utc(field_name, start_at)
    end_utc = _as_utc("end_at", end_at)
    delta = end_utc - start_utc
    total_microseconds = (
        (delta.days * 86400 * 1000000)
        + (delta.seconds * 1000000)
        + delta.microseconds
    )
    seconds = _quantize(Decimal(total_microseconds) / Decimal("1000000"))
    if seconds < ZERO:
        raise ValueError(f"{field_name} must not be after end_at")
    return seconds


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_report_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for reason_code in values:
        _require_reason_code("reason_codes", reason_code)
    if not values:
        raise ValueError("reason_codes must not be empty")
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    if values[1:] != tuple(sorted(values[1:])):
        raise ValueError("reason_codes must use canonical sequence")
    return values


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for reason_code in values:
        _require_reason_code("reason_codes", reason_code)
    if values != tuple(sorted(values)):
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    return values


def _require_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    if not all(character.islower() or character.isdigit() or character == "_" for character in value):
        raise ValueError(f"{field_name} must be snake_case")
    _require_safe_public_string(field_name, value)


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _require_public_ref(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    _require_safe_public_string(field_name, value)


def _require_safe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_optional_string(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_canonical_string(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_at_most(field_name: str, value: Decimal, upper_bound: Decimal) -> None:
    if value > upper_bound:
        raise ValueError(f"{field_name} must be less than or equal to upper bound")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        for field in fields(value):
            _require_payload_safe_value(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})
        return
    if type(value) is Decimal:
        _normalize_decimal(label, value)
        return
    if type(value) is datetime:
        _as_utc(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            _require_canonical_string(label, value)
        return
    raise ValueError(f"{label} contains unsupported value")


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
            if field.name not in _SENSITIVE_INPUT_FIELDS
        }
    if value is None or type(value) in (bool, str):
        return value
    raise ValueError("payload contains an unsupported value")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_name = field.name
            if field_name in _SENSITIVE_INPUT_FIELDS:
                continue
            _reject_public_key(label, field_name)
            _reject_unsafe_public_payload(
                f"{label}.{field_name}",
                getattr(value, field_name),
            )
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} payload keys must be strings")
            _reject_public_key(label, key)
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if type(value) is str:
        _require_safe_public_string(label, value)


def _reject_public_key(label: str, key: str) -> None:
    normalized_key = key.lower()
    if normalized_key in _UNSAFE_PUBLIC_KEYS:
        raise ValueError(f"{label} contains unsafe public field: {key}")
