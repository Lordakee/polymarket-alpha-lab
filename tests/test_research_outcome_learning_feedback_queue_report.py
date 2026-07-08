from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_outcome_learning_feedback_queue_report"


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_RESEARCH_OUTCOME_LEARNING_FEEDBACK_QUEUE_CONFIG_VERSION,
        "watch_feedback_pressure_threshold": d("0.350000"),
        "block_feedback_pressure_threshold": d("0.700000"),
        "aggregate_forecast_error_weight": d("0.300000"),
        "evidence_miss_weight": d("0.250000"),
        "source_reliability_drift_weight": d("0.200000"),
        "cost_friction_miss_weight": d("0.150000"),
        "team_calibration_drift_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchOutcomeLearningFeedbackQueueConfig(**values)


def item(**overrides: object):
    module = api()
    values = {
        "learning_key": "steady_baseline",
        "outcome_count": d("20"),
        "aggregate_forecast_error": d("0.100000"),
        "evidence_miss_score": d("0.050000"),
        "source_reliability_drift": d("0.040000"),
        "cost_friction_miss_score": d("0.030000"),
        "team_calibration_drift": d("0.020000"),
        "reason_codes": ("outcome_reviewed",),
    }
    values.update(overrides)
    return module.ResearchOutcomeLearningFeedbackItem(**values)


def report(rows: tuple[object, ...], *, cfg: object | None = None):
    module = api()
    return module.build_research_outcome_learning_feedback_queue_report(
        rows,
        config=config() if cfg is None else cfg,
    )


