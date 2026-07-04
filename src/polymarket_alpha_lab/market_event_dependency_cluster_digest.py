from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_EVENT_DEPENDENCY_CLUSTER_DIGEST_CONFIG_VERSION = (
    "market-event-dependency-cluster-digest-v0"
)
STATUSES = ("pass", "watch", "blocked")
INPUT_REASON_CODES = ("market_dependency_candidate",)
CLUSTER_REASON_CODES = (
    "category_overlap",
    "exposure_concentration_high",
    "resolution_dependency_overlap",
    "shared_event_key",
    "source_family_overlap",
)
REPORT_REASON_CODES = (
    "dependency_clusters_clear",
    "dependency_clusters_watch",
    "dependency_clusters_blocked",
    "exposure_concentration_high",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DEFAULT_MAX_CLUSTER_EXPOSURE_SHARE = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "pass": Decimal("0"),
    "watch": Decimal("1"),
    "blocked": Decimal("2"),
}


@dataclass(frozen=True)
class MarketEventDependencyClusterDigestConfig:
    config_version: str = DEFAULT_MARKET_EVENT_DEPENDENCY_CLUSTER_DIGEST_CONFIG_VERSION
    max_cluster_exposure_share: Decimal = DEFAULT_MAX_CLUSTER_EXPOSURE_SHARE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_cluster_exposure_share",
            _normalize_ratio(
                "max_cluster_exposure_share",
                self.max_cluster_exposure_share,
            ),
        )
        require_paper_only_flags("MarketEventDependencyClusterDigestConfig", self)


@dataclass(frozen=True)
class MarketEventDependencyInput:
    market_id: str
    event_key: str
    category_id: str
    source_families: tuple[str, ...]
    resolution_dependencies: tuple[str, ...]
    paper_exposure: Decimal
    reason_codes: tuple[str, ...]
    sensitive_reference: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("event_key", self.event_key)
        _require_canonical_string("category_id", self.category_id)
        object.__setattr__(
            self,
            "source_families",
            _normalize_string_tuple("source_families", self.source_families),
        )
        object.__setattr__(
            self,
            "resolution_dependencies",
            _normalize_string_tuple(
                "resolution_dependencies",
                self.resolution_dependencies,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "paper_exposure",
            _normalize_nonnegative_count("paper_exposure", self.paper_exposure),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                INPUT_REASON_CODES,
            ),
        )
        if self.sensitive_reference is not None:
            _require_canonical_string("sensitive_reference", self.sensitive_reference)
        require_paper_only_flags("MarketEventDependencyInput", self)


@dataclass(frozen=True)
class MarketEventDependencyClusterDigestRow:
    cluster_key: str
    market_count: Decimal
    category_overlap_count: Decimal
    source_family_overlap_count: Decimal
    resolution_dependency_count: Decimal
    paper_exposure: Decimal
    exposure_share: Decimal
    status: str
    reason_codes: tuple[str, ...]
    redacted_market_ids: tuple[str, ...]
    redacted_references: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("cluster_key", self.cluster_key)
        for field_name in (
            "market_count",
            "category_overlap_count",
            "source_family_overlap_count",
            "resolution_dependency_count",
            "paper_exposure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "exposure_share",
            _normalize_ratio("exposure_share", self.exposure_share),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                CLUSTER_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "redacted_market_ids",
            _normalize_redacted_values("redacted_market_ids", self.redacted_market_ids),
        )
        object.__setattr__(
            self,
            "redacted_references",
            _normalize_redacted_values("redacted_references", self.redacted_references),
        )
        _validate_cluster_row(self)
        reject_unsafe_surface_fields("market event dependency cluster row", self)
        require_paper_only_flags("MarketEventDependencyClusterDigestRow", self)


