"""Pure report-only cost/probability memory guard research report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_MARKET_COST_PROBABILITY_MEMORY_GUARD_CONFIG_VERSION = (
    "research-market-cost-probability-memory-guard-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_THREE = Decimal("3.000000")
_PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = ("pass", "watch", "block")
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_REASON_CODE_SEQUENCE = (
    "no_observations",
    "cost_pressure_high",
    "probability_pressure_high",
    "memory_pressure_high",
    "composite_pressure_watch",
    "composite_pressure_block",
    "memory_guard_pass",
)
_SENSITIVE_PUBLIC_TERMS = tuple(
    "".join(parts)
    for parts in (
        ("raw",),
        ("candi", "date"),
        ("market_id",),
        ("market-id",),
        ("market.id",),
        ("marketid",),
        ("market_slug",),
        ("market-slug",),
        ("market.slug",),
        ("marketslug",),
        ("slug",),
        ("question",),
        ("sou", "rce"),
        ("u", "rl"),
        ("te", "xt"),
        ("d", "sn"),
        ("ta", "ble"),
        ("tok", "en"),
        ("d", "b"),
        ("net", "work"),
        ("wall", "et"),
        ("au", "th"),
        ("ord", "er"),
        ("li", "ve"),
        ("tra", "de"),
        ("trad", "ing"),
        ("siz", "ing"),
        ("recomm", "endation"),
    )
)


@dataclass(frozen=True)
class ResearchMarketCostProbabilityMemoryGuardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_COST_PROBABILITY_MEMORY_GUARD_CONFIG_VERSION
    )
    watch_threshold: Decimal = Decimal("0.500000")
    block_threshold: Decimal = Decimal("0.750000")
    cost_weight: Decimal = Decimal("0.400000")
    probability_weight: Decimal = Decimal("0.300000")
    memory_weight: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketCostProbabilityMemoryGuardConfig:
            raise TypeError(
                "ResearchMarketCostProbabilityMemoryGuardConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketCostProbabilityMemoryGuardConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchMarketCostProbabilityMemoryGuardConfig",
            )
        _require_public_id("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_COST_PROBABILITY_MEMORY_GUARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_threshold",
            "block_threshold",
            "cost_weight",
            "probability_weight",
            "memory_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_threshold >= self.block_threshold:
            raise ValueError("watch_threshold must be less than block_threshold")
        if (
            _quantize(self.cost_weight + self.probability_weight + self.memory_weight)
            != _ONE
        ):
            raise ValueError(
                "cost_weight, probability_weight, and memory_weight must sum to one",
            )
        _require_hard_flags("config", self)
        _reject_sensitive_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketCostProbabilityMemoryGuardObservation:
    research_id: str
    observation_id: str
    observed_at: datetime
    cost_pressure: Decimal
    probability_pressure: Decimal
    memory_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketCostProbabilityMemoryGuardObservation:
            raise TypeError(
                "ResearchMarketCostProbabilityMemoryGuardObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketCostProbabilityMemoryGuardObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchMarketCostProbabilityMemoryGuardObservation",
            )
        for field_name in ("research_id", "observation_id"):
            _require_public_id(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "cost_pressure",
            "probability_pressure",
            "memory_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem:
            raise TypeError(
                "ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem",
            )
        _require_public_id("key", self.key)
        _require_public_value("value", self.value)
        _require_hard_flags("public payload item", self)
        _reject_sensitive_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchMarketCostProbabilityMemoryGuardRow:
    research_digest: str
    observation_count: Decimal
    latest_observed_at: datetime
    max_cost_pressure: Decimal
    max_probability_pressure: Decimal
    max_memory_pressure: Decimal
    composite_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketCostProbabilityMemoryGuardRow:
            raise TypeError(
                "ResearchMarketCostProbabilityMemoryGuardRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketCostProbabilityMemoryGuardRow:
            raise ValueError("row must be exactly ResearchMarketCostProbabilityMemoryGuardRow")
        _require_sha256_digest("research_digest", self.research_digest)
        object.__setattr__(
            self,
            "observation_count",
            _require_positive_count_decimal(
                "observation_count",
                self.observation_count,
            ),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "max_cost_pressure",
            "max_probability_pressure",
            "max_memory_pressure",
            "composite_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_sensitive_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketCostProbabilityMemoryGuardReport:
    generated_at: datetime
    config_version: str
    status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_composite_pressure: Decimal
    max_composite_pressure: Decimal
    rows: tuple[ResearchMarketCostProbabilityMemoryGuardRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[
        ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketCostProbabilityMemoryGuardReport:
            raise TypeError(
                "ResearchMarketCostProbabilityMemoryGuardReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketCostProbabilityMemoryGuardReport:
            raise ValueError(
                "report must be exactly ResearchMarketCostProbabilityMemoryGuardReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_id("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_COST_PROBABILITY_MEMORY_GUARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_composite_pressure", "max_composite_pressure"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_sensitive_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_sensitive_public_payload(
            "ResearchMarketCostProbabilityMemoryGuardReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_market_cost_probability_memory_guard_report(
    observations: Sequence[ResearchMarketCostProbabilityMemoryGuardObservation],
    *,
    generated_at: datetime,
    config: ResearchMarketCostProbabilityMemoryGuardConfig | None = None,
    public_payload: Sequence[
        ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem
    ] = (),
) -> ResearchMarketCostProbabilityMemoryGuardReport:
    if config is None:
        config = ResearchMarketCostProbabilityMemoryGuardConfig()
    if type(config) is not ResearchMarketCostProbabilityMemoryGuardConfig:
        raise ValueError(
            "config must be a ResearchMarketCostProbabilityMemoryGuardConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.observed_at > generated_at:
            raise ValueError("observation observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    _reject_public_payload_observation_identifiers(
        payload_items,
        normalized_observations,
    )
    rows = _normalize_rows(_build_rows(normalized_observations, config))
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "item_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_composite_pressure": _average(
            tuple(row.composite_pressure for row in rows),
        ),
        "max_composite_pressure": max(
            (row.composite_pressure for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketCostProbabilityMemoryGuardReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    observations: tuple[ResearchMarketCostProbabilityMemoryGuardObservation, ...],
    config: ResearchMarketCostProbabilityMemoryGuardConfig,
) -> tuple[ResearchMarketCostProbabilityMemoryGuardRow, ...]:
    grouped: dict[str, list[ResearchMarketCostProbabilityMemoryGuardObservation]] = {}
    for item in observations:
        grouped.setdefault(item.research_id, []).append(item)
    return tuple(
        _row_for_group(research_id, tuple(items), config)
        for research_id, items in sorted(grouped.items())
    )


def _row_for_group(
    research_id: str,
    observations: tuple[ResearchMarketCostProbabilityMemoryGuardObservation, ...],
    config: ResearchMarketCostProbabilityMemoryGuardConfig,
) -> ResearchMarketCostProbabilityMemoryGuardRow:
    latest_observed_at = max(item.observed_at for item in observations)
    max_cost_pressure = max(item.cost_pressure for item in observations)
    max_probability_pressure = max(item.probability_pressure for item in observations)
    max_memory_pressure = max(item.memory_pressure for item in observations)
    composite_pressure = _clamp_ratio(
        (max_cost_pressure * config.cost_weight)
        + (max_probability_pressure * config.probability_weight)
        + (max_memory_pressure * config.memory_weight),
    )
    status = _row_status(composite_pressure, config)
    return ResearchMarketCostProbabilityMemoryGuardRow(
        research_digest=_stable_digest(research_id),
        observation_count=_decimal_count(len(observations)),
        latest_observed_at=latest_observed_at,
        max_cost_pressure=max_cost_pressure,
        max_probability_pressure=max_probability_pressure,
        max_memory_pressure=max_memory_pressure,
        composite_pressure=composite_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            max_cost_pressure=max_cost_pressure,
            max_probability_pressure=max_probability_pressure,
            max_memory_pressure=max_memory_pressure,
            composite_pressure=composite_pressure,
            config=config,
        ),
    )


def _row_status(
    composite_pressure: Decimal,
    config: ResearchMarketCostProbabilityMemoryGuardConfig,
) -> str:
    if composite_pressure >= config.block_threshold:
        return "block"
    if composite_pressure >= config.watch_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    max_cost_pressure: Decimal,
    max_probability_pressure: Decimal,
    max_memory_pressure: Decimal,
    composite_pressure: Decimal,
    config: ResearchMarketCostProbabilityMemoryGuardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if max_cost_pressure >= config.watch_threshold:
        reason_codes.append("cost_pressure_high")
    if max_probability_pressure >= config.watch_threshold:
        reason_codes.append("probability_pressure_high")
    if max_memory_pressure >= config.watch_threshold:
        reason_codes.append("memory_pressure_high")
    if status == "watch" and composite_pressure >= config.watch_threshold:
        reason_codes.append("composite_pressure_watch")
    if status == "block":
        reason_codes.append("composite_pressure_block")
    if status == "pass":
        reason_codes.append("memory_guard_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchMarketCostProbabilityMemoryGuardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_observations",)
    seen: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in seen:
                seen.append(reason_code)
    return _normalize_reason_codes(tuple(seen))


def _report_status(
    rows: tuple[ResearchMarketCostProbabilityMemoryGuardRow, ...],
) -> str:
    if not rows:
        return "block"
    statuses = tuple(row.status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchMarketCostProbabilityMemoryGuardRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_observations(
    observations: Sequence[ResearchMarketCostProbabilityMemoryGuardObservation],
) -> tuple[ResearchMarketCostProbabilityMemoryGuardObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchMarketCostProbabilityMemoryGuardObservation] = []
    seen: set[tuple[str, str]] = set()
    for item in observations:
        if type(item) is not ResearchMarketCostProbabilityMemoryGuardObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketCostProbabilityMemoryGuardObservation items",
            )
        key = (item.research_id, item.observation_id)
        if key in seen:
            raise ValueError("observations must not contain duplicate public ids")
        seen.add(key)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (item.research_id, item.observed_at, item.observation_id),
        ),
    )


def _normalize_rows(
    rows: tuple[ResearchMarketCostProbabilityMemoryGuardRow, ...],
) -> tuple[ResearchMarketCostProbabilityMemoryGuardRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketCostProbabilityMemoryGuardRow:
            raise ValueError(
                "rows must contain ResearchMarketCostProbabilityMemoryGuardRow items",
            )
    normalized = tuple(sorted(rows, key=lambda row: row.research_digest))
    if len({row.research_digest for row in normalized}) != len(normalized):
        raise ValueError("rows must not contain duplicate research digests")
    return normalized


def _normalize_public_payload(
    public_payload: Sequence[ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem],
) -> tuple[ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem items",
            )
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _reject_public_payload_observation_identifiers(
    public_payload: tuple[ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem, ...],
    observations: tuple[ResearchMarketCostProbabilityMemoryGuardObservation, ...],
) -> None:
    known_identifiers = {
        identifier.lower()
        for item in observations
        for identifier in (item.research_id, item.observation_id)
    }
    for item in public_payload:
        for public_value in (item.key, item.value):
            lowered = public_value.lower()
            for identifier in known_identifiers:
                if lowered == identifier or (
                    len(identifier) >= 3 and identifier in lowered
                ):
                    raise ValueError(
                        "public_payload must not contain observation identifiers",
                    )


def _validate_row_consistency(
    row: ResearchMarketCostProbabilityMemoryGuardRow,
) -> None:
    if row.status == "pass" and "memory_guard_pass" not in row.reason_codes:
        raise ValueError("pass row must include memory_guard_pass")
    if row.status == "watch" and "composite_pressure_watch" not in row.reason_codes:
        raise ValueError("watch row must include composite_pressure_watch")
    if row.status == "block" and "composite_pressure_block" not in row.reason_codes:
        raise ValueError("block row must include composite_pressure_block")


def _validate_report_consistency(
    report: ResearchMarketCostProbabilityMemoryGuardReport,
) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must equal rows length")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must equal pass rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must equal watch rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must equal block rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must summarize rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must summarize rows")
    expected_average = _average(tuple(row.composite_pressure for row in report.rows))
    if report.average_composite_pressure != expected_average:
        raise ValueError("average_composite_pressure must summarize rows")
    expected_max = max((row.composite_pressure for row in report.rows), default=_ZERO)
    if report.max_composite_pressure != expected_max:
        raise ValueError("max_composite_pressure must summarize rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_public_id(field_name: str, value: object) -> None:
    if type(value) is not str or _PUBLIC_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_sensitive_public_string(field_name, value)


def _require_public_value(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value or len(value) > 256:
        raise ValueError(f"{field_name} must be a canonical public value")
    _reject_sensitive_public_string(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of {_STATUSES}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value().quantize(_QUANT):
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
        raise ValueError("count must be a nonnegative int")
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


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in _REASON_CODE_SEQUENCE:
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


def _stable_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchMarketCostProbabilityMemoryGuardReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_sensitive_public_payload(
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


def _reject_sensitive_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_sensitive_public_key(field.name, current_path)
            _reject_sensitive_public_payload(
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
            _reject_sensitive_public_key(key, current_path)
            _reject_sensitive_public_payload(
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
            _reject_sensitive_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_sensitive_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_sensitive_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if lowered in {"research_id", "observation_id"}:
        return
    if any(term in lowered for term in _SENSITIVE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has sensitive public field")


def _reject_sensitive_public_string(path: str, value: str) -> None:
    if _SHA256_RE.fullmatch(value) is not None:
        return
    lowered = value.lower()
    if any(term in lowered for term in _SENSITIVE_PUBLIC_TERMS):
        raise ValueError(f"{path} has sensitive public value")
    if "://" in lowered or "@" in lowered or "/" in lowered or "\\" in lowered:
        raise ValueError(f"{path} has sensitive public value")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_COST_PROBABILITY_MEMORY_GUARD_CONFIG_VERSION",
    "ResearchMarketCostProbabilityMemoryGuardConfig",
    "ResearchMarketCostProbabilityMemoryGuardObservation",
    "ResearchMarketCostProbabilityMemoryGuardPublicPayloadItem",
    "ResearchMarketCostProbabilityMemoryGuardReport",
    "ResearchMarketCostProbabilityMemoryGuardRow",
    "build_research_market_cost_probability_memory_guard_report",
)
