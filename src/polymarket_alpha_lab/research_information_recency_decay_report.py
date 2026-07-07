"""Report-only reducer for research information recency decay."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_INFORMATION_RECENCY_DECAY_REPORT_CONFIG_VERSION = (
    "research-information-recency-decay-report-v1"
)

_DECIMAL_PRECISION = 64
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_HALF = Decimal("0.500000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = ("pass", "watch", "block")
_REFRESH_PRIORITIES = ("low", "medium", "high", "critical")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "://",
    "http",
    "www.",
    "source_url",
    "source_text",
    "source_ref",
    "market_id",
    "market",
)
_REASON_CODE_SEQUENCE = (
    "empty_information",
    "refresh_window_breached",
    "recency_weight_pass",
    "recency_weight_watch",
    "recency_weight_block",
    "expiry_risk_low",
    "expiry_risk_elevated",
    "expiry_risk_high",
    "time_pressure_high",
    "refresh_priority_critical",
    "refresh_priority_high",
    "refresh_priority_medium",
    "refresh_priority_low",
)
_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "report_status",
    "item_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_recency_weight",
    "max_expiry_risk_score",
    "overall_refresh_priority",
    "rows",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchInformationRecencyConfig:
    config_version: str = DEFAULT_RESEARCH_INFORMATION_RECENCY_DECAY_REPORT_CONFIG_VERSION
    pass_recency_weight_min: Decimal = Decimal("0.650000")
    watch_recency_weight_min: Decimal = Decimal("0.250000")
    elevated_expiry_risk_min: Decimal = Decimal("0.500000")
    high_expiry_risk_min: Decimal = Decimal("0.750000")
    high_time_pressure_min: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationRecencyConfig:
            raise TypeError("ResearchInformationRecencyConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationRecencyConfig:
            raise ValueError("config must be exactly ResearchInformationRecencyConfig")
        _require_config_version(self.config_version)
        for field_name in (
            "pass_recency_weight_min",
            "watch_recency_weight_min",
            "elevated_expiry_risk_min",
            "high_expiry_risk_min",
            "high_time_pressure_min",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_recency_weight_min >= self.pass_recency_weight_min:
            raise ValueError("watch_recency_weight_min must be below pass_recency_weight_min")
        if self.elevated_expiry_risk_min >= self.high_expiry_risk_min:
            raise ValueError("elevated_expiry_risk_min must be below high_expiry_risk_min")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchInformationRecencyItem:
    topic_key: str
    source_family: str
    information_age_minutes: Decimal
    half_life_minutes: Decimal
    refresh_window_minutes: Decimal
    source_reliability: Decimal
    time_sensitivity: Decimal
    resolution_urgency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationRecencyItem:
            raise TypeError("ResearchInformationRecencyItem does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationRecencyItem:
            raise ValueError("item must be exactly ResearchInformationRecencyItem")
        _require_public_identifier("topic_key", self.topic_key)
        _require_public_identifier("source_family", self.source_family)
        object.__setattr__(
            self,
            "information_age_minutes",
            _require_nonnegative_decimal(
                "information_age_minutes",
                self.information_age_minutes,
            ),
        )
        for field_name in ("half_life_minutes", "refresh_window_minutes"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_reliability",
            "time_sensitivity",
            "resolution_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("item", self)
        _reject_unsafe_public_payload("item", self)


@dataclass(frozen=True)
class ResearchInformationRecencyRow:
    topic_key: str
    source_family: str
    information_age_minutes: Decimal
    half_life_minutes: Decimal
    refresh_window_minutes: Decimal
    refresh_window_remaining_minutes: Decimal
    source_reliability: Decimal
    time_sensitivity: Decimal
    resolution_urgency: Decimal
    recency_weight: Decimal
    expiry_risk_score: Decimal
    recency_status: str
    refresh_priority: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationRecencyRow:
            raise TypeError("ResearchInformationRecencyRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationRecencyRow:
            raise ValueError("row must be exactly ResearchInformationRecencyRow")
        _require_public_identifier("topic_key", self.topic_key)
        _require_public_identifier("source_family", self.source_family)
        for field_name in (
            "information_age_minutes",
            "refresh_window_remaining_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("half_life_minutes", "refresh_window_minutes"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_reliability",
            "time_sensitivity",
            "resolution_urgency",
            "recency_weight",
            "expiry_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("recency_status", self.recency_status, _STATUSES)
        _require_member("refresh_priority", self.refresh_priority, _REFRESH_PRIORITIES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchInformationRecencyDecayReport:
    generated_at: datetime
    config_version: str
    report_status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_recency_weight: Decimal
    max_expiry_risk_score: Decimal
    overall_refresh_priority: str
    rows: tuple[ResearchInformationRecencyRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationRecencyDecayReport:
            raise TypeError(
                "ResearchInformationRecencyDecayReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationRecencyDecayReport:
            raise ValueError("report must be exactly ResearchInformationRecencyDecayReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        _require_member("report_status", self.report_status, _STATUSES)
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_recency_weight", "max_expiry_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "overall_refresh_priority",
            self.overall_refresh_priority,
            _REFRESH_PRIORITIES,
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_information_recency_decay_report_payload(self)


def build_research_information_recency_decay_report(
    items: Sequence[ResearchInformationRecencyItem],
    *,
    generated_at: datetime,
    config: ResearchInformationRecencyConfig | None = None,
) -> ResearchInformationRecencyDecayReport:
    if config is None:
        config = ResearchInformationRecencyConfig()
    if type(config) is not ResearchInformationRecencyConfig:
        raise ValueError("config must be a ResearchInformationRecencyConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    rows = tuple(_row_for_item(item, config) for item in normalized_items)
    rows = _normalize_rows(rows)
    reason_codes = _report_reason_codes(rows)
    return ResearchInformationRecencyDecayReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_status=_report_status(rows),
        item_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_recency_weight=_average(tuple(row.recency_weight for row in rows)),
        max_expiry_risk_score=max(
            (row.expiry_risk_score for row in rows),
            default=_ZERO,
        ),
        overall_refresh_priority=_overall_refresh_priority(rows),
        rows=rows,
        reason_codes=reason_codes,
    )


def research_information_recency_decay_report_payload(
    report: ResearchInformationRecencyDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchInformationRecencyDecayReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsupported_payload_fields(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchInformationRecencyDecayReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsupported_payload_fields(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload(
        "ResearchInformationRecencyDecayReport.payload",
        payload,
        allow_json_containers=True,
    )
    return payload


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


def _row_for_item(
    item: ResearchInformationRecencyItem,
    config: ResearchInformationRecencyConfig,
) -> ResearchInformationRecencyRow:
    recency_weight = _recency_weight(item)
    expiry_risk_score = _clamp_ratio(_ONE - recency_weight)
    recency_status = _recency_status(recency_weight, config)
    refresh_priority = _refresh_priority(
        item,
        recency_status=recency_status,
        expiry_risk_score=expiry_risk_score,
        config=config,
    )
    return ResearchInformationRecencyRow(
        topic_key=item.topic_key,
        source_family=item.source_family,
        information_age_minutes=item.information_age_minutes,
        half_life_minutes=item.half_life_minutes,
        refresh_window_minutes=item.refresh_window_minutes,
        refresh_window_remaining_minutes=_refresh_window_remaining(item),
        source_reliability=item.source_reliability,
        time_sensitivity=item.time_sensitivity,
        resolution_urgency=item.resolution_urgency,
        recency_weight=recency_weight,
        expiry_risk_score=expiry_risk_score,
        recency_status=recency_status,
        refresh_priority=refresh_priority,
        reason_codes=_row_reason_codes(
            item,
            recency_status=recency_status,
            expiry_risk_score=expiry_risk_score,
            refresh_priority=refresh_priority,
            config=config,
        ),
    )


def _recency_weight(item: ResearchInformationRecencyItem) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = _DECIMAL_PRECISION
        age_ratio = item.information_age_minutes / item.half_life_minutes
        decay_curve = ctx.power(_HALF, age_ratio)
        raw_weight = item.source_reliability * decay_curve
    return _clamp_ratio(_quantize(raw_weight))


def _recency_status(
    recency_weight: Decimal,
    config: ResearchInformationRecencyConfig,
) -> str:
    if recency_weight >= config.pass_recency_weight_min:
        return "pass"
    if recency_weight >= config.watch_recency_weight_min:
        return "watch"
    return "block"


def _refresh_priority(
    item: ResearchInformationRecencyItem,
    *,
    recency_status: str,
    expiry_risk_score: Decimal,
    config: ResearchInformationRecencyConfig,
) -> str:
    if (
        recency_status == "block"
        or item.information_age_minutes >= item.refresh_window_minutes
        or expiry_risk_score >= config.high_expiry_risk_min
    ):
        return "critical"
    if (
        recency_status == "watch"
        or expiry_risk_score >= config.elevated_expiry_risk_min
        or _time_pressure(item) >= config.high_time_pressure_min
    ):
        return "high"
    if _window_elapsed_ratio(item) >= config.elevated_expiry_risk_min:
        return "medium"
    return "low"


def _row_reason_codes(
    item: ResearchInformationRecencyItem,
    *,
    recency_status: str,
    expiry_risk_score: Decimal,
    refresh_priority: str,
    config: ResearchInformationRecencyConfig,
) -> tuple[str, ...]:
    reason_codes = []
    if item.information_age_minutes >= item.refresh_window_minutes:
        reason_codes.append("refresh_window_breached")
    reason_codes.append(f"recency_weight_{recency_status}")
    reason_codes.append(_expiry_risk_reason_code(expiry_risk_score, config))
    if _time_pressure(item) >= config.high_time_pressure_min:
        reason_codes.append("time_pressure_high")
    reason_codes.append(f"refresh_priority_{refresh_priority}")
    return _normalize_reason_codes(tuple(reason_codes))


def _expiry_risk_reason_code(
    expiry_risk_score: Decimal,
    config: ResearchInformationRecencyConfig,
) -> str:
    if expiry_risk_score >= config.high_expiry_risk_min:
        return "expiry_risk_high"
    if expiry_risk_score >= config.elevated_expiry_risk_min:
        return "expiry_risk_elevated"
    return "expiry_risk_low"


def _time_pressure(item: ResearchInformationRecencyItem) -> Decimal:
    return _quantize((item.time_sensitivity + item.resolution_urgency) / _TWO)


def _window_elapsed_ratio(item: ResearchInformationRecencyItem) -> Decimal:
    return _clamp_ratio(_quantize(item.information_age_minutes / item.refresh_window_minutes))


def _refresh_window_remaining(item: ResearchInformationRecencyItem) -> Decimal:
    return _quantize(max(item.refresh_window_minutes - item.information_age_minutes, _ZERO))


def _report_status(rows: tuple[ResearchInformationRecencyRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.recency_status == "block" for row in rows):
        return "block"
    if any(row.recency_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _overall_refresh_priority(rows: tuple[ResearchInformationRecencyRow, ...]) -> str:
    if not rows:
        return "critical"
    return min(rows, key=lambda row: _PRIORITY_RANK[row.refresh_priority]).refresh_priority


def _report_reason_codes(
    rows: tuple[ResearchInformationRecencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_information", "refresh_priority_critical")
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(rows: tuple[ResearchInformationRecencyRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.recency_status == status)


def _validate_row_consistency(row: ResearchInformationRecencyRow) -> None:
    if row.refresh_window_remaining_minutes != _quantize(
        max(row.refresh_window_minutes - row.information_age_minutes, _ZERO),
    ):
        raise ValueError("refresh_window_remaining_minutes must match age and window")
    if row.recency_status == "block" and "recency_weight_block" not in row.reason_codes:
        raise ValueError("block rows must include recency_weight_block")
    if row.refresh_priority == "critical" and (
        "refresh_priority_critical" not in row.reason_codes
    ):
        raise ValueError("critical rows must include refresh_priority_critical")


def _validate_report_consistency(report: ResearchInformationRecencyDecayReport) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_recency_weight != _average(
        tuple(row.recency_weight for row in report.rows),
    ):
        raise ValueError("average_recency_weight must match rows")
    expected_max = max((row.expiry_risk_score for row in report.rows), default=_ZERO)
    if report.max_expiry_risk_score != expected_max:
        raise ValueError("max_expiry_risk_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.overall_refresh_priority != _overall_refresh_priority(report.rows):
        raise ValueError("overall_refresh_priority must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_items(
    items: Sequence[ResearchInformationRecencyItem],
) -> tuple[ResearchInformationRecencyItem, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("items must be a sequence")
    normalized: list[ResearchInformationRecencyItem] = []
    for item in items:
        if type(item) is not ResearchInformationRecencyItem:
            raise ValueError("items must be ResearchInformationRecencyItem")
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: (item.topic_key, item.source_family)))


def _normalize_rows(
    rows: Sequence[ResearchInformationRecencyRow],
) -> tuple[ResearchInformationRecencyRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchInformationRecencyRow] = []
    for row in rows:
        if type(row) is not ResearchInformationRecencyRow:
            raise ValueError("rows must contain ResearchInformationRecencyRow")
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                _PRIORITY_RANK[row.refresh_priority],
                _STATUS_RANK[row.recency_status],
                -row.expiry_risk_score,
                row.refresh_window_remaining_minutes,
                row.topic_key,
                row.source_family,
            ),
        ),
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_config_version(value: object) -> None:
    _require_public_identifier("config_version", value)
    if value != DEFAULT_RESEARCH_INFORMATION_RECENCY_DECAY_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
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
    with localcontext() as ctx:
        ctx.prec = _DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        return value.quantize(_QUANT)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


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
    if type(value) is int:
        raise ValueError("numeric payload values must be Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
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


def _reject_unsupported_payload_fields(value: dict[str, object]) -> None:
    for key in value:
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        if key not in _PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")


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
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if lowered in {"source_url", "source_text", "source_ref", "market_id"}:
        raise ValueError(f"{path}.{key} has unsafe public field")
    if lowered.endswith("_url") or lowered.endswith("_ref"):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_INFORMATION_RECENCY_DECAY_REPORT_CONFIG_VERSION",
    "ResearchInformationRecencyConfig",
    "ResearchInformationRecencyDecayReport",
    "ResearchInformationRecencyItem",
    "ResearchInformationRecencyRow",
    "build_research_information_recency_decay_report",
    "research_information_recency_decay_report_payload",
)
