"""Report-only refresh schedule for sanitized evidence-source buckets.

The module is deterministic and side-effect free. Callers provide already
sanitized source buckets and local scoring inputs; the report returns a refresh
schedule snapshot without network, storage, execution, or live-trading surfaces.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_EVIDENCE_REFRESH_SCHEDULE_CONFIG_VERSION = (
    "research-source-evidence-refresh-schedule-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = ("pass", "watch", "block")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TOKENS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "live",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "secret",
        "apikey",
        "auth",
    ),
)
_REASON_CODE_SEQUENCE = (
    "empty_source_schedule",
    "freshness_decay_pressure",
    "low_authority_pressure",
    "contradiction_exposure_pressure",
    "low_independence_pressure",
    "category_volatility_pressure",
    "refresh_overdue",
    "refresh_schedule_pass",
    "refresh_schedule_watch",
    "refresh_schedule_block",
)


@dataclass(frozen=True)
class ResearchSourceEvidenceRefreshScheduleConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_EVIDENCE_REFRESH_SCHEDULE_CONFIG_VERSION
    stale_after_seconds: Decimal = Decimal("86400.000000")
    base_refresh_interval_seconds: Decimal = Decimal("86400.000000")
    min_refresh_interval_seconds: Decimal = Decimal("900.000000")
    max_refresh_interval_seconds: Decimal = Decimal("604800.000000")
    watch_refresh_pressure_score: Decimal = Decimal("0.400000")
    block_refresh_pressure_score: Decimal = Decimal("0.750000")
    freshness_decay_weight: Decimal = Decimal("0.300000")
    authority_gap_weight: Decimal = Decimal("0.250000")
    contradiction_exposure_weight: Decimal = Decimal("0.200000")
    independence_gap_weight: Decimal = Decimal("0.150000")
    category_volatility_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceRefreshScheduleConfig:
            raise TypeError(
                "ResearchSourceEvidenceRefreshScheduleConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceRefreshScheduleConfig:
            raise ValueError(
                "config must be exactly ResearchSourceEvidenceRefreshScheduleConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_EVIDENCE_REFRESH_SCHEDULE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "stale_after_seconds",
            "base_refresh_interval_seconds",
            "min_refresh_interval_seconds",
            "max_refresh_interval_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_refresh_interval_seconds > self.base_refresh_interval_seconds:
            raise ValueError(
                "min_refresh_interval_seconds must not exceed "
                "base_refresh_interval_seconds",
            )
        if self.base_refresh_interval_seconds > self.max_refresh_interval_seconds:
            raise ValueError(
                "base_refresh_interval_seconds must not exceed "
                "max_refresh_interval_seconds",
            )
        for field_name in (
            "watch_refresh_pressure_score",
            "block_refresh_pressure_score",
            "freshness_decay_weight",
            "authority_gap_weight",
            "contradiction_exposure_weight",
            "independence_gap_weight",
            "category_volatility_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_refresh_pressure_score >= self.block_refresh_pressure_score:
            raise ValueError(
                "watch_refresh_pressure_score must be below "
                "block_refresh_pressure_score",
            )
        weight_sum = _quantize(
            self.freshness_decay_weight
            + self.authority_gap_weight
            + self.contradiction_exposure_weight
            + self.independence_gap_weight
            + self.category_volatility_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("refresh pressure weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceRefreshScheduleInput:
    source_key: str
    last_verified_at: datetime
    authority_score: Decimal
    contradiction_exposure_score: Decimal
    independence_score: Decimal
    category_volatility_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceRefreshScheduleInput:
            raise TypeError(
                "ResearchSourceEvidenceRefreshScheduleInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceRefreshScheduleInput:
            raise ValueError(
                "schedule input must be exactly "
                "ResearchSourceEvidenceRefreshScheduleInput",
            )
        _require_public_identifier("source_key", self.source_key)
        object.__setattr__(
            self,
            "last_verified_at",
            _as_utc("last_verified_at", self.last_verified_at),
        )
        for field_name in (
            "authority_score",
            "contradiction_exposure_score",
            "independence_score",
            "category_volatility_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("schedule input", self)
        _reject_unsafe_public_payload("schedule input", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceRefreshSchedulePublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceRefreshSchedulePublicPayloadItem:
            raise TypeError(
                "ResearchSourceEvidenceRefreshSchedulePublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceRefreshSchedulePublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchSourceEvidenceRefreshSchedulePublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceRefreshScheduleReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceRefreshScheduleReasonCodeCount:
            raise TypeError(
                "ResearchSourceEvidenceRefreshScheduleReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceRefreshScheduleReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchSourceEvidenceRefreshScheduleReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceRefreshScheduleRow:
    source_key: str
    last_verified_at: datetime
    source_age_seconds: Decimal
    freshness_decay_score: Decimal
    authority_score: Decimal
    authority_gap_score: Decimal
    contradiction_exposure_score: Decimal
    independence_score: Decimal
    independence_gap_score: Decimal
    category_volatility_score: Decimal
    refresh_pressure_score: Decimal
    refresh_interval_seconds: Decimal
    next_refresh_due_at: datetime
    overdue_by_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceRefreshScheduleRow:
            raise TypeError(
                "ResearchSourceEvidenceRefreshScheduleRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceRefreshScheduleRow:
            raise ValueError("row must be exactly ResearchSourceEvidenceRefreshScheduleRow")
        _require_public_identifier("source_key", self.source_key)
        object.__setattr__(
            self,
            "last_verified_at",
            _as_utc("last_verified_at", self.last_verified_at),
        )
        object.__setattr__(
            self,
            "next_refresh_due_at",
            _as_utc("next_refresh_due_at", self.next_refresh_due_at),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        for field_name in (
            "freshness_decay_score",
            "authority_score",
            "authority_gap_score",
            "contradiction_exposure_score",
            "independence_score",
            "independence_gap_score",
            "category_volatility_score",
            "refresh_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "refresh_interval_seconds",
            _require_positive_decimal(
                "refresh_interval_seconds",
                self.refresh_interval_seconds,
            ),
        )
        object.__setattr__(
            self,
            "overdue_by_seconds",
            _require_nonnegative_decimal("overdue_by_seconds", self.overdue_by_seconds),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceRefreshScheduleReport:
    generated_at: datetime
    config_version: str
    stale_after_seconds: Decimal
    base_refresh_interval_seconds: Decimal
    min_refresh_interval_seconds: Decimal
    max_refresh_interval_seconds: Decimal
    watch_refresh_pressure_score: Decimal
    block_refresh_pressure_score: Decimal
    status: str
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    overdue_source_count: Decimal
    average_refresh_pressure_score: Decimal
    max_refresh_pressure_score: Decimal
    rows: tuple[ResearchSourceEvidenceRefreshScheduleRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceEvidenceRefreshScheduleReasonCodeCount, ...]
    public_payload: tuple[ResearchSourceEvidenceRefreshSchedulePublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceRefreshScheduleReport:
            raise TypeError(
                "ResearchSourceEvidenceRefreshScheduleReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceRefreshScheduleReport:
            raise ValueError(
                "report must be exactly ResearchSourceEvidenceRefreshScheduleReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_EVIDENCE_REFRESH_SCHEDULE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "stale_after_seconds",
            "base_refresh_interval_seconds",
            "min_refresh_interval_seconds",
            "max_refresh_interval_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_refresh_pressure_score",
            "block_refresh_pressure_score",
            "average_refresh_pressure_score",
            "max_refresh_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_refresh_pressure_score >= self.block_refresh_pressure_score:
            raise ValueError(
                "watch_refresh_pressure_score must be below "
                "block_refresh_pressure_score",
            )
        _require_status("status", self.status)
        for field_name in (
            "source_count",
            "pass_count",
            "watch_count",
            "block_count",
            "overdue_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchSourceEvidenceRefreshScheduleReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_source_evidence_refresh_schedule_report(
    schedule_inputs: Sequence[ResearchSourceEvidenceRefreshScheduleInput],
    *,
    generated_at: datetime,
    config: ResearchSourceEvidenceRefreshScheduleConfig | None = None,
    public_payload: Sequence[ResearchSourceEvidenceRefreshSchedulePublicPayloadItem] = (),
) -> ResearchSourceEvidenceRefreshScheduleReport:
    """Build a local report-only evidence-source refresh schedule snapshot."""

    if config is None:
        config = ResearchSourceEvidenceRefreshScheduleConfig()
    if type(config) is not ResearchSourceEvidenceRefreshScheduleConfig:
        raise ValueError(
            "config must be a ResearchSourceEvidenceRefreshScheduleConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(schedule_inputs)
    for item in normalized_inputs:
        if item.last_verified_at > generated_at_utc:
            raise ValueError("last_verified_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = tuple(
        _row_from_input(item, generated_at=generated_at_utc, config=config)
        for item in normalized_inputs
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "stale_after_seconds": config.stale_after_seconds,
        "base_refresh_interval_seconds": config.base_refresh_interval_seconds,
        "min_refresh_interval_seconds": config.min_refresh_interval_seconds,
        "max_refresh_interval_seconds": config.max_refresh_interval_seconds,
        "watch_refresh_pressure_score": config.watch_refresh_pressure_score,
        "block_refresh_pressure_score": config.block_refresh_pressure_score,
        "status": _report_status(rows),
        "source_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "overdue_source_count": _decimal_count(
            sum(1 for row in rows if row.overdue_by_seconds > _ZERO),
        ),
        "average_refresh_pressure_score": _average(
            tuple(row.refresh_pressure_score for row in rows),
        ),
        "max_refresh_pressure_score": max(
            (row.refresh_pressure_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceEvidenceRefreshScheduleReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_evidence_refresh_schedule_report_payload(
    report: ResearchSourceEvidenceRefreshScheduleReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourceEvidenceRefreshScheduleReport:
        raise ValueError(
            "report must be a ResearchSourceEvidenceRefreshScheduleReport",
        )
    _require_hard_flags("report", report)
    return report.payload


def _row_from_input(
    item: ResearchSourceEvidenceRefreshScheduleInput,
    *,
    generated_at: datetime,
    config: ResearchSourceEvidenceRefreshScheduleConfig,
) -> ResearchSourceEvidenceRefreshScheduleRow:
    source_age = _age_seconds(generated_at, item.last_verified_at)
    freshness_decay = _freshness_decay_score(source_age, config.stale_after_seconds)
    authority_gap = _clamp_ratio(_ONE - item.authority_score)
    independence_gap = _clamp_ratio(_ONE - item.independence_score)
    pressure = _refresh_pressure_score(
        freshness_decay_score=freshness_decay,
        authority_gap_score=authority_gap,
        contradiction_exposure_score=item.contradiction_exposure_score,
        independence_gap_score=independence_gap,
        category_volatility_score=item.category_volatility_score,
        config=config,
    )
    interval = _refresh_interval_seconds(
        pressure,
        base_refresh_interval_seconds=config.base_refresh_interval_seconds,
        min_refresh_interval_seconds=config.min_refresh_interval_seconds,
        max_refresh_interval_seconds=config.max_refresh_interval_seconds,
    )
    due_at = _datetime_plus_decimal_seconds(item.last_verified_at, interval)
    overdue_by = _overdue_by_seconds(generated_at, due_at)
    status = _row_status(
        refresh_pressure_score=pressure,
        overdue_by_seconds=overdue_by,
        watch_refresh_pressure_score=config.watch_refresh_pressure_score,
        block_refresh_pressure_score=config.block_refresh_pressure_score,
    )
    return ResearchSourceEvidenceRefreshScheduleRow(
        source_key=item.source_key,
        last_verified_at=item.last_verified_at,
        source_age_seconds=source_age,
        freshness_decay_score=freshness_decay,
        authority_score=item.authority_score,
        authority_gap_score=authority_gap,
        contradiction_exposure_score=item.contradiction_exposure_score,
        independence_score=item.independence_score,
        independence_gap_score=independence_gap,
        category_volatility_score=item.category_volatility_score,
        refresh_pressure_score=pressure,
        refresh_interval_seconds=interval,
        next_refresh_due_at=due_at,
        overdue_by_seconds=overdue_by,
        status=status,
        reason_codes=_row_reason_codes(
            freshness_decay_score=freshness_decay,
            authority_gap_score=authority_gap,
            contradiction_exposure_score=item.contradiction_exposure_score,
            independence_gap_score=independence_gap,
            category_volatility_score=item.category_volatility_score,
            overdue_by_seconds=overdue_by,
            status=status,
        ),
    )


def _refresh_pressure_score(
    *,
    freshness_decay_score: Decimal,
    authority_gap_score: Decimal,
    contradiction_exposure_score: Decimal,
    independence_gap_score: Decimal,
    category_volatility_score: Decimal,
    config: ResearchSourceEvidenceRefreshScheduleConfig,
) -> Decimal:
    return _clamp_ratio(
        (freshness_decay_score * config.freshness_decay_weight)
        + (authority_gap_score * config.authority_gap_weight)
        + (contradiction_exposure_score * config.contradiction_exposure_weight)
        + (independence_gap_score * config.independence_gap_weight)
        + (category_volatility_score * config.category_volatility_weight),
    )


def _refresh_interval_seconds(
    refresh_pressure_score: Decimal,
    *,
    base_refresh_interval_seconds: Decimal,
    min_refresh_interval_seconds: Decimal,
    max_refresh_interval_seconds: Decimal,
) -> Decimal:
    raw_interval = _quantize(
        base_refresh_interval_seconds * (_ONE - refresh_pressure_score),
    )
    bounded = max(min_refresh_interval_seconds, min(max_refresh_interval_seconds, raw_interval))
    return _quantize(bounded)


def _freshness_decay_score(source_age_seconds: Decimal, stale_after_seconds: Decimal) -> Decimal:
    if source_age_seconds >= stale_after_seconds:
        return _ONE
    return _clamp_ratio(source_age_seconds / stale_after_seconds)


def _row_status(
    *,
    refresh_pressure_score: Decimal,
    overdue_by_seconds: Decimal,
    watch_refresh_pressure_score: Decimal,
    block_refresh_pressure_score: Decimal,
) -> str:
    if refresh_pressure_score >= block_refresh_pressure_score:
        return "block"
    if refresh_pressure_score >= watch_refresh_pressure_score:
        return "watch"
    if overdue_by_seconds > _ZERO:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    freshness_decay_score: Decimal,
    authority_gap_score: Decimal,
    contradiction_exposure_score: Decimal,
    independence_gap_score: Decimal,
    category_volatility_score: Decimal,
    overdue_by_seconds: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"refresh_schedule_{status}"]
    if freshness_decay_score >= Decimal("0.500000"):
        reason_codes.append("freshness_decay_pressure")
    if authority_gap_score >= Decimal("0.500000"):
        reason_codes.append("low_authority_pressure")
    if contradiction_exposure_score >= Decimal("0.500000"):
        reason_codes.append("contradiction_exposure_pressure")
    if independence_gap_score >= Decimal("0.500000"):
        reason_codes.append("low_independence_pressure")
    if category_volatility_score >= Decimal("0.500000"):
        reason_codes.append("category_volatility_pressure")
    if overdue_by_seconds > _ZERO:
        reason_codes.append("refresh_overdue")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchSourceEvidenceRefreshScheduleRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceEvidenceRefreshScheduleRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_source_schedule",)
    return _normalize_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchSourceEvidenceRefreshScheduleRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceEvidenceRefreshScheduleReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceEvidenceRefreshScheduleReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceEvidenceRefreshScheduleReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if counts[reason_code] > 0
    )


def _status_count(
    rows: tuple[ResearchSourceEvidenceRefreshScheduleRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_inputs(
    schedule_inputs: Sequence[ResearchSourceEvidenceRefreshScheduleInput],
) -> tuple[ResearchSourceEvidenceRefreshScheduleInput, ...]:
    if isinstance(schedule_inputs, (str, bytes)) or not isinstance(
        schedule_inputs,
        Sequence,
    ):
        raise ValueError("schedule_inputs must be a sequence")
    normalized: list[ResearchSourceEvidenceRefreshScheduleInput] = []
    seen: set[str] = set()
    for item in schedule_inputs:
        if type(item) is not ResearchSourceEvidenceRefreshScheduleInput:
            raise ValueError(
                "schedule_inputs must contain "
                "ResearchSourceEvidenceRefreshScheduleInput values",
            )
        _require_hard_flags("schedule input", item)
        if item.source_key in seen:
            raise ValueError("schedule_inputs must not contain duplicate source_key values")
        seen.add(item.source_key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.source_key))


def _normalize_rows(
    rows: Sequence[ResearchSourceEvidenceRefreshScheduleRow],
) -> tuple[ResearchSourceEvidenceRefreshScheduleRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceEvidenceRefreshScheduleRow] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceEvidenceRefreshScheduleRow:
            raise ValueError(
                "rows must contain ResearchSourceEvidenceRefreshScheduleRow values",
            )
        _require_hard_flags("row", row)
        if row.source_key in seen:
            raise ValueError("rows must not contain duplicate source_key values")
        seen.add(row.source_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.source_key))


def _normalize_public_payload(
    public_payload: Sequence[ResearchSourceEvidenceRefreshSchedulePublicPayloadItem],
) -> tuple[ResearchSourceEvidenceRefreshSchedulePublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchSourceEvidenceRefreshSchedulePublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchSourceEvidenceRefreshSchedulePublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchSourceEvidenceRefreshSchedulePublicPayloadItem values",
            )
        _require_hard_flags("public payload item", item)
        if item.key in seen:
            raise ValueError("public_payload must not contain duplicate keys")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_reason_code_counts(
    counts: Sequence[ResearchSourceEvidenceRefreshScheduleReasonCodeCount],
) -> tuple[ResearchSourceEvidenceRefreshScheduleReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchSourceEvidenceRefreshScheduleReasonCodeCount] = []
    seen: set[str] = set()
    for count in counts:
        if type(count) is not ResearchSourceEvidenceRefreshScheduleReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceEvidenceRefreshScheduleReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason codes")
        seen.add(count.reason_code)
        normalized.append(count)
    return tuple(
        count
        for reason_code in _REASON_CODE_SEQUENCE
        for count in normalized
        if count.reason_code == reason_code
    )


def _validate_row_consistency(row: ResearchSourceEvidenceRefreshScheduleRow) -> None:
    if row.authority_gap_score != _clamp_ratio(_ONE - row.authority_score):
        raise ValueError("authority_gap_score must match authority_score")
    if row.independence_gap_score != _clamp_ratio(_ONE - row.independence_score):
        raise ValueError("independence_gap_score must match independence_score")
    if row.next_refresh_due_at != _datetime_plus_decimal_seconds(
        row.last_verified_at,
        row.refresh_interval_seconds,
    ):
        raise ValueError("next_refresh_due_at must match refresh_interval_seconds")
    if row.status == "pass" and "refresh_schedule_pass" not in row.reason_codes:
        raise ValueError("pass rows must include refresh_schedule_pass")
    if row.status == "watch" and "refresh_schedule_watch" not in row.reason_codes:
        raise ValueError("watch rows must include refresh_schedule_watch")
    if row.status == "block" and "refresh_schedule_block" not in row.reason_codes:
        raise ValueError("block rows must include refresh_schedule_block")


def _validate_report_consistency(
    report: ResearchSourceEvidenceRefreshScheduleReport,
) -> None:
    if report.source_count != _decimal_count(len(report.rows)):
        raise ValueError("source_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    expected_overdue_count = _decimal_count(
        sum(1 for row in report.rows if row.overdue_by_seconds > _ZERO),
    )
    if report.overdue_source_count != expected_overdue_count:
        raise ValueError("overdue_source_count must match rows")
    expected_average = _average(tuple(row.refresh_pressure_score for row in report.rows))
    if report.average_refresh_pressure_score != expected_average:
        raise ValueError("average_refresh_pressure_score must match rows")
    expected_max = max(
        (row.refresh_pressure_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_refresh_pressure_score != expected_max:
        raise ValueError("max_refresh_pressure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    for row in report.rows:
        expected_status = _row_status(
            refresh_pressure_score=row.refresh_pressure_score,
            overdue_by_seconds=row.overdue_by_seconds,
            watch_refresh_pressure_score=report.watch_refresh_pressure_score,
            block_refresh_pressure_score=report.block_refresh_pressure_score,
        )
        if row.status != expected_status:
            raise ValueError("row status must match report thresholds")
        expected_overdue = _overdue_by_seconds(report.generated_at, row.next_refresh_due_at)
        if row.overdue_by_seconds != expected_overdue:
            raise ValueError("row overdue_by_seconds must match generated_at")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    seen: set[str] = set()
    for reason_code in reason_codes:
        seen.add(_require_reason_code("reason_code", reason_code))
    if not seen:
        raise ValueError("reason_codes must be nonempty")
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in seen)


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


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


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND),
    )


def _datetime_plus_decimal_seconds(start: datetime, seconds: Decimal) -> datetime:
    microseconds = int(
        (seconds * _MICROSECONDS_PER_SECOND).to_integral_value(
            rounding=ROUND_HALF_UP,
        ),
    )
    return start + timedelta(microseconds=microseconds)


def _overdue_by_seconds(generated_at: datetime, due_at: datetime) -> Decimal:
    if due_at >= generated_at:
        return _ZERO
    return _age_seconds(generated_at, due_at)


def _report_values_without_digest(
    report: ResearchSourceEvidenceRefreshScheduleReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if type(value) in (bool, Decimal, datetime):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    _reject_unsafe_public_string(f"{path}.{key}", key)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if "/" in lowered or "\\" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    tokens = set(re.findall(r"[a-z0-9]+", lowered))
    if tokens & _UNSAFE_PUBLIC_TOKENS:
        raise ValueError(f"{field_name} has unsafe public value")
    if {"source", "text"}.issubset(tokens) or {"source", "url"}.issubset(tokens):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_EVIDENCE_REFRESH_SCHEDULE_CONFIG_VERSION",
    "ResearchSourceEvidenceRefreshScheduleConfig",
    "ResearchSourceEvidenceRefreshScheduleInput",
    "ResearchSourceEvidenceRefreshSchedulePublicPayloadItem",
    "ResearchSourceEvidenceRefreshScheduleReasonCodeCount",
    "ResearchSourceEvidenceRefreshScheduleReport",
    "ResearchSourceEvidenceRefreshScheduleRow",
    "build_research_source_evidence_refresh_schedule_report",
    "research_source_evidence_refresh_schedule_report_payload",
)
