"""Pure research market data staleness heatmap reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import UNSAFE_SURFACE_FIELD_FRAGMENTS


__all__ = (
    "DEFAULT_RESEARCH_MARKET_DATA_STALENESS_HEATMAP_CONFIG_VERSION",
    "ResearchMarketDataStalenessHeatmapConfig",
    "ResearchMarketDataStalenessHeatmapDigest",
    "ResearchMarketDataStalenessHeatmapInput",
    "ResearchMarketDataStalenessHeatmapReasonCodeCount",
    "ResearchMarketDataStalenessHeatmapReport",
    "ResearchMarketDataStalenessHeatmapRow",
    "build_research_market_data_staleness_heatmap_report",
    "research_market_data_staleness_heatmap_digest",
    "research_market_data_staleness_heatmap_report_payload",
)


DEFAULT_RESEARCH_MARKET_DATA_STALENESS_HEATMAP_CONFIG_VERSION = (
    "research-market-data-staleness-heatmap-report-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "market_data_staleness_heatmap_no_inputs"


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchMarketDataStalenessHeatmapConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_MARKET_DATA_STALENESS_HEATMAP_CONFIG_VERSION
    watch_age_seconds: Decimal = Decimal("3600.000000")
    block_age_seconds: Decimal = Decimal("7200.000000")
    minimum_source_family_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDataStalenessHeatmapConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_age_seconds",
            "block_age_seconds",
            "minimum_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_age_seconds > self.block_age_seconds:
            raise ValueError("watch_age_seconds must be less than or equal to limit")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketDataStalenessHeatmapInput(_FinalPublicDataclass):
    event_category: str
    source_family: str
    research_team: str
    latest_observed_at: datetime
    source_family_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDataStalenessHeatmapInput, "input")
        for field_name in ("event_category", "source_family", "research_team"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "source_family_count",
            _normalize_nonnegative_decimal(
                "source_family_count",
                self.source_family_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchMarketDataStalenessHeatmapRow(_FinalPublicDataclass):
    event_category: str
    source_family: str
    research_team: str
    latest_observed_at: datetime
    source_family_count: Decimal
    staleness_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDataStalenessHeatmapRow, "row")
        for field_name in ("event_category", "source_family", "research_team"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in ("source_family_count", "staleness_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketDataStalenessHeatmapReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDataStalenessHeatmapReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketDataStalenessHeatmapDigest(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    cell_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketDataStalenessHeatmapReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDataStalenessHeatmapDigest, "digest")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("cell_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_digest(self)
        _require_hard_flags("digest", self)
        _reject_unsafe_public_payload("digest", self)


@dataclass(frozen=True)
class ResearchMarketDataStalenessHeatmapReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    cell_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_watch_count: Decimal
    stale_block_count: Decimal
    source_family_gap_count: Decimal
    mean_staleness_age_seconds: Decimal
    max_staleness_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketDataStalenessHeatmapReasonCodeCount, ...]
    heatmap_rows: tuple[ResearchMarketDataStalenessHeatmapRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDataStalenessHeatmapReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "cell_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_watch_count",
            "stale_block_count",
            "source_family_gap_count",
            "mean_staleness_age_seconds",
            "max_staleness_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "heatmap_rows", _normalize_rows(self.heatmap_rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchMarketDataStalenessHeatmapConfig,
    ResearchMarketDataStalenessHeatmapDigest,
    ResearchMarketDataStalenessHeatmapInput,
    ResearchMarketDataStalenessHeatmapReasonCodeCount,
    ResearchMarketDataStalenessHeatmapReport,
    ResearchMarketDataStalenessHeatmapRow,
)


def build_research_market_data_staleness_heatmap_report(
    observations: Iterable[ResearchMarketDataStalenessHeatmapInput],
    *,
    config: ResearchMarketDataStalenessHeatmapConfig,
    generated_at: datetime,
) -> ResearchMarketDataStalenessHeatmapReport:
    if type(config) is not ResearchMarketDataStalenessHeatmapConfig:
        raise ValueError("config must be a ResearchMarketDataStalenessHeatmapConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(observations)
    rows = tuple(
        sorted(
            (
                _heatmap_row(
                    row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for row in inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchMarketDataStalenessHeatmapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        cell_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        stale_watch_count=_reason_row_count(rows, "staleness_watch"),
        stale_block_count=_reason_row_count(rows, "staleness_block"),
        source_family_gap_count=_reason_row_count(rows, "source_family_gap_block"),
        mean_staleness_age_seconds=_mean(
            tuple(row.staleness_age_seconds for row in rows),
        ),
        max_staleness_age_seconds=_max_decimal(
            tuple(row.staleness_age_seconds for row in rows),
        ),
        status=_rollup_status(tuple(row.status for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        heatmap_rows=rows,
    )


def research_market_data_staleness_heatmap_digest(
    value: ResearchMarketDataStalenessHeatmapReport,
) -> ResearchMarketDataStalenessHeatmapDigest:
    if type(value) is not ResearchMarketDataStalenessHeatmapReport:
        raise ValueError("value must be a ResearchMarketDataStalenessHeatmapReport")
    _validate_report(value)
    _reject_unsafe_public_payload("report", value)
    return ResearchMarketDataStalenessHeatmapDigest(
        generated_at=value.generated_at,
        config_version=value.config_version,
        cell_count=value.cell_count,
        pass_count=value.pass_count,
        watch_count=value.watch_count,
        block_count=value.block_count,
        status=value.status,
        reason_codes=value.reason_codes,
        reason_code_counts=value.reason_code_counts,
    )


def research_market_data_staleness_heatmap_report_payload(
    value: ResearchMarketDataStalenessHeatmapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchMarketDataStalenessHeatmapReport:
        _validate_report(value)
        _reject_unsafe_public_payload("report", value)
        payload = _json_ready(value)
    elif type(value) is dict:
        _reject_unsafe_public_payload("ResearchMarketDataStalenessHeatmapReport", value)
        _reject_flag_downgrades("ResearchMarketDataStalenessHeatmapReport", value)
        payload = value
    else:
        raise ValueError("value must be a ResearchMarketDataStalenessHeatmapReport")
    if type(payload) is not dict:
        raise ValueError("ResearchMarketDataStalenessHeatmapReport payload must be a dict")
    return dict(payload)


def _heatmap_row(
    row: ResearchMarketDataStalenessHeatmapInput,
    *,
    config: ResearchMarketDataStalenessHeatmapConfig,
    generated_at: datetime,
) -> ResearchMarketDataStalenessHeatmapRow:
    staleness_age_seconds = _source_age_seconds(row.latest_observed_at, generated_at)
    reason_codes = _row_reason_codes(
        row,
        config=config,
        staleness_age_seconds=staleness_age_seconds,
    )
    return ResearchMarketDataStalenessHeatmapRow(
        event_category=row.event_category,
        source_family=row.source_family,
        research_team=row.research_team,
        latest_observed_at=row.latest_observed_at,
        source_family_count=row.source_family_count,
        staleness_age_seconds=staleness_age_seconds,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchMarketDataStalenessHeatmapInput,
    *,
    config: ResearchMarketDataStalenessHeatmapConfig,
    staleness_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes = list(row.reason_codes)
    if row.source_family_count < config.minimum_source_family_count:
        reason_codes.append("source_family_gap_block")
    if staleness_age_seconds >= config.block_age_seconds:
        reason_codes.append("staleness_block")
    elif staleness_age_seconds >= config.watch_age_seconds:
        reason_codes.append("staleness_watch")
    if not _has_status_reason(reason_codes):
        reason_codes.append("freshness_clear")
    return tuple(sorted(reason_codes))


def _has_status_reason(reason_codes: list[str]) -> bool:
    return any(
        reason_code.endswith("_watch") or reason_code.endswith("_block")
        for reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _rollup_reason_codes(
    rows: tuple[ResearchMarketDataStalenessHeatmapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [f"market_data_staleness_heatmap_{status}"]
    row_reason_codes = frozenset(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    for reason_code in (
        "source_family_gap_block",
        "staleness_block",
        "staleness_watch",
    ):
        if reason_code in row_reason_codes:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchMarketDataStalenessHeatmapRow, ...],
) -> tuple[ResearchMarketDataStalenessHeatmapReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketDataStalenessHeatmapReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchMarketDataStalenessHeatmapReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _source_age_seconds(latest_observed_at: datetime, generated_at: datetime) -> Decimal:
    seconds = Decimal(
        str((generated_at - _as_utc("latest_observed_at", latest_observed_at)).total_seconds()),
    )
    age_seconds = _quantize(seconds)
    if age_seconds < ZERO:
        raise ValueError("latest_observed_at must not be after generated_at")
    return age_seconds


def _normalize_inputs(
    observations: Iterable[ResearchMarketDataStalenessHeatmapInput],
) -> tuple[ResearchMarketDataStalenessHeatmapInput, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        rows = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchMarketDataStalenessHeatmapInput:
            raise ValueError(
                "observations must contain ResearchMarketDataStalenessHeatmapInput values",
            )
        _require_hard_flags("input", row)
        row_key = _heatmap_key(row)
        if row_key in seen_keys:
            raise ValueError("observations must not contain duplicate heatmap cells")
        seen_keys.add(row_key)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchMarketDataStalenessHeatmapRow],
) -> tuple[ResearchMarketDataStalenessHeatmapRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("heatmap_rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("heatmap_rows must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for row in values:
        if type(row) is not ResearchMarketDataStalenessHeatmapRow:
            raise ValueError(
                "heatmap_rows must contain ResearchMarketDataStalenessHeatmapRow values",
            )
        _require_hard_flags("row", row)
        row_key = _heatmap_key(row)
        if row_key in seen_keys:
            raise ValueError("heatmap_rows must not contain duplicate heatmap cells")
        seen_keys.add(row_key)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("heatmap_rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchMarketDataStalenessHeatmapReasonCodeCount],
) -> tuple[ResearchMarketDataStalenessHeatmapReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchMarketDataStalenessHeatmapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchMarketDataStalenessHeatmapReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must be sorted by count then reason_code")
    return values


def _row_sort_key(
    row: ResearchMarketDataStalenessHeatmapRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.staleness_age_seconds,
        row.event_category,
        row.source_family,
        row.research_team,
    )


def _heatmap_key(
    row: ResearchMarketDataStalenessHeatmapInput | ResearchMarketDataStalenessHeatmapRow,
) -> tuple[str, str, str]:
    return (row.event_category, row.source_family, row.research_team)


def _status_count(
    rows: tuple[ResearchMarketDataStalenessHeatmapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_row_count(
    rows: tuple[ResearchMarketDataStalenessHeatmapRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _validate_digest(report: ResearchMarketDataStalenessHeatmapDigest) -> None:
    if report.cell_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("cell_count must match status counts")
    if report.status == "pass" and report.cell_count != report.pass_count:
        raise ValueError("status must match counts")
    if report.status == "watch" and report.watch_count <= ZERO:
        raise ValueError("status must match counts")
    if report.status == "block" and report.block_count <= ZERO and report.cell_count > ZERO:
        raise ValueError("status must match counts")
    if report.status != _digest_status_from_counts(report):
        raise ValueError("status must match counts")


def _digest_status_from_counts(
    report: ResearchMarketDataStalenessHeatmapDigest,
) -> str:
    if report.cell_count <= ZERO:
        return "block"
    if report.block_count > ZERO:
        return "block"
    if report.watch_count > ZERO:
        return "watch"
    return "pass"


def _validate_report(report: ResearchMarketDataStalenessHeatmapReport) -> None:
    rows = report.heatmap_rows
    if report.cell_count != _count(len(rows)):
        raise ValueError("cell_count must match heatmap_rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match heatmap_rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match heatmap_rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match heatmap_rows")
    if report.stale_watch_count != _reason_row_count(rows, "staleness_watch"):
        raise ValueError("stale_watch_count must match heatmap_rows")
    if report.stale_block_count != _reason_row_count(rows, "staleness_block"):
        raise ValueError("stale_block_count must match heatmap_rows")
    if report.source_family_gap_count != _reason_row_count(rows, "source_family_gap_block"):
        raise ValueError("source_family_gap_count must match heatmap_rows")
    if report.mean_staleness_age_seconds != _mean(
        tuple(row.staleness_age_seconds for row in rows),
    ):
        raise ValueError("mean_staleness_age_seconds must match heatmap_rows")
    if report.max_staleness_age_seconds != _max_decimal(
        tuple(row.staleness_age_seconds for row in rows),
    ):
        raise ValueError("max_staleness_age_seconds must match heatmap_rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match heatmap_rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match heatmap_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match heatmap_rows")


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload("JSON value", value)
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if isinstance(value, (list, dict, set)):
        raise ValueError("JSON value must come from public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for field_name in PHASE_FLAG_FIELDS:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True for {label}")
        for item in value.values():
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains unsupported dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            if _has_unsafe_fragment(field.name):
                raise ValueError(f"{item_path} has unsafe public field")
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if value.strip() != value or "://" in value or "?" in value:
            raise ValueError(f"{path or label} has unsafe public value")
        if _has_unsafe_fragment(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if isinstance(value, Decimal):
        _require_six_decimal_decimal(path or label, value)
        return
    if isinstance(value, datetime):
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    extra_fragments = (
        "raw_"
        "candidate",
        "market_"
        "id",
        "slug",
        "que"
        "stion",
        "source_"
        "ref",
        "source_"
        "url",
        "source_"
        "text",
        "d"
        "sn",
        "ta"
        "ble",
        "to"
        "ken",
        "wal"
        "let",
        "ord"
        "er",
        "tra"
        "de",
        "pos"
        "ition",
        "bu"
        "y",
        "se"
        "ll",
        "reco"
        "mmend",
        "au"
        "th",
    )
    return any(
        fragment in normalized
        for fragment in (*UNSAFE_SURFACE_FIELD_FRAGMENTS, *extra_fragments)
    )


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_canonical_string("reason_codes", reason_code)
    normalized = tuple(sorted(values))
    if values != normalized:
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _normalize_report_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_canonical_string("reason_codes", reason_code)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    return values


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if "://" in value or "?" in value or _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
