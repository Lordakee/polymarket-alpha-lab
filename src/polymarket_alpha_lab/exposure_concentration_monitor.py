from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.positions import PaperPortfolio, PaperPosition
from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
GROUP_TYPES = ("team", "category")
STATUSES = ("no_open_positions", "concentration_clear", "concentration_watch")


@dataclass(frozen=True)
class PaperExposureConcentrationMonitorConfig:
    config_version: str
    event_warn_share: Decimal
    team_warn_share: Decimal
    category_warn_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "event_warn_share",
            "team_warn_share",
            "category_warn_share",
        ):
            _require_ratio_decimal(field_name, getattr(self, field_name))
        _require_report_flags(self)


@dataclass(frozen=True)
class PaperExposureConcentrationEventRow:
    condition_id: str
    position_count: Decimal
    open_size: Decimal
    cost_basis: Decimal
    share_of_total_cost_basis: Decimal | None
    warning_triggered: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_positive_count_decimal("position_count", self.position_count)
        _require_positive_decimal("open_size", self.open_size)
        _require_nonnegative_decimal("cost_basis", self.cost_basis)
        _require_optional_ratio_decimal(
            "share_of_total_cost_basis",
            self.share_of_total_cost_basis,
        )
        _require_bool("warning_triggered", self.warning_triggered)
        _require_report_flags(self)
        if self.cost_basis > self.open_size:
            raise ValueError("cost_basis must not exceed open_size")


@dataclass(frozen=True)
class PaperExposureConcentrationGroupRow:
    group_type: str
    group_value: str
    position_count: Decimal
    event_count: Decimal
    open_size: Decimal
    cost_basis: Decimal
    share_of_total_cost_basis: Decimal | None
    warning_triggered: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if self.group_type not in GROUP_TYPES:
            raise ValueError("group_type must be a known concentration group type")
        _require_canonical_string("group_value", self.group_value)
        _require_positive_count_decimal("position_count", self.position_count)
        _require_positive_count_decimal("event_count", self.event_count)
        _require_positive_decimal("open_size", self.open_size)
        _require_nonnegative_decimal("cost_basis", self.cost_basis)
        _require_optional_ratio_decimal(
            "share_of_total_cost_basis",
            self.share_of_total_cost_basis,
        )
        _require_bool("warning_triggered", self.warning_triggered)
        _require_report_flags(self)
        if self.cost_basis > self.open_size:
            raise ValueError("cost_basis must not exceed open_size")


