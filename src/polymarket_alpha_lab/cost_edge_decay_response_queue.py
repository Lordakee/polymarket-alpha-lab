"""Pure report reducer for cost-edge decay response queues."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_COST_EDGE_DECAY_RESPONSE_QUEUE_CONFIG_VERSION = (
    "cost-edge-decay-response-queue-v0"
)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE = Decimal("1")
BOUNDARY_STATEMENT = (
    "Report-only cost-edge decay response queue; no investment guidance or trade instructions."
)
RESPONSE_STATUSES = (
    "monitor_only",
    "stale_edge",
    "review_needed",
    "abstain_until_refresh",
)
REPORT_STATUSES = ("response_queue_clear", "response_queue_attention")
ROW_REASON_CODES = (
    "edge_decay_clear",
    "stale_edge",
    "edge_decay_review_needed",
    "edge_below_refresh_threshold",
)
REPORT_REASON_CODES = (
    "cost_edge_decay_response_queue_clear",
    "review_needed_edges_present",
    "stale_edges_require_refresh",
    "abstain_until_refresh_edges_present",
)
STATUS_WEIGHT = {
    "review_needed": 0,
    "abstain_until_refresh": 1,
    "stale_edge": 2,
    "monitor_only": 3,
}


@dataclass(frozen=True)
class CostEdgeDecayResponseQueueConfig:
    config_version: str = DEFAULT_COST_EDGE_DECAY_RESPONSE_QUEUE_CONFIG_VERSION
    stale_observation_count: int = 3
    review_decay_threshold: Decimal = Decimal("0.020000")
    abstain_cost_adjusted_edge_threshold: Decimal = Decimal("0.010000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("stale_observation_count", self.stale_observation_count)
        object.__setattr__(
            self,
            "review_decay_threshold",
            _normalize_nonnegative_ratio(
                "review_decay_threshold",
                self.review_decay_threshold,
            ),
        )
        object.__setattr__(
            self,
            "abstain_cost_adjusted_edge_threshold",
            _normalize_ratio(
                "abstain_cost_adjusted_edge_threshold",
                self.abstain_cost_adjusted_edge_threshold,
            ),
        )
        require_paper_only_flags("CostEdgeDecayResponseQueueConfig", self)


@dataclass(frozen=True)
class CostEdgeDecayObservation:
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
        require_paper_only_flags("CostEdgeDecayObservation", self)


@dataclass(frozen=True)
class CostEdgeDecayResponseRow:
    edge_key: str
    observation_count: Decimal
    first_observed_at: datetime
    latest_observed_at: datetime
    first_cost_adjusted_edge: Decimal
    latest_cost_adjusted_edge: Decimal
    peak_cost_adjusted_edge: Decimal
    edge_delta: Decimal
    edge_decay: Decimal
    response_status: str
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
        _require_member("response_status", self.response_status, RESPONSE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("CostEdgeDecayResponseRow", self)


@dataclass(frozen=True)
class CostEdgeDecayResponseQueueReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    edge_count: Decimal
    review_needed_count: Decimal
    abstain_until_refresh_count: Decimal
    stale_edge_count: Decimal
    monitor_only_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    response_rows: tuple[CostEdgeDecayResponseRow, ...]
    derived_validation_digest: str
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "edge_count",
            "review_needed_count",
            "abstain_until_refresh_count",
            "stale_edge_count",
            "monitor_only_count",
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
        object.__setattr__(self, "response_rows", _normalize_rows(self.response_rows))
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match report-only boundary")
        _validate_report(self)
        reject_unsafe_surface_fields("cost edge decay response queue report", self)
        require_paper_only_flags("CostEdgeDecayResponseQueueReport", self)
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _report_derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report fields")


def build_cost_edge_decay_response_queue_report(
    observations: list[CostEdgeDecayObservation] | tuple[CostEdgeDecayObservation, ...],
    *,
    config: CostEdgeDecayResponseQueueConfig,
    generated_at: datetime,
) -> CostEdgeDecayResponseQueueReport:
    if type(config) is not CostEdgeDecayResponseQueueConfig:
        raise ValueError("config must be a CostEdgeDecayResponseQueueConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_observations(observations, generated_at_utc)
    response_rows = tuple(
        sorted(
            (
                _response_row(edge_key, edge_observations, config)
                for edge_key, edge_observations in _edge_groups(rows)
            ),
            key=_response_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "observation_count": _count(len(rows)),
        "edge_count": _count(len(response_rows)),
        "review_needed_count": _status_count(response_rows, "review_needed"),
        "abstain_until_refresh_count": _status_count(
            response_rows,
            "abstain_until_refresh",
        ),
        "stale_edge_count": _status_count(response_rows, "stale_edge"),
        "monitor_only_count": _status_count(response_rows, "monitor_only"),
        "status": _report_status(response_rows),
        "reason_codes": _report_reason_codes(response_rows),
        "response_rows": response_rows,
        "boundary_statement": BOUNDARY_STATEMENT,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CostEdgeDecayResponseQueueReport(
        **values,
        derived_validation_digest=_derived_validation_digest(values),
    )


def cost_edge_decay_response_queue_payload(
    report: CostEdgeDecayResponseQueueReport,
) -> dict[str, Any]:
    if type(report) is not CostEdgeDecayResponseQueueReport:
        raise ValueError("report must be a CostEdgeDecayResponseQueueReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("cost edge decay response queue report", report)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    return json_ready_no_floats(report)


def _normalize_observations(
    observations: list[CostEdgeDecayObservation] | tuple[CostEdgeDecayObservation, ...],
    generated_at: datetime,
) -> tuple[CostEdgeDecayObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(observations)
    seen_keys: set[tuple[str, int]] = set()
    for row in rows:
        if type(row) is not CostEdgeDecayObservation:
            raise ValueError("observations must contain CostEdgeDecayObservation values")
        require_paper_only_flags("observation", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (row.edge_key, row.observation_sequence)
        if key in seen_keys:
            raise ValueError("observations must not contain duplicate edge sequence values")
        seen_keys.add(key)
    return rows


def _edge_groups(
    rows: tuple[CostEdgeDecayObservation, ...],
) -> tuple[tuple[str, tuple[CostEdgeDecayObservation, ...]], ...]:
    groups: dict[str, list[CostEdgeDecayObservation]] = defaultdict(list)
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


def _response_row(
    edge_key: str,
    observations: tuple[CostEdgeDecayObservation, ...],
    config: CostEdgeDecayResponseQueueConfig,
) -> CostEdgeDecayResponseRow:
    first = observations[0]
    latest = observations[-1]
    peak_cost_adjusted_edge = max(row.cost_adjusted_edge for row in observations)
    edge_delta = latest.cost_adjusted_edge - first.cost_adjusted_edge
    edge_decay = max(peak_cost_adjusted_edge - latest.cost_adjusted_edge, ZERO_RATIO)
    response_status = _response_status(
        observation_count=len(observations),
        latest_cost_adjusted_edge=latest.cost_adjusted_edge,
        edge_decay=edge_decay,
        config=config,
    )
    return CostEdgeDecayResponseRow(
        edge_key=edge_key,
        observation_count=_count(len(observations)),
        first_observed_at=first.observed_at,
        latest_observed_at=latest.observed_at,
        first_cost_adjusted_edge=first.cost_adjusted_edge,
        latest_cost_adjusted_edge=latest.cost_adjusted_edge,
        peak_cost_adjusted_edge=peak_cost_adjusted_edge,
        edge_delta=edge_delta,
        edge_decay=edge_decay,
        response_status=response_status,
        reason_codes=_row_reason_codes(response_status),
    )


def _response_status(
    *,
    observation_count: int,
    latest_cost_adjusted_edge: Decimal,
    edge_decay: Decimal,
    config: CostEdgeDecayResponseQueueConfig,
) -> str:
    if edge_decay >= config.review_decay_threshold:
        return "review_needed"
    if observation_count >= config.stale_observation_count:
        if latest_cost_adjusted_edge <= config.abstain_cost_adjusted_edge_threshold:
            return "abstain_until_refresh"
        return "stale_edge"
    return "monitor_only"


def _response_row_sort_key(row: CostEdgeDecayResponseRow) -> tuple[int, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.response_status],
        -row.edge_decay,
        row.latest_cost_adjusted_edge,
        row.edge_key,
    )


def _row_reason_codes(status: str) -> tuple[str, ...]:
    if status == "review_needed":
        return ("edge_decay_review_needed",)
    if status == "abstain_until_refresh":
        return ("stale_edge", "edge_below_refresh_threshold")
    if status == "stale_edge":
        return ("stale_edge",)
    return ("edge_decay_clear",)


def _report_status(rows: tuple[CostEdgeDecayResponseRow, ...]) -> str:
    if any(row.response_status != "monitor_only" for row in rows):
        return "response_queue_attention"
    return "response_queue_clear"


def _report_reason_codes(rows: tuple[CostEdgeDecayResponseRow, ...]) -> tuple[str, ...]:
    if not rows or all(row.response_status == "monitor_only" for row in rows):
        return ("cost_edge_decay_response_queue_clear",)
    codes: list[str] = []
    if any(row.response_status == "review_needed" for row in rows):
        codes.append("review_needed_edges_present")
    if any(
        row.response_status in ("stale_edge", "abstain_until_refresh")
        for row in rows
    ):
        codes.append("stale_edges_require_refresh")
    if any(row.response_status == "abstain_until_refresh" for row in rows):
        codes.append("abstain_until_refresh_edges_present")
    return tuple(codes)


def _status_count(rows: tuple[CostEdgeDecayResponseRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.response_status == status))


def _validate_row(row: CostEdgeDecayResponseRow) -> None:
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
    if row.reason_codes != _row_reason_codes(row.response_status):
        raise ValueError("reason_codes must match response_status")


def _validate_report(report: CostEdgeDecayResponseQueueReport) -> None:
    if report.edge_count != _count(len(report.response_rows)):
        raise ValueError("edge_count must match response_rows")
    if report.observation_count != sum(
        (row.observation_count for row in report.response_rows),
        ZERO_COUNT,
    ):
        raise ValueError("observation_count must match response_rows")
    if report.review_needed_count != _status_count(report.response_rows, "review_needed"):
        raise ValueError("review_needed_count must match response_rows")
    if report.abstain_until_refresh_count != _status_count(
        report.response_rows,
        "abstain_until_refresh",
    ):
        raise ValueError("abstain_until_refresh_count must match response_rows")
    if report.stale_edge_count != _status_count(report.response_rows, "stale_edge"):
        raise ValueError("stale_edge_count must match response_rows")
    if report.monitor_only_count != _status_count(report.response_rows, "monitor_only"):
        raise ValueError("monitor_only_count must match response_rows")
    if report.status != _report_status(report.response_rows):
        raise ValueError("status must match response_rows")
    if report.reason_codes != _report_reason_codes(report.response_rows):
        raise ValueError("reason_codes must match response_rows")
    if report.response_rows != tuple(
        sorted(report.response_rows, key=_response_row_sort_key),
    ):
        raise ValueError("response_rows must use deterministic sorting")


def _report_derived_validation_digest(
    report: CostEdgeDecayResponseQueueReport,
) -> str:
    return _derived_validation_digest(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "observation_count": report.observation_count,
            "edge_count": report.edge_count,
            "review_needed_count": report.review_needed_count,
            "abstain_until_refresh_count": report.abstain_until_refresh_count,
            "stale_edge_count": report.stale_edge_count,
            "monitor_only_count": report.monitor_only_count,
            "status": report.status,
            "reason_codes": report.reason_codes,
            "response_rows": report.response_rows,
            "boundary_statement": report.boundary_statement,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _derived_validation_digest(values: dict[str, object]) -> str:
    ready = json_ready_no_floats(values)
    reject_unsafe_surface_fields("cost edge decay response queue validation digest", ready)
    canonical = json.dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_rows(value: object) -> tuple[CostEdgeDecayResponseRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("response_rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("response_rows must be a tuple") from exc
    for row in rows:
        if type(row) is not CostEdgeDecayResponseRow:
            raise ValueError("response_rows must contain CostEdgeDecayResponseRow values")
        require_paper_only_flags("response row", row)
    return rows


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


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


__all__ = (
    "DEFAULT_COST_EDGE_DECAY_RESPONSE_QUEUE_CONFIG_VERSION",
    "CostEdgeDecayResponseQueueConfig",
    "CostEdgeDecayObservation",
    "CostEdgeDecayResponseRow",
    "CostEdgeDecayResponseQueueReport",
    "build_cost_edge_decay_response_queue_report",
    "cost_edge_decay_response_queue_payload",
)