def public_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_public_json_scalars(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected raw Decimal value {value!r}")
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for key, nested in value.items():
            assert type(key) is str
            assert_public_json_scalars(nested)
    elif isinstance(value, list):
        for nested in value:
            assert_public_json_scalars(nested)


def test_queues_outcome_learning_feedback_as_pass_watch_and_block() -> None:
    module = api()

    feedback_report = report(
        (
            item(),
            item(
                learning_key="drifting_sources",
                outcome_count=d("12"),
                aggregate_forecast_error=d("0.500000"),
                evidence_miss_score=d("0.400000"),
                source_reliability_drift=d("0.300000"),
                cost_friction_miss_score=d("0.200000"),
                team_calibration_drift=d("0.100000"),
                reason_codes=("source_check_changed",),
            ),
            item(
                learning_key="broken_evidence",
                outcome_count=d("8"),
                aggregate_forecast_error=d("0.900000"),
                evidence_miss_score=d("0.800000"),
                source_reliability_drift=d("0.700000"),
                cost_friction_miss_score=d("0.600000"),
                team_calibration_drift=d("0.500000"),
                reason_codes=("postmortem_complete",),
            ),
        ),
    )

    assert type(feedback_report) is module.ResearchOutcomeLearningFeedbackQueueReport
    assert feedback_report.status == "block"
    assert feedback_report.item_count == d("3")
    assert feedback_report.pass_count == d("1")
    assert feedback_report.watch_count == d("1")
    assert feedback_report.block_count == d("1")
    assert feedback_report.queued_feedback_count == d("2")
    assert feedback_report.max_feedback_pressure == d("0.750000")
    assert tuple(row.learning_key for row in feedback_report.rows) == (
        "broken_evidence",
        "drifting_sources",
        "steady_baseline",
    )
    assert tuple(row.status for row in feedback_report.rows) == ("block", "watch", "pass")
    assert tuple(row.queued for row in feedback_report.rows) == (True, True, False)
    assert tuple(row.feedback_pressure for row in feedback_report.rows) == (
        d("0.750000"),
        d("0.350000"),
        d("0.057000"),
    )
    assert "research_outcome_learning_feedback_queue_block" in feedback_report.reason_codes
    assert feedback_report.reason_code_counts[0].reason_code == (
        "aggregate_forecast_error_miss"
    )
    assert feedback_report.paper_only is True
    assert feedback_report.report_only is True
    assert feedback_report.readonly is True


def test_empty_input_is_blocked_report_only_feedback_queue() -> None:
    feedback_report = report(())

    assert feedback_report.status == "block"
    assert feedback_report.item_count == d("0")
    assert feedback_report.rows == ()
    assert feedback_report.reason_codes == (
        "no_outcome_learning_feedback_items",
        "research_outcome_learning_feedback_queue_block",
        "report_only_feedback_queue",
    )
    assert feedback_report.derived_validation_digest
    assert feedback_report.paper_only is True
    assert feedback_report.report_only is True
    assert feedback_report.readonly is True


def test_decimal_only_strict_types_and_status_vocabulary_are_enforced() -> None:
    module = api()

    with pytest.raises(ValueError, match="aggregate_forecast_error must be an exact Decimal"):
        item(aggregate_forecast_error=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="evidence_miss_score must be a Decimal"):
        item(evidence_miss_score=0.4)
    with pytest.raises(ValueError, match="outcome_count must be a Decimal"):
        item(outcome_count=3)
    with pytest.raises(ValueError, match="outcome_count must be a whole count"):
        item(outcome_count=d("1.500000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        item(reason_codes=["outcome_reviewed"])
    with pytest.raises(ValueError, match="learning_key"):
        item(learning_key="market_slug")
    with pytest.raises(ValueError, match="items must contain"):
        report((object(),))
    with pytest.raises(ValueError, match="config must be"):
        report((item(),), cfg=object())
    with pytest.raises(ValueError, match="config weights must sum to 1"):
        config(team_calibration_drift_weight=d("0.110000"))
    with pytest.raises(ValueError, match="block_feedback_pressure_threshold"):
        config(block_feedback_pressure_threshold=d("0.300000"))

    with pytest.raises(ValueError, match="status"):
        module.ResearchOutcomeLearningFeedbackQueueRow(
            learning_key="bad_status",
            outcome_count=d("1"),
            aggregate_forecast_error=d("0.100000"),
            evidence_miss_score=d("0.100000"),
            source_reliability_drift=d("0.100000"),
            cost_friction_miss_score=d("0.100000"),
            team_calibration_drift=d("0.100000"),
            feedback_pressure=d("0.100000"),
            status="blocked",
            queued=False,
            reason_codes=("report_only_feedback_queue",),
        )


def test_public_payload_is_deterministic_digest_safe_and_identifier_free() -> None:
    module = api()
    first = report(
        (
            item(learning_key="steady_baseline"),
            item(
                learning_key="broken_evidence",
                aggregate_forecast_error=d("0.900000"),
                evidence_miss_score=d("0.800000"),
                source_reliability_drift=d("0.700000"),
                cost_friction_miss_score=d("0.600000"),
                team_calibration_drift=d("0.500000"),
            ),
        ),
    )
    second = report((first.rows[0], first.rows[1]))
    first_payload = module.research_outcome_learning_feedback_queue_report_payload(first)
    second_payload = module.research_outcome_learning_feedback_queue_report_payload(second)

    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(first_payload["derived_validation_digest"]) == 64
    json.dumps(first_payload, sort_keys=True)
    assert_public_json_scalars(first_payload)
    encoded = json.dumps(first_payload, sort_keys=True)
    for forbidden in (
        "event_id",
        "market_slug",
        "market_id",
        "source_id",
        "source_url",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in encoded

    unsafe_payloads = (
        {"event_id": "raw-event-123"},
        {"raw_event_id": "event-123"},
        {"market_slug": "will-this-resolve"},
        {"market_id": "market-123"},
        {"source_id": "source-123"},
        {"source_url": "https://example.invalid/source"},
        {"learning_key": "wallet"},
        {"status_note": "auth"},
        {"status_note": "order"},
        {"status_note": "trade"},
        {"status_note": "live execution"},
        {"status_note": "recommendation"},
        {"status_note": "sizing"},
    )
    for unsafe_payload in unsafe_payloads:
        with pytest.raises(ValueError, match="unsafe public payload entry"):
            module.validate_research_outcome_learning_feedback_queue_public_payload(
                {**first_payload, **unsafe_payload},
            )


def test_hard_flags_and_frozen_records_are_enforced() -> None:
    module = api()
    cfg = config()
    row_input = item()
    feedback_report = report((row_input,), cfg=cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(row_input)
    assert is_dataclass(feedback_report)
    with pytest.raises(FrozenInstanceError):
        feedback_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        feedback_report.rows[0].status = "watch"  # type: ignore[misc]

    for instance in (cfg, row_input, feedback_report, feedback_report.rows[0]):
        assert public_values(instance)["paper_only"] is True
        assert public_values(instance)["report_only"] is True
        assert public_values(instance)["readonly"] is True
        with pytest.raises(ValueError, match="paper_only"):
            replace(instance, paper_only=False)
        with pytest.raises(ValueError, match="report_only"):
            replace(instance, report_only=False)
        with pytest.raises(ValueError, match="readonly"):
            replace(instance, readonly=False)

    payload = module.research_outcome_learning_feedback_queue_report_payload(feedback_report)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_module_has_no_storage_network_execution_or_trading_surface() -> None:
    module = api()
    source_path = Path(module.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    forbidden_imports = {
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "web3",
        "ccxt",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".", maxsplit=1)[0] for alias in node.names}
            assert imported.isdisjoint(forbidden_imports)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", maxsplit=1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            callee = node.func
            if isinstance(callee, ast.Name):
                assert callee.id not in {"open", "connect", "request", "post", "put"}
            elif isinstance(callee, ast.Attribute):
                assert callee.attr not in {"connect", "request", "post", "put", "commit"}

    public_names = set(module.__all__)
    for public_name in public_names:
        for forbidden in ("wallet", "auth", "order", "trade", "live"):
            assert forbidden not in public_name
