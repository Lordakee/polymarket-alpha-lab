"""Pure report-only memory probability cost guard research report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_MEMORY_PROBABILITY_COST_GUARD_REPORT_CONFIG_VERSION = (
    "research-market-memory-probability-cost-guard-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "memory_probability_cost_guard_"
NO_INPUTS_REASON = REASON_PREFIX + "no_inputs"
PASS_REASON = REASON_PREFIX + STATUS_PASS
WATCH_REASON = REASON_PREFIX + STATUS_WATCH
BLOCK_REASON = REASON_PREFIX + STATUS_BLOCK
PROBABILITY_GAP_WATCH_REASON = REASON_PREFIX + "probability_gap_watch"
PROBABILITY_GAP_BLOCK_REASON = REASON_PREFIX + "probability_gap_block"
COST_RATIO_WATCH_REASON = REASON_PREFIX + "cost_ratio_watch"
COST_RATIO_BLOCK_REASON = REASON_PREFIX + "cost_ratio_block"
MEMORY_DECAY_WATCH_REASON = REASON_PREFIX + "memory_decay_watch"
MEMORY_DECAY_BLOCK_REASON = REASON_PREFIX + "memory_decay_block"

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIXTY_FOUR = 64
PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FLAG_FIELDS = ("paper_only", "report_only", "readonly")
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
REASON_RANK = {
    NO_INPUTS_REASON: 0,
    BLOCK_REASON: 1,
    COST_RATIO_BLOCK_REASON: 2,
    MEMORY_DECAY_BLOCK_REASON: 3,
    PROBABILITY_GAP_BLOCK_REASON: 4,
    COST_RATIO_WATCH_REASON: 5,
    MEMORY_DECAY_WATCH_REASON: 6,
    PROBABILITY_GAP_WATCH_REASON: 7,
    WATCH_REASON: 8,
    PASS_REASON: 9,
}


def _join(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join("ra", "w"),
    _join("can", "didate"),
    _join("sou", "rce"),
    _join("u", "rl"),
    _join("te", "xt"),
    _join("d", "sn"),
    _join("ta", "ble"),
    _join("to", "ken"),
    _join("d", "b"),
    _join("data", "base"),
    _join("net", "work"),
    _join("wal", "let"),
    _join("au", "th"),
    _join("or", "der"),
    _join("li", "ve"),
    _join("tra", "ding"),
    _join("siz", "ing"),
    _join("reco", "mmendation"),
    _join("sec", "ret"),
    _join("private", "_", "key"),
    _join("a", "pi", "_", "key"),
    "://",
    "?",
)


@dataclass(frozen=True)
class ResearchMarketMemoryProbabilityCostGuardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_MEMORY_PROBABILITY_COST_GUARD_REPORT_CONFIG_VERSION
    )
    watch_probability_gap_ratio: Decimal = Decimal("0.080000")
    block_probability_gap_ratio: Decimal = Decimal("0.200000")
    watch_cost_ratio: Decimal = Decimal("0.030000")
    block_cost_ratio: Decimal = Decimal("0.080000")
    watch_memory_decay_ratio: Decimal = Decimal("0.200000")
    block_memory_decay_ratio: Decimal = Decimal("0.400000")
    probability_gap_weight: Decimal = Decimal("0.400000")
    cost_weight: Decimal = Decimal("0.300000")
    memory_decay_weight: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketMemoryProbabilityCostGuardConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketMemoryProbabilityCostGuardConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_id("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_MEMORY_PROBABILITY_COST_GUARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_probability_gap_ratio",
            "block_probability_gap_ratio",
            "watch_cost_ratio",
            "block_cost_ratio",
            "watch_memory_decay_ratio",
            "block_memory_decay_ratio",
            "probability_gap_weight",
            "cost_weight",
            "memory_decay_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "watch_probability_gap_ratio",
            self.watch_probability_gap_ratio,
            "block_probability_gap_ratio",
            self.block_probability_gap_ratio,
        )
        _require_less_than(
            "watch_cost_ratio",
            self.watch_cost_ratio,
            "block_cost_ratio",
            self.block_cost_ratio,
        )
        _require_less_than(
            "watch_memory_decay_ratio",
            self.watch_memory_decay_ratio,
            "block_memory_decay_ratio",
            self.block_memory_decay_ratio,
        )
        if (
            _quantize(
                self.probability_gap_weight
                + self.cost_weight
                + self.memory_decay_weight,
            )
            != ONE
        ):
            raise ValueError(
                "probability_gap_weight, cost_weight, and memory_decay_weight "
                "must sum to one",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketMemoryProbabilityCostGuardObservation:
    record_ref: str
    sample_ref: str
    observed_at: datetime
    memory_probability: Decimal
    current_probability: Decimal
    cost_ratio: Decimal
    memory_decay_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketMemoryProbabilityCostGuardObservation does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketMemoryProbabilityCostGuardObservation,
            "observation",
        )
        object.__setattr__(self, "record_ref", _require_raw_ref("record_ref", self.record_ref))
        object.__setattr__(self, "sample_ref", _require_raw_ref("sample_ref", self.sample_ref))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "memory_probability",
            "current_probability",
            "cost_ratio",
            "memory_decay_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketMemoryProbabilityCostGuardPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketMemoryProbabilityCostGuardPublicPayloadItem does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketMemoryProbabilityCostGuardPublicPayloadItem,
            "public payload item",
        )
        object.__setattr__(self, "key", _require_public_id("key", self.key))
        object.__setattr__(self, "value", _require_public_value("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchMarketMemoryProbabilityCostGuardRow:
    record_digest: str
    observation_count: Decimal
    latest_observed_at: datetime
    probability_gap_ratio: Decimal
    cost_ratio: Decimal
    memory_decay_ratio: Decimal
    guard_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketMemoryProbabilityCostGuardRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketMemoryProbabilityCostGuardRow, "row")
        object.__setattr__(
            self,
            "record_digest",
            _require_sha256_digest("record_digest", self.record_digest),
        )
        object.__setattr__(
            self,
            "observation_count",
            _require_positive_count_decimal("observation_count", self.observation_count),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "probability_gap_ratio",
            "cost_ratio",
            "memory_decay_ratio",
            "guard_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_reason_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketMemoryProbabilityCostGuardReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketMemoryProbabilityCostGuardReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketMemoryProbabilityCostGuardReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _normalize_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketMemoryProbabilityCostGuardReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_probability_gap_ratio: Decimal
    max_cost_ratio: Decimal
    max_memory_decay_ratio: Decimal
    average_guard_pressure: Decimal
    max_guard_pressure: Decimal
    rows: tuple[ResearchMarketMemoryProbabilityCostGuardRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketMemoryProbabilityCostGuardReasonCodeCount,
        ...,
    ]
    public_payload: tuple[ResearchMarketMemoryProbabilityCostGuardPublicPayloadItem, ...] = ()
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketMemoryProbabilityCostGuardReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketMemoryProbabilityCostGuardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_id("config_version", self.config_version),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_probability_gap_ratio",
            "max_cost_ratio",
            "max_memory_decay_ratio",
            "average_guard_pressure",
            "max_guard_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload_items(self.public_payload),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _payload_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _reject_unsafe_public_payload("report", self.payload)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        return payload


def build_research_market_memory_probability_cost_guard_report(
    observations: Iterable[ResearchMarketMemoryProbabilityCostGuardObservation],
    *,
    config: ResearchMarketMemoryProbabilityCostGuardConfig,
    generated_at: datetime,
    public_payload: Sequence[
        ResearchMarketMemoryProbabilityCostGuardPublicPayloadItem
    ] = (),
) -> ResearchMarketMemoryProbabilityCostGuardReport:
    if type(config) is not ResearchMarketMemoryProbabilityCostGuardConfig:
        raise ValueError(
            "config must be a ResearchMarketMemoryProbabilityCostGuardConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = _build_rows(
        normalized_observations,
        config=config,
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketMemoryProbabilityCostGuardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_rollup_status(rows),
        input_count=_count_decimal(len(normalized_observations)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        max_probability_gap_ratio=_max_decimal(tuple(row.probability_gap_ratio for row in rows)),
        max_cost_ratio=_max_decimal(tuple(row.cost_ratio for row in rows)),
        max_memory_decay_ratio=_max_decimal(tuple(row.memory_decay_ratio for row in rows)),
        average_guard_pressure=_mean_decimal(tuple(row.guard_pressure for row in rows)),
        max_guard_pressure=_max_decimal(tuple(row.guard_pressure for row in rows)),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes),
        public_payload=tuple(public_payload),
    )


def research_market_memory_probability_cost_guard_payload(
    observations: Iterable[ResearchMarketMemoryProbabilityCostGuardObservation],
    *,
    config: ResearchMarketMemoryProbabilityCostGuardConfig,
    generated_at: datetime,
    public_payload: Sequence[
        ResearchMarketMemoryProbabilityCostGuardPublicPayloadItem
    ] = (),
) -> dict[str, object]:
    return build_research_market_memory_probability_cost_guard_report(
        observations,
        config=config,
        generated_at=generated_at,
        public_payload=public_payload,
    ).payload


def _build_rows(
    observations: tuple[ResearchMarketMemoryProbabilityCostGuardObservation, ...],
    *,
    config: ResearchMarketMemoryProbabilityCostGuardConfig,
) -> tuple[ResearchMarketMemoryProbabilityCostGuardRow, ...]:
    grouped: dict[str, list[ResearchMarketMemoryProbabilityCostGuardObservation]] = {}
    for item in observations:
        if item.record_ref not in grouped:
            grouped[item.record_ref] = []
        grouped[item.record_ref].append(item)
    rows = tuple(
        _row_for_record(record_ref, tuple(items), config=config)
        for record_ref, items in grouped.items()
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _row_for_record(
    record_ref: str,
    observations: tuple[ResearchMarketMemoryProbabilityCostGuardObservation, ...],
    *,
    config: ResearchMarketMemoryProbabilityCostGuardConfig,
) -> ResearchMarketMemoryProbabilityCostGuardRow:
    probability_gap_ratio = _max_decimal(
        tuple(
            _absolute(item.current_probability - item.memory_probability)
            for item in observations
        ),
    )
    cost_ratio = _max_decimal(tuple(item.cost_ratio for item in observations))
    memory_decay_ratio = _max_decimal(
        tuple(item.memory_decay_ratio for item in observations),
    )
    guard_pressure = _guard_pressure(
        probability_gap_ratio=probability_gap_ratio,
        cost_ratio=cost_ratio,
        memory_decay_ratio=memory_decay_ratio,
        config=config,
    )
    status = _row_status(
        probability_gap_ratio=probability_gap_ratio,
        cost_ratio=cost_ratio,
        memory_decay_ratio=memory_decay_ratio,
        guard_pressure=guard_pressure,
        config=config,
    )
    return ResearchMarketMemoryProbabilityCostGuardRow(
        record_digest=_sha256_text(record_ref),
        observation_count=_count_decimal(len(observations)),
        latest_observed_at=max(item.observed_at for item in observations),
        probability_gap_ratio=probability_gap_ratio,
        cost_ratio=cost_ratio,
        memory_decay_ratio=memory_decay_ratio,
        guard_pressure=guard_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            probability_gap_ratio=probability_gap_ratio,
            cost_ratio=cost_ratio,
            memory_decay_ratio=memory_decay_ratio,
            config=config,
        ),
    )


def _row_status(
    *,
    probability_gap_ratio: Decimal,
    cost_ratio: Decimal,
    memory_decay_ratio: Decimal,
    guard_pressure: Decimal,
    config: ResearchMarketMemoryProbabilityCostGuardConfig,
) -> str:
    if (
        probability_gap_ratio >= config.block_probability_gap_ratio
        or cost_ratio >= config.block_cost_ratio
        or memory_decay_ratio >= config.block_memory_decay_ratio
        or guard_pressure >= ONE
    ):
        return STATUS_BLOCK
    if (
        probability_gap_ratio >= config.watch_probability_gap_ratio
        or cost_ratio >= config.watch_cost_ratio
        or memory_decay_ratio >= config.watch_memory_decay_ratio
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    status: str,
    probability_gap_ratio: Decimal,
    cost_ratio: Decimal,
    memory_decay_ratio: Decimal,
    config: ResearchMarketMemoryProbabilityCostGuardConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if status == STATUS_BLOCK:
        codes.append(BLOCK_REASON)
    if cost_ratio >= config.block_cost_ratio:
        codes.append(COST_RATIO_BLOCK_REASON)
    elif cost_ratio >= config.watch_cost_ratio:
        codes.append(COST_RATIO_WATCH_REASON)
    if memory_decay_ratio >= config.block_memory_decay_ratio:
        codes.append(MEMORY_DECAY_BLOCK_REASON)
    elif memory_decay_ratio >= config.watch_memory_decay_ratio:
        codes.append(MEMORY_DECAY_WATCH_REASON)
    if probability_gap_ratio >= config.block_probability_gap_ratio:
        codes.append(PROBABILITY_GAP_BLOCK_REASON)
    elif probability_gap_ratio >= config.watch_probability_gap_ratio:
        codes.append(PROBABILITY_GAP_WATCH_REASON)
    if status == STATUS_WATCH:
        codes.append(WATCH_REASON)
    if status == STATUS_PASS:
        codes.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _guard_pressure(
    *,
    probability_gap_ratio: Decimal,
    cost_ratio: Decimal,
    memory_decay_ratio: Decimal,
    config: ResearchMarketMemoryProbabilityCostGuardConfig,
) -> Decimal:
    pressure = (
        _capped_ratio(probability_gap_ratio, config.block_probability_gap_ratio)
        * config.probability_gap_weight
        + _capped_ratio(cost_ratio, config.block_cost_ratio) * config.cost_weight
        + _capped_ratio(memory_decay_ratio, config.block_memory_decay_ratio)
        * config.memory_decay_weight
    )
    return _require_ratio_decimal("guard_pressure", pressure)


def _report_reason_codes(
    rows: tuple[ResearchMarketMemoryProbabilityCostGuardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(code for row in rows for code in row.reason_codes),
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketMemoryProbabilityCostGuardReasonCodeCount, ...]:
    counts = Counter(reason_codes)
    return tuple(
        ResearchMarketMemoryProbabilityCostGuardReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
        )
        for reason_code in _normalize_reason_codes("reason_codes", tuple(counts))
    )


def _rollup_status(
    rows: tuple[ResearchMarketMemoryProbabilityCostGuardRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchMarketMemoryProbabilityCostGuardRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _row_sort_key(row: ResearchMarketMemoryProbabilityCostGuardRow) -> tuple[int, str]:
    return (STATUS_RANK[row.status], row.record_digest)


def _normalize_observations(
    observations: Iterable[ResearchMarketMemoryProbabilityCostGuardObservation],
) -> tuple[ResearchMarketMemoryProbabilityCostGuardObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observations")
    normalized: list[ResearchMarketMemoryProbabilityCostGuardObservation] = []
    seen: set[tuple[str, str]] = set()
    for item in observations:
        if type(item) is not ResearchMarketMemoryProbabilityCostGuardObservation:
            raise ValueError(
                "observations must contain only "
                "ResearchMarketMemoryProbabilityCostGuardObservation values",
            )
        _require_hard_flags("observation", item)
        key = (item.record_ref, item.sample_ref)
        if key in seen:
            raise ValueError("duplicate observation record_ref and sample_ref")
        seen.add(key)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: Sequence[ResearchMarketMemoryProbabilityCostGuardRow],
) -> tuple[ResearchMarketMemoryProbabilityCostGuardRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a sequence of rows")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketMemoryProbabilityCostGuardRow:
            raise ValueError(
                "rows must contain only ResearchMarketMemoryProbabilityCostGuardRow values",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_public_payload_items(
    items: Sequence[ResearchMarketMemoryProbabilityCostGuardPublicPayloadItem],
) -> tuple[ResearchMarketMemoryProbabilityCostGuardPublicPayloadItem, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("public_payload must be a sequence of public payload items")
    normalized = tuple(items)
    for item in normalized:
        if type(item) is not ResearchMarketMemoryProbabilityCostGuardPublicPayloadItem:
            raise ValueError(
                "public_payload must contain only "
                "ResearchMarketMemoryProbabilityCostGuardPublicPayloadItem values",
            )
        _reject_unsafe_public_payload("public payload item", item)
    keys = tuple(item.key for item in normalized)
    if len(set(keys)) != len(keys):
        raise ValueError("public_payload keys must be unique")
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_reason_code_counts(
    values: Sequence[ResearchMarketMemoryProbabilityCostGuardReasonCodeCount],
) -> tuple[ResearchMarketMemoryProbabilityCostGuardReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be a sequence")
    normalized = tuple(values)
    for item in normalized:
        if type(item) is not ResearchMarketMemoryProbabilityCostGuardReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain only "
                "ResearchMarketMemoryProbabilityCostGuardReasonCodeCount values",
            )
    return tuple(sorted(normalized, key=lambda item: _reason_sort_key(item.reason_code)))


def _normalize_reason_codes(
    label: str,
    values: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{label} must be a sequence of reason codes")
    normalized = tuple(_normalize_reason_code(label, value) for value in values)
    return tuple(sorted(set(normalized), key=_reason_sort_key))


def _normalize_reason_code(label: str, value: str) -> str:
    value = _require_public_id(label, value)
    if value not in REASON_RANK:
        raise ValueError(f"{label} contains unsupported reason code")
    return value


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in REASON_RANK:
        return (REASON_RANK[reason_code], reason_code)
    return (len(REASON_RANK), reason_code)


def _validate_row_reason_consistency(
    row: ResearchMarketMemoryProbabilityCostGuardRow,
) -> None:
    if row.status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("status must match pass reason_codes")
    if row.status == STATUS_WATCH and WATCH_REASON not in row.reason_codes:
        raise ValueError("status must match watch reason_codes")
    if row.status == STATUS_BLOCK and BLOCK_REASON not in row.reason_codes:
        raise ValueError("status must match block reason_codes")


def _validate_report_consistency(
    report: ResearchMarketMemoryProbabilityCostGuardReport,
) -> None:
    if report.config_version != DEFAULT_RESEARCH_MARKET_MEMORY_PROBABILITY_COST_GUARD_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    if report.status != _rollup_status(report.rows):
        raise ValueError("status must match row statuses")
    if report.input_count < report.row_count:
        raise ValueError("input_count must be at least row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.max_probability_gap_ratio != _max_decimal(
        tuple(row.probability_gap_ratio for row in report.rows),
    ):
        raise ValueError("max_probability_gap_ratio must match rows")
    if report.max_cost_ratio != _max_decimal(tuple(row.cost_ratio for row in report.rows)):
        raise ValueError("max_cost_ratio must match rows")
    if report.max_memory_decay_ratio != _max_decimal(
        tuple(row.memory_decay_ratio for row in report.rows),
    ):
        raise ValueError("max_memory_decay_ratio must match rows")
    if report.average_guard_pressure != _mean_decimal(
        tuple(row.guard_pressure for row in report.rows),
    ):
        raise ValueError("average_guard_pressure must match rows")
    if report.max_guard_pressure != _max_decimal(tuple(row.guard_pressure for row in report.rows)):
        raise ValueError("max_guard_pressure must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_counts = _reason_code_counts(report.reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match reason_codes")


def _payload_digest(report: ResearchMarketMemoryProbabilityCostGuardReport) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    del payload["derived_validation_digest"]
    return _stable_sha256(payload)


def _stable_sha256(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        return _decimal_to_string(value)
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_ready(nested) for key, nested in value.items()}
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, str):
        if SHA256_RE.fullmatch(value):
            return
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public payload content")
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _reject_unsafe_public_payload(label, str(key))
            _reject_unsafe_public_payload(label, nested)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(label, field.name)
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            _reject_unsafe_public_payload(label, nested)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_public_id(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not PUBLIC_ID_RE.fullmatch(value):
        raise ValueError(f"{label} must be a canonical public identifier")
    return value


def _require_public_value(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not value or len(value) > 128:
        raise ValueError(f"{label} must be a non-empty public value")
    if any(ord(character) < 32 or ord(character) > 126 for character in value):
        raise ValueError(f"{label} must be printable ASCII")
    return value


def _require_raw_ref(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not value:
        raise ValueError(f"{label} must be non-empty")
    if "\x00" in value:
        raise ValueError(f"{label} must not contain null bytes")
    return value


def _require_status(label: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{label} must be one of pass, watch, block")
    return value


def _require_sha256_digest(label: str, value: object) -> str:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{label} must be a sha256 digest")
    return value


def _require_decimal(label: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be a Decimal")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a finite Decimal") from exc


def _require_ratio_decimal(label: str, value: object) -> Decimal:
    decimal = _require_decimal(label, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{label} must be between zero and one")
    return decimal


def _require_nonnegative_count_decimal(label: str, value: object) -> Decimal:
    decimal = _require_decimal(label, value)
    if decimal < ZERO:
        raise ValueError(f"{label} must be non-negative")
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{label} must be a whole Decimal count")
    return decimal


def _require_positive_count_decimal(label: str, value: object) -> Decimal:
    decimal = _require_nonnegative_count_decimal(label, value)
    if decimal <= ZERO:
        raise ValueError(f"{label} must be positive")
    return decimal


def _require_less_than(
    left_label: str,
    left: Decimal,
    right_label: str,
    right: Decimal,
) -> None:
    if left >= right:
        raise ValueError(f"{left_label} must be below {right_label}")


def _quantize(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise InvalidOperation
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_to_string(value: Decimal) -> str:
    return format(_quantize(value), ".6f")


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _absolute(value: Decimal) -> Decimal:
    if value < ZERO:
        return _quantize(-value)
    return _quantize(value)


def _capped_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    ratio = _quantize(value / denominator)
    if ratio > ONE:
        return ONE
    if ratio < ZERO:
        return ZERO
    return ratio


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _require_ratio_decimal("max_decimal", max(values))


def _mean_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _require_ratio_decimal(
        "mean_decimal",
        sum(values, ZERO) / _count_decimal(len(values)),
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _as_utc(label: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)
