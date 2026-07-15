"""Pure readonly report for market outcome resolution dependency maps."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import re
from typing import Any


__all__ = (
    "DEFAULT_MARKET_OUTCOME_RESOLUTION_DEPENDENCY_MAP_REPORT_VERSION",
    "MarketOutcomeResolutionDependencyMapConfig",
    "MarketOutcomeResolutionDependencyMapInput",
    "MarketOutcomeResolutionDependencyMapRow",
    "MarketOutcomeResolutionDependencyMapReport",
    "build_market_outcome_resolution_dependency_map_report",
    "market_outcome_resolution_dependency_map_report_payload",
)


DEFAULT_MARKET_OUTCOME_RESOLUTION_DEPENDENCY_MAP_REPORT_VERSION = (
    "market-outcome-resolution-dependency-map-report-v0"
)
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_PUBLIC_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_MANUAL_NEXT_STEPS = frozenset(
    (
        "monitor_standard_resolution_path",
        "review_resolution_dependency_map_freshness",
        "review_ambiguous_resolution_dependencies",
        "confirm_resolution_dependency_sources",
        "escalate_missing_official_resolution_source",
    ),
)
_REPORT_REASON_PRIORITY = (
    "missing_official_resolution_source",
    "stale_resolution_dependency_map",
    "dependency_count_block",
    "ambiguous_dependency_count_block",
    "resolution_dependency_map_refresh_watch",
    "dependency_count_watch",
    "ambiguous_dependency_count_watch",
    "no_resolution_dependencies",
    "official_resolution_source_present",
    "resolution_dependency_map_fresh",
)


@dataclass(frozen=True)
class MarketOutcomeResolutionDependencyMapConfig:
    config_version: str = DEFAULT_MARKET_OUTCOME_RESOLUTION_DEPENDENCY_MAP_REPORT_VERSION
    watch_dependency_count: Decimal = Decimal("1.000000")
    block_dependency_count: Decimal = Decimal("4.000000")
    watch_ambiguous_dependency_count: Decimal = Decimal("1.000000")
    block_ambiguous_dependency_count: Decimal = Decimal("2.000000")
    watch_refresh_age_hours: Decimal = Decimal("12.000000")
    block_refresh_age_hours: Decimal = Decimal("24.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketOutcomeResolutionDependencyMapConfig:
            raise TypeError(
                "MarketOutcomeResolutionDependencyMapConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketOutcomeResolutionDependencyMapConfig:
            raise ValueError(
                "config must be exactly MarketOutcomeResolutionDependencyMapConfig",
            )
        _require_public_ref("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_OUTCOME_RESOLUTION_DEPENDENCY_MAP_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_dependency_count",
            "block_dependency_count",
            "watch_ambiguous_dependency_count",
            "block_ambiguous_dependency_count",
            "watch_refresh_age_hours",
            "block_refresh_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_sequence(
            "watch_dependency_count",
            self.watch_dependency_count,
            "block_dependency_count",
            self.block_dependency_count,
        )
        _require_threshold_sequence(
            "watch_ambiguous_dependency_count",
            self.watch_ambiguous_dependency_count,
            "block_ambiguous_dependency_count",
            self.block_ambiguous_dependency_count,
        )
        _require_threshold_sequence(
            "watch_refresh_age_hours",
            self.watch_refresh_age_hours,
            "block_refresh_age_hours",
            self.block_refresh_age_hours,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketOutcomeResolutionDependencyMapInput:
    market_ref: str
    resolution_source_refs: tuple[str, ...]
    dependency_count: Decimal
    official_source_present: bool
    ambiguous_dependency_count: Decimal
    refresh_age_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketOutcomeResolutionDependencyMapInput:
            raise TypeError(
                "MarketOutcomeResolutionDependencyMapInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketOutcomeResolutionDependencyMapInput:
            raise ValueError("input must be exactly MarketOutcomeResolutionDependencyMapInput")
        _require_public_ref("market_ref", self.market_ref)
        object.__setattr__(
            self,
            "resolution_source_refs",
            _normalize_refs("resolution_source_refs", self.resolution_source_refs),
        )
        if type(self.official_source_present) is not bool:
            raise ValueError("official_source_present must be a bool")
        for field_name in (
            "dependency_count",
            "ambiguous_dependency_count",
            "refresh_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.ambiguous_dependency_count > self.dependency_count:
            raise ValueError("ambiguous_dependency_count must not exceed dependency_count")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class MarketOutcomeResolutionDependencyMapRow:
    market_ref: str
    resolution_source_refs: tuple[str, ...]
    dependency_count: Decimal
    official_source_present: bool
    ambiguous_dependency_count: Decimal
    refresh_age_hours: Decimal
    dependency_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketOutcomeResolutionDependencyMapRow:
            raise TypeError(
                "MarketOutcomeResolutionDependencyMapRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketOutcomeResolutionDependencyMapRow:
            raise ValueError("row must be exactly MarketOutcomeResolutionDependencyMapRow")
        _require_public_ref("market_ref", self.market_ref)
        object.__setattr__(
            self,
            "resolution_source_refs",
            _normalize_refs("resolution_source_refs", self.resolution_source_refs),
        )
        if type(self.official_source_present) is not bool:
            raise ValueError("official_source_present must be a bool")
        for field_name in (
            "dependency_count",
            "ambiguous_dependency_count",
            "refresh_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.ambiguous_dependency_count > self.dependency_count:
            raise ValueError("ambiguous_dependency_count must not exceed dependency_count")
        _require_status("dependency_status", self.dependency_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        if self.dependency_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("dependency_status must match reason_codes")
        if self.manual_next_step != _manual_next_step_from_reason_codes(self.reason_codes):
            raise ValueError("manual_next_step must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketOutcomeResolutionDependencyMapReport:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    official_source_present_count: Decimal
    ambiguous_dependency_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketOutcomeResolutionDependencyMapRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketOutcomeResolutionDependencyMapReport:
            raise TypeError(
                "MarketOutcomeResolutionDependencyMapReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketOutcomeResolutionDependencyMapReport:
            raise ValueError(
                "report must be exactly MarketOutcomeResolutionDependencyMapReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_ref("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_OUTCOME_RESOLUTION_DEPENDENCY_MAP_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "block_count",
            "official_source_present_count",
            "ambiguous_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_market_outcome_resolution_dependency_map_report(
    inputs: Iterable[MarketOutcomeResolutionDependencyMapInput],
    *,
    generated_at: datetime,
    config: MarketOutcomeResolutionDependencyMapConfig | None = None,
) -> MarketOutcomeResolutionDependencyMapReport:
    if config is None:
        config = MarketOutcomeResolutionDependencyMapConfig()
    if type(config) is not MarketOutcomeResolutionDependencyMapConfig:
        raise ValueError("config must be a MarketOutcomeResolutionDependencyMapConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in normalized_inputs),
            key=_row_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return MarketOutcomeResolutionDependencyMapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        official_source_present_count=_count(
            sum(1 for row in rows if row.official_source_present),
        ),
        ambiguous_dependency_count=sum(
            (row.ambiguous_dependency_count for row in rows),
            _ZERO,
        ),
        status=_report_status(rows),
        reason_codes=reason_codes,
        rows=rows,
    )


def market_outcome_resolution_dependency_map_report_payload(
    report: MarketOutcomeResolutionDependencyMapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketOutcomeResolutionDependencyMapReport:
        _require_hard_flags("report", report)
        payload = report.payload
    elif type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
    else:
        raise ValueError(
            "report must be a MarketOutcomeResolutionDependencyMapReport",
        )
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, Any]

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
    item: MarketOutcomeResolutionDependencyMapInput,
    *,
    config: MarketOutcomeResolutionDependencyMapConfig,
) -> MarketOutcomeResolutionDependencyMapRow:
    reason_codes = _row_reason_codes(item, config)
    return MarketOutcomeResolutionDependencyMapRow(
        market_ref=item.market_ref,
        resolution_source_refs=item.resolution_source_refs,
        dependency_count=item.dependency_count,
        official_source_present=item.official_source_present,
        ambiguous_dependency_count=item.ambiguous_dependency_count,
        refresh_age_hours=item.refresh_age_hours,
        dependency_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step_from_reason_codes(reason_codes),
    )


def _row_reason_codes(
    item: MarketOutcomeResolutionDependencyMapInput,
    config: MarketOutcomeResolutionDependencyMapConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if not item.official_source_present:
        codes.append("missing_official_resolution_source")
    if item.refresh_age_hours >= config.block_refresh_age_hours:
        codes.append("stale_resolution_dependency_map")
    elif item.refresh_age_hours >= config.watch_refresh_age_hours:
        codes.append("resolution_dependency_map_refresh_watch")
    if item.dependency_count >= config.block_dependency_count:
        codes.append("dependency_count_block")
    elif item.dependency_count >= config.watch_dependency_count:
        codes.append("dependency_count_watch")
    else:
        codes.append("no_resolution_dependencies")
    if item.ambiguous_dependency_count >= config.block_ambiguous_dependency_count:
        codes.append("ambiguous_dependency_count_block")
    elif item.ambiguous_dependency_count >= config.watch_ambiguous_dependency_count:
        codes.append("ambiguous_dependency_count_watch")
    if item.official_source_present:
        codes.append("official_resolution_source_present")
    if item.refresh_age_hours < config.watch_refresh_age_hours:
        codes.append("resolution_dependency_map_fresh")
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _manual_next_step_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "missing_official_resolution_source" in reason_codes:
        return "escalate_missing_official_resolution_source"
    if "ambiguous_dependency_count_block" in reason_codes:
        return "review_ambiguous_resolution_dependencies"
    if "dependency_count_block" in reason_codes:
        return "confirm_resolution_dependency_sources"
    if "stale_resolution_dependency_map" in reason_codes:
        return "review_resolution_dependency_map_freshness"
    if "ambiguous_dependency_count_watch" in reason_codes:
        return "review_ambiguous_resolution_dependencies"
    if "dependency_count_watch" in reason_codes:
        return "confirm_resolution_dependency_sources"
    if "resolution_dependency_map_refresh_watch" in reason_codes:
        return "review_resolution_dependency_map_freshness"
    return "monitor_standard_resolution_path"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes) or (
        "missing_official_resolution_source" in reason_codes
    ) or ("stale_resolution_dependency_map" in reason_codes):
        return "block"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[MarketOutcomeResolutionDependencyMapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_market_resolution_dependency_inputs",)
    codes: list[str] = [f"outcome_resolution_dependency_map_report_{_report_status(rows)}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    for code in _REPORT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    for code in row_codes:
        if code not in codes:
            codes.append(code)
    return tuple(codes)


def _report_status(rows: tuple[MarketOutcomeResolutionDependencyMapRow, ...]) -> str:
    statuses = tuple(row.dependency_status for row in rows)
    if not statuses or "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _validate_report(report: MarketOutcomeResolutionDependencyMapReport) -> None:
    rows = report.rows
    if report.market_count != _count(len(rows)):
        raise ValueError("market_count must match rows")
    if report.pass_count != _count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.official_source_present_count != _count(
        sum(1 for row in rows if row.official_source_present),
    ):
        raise ValueError("official_source_present_count must match rows")
    if report.ambiguous_dependency_count != sum(
        (row.ambiguous_dependency_count for row in rows),
        _ZERO,
    ):
        raise ValueError("ambiguous_dependency_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _normalize_inputs(
    inputs: Iterable[MarketOutcomeResolutionDependencyMapInput],
) -> tuple[MarketOutcomeResolutionDependencyMapInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not MarketOutcomeResolutionDependencyMapInput:
            raise ValueError("inputs must contain MarketOutcomeResolutionDependencyMapInput")
        if item.market_ref in seen:
            raise ValueError("market_ref values must be unique")
        seen.add(item.market_ref)
        _require_hard_flags("input", item)
    return normalized


def _normalize_rows(
    rows: tuple[MarketOutcomeResolutionDependencyMapRow, ...],
) -> tuple[MarketOutcomeResolutionDependencyMapRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must be sorted by market_ref")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketOutcomeResolutionDependencyMapRow:
            raise ValueError("rows must contain MarketOutcomeResolutionDependencyMapRow")
        if row.market_ref in seen:
            raise ValueError("rows market_ref values must be unique")
        seen.add(row.market_ref)
        _require_hard_flags("row", row)
    return rows


def _normalize_refs(field_name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for value in values:
        _require_public_ref(field_name, value)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    values: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not _REASON_CODE_RE.fullmatch(value):
            raise ValueError(f"{field_name} must be lowercase snake_case strings")
        if value not in normalized:
            normalized.append(value)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _input_key(item: MarketOutcomeResolutionDependencyMapInput) -> str:
    return item.market_ref


def _row_key(row: MarketOutcomeResolutionDependencyMapRow) -> str:
    return f"{_status_rank(row.dependency_status)}:{row.market_ref}"


def _status_rank(status: str) -> str:
    if status == "pass":
        return "0"
    if status == "watch":
        return "1"
    return "2"


def _status_count(
    rows: tuple[MarketOutcomeResolutionDependencyMapRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.dependency_status == status)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_public_ref(field_name: str, value: object) -> None:
    if type(value) is not str or not _PUBLIC_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_manual_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a supported manual next step")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    if normalized != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_threshold_sequence(
    watch_field: str,
    watch_value: Decimal,
    block_field: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_field} must exceed {watch_field}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    normalized = value.astimezone(UTC)
    if normalized.tzinfo is not UTC:
        raise ValueError(f"{field_name} must normalize to UTC")
    return normalized


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
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {
            _json_ready(key): _json_ready(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


for _type in (
    MarketOutcomeResolutionDependencyMapConfig,
    MarketOutcomeResolutionDependencyMapInput,
    MarketOutcomeResolutionDependencyMapRow,
    MarketOutcomeResolutionDependencyMapReport,
):
    for _field in fields(_type):
        if _field.name in _PHASE_FLAG_FIELDS:
            continue