@dataclass(frozen=True)
class PaperExposureConcentrationReport:
    generated_at: datetime
    config_version: str
    starting_cash: Decimal
    cash_balance: Decimal
    realized_pnl: Decimal
    total_cost_basis: Decimal
    open_position_count: Decimal
    event_count: Decimal
    team_count: Decimal
    category_count: Decimal
    largest_event_condition_id: str | None
    largest_event_share: Decimal | None
    largest_team_share: Decimal | None
    largest_category_share: Decimal | None
    status: str
    event_rows: tuple[PaperExposureConcentrationEventRow, ...]
    team_rows: tuple[PaperExposureConcentrationGroupRow, ...]
    category_rows: tuple[PaperExposureConcentrationGroupRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_positive_decimal("starting_cash", self.starting_cash)
        _require_nonnegative_decimal("cash_balance", self.cash_balance)
        _require_decimal("realized_pnl", self.realized_pnl)
        _require_nonnegative_decimal("total_cost_basis", self.total_cost_basis)
        for field_name in (
            "open_position_count",
            "event_count",
            "team_count",
            "category_count",
        ):
            _require_nonnegative_count_decimal(field_name, getattr(self, field_name))
        _require_optional_canonical_string(
            "largest_event_condition_id",
            self.largest_event_condition_id,
        )
        for field_name in (
            "largest_event_share",
            "largest_team_share",
            "largest_category_share",
        ):
            _require_optional_ratio_decimal(field_name, getattr(self, field_name))
        if self.status not in STATUSES:
            raise ValueError("status must be a known concentration monitor status")
        object.__setattr__(
            self,
            "event_rows",
            _normalize_typed_tuple(
                "event_rows",
                self.event_rows,
                PaperExposureConcentrationEventRow,
            ),
        )
        object.__setattr__(
            self,
            "team_rows",
            _normalize_typed_tuple(
                "team_rows",
                self.team_rows,
                PaperExposureConcentrationGroupRow,
            ),
        )
        object.__setattr__(
            self,
            "category_rows",
            _normalize_typed_tuple(
                "category_rows",
                self.category_rows,
                PaperExposureConcentrationGroupRow,
            ),
        )
        _require_report_flags(self)
        _validate_report_consistency(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _report_derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report fields")


def build_paper_exposure_concentration_report(
    portfolio: PaperPortfolio,
    *,
    config: PaperExposureConcentrationMonitorConfig,
    generated_at: datetime,
) -> PaperExposureConcentrationReport:
    if type(portfolio) is not PaperPortfolio:
        raise ValueError("portfolio must be a PaperPortfolio")
    if type(config) is not PaperExposureConcentrationMonitorConfig:
        raise ValueError("config must be a PaperExposureConcentrationMonitorConfig")
    generated_at = _as_utc("generated_at", generated_at)

    positions = portfolio.positions
    total_cost_basis = _sum_decimal(position.cost_basis for position in positions)
    event_rows = _build_event_rows(
        positions,
        total_cost_basis=total_cost_basis,
        warn_share=config.event_warn_share,
    )
    team_rows = _build_group_rows(
        _positions_with_teams(positions),
        group_type="team",
        total_cost_basis=total_cost_basis,
        warn_share=config.team_warn_share,
    )
    category_rows = _build_group_rows(
        _positions_with_categories(positions),
        group_type="category",
        total_cost_basis=total_cost_basis,
        warn_share=config.category_warn_share,
    )
    largest_event = _largest_event_row(event_rows)
    largest_event_share = (
        None if largest_event is None else largest_event.share_of_total_cost_basis
    )
    largest_team_share = _largest_group_share(team_rows)
    largest_category_share = _largest_group_share(category_rows)

    return PaperExposureConcentrationReport(
        generated_at=generated_at,
        config_version=config.config_version,
        starting_cash=portfolio.starting_cash,
        cash_balance=portfolio.cash_balance,
        realized_pnl=portfolio.realized_pnl,
        total_cost_basis=total_cost_basis,
        open_position_count=_count_decimal(len(positions)),
        event_count=_count_decimal(len(event_rows)),
        team_count=_count_decimal(len(team_rows)),
        category_count=_count_decimal(len(category_rows)),
        largest_event_condition_id=None if largest_event is None else largest_event.condition_id,
        largest_event_share=largest_event_share,
        largest_team_share=largest_team_share,
        largest_category_share=largest_category_share,
        status=_status(event_rows, team_rows, category_rows),
        event_rows=event_rows,
        team_rows=team_rows,
        category_rows=category_rows,
    )


def _build_event_rows(
    positions: tuple[PaperPosition, ...],
    *,
    total_cost_basis: Decimal,
    warn_share: Decimal,
) -> tuple[PaperExposureConcentrationEventRow, ...]:
    grouped: dict[str, list[PaperPosition]] = {}
    for position in positions:
        grouped.setdefault(position.condition_id, []).append(position)

    rows = []
    for condition_id in sorted(grouped):
        items = tuple(grouped[condition_id])
        share = _optional_ratio(_position_cost_basis(items), total_cost_basis)
        rows.append(
            PaperExposureConcentrationEventRow(
                condition_id=condition_id,
                position_count=_count_decimal(len(items)),
                open_size=_position_open_size(items),
                cost_basis=_position_cost_basis(items),
                share_of_total_cost_basis=share,
                warning_triggered=share is not None and share >= warn_share,
            ),
        )
    return tuple(sorted(rows, key=_event_row_sort_key))


def _build_group_rows(
    positions: Iterable[tuple[PaperPosition, str]],
    *,
    group_type: str,
    total_cost_basis: Decimal,
    warn_share: Decimal,
) -> tuple[PaperExposureConcentrationGroupRow, ...]:
    grouped: dict[str, list[PaperPosition]] = {}
    for position, group_value in positions:
        grouped.setdefault(group_value, []).append(position)

    rows = []
    for group_value in sorted(grouped):
        items = tuple(grouped[group_value])
        share = _optional_ratio(_position_cost_basis(items), total_cost_basis)
        rows.append(
            PaperExposureConcentrationGroupRow(
                group_type=group_type,
                group_value=group_value,
                position_count=_count_decimal(len(items)),
                event_count=_count_decimal(
                    len({position.condition_id for position in items}),
                ),
                open_size=_position_open_size(items),
                cost_basis=_position_cost_basis(items),
                share_of_total_cost_basis=share,
                warning_triggered=share is not None and share >= warn_share,
            ),
        )
    return tuple(sorted(rows, key=_group_row_sort_key))


def _positions_with_categories(
    positions: tuple[PaperPosition, ...],
) -> tuple[tuple[PaperPosition, str], ...]:
    items: list[tuple[PaperPosition, str]] = []
    for position in positions:
        for category in position.risk_tags:
            items.append((position, category))
    return tuple(items)


def _positions_with_teams(
    positions: tuple[PaperPosition, ...],
) -> tuple[tuple[PaperPosition, str], ...]:
    return tuple((position, position.strategy_type) for position in positions)


def _largest_event_row(
    rows: tuple[PaperExposureConcentrationEventRow, ...],
) -> PaperExposureConcentrationEventRow | None:
    if not rows:
        return None
    return rows[0]


def _largest_group_share(
    rows: tuple[PaperExposureConcentrationGroupRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    shares = tuple(
        row.share_of_total_cost_basis
        for row in rows
        if row.share_of_total_cost_basis is not None
    )
    if not shares:
        return None
    return max(shares)


def paper_exposure_concentration_monitor_payload(
    report: PaperExposureConcentrationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is PaperExposureConcentrationReport:
        _require_report_flags(report)
        if report.derived_validation_digest != _report_derived_validation_digest(report):
            raise ValueError("derived_validation_digest must match report fields")
        payload = _report_public_payload(report, include_digest=True)
        reject_unsafe_surface_fields("exposure concentration monitor payload", payload)
        return payload
    if type(report) is dict:
        payload = json_ready_no_floats(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_public_payload_flags(payload)
        reject_unsafe_surface_fields("exposure concentration monitor payload", payload)
        digest = payload.get("derived_validation_digest")
        _require_sha256_digest("derived_validation_digest", digest)
        if digest != _public_payload_derived_validation_digest(payload):
            raise ValueError("derived_validation_digest must match public payload")
        return payload
    raise ValueError("report must be a PaperExposureConcentrationReport")


def _status(
    event_rows: tuple[PaperExposureConcentrationEventRow, ...],
    team_rows: tuple[PaperExposureConcentrationGroupRow, ...],
    category_rows: tuple[PaperExposureConcentrationGroupRow, ...],
) -> str:
    if not event_rows and not team_rows and not category_rows:
        return "no_open_positions"
    if any(row.warning_triggered for row in (*event_rows, *team_rows, *category_rows)):
        return "concentration_watch"
    return "concentration_clear"


def _event_row_sort_key(
    row: PaperExposureConcentrationEventRow,
) -> tuple[Decimal, str]:
    return (-row.cost_basis, row.condition_id)


def _group_row_sort_key(
    row: PaperExposureConcentrationGroupRow,
) -> tuple[str, str]:
    return (row.group_type, row.group_value)


def _position_open_size(positions: tuple[PaperPosition, ...]) -> Decimal:
    return _sum_decimal(position.open_size for position in positions)


def _position_cost_basis(positions: tuple[PaperPosition, ...]) -> Decimal:
    return _sum_decimal(position.cost_basis for position in positions)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        _require_decimal("value", value)
        total += value
    return total


def _optional_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator <= ZERO:
        return None
    return (numerator / denominator).quantize(RATIO_QUANTUM)


def _validate_report_consistency(report: PaperExposureConcentrationReport) -> None:
    if report.open_position_count == ZERO:
        if report.total_cost_basis != ZERO:
            raise ValueError("total_cost_basis must be zero when no positions are open")
        if report.status != "no_open_positions":
            raise ValueError("empty exposure concentration report status must match")
        if report.event_rows or report.team_rows or report.category_rows:
            raise ValueError("empty exposure concentration report cannot include rows")
        if (
            report.largest_event_condition_id is not None
            or report.largest_event_share is not None
            or report.largest_team_share is not None
            or report.largest_category_share is not None
        ):
            raise ValueError("empty exposure concentration report cannot include largest metrics")
        return

    if report.event_count != _count_decimal(len(report.event_rows)):
        raise ValueError("event_count must match event_rows length")
    if report.team_count != _count_decimal(len(report.team_rows)):
        raise ValueError("team_count must match team_rows length")
    if report.category_count != _count_decimal(len(report.category_rows)):
        raise ValueError("category_count must match category_rows length")
    if report.total_cost_basis != _sum_decimal(row.cost_basis for row in report.event_rows):
        raise ValueError("total_cost_basis must match event row cost_basis")
    event_positions = _sum_decimal(row.position_count for row in report.event_rows)
    if report.open_position_count != event_positions:
        raise ValueError("open_position_count must match event row position counts")
    largest_event = _largest_event_row(report.event_rows)
    if largest_event is None:
        raise ValueError("largest event row is required when positions are open")
    if report.largest_event_condition_id != largest_event.condition_id:
        raise ValueError("largest_event_condition_id must match event rows")
    if report.largest_event_share != largest_event.share_of_total_cost_basis:
        raise ValueError("largest_event_share must match event rows")
    if report.largest_team_share != _largest_group_share(report.team_rows):
        raise ValueError("largest_team_share must match team rows")
    if report.largest_category_share != _largest_group_share(report.category_rows):
        raise ValueError("largest_category_share must match category rows")
    if report.status == "no_open_positions":
        raise ValueError("status cannot be no_open_positions when positions are open")
    warnings_present = any(
        row.warning_triggered
        for row in (*report.event_rows, *report.team_rows, *report.category_rows)
    )
    if warnings_present and report.status != "concentration_watch":
        raise ValueError("status must be concentration_watch when warnings exist")
    if not warnings_present and report.status != "concentration_clear":
        raise ValueError("status must be concentration_clear when warnings are absent")


def _normalize_typed_tuple(
    field_name: str,
    values: tuple[object, ...],
    expected_type: type,
) -> tuple[object, ...]:
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for item in items:
        if type(item) is not expected_type:
            raise ValueError(f"{field_name} must contain {expected_type.__name__} values")
    return items


def _report_public_payload(
    report: PaperExposureConcentrationReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    values = asdict(report)
    values.pop("cash_balance", None)
    if not include_digest:
        values.pop("derived_validation_digest", None)
    payload = json_ready_no_floats(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _report_derived_validation_digest(
    report: PaperExposureConcentrationReport,
) -> str:
    return _public_payload_derived_validation_digest(
        _report_public_payload(report, include_digest=False),
    )


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded_payload = json.dumps(
        digest_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_optional_canonical_string(field_name: str, value: str | None) -> None:
    if value is None:
        return
    _require_canonical_string(field_name, value)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")


def _require_positive_count_decimal(field_name: str, value: Decimal) -> None:
    _require_nonnegative_count_decimal(field_name, value)
    if value == ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_ratio_decimal(field_name: str, value: Decimal) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value > Decimal("1"):
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_optional_ratio_decimal(field_name: str, value: Decimal | None) -> None:
    if value is None:
        return
    _require_ratio_decimal(field_name, value)


def _require_report_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if len(value) != 64 or value != value.lower():
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")


__all__ = (
    "PaperExposureConcentrationMonitorConfig",
    "PaperExposureConcentrationEventRow",
    "PaperExposureConcentrationGroupRow",
    "PaperExposureConcentrationReport",
    "build_paper_exposure_concentration_report",
    "paper_exposure_concentration_monitor_payload",
)
