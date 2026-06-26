"""Pure row codec for persisted local observability trends reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.local_observability_trends import (
    LocalObservabilityTrendsReport,
)
from polymarket_alpha_lab.nav_risk_trend import NAV_RISK_TREND_STATUSES
from polymarket_alpha_lab.outcome_freshness import OUTCOME_FRESHNESS_STATUSES
from polymarket_alpha_lab.paper_trade_cost_trend import COST_TREND_STATUSES
from polymarket_alpha_lab.strategy_evidence import SNAPSHOT_STATUSES


__all__ = (
    "LocalObservabilityTrendsDbRow",
    "local_observability_trends_report_from_db_row",
    "local_observability_trends_report_to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "strategy_evidence_snapshot_count",
    "strategy_evidence_latest_status",
    "outcome_freshness_status",
    "outcome_report_count",
    "nav_risk_status",
    "nav_risk_report_count",
    "paper_trade_cost_status",
    "paper_trade_cost_report_count",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class LocalObservabilityTrendsDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    strategy_evidence_snapshot_count: int
    strategy_evidence_latest_status: str | None
    outcome_freshness_status: str
    outcome_report_count: int
    nav_risk_status: str
    nav_risk_report_count: int
    paper_trade_cost_status: str
    paper_trade_cost_report_count: int
    payload_json: dict[str, object]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "strategy_evidence_snapshot_count",
            "outcome_report_count",
            "nav_risk_report_count",
            "paper_trade_cost_report_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_optional_member(
            "strategy_evidence_latest_status",
            self.strategy_evidence_latest_status,
            SNAPSHOT_STATUSES,
        )
        _validate_strategy_evidence_status_count_pair(
            self.strategy_evidence_snapshot_count,
            self.strategy_evidence_latest_status,
        )
        _require_member(
            "outcome_freshness_status",
            self.outcome_freshness_status,
            OUTCOME_FRESHNESS_STATUSES,
        )
        _require_member("nav_risk_status", self.nav_risk_status, NAV_RISK_TREND_STATUSES)
        _require_member(
            "paper_trade_cost_status",
            self.paper_trade_cost_status,
            COST_TREND_STATUSES,
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _validate_json_hard_flags(self.payload_json, "payload_json")
        _validate_materialized_fields_match_payload(self)
        _validate_payload_recovers_to_expected_row(self)
        _require_hard_flags("DB row", self)


def local_observability_trends_report_to_db_row(
    report: LocalObservabilityTrendsReport,
) -> LocalObservabilityTrendsDbRow:
    if type(report) is not LocalObservabilityTrendsReport:
        raise ValueError("report must be a LocalObservabilityTrendsReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return LocalObservabilityTrendsDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        strategy_evidence_snapshot_count=(
            report.strategy_evidence_trend.snapshot_report_count
        ),
        strategy_evidence_latest_status=report.strategy_evidence_trend.latest_status,
        outcome_freshness_status=report.outcome_freshness.status,
        outcome_report_count=report.outcome_freshness.outcome_report_count,
        nav_risk_status=report.nav_risk_trend.status,
        nav_risk_report_count=report.nav_risk_trend.nav_risk_report_count,
        paper_trade_cost_status=report.paper_trade_cost_trend.status,
        paper_trade_cost_report_count=(
            report.paper_trade_cost_trend.cost_audit_report_count
        ),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def local_observability_trends_report_from_db_row(
    row: LocalObservabilityTrendsDbRow,
) -> LocalObservabilityTrendsReport:
    if type(row) is not LocalObservabilityTrendsDbRow:
        raise ValueError("row must be a LocalObservabilityTrendsDbRow")
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    _validate_materialized_fields_match_payload(row)
    try:
        report = from_jsonable(LocalObservabilityTrendsReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid local observability trends report: {exc}",
        ) from exc
    if type(report) is not LocalObservabilityTrendsReport:
        raise ValueError(
            "payload_json must recover a LocalObservabilityTrendsReport",
        )
    _validate_report_tree(report)
    expected_row = local_observability_trends_report_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def _validate_report_tree(report: LocalObservabilityTrendsReport) -> None:
    _validate_hard_flags_tree(report, "report")


def _validate_hard_flags_tree(value: Any, field_name: str) -> None:
    if _has_hard_flag(value):
        _require_hard_flags(field_name, value)
    if is_dataclass(value) and not isinstance(value, type):
        for item_field in fields(value):
            _validate_hard_flags_tree(
                getattr(value, item_field.name),
                f"{field_name}.{item_field.name}",
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_hard_flags_tree(item, f"{field_name}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_hard_flags_tree(item, f"{field_name}.{index}")


def _has_hard_flag(value: Any) -> bool:
    return any(
        hasattr(value, flag_name)
        for flag_name in ("paper_only", "report_only", "readonly")
    )


def _validate_row_matches_payload(
    row: LocalObservabilityTrendsDbRow,
    expected: LocalObservabilityTrendsDbRow,
) -> None:
    for field_name in _MATERIALIZED_FIELDS:
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_materialized_fields_match_payload(
    row: LocalObservabilityTrendsDbRow,
) -> None:
    payload_json = row.payload_json
    strategy_evidence_trend = _require_json_object(
        "payload_json strategy_evidence_trend",
        payload_json.get("strategy_evidence_trend"),
    )
    outcome_freshness = _require_json_object(
        "payload_json outcome_freshness",
        payload_json.get("outcome_freshness"),
    )
    nav_risk_trend = _require_json_object(
        "payload_json nav_risk_trend",
        payload_json.get("nav_risk_trend"),
    )
    paper_trade_cost_trend = _require_json_object(
        "payload_json paper_trade_cost_trend",
        payload_json.get("paper_trade_cost_trend"),
    )
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at"),
        "config_version": payload_json.get("config_version"),
        "strategy_evidence_snapshot_count": strategy_evidence_trend.get(
            "snapshot_report_count",
        ),
        "strategy_evidence_latest_status": strategy_evidence_trend.get(
            "latest_status",
        ),
        "outcome_freshness_status": outcome_freshness.get("status"),
        "outcome_report_count": outcome_freshness.get("outcome_report_count"),
        "nav_risk_status": nav_risk_trend.get("status"),
        "nav_risk_report_count": nav_risk_trend.get("nav_risk_report_count"),
        "paper_trade_cost_status": paper_trade_cost_trend.get("status"),
        "paper_trade_cost_report_count": paper_trade_cost_trend.get(
            "cost_audit_report_count",
        ),
        "paper_only": payload_json.get("paper_only"),
        "report_only": payload_json.get("report_only"),
        "readonly": payload_json.get("readonly"),
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at.isoformat(),
        "config_version": row.config_version,
        "strategy_evidence_snapshot_count": row.strategy_evidence_snapshot_count,
        "strategy_evidence_latest_status": row.strategy_evidence_latest_status,
        "outcome_freshness_status": row.outcome_freshness_status,
        "outcome_report_count": row.outcome_report_count,
        "nav_risk_status": row.nav_risk_status,
        "nav_risk_report_count": row.nav_risk_report_count,
        "paper_trade_cost_status": row.paper_trade_cost_status,
        "paper_trade_cost_report_count": row.paper_trade_cost_report_count,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name in _MATERIALIZED_FIELDS:
        if actual_values[field_name] != expected_values[field_name]:
            raise ValueError(f"{field_name} must match payload_json")


def _validate_payload_recovers_to_expected_row(
    row: LocalObservabilityTrendsDbRow,
) -> None:
    try:
        report = from_jsonable(LocalObservabilityTrendsReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid local observability trends report: {exc}",
        ) from exc
    if type(report) is not LocalObservabilityTrendsReport:
        raise ValueError("payload_json must recover a LocalObservabilityTrendsReport")
    _validate_report_tree(report)
    expected_payload_json = _json_ready(asdict(report))
    if row.payload_json != expected_payload_json:
        raise ValueError("payload_json must match canonical recovered report payload")


def _require_json_object(field_name: str, value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return value


def _report_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("local observability trends DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    return {key: _json_ready(item) for key, item in value.items()}


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_json_floats(item)


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if isinstance(value, dict):
        hard_flags = ("paper_only", "report_only", "readonly")
        if any(flag_name in value for flag_name in hard_flags):
            for flag_name in hard_flags:
                if value.get(flag_name) is not True:
                    raise ValueError(f"{field_name} {flag_name} must be present and true")
        for key, item in value.items():
            _validate_json_hard_flags(item, f"{field_name}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_json_hard_flags(item, f"{field_name}.{index}")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known status")


def _require_optional_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value is None:
        return
    _require_member(field_name, value, allowed_values)


def _validate_strategy_evidence_status_count_pair(
    snapshot_count: int,
    latest_status: str | None,
) -> None:
    if snapshot_count == 0 and latest_status is not None:
        raise ValueError(
            "strategy_evidence_latest_status must be null when "
            "strategy_evidence_snapshot_count is zero",
        )
    if snapshot_count > 0 and latest_status is None:
        raise ValueError(
            "strategy_evidence_latest_status must be present when "
            "strategy_evidence_snapshot_count is positive",
        )


def _require_hard_flags(field_name: str, value: Any) -> None:
    if value.paper_only is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if value.report_only is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if value.readonly is not True:
        raise ValueError(f"{field_name} readonly must be True")
