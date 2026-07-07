"""Read-only Phase 1 category research capacity heatmap."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json


def _join_parts(*parts: str) -> str:
    return "".join(parts)


DEFAULT_CATEGORY_RESEARCH_CAPACITY_HEATMAP_CONFIG_VERSION = (
    "category-research-capacity-heatmap-v0"
)
CATEGORY_RESEARCH_CAPACITY_HEATMAP_CATEGORIES = (
    "politics",
    "crypto",
    "macro",
    "commodities",
    "sports",
)

_CATEGORY_TO_TEAMS = {
    "politics": ("politics",),
    "crypto": ("crypto_btc", "crypto_eth"),
    "macro": ("macro_rates",),
    "commodities": ("commodities_gold", "commodities_oil"),
    "sports": ("sports_soccer", "sports_basketball", "sports_other"),
}
_TEAM_TO_CATEGORY = {
    team_id: category_id
    for category_id, team_ids in _CATEGORY_TO_TEAMS.items()
    for team_id in team_ids
}
_COUNT_QUANTUM = Decimal("1")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_CAPACITY_STATUSES = ("ready", "overloaded", "blocked")
_BACKLOG_STATUSES = ("pass", "watch", "blocked")
_MEMORY_STATUSES = ("pass", "watch", "blocked")
_HEATMAP_STATUSES = ("ready", "watch", "blocked")
_REASON_CODES = (
    "category_source_missing",
    "category_capacity_ready",
    "category_capacity_watch",
    "category_capacity_blocked",
    "category_backlog_ready",
    "category_backlog_watch",
    "category_backlog_blocked",
    "category_memory_ready",
    "category_memory_watch",
    "category_memory_blocked",
)
_UNSAFE_PUBLIC_TERMS = (
    _join_parts("fa", "st"),
    _join_parts("li", "ve"),
    _join_parts("au", "th"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("acc", "ount"),
    _join_parts("sl", "ug"),
    _join_parts("que", "stion"),
    _join_parts("mar", "ket"),
    _join_parts("st", "ore"),
    _join_parts("net", "work"),
    _join_parts("data", "base"),
    _join_parts("tra", "de"),
    _join_parts("buy"),
    _join_parts("sell"),
    _join_parts("mut", "ation"),
    _join_parts("pers", "ist"),
    _join_parts("sec", "ret"),
    _join_parts("tok", "en"),
)


@dataclass(frozen=True)
class CategoryResearchCapacityHeatmapConfig:
    config_version: str = DEFAULT_CATEGORY_RESEARCH_CAPACITY_HEATMAP_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class CategoryResearchCapacityHeatmapInput:
    team_id: str
    queue_count: Decimal
    available_analyst_agent_slots: Decimal
    capacity_gap_count: Decimal
    capacity_status: str
    backlog_assignment_count: Decimal
    backlog_count: Decimal
    backlog_pressure_status: str
    memory_source_count: Decimal
    memory_pass_count: Decimal
    memory_watch_count: Decimal
    memory_blocked_count: Decimal
    memory_readiness_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_known_team_id("team_id", self.team_id)
        for field_name in (
            "queue_count",
            "available_analyst_agent_slots",
            "capacity_gap_count",
            "backlog_assignment_count",
            "backlog_count",
            "memory_source_count",
            "memory_pass_count",
            "memory_watch_count",
            "memory_blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("capacity_status", self.capacity_status, _CAPACITY_STATUSES)
        _require_member(
            "backlog_pressure_status",
            self.backlog_pressure_status,
            _BACKLOG_STATUSES,
        )
        _require_member(
            "memory_readiness_status",
            self.memory_readiness_status,
            _MEMORY_STATUSES,
        )
        if self.capacity_gap_count > self.queue_count:
            raise ValueError("capacity_gap_count must not exceed queue_count")
        if self.backlog_count > self.backlog_assignment_count:
            raise ValueError("backlog_count must not exceed backlog_assignment_count")
        if (
            self.memory_pass_count + self.memory_watch_count + self.memory_blocked_count
            != self.memory_source_count
        ):
            raise ValueError("memory counts must sum to memory_source_count")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class CategoryResearchCapacityHeatmapPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", _require_public_payload_key("key", self.key))
        object.__setattr__(
            self,
            "value",
            _require_public_payload_text("value", self.value),
        )
        _require_hard_flags("public payload item", self)


@dataclass(frozen=True)
class CategoryResearchCapacityHeatmapRow:
    category_id: str
    configured_team_count: Decimal
    observed_team_count: Decimal
    queue_count: Decimal
    available_analyst_agent_slots: Decimal
    capacity_gap_count: Decimal
    capacity_pressure_ratio: Decimal
    backlog_assignment_count: Decimal
    backlog_count: Decimal
    backlog_pressure_ratio: Decimal
    memory_source_count: Decimal
    memory_pass_count: Decimal
    memory_watch_count: Decimal
    memory_blocked_count: Decimal
    memory_readiness_ratio: Decimal
    capacity_status: str
    backlog_pressure_status: str
    memory_readiness_status: str
    heatmap_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_category_id("category_id", self.category_id)
        for field_name in (
            "configured_team_count",
            "observed_team_count",
            "queue_count",
            "available_analyst_agent_slots",
            "capacity_gap_count",
            "backlog_assignment_count",
            "backlog_count",
            "memory_source_count",
            "memory_pass_count",
            "memory_watch_count",
            "memory_blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "capacity_pressure_ratio",
            "backlog_pressure_ratio",
            "memory_readiness_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("capacity_status", self.capacity_status, _HEATMAP_STATUSES)
        _require_member(
            "backlog_pressure_status",
            self.backlog_pressure_status,
            _HEATMAP_STATUSES,
        )
        _require_member(
            "memory_readiness_status",
            self.memory_readiness_status,
            _HEATMAP_STATUSES,
        )
        _require_member("heatmap_status", self.heatmap_status, _HEATMAP_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class CategoryResearchCapacityHeatmapReport:
    generated_at: datetime
    config_version: str
    heatmap_status: str
    category_count: Decimal
    configured_team_count: Decimal
    observed_team_count: Decimal
    ready_category_count: Decimal
    watch_category_count: Decimal
    blocked_category_count: Decimal
    category_rows: tuple[CategoryResearchCapacityHeatmapRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[CategoryResearchCapacityHeatmapPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("heatmap_status", self.heatmap_status, _HEATMAP_STATUSES)
        for field_name in (
            "category_count",
            "configured_team_count",
            "observed_team_count",
            "ready_category_count",
            "watch_category_count",
            "blocked_category_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "category_rows", _normalize_category_rows(self.category_rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload("report payload", payload)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_category_research_capacity_heatmap_rows(
    inputs: list[CategoryResearchCapacityHeatmapInput]
    | tuple[CategoryResearchCapacityHeatmapInput, ...],
    *,
    config: CategoryResearchCapacityHeatmapConfig,
) -> tuple[CategoryResearchCapacityHeatmapRow, ...]:
    if type(config) is not CategoryResearchCapacityHeatmapConfig:
        raise ValueError("config must be a CategoryResearchCapacityHeatmapConfig")
    _require_hard_flags("config", config)
    signals = _normalize_inputs(inputs)
    by_category = {
        category_id: tuple(
            signal
            for signal in signals
            if _TEAM_TO_CATEGORY[signal.team_id] == category_id
        )
        for category_id in CATEGORY_RESEARCH_CAPACITY_HEATMAP_CATEGORIES
    }
    return tuple(
        _heatmap_row(category_id, by_category[category_id])
        for category_id in CATEGORY_RESEARCH_CAPACITY_HEATMAP_CATEGORIES
    )


def build_category_research_capacity_heatmap_report(
    inputs: list[CategoryResearchCapacityHeatmapInput]
    | tuple[CategoryResearchCapacityHeatmapInput, ...],
    *,
    generated_at: datetime,
    config: CategoryResearchCapacityHeatmapConfig,
    public_payload: list[CategoryResearchCapacityHeatmapPublicPayloadItem]
    | tuple[CategoryResearchCapacityHeatmapPublicPayloadItem, ...] = (),
) -> CategoryResearchCapacityHeatmapReport:
    if type(config) is not CategoryResearchCapacityHeatmapConfig:
        raise ValueError("config must be a CategoryResearchCapacityHeatmapConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    category_rows = build_category_research_capacity_heatmap_rows(inputs, config=config)
    payload_items = _normalize_public_payload(public_payload)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "heatmap_status": _status_rollup(
            tuple(row.heatmap_status for row in category_rows),
        ),
        "category_count": _count(len(category_rows)),
        "configured_team_count": _sum_category_rows(category_rows, "configured_team_count"),
        "observed_team_count": _sum_category_rows(category_rows, "observed_team_count"),
        "ready_category_count": _category_status_count(category_rows, "ready"),
        "watch_category_count": _category_status_count(category_rows, "watch"),
        "blocked_category_count": _category_status_count(category_rows, "blocked"),
        "category_rows": category_rows,
        "reason_codes": _report_reason_codes(category_rows),
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CategoryResearchCapacityHeatmapReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _normalize_inputs(
    inputs: list[CategoryResearchCapacityHeatmapInput]
    | tuple[CategoryResearchCapacityHeatmapInput, ...],
) -> tuple[CategoryResearchCapacityHeatmapInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    signals = tuple(inputs)
    seen_team_ids: set[str] = set()
    for signal in signals:
        if type(signal) is not CategoryResearchCapacityHeatmapInput:
            raise ValueError("inputs must contain CategoryResearchCapacityHeatmapInput values")
        _require_hard_flags("input", signal)
        if signal.team_id in seen_team_ids:
            raise ValueError("inputs must not contain duplicate team_id values")
        seen_team_ids.add(signal.team_id)
    return signals


def _heatmap_row(
    category_id: str,
    signals: tuple[CategoryResearchCapacityHeatmapInput, ...],
) -> CategoryResearchCapacityHeatmapRow:
    configured_team_count = _count(len(_CATEGORY_TO_TEAMS[category_id]))
    observed_team_count = _count(len(signals))
    queue_count = _sum(signals, "queue_count")
    available_slots = _sum(signals, "available_analyst_agent_slots")
    capacity_gap_count = _sum(signals, "capacity_gap_count")
    backlog_assignment_count = _sum(signals, "backlog_assignment_count")
    backlog_count = _sum(signals, "backlog_count")
    memory_source_count = _sum(signals, "memory_source_count")
    memory_pass_count = _sum(signals, "memory_pass_count")
    memory_watch_count = _sum(signals, "memory_watch_count")
    memory_blocked_count = _sum(signals, "memory_blocked_count")
    source_missing = observed_team_count < configured_team_count
    capacity_status = _category_status(
        tuple(_capacity_signal_status(signal) for signal in signals),
        source_missing=source_missing,
    )
    backlog_status = _category_status(
        tuple(_source_status(signal.backlog_pressure_status) for signal in signals),
        source_missing=source_missing,
    )
    memory_status = _category_status(
        tuple(_source_status(signal.memory_readiness_status) for signal in signals),
        source_missing=source_missing,
    )
    heatmap_status = _status_rollup((capacity_status, backlog_status, memory_status))
    reason_codes = _row_reason_codes(
        source_missing=source_missing,
        capacity_status=capacity_status,
        backlog_status=backlog_status,
        memory_status=memory_status,
    )

    return CategoryResearchCapacityHeatmapRow(
        category_id=category_id,
        configured_team_count=configured_team_count,
        observed_team_count=observed_team_count,
        queue_count=queue_count,
        available_analyst_agent_slots=available_slots,
        capacity_gap_count=capacity_gap_count,
        capacity_pressure_ratio=_ratio(queue_count, available_slots),
        backlog_assignment_count=backlog_assignment_count,
        backlog_count=backlog_count,
        backlog_pressure_ratio=_ratio(backlog_count, backlog_assignment_count),
        memory_source_count=memory_source_count,
        memory_pass_count=memory_pass_count,
        memory_watch_count=memory_watch_count,
        memory_blocked_count=memory_blocked_count,
        memory_readiness_ratio=_ratio(memory_pass_count, memory_source_count),
        capacity_status=capacity_status,
        backlog_pressure_status=backlog_status,
        memory_readiness_status=memory_status,
        heatmap_status=heatmap_status,
        reason_codes=reason_codes,
    )


def _capacity_signal_status(signal: CategoryResearchCapacityHeatmapInput) -> str:
    if signal.capacity_status == "blocked":
        return "blocked"
    if signal.capacity_status == "overloaded":
        return "watch"
    return "ready"


def _source_status(value: str) -> str:
    if value == "pass":
        return "ready"
    return value


def _category_status(
    statuses: tuple[str, ...],
    *,
    source_missing: bool,
) -> str:
    if source_missing or not statuses:
        return "blocked"
    return _status_rollup(statuses)


def _status_rollup(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "ready"


def _row_reason_codes(
    *,
    source_missing: bool,
    capacity_status: str,
    backlog_status: str,
    memory_status: str,
) -> tuple[str, ...]:
    if source_missing:
        return ("category_source_missing",)
    return (
        f"category_capacity_{capacity_status}",
        f"category_backlog_{backlog_status}",
        f"category_memory_{memory_status}",
    )


def _sum(
    signals: tuple[CategoryResearchCapacityHeatmapInput, ...],
    field_name: str,
) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        sum((getattr(signal, field_name) for signal in signals), _ZERO_COUNT),
    )


def _sum_category_rows(
    category_rows: tuple[CategoryResearchCapacityHeatmapRow, ...],
    field_name: str,
) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        sum((getattr(row, field_name) for row in category_rows), _ZERO_COUNT),
    )


def _category_status_count(
    category_rows: tuple[CategoryResearchCapacityHeatmapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in category_rows if row.heatmap_status == status))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO_COUNT:
        return _ZERO_RATIO
    with localcontext(_DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(_RATIO_QUANTUM)


def _validate_row(row: CategoryResearchCapacityHeatmapRow) -> None:
    if row.observed_team_count > row.configured_team_count:
        raise ValueError("observed_team_count must not exceed configured_team_count")
    if row.capacity_gap_count > row.queue_count:
        raise ValueError("capacity_gap_count must not exceed queue_count")
    if row.backlog_count > row.backlog_assignment_count:
        raise ValueError("backlog_count must not exceed backlog_assignment_count")
    if (
        row.memory_pass_count + row.memory_watch_count + row.memory_blocked_count
        != row.memory_source_count
    ):
        raise ValueError("memory counts must sum to memory_source_count")
    expected_status = _status_rollup(
        (row.capacity_status, row.backlog_pressure_status, row.memory_readiness_status)
    )
    if row.heatmap_status != expected_status:
        raise ValueError("heatmap_status must summarize component statuses")


def _validate_report(report: CategoryResearchCapacityHeatmapReport) -> None:
    if report.category_count != _count(len(report.category_rows)):
        raise ValueError("category_count must match category_rows")
    if report.configured_team_count != _sum_category_rows(
        report.category_rows,
        "configured_team_count",
    ):
        raise ValueError("configured_team_count must match category_rows")
    if report.observed_team_count != _sum_category_rows(
        report.category_rows,
        "observed_team_count",
    ):
        raise ValueError("observed_team_count must match category_rows")
    if report.ready_category_count != _category_status_count(report.category_rows, "ready"):
        raise ValueError("ready_category_count must match category_rows")
    if report.watch_category_count != _category_status_count(report.category_rows, "watch"):
        raise ValueError("watch_category_count must match category_rows")
    if report.blocked_category_count != _category_status_count(
        report.category_rows,
        "blocked",
    ):
        raise ValueError("blocked_category_count must match category_rows")
    expected_status = _status_rollup(tuple(row.heatmap_status for row in report.category_rows))
    if report.heatmap_status != expected_status:
        raise ValueError("heatmap_status must summarize category_rows")
    if report.reason_codes != _report_reason_codes(report.category_rows):
        raise ValueError("reason_codes must summarize category_rows")


def _normalize_category_rows(value: object) -> tuple[CategoryResearchCapacityHeatmapRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("category_rows must be a list or tuple")
    category_rows = tuple(value)
    if len(category_rows) != len(CATEGORY_RESEARCH_CAPACITY_HEATMAP_CATEGORIES):
        raise ValueError("category_rows must cover Phase 1 categories")
    for category_id, row in zip(
        CATEGORY_RESEARCH_CAPACITY_HEATMAP_CATEGORIES,
        category_rows,
        strict=True,
    ):
        if type(row) is not CategoryResearchCapacityHeatmapRow:
            raise ValueError("category_rows must contain heatmap row values")
        _require_hard_flags("category row", row)
        if row.category_id != category_id:
            raise ValueError("category_rows must follow Phase 1 category sequence")
    return category_rows


def _normalize_public_payload(
    value: object,
) -> tuple[CategoryResearchCapacityHeatmapPublicPayloadItem, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("public_payload must be a list or tuple")
    payload_items = tuple(value)
    seen_keys: set[str] = set()
    for item in payload_items:
        if type(item) is not CategoryResearchCapacityHeatmapPublicPayloadItem:
            raise ValueError("public_payload must contain public payload items")
        _require_hard_flags("public payload item", item)
        if item.key in seen_keys:
            raise ValueError("public_payload keys must be unique")
        seen_keys.add(item.key)
    return tuple(sorted(payload_items, key=lambda item: item.key))


def _report_reason_codes(
    category_rows: tuple[CategoryResearchCapacityHeatmapRow, ...],
) -> tuple[str, ...]:
    row_codes = {
        reason_code
        for row in category_rows
        for reason_code in row.reason_codes
    }
    return tuple(reason_code for reason_code in _REASON_CODES if reason_code in row_codes)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_member("reason_codes", reason_code, _REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _report_values_without_digest(
    report: CategoryResearchCapacityHeatmapReport,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "heatmap_status": report.heatmap_status,
        "category_count": report.category_count,
        "configured_team_count": report.configured_team_count,
        "observed_team_count": report.observed_team_count,
        "ready_category_count": report.ready_category_count,
        "watch_category_count": report.watch_category_count,
        "blocked_category_count": report.blocked_category_count,
        "category_rows": report.category_rows,
        "reason_codes": report.reason_codes,
        "public_payload": report.public_payload,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _report_digest_from_values(values: dict[str, object]) -> str:
    encoded = json.dumps(
        _json_ready(values),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if type(value) is bool or value is None or isinstance(value, str):
        return value
    if isinstance(value, tuple) or isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _json_ready(item)
            for key, item in value.items()
        }
    if hasattr(value, "__dataclass_fields__"):
        return _json_ready(asdict(value))
    raise ValueError("value is not JSON serializable")


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_RATIO_QUANTUM)
    if quantized < _ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_category_id(field_name: str, value: object) -> None:
    _require_member(field_name, value, CATEGORY_RESEARCH_CAPACITY_HEATMAP_CATEGORIES)


def _require_known_team_id(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in _TEAM_TO_CATEGORY:
        raise ValueError(f"{field_name} must be a known Phase 1 category team")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_payload_key(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if len(value) > 128:
        raise ValueError(f"{field_name} must be at most 128 characters")
    if not all(
        character.isalnum() or character in ("_", ".", "-")
        for character in value
    ):
        raise ValueError(f"{field_name} must be a public payload key")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_public_payload_text(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if len(value) > 512:
        raise ValueError(f"{field_name} must be at most 512 characters")
    if any(character < " " for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_unsafe_public_payload(field_name: str, value: object) -> None:
    if isinstance(value, str):
        _reject_unsafe_public_text(field_name, value)
        return
    if type(value) is bool or value is None or isinstance(value, (Decimal, datetime)):
        return
    if isinstance(value, tuple) or isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(field_name, item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(field_name, str(key))
            _reject_unsafe_public_payload(field_name, item)
        return
    if hasattr(value, "__dataclass_fields__"):
        _reject_unsafe_public_payload(field_name, asdict(value))
        return
    raise ValueError(f"{field_name} contains unsupported public payload value")


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} contains unsafe public value")


__all__ = (
    "DEFAULT_CATEGORY_RESEARCH_CAPACITY_HEATMAP_CONFIG_VERSION",
    "CATEGORY_RESEARCH_CAPACITY_HEATMAP_CATEGORIES",
    "CategoryResearchCapacityHeatmapConfig",
    "CategoryResearchCapacityHeatmapInput",
    "CategoryResearchCapacityHeatmapPublicPayloadItem",
    "CategoryResearchCapacityHeatmapRow",
    "CategoryResearchCapacityHeatmapReport",
    "build_category_research_capacity_heatmap_rows",
    "build_category_research_capacity_heatmap_report",
)
