from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.operator_recommendation_ready_queue_rollup_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: object) -> Any:
    module = api()
    values = {
        "ready_candidate_count": d("3.000000"),
        "watch_candidate_count": d("1.000000"),
        "blocked_candidate_count": d("0.000000"),
        "manual_capacity_count": d("5.000000"),
        "packet_digest_missing_count": d("0.000000"),
    }
    values.update(overrides)
    inputs = module.OperatorRecommendationReadyQueueRollupInput(**values)
    return module.build_operator_recommendation_ready_queue_rollup_report(inputs)


def assert_no_float_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)
    else:
        assert type(value) is not float


def test_ready_queue_capacity_available_returns_ready_report() -> None:
    module = api()
    report = build_report(
        ready_candidate_count=d("3.000000"),
        watch_candidate_count=d("1.000000"),
        blocked_candidate_count=d("0.000000"),
        manual_capacity_count=d("5.000000"),
        packet_digest_missing_count=d("0.000000"),
    )

    assert type(report) is module.OperatorRecommendationReadyQueueRollupReport
    assert report.config_version == (
        module.OPERATOR_RECOMMENDATION_READY_QUEUE_ROLLUP_REPORT_VERSION
    )
    assert report.ready_queue_status == "ready"
    assert report.reason_codes == (
        "operator_recommendation_ready_queue_rollup_ready",
    )
    assert report.manual_next_step == (
        "continue_manual_recommendation_ready_queue_review"
    )
    assert report.ready_candidate_count == d("3.000000")
    assert report.watch_candidate_count == d("1.000000")
    assert report.blocked_candidate_count == d("0.000000")
    assert report.manual_capacity_count == d("5.000000")
    assert report.packet_digest_missing_count == d("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_queue_statuses_reason_codes_and_steps_are_deterministic() -> None:
    watch = build_report(
        ready_candidate_count=d("4.000000"),
        watch_candidate_count=d("2.000000"),
        blocked_candidate_count=d("0.000000"),
        manual_capacity_count=d("3.000000"),
        packet_digest_missing_count=d("0.000000"),
    )
    assert watch.ready_queue_status == "watch"
    assert watch.reason_codes == (
        "operator_recommendation_ready_queue_rollup_watch_candidates_present",
        "operator_recommendation_ready_queue_rollup_ready_above_manual_capacity",
    )
    assert watch.manual_next_step == "prioritize_ready_candidates_within_manual_capacity"

    blocked = build_report(
        ready_candidate_count=d("2.000000"),
        watch_candidate_count=d("1.000000"),
        blocked_candidate_count=d("1.000000"),
        manual_capacity_count=d("3.000000"),
        packet_digest_missing_count=d("1.000000"),
    )
    assert blocked.ready_queue_status == "blocked"
    assert blocked.reason_codes == (
        "operator_recommendation_ready_queue_rollup_blocked_candidates_present",
        "operator_recommendation_ready_queue_rollup_packet_digest_missing",
        "operator_recommendation_ready_queue_rollup_watch_candidates_present",
    )
    assert blocked.manual_next_step == "resolve_blocked_candidates_and_missing_packet_digests"

    no_capacity = build_report(
        ready_candidate_count=d("2.000000"),
        watch_candidate_count=d("0.000000"),
        blocked_candidate_count=d("0.000000"),
        manual_capacity_count=d("0.000000"),
        packet_digest_missing_count=d("0.000000"),
    )
    assert no_capacity.ready_queue_status == "blocked"
    assert no_capacity.reason_codes == (
        "operator_recommendation_ready_queue_rollup_no_manual_capacity",
        "operator_recommendation_ready_queue_rollup_ready_above_manual_capacity",
    )
    assert no_capacity.manual_next_step == "assign_manual_capacity_before_ready_queue_review"


def test_public_payload_is_immutable_decimal_string_only_and_digest_bound() -> None:
    module = api()
    report = build_report(
        ready_candidate_count=d("6.000000"),
        watch_candidate_count=d("2.000000"),
        blocked_candidate_count=d("1.000000"),
        manual_capacity_count=d("4.000000"),
        packet_digest_missing_count=d("1.000000"),
    )

    payload = report.public_payload
    assert type(payload) is module.OperatorRecommendationReadyQueueRollupPublicPayload
    assert payload == module.operator_recommendation_ready_queue_rollup_report_payload(
        report,
    )
    assert payload["ready_candidate_count"] == "6.000000"
    assert payload["watch_candidate_count"] == "2.000000"
    assert payload["blocked_candidate_count"] == "1.000000"
    assert payload["manual_capacity_count"] == "4.000000"
    assert payload["packet_digest_missing_count"] == "1.000000"
    assert payload["ready_queue_status"] == "blocked"
    assert payload["payload_digest"] == report.payload_digest
    assert report.payload_digest == (
        module.operator_recommendation_ready_queue_rollup_report_payload_digest(report)
    )
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)

    with pytest.raises(TypeError, match="immutable"):
        payload["ready_queue_status"] = "ready"

    tampered_payload = dict(payload)
    tampered_payload["ready_candidate_count"] = "7.000000"
    with pytest.raises(ValueError, match="digest"):
        module.operator_recommendation_ready_queue_rollup_report_payload(tampered_payload)


def test_decimal_only_frozen_dataclasses_and_hard_flags_are_enforced() -> None:
    module = api()
    report = build_report()

    assert module.__all__ == (
        "OPERATOR_RECOMMENDATION_READY_QUEUE_ROLLUP_REPORT_VERSION",
        "OperatorRecommendationReadyQueueRollupInput",
        "OperatorRecommendationReadyQueueRollupPublicPayload",
        "OperatorRecommendationReadyQueueRollupReport",
        "build_operator_recommendation_ready_queue_rollup_report",
        "operator_recommendation_ready_queue_rollup_report_payload",
        "operator_recommendation_ready_queue_rollup_report_payload_digest",
    )
    for dataclass_type in (
        module.OperatorRecommendationReadyQueueRollupInput,
        module.OperatorRecommendationReadyQueueRollupReport,
    ):
        assert is_dataclass(dataclass_type)
        assert dataclass_type.__dataclass_params__.frozen is True
        for field in fields(dataclass_type):
            assert "float" not in str(field.type)
            assert "int" not in str(field.type)

    with pytest.raises(FrozenInstanceError):
        report.ready_queue_status = "watch"
    with pytest.raises(ValueError, match="ready_candidate_count must be a Decimal"):
        build_report(ready_candidate_count=1)
    with pytest.raises(ValueError, match="watch_candidate_count must be a Decimal"):
        build_report(watch_candidate_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="nonnegative"):
        build_report(blocked_candidate_count=d("-1.000000"))
    with pytest.raises(ValueError, match="packet_digest_missing_count cannot exceed"):
        build_report(
            ready_candidate_count=d("1.000000"),
            watch_candidate_count=d("0.000000"),
            blocked_candidate_count=d("0.000000"),
            packet_digest_missing_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.OperatorRecommendationReadyQueueRollupInput(
            ready_candidate_count=d("1.000000"),
            watch_candidate_count=d("0.000000"),
            blocked_candidate_count=d("0.000000"),
            manual_capacity_count=d("1.000000"),
            packet_digest_missing_count=d("0.000000"),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_module_scope_is_readonly_report_only_without_execution_or_persistence_surface() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "live",
        "auth",
        "wallet",
        "private_key",
        "api_key",
        "secret_key",
        "sign",
        "submit",
        "cancel",
        "order",
        "execute",
        "execution",
        "jsonl",
        "persist",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
