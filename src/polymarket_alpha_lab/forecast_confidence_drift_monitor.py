"""Read-only monitor for paper forecast confidence drift."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_FORECAST_CONFIDENCE_DRIFT_MONITOR_CONFIG_VERSION = (
    "forecast-confidence-drift-monitor-v0"
)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
ROW_STATUSES = (
    "insufficient_forecast_history",
    "confidence_stable",
    "confidence_drift_watch",
    "confidence_drift_block",
)
REPORT_STATUSES = (
    "empty_forecast_set",
    "insufficient_forecast_history",
    "confidence_stable",
    "confidence_drift_watch",
    "confidence_drift_block",
)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
HARD_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
UNSAFE_LIVE_SURFACE_FRAGMENTS = frozenset(
    (
        "live",
        "trading",
        "trade",
        "auth",
        "token",
        "secret",
        "private_key",
        "wallet",
        "account",
        "balance",
        "order",
        "cancel",
        "replace",
        "sign",
        "network",
        "http",
        "url",
        "database",
        "dsn",
        "persist",
        "path",
        "sqlite",
        "psycopg",
        "redis",
        "web3",
    ),
)


@dataclass(frozen=True)
class ForecastConfidenceDriftMonitorConfig:
    config_version: str = DEFAULT_FORECAST_CONFIDENCE_DRIFT_MONITOR_CONFIG_VERSION
    min_forecast_count: Decimal = Decimal("4")
    min_baseline_count: Decimal = Decimal("2")
    min_latest_count: Decimal = Decimal("2")
    drift_watch_threshold: Decimal = Decimal("0.100000")
    drift_block_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_forecast_count",
            "min_baseline_count",
            "min_latest_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "drift_watch_threshold",
            _normalize_probability_delta(
                "drift_watch_threshold",
                self.drift_watch_threshold,
            ),
        )
        object.__setattr__(
            self,
            "drift_block_threshold",
            _normalize_probability_delta(
                "drift_block_threshold",
                self.drift_block_threshold,
            ),
        )
        if self.drift_block_threshold < self.drift_watch_threshold:
            raise ValueError("drift_block_threshold must be at least drift_watch_threshold")
        _require_hard_flags("ForecastConfidenceDriftMonitorConfig", self)


@dataclass(frozen=True)
class ForecastConfidenceDriftForecast:
    forecast_id: str
    condition_id: str
    team_id: str
    source_id: str
    confidence: Decimal
    generated_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("forecast_id", self.forecast_id)
        _require_canonical_string("condition_id", self.condition_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("source_id", self.source_id)
        object.__setattr__(
            self,
            "confidence",
            _normalize_probability("confidence", self.confidence),
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_hard_flags("ForecastConfidenceDriftForecast", self)


@dataclass(frozen=True)
class ForecastConfidenceDriftRow:
    condition_id: str
    forecast_count: Decimal
    baseline_count: Decimal
    latest_count: Decimal
    baseline_mean_confidence: Decimal | None
    latest_mean_confidence: Decimal | None
    confidence_delta: Decimal | None
    absolute_confidence_delta: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        object.__setattr__(
            self,
            "forecast_count",
            _normalize_positive_count_decimal("forecast_count", self.forecast_count),
        )
        for field_name in ("baseline_count", "latest_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "baseline_mean_confidence",
            "latest_mean_confidence",
            "absolute_confidence_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_delta",
            _normalize_optional_signed_probability_delta(
                "confidence_delta",
                self.confidence_delta,
            ),
        )
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("ForecastConfidenceDriftRow", self)
        _validate_row(self)
        object.__setattr__(
            self,
            DERIVED_VALIDATION_DIGEST_FIELD,
            _finalize_digest(self, self.derived_validation_digest),
        )


@dataclass(frozen=True)
class ForecastConfidenceDriftMonitorReport:
    generated_at: datetime
    config_version: str
    forecast_count: Decimal
    row_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_absolute_confidence_delta: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ForecastConfidenceDriftRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("forecast_count", "row_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_absolute_confidence_delta",
            _normalize_optional_probability(
                "max_absolute_confidence_delta",
                self.max_absolute_confidence_delta,
            ),
        )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("ForecastConfidenceDriftMonitorReport", self)
        _validate_report(self)
        object.__setattr__(
            self,
            DERIVED_VALIDATION_DIGEST_FIELD,
            _finalize_digest(self, self.derived_validation_digest),
        )


def build_forecast_confidence_drift_monitor_report(
    forecasts: Iterable[ForecastConfidenceDriftForecast],
    *,
    config: ForecastConfidenceDriftMonitorConfig,
    generated_at: datetime,
) -> ForecastConfidenceDriftMonitorReport:
    if isinstance(forecasts, (str, bytes)):
        raise ValueError("forecasts must be an iterable")
    if type(config) is not ForecastConfidenceDriftMonitorConfig:
        raise ValueError("config must be a ForecastConfidenceDriftMonitorConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("ForecastConfidenceDriftMonitorConfig", config)

    try:
        forecast_items = tuple(forecasts)
    except TypeError as exc:
        raise ValueError("forecasts must be an iterable") from exc
    for forecast in forecast_items:
        if type(forecast) is not ForecastConfidenceDriftForecast:
            raise ValueError(
                "forecasts must contain ForecastConfidenceDriftForecast values",
            )
        try:
            _require_hard_flags("ForecastConfidenceDriftForecast", forecast)
        except ValueError as exc:
            raise ValueError("forecasts must be paper_only report_only readonly") from exc

    rows = _build_rows(forecast_items, config)
    status = _report_status(rows)
    return ForecastConfidenceDriftMonitorReport(
        generated_at=generated_at,
        config_version=config.config_version,
        forecast_count=_count_decimal(len(forecast_items)),
        row_count=_count_decimal(len(rows)),
        watch_count=_count_decimal(
            sum(1 for row in rows if row.status == "confidence_drift_watch"),
        ),
        block_count=_count_decimal(
            sum(1 for row in rows if row.status == "confidence_drift_block"),
        ),
        max_absolute_confidence_delta=_max_absolute_confidence_delta(rows),
        status=status,
        reason_codes=_report_reason_codes(status),
        rows=rows,
    )


def forecast_confidence_drift_monitor_payload(
    report: ForecastConfidenceDriftMonitorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ForecastConfidenceDriftMonitorReport:
        _require_hard_flags("ForecastConfidenceDriftMonitorReport", report)
        _reject_unsafe_live_surface("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_live_surface("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ForecastConfidenceDriftMonitorReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_live_surface("payload", payload)
    _validate_payload_digests(payload)
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


def _build_rows(
    forecasts: tuple[ForecastConfidenceDriftForecast, ...],
    config: ForecastConfidenceDriftMonitorConfig,
) -> tuple[ForecastConfidenceDriftRow, ...]:
    grouped: dict[str, list[ForecastConfidenceDriftForecast]] = {}
    for forecast in forecasts:
        grouped.setdefault(forecast.condition_id, []).append(forecast)

    rows: list[ForecastConfidenceDriftRow] = []
    for condition_id, values in sorted(grouped.items()):
        ordered = tuple(sorted(values, key=lambda item: (item.generated_at, item.forecast_id)))
        midpoint = len(ordered) // 2
        baseline = ordered[:midpoint]
        latest = ordered[midpoint:]
        forecast_count = _count_decimal(len(ordered))
        baseline_count = _count_decimal(len(baseline))
        latest_count = _count_decimal(len(latest))
        if (
            forecast_count < config.min_forecast_count
            or baseline_count < config.min_baseline_count
            or latest_count < config.min_latest_count
        ):
            rows.append(
                ForecastConfidenceDriftRow(
                    condition_id=condition_id,
                    forecast_count=forecast_count,
                    baseline_count=baseline_count,
                    latest_count=latest_count,
                    baseline_mean_confidence=None,
                    latest_mean_confidence=None,
                    confidence_delta=None,
                    absolute_confidence_delta=None,
                    status="insufficient_forecast_history",
                    reason_codes=("insufficient_forecast_history",),
                ),
            )
            continue

        baseline_mean = _mean(tuple(item.confidence for item in baseline))
        latest_mean = _mean(tuple(item.confidence for item in latest))
        confidence_delta = _quantize_ratio(latest_mean - baseline_mean)
        absolute_delta = _quantize_ratio(abs(confidence_delta))
        status, reason_codes = _row_status(
            absolute_delta=absolute_delta,
            config=config,
        )
        rows.append(
            ForecastConfidenceDriftRow(
                condition_id=condition_id,
                forecast_count=forecast_count,
                baseline_count=baseline_count,
                latest_count=latest_count,
                baseline_mean_confidence=baseline_mean,
                latest_mean_confidence=latest_mean,
                confidence_delta=confidence_delta,
                absolute_confidence_delta=absolute_delta,
                status=status,
                reason_codes=reason_codes,
            ),
        )
    return tuple(rows)


def _row_status(
    *,
    absolute_delta: Decimal,
    config: ForecastConfidenceDriftMonitorConfig,
) -> tuple[str, tuple[str, ...]]:
    if absolute_delta >= config.drift_block_threshold:
        return "confidence_drift_block", ("confidence_drift_blocked",)
    if absolute_delta >= config.drift_watch_threshold:
        return "confidence_drift_watch", ("confidence_drift_detected",)
    return "confidence_stable", ("confidence_stable",)


def _report_status(rows: tuple[ForecastConfidenceDriftRow, ...]) -> str:
    if not rows:
        return "empty_forecast_set"
    if any(row.status == "confidence_drift_block" for row in rows):
        return "confidence_drift_block"
    if any(row.status == "confidence_drift_watch" for row in rows):
        return "confidence_drift_watch"
    if any(row.status == "insufficient_forecast_history" for row in rows):
        return "insufficient_forecast_history"
    return "confidence_stable"


def _report_reason_codes(status: str) -> tuple[str, ...]:
    if status == "empty_forecast_set":
        return ("no_forecasts",)
    if status == "confidence_drift_block":
        return ("confidence_drift_blocked",)
    if status == "confidence_drift_watch":
        return ("confidence_drift_detected",)
    if status == "insufficient_forecast_history":
        return ("insufficient_forecast_history",)
    return ("confidence_stable",)


def _normalize_rows(value: object) -> tuple[ForecastConfidenceDriftRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ForecastConfidenceDriftRow:
            raise ValueError("rows must contain ForecastConfidenceDriftRow values")
        _require_hard_flags("ForecastConfidenceDriftRow", row)
    if tuple(sorted(rows, key=lambda row: row.condition_id)) != rows:
        raise ValueError("rows must be sorted by condition_id")
    if len({row.condition_id for row in rows}) != len(rows):
        raise ValueError("rows must use unique condition_id values")
    return rows


def _validate_row(row: ForecastConfidenceDriftRow) -> None:
    if row.baseline_count + row.latest_count != row.forecast_count:
        raise ValueError("baseline_count and latest_count must match forecast_count")
    metric_values = (
        row.baseline_mean_confidence,
        row.latest_mean_confidence,
        row.confidence_delta,
        row.absolute_confidence_delta,
    )
    if row.status == "insufficient_forecast_history":
        if any(value is not None for value in metric_values):
            raise ValueError("drift metrics must be absent without sufficient history")
        if row.reason_codes != ("insufficient_forecast_history",):
            raise ValueError("reason_codes must match insufficient history status")
        return
    if any(value is None for value in metric_values):
        raise ValueError("drift metrics are required with sufficient history")
    if row.confidence_delta is None or row.absolute_confidence_delta is None:
        raise ValueError("confidence_delta is required with sufficient history")
    if abs(row.confidence_delta) != row.absolute_confidence_delta:
        raise ValueError("absolute_confidence_delta must match confidence_delta")
    if row.status == "confidence_drift_block" and row.reason_codes != (
        "confidence_drift_blocked",
    ):
        raise ValueError("reason_codes must match confidence drift block status")
    if row.status == "confidence_drift_watch" and row.reason_codes != (
        "confidence_drift_detected",
    ):
        raise ValueError("reason_codes must match confidence drift watch status")
    if row.status == "confidence_stable" and row.reason_codes != ("confidence_stable",):
        raise ValueError("reason_codes must match confidence stable status")


def _validate_report(report: ForecastConfidenceDriftMonitorReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "confidence_drift_watch"),
    ):
        raise ValueError("watch_count must match confidence drift watch rows")
    if report.block_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "confidence_drift_block"),
    ):
        raise ValueError("block_count must match confidence drift block rows")
    if report.forecast_count != sum((row.forecast_count for row in report.rows), ZERO):
        raise ValueError("forecast_count must match rows")
    expected_max = _max_absolute_confidence_delta(report.rows)
    if report.max_absolute_confidence_delta != expected_max:
        raise ValueError("max_absolute_confidence_delta must match rows")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.status):
        raise ValueError("reason_codes must match status")
    if report.forecast_count == ZERO:
        if report.rows != ():
            raise ValueError("rows must be empty without forecasts")
        if report.status != "empty_forecast_set":
            raise ValueError("status must match empty forecast set")
        if report.max_absolute_confidence_delta is not None:
            raise ValueError(
                "max_absolute_confidence_delta must be absent without forecasts",
            )


def _max_absolute_confidence_delta(
    rows: tuple[ForecastConfidenceDriftRow, ...],
) -> Decimal | None:
    deltas = tuple(
        row.absolute_confidence_delta
        for row in rows
        if row.absolute_confidence_delta is not None
    )
    if not deltas:
        return None
    return _quantize_ratio(max(deltas))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must not be empty")
    return _quantize_ratio(sum(values, ZERO) / Decimal(len(values)))


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=UTC,
            fold=value.fold,
        )
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain canonical strings") from exc
    if not items:
        raise ValueError("reason_codes must contain canonical strings")
    for item in items:
        _require_canonical_string("reason_codes", item)
    if len(set(items)) != len(items):
        raise ValueError("reason_codes must be unique")
    return items


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    count = _normalize_count_decimal(field_name, value)
    if count <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return count


def _normalize_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    count = _normalize_count_decimal(field_name, value)
    if count < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return count


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return value.quantize(COUNT_QUANTUM)


def _normalize_optional_probability(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(value)


def _normalize_probability_delta(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(value)


def _normalize_optional_signed_probability_delta(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < -ONE or value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return _quantize_ratio(value)


def _quantize_ratio(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("ratio must be finite")
    return value.quantize(RATIO_QUANTUM)


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _finalize_digest(value: object, supplied_digest: str) -> str:
    expected_digest = _derived_validation_digest(value)
    if supplied_digest == "":
        return expected_digest
    if type(supplied_digest) is not str or supplied_digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload")
    return supplied_digest


def _derived_validation_digest(value: object) -> str:
    ready = _json_ready(_digest_source(value))
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _digest_source(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _digest_source(getattr(value, field.name))
            for field in fields(value)
            if field.name != DERIVED_VALIDATION_DIGEST_FIELD
        }
    if isinstance(value, dict):
        return {
            key: _digest_source(item)
            for key, item in value.items()
            if key != DERIVED_VALIDATION_DIGEST_FIELD
        }
    if isinstance(value, (list, tuple)):
        return [_digest_source(item) for item in value]
    return value


def _validate_payload_digests(value: object) -> None:
    if isinstance(value, dict):
        requires_digest = HARD_FLAG_FIELDS.issubset(value) and (
            "rows" in value or "condition_id" in value
        )
        if requires_digest and DERIVED_VALIDATION_DIGEST_FIELD not in value:
            raise ValueError("derived_validation_digest is required")
        if DERIVED_VALIDATION_DIGEST_FIELD in value:
            supplied = value[DERIVED_VALIDATION_DIGEST_FIELD]
            expected = _derived_validation_digest(value)
            if type(supplied) is not str or supplied != expected:
                raise ValueError("derived_validation_digest must match payload")
        for item in value.values():
            _validate_payload_digests(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_digests(item)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_live_surface(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_live_surface(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_live_fragment(value):
            raise ValueError(f"unsafe live surface in {path or label}")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_live_fragment(key):
                raise ValueError(f"unsafe live surface in {label}: {key}")
            if key in HARD_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_live_surface(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_live_surface(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_live_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_LIVE_SURFACE_FRAGMENTS)


__all__ = (
    "ForecastConfidenceDriftForecast",
    "ForecastConfidenceDriftMonitorConfig",
    "ForecastConfidenceDriftMonitorReport",
    "ForecastConfidenceDriftRow",
    "build_forecast_confidence_drift_monitor_report",
    "forecast_confidence_drift_monitor_payload",
)
