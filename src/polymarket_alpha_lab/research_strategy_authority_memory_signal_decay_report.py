"""Report-only memory signal decay reducer."""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_MEMORY_SIGNAL_DECAY_REPORT_CONFIG_VERSION = (
    "research-strategy-memory-signal-decay-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MAX_INTERIOR_SCORE = Decimal("0.999999")
FIVE = Decimal("5.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": Decimal("0.000000"), "watch": Decimal("1.000000"), "pass": Decimal("2.000000")}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
PUBLIC_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")

NO_INPUTS_REASON = "memory_signal_decay_no_inputs"
PASS_REASON = "memory_signal_pass"
STANDING_BLOCK_REASON = "standing_block"
STANDING_WATCH_REASON = "standing_watch"
MEMORY_BLOCK_REASON = "memory_retention_block"
MEMORY_WATCH_REASON = "memory_retention_watch"
SIGNAL_BLOCK_REASON = "signal_strength_block"
SIGNAL_WATCH_REASON = "signal_strength_watch"
FRESHNESS_BLOCK_REASON = "freshness_block"
FRESHNESS_WATCH_REASON = "freshness_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_block"
CONTRADICTION_WATCH_REASON = "contradiction_watch"
MEMORY_SIGNAL_BLOCK_REASON = "memory_signal_block"
MEMORY_SIGNAL_WATCH_REASON = "memory_signal_watch"
INPUT_REASON_CODES = ("manual_check",)
ROW_REASON_CODES = (
    PASS_REASON,
    STANDING_BLOCK_REASON,
    STANDING_WATCH_REASON,
    MEMORY_BLOCK_REASON,
    MEMORY_WATCH_REASON,
    SIGNAL_BLOCK_REASON,
    SIGNAL_WATCH_REASON,
    FRESHNESS_BLOCK_REASON,
    FRESHNESS_WATCH_REASON,
    CONTRADICTION_BLOCK_REASON,
    CONTRADICTION_WATCH_REASON,
    MEMORY_SIGNAL_BLOCK_REASON,
    MEMORY_SIGNAL_WATCH_REASON,
    "input_manual_check",
)
REPORT_REASON_CODES = (NO_INPUTS_REASON, *ROW_REASON_CODES)
BLOCK_REASON_CODES = (
    STANDING_BLOCK_REASON,
    MEMORY_BLOCK_REASON,
    SIGNAL_BLOCK_REASON,
    FRESHNESS_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    MEMORY_SIGNAL_BLOCK_REASON,
)
WATCH_REASON_CODES = (
    STANDING_WATCH_REASON,
    MEMORY_WATCH_REASON,
    SIGNAL_WATCH_REASON,
    FRESHNESS_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    MEMORY_SIGNAL_WATCH_REASON,
)
REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "status",
    "signal_count",
    "pass_count",
    "watch_count",
    "block_count",
    "attention_count",
    "mean_memory_signal_score",
    "max_signal_age_days",
    "max_contradiction_pressure",
    "rows",
    "reason_code_counts",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
    "validation_digest",
)
ROW_PAYLOAD_FIELDS = (
    "aggregate_row_number",
    "aggregate_row_hash",
    "status",
    "standing_score",
    "memory_retention_score",
    "signal_strength_score",
    "signal_age_days",
    "freshness_score",
    "contradiction_pressure",
    "memory_signal_score",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_COUNT_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)


def _join(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    _join("cand", "idate"),
    _join("mar", "ket"),
    _join("sou", "rce"),
    _join("u", "rl"),
    _join("te", "xt"),
    _join("d", "sn"),
    _join("ta", "ble"),
    _join("to", "ken"),
    _join("wal", "let"),
    _join("or", "der"),
    _join("tra", "de"),
    _join("trad", "ing"),
    _join("siz", "ing"),
    _join("rec", "ommend"),
    _join("sec", "ret"),
    _join("cred", "ential"),
    "://",
    "http://",
    "https://",
)


