from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.probability_event_edge_stability_over_time_report import (
    DEFAULT_PROBABILITY_EVENT_EDGE_STABILITY_OVER_TIME_CONFIG_VERSION,
    ProbabilityEventEdgeStabilityOverTimeInput,
    ProbabilityEventEdgeStabilityOverTimeReport,
    build_probability_event_edge_stability_over_time_report,
    probability_event_edge_stability_over_time_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_edge_stability_over_time_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: object) -> ProbabilityEventEdgeStabilityOverTimeReport:
    values: dict[str, object] = {
        "initial_edge_probability": d("0.120000"),
        "current_edge_probability": d("0.100000"),
        "edge_age_hours": d("36.000000"),
        "market_move_probability": d("0.015000"),
        "stability_threshold_probability": d("0.050000"),
    }
    values.update(overrides)
    return build_probability_event_edge_stability_over_time_report(**values)


def test_stable_edge_report_uses_decimal_inputs_and_public_payload() -> None:
    report = build_report()
    payload = probability_event_edge_stability_over_time_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert type(report) is ProbabilityEventEdgeStabilityOverTimeReport
    assert report.edge_stability_status == "stable"
    assert report.edge_drift_probability == d("0.020000")
    assert report.reason_codes == ("edge_stability_stable",)
    assert report.manual_next_step == "continue_manual_watch"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.public_payload == payload
    assert payload == probability_event_edge_stability_over_time_payload(report)
    assert payload["edge_stability_status"] == "stable"
    assert payload["edge_drift_probability"] == "0.020000"
    assert payload["payload_digest"] == report.payload_digest
    assert len(report.payload_digest) == 64
    assert encoded == json.dumps(report.public_payload, sort_keys=True)
    assert not any(type(value) in (Decimal, float, int) for value in walk_values(payload))


def test_watch_and_block_statuses_reflect_drift_market_move_and_age() -> None:
    watch_report = build_report(
        current_edge_probability=d("0.040000"),
        market_move_probability=d("0.020000"),
    )
    block_report = build_report(
        current_edge_probability=d("0.010000"),
        edge_age_hours=d("96.000000"),
        market_move_probability=d("0.100000"),
    )

    assert watch_report.edge_stability_status == "watch"
    assert watch_report.edge_drift_probability == d("0.080000")
    assert watch_report.reason_codes == (
        "edge_stability_watch",
        "edge_drift_above_threshold",
    )
    assert watch_report.manual_next_step == "manual_review_edge_drift"

    assert block_report.edge_stability_status == "block"
    assert block_report.edge_drift_probability == d("0.110000")
    assert block_report.reason_codes == (
        "edge_stability_block",
        "edge_drift_above_threshold",
        "edge_stale_over_time",
        "market_move_above_threshold",
    )
    assert block_report.manual_next_step == "manual_rebuild_required"


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("initial_edge_probability", 1),
        ("current_edge_probability", 0.1),
        ("edge_age_hours", "36.000000"),
        ("market_move_probability", _DecimalSubclass("0.015000")),
        ("stability_threshold_probability", d("1.500000")),
    ),
)
def test_inputs_require_exact_decimal_probability_values(
    field_name: str,
    value: object,
) -> None:
    values: dict[str, object] = {
        "initial_edge_probability": d("0.120000"),
        "current_edge_probability": d("0.100000"),
        "edge_age_hours": d("36.000000"),
        "market_move_probability": d("0.015000"),
        "stability_threshold_probability": d("0.050000"),
    }
    values[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        ProbabilityEventEdgeStabilityOverTimeInput(**values)


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ProbabilityEventEdgeStabilityOverTimeInput(
            initial_edge_probability=d("0.120000"),
            current_edge_probability=d("0.100000"),
            edge_age_hours=d("36.000000"),
            market_move_probability=d("0.015000"),
            stability_threshold_probability=d("0.050000"),
            paper_only=False,
        )

    report = build_report()
    with pytest.raises(FrozenInstanceError):
        report.edge_stability_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="payload_digest"):
        replace(report, payload_digest="not-a-digest")


def test_module_is_report_only_and_exposes_no_io_or_execution_surface() -> None:
    import polymarket_alpha_lab.probability_event_edge_stability_over_time_report as module

    source = MODULE_PATH.read_text(encoding="utf-8").lower()

    assert module.__all__ == (
        "DEFAULT_PROBABILITY_EVENT_EDGE_STABILITY_OVER_TIME_CONFIG_VERSION",
        "ProbabilityEventEdgeStabilityOverTimeInput",
        "ProbabilityEventEdgeStabilityOverTimeReport",
        "build_probability_event_edge_stability_over_time_report",
        "probability_event_edge_stability_over_time_payload",
    )
    assert DEFAULT_PROBABILITY_EVENT_EDGE_STABILITY_OVER_TIME_CONFIG_VERSION.endswith("-v0")
    assert all(
        field.default is True
        for public_type in (
            ProbabilityEventEdgeStabilityOverTimeInput,
            ProbabilityEventEdgeStabilityOverTimeReport,
        )
        for field in fields(public_type)
        if field.name in {"paper_only", "report_only", "readonly"}
    )
    assert all(
        forbidden not in source
        for forbidden in (
            "requests",
            "urllib",
            "httpx",
            "aiohttp",
            "socket",
            "subprocess",
            "pathlib",
            "open(",
            "connect(",
            "execute(",
            "commit(",
            "rollback(",
            "send(",
            "submit(",
            "live",
            "auth",
            "wallet",
            "keys",
            "signing",
            "execution",
        )
    )


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_values(item))
    else:
        values.append(value)
    return tuple(values)