@dataclass(frozen=True)
class MarketEventDependencyClusterDigestReport:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    cluster_count: Decimal
    dependency_cluster_count: Decimal
    total_paper_exposure: Decimal
    max_cluster_exposure_share: Decimal
    status: str
    reason_codes: tuple[str, ...]
    cluster_rows: tuple[MarketEventDependencyClusterDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "cluster_count",
            "dependency_cluster_count",
            "total_paper_exposure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_cluster_exposure_share",
            _normalize_ratio(
                "max_cluster_exposure_share",
                self.max_cluster_exposure_share,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "cluster_rows",
            _normalize_cluster_rows(self.cluster_rows),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("market event dependency cluster report", self)
        require_paper_only_flags("MarketEventDependencyClusterDigestReport", self)


def build_market_event_dependency_cluster_digest(
    inputs: list[MarketEventDependencyInput] | tuple[MarketEventDependencyInput, ...],
    *,
    config: MarketEventDependencyClusterDigestConfig,
    generated_at: datetime,
) -> MarketEventDependencyClusterDigestReport:
    if type(config) is not MarketEventDependencyClusterDigestConfig:
        raise ValueError("config must be a MarketEventDependencyClusterDigestConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_inputs(inputs)
    total_paper_exposure = _sum_inputs(rows)
    cluster_rows = tuple(
        sorted(
            (
                _cluster_row(
                    cluster_key=cluster_key,
                    rows=clustered_rows,
                    total_paper_exposure=total_paper_exposure,
                    max_cluster_exposure_share=config.max_cluster_exposure_share,
                )
                for cluster_key, clustered_rows in _event_groups(rows)
            ),
            key=_cluster_row_sort_key,
        ),
    )
    return MarketEventDependencyClusterDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_count(len(rows)),
        cluster_count=_count(len(cluster_rows)),
        dependency_cluster_count=_count(
            sum(1 for row in cluster_rows if _is_dependency_cluster(row)),
        ),
        total_paper_exposure=total_paper_exposure,
        max_cluster_exposure_share=_max_exposure_share(cluster_rows),
        status=_report_status(cluster_rows),
        reason_codes=_report_reason_codes(cluster_rows),
        cluster_rows=cluster_rows,
    )


def market_event_dependency_cluster_digest_payload(
    report: MarketEventDependencyClusterDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketEventDependencyClusterDigestReport:
        raise ValueError("report must be a MarketEventDependencyClusterDigestReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("market event dependency cluster report", report)
    return json_ready_no_floats(report)


def _normalize_inputs(
    inputs: list[MarketEventDependencyInput] | tuple[MarketEventDependencyInput, ...],
) -> tuple[MarketEventDependencyInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketEventDependencyInput:
            raise ValueError("inputs must contain MarketEventDependencyInput values")
        require_paper_only_flags("input", row)
        if row.market_id in seen:
            raise ValueError("inputs must not contain duplicate market_id values")
        seen.add(row.market_id)
    return rows


def _event_groups(
    rows: tuple[MarketEventDependencyInput, ...],
) -> tuple[tuple[str, tuple[MarketEventDependencyInput, ...]], ...]:
    event_keys = tuple(sorted({row.event_key for row in rows}))
    return tuple(
        (
            f"event:{event_key}",
            tuple(row for row in rows if row.event_key == event_key),
        )
        for event_key in event_keys
    )


def _cluster_row(
    *,
    cluster_key: str,
    rows: tuple[MarketEventDependencyInput, ...],
    total_paper_exposure: Decimal,
    max_cluster_exposure_share: Decimal,
) -> MarketEventDependencyClusterDigestRow:
    paper_exposure = _sum_inputs(rows)
    exposure_share = _safe_ratio(paper_exposure, total_paper_exposure)
    reason_codes = _cluster_reason_codes(
        rows,
        exposure_share=exposure_share,
        max_cluster_exposure_share=max_cluster_exposure_share,
    )
    return MarketEventDependencyClusterDigestRow(
        cluster_key=cluster_key,
        market_count=_count(len(rows)),
        category_overlap_count=_shared_value_count(tuple(row.category_id for row in rows)),
        source_family_overlap_count=_overlap_count(
            tuple(row.source_families for row in rows),
        ),
        resolution_dependency_count=_overlap_count(
            tuple(row.resolution_dependencies for row in rows),
        ),
        paper_exposure=paper_exposure,
        exposure_share=exposure_share,
        status=_cluster_status(reason_codes),
        reason_codes=reason_codes,
        redacted_market_ids=_redacted_market_ids(rows),
        redacted_references=tuple("redacted:reference" for _row in rows),
    )


def _cluster_reason_codes(
    rows: tuple[MarketEventDependencyInput, ...],
    *,
    exposure_share: Decimal,
    max_cluster_exposure_share: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if len(rows) > 1:
        codes.append("shared_event_key")
    if _shared_value_count(tuple(row.category_id for row in rows)) > ZERO_COUNT:
        codes.append("category_overlap")
    if _overlap_count(tuple(row.source_families for row in rows)) > ZERO_COUNT:
        codes.append("source_family_overlap")
    if _overlap_count(tuple(row.resolution_dependencies for row in rows)) > ZERO_COUNT:
        codes.append("resolution_dependency_overlap")
    if exposure_share > max_cluster_exposure_share and len(rows) > 1:
        codes.append("exposure_concentration_high")
    if not codes:
        codes.append("shared_event_key")
    return tuple(code for code in CLUSTER_REASON_CODES if code in codes)


def _cluster_status(reason_codes: tuple[str, ...]) -> str:
    if "exposure_concentration_high" in reason_codes:
        return "blocked"
    if (
        "resolution_dependency_overlap" in reason_codes
        or "source_family_overlap" in reason_codes
        or "category_overlap" in reason_codes
    ):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[MarketEventDependencyClusterDigestRow, ...],
) -> tuple[str, ...]:
    if not rows or not any(_is_dependency_cluster(row) for row in rows):
        return ("dependency_clusters_clear",)
    codes: list[str] = []
    status = _report_status(rows)
    if status == "blocked":
        codes.append("dependency_clusters_blocked")
    elif status == "watch":
        codes.append("dependency_clusters_watch")
    if any("exposure_concentration_high" in row.reason_codes for row in rows):
        codes.append("exposure_concentration_high")
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _report_status(rows: tuple[MarketEventDependencyClusterDigestRow, ...]) -> str:
    statuses = tuple(row.status for row in rows if _is_dependency_cluster(row))
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _is_dependency_cluster(row: MarketEventDependencyClusterDigestRow) -> bool:
    return row.market_count > Decimal("1")


def _cluster_row_sort_key(
    row: MarketEventDependencyClusterDigestRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.paper_exposure,
        -row.market_count,
        -row.exposure_share,
        row.cluster_key,
    )


def _redacted_market_ids(
    rows: tuple[MarketEventDependencyInput, ...],
) -> tuple[str, ...]:
    sorted_ids = tuple(sorted(row.market_id for row in rows))
    return tuple(
        f"redacted:market:{index:06d}"
        for index, _market_id in enumerate(sorted_ids, start=1)
    )


def _shared_value_count(values: tuple[str, ...]) -> Decimal:
    if len(values) < 2:
        return ZERO_COUNT
    return _count(sum(1 for value in set(values) if values.count(value) > 1))


def _overlap_count(values: tuple[tuple[str, ...], ...]) -> Decimal:
    if len(values) < 2:
        return ZERO_COUNT
    observed: dict[str, int] = {}
    for row_values in values:
        for value in set(row_values):
            observed[value] = observed.get(value, 0) + 1
    return _count(sum(1 for count in observed.values() if count > 1))


def _sum_inputs(rows: tuple[MarketEventDependencyInput, ...]) -> Decimal:
    return _normalize_nonnegative_count(
        "paper_exposure",
        sum((row.paper_exposure for row in rows), ZERO_COUNT),
    )


def _sum_rows(
    rows: tuple[MarketEventDependencyClusterDigestRow, ...],
    field_name: str,
) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _max_exposure_share(
    rows: tuple[MarketEventDependencyClusterDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return _normalize_ratio("max_cluster_exposure_share", max(row.exposure_share for row in rows))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("ratio", numerator / denominator)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _validate_cluster_row(row: MarketEventDependencyClusterDigestRow) -> None:
    if row.market_count == ZERO_COUNT:
        raise ValueError("market_count must be positive")
    if row.market_count == Decimal("1") and row.status != "pass":
        raise ValueError("single market clusters must pass")
    if row.status != _cluster_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if len(row.redacted_market_ids) != int(row.market_count):
        raise ValueError("redacted_market_ids must match market_count")
    if len(row.redacted_references) != int(row.market_count):
        raise ValueError("redacted_references must match market_count")


def _validate_report(report: MarketEventDependencyClusterDigestReport) -> None:
    if report.market_count != _sum_rows(report.cluster_rows, "market_count"):
        raise ValueError("market_count must match cluster_rows")
    if report.cluster_count != _count(len(report.cluster_rows)):
        raise ValueError("cluster_count must match cluster_rows")
    if report.dependency_cluster_count != _count(
        sum(1 for row in report.cluster_rows if _is_dependency_cluster(row)),
    ):
        raise ValueError("dependency_cluster_count must match cluster_rows")
    if report.total_paper_exposure != _sum_rows(report.cluster_rows, "paper_exposure"):
        raise ValueError("total_paper_exposure must match cluster_rows")
    if report.max_cluster_exposure_share != _max_exposure_share(report.cluster_rows):
        raise ValueError("max_cluster_exposure_share must match cluster_rows")
    if report.status != _report_status(report.cluster_rows):
        raise ValueError("status must match cluster_rows")
    if report.reason_codes != _report_reason_codes(report.cluster_rows):
        raise ValueError("reason_codes must match cluster_rows")
    if report.cluster_rows != tuple(sorted(report.cluster_rows, key=_cluster_row_sort_key)):
        raise ValueError("cluster_rows must use deterministic sequence")


def _normalize_cluster_rows(
    value: object,
) -> tuple[MarketEventDependencyClusterDigestRow, ...]:
    if type(value) is not tuple:
        raise ValueError("cluster_rows must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketEventDependencyClusterDigestRow:
            raise ValueError(
                "cluster_rows must contain MarketEventDependencyClusterDigestRow values",
            )
        require_paper_only_flags("cluster row", row)
        if row.cluster_key in seen:
            raise ValueError("cluster_rows must contain unique cluster_key values")
        seen.add(row.cluster_key)
    return rows


def _normalize_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    rows = tuple(value)
    if not allow_empty and not rows:
        raise ValueError(f"{field_name} must not be empty")
    for row in rows:
        _require_canonical_string(field_name, row)
    if len(set(rows)) != len(rows):
        raise ValueError(f"{field_name} must be unique")
    return rows


def _normalize_redacted_values(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError(f"{field_name} must not be empty")
    for row in rows:
        _require_canonical_string(field_name, row)
        if not row.startswith("redacted:"):
            raise ValueError(f"{field_name} must contain redacted values")
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    rows = _normalize_string_tuple(field_name, value)
    for row in rows:
        _require_member(field_name, row, allowed)
    if tuple(code for code in allowed if code in rows) != rows:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return rows


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "DEFAULT_MARKET_EVENT_DEPENDENCY_CLUSTER_DIGEST_CONFIG_VERSION",
    "MarketEventDependencyClusterDigestConfig",
    "MarketEventDependencyInput",
    "MarketEventDependencyClusterDigestReport",
    "MarketEventDependencyClusterDigestRow",
    "build_market_event_dependency_cluster_digest",
    "market_event_dependency_cluster_digest_payload",
)