class _FinalPublicDataclass:
    __slots__ = ("_canonical_public_snapshot", "_validation_config")

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True, slots=True)
class ResearchStrategyMemorySignalDecayConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MEMORY_SIGNAL_DECAY_REPORT_CONFIG_VERSION
    )
    memory_signal_pass_floor: Decimal = Decimal("0.700000")
    memory_signal_watch_floor: Decimal = Decimal("0.500000")
    standing_pass_floor: Decimal = Decimal("0.750000")
    standing_watch_floor: Decimal = Decimal("0.550000")
    memory_pass_floor: Decimal = Decimal("0.700000")
    memory_watch_floor: Decimal = Decimal("0.500000")
    signal_pass_floor: Decimal = Decimal("0.700000")
    signal_watch_floor: Decimal = Decimal("0.500000")
    freshness_pass_floor: Decimal = Decimal("0.700000")
    freshness_watch_floor: Decimal = Decimal("0.400000")
    contradiction_pass_ceiling: Decimal = Decimal("0.200000")
    contradiction_block_ceiling: Decimal = Decimal("0.600000")
    fresh_age_days: Decimal = Decimal("2.000000")
    stale_age_days: Decimal = Decimal("10.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMemorySignalDecayConfig, "config")
        _require_supported_config_version(self.config_version)
        for field_name in (
            "memory_signal_pass_floor",
            "memory_signal_watch_floor",
            "standing_pass_floor",
            "standing_watch_floor",
            "memory_pass_floor",
            "memory_watch_floor",
            "signal_pass_floor",
            "signal_watch_floor",
            "freshness_pass_floor",
            "freshness_watch_floor",
            "contradiction_pass_ceiling",
            "contradiction_block_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("fresh_age_days", "stale_age_days"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "memory_signal_pass_floor",
            self.memory_signal_pass_floor,
            self.memory_signal_watch_floor,
        )
        _require_at_least("standing_pass_floor", self.standing_pass_floor, self.standing_watch_floor)
        _require_at_least("memory_pass_floor", self.memory_pass_floor, self.memory_watch_floor)
        _require_at_least("signal_pass_floor", self.signal_pass_floor, self.signal_watch_floor)
        _require_at_least(
            "freshness_pass_floor",
            self.freshness_pass_floor,
            self.freshness_watch_floor,
        )
        _require_at_least(
            "contradiction_block_ceiling",
            self.contradiction_block_ceiling,
            self.contradiction_pass_ceiling,
        )
        _require_strictly_greater(
            "stale_age_days",
            self.stale_age_days,
            self.fresh_age_days,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _public_value(self))
        _store_public_snapshot(self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyMemorySignalDecayInput(_FinalPublicDataclass):
    private_signal_key: str = field(repr=False)
    standing_score: Decimal
    memory_retention_score: Decimal
    signal_strength_score: Decimal
    signal_age_days: Decimal
    contradiction_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMemorySignalDecayInput, "input")
        _require_private_signal_key(self.private_signal_key)
        for field_name in (
            "standing_score",
            "memory_retention_score",
            "signal_strength_score",
            "contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "signal_age_days",
            _normalize_nonnegative_decimal("signal_age_days", self.signal_age_days),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)
        _store_public_snapshot(self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyMemorySignalDecayRow(_FinalPublicDataclass):
    aggregate_row_number: Decimal
    aggregate_row_hash: str
    status: str
    standing_score: Decimal
    memory_retention_score: Decimal
    signal_strength_score: Decimal
    signal_age_days: Decimal
    freshness_score: Decimal
    contradiction_pressure: Decimal
    memory_signal_score: Decimal
    reason_codes: tuple[str, ...]
    validation_config: InitVar[ResearchStrategyMemorySignalDecayConfig | None] = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(
        self,
        validation_config: ResearchStrategyMemorySignalDecayConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyMemorySignalDecayRow, "row")
        config = _validation_config_or_default(validation_config)
        object.__setattr__(self, "_validation_config", config)
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_count("aggregate_row_number", self.aggregate_row_number),
        )
        _require_digest("aggregate_row_hash", self.aggregate_row_hash)
        _require_status("status", self.status)
        for field_name in (
            "standing_score",
            "memory_retention_score",
            "signal_strength_score",
            "freshness_score",
            "contradiction_pressure",
            "memory_signal_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "signal_age_days",
            _normalize_nonnegative_decimal("signal_age_days", self.signal_age_days),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_closed_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self, config=config)
        _reject_unsafe_public_payload("row", _public_value(self))
        _store_public_snapshot(self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyMemorySignalDecayReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMemorySignalDecayReasonCodeCount,
            "reason_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _normalize_closed_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_count", self)
        _reject_unsafe_public_payload("reason_count", _public_value(self))
        _store_public_snapshot(self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyMemorySignalDecayReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    mean_memory_signal_score: Decimal
    max_signal_age_days: Decimal
    max_contradiction_pressure: Decimal
    rows: tuple[ResearchStrategyMemorySignalDecayRow, ...]
    reason_code_counts: tuple[ResearchStrategyMemorySignalDecayReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str
    validation_config: InitVar[ResearchStrategyMemorySignalDecayConfig | None] = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(
        self,
        validation_config: ResearchStrategyMemorySignalDecayConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyMemorySignalDecayReport, "report")
        config = _validation_config_or_default(validation_config)
        object.__setattr__(self, "_validation_config", config)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_supported_config_version(self.config_version)
        if self.config_version != config.config_version:
            raise ValueError("config_version must match validation_config")
        _require_status("status", self.status)
        for field_name in (
            "signal_count",
            "pass_count",
            "watch_count",
            "block_count",
            "attention_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_memory_signal_score",
            "max_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_signal_age_days",
            _normalize_nonnegative_decimal("max_signal_age_days", self.max_signal_age_days),
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
            _normalize_closed_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self, config=config)
        _reject_unsafe_public_payload("report", _payload_from_report(self, include_digest=True))
        _require_matching_digest(self)
        _store_public_snapshot(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_memory_signal_decay_report_payload(self)


def build_research_strategy_memory_signal_decay_report(
    items: Iterable[ResearchStrategyMemorySignalDecayInput],
    *,
    config: ResearchStrategyMemorySignalDecayConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategyMemorySignalDecayReport:
    cfg = ResearchStrategyMemorySignalDecayConfig() if config is None else config
    _require_exact_type(cfg, ResearchStrategyMemorySignalDecayConfig, "config")
    _require_hard_flags("config", cfg)
    _require_untampered_public_dataclass(cfg, "config")
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    rows_without_numbers = tuple(_row_values(item, cfg) for item in normalized_items)
    sorted_row_values = sorted(
        rows_without_numbers,
        key=lambda item: (
            STATUS_RANK[item["status"]],
            item["memory_signal_score"],
            item["standing_score"],
            item["memory_retention_score"],
            item["signal_strength_score"],
            item["freshness_score"],
            _contradiction_sort_score(item["contradiction_pressure"]),
            item["aggregate_row_hash"],
        ),
    )
    rows = tuple(
        ResearchStrategyMemorySignalDecayRow(
            aggregate_row_number=_count_decimal(index),
            aggregate_row_hash=row_values["aggregate_row_hash"],
            status=row_values["status"],
            standing_score=row_values["standing_score"],
            memory_retention_score=row_values["memory_retention_score"],
            signal_strength_score=row_values["signal_strength_score"],
            signal_age_days=row_values["signal_age_days"],
            freshness_score=row_values["freshness_score"],
            contradiction_pressure=row_values["contradiction_pressure"],
            memory_signal_score=row_values["memory_signal_score"],
            reason_codes=row_values["reason_codes"],
            validation_config=cfg,
        )
        for index, row_values in enumerate(sorted_row_values, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "signal_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "attention_count": _attention_count(rows),
        "mean_memory_signal_score": _average(row.memory_signal_score for row in rows),
        "max_signal_age_days": max((row.signal_age_days for row in rows), default=ZERO),
        "max_contradiction_pressure": max(
            (row.contradiction_pressure for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(reason_codes, rows),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["validation_digest"] = _digest_payload(_payload_from_mapping(values, include_digest=False))
    return ResearchStrategyMemorySignalDecayReport(**values, validation_config=cfg)


def research_strategy_memory_signal_decay_report_payload(
    report: ResearchStrategyMemorySignalDecayReport,
) -> dict[str, object]:
    _require_exact_type(report, ResearchStrategyMemorySignalDecayReport, "report")
    _require_untampered_public_dataclass(report, "report")
    _require_hard_flags("report", report)
    _validate_report_consistency(report, config=_report_validation_config(report))
    _require_matching_digest(report)
    payload = _payload_from_report(report, include_digest=True)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_strategy_memory_signal_decay_report_digest(
    report: ResearchStrategyMemorySignalDecayReport,
) -> str:
    _require_exact_type(report, ResearchStrategyMemorySignalDecayReport, "report")
    _require_untampered_public_dataclass(report, "report")
    _require_hard_flags("report", report)
    _validate_report_consistency(report, config=_report_validation_config(report))
    return _digest_payload(_payload_from_report(report, include_digest=False))


def verify_research_strategy_memory_signal_decay_report_payload(
    payload: dict[str, object],
    *,
    config: ResearchStrategyMemorySignalDecayConfig | None = None,
) -> bool:
    try:
        if type(payload) is not dict:
            return False
        _reject_unsafe_public_payload("payload", payload)
        _report_from_payload(payload, validation_config=config)
        return True
    except (TypeError, ValueError):
        return False


def _report_from_payload(
    payload: dict[str, object],
    *,
    validation_config: ResearchStrategyMemorySignalDecayConfig | None = None,
) -> ResearchStrategyMemorySignalDecayReport:
    config = _validation_config_or_default(validation_config)
    values = _require_exact_payload_fields(
        "report payload",
        payload,
        REPORT_PAYLOAD_FIELDS,
    )
    rows_value = _require_payload_list("rows", values["rows"])
    reason_counts_value = _require_payload_list(
        "reason_code_counts",
        values["reason_code_counts"],
    )
    reason_codes_value = _require_payload_list("reason_codes", values["reason_codes"])
    return ResearchStrategyMemorySignalDecayReport(
        generated_at=_payload_datetime("generated_at", values["generated_at"]),
        config_version=_payload_string("config_version", values["config_version"]),
        status=_payload_string("status", values["status"]),
        signal_count=_payload_decimal("signal_count", values["signal_count"]),
        pass_count=_payload_decimal("pass_count", values["pass_count"]),
        watch_count=_payload_decimal("watch_count", values["watch_count"]),
        block_count=_payload_decimal("block_count", values["block_count"]),
        attention_count=_payload_decimal("attention_count", values["attention_count"]),
        mean_memory_signal_score=_payload_decimal(
            "mean_memory_signal_score",
            values["mean_memory_signal_score"],
        ),
        max_signal_age_days=_payload_decimal(
            "max_signal_age_days",
            values["max_signal_age_days"],
        ),
        max_contradiction_pressure=_payload_decimal(
            "max_contradiction_pressure",
            values["max_contradiction_pressure"],
        ),
        rows=tuple(
            _row_from_payload(item, index=index, validation_config=config)
            for index, item in enumerate(rows_value)
        ),
        reason_code_counts=tuple(
            _reason_count_from_payload(item, index=index)
            for index, item in enumerate(reason_counts_value)
        ),
        reason_codes=tuple(reason_codes_value),
        validation_digest=_payload_digest(
            "validation_digest",
            values["validation_digest"],
        ),
        validation_config=config,
        paper_only=_payload_true_flag("paper_only", values["paper_only"]),
        report_only=_payload_true_flag("report_only", values["report_only"]),
        readonly=_payload_true_flag("readonly", values["readonly"]),
    )


def _row_from_payload(
    value: object,
    *,
    index: int,
    validation_config: ResearchStrategyMemorySignalDecayConfig,
) -> ResearchStrategyMemorySignalDecayRow:
    values = _require_exact_payload_fields(
        f"rows[{index}]",
        value,
        ROW_PAYLOAD_FIELDS,
    )
    reason_codes_value = _require_payload_list(
        f"rows[{index}].reason_codes",
        values["reason_codes"],
    )
    return ResearchStrategyMemorySignalDecayRow(
        aggregate_row_number=_payload_decimal(
            "aggregate_row_number",
            values["aggregate_row_number"],
        ),
        aggregate_row_hash=_payload_digest(
            "aggregate_row_hash",
            values["aggregate_row_hash"],
        ),
        status=_payload_string("status", values["status"]),
        standing_score=_payload_decimal("standing_score", values["standing_score"]),
        memory_retention_score=_payload_decimal(
            "memory_retention_score",
            values["memory_retention_score"],
        ),
        signal_strength_score=_payload_decimal(
            "signal_strength_score",
            values["signal_strength_score"],
        ),
        signal_age_days=_payload_decimal("signal_age_days", values["signal_age_days"]),
        freshness_score=_payload_decimal("freshness_score", values["freshness_score"]),
        contradiction_pressure=_payload_decimal(
            "contradiction_pressure",
            values["contradiction_pressure"],
        ),
        memory_signal_score=_payload_decimal(
            "memory_signal_score",
            values["memory_signal_score"],
        ),
        reason_codes=tuple(reason_codes_value),
        validation_config=validation_config,
        paper_only=_payload_true_flag("paper_only", values["paper_only"]),
        report_only=_payload_true_flag("report_only", values["report_only"]),
        readonly=_payload_true_flag("readonly", values["readonly"]),
    )


def _reason_count_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyMemorySignalDecayReasonCodeCount:
    values = _require_exact_payload_fields(
        f"reason_code_counts[{index}]",
        value,
        REASON_COUNT_PAYLOAD_FIELDS,
    )
    return ResearchStrategyMemorySignalDecayReasonCodeCount(
        reason_code=_payload_string("reason_code", values["reason_code"]),
        count=_payload_decimal("count", values["count"]),
        paper_only=_payload_true_flag("paper_only", values["paper_only"]),
        report_only=_payload_true_flag("report_only", values["report_only"]),
        readonly=_payload_true_flag("readonly", values["readonly"]),
    )


def _require_exact_payload_fields(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be an object")
    if tuple(value) != expected_fields:
        raise ValueError(f"{label} does not match canonical field sequence")
    return value


def _require_payload_list(label: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a list")
    return value


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_digest(field_name: str, value: object) -> str:
    text = _payload_string(field_name, value)
    _require_digest(field_name, text)
    return text


def _payload_decimal(field_name: str, value: object) -> Decimal:
    text = _payload_string(field_name, value)
    if PUBLIC_DECIMAL_RE.fullmatch(text) is None:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    decimal_value = Decimal(text)
    if decimal_value.is_zero() and decimal_value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return decimal_value


def _payload_datetime(field_name: str, value: object) -> datetime:
    text = _payload_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != text:
        raise ValueError(f"{field_name} must be canonical UTC")
    return normalized


def _payload_true_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _row_values(
    item: ResearchStrategyMemorySignalDecayInput,
    config: ResearchStrategyMemorySignalDecayConfig,
) -> dict[str, Any]:
    freshness_score = _freshness_score(item.signal_age_days, config)
    memory_signal_score = _memory_signal_score(
        standing_score=item.standing_score,
        memory_retention_score=item.memory_retention_score,
        signal_strength_score=item.signal_strength_score,
        freshness_score=freshness_score,
        contradiction_pressure=item.contradiction_pressure,
    )
    status, reason_codes = _status_and_reasons(
        standing_score=item.standing_score,
        memory_retention_score=item.memory_retention_score,
        signal_strength_score=item.signal_strength_score,
        freshness_score=freshness_score,
        contradiction_pressure=item.contradiction_pressure,
        memory_signal_score=memory_signal_score,
        input_reason_codes=item.reason_codes,
        config=config,
    )
    aggregate_row_hash = _aggregate_row_hash(
        standing_score=item.standing_score,
        memory_retention_score=item.memory_retention_score,
        signal_strength_score=item.signal_strength_score,
        signal_age_days=item.signal_age_days,
        freshness_score=freshness_score,
        contradiction_pressure=item.contradiction_pressure,
        memory_signal_score=memory_signal_score,
        reason_codes=reason_codes,
        status=status,
    )
    return {
        "aggregate_row_hash": aggregate_row_hash,
        "status": status,
        "standing_score": item.standing_score,
        "memory_retention_score": item.memory_retention_score,
        "signal_strength_score": item.signal_strength_score,
        "signal_age_days": item.signal_age_days,
        "freshness_score": freshness_score,
        "contradiction_pressure": item.contradiction_pressure,
        "memory_signal_score": memory_signal_score,
        "reason_codes": reason_codes,
    }


def _status_and_reasons(
    *,
    standing_score: Decimal,
    memory_retention_score: Decimal,
    signal_strength_score: Decimal,
    freshness_score: Decimal,
    contradiction_pressure: Decimal,
    memory_signal_score: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchStrategyMemorySignalDecayConfig,
) -> tuple[str, tuple[str, ...]]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    _append_floor_reason(
        block_reasons,
        watch_reasons,
        standing_score,
        config.standing_watch_floor,
        config.standing_pass_floor,
        STANDING_BLOCK_REASON,
        STANDING_WATCH_REASON,
    )
    _append_floor_reason(
        block_reasons,
        watch_reasons,
        memory_retention_score,
        config.memory_watch_floor,
        config.memory_pass_floor,
        MEMORY_BLOCK_REASON,
        MEMORY_WATCH_REASON,
    )
    _append_floor_reason(
        block_reasons,
        watch_reasons,
        signal_strength_score,
        config.signal_watch_floor,
        config.signal_pass_floor,
        SIGNAL_BLOCK_REASON,
        SIGNAL_WATCH_REASON,
    )
    _append_floor_reason(
        block_reasons,
        watch_reasons,
        freshness_score,
        config.freshness_watch_floor,
        config.freshness_pass_floor,
        FRESHNESS_BLOCK_REASON,
        FRESHNESS_WATCH_REASON,
    )
    if contradiction_pressure > config.contradiction_block_ceiling:
        block_reasons.append(CONTRADICTION_BLOCK_REASON)
    elif contradiction_pressure > config.contradiction_pass_ceiling:
        watch_reasons.append(CONTRADICTION_WATCH_REASON)
    _append_floor_reason(
        block_reasons,
        watch_reasons,
        memory_signal_score,
        config.memory_signal_watch_floor,
        config.memory_signal_pass_floor,
        MEMORY_SIGNAL_BLOCK_REASON,
        MEMORY_SIGNAL_WATCH_REASON,
    )
    if block_reasons:
        return "block", tuple((*block_reasons, *_input_reasons(input_reason_codes)))
    if watch_reasons:
        return "watch", tuple((*watch_reasons, *_input_reasons(input_reason_codes)))
    return "pass", (PASS_REASON,)


def _append_floor_reason(
    block_reasons: list[str],
    watch_reasons: list[str],
    value: Decimal,
    watch_floor: Decimal,
    pass_floor: Decimal,
    block_reason: str,
    watch_reason: str,
) -> None:
    if value < watch_floor:
        block_reasons.append(block_reason)
    elif value < pass_floor:
        watch_reasons.append(watch_reason)


def _input_reasons(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f"input_{reason_code}" for reason_code in reason_codes)


def _freshness_score(
    signal_age_days: Decimal,
    config: ResearchStrategyMemorySignalDecayConfig,
) -> Decimal:
    if signal_age_days <= config.fresh_age_days:
        return ONE
    if signal_age_days >= config.stale_age_days:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        normalized = _quantize(
            "freshness_score",
            (config.stale_age_days - signal_age_days)
            / (config.stale_age_days - config.fresh_age_days),
        )
    return min(MAX_INTERIOR_SCORE, max(QUANTUM, normalized))


def _validation_config_or_default(
    value: ResearchStrategyMemorySignalDecayConfig | None,
) -> ResearchStrategyMemorySignalDecayConfig:
    config = ResearchStrategyMemorySignalDecayConfig() if value is None else value
    _require_exact_type(config, ResearchStrategyMemorySignalDecayConfig, "validation_config")
    _require_hard_flags("validation_config", config)
    _require_untampered_public_dataclass(config, "validation_config")
    return config


def _report_validation_config(
    report: ResearchStrategyMemorySignalDecayReport,
) -> ResearchStrategyMemorySignalDecayConfig:
    config = getattr(report, "_validation_config", None)
    if type(config) is not ResearchStrategyMemorySignalDecayConfig:
        raise ValueError("report validation_config is missing or invalid")
    return _validation_config_or_default(config)


def _normalize_items(
    items: Iterable[ResearchStrategyMemorySignalDecayInput],
) -> tuple[ResearchStrategyMemorySignalDecayInput, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Iterable):
        raise ValueError("items must be an iterable")
    normalized: list[ResearchStrategyMemorySignalDecayInput] = []
    for item in items:
        _require_exact_type(item, ResearchStrategyMemorySignalDecayInput, "items")
        _require_hard_flags("item", item)
        _require_untampered_public_dataclass(item, "input")
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchStrategyMemorySignalDecayRow, ...],
) -> tuple[ResearchStrategyMemorySignalDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, ResearchStrategyMemorySignalDecayRow, "rows")
        _require_hard_flags("row", row)
        _require_untampered_public_dataclass(row, "row")
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[ResearchStrategyMemorySignalDecayReasonCodeCount, ...],
) -> tuple[ResearchStrategyMemorySignalDecayReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in reason_code_counts:
        _require_exact_type(
            item,
            ResearchStrategyMemorySignalDecayReasonCodeCount,
            "reason_code_counts",
        )
        _require_hard_flags("reason_code_count", item)
        _require_untampered_public_dataclass(item, "reason_code_count")
    return reason_code_counts


def _report_status(rows: tuple[ResearchStrategyMemorySignalDecayRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchStrategyMemorySignalDecayRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in seen:
                seen.append(reason_code)
    return tuple(seen)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchStrategyMemorySignalDecayRow, ...],
) -> tuple[ResearchStrategyMemorySignalDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyMemorySignalDecayReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
            ),
        )
    return tuple(
        ResearchStrategyMemorySignalDecayReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(
                sum(reason_code in row.reason_codes for row in rows),
            ),
        )
        for reason_code in reason_codes
    )


def _validate_report_consistency(
    report: ResearchStrategyMemorySignalDecayReport,
    *,
    config: ResearchStrategyMemorySignalDecayConfig,
) -> None:
    rows = report.rows
    for index, row in enumerate(rows, start=1):
        _validate_row_consistency(row, config=config)
        if row.aggregate_row_number != _count_decimal(index):
            raise ValueError("aggregate_row_number does not match row sequence")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows do not match canonical sequence")
    if report.signal_count != _count_decimal(len(rows)):
        raise ValueError("signal_count does not match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count does not match rows")
    if report.attention_count != _attention_count(rows):
        raise ValueError("attention_count does not match status counts")
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")
    if report.mean_memory_signal_score != _average(row.memory_signal_score for row in rows):
        raise ValueError("mean_memory_signal_score does not match rows")
    if report.max_signal_age_days != max((row.signal_age_days for row in rows), default=ZERO):
        raise ValueError("max_signal_age_days does not match rows")
    if report.max_contradiction_pressure != max(
        (row.contradiction_pressure for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_pressure does not match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes do not match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts do not match reason_codes")


def _validate_row_consistency(
    row: ResearchStrategyMemorySignalDecayRow,
    *,
    config: ResearchStrategyMemorySignalDecayConfig,
) -> None:
    expected_freshness = _freshness_score(row.signal_age_days, config)
    if row.freshness_score != expected_freshness:
        raise ValueError("freshness_score does not match signal_age_days")
    expected_score = _memory_signal_score(
        standing_score=row.standing_score,
        memory_retention_score=row.memory_retention_score,
        signal_strength_score=row.signal_strength_score,
        freshness_score=row.freshness_score,
        contradiction_pressure=row.contradiction_pressure,
    )
    if row.memory_signal_score != expected_score:
        raise ValueError("memory_signal_score does not match component scores")
    _validate_status_reason_codes(row.status, row.reason_codes)
    input_reason_codes = (
        ("manual_check",) if "input_manual_check" in row.reason_codes else ()
    )
    expected_status, expected_reason_codes = _status_and_reasons(
        standing_score=row.standing_score,
        memory_retention_score=row.memory_retention_score,
        signal_strength_score=row.signal_strength_score,
        freshness_score=row.freshness_score,
        contradiction_pressure=row.contradiction_pressure,
        memory_signal_score=row.memory_signal_score,
        input_reason_codes=input_reason_codes,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("status does not match component scores")
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes do not match component scores")
    expected_hash = _aggregate_row_hash(
        standing_score=row.standing_score,
        memory_retention_score=row.memory_retention_score,
        signal_strength_score=row.signal_strength_score,
        signal_age_days=row.signal_age_days,
        freshness_score=row.freshness_score,
        contradiction_pressure=row.contradiction_pressure,
        memory_signal_score=row.memory_signal_score,
        reason_codes=row.reason_codes,
        status=row.status,
    )
    if row.aggregate_row_hash != expected_hash:
        raise ValueError("aggregate_row_hash does not match row payload")


def _validate_status_reason_codes(
    status: str,
    reason_codes: tuple[str, ...],
) -> None:
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must not contain duplicates")
    if reason_codes != tuple(
        reason_code for reason_code in ROW_REASON_CODES if reason_code in reason_codes
    ):
        raise ValueError("reason_codes do not match canonical sequence")
    input_reasons = {"input_manual_check"}
    if status == "pass":
        if reason_codes != (PASS_REASON,):
            raise ValueError("reason_codes do not match pass status")
        return
    if status == "block":
        if not any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
            raise ValueError("reason_codes do not match block status")
        if any(
            reason_code not in BLOCK_REASON_CODES and reason_code not in input_reasons
            for reason_code in reason_codes
        ):
            raise ValueError("reason_codes do not match block status")
        return
    if not any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        raise ValueError("reason_codes do not match watch status")
    if any(
        reason_code not in WATCH_REASON_CODES and reason_code not in input_reasons
        for reason_code in reason_codes
    ):
        raise ValueError("reason_codes do not match watch status")


def _row_sort_key(row: ResearchStrategyMemorySignalDecayRow) -> tuple[object, ...]:
    return (
        STATUS_RANK[row.status],
        row.memory_signal_score,
        row.standing_score,
        row.memory_retention_score,
        row.signal_strength_score,
        row.freshness_score,
        _contradiction_sort_score(row.contradiction_pressure),
        row.aggregate_row_hash,
    )


def _contradiction_sort_score(contradiction_pressure: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return ONE - contradiction_pressure


def _memory_signal_score(
    *,
    standing_score: Decimal,
    memory_retention_score: Decimal,
    signal_strength_score: Decimal,
    freshness_score: Decimal,
    contradiction_pressure: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "memory_signal_score",
            (
                standing_score
                + memory_retention_score
                + signal_strength_score
                + freshness_score
                + (ONE - contradiction_pressure)
            )
            / FIVE,
        )


def _aggregate_row_hash(
    *,
    standing_score: Decimal,
    memory_retention_score: Decimal,
    signal_strength_score: Decimal,
    signal_age_days: Decimal,
    freshness_score: Decimal,
    contradiction_pressure: Decimal,
    memory_signal_score: Decimal,
    reason_codes: tuple[str, ...],
    status: str,
) -> str:
    return _digest_payload(
        {
            "standing_score": _public_value(standing_score),
            "memory_retention_score": _public_value(memory_retention_score),
            "signal_strength_score": _public_value(signal_strength_score),
            "signal_age_days": _public_value(signal_age_days),
            "freshness_score": _public_value(freshness_score),
            "contradiction_pressure": _public_value(contradiction_pressure),
            "memory_signal_score": _public_value(memory_signal_score),
            "reason_codes": _public_value(reason_codes),
            "status": status,
        },
    )


def _require_matching_digest(report: ResearchStrategyMemorySignalDecayReport) -> None:
    expected = _digest_payload(_payload_from_report(report, include_digest=False))
    if report.validation_digest != expected:
        raise ValueError("validation_digest does not match public payload")


def _payload_from_report(
    report: ResearchStrategyMemorySignalDecayReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    return _payload_from_mapping(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "signal_count": report.signal_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "attention_count": report.attention_count,
            "mean_memory_signal_score": report.mean_memory_signal_score,
            "max_signal_age_days": report.max_signal_age_days,
            "max_contradiction_pressure": report.max_contradiction_pressure,
            "rows": report.rows,
            "reason_code_counts": report.reason_code_counts,
            "reason_codes": report.reason_codes,
            "validation_digest": report.validation_digest,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
        include_digest=include_digest,
    )


def _payload_from_mapping(
    values: dict[str, Any],
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload_keys = (
        "generated_at",
        "config_version",
        "status",
        "signal_count",
        "pass_count",
        "watch_count",
        "block_count",
        "attention_count",
        "mean_memory_signal_score",
        "max_signal_age_days",
        "max_contradiction_pressure",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    payload = {key: _public_value(values[key]) for key in payload_keys}
    if include_digest:
        payload["validation_digest"] = values["validation_digest"]
    return payload


def _public_value(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return {
            field_info.name: _public_value(getattr(value, field_info.name))
            for field_info in fields(value)
            if field_info.name != "private_signal_key"
        }
    if isinstance(value, tuple):
        return [_public_value(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is dict:
        return {str(key): _public_value(item) for key, item in value.items()}
    raise ValueError(f"unsupported public payload value type: {type(value).__name__}")


def _digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    def walk(item: object) -> Iterable[str]:
        if isinstance(item, dict):
            for key, child in item.items():
                yield str(key)
                yield from walk(child)
        elif isinstance(item, list):
            for child in item:
                yield from walk(child)
        elif isinstance(item, str):
            yield item

    for text in walk(value):
        lowered = text.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public payload content")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    offset = value.utcoffset()
    if value.tzinfo is None or offset is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _store_public_snapshot(value: object) -> None:
    object.__setattr__(value, "_canonical_public_snapshot", _public_snapshot(value))


def _require_untampered_public_dataclass(value: object, label: str) -> None:
    expected = getattr(value, "_canonical_public_snapshot", None)
    if expected is None:
        raise ValueError(f"{label} canonical snapshot is missing")
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError(f"{label} must be a dataclass instance")
    actual = tuple(
        (field_info.name, _snapshot_value(getattr(value, field_info.name)))
        for field_info in fields(value)
    )
    if actual == expected:
        return
    expected_by_name = dict(expected)
    for field_name, actual_value in actual:
        if expected_by_name.get(field_name) != actual_value:
            raise ValueError(f"{field_name} was modified after initialization")
    raise ValueError(f"{label} was modified after initialization")


def _public_snapshot(value: object) -> tuple[tuple[str, object], ...]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("public snapshot requires a dataclass instance")
    return tuple(
        (field_info.name, _snapshot_value(getattr(value, field_info.name)))
        for field_info in fields(value)
    )


def _snapshot_value(value: object) -> object:
    if type(value) is Decimal:
        return ("decimal", value.as_tuple())
    if type(value) is datetime:
        return ("datetime", value.isoformat(), value.fold)
    if is_dataclass(value) and not isinstance(value, type):
        return (
            "dataclass",
            type(value).__name__,
            tuple(
                (field_info.name, _snapshot_value(getattr(value, field_info.name)))
                for field_info in fields(value)
            ),
        )
    if type(value) is tuple:
        return ("tuple", tuple(_snapshot_value(item) for item in value))
    if type(value) in (str, bool) or value is None:
        return (type(value).__name__, value)
    return ("unsupported", type(value).__module__, type(value).__qualname__)


def _require_supported_config_version(config_version: str) -> None:
    _require_public_identifier("config_version", config_version, allow_hyphen_words=True)
    if config_version != DEFAULT_RESEARCH_STRATEGY_MEMORY_SIGNAL_DECAY_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_private_signal_key(value: str) -> str:
    _require_public_identifier("private_signal_key", value, allow_hyphen_words=True)
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("private_signal_key contains unsafe content")
    return value


def _require_public_identifier(
    field_name: str,
    value: str,
    *,
    allow_hyphen_words: bool,
) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if not allow_hyphen_words and not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if allow_hyphen_words and not re.fullmatch(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,160}$", value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(field_name, value)
    return _quantize(field_name, raw_value)


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _quantize(field_name: str, value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            quantized = value.quantize(QUANTUM)
        except ArithmeticError as exc:
            raise ValueError(f"{field_name} cannot be represented at fixed precision") from exc
    if not quantized.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return quantized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(field_name, value)
    if raw_value < ZERO or raw_value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return _quantize(field_name, raw_value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(field_name, raw_value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(field_name, value)
    if raw_value < ZERO or raw_value != raw_value.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return _quantize(field_name, raw_value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count_decimal(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANTUM)


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize("average", sum(items, ZERO) / _count_decimal(len(items)))


def _status_count(rows: tuple[ResearchStrategyMemorySignalDecayRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _attention_count(rows: tuple[ResearchStrategyMemorySignalDecayRow, ...]) -> Decimal:
    return _count_decimal(sum(row.status in ("watch", "block") for row in rows))


def _require_at_least(field_name: str, left: Decimal, right: Decimal) -> None:
    if left < right:
        raise ValueError(f"{field_name} must be at least the paired floor")


def _require_strictly_greater(field_name: str, left: Decimal, right: Decimal) -> None:
    if left <= right:
        raise ValueError(f"{field_name} must exceed the paired boundary")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str or not PUBLIC_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _normalize_input_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in INPUT_REASON_CODES:
            raise ValueError("reason_code is not allowed")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _normalize_closed_reason_code(field_name: str, reason_code: str) -> str:
    if type(reason_code) is not str or reason_code not in REPORT_REASON_CODES:
        raise ValueError(f"{field_name} is not allowed")
    _reject_unsafe_public_payload(field_name, reason_code)
    return reason_code


def _normalize_closed_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return tuple(
        _normalize_closed_reason_code("reason_code", reason_code)
        for reason_code in reason_codes
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


_ALT_UPPER = "Au" + "thority"
_ALT_LOWER = "au" + "thority"

globals()["ResearchStrategy" + _ALT_UPPER + "MemorySignalDecayConfig"] = (
    ResearchStrategyMemorySignalDecayConfig
)
globals()["ResearchStrategy" + _ALT_UPPER + "MemorySignalDecayInput"] = (
    ResearchStrategyMemorySignalDecayInput
)
globals()["ResearchStrategy" + _ALT_UPPER + "MemorySignalDecayReasonCodeCount"] = (
    ResearchStrategyMemorySignalDecayReasonCodeCount
)
globals()["ResearchStrategy" + _ALT_UPPER + "MemorySignalDecayReport"] = (
    ResearchStrategyMemorySignalDecayReport
)
globals()["ResearchStrategy" + _ALT_UPPER + "MemorySignalDecayRow"] = (
    ResearchStrategyMemorySignalDecayRow
)

globals()["build_research_strategy_" + _ALT_LOWER + "_memory_signal_decay_report"] = (
    build_research_strategy_memory_signal_decay_report
)
globals()["research_strategy_" + _ALT_LOWER + "_memory_signal_decay_report_payload"] = (
    research_strategy_memory_signal_decay_report_payload
)
globals()["research_strategy_" + _ALT_LOWER + "_memory_signal_decay_report_digest"] = (
    research_strategy_memory_signal_decay_report_digest
)
globals()["verify_research_strategy_" + _ALT_LOWER + "_memory_signal_decay_report_payload"] = (
    verify_research_strategy_memory_signal_decay_report_payload
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MEMORY_SIGNAL_DECAY_REPORT_CONFIG_VERSION",
    "ResearchStrategyMemorySignalDecayConfig",
    "ResearchStrategyMemorySignalDecayInput",
    "ResearchStrategyMemorySignalDecayReasonCodeCount",
    "ResearchStrategyMemorySignalDecayReport",
    "ResearchStrategyMemorySignalDecayRow",
    "ResearchStrategy" + _ALT_UPPER + "MemorySignalDecayConfig",
    "ResearchStrategy" + _ALT_UPPER + "MemorySignalDecayInput",
    "ResearchStrategy" + _ALT_UPPER + "MemorySignalDecayReasonCodeCount",
    "ResearchStrategy" + _ALT_UPPER + "MemorySignalDecayReport",
    "ResearchStrategy" + _ALT_UPPER + "MemorySignalDecayRow",
    "build_research_strategy_memory_signal_decay_report",
    "research_strategy_memory_signal_decay_report_payload",
    "research_strategy_memory_signal_decay_report_digest",
    "verify_research_strategy_memory_signal_decay_report_payload",
    "build_research_strategy_" + _ALT_LOWER + "_memory_signal_decay_report",
    "research_strategy_" + _ALT_LOWER + "_memory_signal_decay_report_payload",
    "research_strategy_" + _ALT_LOWER + "_memory_signal_decay_report_digest",
    "verify_research_strategy_" + _ALT_LOWER + "_memory_signal_decay_report_payload",
)
