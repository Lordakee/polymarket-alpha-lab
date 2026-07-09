from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from typing import Any


__all__ = (
    "ResearchMarketSourceMemoryCostGuardConfig",
    "ResearchMarketSourceMemoryCostGuardInputRow",
    "ResearchMarketSourceMemoryCostGuardReasonCodeCount",
    "ResearchMarketSourceMemoryCostGuardReport",
    "ResearchMarketSourceMemoryCostGuardReportRow",
    "build_research_market_source_memory_cost_guard_report",
    "research_market_source_memory_cost_guard_public_payload",
    "validate_research_market_source_memory_cost_guard_payload_digest",
)


DEFAULT_CONFIG_VERSION = "memory-cost-guard-v0"
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
NO_ITEMS_REASON = "no_items"
ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
_HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_REASON_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_PUBLIC_STRING_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")
_PRIVATE_TERMS = (
    "candidate",
    "market",
    "ques" + "tion",
    "sl" + "ug",
    "source_" + "ur" + "l",
    "ur" + "l",
    "te" + "xt",
    "ds" + "n",
    "ta" + "ble",
    "to" + "ken",
    "wal" + "let",
    "ord" + "er",
    "tra" + "de",
    "exec" + "ution",
    "siz" + "ing",
    "recom" + "mendation",
    "au" + "th",
)


