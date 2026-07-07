"""Paper-only event cluster exposure summary."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


DEFAULT_CONFIG_VERSION = "market-event-cluster-exposure-report-v1"

SPARSE_STATUS = "sparse"
WATCH_STATUS = "watch"
CONCENTRATED_STATUS = "concentrated"
CONCENTRATION_STATUSES = (SPARSE_STATUS, WATCH_STATUS, CONCENTRATED_STATUS)

MISSING_ROWS_REASON = "missing_event_cluster_rows"
SPARSE_REASON = "cluster_exposure_distribution_sparse"
EXPOSURE_WATCH_REASON = "cluster_exposure_share_watch"
UNRESOLVED_WATCH_REASON = "cluster_unresolved_share_watch"
EXPOSURE_CONCENTRATED_REASON = "cluster_exposure_share_concentrated"
UNRESOLVED_CONCENTRATED_REASON = "cluster_unresolved_share_concentrated"
REASON_CODES = (
    MISSING_ROWS_REASON,
    SPARSE_REASON,
    EXPOSURE_WATCH_REASON,
    UNRESOLVED_WATCH_REASON,
    EXPOSURE_CONCENTRATED_REASON,
    UNRESOLVED_CONCENTRATED_REASON,
)

MONEY_QUANT = Decimal("0.0000")
RATIO_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
DECIMAL_ZERO = Decimal("0")
DECIMAL_ONE = Decimal("1.000000")
UNSAFE_PUBLIC_PAYLOAD_KEY_MARKERS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
)


@dataclass(frozen=True)
class MarketEventClusterExposureReportConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_exposure_share_threshold: Decimal = Decimal("0.400000")
    concentrated_exposure_share_threshold: Decimal = Decimal("0.600000")
    watch_unresolved_share_threshold: Decimal = Decimal("0.400000")
    concentrated_unresolved_share_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_exposure_share_threshold",
            "concentrated_exposure_share_threshold",
            "watch_unresolved_share_threshold",
            "concentrated_unresolved_share_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if (
            self.watch_exposure_share_threshold
            > self.concentrated_exposure_share_threshold
        ):
            raise ValueError(
                "watch_exposure_share_threshold must be <= concentrated_exposure_share_threshold",
            )
        if (
            self.watch_unresolved_share_threshold
            > self.concentrated_unresolved_share_threshold
        ):
            raise ValueError(
                "watch_unresolved_share_threshold must be <= concentrated_unresolved_share_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketEventClusterExposureSourceRow:
    cluster_id: str
    team: str
    category: str
    paper_exposure: Decimal
    unresolved_count: Decimal
    expected_resolution_window_start_at: datetime
    expected_resolution_window_end_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("cluster_id", "team", "category"):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_unsafe_public_payload_text(getattr(self, field_name))
        object.__setattr__(
            self,
            "paper_exposure",
            _normalize_nonnegative_money("paper_exposure", self.paper_exposure),
        )
        object.__setattr__(
            self,
            "unresolved_count",
            _normalize_nonnegative_integral_decimal(
                "unresolved_count",
                self.unresolved_count,
            ),
        )
        object.__setattr__(
            self,
            "expected_resolution_window_start_at",
            _as_utc(
                "expected_resolution_window_start_at",
                self.expected_resolution_window_start_at,
            ),
        )
        object.__setattr__(
            self,
            "expected_resolution_window_end_at",
            _as_utc(
                "expected_resolution_window_end_at",
                self.expected_resolution_window_end_at,
            ),
        )
        if (
            self.expected_resolution_window_start_at
            > self.expected_resolution_window_end_at
        ):
            raise ValueError("expected resolution window start must be <= end")
        _require_hard_flags("source row", self)


@dataclass(frozen=True)
class MarketEventClusterExposureReportRow:
    cluster_id: str
    team: str
    category: str
    paper_exposure: Decimal
    unresolved_count: Decimal
    exposure_share: Decimal
    unresolved_share: Decimal
    expected_resolution_window_start_at: datetime
    expected_resolution_window_end_at: datetime
    concentration_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("cluster_id", "team", "category"):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_unsafe_public_payload_text(getattr(self, field_name))
        object.__setattr__(
            self,
            "paper_exposure",
            _normalize_nonnegative_money("paper_exposure", self.paper_exposure),
        )
        object.__setattr__(
            self,
            "unresolved_count",
            _normalize_nonnegative_integral_decimal(
                "unresolved_count",
                self.unresolved_count,
            ),
        )
        object.__setattr__(
            self,
            "exposure_share",
            _normalize_ratio("exposure_share", self.exposure_share),
        )
        object.__setattr__(
            self,
            "unresolved_share",
            _normalize_ratio("unresolved_share", self.unresolved_share),
        )
        object.__setattr__(
            self,
            "expected_resolution_window_start_at",
            _as_utc(
                "expected_resolution_window_start_at",
                self.expected_resolution_window_start_at,
            ),
        )
        object.__setattr__(
            self,
            "expected_resolution_window_end_at",
            _as_utc(
                "expected_resolution_window_end_at",
                self.expected_resolution_window_end_at,
            ),
        )
        if (
            self.expected_resolution_window_start_at
            > self.expected_resolution_window_end_at
        ):
            raise ValueError("expected resolution window start must be <= end")
        _require_concentration_status(
            "concentration_status",
            self.concentration_status,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("report row", self)


@dataclass(frozen=True)
class MarketEventClusterExposureReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    cluster_count: Decimal
    total_paper_exposure: Decimal
    total_unresolved_count: Decimal
    top_cluster_id: str | None
    top_cluster_exposure_share: Decimal
    top_cluster_unresolved_share: Decimal
    concentration_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    rows: tuple[MarketEventClusterExposureReportRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("source_row_count", "cluster_count", "total_unresolved_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "total_paper_exposure",
            _normalize_nonnegative_money(
                "total_paper_exposure",
                self.total_paper_exposure,
            ),
        )
        if self.top_cluster_id is not None:
            _require_canonical_string("top_cluster_id", self.top_cluster_id)
            _reject_unsafe_public_payload_text(self.top_cluster_id)
        object.__setattr__(
            self,
            "top_cluster_exposure_share",
            _normalize_ratio(
                "top_cluster_exposure_share",
                self.top_cluster_exposure_share,
            ),
        )
        object.__setattr__(
            self,
            "top_cluster_unresolved_share",
            _normalize_ratio(
                "top_cluster_unresolved_share",
                self.top_cluster_unresolved_share,
            ),
        )
        _require_concentration_status(
            "concentration_status",
            self.concentration_status,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_validation_digest("derived_validation_digest", self.derived_validation_digest)
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)


def build_market_event_cluster_exposure_report(
    rows: list[MarketEventClusterExposureSourceRow]
    | tuple[MarketEventClusterExposureSourceRow, ...],
    *,
    config: MarketEventClusterExposureReportConfig,
    generated_at: datetime,
) -> MarketEventClusterExposureReport:
    if type(config) is not MarketEventClusterExposureReportConfig:
        raise ValueError("config must be a MarketEventClusterExposureReportConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_source_rows(rows)
    report_rows = _build_report_rows(source_rows, config=config)
    top_row = report_rows[0] if report_rows else None
    total_exposure = _sum_money(row.paper_exposure for row in source_rows)
    total_unresolved = _sum_count(row.unresolved_count for row in source_rows)
    top_exposure_share = (
        top_row.exposure_share if top_row is not None else _normalize_ratio_zero()
    )
    top_unresolved_share = (
        top_row.unresolved_share if top_row is not None else _normalize_ratio_zero()
    )
    status = _overall_status(report_rows)
    reason_codes = _report_reason_codes(report_rows, status)

    return MarketEventClusterExposureReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=Decimal(len(source_rows)),
        cluster_count=Decimal(len(report_rows)),
        total_paper_exposure=total_exposure,
        total_unresolved_count=total_unresolved,
        top_cluster_id=top_row.cluster_id if top_row is not None else None,
        top_cluster_exposure_share=top_exposure_share,
        top_cluster_unresolved_share=top_unresolved_share,
        concentration_status=status,
        reason_codes=reason_codes,
        derived_validation_digest=_derived_validation_digest_for_report_values(
            {
                "generated_at": generated_at_utc,
                "config_version": config.config_version,
                "source_row_count": Decimal(len(source_rows)),
                "cluster_count": Decimal(len(report_rows)),
                "total_paper_exposure": total_exposure,
                "total_unresolved_count": total_unresolved,
                "top_cluster_id": top_row.cluster_id if top_row is not None else None,
                "top_cluster_exposure_share": top_exposure_share,
                "top_cluster_unresolved_share": top_unresolved_share,
                "concentration_status": status,
                "reason_codes": reason_codes,
                "rows": tuple(asdict(row) for row in report_rows),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
        rows=report_rows,
    )


def market_event_cluster_exposure_report_payload(
    report: MarketEventClusterExposureReport,
) -> dict[str, Any]:
    if type(report) is not MarketEventClusterExposureReport:
        raise ValueError("report must be a MarketEventClusterExposureReport")
    _require_hard_flags("report", report)
    return _json_ready(asdict(report))


def _normalize_source_rows(
    value: (
        list[MarketEventClusterExposureSourceRow]
        | tuple[MarketEventClusterExposureSourceRow, ...]
    ),
) -> tuple[MarketEventClusterExposureSourceRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketEventClusterExposureSourceRow:
            raise ValueError(
                "rows must contain MarketEventClusterExposureSourceRow values",
            )
        _require_hard_flags("source row", row)
    return rows


def _build_report_rows(
    source_rows: tuple[MarketEventClusterExposureSourceRow, ...],
    *,
    config: MarketEventClusterExposureReportConfig,
) -> tuple[MarketEventClusterExposureReportRow, ...]:
    grouped: dict[tuple[str, str, str], list[MarketEventClusterExposureSourceRow]] = defaultdict(list)
    for row in source_rows:
        grouped[(row.cluster_id, row.team, row.category)].append(row)

    total_exposure = _sum_money(row.paper_exposure for row in source_rows)
    total_unresolved = _sum_count(row.unresolved_count for row in source_rows)
    rows = tuple(
        _build_report_row(
            cluster_id=cluster_id,
            team=team,
            category=category,
            source_rows=tuple(cluster_rows),
            total_exposure=total_exposure,
            total_unresolved=total_unresolved,
            config=config,
        )
        for (cluster_id, team, category), cluster_rows in grouped.items()
    )
    return tuple(sorted(rows, key=_report_row_sort_key))


def _build_report_row(
    *,
    cluster_id: str,
    team: str,
    category: str,
    source_rows: tuple[MarketEventClusterExposureSourceRow, ...],
    total_exposure: Decimal,
    total_unresolved: Decimal,
    config: MarketEventClusterExposureReportConfig,
) -> MarketEventClusterExposureReportRow:
    paper_exposure = _sum_money(row.paper_exposure for row in source_rows)
    unresolved_count = _sum_count(row.unresolved_count for row in source_rows)
    exposure_share = _share(paper_exposure, total_exposure)
    unresolved_share = _share(unresolved_count, total_unresolved)
    status = _row_status(
        exposure_share=exposure_share,
        unresolved_share=unresolved_share,
        config=config,
    )
    return MarketEventClusterExposureReportRow(
        cluster_id=cluster_id,
        team=team,
        category=category,
        paper_exposure=paper_exposure,
        unresolved_count=unresolved_count,
        exposure_share=exposure_share,
        unresolved_share=unresolved_share,
        expected_resolution_window_start_at=min(
            row.expected_resolution_window_start_at for row in source_rows
        ),
        expected_resolution_window_end_at=max(
            row.expected_resolution_window_end_at for row in source_rows
        ),
        concentration_status=status,
        reason_codes=_row_reason_codes(
            exposure_share=exposure_share,
            unresolved_share=unresolved_share,
            status=status,
            config=config,
        ),
    )


def _report_row_sort_key(
    row: MarketEventClusterExposureReportRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        -row.paper_exposure,
        -row.unresolved_count,
        row.cluster_id,
        row.team,
        row.category,
    )


def _row_status(
    *,
    exposure_share: Decimal,
    unresolved_share: Decimal,
    config: MarketEventClusterExposureReportConfig,
) -> str:
    if (
        exposure_share >= config.concentrated_exposure_share_threshold
        or unresolved_share >= config.concentrated_unresolved_share_threshold
    ):
        return CONCENTRATED_STATUS
    if (
        exposure_share >= config.watch_exposure_share_threshold
        or unresolved_share >= config.watch_unresolved_share_threshold
    ):
        return WATCH_STATUS
    return SPARSE_STATUS


def _overall_status(rows: tuple[MarketEventClusterExposureReportRow, ...]) -> str:
    if any(row.concentration_status == CONCENTRATED_STATUS for row in rows):
        return CONCENTRATED_STATUS
    if any(row.concentration_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return SPARSE_STATUS


def _row_reason_codes(
    *,
    exposure_share: Decimal,
    unresolved_share: Decimal,
    status: str,
    config: MarketEventClusterExposureReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if status == CONCENTRATED_STATUS:
        if exposure_share >= config.concentrated_exposure_share_threshold:
            reasons.append(EXPOSURE_CONCENTRATED_REASON)
        if unresolved_share >= config.concentrated_unresolved_share_threshold:
            reasons.append(UNRESOLVED_CONCENTRATED_REASON)
        return tuple(reasons)
    if status == WATCH_STATUS:
        if exposure_share >= config.watch_exposure_share_threshold:
            reasons.append(EXPOSURE_WATCH_REASON)
        if unresolved_share >= config.watch_unresolved_share_threshold:
            reasons.append(UNRESOLVED_WATCH_REASON)
        return tuple(reasons)
    return (SPARSE_REASON,)


def _report_reason_codes(
    rows: tuple[MarketEventClusterExposureReportRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_ROWS_REASON,)
    if status == SPARSE_STATUS:
        return (SPARSE_REASON,)
    reasons: list[str] = []
    for row in rows:
        if row.concentration_status == status:
            for reason_code in row.reason_codes:
                if reason_code not in reasons:
                    reasons.append(reason_code)
    if not reasons:
        raise ValueError("status must match at least one report row")
    return tuple(reasons)


def _validate_report(report: MarketEventClusterExposureReport) -> None:
    if report.cluster_count != Decimal(len(report.rows)):
        raise ValueError("cluster_count must match rows")
    row_exposure_total = _sum_money(row.paper_exposure for row in report.rows)
    if report.total_paper_exposure != row_exposure_total:
        raise ValueError("row exposure must match total_paper_exposure")
    row_unresolved_total = _sum_count(row.unresolved_count for row in report.rows)
    if report.total_unresolved_count != row_unresolved_total:
        raise ValueError("row unresolved counts must match total_unresolved_count")
    if tuple(sorted(report.rows, key=_report_row_sort_key)) != report.rows:
        raise ValueError("report rows must be sorted")
    if report.source_row_count < report.cluster_count:
        raise ValueError("source_row_count must be >= cluster_count")
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    if not report.rows:
        _validate_empty_report(report)
        return
    _validate_nonempty_report(report)


def _validate_empty_report(report: MarketEventClusterExposureReport) -> None:
    if report.source_row_count != DECIMAL_ZERO:
        raise ValueError("source_row_count must be zero without rows")
    if report.total_paper_exposure != DECIMAL_ZERO.quantize(MONEY_QUANT):
        raise ValueError("total_paper_exposure must be zero without rows")
    if report.total_unresolved_count != DECIMAL_ZERO:
        raise ValueError("total_unresolved_count must be zero without rows")
    if report.top_cluster_id is not None:
        raise ValueError("top_cluster_id must be absent without rows")
    if report.top_cluster_exposure_share != DECIMAL_ZERO.quantize(RATIO_QUANT):
        raise ValueError("top_cluster_exposure_share must be zero without rows")
    if report.top_cluster_unresolved_share != DECIMAL_ZERO.quantize(RATIO_QUANT):
        raise ValueError("top_cluster_unresolved_share must be zero without rows")
    if report.concentration_status != SPARSE_STATUS:
        raise ValueError("empty report must be sparse")
    if report.reason_codes != (MISSING_ROWS_REASON,):
        raise ValueError("empty report requires missing rows reason")


def _validate_nonempty_report(report: MarketEventClusterExposureReport) -> None:
    top_row = report.rows[0]
    if report.top_cluster_id != top_row.cluster_id:
        raise ValueError("top_cluster_id must match first row")
    if report.top_cluster_exposure_share != top_row.exposure_share:
        raise ValueError("top_cluster_exposure_share must match first row")
    if report.top_cluster_unresolved_share != top_row.unresolved_share:
        raise ValueError("top_cluster_unresolved_share must match first row")
    if report.concentration_status != _overall_status(report.rows):
        raise ValueError("concentration_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows, report.concentration_status):
        raise ValueError("reason_codes must match concentration_status")
    for row in report.rows:
        if row.exposure_share != _share(row.paper_exposure, report.total_paper_exposure):
            raise ValueError("row exposure shares must match total exposure")
        if row.unresolved_share != _share(
            row.unresolved_count,
            report.total_unresolved_count,
        ):
            raise ValueError("row unresolved shares must match total unresolved count")


def _normalize_report_rows(value: object) -> tuple[MarketEventClusterExposureReportRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketEventClusterExposureReportRow:
            raise ValueError(
                "rows must contain MarketEventClusterExposureReportRow values",
            )
        _require_hard_flags("report row", row)
    if len({(row.cluster_id, row.team, row.category) for row in rows}) != len(rows):
        raise ValueError("rows must be unique by cluster, team, and category")
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _derived_validation_digest(report: MarketEventClusterExposureReport) -> str:
    return _derived_validation_digest_for_report_values(asdict(report))


def _derived_validation_digest_for_report_values(values: dict[str, Any]) -> str:
    payload = {
        key: item for key, item in values.items() if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        _json_ready(payload),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_validation_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _share(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == DECIMAL_ZERO:
        return _normalize_ratio_zero()
    return (numerator / denominator).quantize(RATIO_QUANT)


def _sum_money(values: object) -> Decimal:
    return sum(values, DECIMAL_ZERO).quantize(MONEY_QUANT)  # type: ignore[arg-type]


def _sum_count(values: object) -> Decimal:
    return sum(values, DECIMAL_ZERO).quantize(COUNT_QUANT)  # type: ignore[arg-type]


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_money(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(MONEY_QUANT)


def _normalize_nonnegative_money(field_name: str, value: object) -> Decimal:
    quantized = _normalize_money(field_name, value)
    if quantized < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    quantized = _normalize_integral_decimal(field_name, value)
    if quantized < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(RATIO_QUANT)
    if quantized < DECIMAL_ZERO or quantized > DECIMAL_ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _normalize_ratio_zero() -> Decimal:
    return DECIMAL_ZERO.quantize(RATIO_QUANT)


def _require_concentration_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in CONCENTRATION_STATUSES:
        raise ValueError(f"{field_name} must be one of sparse, watch, concentrated")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known cluster exposure reasons")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload_key(key: str) -> None:
    _reject_unsafe_public_payload_text(key)


def _reject_unsafe_public_payload_text(value: str) -> None:
    lowered = value.lower()
    tokens = tuple(lowered.split("_"))
    if any(
        lowered == marker or marker in tokens
        for marker in UNSAFE_PUBLIC_PAYLOAD_KEY_MARKERS
    ):
        raise ValueError(f"unsafe public payload value: {value}")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, str):
        _reject_unsafe_public_payload_text(value)
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_payload_key(key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "MarketEventClusterExposureReportConfig",
    "MarketEventClusterExposureSourceRow",
    "MarketEventClusterExposureReportRow",
    "MarketEventClusterExposureReport",
    "build_market_event_cluster_exposure_report",
    "market_event_cluster_exposure_report_payload",
)
