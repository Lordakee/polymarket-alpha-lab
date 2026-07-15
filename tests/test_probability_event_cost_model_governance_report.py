from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.probability_event_cost_model_governance_report import (
    ProbabilityEventCostModelGovernanceReport,
    build_probability_event_cost_model_governance_report,
    probability_event_cost_model_governance_report_digest,
    probability_event_cost_model_governance_report_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(
    *,
    taker_fee_model_ready: bool = True,
    slippage_model_ready: bool = True,
    spread_model_ready: bool = True,
    liquidity_haircut_ready: bool = True,
    settlement_cost_ready: bool = True,
    revision_digest_present: bool = True,
    threshold_backtest_ready: bool = True,
    operator_safety_ready: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventCostModelGovernanceReport:
    return build_probability_event_cost_model_governance_report(
        taker_fee_model_ready=taker_fee_model_ready,
        slippage_model_ready=slippage_model_ready,
        spread_model_ready=spread_model_ready,
        liquidity_haircut_ready=liquidity_haircut_ready,
        settlement_cost_ready=settlement_cost_ready,
        revision_digest_present=revision_digest_present,
        threshold_backtest_ready=threshold_backtest_ready,
        operator_safety_ready=operator_safety_ready,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_ready_report_requires_all_cost_model_governance_components() -> None:
    readiness_report = report()

    assert type(readiness_report) is ProbabilityEventCostModelGovernanceReport
    assert readiness_report.cost_model_governance_ready is True
    assert readiness_report.governance_band == "ready"
    assert readiness_report.blocked_reason_codes == ()
    assert readiness_report.attention_reason_codes == ()
    assert readiness_report.ready_ratio == d("1.000000")
    assert len(readiness_report.digest) == 64
    assert readiness_report.digest == probability_event_cost_model_governance_report_digest(
        readiness_report,
    )
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True


def test_blocker_report_surfaces_missing_mandatory_governance_inputs() -> None:
    readiness_report = report(
        taker_fee_model_ready=False,
        slippage_model_ready=False,
        spread_model_ready=False,
        liquidity_haircut_ready=False,
        settlement_cost_ready=False,
        revision_digest_present=False,
        threshold_backtest_ready=False,
        operator_safety_ready=False,
    )

    assert readiness_report.cost_model_governance_ready is False
    assert readiness_report.governance_band == "blocked"
    assert readiness_report.ready_ratio == d("0.000000")
    assert readiness_report.blocked_reason_codes == (
        "taker_fee_model_not_ready",
        "slippage_model_not_ready",
        "spread_model_not_ready",
        "liquidity_haircut_not_ready",
        "settlement_cost_not_ready",
        "revision_digest_missing",
        "threshold_backtest_not_ready",
        "operator_safety_not_ready",
    )
    assert readiness_report.attention_reason_codes == ()


def test_attention_report_keeps_model_complete_but_flags_governance_prerequisites() -> None:
    readiness_report = report(
        revision_digest_present=False,
        threshold_backtest_ready=False,
    )

    assert readiness_report.cost_model_governance_ready is False
    assert readiness_report.governance_band == "attention"
    assert readiness_report.ready_ratio == d("0.750000")
    assert readiness_report.blocked_reason_codes == ()
    assert readiness_report.attention_reason_codes == (
        "revision_digest_missing",
        "threshold_backtest_not_ready",
    )


def test_payload_and_digest_are_deterministic_public_safe_decimal_strings() -> None:
    first_report = report()
    second_report = report()

    first_payload = probability_event_cost_model_governance_report_payload(first_report)
    second_payload = probability_event_cost_model_governance_report_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_payload["digest"] == first_report.digest
    assert first_payload["ready_ratio"] == "1.000000"
    assert not any(type(value) is float for value in _walk_payload_values(first_payload))
    assert not any(type(value) is int for value in _walk_payload_values(first_payload))
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "market_id",
            "market_slug",
            "wallet",
            "auth",
            "order",
            "trade",
            "live",
            "execution",
            "token",
            "http://",
            "https://",
        )
    )


def test_validation_rejects_non_bool_flags_and_non_report_modes() -> None:
    with pytest.raises(ValueError, match="taker_fee_model_ready"):
        report(taker_fee_model_ready=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="revision_digest_present"):
        report(revision_digest_present="true")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        report(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        report(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report(readonly=False)
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(report(), ready_ratio=_DecimalSubclass("1.000000"))


def test_public_dataclass_is_frozen_and_payload_revalidates_tampering() -> None:
    readiness_report = report()

    with pytest.raises(FrozenInstanceError):
        readiness_report.ready_ratio = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="digest"):
        replace(readiness_report, digest="0" * 64)

    object.__setattr__(readiness_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        probability_event_cost_model_governance_report_payload(readiness_report)


def test_owned_module_has_no_io_network_live_trading_auth_or_database_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "probability_event_cost_model_governance_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "execution",
        "insert",
        "update ",
        "delete ",
        "commit",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
