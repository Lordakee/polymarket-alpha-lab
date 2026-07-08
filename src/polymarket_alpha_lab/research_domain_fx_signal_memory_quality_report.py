"""Public-safe FX signal memory quality report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_FX_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION",
    "ResearchDomainFxSignalMemoryInput",
    "ResearchDomainFxSignalMemoryQualityConfig",
    "ResearchDomainFxSignalMemoryQualityReasonCodeCount",
    "ResearchDomainFxSignalMemoryQualityReport",
    "ResearchDomainFxSignalMemoryQualityRow",
    "build_research_domain_fx_signal_memory_quality_report",
    "research_domain_fx_signal_memory_quality_report_payload",
)


DEFAULT_RESEARCH_DOMAIN_FX_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION = (
    "research-domain-fx-signal-memory-quality-report-v0"
)

COUNT_QUANTUM = Decimal("1")
VALUE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_VALUE = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
FX_MEMORY_INPUTS = (
    "central_bank",
    "rates",
    "macro_release",
    "intervention",
    "cross_asset",
)
PASS_ROW_REASON_CODE = "fx_memory_clear"
MISSING_REQUIRED_INPUT_REASON_CODE = "fx_memory_required_input_missing"
BLOCK_REASON_CODES = (
    "fx_memory_stale_block",
    "fx_memory_conflict_block",
    "fx_memory_missing_block",
)
WATCH_REASON_CODES = (
    "fx_memory_stale_watch",
    "fx_memory_conflict_watch",
    "fx_memory_missing_watch",
)
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_ROW_REASON_CODE,)
REPORT_REASON_PRIORITY = (
    MISSING_REQUIRED_INPUT_REASON_CODE,
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
)
HEX_CHARS = frozenset("0123456789abcdef")
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "broker",
        "execution",
        "database",
        "network",
        "private_key",
        "signing",
        "position",
        "buy",
        "sell",
        "recom" + "mendation",
        "siz" + "ing",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchDomainFxSignalMemoryQualityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_FX_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
    )
    watch_stale_after_hours: Decimal = Decimal("12.000000")
    block_stale_after_hours: Decimal = Decimal("48.000000")
    watch_conflict_count: Decimal = Decimal("1")
    block_conflict_count: Decimal = Decimal("3")
    watch_missing_count: Decimal = Decimal("1")
    block_missing_count: Decimal = Decimal("2")
    required_memory_inputs: tuple[str, ...] = FX_MEMORY_INPUTS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainFxSignalMemoryQualityConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_FX_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_stale_after_hours", "block_stale_after_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_conflict_count",
            "block_conflict_count",
            "watch_missing_count",
            "block_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_memory_inputs",
            _require_memory_inputs(
                "required_memory_inputs",
                self.required_memory_inputs,
            ),
        )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainFxSignalMemoryInput(_FinalPublicDataclass):
    memory_input: str
    age_hours: Decimal
    conflict_count: Decimal
    missing_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainFxSignalMemoryInput, "input")
        _require_memory_input("memory_input", self.memory_input)
        object.__setattr__(
            self,
            "age_hours",
            _require_nonnegative_decimal("age_hours", self.age_hours),
        )
        for field_name in ("conflict_count", "missing_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchDomainFxSignalMemoryQualityRow(_FinalPublicDataclass):
    memory_input: str
    memory_status: str
    age_hours: Decimal
    conflict_count: Decimal
    missing_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainFxSignalMemoryQualityRow, "row")
        _require_memory_input("memory_input", self.memory_input)
        _require_status("memory_status", self.memory_status)
        object.__setattr__(
            self,
            "age_hours",
            _require_nonnegative_decimal("age_hours", self.age_hours),
        )
        for field_name in ("conflict_count", "missing_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchDomainFxSignalMemoryQualityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    memory_input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainFxSignalMemoryQualityReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be a supported row reason code")
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "memory_input_ratio",
            _require_ratio_decimal("memory_input_ratio", self.memory_input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchDomainFxSignalMemoryQualityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    memory_input_count: Decimal
    required_memory_input_count: Decimal
    missing_required_memory_input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_age_hours: Decimal
    total_conflict_count: Decimal
    total_missing_count: Decimal
    status: str
    forecast_handoff_status: str
    missing_memory_inputs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchDomainFxSignalMemoryQualityReasonCodeCount, ...]
    rows: tuple[ResearchDomainFxSignalMemoryQualityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainFxSignalMemoryQualityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_FX_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "memory_input_count",
            "required_memory_input_count",
            "missing_required_memory_input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_conflict_count",
            "total_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_age_hours",
            _require_nonnegative_decimal("max_age_hours", self.max_age_hours),
        )
        _require_status("status", self.status)
        _require_status("forecast_handoff_status", self.forecast_handoff_status)
        if self.forecast_handoff_status != self.status:
            raise ValueError("forecast_handoff_status must match status")
        object.__setattr__(
            self,
            "missing_memory_inputs",
            _require_memory_inputs("missing_memory_inputs", self.missing_memory_inputs),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_research_domain_fx_signal_memory_quality_report(
    memory_inputs: Iterable[ResearchDomainFxSignalMemoryInput],
    *,
    config: ResearchDomainFxSignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainFxSignalMemoryQualityReport:
    if type(config) is not ResearchDomainFxSignalMemoryQualityConfig:
        raise ValueError("config must be a ResearchDomainFxSignalMemoryQualityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(memory_inputs)
    for item in inputs:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be in the future")
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in inputs),
            key=_row_sort_key,
        ),
    )
    missing_inputs = _missing_required_memory_inputs(rows=rows, config=config)
    status = _report_status(rows=rows, missing_inputs=missing_inputs)
    return ResearchDomainFxSignalMemoryQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        memory_input_count=_count(len(rows)),
        required_memory_input_count=_count(len(config.required_memory_inputs)),
        missing_required_memory_input_count=_count(len(missing_inputs)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        max_age_hours=_max_decimal(tuple(row.age_hours for row in rows)),
        total_conflict_count=_sum_decimal(tuple(row.conflict_count for row in rows)),
        total_missing_count=_sum_decimal(tuple(row.missing_count for row in rows)),
        status=status,
        forecast_handoff_status=status,
        missing_memory_inputs=missing_inputs,
        reason_codes=_report_reason_codes(rows=rows, missing_inputs=missing_inputs),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_domain_fx_signal_memory_quality_report_payload(
    report: ResearchDomainFxSignalMemoryQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainFxSignalMemoryQualityReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_materialized_fields(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError("report must be a ResearchDomainFxSignalMemoryQualityReport")


@dataclass(frozen=True)
class _PayloadFlags:
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


def _row_from_input(
    item: ResearchDomainFxSignalMemoryInput,
    *,
    config: ResearchDomainFxSignalMemoryQualityConfig,
) -> ResearchDomainFxSignalMemoryQualityRow:
    reason_codes = _row_reason_codes(item, config=config)
    return ResearchDomainFxSignalMemoryQualityRow(
        memory_input=item.memory_input,
        memory_status=_row_status(reason_codes),
        age_hours=item.age_hours,
        conflict_count=item.conflict_count,
        missing_count=item.missing_count,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchDomainFxSignalMemoryInput,
    *,
    config: ResearchDomainFxSignalMemoryQualityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.age_hours >= config.block_stale_after_hours:
        reason_codes.append("fx_memory_stale_block")
    elif item.age_hours >= config.watch_stale_after_hours:
        reason_codes.append("fx_memory_stale_watch")

    if item.conflict_count >= config.block_conflict_count:
        reason_codes.append("fx_memory_conflict_block")
    elif item.conflict_count >= config.watch_conflict_count:
        reason_codes.append("fx_memory_conflict_watch")

    if item.missing_count >= config.block_missing_count:
        reason_codes.append("fx_memory_missing_block")
    elif item.missing_count >= config.watch_missing_count:
        reason_codes.append("fx_memory_missing_watch")

    if not reason_codes:
        reason_codes.append(PASS_ROW_REASON_CODE)
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    *,
    rows: tuple[ResearchDomainFxSignalMemoryQualityRow, ...],
    missing_inputs: tuple[str, ...],
) -> str:
    if missing_inputs or any(row.memory_status == "block" for row in rows):
        return "block"
    if any(row.memory_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    rows: tuple[ResearchDomainFxSignalMemoryQualityRow, ...],
    missing_inputs: tuple[str, ...],
) -> tuple[str, ...]:
    status = _report_status(rows=rows, missing_inputs=missing_inputs)
    reason_codes = [f"fx_memory_quality_{status}"]
    row_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_ROW_REASON_CODE
    )
    if missing_inputs:
        reason_codes.append(MISSING_REQUIRED_INPUT_REASON_CODE)
    for reason_code in REPORT_REASON_PRIORITY:
        if reason_code != MISSING_REQUIRED_INPUT_REASON_CODE and reason_code in row_reasons:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchDomainFxSignalMemoryQualityRow, ...],
) -> tuple[ResearchDomainFxSignalMemoryQualityReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    priority = {
        reason_code: index
        for index, reason_code in enumerate(
            (PASS_ROW_REASON_CODE,) + BLOCK_REASON_CODES + WATCH_REASON_CODES,
        )
    }
    return tuple(
        ResearchDomainFxSignalMemoryQualityReasonCodeCount(
            reason_code=reason_code,
            count=count,
            memory_input_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(value), reason_code) for reason_code, value in counter.items()),
            key=lambda item: (-item[0], priority.get(item[1], 999), item[1]),
        )
    )


def _normalize_inputs(
    memory_inputs: Iterable[ResearchDomainFxSignalMemoryInput],
) -> tuple[ResearchDomainFxSignalMemoryInput, ...]:
    if isinstance(memory_inputs, (str, bytes)):
        raise ValueError("memory_inputs must be an iterable")
    try:
        items = tuple(memory_inputs)
    except TypeError as exc:
        raise ValueError("memory_inputs must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchDomainFxSignalMemoryInput:
            raise ValueError("memory_inputs must contain ResearchDomainFxSignalMemoryInput")
        _require_hard_flags("input", item)
        if item.memory_input in seen:
            raise ValueError("memory_input values must be unique")
        seen.add(item.memory_input)
    return items


def _missing_required_memory_inputs(
    *,
    rows: tuple[ResearchDomainFxSignalMemoryQualityRow, ...],
    config: ResearchDomainFxSignalMemoryQualityConfig,
) -> tuple[str, ...]:
    present = {row.memory_input for row in rows}
    return tuple(
        memory_input
        for memory_input in config.required_memory_inputs
        if memory_input not in present
    )


def _validate_config(config: ResearchDomainFxSignalMemoryQualityConfig) -> None:
    if config.block_stale_after_hours <= config.watch_stale_after_hours:
        raise ValueError("block_stale_after_hours must exceed watch_stale_after_hours")
    if config.block_conflict_count <= config.watch_conflict_count:
        raise ValueError("block_conflict_count must exceed watch_conflict_count")
    if config.block_missing_count <= config.watch_missing_count:
        raise ValueError("block_missing_count must exceed watch_missing_count")


def _validate_row(row: ResearchDomainFxSignalMemoryQualityRow) -> None:
    if row.memory_status != _row_status(row.reason_codes):
        raise ValueError("memory_status must match reason_codes")


def _validate_report_materialized_fields(
    report: ResearchDomainFxSignalMemoryQualityReport,
) -> None:
    if report.memory_input_count != _count(len(report.rows)):
        raise ValueError("memory_input_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.memory_input_count:
        raise ValueError("status counts must match memory_input_count")
    if report.missing_required_memory_input_count != _count(
        len(report.missing_memory_inputs),
    ):
        raise ValueError("missing_required_memory_input_count must match missing inputs")
    if report.max_age_hours != _max_decimal(tuple(row.age_hours for row in report.rows)):
        raise ValueError("max_age_hours must match rows")
    if report.total_conflict_count != _sum_decimal(
        tuple(row.conflict_count for row in report.rows),
    ):
        raise ValueError("total_conflict_count must match rows")
    if report.total_missing_count != _sum_decimal(
        tuple(row.missing_count for row in report.rows),
    ):
        raise ValueError("total_missing_count must match rows")
    status = _report_status(rows=report.rows, missing_inputs=report.missing_memory_inputs)
    if report.status != status:
        raise ValueError("status must match rows and missing inputs")
    if report.reason_codes != _report_reason_codes(
        rows=report.rows,
        missing_inputs=report.missing_memory_inputs,
    ):
        raise ValueError("reason_codes must match rows and missing inputs")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: Iterable[ResearchDomainFxSignalMemoryQualityRow],
) -> tuple[ResearchDomainFxSignalMemoryQualityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in values:
        if type(row) is not ResearchDomainFxSignalMemoryQualityRow:
            raise ValueError("rows must contain ResearchDomainFxSignalMemoryQualityRow")
        _require_hard_flags("row", row)
        if row.memory_input in seen:
            raise ValueError("memory_input values must be unique")
        seen.add(row.memory_input)
    return tuple(sorted(values, key=_row_sort_key))


def _require_reason_code_counts(
    values: Iterable[ResearchDomainFxSignalMemoryQualityReasonCodeCount],
) -> tuple[ResearchDomainFxSignalMemoryQualityReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for value in counts:
        if type(value) is not ResearchDomainFxSignalMemoryQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchDomainFxSignalMemoryQualityReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
    priority = {
        reason_code: index
        for index, reason_code in enumerate(
            (PASS_ROW_REASON_CODE,) + BLOCK_REASON_CODES + WATCH_REASON_CODES,
        )
    }
    return tuple(
        sorted(
            counts,
            key=lambda item: (
                -item.count,
                priority.get(item.reason_code, 999),
                item.reason_code,
            ),
        ),
    )


def _require_memory_inputs(field_name: str, values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        inputs = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    seen: set[str] = set()
    for memory_input in inputs:
        _require_memory_input(field_name, memory_input)
        if memory_input in seen:
            raise ValueError(f"{field_name} values must be unique")
        seen.add(memory_input)
    return inputs


def _require_memory_input(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in FX_MEMORY_INPUTS:
        raise ValueError(f"{field_name} must be a supported FX memory input")


def _require_report_reason_codes(values: Iterable[str]) -> tuple[str, ...]:
    reason_codes = _require_reason_codes(values, require_nonempty=True)
    for reason_code in reason_codes:
        if (
            not reason_code.startswith("fx_memory_quality_")
            and reason_code not in REPORT_REASON_PRIORITY
        ):
            raise ValueError("reason_codes must contain supported report reason codes")
    return reason_codes


def _require_reason_codes(
    values: Iterable[str],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_string("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return _require_nonnegative_decimal(field_name, value, quantum=COUNT_QUANTUM)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be less than or equal to 1")
    return normalized


def _require_nonnegative_decimal(
    field_name: str,
    value: object,
    *,
    quantum: Decimal = VALUE_QUANTUM,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value, quantum)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    try:
        require_paper_only_flags(label, value)
    except ValueError as exc:
        raise ValueError(f"{label} {exc}") from exc


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value), COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_VALUE
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_COUNT
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO_COUNT)
    return _quantize(total, COUNT_QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_VALUE
    return _quantize(max(values))


def _status_count(
    rows: tuple[ResearchDomainFxSignalMemoryQualityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.memory_status == status))


def _quantize(value: Decimal, quantum: Decimal = VALUE_QUANTUM) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _row_sort_key(
    row: ResearchDomainFxSignalMemoryQualityRow,
) -> tuple[Decimal, Decimal]:
    return (-_status_weight(row.memory_status), _memory_input_weight(row.memory_input))


def _status_weight(status: str) -> Decimal:
    if status == "block":
        return Decimal("2")
    if status == "watch":
        return Decimal("1")
    return Decimal("0")


def _memory_input_weight(memory_input: str) -> Decimal:
    return Decimal(FX_MEMORY_INPUTS.index(memory_input))


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        _reject_foreign_dataclass(value)
        _require_hard_flags("dataclass", value)
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {
            _json_key(key): _json_ready(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value {type(value).__name__}")


def _json_key(value: object) -> str:
    if type(value) is not str:
        raise ValueError("payload keys must be strings")
    _require_public_string("payload key", value)
    return value


def _reject_foreign_dataclass(value: object) -> None:
    if not isinstance(value, _FinalPublicDataclass):
        raise ValueError("only supported public dataclasses may be serialized")


def _derived_validation_digest(report: ResearchDomainFxSignalMemoryQualityReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    unsigned = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    public = _json_ready(value) if is_dataclass(value) else value
    _walk_public_payload(label, public)


def _walk_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_string(f"{label}.{key}", key)
            _walk_public_payload(f"{label}.{key}", item)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_public_payload(f"{label}[{index}]", item)
    elif type(value) is str:
        if len(value) == 64 and all(character in HEX_CHARS for character in value):
            return
        _reject_unsafe_string(label, value)
    elif type(value) in (bool, type(None), int, float):
        return
    elif type(value) in (Decimal, datetime):
        return
    else:
        raise ValueError(f"{label} contains unsafe public value")


def _reject_unsafe_string(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public content")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be serialized strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)
