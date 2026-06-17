"""Append-only local JSONL log for Strategy Risk Audit reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)

__all__ = ("PaperStrategyRiskAuditLog",)


@dataclass(frozen=True)
class PaperStrategyRiskAuditLog:
    """Append/read local Strategy Risk Audit JSONL reports."""

    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: PaperStrategyRiskAuditReport) -> None:
        if type(report) is not PaperStrategyRiskAuditReport:
            raise ValueError("report must be a PaperStrategyRiskAuditReport")
        validated = _validate_report_tree(report)
        line = (
            json.dumps(
                _json_ready(asdict(validated)),
                allow_nan=False,
                sort_keys=True,
            )
            + "\n"
        )
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    @staticmethod
    def read(path: Path | str) -> tuple[PaperStrategyRiskAuditReport, ...]:
        """Read local Strategy Risk Audit JSONL reports back into dataclasses."""

        target = Path(path)
        records: list[PaperStrategyRiskAuditReport] = []
        with target.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"strategy risk audit log line {line_number} "
                        f"is not valid JSON: {exc}",
                    ) from exc
                try:
                    records.append(_report_from_jsonable(row))
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValueError(
                        f"strategy risk audit log line {line_number} "
                        f"is not a valid report: {exc}",
                    ) from exc
        return tuple(records)


def _validate_report_tree(
    report: PaperStrategyRiskAuditReport,
) -> PaperStrategyRiskAuditReport:
    gate_results = tuple(
        PaperStrategyRiskAuditGateResult(
            gate_name=gate.gate_name,
            status=gate.status,
            message=gate.message,
            observed_value=gate.observed_value,
            threshold=gate.threshold,
        )
        for gate in report.gate_results
    )
    return PaperStrategyRiskAuditReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        gate_count=report.gate_count,
        pass_count=report.pass_count,
        fail_count=report.fail_count,
        incomplete_count=report.incomplete_count,
        gate_results=gate_results,
        paper_only=report.paper_only,
        report_only=report.report_only,
    )


def _report_from_jsonable(row: Any) -> PaperStrategyRiskAuditReport:
    if not isinstance(row, dict):
        raise ValueError("report row must be a JSON object")
    return PaperStrategyRiskAuditReport(
        generated_at=_datetime_from_jsonable(row["generated_at"]),
        config_version=row["config_version"],
        status=row["status"],
        gate_count=_int_from_jsonable("gate_count", row["gate_count"]),
        pass_count=_int_from_jsonable("pass_count", row["pass_count"]),
        fail_count=_int_from_jsonable("fail_count", row["fail_count"]),
        incomplete_count=_int_from_jsonable(
            "incomplete_count",
            row["incomplete_count"],
        ),
        gate_results=_gate_results_from_jsonable(row["gate_results"]),
        paper_only=row["paper_only"],
        report_only=row["report_only"],
    )


def _gate_results_from_jsonable(
    value: Any,
) -> tuple[PaperStrategyRiskAuditGateResult, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, list):
        raise ValueError("gate_results must be a JSON array")
    return tuple(_gate_from_jsonable(item) for item in value)


def _gate_from_jsonable(row: Any) -> PaperStrategyRiskAuditGateResult:
    if not isinstance(row, dict):
        raise ValueError("gate row must be a JSON object")
    gate_name = row["gate_name"]
    return PaperStrategyRiskAuditGateResult(
        gate_name=gate_name,
        status=row["status"],
        message=row["message"],
        observed_value=_audit_value_from_jsonable(
            gate_name,
            row.get("observed_value"),
        ),
        threshold=_audit_value_from_jsonable(gate_name, row.get("threshold")),
    )


def _audit_value_from_jsonable(
    gate_name: str,
    value: Any,
) -> Decimal | int | str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("audit value must not be a bool")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        raise ValueError("audit value must not be a float")
    if isinstance(value, str):
        if gate_name != "nav_drawdown":
            return value
        try:
            decimal = Decimal(value)
        except InvalidOperation:
            return value
        return decimal
    raise ValueError("audit value must be a Decimal, int, string, or None")


def _datetime_from_jsonable(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("generated_at must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("generated_at must be an ISO datetime string") from exc
    return _as_utc(parsed)


def _int_from_jsonable(field_name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    return value


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
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
    raise ValueError("strategy risk audit log values must be JSON serializable")


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError("path is required")
    try:
        path = Path(value)
    except TypeError as exc:
        raise ValueError("path must be path-like") from exc
    if path.exists() and path.is_dir():
        raise ValueError("path must be a file path")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    for parent in (path.parent, *path.parent.parents):
        if parent.exists():
            if not parent.is_dir():
                raise ValueError("path parent must be a directory")
            return
