"""Paper-only diagnostics for cost-adjusted edge decay."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_COST_ADJUSTED_EDGE_DECAY_MONITOR_CONFIG_VERSION = (
    "cost-adjusted-edge-decay-monitor-v0"
)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE = Decimal("1")
DECAY_STATUSES = ("pass", "stale", "decayed")
REPORT_STATUSES = ("pass", "watch")
ROW_REASON_CODES = (
    "edge_decay_clear",
    "edge_stale",
    "edge_decayed",
)
REPORT_REASON_CODES = (
    "cost_adjusted_edge_decay_clear",
    "cost_adjusted_edges_decayed",
    "stale_cost_adjusted_edges_present",
)
STATUS_WEIGHT = {"decayed": 0, "stale": 1, "pass": 2}


@dataclass(frozen=True)
class CostAdjustedEdgeDecayMonitorConfig:
    config_version: str = DEFAULT_COST_ADJUSTED_EDGE_DECAY_MONITOR_CONFIG_VERSION
    stale_observation_count: int = 3
    decay_threshold: Decimal = Decimal("0.020000")
    stale_cost_adjusted_edge_threshold: Decimal = Decimal("0.010000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("stale_observation_count", self.stale_observation_count)
        object.__setattr__(
            self,
            "decay_threshold",
            _normalize_nonnegative_ratio("decay_threshold", self.decay_threshold),
        )
        object.__setattr__(
            self,
            "stale_cost_adjusted_edge_threshold",
            _normalize_ratio(
                "stale_cost_adjusted_edge_threshold",
                self.stale_cost_adjusted_edge_threshold,
            ),
        )
        require_paper_only_flags("CostAdjustedEdgeDecayMonitorConfig", self)


@dataclass(frozen=True)
class CostAdjustedEdgeObservation:
    edge_key: str
    observation_sequence: int
    observed_at: datetime
    cost_adjusted_edge: Decimal
    source_count: Decimal = ONE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("edge_key", self.edge_key)
        _require_positive_int("observation_sequence", self.observation_sequence)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_ratio("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_positive_count("source_count", self.source_count),
        )
        require_paper_only_flags("CostAdjustedEdgeObservation", self)


@dataclass(frozen=True)
class CostAdjustedEdgeDecayRow:
    edge_key: str
    observation_count: Decimal
    first_observed_at: datetime
    latest_observed_at: datetime
    first_cost_adjusted_edge: Decimal
    latest_cost_adjusted_edge: Decimal
    peak_cost_adjusted_edge: Decimal
    edge_delta: Decimal
    edge_decay: Decimal
    decay_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("edge_key", self.edge_key)
        object.__setattr__(
            self,
            "observation_count",
            _normalize_positive_count("observation_count", self.observation_count),
        )
        object.__setattr__(
            self,
            "first_observed_at",
            _as_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "first_cost_adjusted_edge",
            "latest_cost_adjusted_edge",
            "peak_cost_adjusted_edge",
            "edge_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_decay",
            _normalize_nonnegative_ratio("edge_decay", self.edge_decay),
        )
        _require_member("decay_status", self.decay_status, DECAY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("CostAdjustedEdgeDecayRow", self)


@dataclass(frozen=True)
class CostAdjustedEdgeDecayMonitorReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    edge_count: Decimal
    decayed_edge_count: Decimal
    stale_edge_count: Decimal
    watch_edge_count: Decimal
    pass_edge_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    edge_rows: tuple[CostAdjustedEdgeDecayRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "edge_count",
            "decayed_edge_count",
            "stale_edge_count",
            "watch_edge_count",
            "pass_edge_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "edge_rows", _normalize_rows(self.edge_rows))
        _validate_report(self)
        reject_unsafe_surface_fields("cost adjusted edge decay monitor report", self)
        require_paper_only_flags("CostAdjustedEdgeDecayMonitorReport", self)
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        if self.derived_validation_digest != _report_derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report fields")


def build_cost_adjusted_edge_decay_monitor_report(
    observations: list[CostAdjustedEdgeObservation]
    | tuple[CostAdjustedEdgeObservation, ...],
    *,
    config: CostAdjustedEdgeDecayMonitorConfig,
    generated_at: datetime,
) -> CostAdjustedEdgeDecayMonitorReport:
    if type(config) is not CostAdjustedEdgeDecayMonitorConfig:
        raise ValueError("config must be a CostAdjustedEdgeDecayMonitorConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_observations(observations, generated_at_utc)
    edge_rows = tuple(
        sorted(
            (
                _edge_row(edge_key, edge_observations, config)
                for edge_key, edge_observations in _edge_groups(rows)
            ),
            key=_edge_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "observation_count": _count(len(rows)),
        "edge_count": _count(len(edge_rows)),
        "decayed_edge_count": _status_count(edge_rows, "decayed"),
        "stale_edge_count": _status_count(edge_rows, "stale"),
        "watch_edge_count": _count(
            sum(1 for row in edge_rows if row.decay_status in ("decayed", "stale")),
        ),
        "pass_edge_count": _status_count(edge_rows, "pass"),
        "status": _report_status(edge_rows),
        "reason_codes": _report_reason_codes(edge_rows),
        "edge_rows": edge_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CostAdjustedEdgeDecayMonitorReport(
        **values,
        derived_validation_digest=_derived_validation_digest(values),
    )


def cost_adjusted_edge_decay_monitor_payload(
    report: CostAdjustedEdgeDecayMonitorReport,
) -> dict[str, Any]:
    if type(report) is not CostAdjustedEdgeDecayMonitorReport:
        raise ValueError("report must be a CostAdjustedEdgeDecayMonitorReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("cost adjusted edge decay monitor report", report)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    return json_ready_no_floats(report)


def _normalize_observations(
    observations: list[CostAdjustedEdgeObservation]
    | tuple[CostAdjustedEdgeObservation, ...],
    generated_at: datetime,
) -> tuple[CostAdjustedEdgeObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(observations)
    seen_keys: set[tuple[str, int]] = set()
    for row in rows:
        if type(row) is not CostAdjustedEdgeObservation:
            raise ValueError("observations must contain CostAdjustedEdgeObservation values")
        require_paper_only_flags("observation", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (row.edge_key, row.observation_sequence)
        if key in seen_keys:
            raise ValueError("observations must not contain duplicate edge sequence values")
        seen_keys.add(key)
    return rows


def _edge_groups(
    rows: tuple[CostAdjustedEdgeObservation, ...],
) -> tuple[tuple[str, tuple[CostAdjustedEdgeObservation, ...]], ...]:
    groups: dict[str, list[CostAdjustedEdgeObservation]] = defaultdict(list)
    for row in rows:
        groups[row.edge_key].append(row)
    return tuple(
        (
            edge_key,
            tuple(
                sorted(
                    edge_rows,
                    key=lambda row: (row.observation_sequence, row.observed_at),
                ),
            ),
        )
        for edge_key, edge_rows in groups.items()
    )


def _edge_row(
    edge_key: str,
    observations: tuple[CostAdjustedEdgeObservation, ...],
    config: CostAdjustedEdgeDecayMonitorConfig,
) -> CostAdjustedEdgeDecayRow:
    first = observations[0]
    latest = observations[-1]
    peak_cost_adjusted_edge = max(row.cost_adjusted_edge for row in observations)
    edge_delta = latest.cost_adjusted_edge - first.cost_adjusted_edge
    edge_decay = max(peak_cost_adjusted_edge - latest.cost_adjusted_edge, ZERO_RATIO)
    decay_status = _decay_status(
        observation_count=len(observations),
        latest_cost_adjusted_edge=latest.cost_adjusted_edge,
        edge_decay=edge_decay,
        config=config,
    )
    return CostAdjustedEdgeDecayRow(
        edge_key=edge_key,
        observation_count=_count(len(observations)),
        first_observed_at=first.observed_at,
        latest_observed_at=latest.observed_at,
        first_cost_adjusted_edge=first.cost_adjusted_edge,
        latest_cost_adjusted_edge=latest.cost_adjusted_edge,
        peak_cost_adjusted_edge=peak_cost_adjusted_edge,
        edge_delta=edge_delta,
        edge_decay=edge_decay,
        decay_status=decay_status,
        reason_codes=_row_reason_codes(decay_status),
    )


def _decay_status(
    *,
    observation_count: int,
    latest_cost_adjusted_edge: Decimal,
    edge_decay: Decimal,
    config: CostAdjustedEdgeDecayMonitorConfig,
) -> str:
    if edge_decay >= config.decay_threshold:
        return "decayed"
    if (
        observation_count >= config.stale_observation_count
        and latest_cost_adjusted_edge <= config.stale_cost_adjusted_edge_threshold
    ):
        return "stale"
    return "pass"


def _edge_row_sort_key(row: CostAdjustedEdgeDecayRow) -> tuple[int, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.decay_status],
        -row.edge_decay,
        row.latest_cost_adjusted_edge,
        row.edge_key,
    )


def _row_reason_codes(status: str) -> tuple[str, ...]:
    if status == "decayed":
        return ("edge_decayed",)
    if status == "stale":
        return ("edge_stale",)
    return ("edge_decay_clear",)


def _report_status(rows: tuple[CostAdjustedEdgeDecayRow, ...]) -> str:
    if any(row.decay_status in ("decayed", "stale") for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[CostAdjustedEdgeDecayRow, ...]) -> tuple[str, ...]:
    if not rows or all(row.decay_status == "pass" for row in rows):
        return ("cost_adjusted_edge_decay_clear",)
    codes: list[str] = []
    if any(row.decay_status == "decayed" for row in rows):
        codes.append("cost_adjusted_edges_decayed")
    if any(row.decay_status == "stale" for row in rows):
        codes.append("stale_cost_adjusted_edges_present")
    return tuple(codes)


def _status_count(rows: tuple[CostAdjustedEdgeDecayRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.decay_status == status))


def _validate_row(row: CostAdjustedEdgeDecayRow) -> None:
    if row.latest_observed_at < row.first_observed_at:
        raise ValueError("latest_observed_at must not be before first_observed_at")
    if row.peak_cost_adjusted_edge < row.first_cost_adjusted_edge:
        raise ValueError("peak_cost_adjusted_edge must include first observation")
    if row.peak_cost_adjusted_edge < row.latest_cost_adjusted_edge:
        raise ValueError("peak_cost_adjusted_edge must include latest observation")
    if row.edge_delta != _normalize_ratio(
        "edge_delta",
        row.latest_cost_adjusted_edge - row.first_cost_adjusted_edge,
    ):
        raise ValueError("edge_delta must match first and latest edge")
    if row.edge_decay != _normalize_nonnegative_ratio(
        "edge_decay",
        max(row.peak_cost_adjusted_edge - row.latest_cost_adjusted_edge, ZERO_RATIO),
    ):
        raise ValueError("edge_decay must match peak and latest edge")
    if row.reason_codes != _row_reason_codes(row.decay_status):
        raise ValueError("reason_codes must match decay_status")


def _validate_report(report: CostAdjustedEdgeDecayMonitorReport) -> None:
    if report.edge_count != _count(len(report.edge_rows)):
        raise ValueError("edge_count must match edge_rows")
    if report.observation_count != sum(
        (row.observation_count for row in report.edge_rows),
        ZERO_COUNT,
    ):
        raise ValueError("observation_count must match edge_rows")
    if report.decayed_edge_count != _status_count(report.edge_rows, "decayed"):
        raise ValueError("decayed_edge_count must match edge_rows")
    if report.stale_edge_count != _status_count(report.edge_rows, "stale"):
        raise ValueError("stale_edge_count must match edge_rows")
    if report.pass_edge_count != _status_count(report.edge_rows, "pass"):
        raise ValueError("pass_edge_count must match edge_rows")
    if report.watch_edge_count != report.decayed_edge_count + report.stale_edge_count:
        raise ValueError("watch_edge_count must match edge_rows")
    if report.status != _report_status(report.edge_rows):
        raise ValueError("status must match edge_rows")
    if report.reason_codes != _report_reason_codes(report.edge_rows):
        raise ValueError("reason_codes must match edge_rows")
    if report.edge_rows != tuple(sorted(report.edge_rows, key=_edge_row_sort_key)):
        raise ValueError("edge_rows must use deterministic sorting")


def _normalize_rows(value: object) -> tuple[CostAdjustedEdgeDecayRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("edge_rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("edge_rows must be a tuple") from exc
    for row in rows:
        if type(row) is not CostAdjustedEdgeDecayRow:
            raise ValueError("edge_rows must contain CostAdjustedEdgeDecayRow values")
        require_paper_only_flags("edge row", row)
    return rows


def _report_derived_validation_digest(
    report: CostAdjustedEdgeDecayMonitorReport,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _derived_validation_digest(values)


def _derived_validation_digest(values: dict[str, object]) -> str:
    ready = json_ready_no_floats(values)
    reject_unsafe_surface_fields("cost adjusted edge decay monitor digest", ready)
    canonical = json.dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(RATIO_QUANTUM)


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    ratio = _normalize_ratio(field_name, value)
    if ratio < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return ratio


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


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    count = _normalize_nonnegative_count(field_name, value)
    if count <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return count


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


__all__ = (
    "DEFAULT_COST_ADJUSTED_EDGE_DECAY_MONITOR_CONFIG_VERSION",
    "CostAdjustedEdgeDecayMonitorConfig",
    "CostAdjustedEdgeObservation",
    "CostAdjustedEdgeDecayRow",
    "CostAdjustedEdgeDecayMonitorReport",
    "build_cost_adjusted_edge_decay_monitor_report",
    "cost_adjusted_edge_decay_monitor_payload",
)
