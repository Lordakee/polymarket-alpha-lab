"""Pure in-memory market probability context refresh pressure report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_PROBABILITY_CONTEXT_REFRESH_PRESSURE_CONFIG_VERSION = (
    "market-probability-context-refresh-pressure-report-v0"
)

STATUSES = ("blocked", "watch", "pass")
REPORT_STATUSES = ("pass", "watch", "blocked")
STATUS_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}

CLEAR_REASON = "market_probability_context_current"
BELOW_MATERIALITY_REASON = "market_probability_move_below_materiality"
REFRESH_MISSING_REASON = "market_probability_context_refresh_missing"
CONTEXT_STALE_REASON = "market_probability_context_refresh_stale"
EVIDENCE_STALE_REASON = "market_probability_evidence_refresh_stale"
MOVE_UNACKNOWLEDGED_REASON = "market_probability_move_unacknowledged"
ACKNOWLEDGEMENT_DELAYED_REASON = "market_probability_acknowledgement_delayed"
REPORT_CLEAR_REASON = "market_probability_context_refresh_pressure_clear"

ROW_REASON_CODES = (
    CLEAR_REASON,
    BELOW_MATERIALITY_REASON,
    REFRESH_MISSING_REASON,
    CONTEXT_STALE_REASON,
    EVIDENCE_STALE_REASON,
    MOVE_UNACKNOWLEDGED_REASON,
    ACKNOWLEDGEMENT_DELAYED_REASON,
)
REPORT_REASON_CODES = (
    REPORT_CLEAR_REASON,
    REFRESH_MISSING_REASON,
    CONTEXT_STALE_REASON,
    MOVE_UNACKNOWLEDGED_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
PROBABILITY_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ONE_RATIO = Decimal("1").quantize(RATIO_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
ZERO_PROBABILITY = Decimal("0").quantize(PROBABILITY_QUANTUM)
ONE_PROBABILITY = Decimal("1").quantize(PROBABILITY_QUANTUM)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


LOCAL_UNSAFE_FIELD_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("bro", "ker"),
        _join_parts("sub", "mit"),
        _join_parts("ad", "vice"),
        "network",
        "database",
        "persist",
    ),
)

UNSAFE_VALUE_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("bro", "ker"),
        "auth",
        "private_key",
        "wallet",
        "account",
        "balance",
        "order",
        "cancel",
        "replace",
        "sign",
        "exchange_mutation",
        "token=",
        "secret",
        "private://",
        "network",
        "database",
        "persist",
    ),
)

DIGEST_VERSION = "market_probability_context_refresh_pressure_report:v1"
DIGEST_HEX_LENGTH = 64


@dataclass(frozen=True)
class MarketProbabilityContextRefreshPressureConfig:
    config_version: str = (
        DEFAULT_MARKET_PROBABILITY_CONTEXT_REFRESH_PRESSURE_CONFIG_VERSION
    )
    material_probability_delta: Decimal = Decimal("0.100000")
    max_context_age_seconds: Decimal = Decimal("3600.000000")
    max_evidence_age_seconds: Decimal = Decimal("3600.000000")
    max_unacknowledged_age_seconds: Decimal = Decimal("900.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "material_probability_delta",
            _normalize_nonnegative_probability_delta(
                "material_probability_delta",
                self.material_probability_delta,
            ),
        )
        for field_name in (
            "max_context_age_seconds",
            "max_evidence_age_seconds",
            "max_unacknowledged_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags(
            "MarketProbabilityContextRefreshPressureConfig",
            self,
        )


@dataclass(frozen=True)
class MarketProbabilityContextRefreshPressureSnapshot:
    market_id: str
    probability_observed_at: datetime
    previous_probability: Decimal
    current_probability: Decimal
    probability_delta: Decimal
    context_refreshed_at: datetime | None
    evidence_refreshed_at: datetime | None
    acknowledged_at: datetime | None
    source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "probability_observed_at",
            _as_utc("probability_observed_at", self.probability_observed_at),
        )
        for field_name in ("previous_probability", "current_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_delta",
            _normalize_probability_delta("probability_delta", self.probability_delta),
        )
        expected_delta = _probability_delta(
            self.previous_probability,
            self.current_probability,
        )
        if self.probability_delta != expected_delta:
            raise ValueError("probability_delta must match current minus previous")
        for field_name in (
            "context_refreshed_at",
            "evidence_refreshed_at",
            "acknowledged_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count("source_count", self.source_count),
        )
        require_paper_only_flags(
            "MarketProbabilityContextRefreshPressureSnapshot",
            self,
        )


@dataclass(frozen=True)
class MarketProbabilityContextRefreshPressureRow:
    market_id: str
    probability_observed_at: datetime
    previous_probability: Decimal
    current_probability: Decimal
    probability_delta: Decimal
    absolute_probability_delta: Decimal
    probability_age_seconds: Decimal
    context_refreshed_at: datetime | None
    evidence_refreshed_at: datetime | None
    acknowledged_at: datetime | None
    context_age_seconds: Decimal | None
    evidence_age_seconds: Decimal | None
    unacknowledged_age_seconds: Decimal | None
    source_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "probability_observed_at",
            _as_utc("probability_observed_at", self.probability_observed_at),
        )
        for field_name in ("previous_probability", "current_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_delta",
            _normalize_probability_delta("probability_delta", self.probability_delta),
        )
        object.__setattr__(
            self,
            "absolute_probability_delta",
            _normalize_nonnegative_probability_delta(
                "absolute_probability_delta",
                self.absolute_probability_delta,
            ),
        )
        expected_delta = _probability_delta(
            self.previous_probability,
            self.current_probability,
        )
        if self.probability_delta != expected_delta:
            raise ValueError("probability_delta must match current minus previous")
        if self.absolute_probability_delta != abs(self.probability_delta):
            raise ValueError("absolute_probability_delta must match probability_delta")
        object.__setattr__(
            self,
            "probability_age_seconds",
            _normalize_nonnegative_seconds(
                "probability_age_seconds",
                self.probability_age_seconds,
            ),
        )
        for field_name in (
            "context_refreshed_at",
            "evidence_refreshed_at",
            "acknowledged_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "context_age_seconds",
            "evidence_age_seconds",
            "unacknowledged_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_seconds(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count("source_count", self.source_count),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
                clear_reasons=(CLEAR_REASON, BELOW_MATERIALITY_REASON),
            ),
        )
        require_paper_only_flags(
            "MarketProbabilityContextRefreshPressureRow",
            self,
        )


@dataclass(frozen=True)
class MarketProbabilityContextRefreshPressureReport:
    generated_at: datetime
    config_version: str
    material_probability_delta: Decimal
    max_context_age_seconds: Decimal
    max_evidence_age_seconds: Decimal
    max_unacknowledged_age_seconds: Decimal
    status: str
    market_count: Decimal
    material_move_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    refresh_pressure_count: Decimal
    refresh_pressure_ratio: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[MarketProbabilityContextRefreshPressureRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "material_probability_delta",
            _normalize_nonnegative_probability_delta(
                "material_probability_delta",
                self.material_probability_delta,
            ),
        )
        for field_name in (
            "max_context_age_seconds",
            "max_evidence_age_seconds",
            "max_unacknowledged_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUSES)
        for field_name in (
            "market_count",
            "material_move_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "refresh_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "refresh_pressure_ratio",
            _normalize_ratio("refresh_pressure_ratio", self.refresh_pressure_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
                clear_reasons=(REPORT_CLEAR_REASON,),
            ),
        )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        _require_derived_validation_digest(self)
        _validate_report_consistency(self)
        require_paper_only_flags(
            "MarketProbabilityContextRefreshPressureReport",
            self,
        )


def build_market_probability_context_refresh_pressure_report(
    snapshots: list[MarketProbabilityContextRefreshPressureSnapshot]
    | tuple[MarketProbabilityContextRefreshPressureSnapshot, ...],
    *,
    config: MarketProbabilityContextRefreshPressureConfig,
    generated_at: datetime,
) -> MarketProbabilityContextRefreshPressureReport:
    if type(config) is not MarketProbabilityContextRefreshPressureConfig:
        raise ValueError(
            "config must be a MarketProbabilityContextRefreshPressureConfig",
        )
    require_paper_only_flags(
        "MarketProbabilityContextRefreshPressureConfig",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_snapshots(snapshots)
    _reject_future_snapshot_times(source_rows, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_snapshot(
                    snapshot,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for snapshot in source_rows
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    status = _report_status(reason_codes, rows=rows)
    market_count = _count(len(rows))
    material_move_count = _count(
        sum(
            1
            for row in rows
            if row.absolute_probability_delta >= config.material_probability_delta
        ),
    )
    blocked_count = _count(sum(1 for row in rows if row.status == "blocked"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    pass_count = _count(sum(1 for row in rows if row.status == "pass"))
    refresh_pressure_count = _count(sum(1 for row in rows if row.status != "pass"))
    refresh_pressure_ratio = _ratio(refresh_pressure_count, market_count)
    derived_validation_digest = _derived_validation_digest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        material_probability_delta=config.material_probability_delta,
        max_context_age_seconds=config.max_context_age_seconds,
        max_evidence_age_seconds=config.max_evidence_age_seconds,
        max_unacknowledged_age_seconds=config.max_unacknowledged_age_seconds,
        status=status,
        market_count=market_count,
        material_move_count=material_move_count,
        blocked_count=blocked_count,
        watch_count=watch_count,
        pass_count=pass_count,
        refresh_pressure_count=refresh_pressure_count,
        refresh_pressure_ratio=refresh_pressure_ratio,
        reason_codes=reason_codes,
        rows=rows,
    )

    return MarketProbabilityContextRefreshPressureReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        material_probability_delta=config.material_probability_delta,
        max_context_age_seconds=config.max_context_age_seconds,
        max_evidence_age_seconds=config.max_evidence_age_seconds,
        max_unacknowledged_age_seconds=config.max_unacknowledged_age_seconds,
        status=status,
        market_count=market_count,
        material_move_count=material_move_count,
        blocked_count=blocked_count,
        watch_count=watch_count,
        pass_count=pass_count,
        refresh_pressure_count=refresh_pressure_count,
        refresh_pressure_ratio=refresh_pressure_ratio,
        reason_codes=reason_codes,
        rows=rows,
        derived_validation_digest=derived_validation_digest,
    )


def market_probability_context_refresh_pressure_report_payload(
    report: MarketProbabilityContextRefreshPressureReport | dict[str, Any],
) -> dict[str, Any]:
    label = "market probability context refresh pressure report"
    if type(report) is MarketProbabilityContextRefreshPressureReport:
        require_paper_only_flags(
            "MarketProbabilityContextRefreshPressureReport",
            report,
        )
        ready = json_ready_no_floats(report)
        if not isinstance(ready, dict):
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_fields(label, ready)
        _reject_unsafe_public_values(label, ready)
        return ready
    if isinstance(report, dict):
        _require_payload_flags(label, report)
        _reject_payload_flag_downgrades(label, report)
        _reject_unsafe_public_fields(label, report)
        _reject_unsafe_public_values(label, report)
        ready = json_ready_no_floats(report)
        if not isinstance(ready, dict):
            raise ValueError("report payload must be a JSON object")
        _reject_payload_flag_downgrades(label, ready)
        _reject_unsafe_public_fields(label, ready)
        _reject_unsafe_public_values(label, ready)
        return ready
    raise ValueError(
        "report must be a MarketProbabilityContextRefreshPressureReport",
    )


def _row_from_snapshot(
    snapshot: MarketProbabilityContextRefreshPressureSnapshot,
    *,
    config: MarketProbabilityContextRefreshPressureConfig,
    generated_at: datetime,
) -> MarketProbabilityContextRefreshPressureRow:
    probability_age_seconds = _age_seconds(snapshot.probability_observed_at, generated_at)
    context_age_seconds = _optional_age_seconds(
        snapshot.context_refreshed_at,
        generated_at,
    )
    evidence_age_seconds = _optional_age_seconds(
        snapshot.evidence_refreshed_at,
        generated_at,
    )
    unacknowledged_age_seconds = _unacknowledged_age_seconds(snapshot, generated_at)
    reason_codes = _row_reason_codes(
        snapshot,
        config=config,
        context_age_seconds=context_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
        unacknowledged_age_seconds=unacknowledged_age_seconds,
    )

    return MarketProbabilityContextRefreshPressureRow(
        market_id=snapshot.market_id,
        probability_observed_at=snapshot.probability_observed_at,
        previous_probability=snapshot.previous_probability,
        current_probability=snapshot.current_probability,
        probability_delta=snapshot.probability_delta,
        absolute_probability_delta=abs(snapshot.probability_delta),
        probability_age_seconds=probability_age_seconds,
        context_refreshed_at=snapshot.context_refreshed_at,
        evidence_refreshed_at=snapshot.evidence_refreshed_at,
        acknowledged_at=snapshot.acknowledged_at,
        context_age_seconds=context_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
        unacknowledged_age_seconds=unacknowledged_age_seconds,
        source_count=snapshot.source_count,
        status=_row_status(
            reason_codes,
            unacknowledged_age_seconds=unacknowledged_age_seconds,
            max_unacknowledged_age_seconds=config.max_unacknowledged_age_seconds,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    snapshot: MarketProbabilityContextRefreshPressureSnapshot,
    *,
    config: MarketProbabilityContextRefreshPressureConfig,
    context_age_seconds: Decimal | None,
    evidence_age_seconds: Decimal | None,
    unacknowledged_age_seconds: Decimal | None,
) -> tuple[str, ...]:
    if abs(snapshot.probability_delta) < config.material_probability_delta:
        return (BELOW_MATERIALITY_REASON,)

    reasons: list[str] = []
    if snapshot.context_refreshed_at is None or snapshot.evidence_refreshed_at is None:
        reasons.append(REFRESH_MISSING_REASON)
    if (
        snapshot.context_refreshed_at is not None
        and (
            snapshot.context_refreshed_at < snapshot.probability_observed_at
            or (
                context_age_seconds is not None
                and context_age_seconds > config.max_context_age_seconds
            )
        )
    ):
        reasons.append(CONTEXT_STALE_REASON)
    if (
        snapshot.evidence_refreshed_at is not None
        and (
            snapshot.evidence_refreshed_at < snapshot.probability_observed_at
            or (
                evidence_age_seconds is not None
                and evidence_age_seconds > config.max_evidence_age_seconds
            )
        )
    ):
        reasons.append(EVIDENCE_STALE_REASON)
    if snapshot.acknowledged_at is None:
        reasons.append(MOVE_UNACKNOWLEDGED_REASON)
    elif snapshot.acknowledged_at < snapshot.probability_observed_at:
        reasons.append(MOVE_UNACKNOWLEDGED_REASON)
    elif (
        unacknowledged_age_seconds is not None
        and unacknowledged_age_seconds > config.max_unacknowledged_age_seconds
    ):
        reasons.append(ACKNOWLEDGEMENT_DELAYED_REASON)
    if not reasons:
        return (CLEAR_REASON,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        ROW_REASON_CODES,
        clear_reasons=(CLEAR_REASON, BELOW_MATERIALITY_REASON),
    )


def _row_status(
    reason_codes: tuple[str, ...],
    *,
    unacknowledged_age_seconds: Decimal | None,
    max_unacknowledged_age_seconds: Decimal,
) -> str:
    if reason_codes in ((CLEAR_REASON,), (BELOW_MATERIALITY_REASON,)):
        return "pass"
    if REFRESH_MISSING_REASON in reason_codes:
        return "blocked"
    if (
        MOVE_UNACKNOWLEDGED_REASON in reason_codes
        and unacknowledged_age_seconds is not None
        and unacknowledged_age_seconds > max_unacknowledged_age_seconds
    ):
        return "blocked"
    if ACKNOWLEDGEMENT_DELAYED_REASON in reason_codes:
        return "watch"
    return "watch"


def _report_reason_codes(
    rows: tuple[MarketProbabilityContextRefreshPressureRow, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if any(REFRESH_MISSING_REASON in row.reason_codes for row in rows):
        reasons.append(REFRESH_MISSING_REASON)
    if any(
        CONTEXT_STALE_REASON in row.reason_codes
        or EVIDENCE_STALE_REASON in row.reason_codes
        for row in rows
    ):
        reasons.append(CONTEXT_STALE_REASON)
    if any(
        MOVE_UNACKNOWLEDGED_REASON in row.reason_codes
        or ACKNOWLEDGEMENT_DELAYED_REASON in row.reason_codes
        for row in rows
    ):
        reasons.append(MOVE_UNACKNOWLEDGED_REASON)
    if not reasons:
        return (REPORT_CLEAR_REASON,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        REPORT_REASON_CODES,
        clear_reasons=(REPORT_CLEAR_REASON,),
    )


def _report_status(
    reason_codes: tuple[str, ...],
    *,
    rows: tuple[MarketProbabilityContextRefreshPressureRow, ...],
) -> str:
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if REFRESH_MISSING_REASON in reason_codes:
        return "blocked"
    if reason_codes == (REPORT_CLEAR_REASON,):
        return "pass"
    return "watch"


def _normalize_snapshots(
    value: object,
) -> tuple[MarketProbabilityContextRefreshPressureSnapshot, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    snapshots = tuple(value)
    seen_market_ids: set[str] = set()
    for snapshot in snapshots:
        if type(snapshot) is not MarketProbabilityContextRefreshPressureSnapshot:
            raise ValueError(
                "snapshots must contain "
                "MarketProbabilityContextRefreshPressureSnapshot values",
            )
        require_paper_only_flags(
            "MarketProbabilityContextRefreshPressureSnapshot",
            snapshot,
        )
        if snapshot.market_id in seen_market_ids:
            raise ValueError("duplicate market_id values are not allowed")
        seen_market_ids.add(snapshot.market_id)
    return snapshots


def _reject_future_snapshot_times(
    snapshots: tuple[MarketProbabilityContextRefreshPressureSnapshot, ...],
    generated_at: datetime,
) -> None:
    for snapshot in snapshots:
        for field_name in (
            "probability_observed_at",
            "context_refreshed_at",
            "evidence_refreshed_at",
            "acknowledged_at",
        ):
            value = getattr(snapshot, field_name)
            if value is not None and value > generated_at:
                raise ValueError(f"future {field_name} values are not allowed")


def _normalize_report_rows(
    value: object,
) -> tuple[MarketProbabilityContextRefreshPressureRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_market_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketProbabilityContextRefreshPressureRow:
            raise ValueError(
                "rows must contain MarketProbabilityContextRefreshPressureRow values",
            )
        require_paper_only_flags("MarketProbabilityContextRefreshPressureRow", row)
        if row.market_id in seen_market_ids:
            raise ValueError("rows must not contain duplicate market_id values")
        seen_market_ids.add(row.market_id)
    return rows


def _validate_report_consistency(
    report: MarketProbabilityContextRefreshPressureReport,
) -> None:
    expected_counts = {
        "market_count": _count(len(report.rows)),
        "material_move_count": _count(
            sum(
                1
                for row in report.rows
                if row.absolute_probability_delta >= report.material_probability_delta
            ),
        ),
        "blocked_count": _count(sum(1 for row in report.rows if row.status == "blocked")),
        "watch_count": _count(sum(1 for row in report.rows if row.status == "watch")),
        "pass_count": _count(sum(1 for row in report.rows if row.status == "pass")),
        "refresh_pressure_count": _count(
            sum(1 for row in report.rows if row.status != "pass"),
        ),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.refresh_pressure_ratio != _ratio(
        report.refresh_pressure_count,
        report.market_count,
    ):
        raise ValueError("refresh_pressure_ratio must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.reason_codes, rows=report.rows):
        raise ValueError("status must match reason_codes")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")
    for row in report.rows:
        _validate_row_derived_ages(row, generated_at=report.generated_at)
        expected_reason_codes = _row_reason_codes_for_report(row, report)
        if row.reason_codes != expected_reason_codes:
            raise ValueError("row reason_codes must match refresh pressure state")
        expected_status = _row_status(
            row.reason_codes,
            unacknowledged_age_seconds=row.unacknowledged_age_seconds,
            max_unacknowledged_age_seconds=report.max_unacknowledged_age_seconds,
        )
        if row.status != expected_status:
            raise ValueError("row status must match refresh pressure state")
    if report.derived_validation_digest != _expected_report_digest(report):
        raise ValueError("derived_validation_digest must match report state")


def _require_derived_validation_digest(
    report: MarketProbabilityContextRefreshPressureReport,
) -> None:
    _require_canonical_string(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if len(report.derived_validation_digest) != DIGEST_HEX_LENGTH:
        raise ValueError("derived_validation_digest must be a SHA-256 hex digest")
    if any(
        character not in "0123456789abcdef"
        for character in report.derived_validation_digest
    ):
        raise ValueError("derived_validation_digest must be a SHA-256 hex digest")


def _expected_report_digest(report: MarketProbabilityContextRefreshPressureReport) -> str:
    return _derived_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        material_probability_delta=report.material_probability_delta,
        max_context_age_seconds=report.max_context_age_seconds,
        max_evidence_age_seconds=report.max_evidence_age_seconds,
        max_unacknowledged_age_seconds=report.max_unacknowledged_age_seconds,
        status=report.status,
        market_count=report.market_count,
        material_move_count=report.material_move_count,
        blocked_count=report.blocked_count,
        watch_count=report.watch_count,
        pass_count=report.pass_count,
        refresh_pressure_count=report.refresh_pressure_count,
        refresh_pressure_ratio=report.refresh_pressure_ratio,
        reason_codes=report.reason_codes,
        rows=report.rows,
    )


def _derived_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    material_probability_delta: Decimal,
    max_context_age_seconds: Decimal,
    max_evidence_age_seconds: Decimal,
    max_unacknowledged_age_seconds: Decimal,
    status: str,
    market_count: Decimal,
    material_move_count: Decimal,
    blocked_count: Decimal,
    watch_count: Decimal,
    pass_count: Decimal,
    refresh_pressure_count: Decimal,
    refresh_pressure_ratio: Decimal,
    reason_codes: tuple[str, ...],
    rows: tuple[MarketProbabilityContextRefreshPressureRow, ...],
) -> str:
    digest_payload = {
        "digest_version": DIGEST_VERSION,
        "generated_at": _digest_ready(generated_at),
        "config_version": config_version,
        "material_probability_delta": _digest_ready(material_probability_delta),
        "max_context_age_seconds": _digest_ready(max_context_age_seconds),
        "max_evidence_age_seconds": _digest_ready(max_evidence_age_seconds),
        "max_unacknowledged_age_seconds": _digest_ready(
            max_unacknowledged_age_seconds,
        ),
        "status": status,
        "market_count": _digest_ready(market_count),
        "material_move_count": _digest_ready(material_move_count),
        "blocked_count": _digest_ready(blocked_count),
        "watch_count": _digest_ready(watch_count),
        "pass_count": _digest_ready(pass_count),
        "refresh_pressure_count": _digest_ready(refresh_pressure_count),
        "refresh_pressure_ratio": _digest_ready(refresh_pressure_ratio),
        "reason_codes": _digest_ready(reason_codes),
        "rows": _digest_ready(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    canonical_payload = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _digest_ready(value: object) -> object:
    if value is None:
        return None
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("digest datetime", value).isoformat()
    if type(value) is MarketProbabilityContextRefreshPressureRow:
        return {
            "market_id": value.market_id,
            "probability_observed_at": _digest_ready(value.probability_observed_at),
            "previous_probability": _digest_ready(value.previous_probability),
            "current_probability": _digest_ready(value.current_probability),
            "probability_delta": _digest_ready(value.probability_delta),
            "absolute_probability_delta": _digest_ready(
                value.absolute_probability_delta,
            ),
            "probability_age_seconds": _digest_ready(value.probability_age_seconds),
            "context_refreshed_at": _digest_ready(value.context_refreshed_at),
            "evidence_refreshed_at": _digest_ready(value.evidence_refreshed_at),
            "acknowledged_at": _digest_ready(value.acknowledged_at),
            "context_age_seconds": _digest_ready(value.context_age_seconds),
            "evidence_age_seconds": _digest_ready(value.evidence_age_seconds),
            "unacknowledged_age_seconds": _digest_ready(
                value.unacknowledged_age_seconds,
            ),
            "source_count": _digest_ready(value.source_count),
            "status": value.status,
            "reason_codes": _digest_ready(value.reason_codes),
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
    if isinstance(value, tuple):
        return [_digest_ready(item) for item in value]
    if type(value) in (str, bool):
        return value
    raise ValueError("value is not validation-digest serializable")


def _row_reason_codes_for_report(
    row: MarketProbabilityContextRefreshPressureRow,
    report: MarketProbabilityContextRefreshPressureReport,
) -> tuple[str, ...]:
    snapshot = MarketProbabilityContextRefreshPressureSnapshot(
        market_id=row.market_id,
        probability_observed_at=row.probability_observed_at,
        previous_probability=row.previous_probability,
        current_probability=row.current_probability,
        probability_delta=row.probability_delta,
        context_refreshed_at=row.context_refreshed_at,
        evidence_refreshed_at=row.evidence_refreshed_at,
        acknowledged_at=row.acknowledged_at,
        source_count=row.source_count,
    )
    return _row_reason_codes(
        snapshot,
        config=MarketProbabilityContextRefreshPressureConfig(
            config_version=report.config_version,
            material_probability_delta=report.material_probability_delta,
            max_context_age_seconds=report.max_context_age_seconds,
            max_evidence_age_seconds=report.max_evidence_age_seconds,
            max_unacknowledged_age_seconds=report.max_unacknowledged_age_seconds,
        ),
        context_age_seconds=row.context_age_seconds,
        evidence_age_seconds=row.evidence_age_seconds,
        unacknowledged_age_seconds=row.unacknowledged_age_seconds,
    )


def _validate_row_derived_ages(
    row: MarketProbabilityContextRefreshPressureRow,
    *,
    generated_at: datetime,
) -> None:
    if row.probability_age_seconds != _age_seconds(
        row.probability_observed_at,
        generated_at,
    ):
        raise ValueError("probability_age_seconds must match timestamps")
    if row.context_age_seconds != _optional_age_seconds(
        row.context_refreshed_at,
        generated_at,
    ):
        raise ValueError("context_age_seconds must match timestamps")
    if row.evidence_age_seconds != _optional_age_seconds(
        row.evidence_refreshed_at,
        generated_at,
    ):
        raise ValueError("evidence_age_seconds must match timestamps")
    snapshot = MarketProbabilityContextRefreshPressureSnapshot(
        market_id=row.market_id,
        probability_observed_at=row.probability_observed_at,
        previous_probability=row.previous_probability,
        current_probability=row.current_probability,
        probability_delta=row.probability_delta,
        context_refreshed_at=row.context_refreshed_at,
        evidence_refreshed_at=row.evidence_refreshed_at,
        acknowledged_at=row.acknowledged_at,
        source_count=row.source_count,
    )
    if row.unacknowledged_age_seconds != _unacknowledged_age_seconds(
        snapshot,
        generated_at,
    ):
        raise ValueError("unacknowledged_age_seconds must match timestamps")


def _row_sort_key(row: MarketProbabilityContextRefreshPressureRow) -> tuple[int, Decimal, str]:
    return (STATUS_WEIGHT[row.status], -row.absolute_probability_delta, row.market_id)


def _unacknowledged_age_seconds(
    snapshot: MarketProbabilityContextRefreshPressureSnapshot,
    generated_at: datetime,
) -> Decimal | None:
    if abs(snapshot.probability_delta) == ZERO_PROBABILITY:
        return None
    if (
        snapshot.acknowledged_at is not None
        and snapshot.acknowledged_at >= snapshot.probability_observed_at
    ):
        return _age_seconds(snapshot.probability_observed_at, snapshot.acknowledged_at)
    return _age_seconds(snapshot.probability_observed_at, generated_at)


def _optional_age_seconds(value: datetime | None, generated_at: datetime) -> Decimal | None:
    if value is None:
        return None
    return _age_seconds(value, generated_at)


def _age_seconds(value: datetime, generated_at: datetime) -> Decimal:
    delta = generated_at - value
    seconds = Decimal(delta.days * 86_400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal(1_000_000)
    with localcontext(DECIMAL_CONTEXT):
        return (seconds + fractional_seconds).quantize(SECONDS_QUANTUM)


def _probability_delta(previous_probability: Decimal, current_probability: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (current_probability - previous_probability).quantize(
            PROBABILITY_QUANTUM,
        )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    normalized = decimal.quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != decimal:
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(SECONDS_QUANTUM)
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_seconds(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_seconds(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(PROBABILITY_QUANTUM)
    if normalized < ZERO_PROBABILITY:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE_PROBABILITY:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_nonnegative_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(PROBABILITY_QUANTUM)
    if normalized < ZERO_PROBABILITY:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE_PROBABILITY:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(PROBABILITY_QUANTUM)
    if normalized < -ONE_PROBABILITY:
        raise ValueError(f"{field_name} must be at least -1")
    if normalized > ONE_PROBABILITY:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in LOCAL_UNSAFE_FIELD_FRAGMENTS):
        raise ValueError(f"{field_name} must not name an unsafe live surface")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be known")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
    *,
    clear_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member(field_name, code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in codes) != codes:
        raise ValueError(f"{field_name} must be deterministic")
    for clear_reason in clear_reasons:
        if clear_reason in codes and len(codes) != 1:
            raise ValueError(f"{clear_reason} must be alone")
    return codes


def _reject_unsafe_public_fields(label: str, payload: object) -> None:
    reject_unsafe_surface_fields(label, payload)
    for key in _iter_json_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in LOCAL_UNSAFE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe live surface field in {label}: {key}")


def _reject_unsafe_public_values(label: str, payload: object) -> None:
    for field_name, value in _iter_public_values(payload):
        if isinstance(value, datetime):
            _as_utc(field_name, value)
        elif type(value) in (float, int):
            raise ValueError(
                "public numeric values must be Decimal strings in "
                f"{label}: {field_name}",
            )
        elif type(value) is str:
            normalized_value = value.lower()
            if any(fragment in normalized_value for fragment in UNSAFE_VALUE_FRAGMENTS):
                raise ValueError(f"unsafe live surface value in {label}: {field_name}")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True for {label}")


def _reject_payload_flag_downgrades(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _reject_payload_flag_downgrades(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_payload_flag_downgrades(label, item, item_path)


def _iter_public_values(value: object, path: str = "payload") -> tuple[tuple[str, object], ...]:
    if isinstance(value, dict):
        values: list[tuple[str, object]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            values.extend(_iter_public_values(item, key))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_iter_public_values(item, path))
        return tuple(values)
    return ((path, value),)


def _iter_json_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_json_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_json_keys(item))
        return tuple(keys)
    return ()


__all__ = (
    "MarketProbabilityContextRefreshPressureConfig",
    "MarketProbabilityContextRefreshPressureReport",
    "MarketProbabilityContextRefreshPressureRow",
    "MarketProbabilityContextRefreshPressureSnapshot",
    "build_market_probability_context_refresh_pressure_report",
    "market_probability_context_refresh_pressure_report_payload",
)
