from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re

import pytest

from polymarket_alpha_lab.strategy_risk_audit import (
    PaperStrategyRiskAuditGateResult,
    PaperStrategyRiskAuditReport,
)
from polymarket_alpha_lab.strategy_risk_audit_db_row import (
    PaperStrategyRiskAuditReportDbRow,
    strategy_risk_audit_report_from_db_row,
    strategy_risk_audit_report_to_db_row,
)


GENERATED_AT = datetime(2026, 6, 20, 19, 0, tzinfo=UTC)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
GATE_NAMES = (
    "paper_history",
    "settlement_evidence",
    "forecast_quality",
    "cost_discipline",
    "nav_drawdown",
    "open_exposure",
)


def _canonical_payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class StrategyRiskAuditReportSubclass(PaperStrategyRiskAuditReport):
    pass


def _gate(
    gate_name: str,
    *,
    status: str = "pass",
    observed_value: Decimal | int | str | None = None,
    threshold: Decimal | int | str | None = None,
) -> PaperStrategyRiskAuditGateResult:
    return PaperStrategyRiskAuditGateResult(
        gate_name=gate_name,
        status=status,
        message=f"{gate_name} message",
        observed_value=observed_value,
        threshold=threshold,
    )


def _report(
    *,
    status: str = "audit_ready",
    gate_statuses: tuple[str, ...] = ("pass", "pass", "pass", "pass", "pass", "pass"),
    decimal_gate_value: bool = False,
) -> PaperStrategyRiskAuditReport:
    gate_results = tuple(
        _gate(
            gate_name,
            status=gate_status,
            observed_value=(
                Decimal("0.050000")
                if decimal_gate_value and gate_name == "nav_drawdown"
                else f"{gate_name}=observed"
            ),
            threshold=(
                Decimal("0.100000")
                if decimal_gate_value and gate_name == "nav_drawdown"
                else f"{gate_name}=threshold"
            ),
        )
        for gate_name, gate_status in zip(GATE_NAMES, gate_statuses, strict=True)
    )
    return PaperStrategyRiskAuditReport(
        generated_at=GENERATED_AT,
        config_version="strategy-risk-audit-v0",
        status=status,
        gate_count=len(gate_results),
        pass_count=sum(1 for gate in gate_results if gate.status == "pass"),
        fail_count=sum(1 for gate in gate_results if gate.status == "fail"),
        incomplete_count=sum(1 for gate in gate_results if gate.status == "incomplete"),
        gate_results=gate_results,
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("strategy risk audit DB JSON must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_strategy_risk_audit_db_row_serializes_payload_and_round_trips() -> None:
    report = _report()

    row = strategy_risk_audit_report_to_db_row(report)

    assert type(row) is PaperStrategyRiskAuditReportDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "strategy-risk-audit-v0"
    assert row.status == "audit_ready"
    assert row.gate_count == 6
    assert row.pass_count == 6
    assert row.fail_count == 0
    assert row.incomplete_count == 0
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-20T19:00:00+00:00"
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert "readonly" not in row.payload_json
    assert row.gate_results_json == row.payload_json["gate_results"]
    _assert_no_floats(row.gate_results_json)
    _assert_no_floats(row.payload_json)

    assert strategy_risk_audit_report_from_db_row(row) == report


def test_strategy_risk_audit_db_row_serializes_decimal_gate_values_as_strings() -> None:
    report = _report(decimal_gate_value=True)

    row = strategy_risk_audit_report_to_db_row(report)
    recovered = strategy_risk_audit_report_from_db_row(row)

    assert row.gate_results_json[4]["observed_value"] == "0.050000"
    assert row.gate_results_json[4]["threshold"] == "0.100000"
    assert recovered.gate_results[4].observed_value == "0.050000"
    assert recovered.gate_results[4].threshold == "0.100000"


def test_strategy_risk_audit_db_row_hash_uses_canonical_payload_json() -> None:
    row = strategy_risk_audit_report_to_db_row(_report())
    mutated_payload = {**row.payload_json, "extra_hash_material": "changed"}

    with pytest.raises(ValueError, match="report_sha256 must match payload_json"):
        replace(row, payload_json=mutated_payload)


def test_strategy_risk_audit_db_row_rejects_direct_scalar_payload_mismatch() -> None:
    row = strategy_risk_audit_report_to_db_row(_report())
    mutated_payload = {**row.payload_json, "config_version": "strategy-risk-audit-v1"}

    with pytest.raises(ValueError, match="config_version must match payload_json"):
        PaperStrategyRiskAuditReportDbRow(
            report_sha256=_canonical_payload_sha256(mutated_payload),
            generated_at=row.generated_at,
            config_version=row.config_version,
            status=row.status,
            gate_count=row.gate_count,
            pass_count=row.pass_count,
            fail_count=row.fail_count,
            incomplete_count=row.incomplete_count,
            gate_results_json=row.gate_results_json,
            payload_json=mutated_payload,
        )


def test_strategy_risk_audit_db_row_rejects_wrong_report_type_and_subclasses() -> None:
    report = _report()
    subclass = StrategyRiskAuditReportSubclass(**report.__dict__)

    with pytest.raises(ValueError, match="PaperStrategyRiskAuditReport"):
        strategy_risk_audit_report_to_db_row(object())
    with pytest.raises(ValueError, match="PaperStrategyRiskAuditReport"):
        strategy_risk_audit_report_to_db_row(subclass)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only"))
def test_strategy_risk_audit_db_row_rejects_false_payload_report_flags(
    flag_name: str,
) -> None:
    row = strategy_risk_audit_report_to_db_row(_report())
    payload = {**row.payload_json, flag_name: False}

    with pytest.raises(ValueError, match=flag_name):
        replace(row, payload_json=payload)


def test_strategy_risk_audit_db_row_requires_row_level_readonly() -> None:
    row = strategy_risk_audit_report_to_db_row(_report())

    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)


def test_strategy_risk_audit_db_row_rejects_recursive_float_json_values() -> None:
    row = strategy_risk_audit_report_to_db_row(_report())

    with pytest.raises(ValueError, match="gate_results_json"):
        replace(
            row,
            gate_results_json=[
                {**row.gate_results_json[0], "observed_value": 0.1},
                *row.gate_results_json[1:],
            ],
        )

    with pytest.raises(ValueError, match="payload_json"):
        replace(
            row,
            payload_json={
                **row.payload_json,
                "gate_results": [
                    {**row.gate_results_json[0], "threshold": 0.1},
                    *row.gate_results_json[1:],
                ],
            },
        )


def test_strategy_risk_audit_db_row_rejects_materialized_payload_mismatches() -> None:
    row = strategy_risk_audit_report_to_db_row(_report())

    with pytest.raises(ValueError, match="status must match payload_json"):
        strategy_risk_audit_report_from_db_row(
            replace(row, status="blocked_by_risk", pass_count=5, fail_count=1),
        )
    with pytest.raises(ValueError, match="gate_results_json must match payload_json"):
        replace(row, gate_results_json=list(reversed(row.gate_results_json)))


def test_strategy_risk_audit_db_row_is_frozen_and_validates_shape() -> None:
    row = strategy_risk_audit_report_to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.status = "blocked_by_risk"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_sha256"):
        replace(row, report_sha256="not-a-sha")
    with pytest.raises(ValueError, match="status"):
        replace(row, status="unknown")
    with pytest.raises(ValueError, match="gate_count"):
        replace(row, gate_count=-1)
    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json=[])
