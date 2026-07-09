"""Report-only primary-claim latency memory-floor snapshot.

The module is deterministic and side-effect free. Callers provide local
primary-claim capture observations; the report returns sanitized latency and
memory-floor diagnostics without storage, network, wallet, execution, sizing,
or recommendation surfaces.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_PRIMARY_CLAIM_LATENCY_MEMORY_FLOOR_CONFIG_VERSION = (
    "primary-claim-latency-memory-floor-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_STATUSES = ("pass", "watch", "block")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_ROW_REASON_CODES = (
    "missing_primary_claim_capture",
    "primary_claim_latency_block",
    "primary_claim_latency_watch",
    "memory_floor_block",
    "memory_floor_watch",
    "primary_claim_latency_memory_floor_pass",
)
_REPORT_REASON_CODES = (
    "empty_latency_memory_floor",
    *_ROW_REASON_CODES,
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "http",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "network",
    "database",
    "position",
    "sizing",
    "recommend",
    "buy",
    "sell",
    "live",
)


__all__ = (
    "ResearchSourcePrimaryClaimLatencyMemoryFloorConfig",
    "ResearchSourcePrimaryClaimLatencyMemoryFloorInput",
    "ResearchSourcePrimaryClaimLatencyMemoryFloorReasonCodeCount",
    "ResearchSourcePrimaryClaimLatencyMemoryFloorReport",
    "ResearchSourcePrimaryClaimLatencyMemoryFloorRow",
    "build_research_source_primary_claim_latency_memory_floor_report",
    "research_source_primary_claim_latency_memory_floor_report_digest",
    "research_source_primary_claim_latency_memory_floor_report_payload",
)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimLatencyMemoryFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_PRIMARY_CLAIM_LATENCY_MEMORY_FLOOR_CONFIG_VERSION
    )
    watch_latency_seconds: Decimal = Decimal("900.000000")
    block_latency_seconds: Decimal = Decimal("3600.000000")
    watch_memory_floor_score: Decimal = Decimal("0.750000")
    block_memory_floor_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryClaimLatencyMemoryFloorConfig:
            raise TypeError(
                "ResearchSourcePrimaryClaimLatencyMemoryFloorConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourcePrimaryClaimLatencyMemoryFloorConfig,
            "config",
        )
        _require_text("config_version", self.config_version)
        for field_name in ("watch_latency_seconds", "block_latency_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_latency_seconds >= self.block_latency_seconds:
            raise ValueError("watch_latency_seconds must be below block_latency_seconds")
        for field_name in ("watch_memory_floor_score", "block_memory_floor_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_memory_floor_score >= self.watch_memory_floor_score:
            raise ValueError(
                "block_memory_floor_score must be below watch_memory_floor_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimLatencyMemoryFloorInput:
    claim_ref: str
    capture_ref: str
    authority_family_ref: str
    primary: bool
    observed_at: datetime
    captured_at: datetime
    memory_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryClaimLatencyMemoryFloorInput:
            raise TypeError(
                "ResearchSourcePrimaryClaimLatencyMemoryFloorInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourcePrimaryClaimLatencyMemoryFloorInput,
            "input",
        )
        for field_name in ("claim_ref", "capture_ref", "authority_family_ref"):
            _require_text(field_name, getattr(self, field_name))
        if type(self.primary) is not bool:
            raise ValueError("primary must be a bool")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        if self.captured_at < self.observed_at:
            raise ValueError("captured_at must be on or after observed_at")
        object.__setattr__(
            self,
            "memory_score",
            _require_ratio_decimal("memory_score", self.memory_score),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimLatencyMemoryFloorRow:
    claim_digest: str
    status: str
    input_count: Decimal
    primary_input_count: Decimal
    authority_family_count: Decimal
    max_latency_seconds: Decimal
    average_latency_seconds: Decimal
    memory_floor_score: Decimal
    average_memory_score: Decimal
    latency_breach: bool
    memory_floor_breach: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryClaimLatencyMemoryFloorRow:
            raise TypeError(
                "ResearchSourcePrimaryClaimLatencyMemoryFloorRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_digest_reference("claim_digest", self.claim_digest)
        _require_member("status", self.status, _STATUSES)
        for field_name in (
            "input_count",
            "primary_input_count",
            "authority_family_count",
            "max_latency_seconds",
            "average_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("memory_floor_score", "average_memory_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("latency_breach", "memory_floor_breach"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=_ROW_REASON_CODES,
                allow_empty=False,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimLatencyMemoryFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryClaimLatencyMemoryFloorReasonCodeCount:
            raise TypeError(
                "ResearchSourcePrimaryClaimLatencyMemoryFloorReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, _REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimLatencyMemoryFloorReport:
    generated_at: datetime
    config_version: str
    status: str
    claim_count: Decimal
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    latency_breach_count: Decimal
    memory_floor_breach_count: Decimal
    average_latency_seconds: Decimal
    average_memory_floor_score: Decimal
    rows: tuple[ResearchSourcePrimaryClaimLatencyMemoryFloorRow, ...]
    reason_code_counts: tuple[
        ResearchSourcePrimaryClaimLatencyMemoryFloorReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryClaimLatencyMemoryFloorReport:
            raise TypeError(
                "ResearchSourcePrimaryClaimLatencyMemoryFloorReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourcePrimaryClaimLatencyMemoryFloorReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        _require_member("status", self.status, _STATUSES)
        for field_name in (
            "claim_count",
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "latency_breach_count",
            "memory_floor_breach_count",
            "average_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_memory_floor_score",
            _require_ratio_decimal(
                "average_memory_floor_score",
                self.average_memory_floor_score,
            ),
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=_REPORT_REASON_CODES,
                allow_empty=False,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest_string(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_source_primary_claim_latency_memory_floor_report(
    rows: tuple[ResearchSourcePrimaryClaimLatencyMemoryFloorInput, ...]
    | list[ResearchSourcePrimaryClaimLatencyMemoryFloorInput],
    *,
    config: ResearchSourcePrimaryClaimLatencyMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchSourcePrimaryClaimLatencyMemoryFloorReport:
    if type(config) is not ResearchSourcePrimaryClaimLatencyMemoryFloorConfig:
        raise ValueError(
            "config must be a ResearchSourcePrimaryClaimLatencyMemoryFloorConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(rows)
    for row in inputs:
        if row.captured_at > generated_at_utc:
            raise ValueError("captured_at must be on or before generated_at")

    grouped: dict[str, list[ResearchSourcePrimaryClaimLatencyMemoryFloorInput]] = {}
    for row in inputs:
        grouped.setdefault(row.claim_ref, []).append(row)

    report_rows = tuple(
        sorted(
            (
                _row_for_claim(
                    claim_ref=claim_ref,
                    rows=tuple(grouped[claim_ref]),
                    config=config,
                )
                for claim_ref in grouped
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(report_rows, len(inputs))

    return ResearchSourcePrimaryClaimLatencyMemoryFloorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(report_rows),
        claim_count=_count(len(report_rows)),
        input_count=_count(len(inputs)),
        pass_count=_status_count(report_rows, "pass"),
        watch_count=_status_count(report_rows, "watch"),
        block_count=_status_count(report_rows, "block"),
        latency_breach_count=_count(
            sum(Decimal("1") for row in report_rows if row.latency_breach),
        ),
        memory_floor_breach_count=_count(
            sum(Decimal("1") for row in report_rows if row.memory_floor_breach),
        ),
        average_latency_seconds=_average_decimal(
            tuple(row.max_latency_seconds for row in report_rows),
        ),
        average_memory_floor_score=_average_decimal(
            tuple(row.memory_floor_score for row in report_rows),
        ),
        rows=report_rows,
        reason_code_counts=_reason_code_counts(report_rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_source_primary_claim_latency_memory_floor_report_payload(
    report: ResearchSourcePrimaryClaimLatencyMemoryFloorReport | dict[str, Any],
) -> "FrozenJsonObject":
    if type(report) is ResearchSourcePrimaryClaimLatencyMemoryFloorReport:
        _require_hard_flags("report", report)
        payload = _public_payload(report, include_digest=True)
    elif type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
    else:
        raise ValueError(
            "report must be a ResearchSourcePrimaryClaimLatencyMemoryFloorReport",
        )
    _reject_unsafe_public_payload("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
    return _freeze_json_object(payload)


def research_source_primary_claim_latency_memory_floor_report_digest(
    report: ResearchSourcePrimaryClaimLatencyMemoryFloorReport,
) -> str:
    if type(report) is not ResearchSourcePrimaryClaimLatencyMemoryFloorReport:
        raise ValueError(
            "report must be a ResearchSourcePrimaryClaimLatencyMemoryFloorReport",
        )
    _require_hard_flags("report", report)
    return _report_digest(report)


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


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourcePrimaryClaimLatencyMemoryFloorInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_refs: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourcePrimaryClaimLatencyMemoryFloorInput:
            raise ValueError(
                "rows must contain ResearchSourcePrimaryClaimLatencyMemoryFloorInput",
            )
        _require_hard_flags("input", row)
        key = (row.claim_ref, row.capture_ref)
        if key in seen_refs:
            raise ValueError("duplicate claim_ref and capture_ref values are not allowed")
        seen_refs.add(key)
    return rows


def _row_for_claim(
    *,
    claim_ref: str,
    rows: tuple[ResearchSourcePrimaryClaimLatencyMemoryFloorInput, ...],
    config: ResearchSourcePrimaryClaimLatencyMemoryFloorConfig,
) -> ResearchSourcePrimaryClaimLatencyMemoryFloorRow:
    primary_rows = tuple(row for row in rows if row.primary)
    if not primary_rows:
        return ResearchSourcePrimaryClaimLatencyMemoryFloorRow(
            claim_digest=_digest_reference(claim_ref),
            status="block",
            input_count=_count(len(rows)),
            primary_input_count=_count(0),
            authority_family_count=_count(0),
            max_latency_seconds=_ZERO,
            average_latency_seconds=_ZERO,
            memory_floor_score=_ZERO,
            average_memory_score=_ZERO,
            latency_breach=True,
            memory_floor_breach=True,
            reason_codes=("missing_primary_claim_capture",),
        )

    latency_values = tuple(
        _duration_seconds(row.observed_at, row.captured_at) for row in primary_rows
    )
    memory_values = tuple(row.memory_score for row in primary_rows)
    max_latency = max(latency_values)
    memory_floor = min(memory_values)
    latency_breach = max_latency >= config.watch_latency_seconds
    memory_floor_breach = memory_floor <= config.watch_memory_floor_score
    reason_codes = _row_reason_codes(
        max_latency=max_latency,
        memory_floor=memory_floor,
        config=config,
    )

    return ResearchSourcePrimaryClaimLatencyMemoryFloorRow(
        claim_digest=_digest_reference(claim_ref),
        status=_row_status(reason_codes),
        input_count=_count(len(rows)),
        primary_input_count=_count(len(primary_rows)),
        authority_family_count=_count(
            len({row.authority_family_ref for row in primary_rows}),
        ),
        max_latency_seconds=max_latency,
        average_latency_seconds=_average_decimal(latency_values),
        memory_floor_score=memory_floor,
        average_memory_score=_average_decimal(memory_values),
        latency_breach=latency_breach,
        memory_floor_breach=memory_floor_breach,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    max_latency: Decimal,
    memory_floor: Decimal,
    config: ResearchSourcePrimaryClaimLatencyMemoryFloorConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if max_latency >= config.block_latency_seconds:
        reason_codes.append("primary_claim_latency_block")
    elif max_latency >= config.watch_latency_seconds:
        reason_codes.append("primary_claim_latency_watch")

    if memory_floor <= config.block_memory_floor_score:
        reason_codes.append("memory_floor_block")
    elif memory_floor <= config.watch_memory_floor_score:
        reason_codes.append("memory_floor_watch")

    if not reason_codes:
        reason_codes.append("primary_claim_latency_memory_floor_pass")
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    if reason_codes == ("missing_primary_claim_capture",):
        return "block"
    return "pass"


def _row_sort_key(row: ResearchSourcePrimaryClaimLatencyMemoryFloorRow) -> tuple[int, str]:
    return ({"block": 0, "watch": 1, "pass": 2}[row.status], row.claim_digest)


def _report_status(
    rows: tuple[ResearchSourcePrimaryClaimLatencyMemoryFloorRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourcePrimaryClaimLatencyMemoryFloorRow, ...],
    input_count: int,
) -> tuple[str, ...]:
    if input_count == 0:
        return ("empty_latency_memory_floor",)
    seen: set[str] = set()
    reason_codes: list[str] = []
    for reason_code in _REPORT_REASON_CODES:
        if any(reason_code in row.reason_codes for row in rows) and reason_code not in seen:
            seen.add(reason_code)
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchSourcePrimaryClaimLatencyMemoryFloorRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourcePrimaryClaimLatencyMemoryFloorReasonCodeCount, ...]:
    if reason_codes == ("empty_latency_memory_floor",):
        return (
            ResearchSourcePrimaryClaimLatencyMemoryFloorReasonCodeCount(
                reason_code="empty_latency_memory_floor",
                count=_ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchSourcePrimaryClaimLatencyMemoryFloorReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
        )
        for reason_code in reason_codes
        if counter[reason_code] > 0
    )


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourcePrimaryClaimLatencyMemoryFloorRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchSourcePrimaryClaimLatencyMemoryFloorRow:
            raise ValueError("rows must contain latency memory floor rows")
        _require_hard_flags("row", row)
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourcePrimaryClaimLatencyMemoryFloorReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for item in value:
        if type(item) is not ResearchSourcePrimaryClaimLatencyMemoryFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain latency memory floor reason counts",
            )
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
        _require_hard_flags("reason_code_count", item)
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allowed: tuple[str, ...],
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    for item in value:
        _require_member(field_name, item, allowed)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    return value


def _validate_row(row: ResearchSourcePrimaryClaimLatencyMemoryFloorRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.primary_input_count > row.input_count:
        raise ValueError("primary_input_count must not exceed input_count")
    if row.memory_floor_score > row.average_memory_score:
        raise ValueError("memory_floor_score must not exceed average_memory_score")
    if row.max_latency_seconds < row.average_latency_seconds:
        raise ValueError("max_latency_seconds must not be below average_latency_seconds")


def _validate_report(report: ResearchSourcePrimaryClaimLatencyMemoryFloorReport) -> None:
    if report.claim_count != _count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.input_count != sum((row.input_count for row in report.rows), _ZERO):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.latency_breach_count != _count(
        sum(Decimal("1") for row in report.rows if row.latency_breach),
    ):
        raise ValueError("latency_breach_count must match rows")
    if report.memory_floor_breach_count != _count(
        sum(Decimal("1") for row in report.rows if row.memory_floor_breach),
    ):
        raise ValueError("memory_floor_breach_count must match rows")
    if report.average_latency_seconds != _average_decimal(
        tuple(row.max_latency_seconds for row in report.rows),
    ):
        raise ValueError("average_latency_seconds must match rows")
    if report.average_memory_floor_score != _average_decimal(
        tuple(row.memory_floor_score for row in report.rows),
    ):
        raise ValueError("average_memory_floor_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.input_count)):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchSourcePrimaryClaimLatencyMemoryFloorRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(Decimal("1") for row in rows if row.status == status))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _count(len(values)))


def _count(value: int | Decimal) -> Decimal:
    return _quantize(Decimal(value))


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    delta = finished_at - started_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_digest_reference(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith("sha256:") or len(value) != 71:
        raise ValueError(f"{field_name} must be a sha256 reference")
    _require_digest_string(field_name, value.removeprefix("sha256:"))


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _digest_reference(value: str) -> str:
    return f"sha256:{sha256(('claim:' + value).encode('utf-8')).hexdigest()}"


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _public_payload(
    report: ResearchSourcePrimaryClaimLatencyMemoryFloorReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "status": report.status,
        "claim_count": report.claim_count,
        "input_count": report.input_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "latency_breach_count": report.latency_breach_count,
        "memory_floor_breach_count": report.memory_floor_breach_count,
        "average_latency_seconds": report.average_latency_seconds,
        "average_memory_floor_score": report.average_memory_floor_score,
        "rows": report.rows,
        "reason_code_counts": report.reason_code_counts,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    if include_digest:
        ready["derived_validation_digest"] = report.derived_validation_digest
    _reject_unsafe_public_payload("payload", ready)
    return ready


def _report_digest(report: ResearchSourcePrimaryClaimLatencyMemoryFloorReport) -> str:
    payload = _public_payload(report, include_digest=False)
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest_string("derived_validation_digest", digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest")
    expected_digest = sha256(
        _canonical_json(payload_without_digest).encode("utf-8"),
    ).hexdigest()
    if digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload contents")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
            if field.name != "derived_validation_digest"
        }
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value {value!r}")


def _freeze_json_object(value: dict[str, Any]) -> "FrozenJsonObject":
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if type(value) is dict:
        return _freeze_json_object(value)
    if type(value) is list:
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public payload text")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_payload(label, str(key))
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple, FrozenJsonArray)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