@dataclass(frozen=True)
class ResearchMarketSourceMemoryCostGuardConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    item_pass_memory_mb: Decimal = Decimal("64.000000")
    item_block_memory_mb: Decimal = Decimal("128.000000")
    item_pass_cost_usd: Decimal = Decimal("0.050000")
    item_block_cost_usd: Decimal = Decimal("0.100000")
    total_pass_memory_mb: Decimal = Decimal("160.000000")
    total_block_memory_mb: Decimal = Decimal("240.000000")
    total_pass_cost_usd: Decimal = Decimal("0.120000")
    total_block_cost_usd: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSourceMemoryCostGuardConfig:
            raise TypeError(
                "ResearchMarketSourceMemoryCostGuardConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketSourceMemoryCostGuardConfig:
            raise ValueError(
                "config must be exactly ResearchMarketSourceMemoryCostGuardConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "item_pass_memory_mb",
            "item_block_memory_mb",
            "item_pass_cost_usd",
            "item_block_cost_usd",
            "total_pass_memory_mb",
            "total_block_memory_mb",
            "total_pass_cost_usd",
            "total_block_cost_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_increasing_thresholds(
            "item_memory_mb",
            self.item_pass_memory_mb,
            self.item_block_memory_mb,
        )
        _require_increasing_thresholds(
            "item_cost_usd",
            self.item_pass_cost_usd,
            self.item_block_cost_usd,
        )
        _require_increasing_thresholds(
            "total_memory_mb",
            self.total_pass_memory_mb,
            self.total_block_memory_mb,
        )
        _require_increasing_thresholds(
            "total_cost_usd",
            self.total_pass_cost_usd,
            self.total_block_cost_usd,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketSourceMemoryCostGuardInputRow:
    item_digest: str
    observed_at: datetime
    memory_mb: Decimal
    cost_usd: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSourceMemoryCostGuardInputRow:
            raise TypeError(
                "ResearchMarketSourceMemoryCostGuardInputRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketSourceMemoryCostGuardInputRow:
            raise ValueError(
                "input row must be exactly ResearchMarketSourceMemoryCostGuardInputRow",
            )
        _require_digest("item_digest", self.item_digest)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "memory_mb",
            _require_nonnegative_decimal("memory_mb", self.memory_mb),
        )
        object.__setattr__(
            self,
            "cost_usd",
            _require_nonnegative_decimal("cost_usd", self.cost_usd),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchMarketSourceMemoryCostGuardReportRow:
    item_digest: str
    observed_at: datetime
    memory_mb: Decimal
    cost_usd: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSourceMemoryCostGuardReportRow:
            raise TypeError(
                "ResearchMarketSourceMemoryCostGuardReportRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketSourceMemoryCostGuardReportRow:
            raise ValueError(
                "row must be exactly ResearchMarketSourceMemoryCostGuardReportRow",
            )
        _require_digest("item_digest", self.item_digest)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "memory_mb",
            _require_nonnegative_decimal("memory_mb", self.memory_mb),
        )
        object.__setattr__(
            self,
            "cost_usd",
            _require_nonnegative_decimal("cost_usd", self.cost_usd),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketSourceMemoryCostGuardReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSourceMemoryCostGuardReasonCodeCount:
            raise TypeError(
                "ResearchMarketSourceMemoryCostGuardReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketSourceMemoryCostGuardReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchMarketSourceMemoryCostGuardReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketSourceMemoryCostGuardReport:
    generated_at: datetime
    config_version: str
    status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_memory_mb: Decimal
    total_cost_usd: Decimal
    peak_memory_mb: Decimal
    peak_cost_usd: Decimal
    average_memory_mb: Decimal
    average_cost_usd: Decimal
    rows: tuple[ResearchMarketSourceMemoryCostGuardReportRow, ...]
    reason_code_counts: tuple[ResearchMarketSourceMemoryCostGuardReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketSourceMemoryCostGuardReport:
            raise TypeError(
                "ResearchMarketSourceMemoryCostGuardReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketSourceMemoryCostGuardReport:
            raise ValueError(
                "report must be exactly ResearchMarketSourceMemoryCostGuardReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_memory_mb",
            "total_cost_usd",
            "peak_memory_mb",
            "peak_cost_usd",
            "average_memory_mb",
            "average_cost_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_report_rows("rows", self.rows)
        _require_reason_count_rows("reason_code_counts", self.reason_code_counts)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.reason_codes != tuple(
            item.reason_code for item in self.reason_code_counts
        ):
            raise ValueError("reason_codes must match reason_code_counts")
        if self.item_count != _count_decimal(self.rows):
            raise ValueError("item_count must match rows")
        if self.pass_count != _sum_if(self.rows, lambda row: row.status == STATUS_PASS):
            raise ValueError("pass_count must match rows")
        if self.watch_count != _sum_if(self.rows, lambda row: row.status == STATUS_WATCH):
            raise ValueError("watch_count must match rows")
        if self.block_count != _sum_if(self.rows, lambda row: row.status == STATUS_BLOCK):
            raise ValueError("block_count must match rows")
        if self.status != _report_status(self.rows, self.reason_codes):
            raise ValueError("status must match rows and reason_codes")
        if self.validation_digest != _payload_digest(
            _report_public_values(self, include_digest=False),
        ):
            raise ValueError("validation_digest does not match public payload")
        _require_hard_flags("report", self)


def build_research_market_source_memory_cost_guard_report(
    rows: tuple[ResearchMarketSourceMemoryCostGuardInputRow, ...],
    *,
    config: ResearchMarketSourceMemoryCostGuardConfig | None = None,
    generated_at: datetime,
) -> ResearchMarketSourceMemoryCostGuardReport:
    cfg = config or ResearchMarketSourceMemoryCostGuardConfig()
    if type(cfg) is not ResearchMarketSourceMemoryCostGuardConfig:
        raise TypeError(
            "config must be exactly ResearchMarketSourceMemoryCostGuardConfig",
        )
    observed_at = _as_utc("generated_at", generated_at)
    input_rows = _require_input_rows("rows", rows)
    for row in input_rows:
        if row.observed_at > observed_at:
            raise ValueError("observed_at must not be after generated_at")

    total_memory_mb = _sum_decimal(row.memory_mb for row in input_rows)
    total_cost_usd = _sum_decimal(row.cost_usd for row in input_rows)
    report_rows = tuple(
        _build_report_row(
            row,
            config=cfg,
            total_memory_mb=total_memory_mb,
            total_cost_usd=total_cost_usd,
        )
        for row in input_rows
    )
    sorted_rows = tuple(
        sorted(
            report_rows,
            key=lambda row: (_status_rank(row.status), row.item_digest),
        ),
    )

    if not sorted_rows:
        reason_counts = (
            ResearchMarketSourceMemoryCostGuardReasonCodeCount(
                reason_code=NO_ITEMS_REASON,
                count=ONE,
            ),
        )
        reason_codes = (NO_ITEMS_REASON,)
        public_values = {
            "generated_at": observed_at,
            "config_version": cfg.config_version,
            "status": STATUS_BLOCK,
            "item_count": ZERO,
            "pass_count": ZERO,
            "watch_count": ZERO,
            "block_count": ZERO,
            "total_memory_mb": ZERO,
            "total_cost_usd": ZERO,
            "peak_memory_mb": ZERO,
            "peak_cost_usd": ZERO,
            "average_memory_mb": ZERO,
            "average_cost_usd": ZERO,
            "rows": (),
            "reason_code_counts": reason_counts,
            "reason_codes": reason_codes,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
        return ResearchMarketSourceMemoryCostGuardReport(
            **public_values,
            validation_digest=_payload_digest(public_values),
        )

    reason_counts = _reason_code_counts(sorted_rows)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    item_count = _count_decimal(sorted_rows)
    pass_count = _sum_if(sorted_rows, lambda row: row.status == STATUS_PASS)
    watch_count = _sum_if(sorted_rows, lambda row: row.status == STATUS_WATCH)
    block_count = _sum_if(sorted_rows, lambda row: row.status == STATUS_BLOCK)
    peak_memory_mb = max(row.memory_mb for row in sorted_rows)
    peak_cost_usd = max(row.cost_usd for row in sorted_rows)
    public_values = {
        "generated_at": observed_at,
        "config_version": cfg.config_version,
        "status": _report_status(sorted_rows, reason_codes),
        "item_count": item_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "total_memory_mb": _quantize(total_memory_mb),
        "total_cost_usd": _quantize(total_cost_usd),
        "peak_memory_mb": _quantize(peak_memory_mb),
        "peak_cost_usd": _quantize(peak_cost_usd),
        "average_memory_mb": _quantize(total_memory_mb / item_count),
        "average_cost_usd": _quantize(total_cost_usd / item_count),
        "rows": sorted_rows,
        "reason_code_counts": reason_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketSourceMemoryCostGuardReport(
        **public_values,
        validation_digest=_payload_digest(public_values),
    )


def research_market_source_memory_cost_guard_public_payload(
    report: ResearchMarketSourceMemoryCostGuardReport,
) -> dict[str, object]:
    if type(report) is not ResearchMarketSourceMemoryCostGuardReport:
        raise TypeError(
            "report must be exactly ResearchMarketSourceMemoryCostGuardReport",
        )
    payload = _json_ready(_report_public_values(report, include_digest=True))
    _reject_unsafe_public_payload(
        "public payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    if not validate_research_market_source_memory_cost_guard_payload_digest(payload):
        raise ValueError("public payload validation_digest is invalid")
    return payload


def validate_research_market_source_memory_cost_guard_payload_digest(
    payload: Mapping[str, object],
) -> bool:
    if not isinstance(payload, Mapping):
        return False
    validation_digest = payload.get("validation_digest")
    if type(validation_digest) is not str or not _HEX_SHA256_RE.fullmatch(
        validation_digest,
    ):
        return False
    payload_without_digest = dict(payload)
    payload_without_digest.pop("validation_digest", None)
    try:
        _reject_unsafe_public_payload(
            "public payload",
            payload_without_digest,
            allow_json_containers=True,
        )
        expected_digest = _payload_digest(payload_without_digest)
    except (TypeError, ValueError):
        return False
    return validation_digest == expected_digest


def _build_report_row(
    row: ResearchMarketSourceMemoryCostGuardInputRow,
    *,
    config: ResearchMarketSourceMemoryCostGuardConfig,
    total_memory_mb: Decimal,
    total_cost_usd: Decimal,
) -> ResearchMarketSourceMemoryCostGuardReportRow:
    reason_codes = list(_input_reason_codes(row.reason_codes))
    if row.memory_mb >= config.item_block_memory_mb:
        reason_codes.append("item_memory_block")
    elif row.memory_mb >= config.item_pass_memory_mb:
        reason_codes.append("item_memory_watch")
    if row.cost_usd >= config.item_block_cost_usd:
        reason_codes.append("item_cost_block")
    elif row.cost_usd >= config.item_pass_cost_usd:
        reason_codes.append("item_cost_watch")
    if total_memory_mb >= config.total_block_memory_mb:
        reason_codes.append("total_memory_block")
    elif total_memory_mb >= config.total_pass_memory_mb:
        reason_codes.append("total_memory_watch")
    if total_cost_usd >= config.total_block_cost_usd:
        reason_codes.append("total_cost_block")
    elif total_cost_usd >= config.total_pass_cost_usd:
        reason_codes.append("total_cost_watch")

    status_without_terminal = _status_from_reason_codes(tuple(reason_codes))
    reason_codes.append(f"usage_guard_{status_without_terminal}")
    return ResearchMarketSourceMemoryCostGuardReportRow(
        item_digest=row.item_digest,
        observed_at=row.observed_at,
        memory_mb=row.memory_mb,
        cost_usd=row.cost_usd,
        status=status_without_terminal,
        reason_codes=_normalize_reason_codes("reason_codes", tuple(reason_codes)),
    )


def _report_public_values(
    report: ResearchMarketSourceMemoryCostGuardReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    values: dict[str, object] = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "status": report.status,
        "item_count": report.item_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "total_memory_mb": report.total_memory_mb,
        "total_cost_usd": report.total_cost_usd,
        "peak_memory_mb": report.peak_memory_mb,
        "peak_cost_usd": report.peak_cost_usd,
        "average_memory_mb": report.average_memory_mb,
        "average_cost_usd": report.average_cost_usd,
        "rows": report.rows,
        "reason_code_counts": report.reason_code_counts,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        values["validation_digest"] = report.validation_digest
    return values


def _payload_digest(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "public payload",
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
        return str(_quantize(value))
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
    if value is None or type(value) is bool or type(value) is Decimal:
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _PRIVATE_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or any(term in lowered for term in _PRIVATE_TERMS):
        raise ValueError(f"{path} has unsafe public value")


def _require_input_rows(
    name: str,
    rows: tuple[ResearchMarketSourceMemoryCostGuardInputRow, ...],
) -> tuple[ResearchMarketSourceMemoryCostGuardInputRow, ...]:
    if type(rows) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketSourceMemoryCostGuardInputRow:
            raise ValueError(
                f"{name} entries must be ResearchMarketSourceMemoryCostGuardInputRow",
            )
    return rows


def _require_report_rows(
    name: str,
    rows: tuple[ResearchMarketSourceMemoryCostGuardReportRow, ...],
) -> None:
    if type(rows) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketSourceMemoryCostGuardReportRow:
            raise ValueError(
                f"{name} entries must be ResearchMarketSourceMemoryCostGuardReportRow",
            )


def _require_reason_count_rows(
    name: str,
    rows: tuple[ResearchMarketSourceMemoryCostGuardReasonCodeCount, ...],
) -> None:
    if type(rows) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketSourceMemoryCostGuardReasonCodeCount:
            raise ValueError(
                f"{name} entries must be "
                "ResearchMarketSourceMemoryCostGuardReasonCodeCount",
            )


def _reason_code_counts(
    rows: tuple[ResearchMarketSourceMemoryCostGuardReportRow, ...],
) -> tuple[ResearchMarketSourceMemoryCostGuardReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchMarketSourceMemoryCostGuardReasonCodeCount(
            reason_code=reason_code,
            count=Decimal(counter[reason_code]),
        )
        for reason_code in sorted(counter)
    )


def _normalize_reason_codes(name: str, reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    normalized = tuple(sorted(set(reason_codes)))
    for reason_code in normalized:
        _require_reason_code(name, reason_code)
    return normalized


def _input_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f"input_{reason_code}" for reason_code in reason_codes)


def _require_reason_code(name: str, reason_code: str) -> None:
    if type(reason_code) is not str or not _PUBLIC_REASON_RE.fullmatch(reason_code):
        raise ValueError(f"{name} must contain public snake_case reason codes")
    _reject_unsafe_public_string(name, reason_code)


def _require_digest(name: str, value: str) -> None:
    if type(value) is not str or not _HEX_SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase sha256 hex digest")


def _require_public_string(name: str, value: str) -> None:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or not _PUBLIC_STRING_RE.fullmatch(value)
    ):
        raise ValueError(f"{name} must be a canonical public string")
    _reject_unsafe_public_string(name, value)


def _require_status(name: str, value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    try:
        normalized = _quantize(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name} must be a finite Decimal") from exc
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_increasing_thresholds(name: str, pass_value: Decimal, block_value: Decimal) -> None:
    if pass_value >= block_value:
        raise ValueError(f"{name} block threshold must be greater than pass threshold")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("Decimal must be finite")
    return value.quantize(QUANTUM)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _count_decimal(values: tuple[object, ...]) -> Decimal:
    return Decimal(len(values))


def _sum_if(
    rows: tuple[ResearchMarketSourceMemoryCostGuardReportRow, ...],
    predicate: object,
) -> Decimal:
    count = ZERO
    for row in rows:
        if predicate(row):
            count += ONE
    return count


def _status_rank(status: str) -> Decimal:
    if status == STATUS_BLOCK:
        return Decimal("0")
    if status == STATUS_WATCH:
        return Decimal("1")
    return Decimal("2")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[ResearchMarketSourceMemoryCostGuardReportRow, ...],
    reason_codes: tuple[str, ...],
) -> str:
    if reason_codes == (NO_ITEMS_REASON,):
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS
