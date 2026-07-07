from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.research_packet_source_freshness_alert_score_v2",
    )


def freshness_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "packet_ref": "packet-alpha",
        "question_ref": "question-alpha",
        "source_age_hours": d("2.000000"),
        "official_source_lag_hours": d("1.000000"),
        "independent_corroboration_age_hours": d("3.000000"),
        "contradiction_unresolved_age_hours": d("0.000000"),
        "probability_move_magnitude": d("0.010000"),
        "hours_to_resolution": d("200.000000"),
    }
    values.update(overrides)
    return module.ResearchPacketSourceFreshnessAlertScoreV2Input(**values)


def build(*rows: object):
    module = api()
    return module.build_research_packet_source_freshness_alert_score_v2_report(
        rows or (freshness_input(),),
        config=module.ResearchPacketSourceFreshnessAlertScoreV2Config(),
    )


def assert_payload_has_no_numeric_values(value: Any) -> None:
    if type(value) in (Decimal, int, float):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_numeric_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_payload_has_no_numeric_values(item)


def test_prioritizes_alerts_from_all_decimal_freshness_drivers() -> None:
    module = api()
    report = build(
        freshness_input(packet_ref="packet-clear"),
        freshness_input(
            packet_ref="packet-urgent",
            source_age_hours=d("48.000000"),
            official_source_lag_hours=d("72.000000"),
            independent_corroboration_age_hours=d("72.000000"),
            contradiction_unresolved_age_hours=d("24.000000"),
            probability_move_magnitude=d("1.000000"),
            hours_to_resolution=d("12.000000"),
        ),
        freshness_input(
            packet_ref="packet-watch",
            source_age_hours=d("27.000000"),
            official_source_lag_hours=d("42.000000"),
            independent_corroboration_age_hours=d("42.000000"),
            contradiction_unresolved_age_hours=d("12.000000"),
            probability_move_magnitude=d("0.525000"),
            hours_to_resolution=d("96.000000"),
        ),
    )

    assert report == module.ResearchPacketSourceFreshnessAlertScoreV2Report(
        config_version=(
            module.DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_ALERT_SCORE_V2_CONFIG_VERSION
        ),
        status="blocked",
        recommended_next_step="refresh_sources_before_paper_report",
        input_count=d("3.000000"),
        blocked_count=d("1.000000"),
        watch_count=d("1.000000"),
        pass_count=d("1.000000"),
        stale_source_age_count=d("2.000000"),
        official_source_lag_count=d("2.000000"),
        stale_independent_corroboration_count=d("2.000000"),
        unresolved_contradiction_count=d("2.000000"),
        material_probability_move_count=d("2.000000"),
        close_resolution_urgency_count=d("2.000000"),
        highest_priority_score=d("1.000000"),
        rows=report.rows,
        reason_codes=(
            "source_freshness_alert_status_blocked",
            "stale_source_age",
            "official_source_lag",
            "stale_independent_corroboration",
            "unresolved_contradiction",
            "material_probability_move",
            "close_resolution_urgency",
        ),
        derived_validation_digest=report.derived_validation_digest,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert tuple(row.packet_ref for row in report.rows) == (
        "packet-urgent",
        "packet-watch",
        "packet-clear",
    )

    urgent, watch, clear = report.rows
    assert urgent.priority_rank == d("1.000000")
    assert urgent.priority_score == d("1.000000")
    assert urgent.source_age_score == d("1.000000")
    assert urgent.official_source_lag_score == d("1.000000")
    assert urgent.independent_corroboration_age_score == d("1.000000")
    assert urgent.contradiction_unresolved_age_score == d("1.000000")
    assert urgent.probability_move_score == d("1.000000")
    assert urgent.close_urgency_score == d("1.000000")
    assert urgent.alert_status == "blocked"
    assert urgent.recommended_research_action == "refresh_source_evidence_first"
    assert urgent.reason_codes == (
        "source_freshness_alert_status_blocked",
        "stale_source_age",
        "official_source_lag",
        "stale_independent_corroboration",
        "unresolved_contradiction",
        "material_probability_move",
        "close_resolution_urgency",
    )

    assert watch.priority_rank == d("2.000000")
    assert watch.priority_score == d("0.500000")
    assert watch.source_age_score == d("0.500000")
    assert watch.official_source_lag_score == d("0.500000")
    assert watch.independent_corroboration_age_score == d("0.500000")
    assert watch.contradiction_unresolved_age_score == d("0.500000")
    assert watch.probability_move_score == d("0.500000")
    assert watch.close_urgency_score == d("0.500000")
    assert watch.alert_status == "watch"

    assert clear.priority_rank == d("3.000000")
    assert clear.priority_score == d("0.000000")
    assert clear.alert_status == "pass"
    for row in report.rows:
        assert type(row.priority_score) is Decimal
        assert row.paper_only is True
        assert row.report_only is True
        assert row.readonly is True


def test_empty_report_is_blocked_readonly_and_decimal_zeroed() -> None:
    module = api()
    empty = module.build_research_packet_source_freshness_alert_score_v2_report(
        (),
        config=module.ResearchPacketSourceFreshnessAlertScoreV2Config(),
    )

    assert empty.status == "blocked"
    assert empty.recommended_next_step == "refresh_sources_before_paper_report"
    assert empty.input_count == d("0.000000")
    assert empty.highest_priority_score == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("source_freshness_alert_no_inputs",)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_tie_breakers_and_digests_are_deterministic() -> None:
    left = build(
        freshness_input(packet_ref="packet-beta", question_ref="question-same"),
        freshness_input(packet_ref="packet-alpha", question_ref="question-same"),
    )
    right = build(
        freshness_input(packet_ref="packet-alpha", question_ref="question-same"),
        freshness_input(packet_ref="packet-beta", question_ref="question-same"),
    )

    assert tuple(row.packet_ref for row in left.rows) == ("packet-alpha", "packet-beta")
    assert tuple(row.priority_rank for row in left.rows) == (d("1.000000"), d("2.000000"))
    assert left == right
    assert left.derived_validation_digest == right.derived_validation_digest


def test_public_payload_serializes_decimal_strings_and_rejects_tampering() -> None:
    module = api()
    report = build(
        freshness_input(
            source_age_hours=d("48.000000"),
            official_source_lag_hours=d("72.000000"),
            independent_corroboration_age_hours=d("72.000000"),
            contradiction_unresolved_age_hours=d("24.000000"),
            probability_move_magnitude=d("1.000000"),
            hours_to_resolution=d("12.000000"),
        ),
    )

    payload = module.research_packet_source_freshness_alert_score_v2_payload(report)

    assert payload == report.payload
    assert payload["input_count"] == "1.000000"
    assert payload["highest_priority_score"] == "1.000000"
    assert payload["rows"][0]["priority_score"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["derived_validation_digest"])
    assert_payload_has_no_numeric_values(payload)

    restored = module.ResearchPacketSourceFreshnessAlertScoreV2Report.from_payload(payload)
    assert restored == report

    tampered = dict(payload)
    tampered["highest_priority_score"] = "0.100000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.ResearchPacketSourceFreshnessAlertScoreV2Report.from_payload(tampered)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, status="watch")
    mutated = build(freshness_input())
    object.__setattr__(mutated.rows[0], "priority_score", d("0.500000"))
    with pytest.raises(ValueError, match="priority_score must match"):
        module.research_packet_source_freshness_alert_score_v2_payload(mutated)


def test_rejects_unsafe_public_keys_values_bad_flags_and_wrong_types() -> None:
    module = api()
    subject = freshness_input()
    report = build(subject)

    class InputSubclass(module.ResearchPacketSourceFreshnessAlertScoreV2Input):
        pass

    class ReportSubclass(module.ResearchPacketSourceFreshnessAlertScoreV2Report):
        pass

    with pytest.raises(FrozenInstanceError):
        subject.packet_ref = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="subject must be"):
        InputSubclass(**subject.__dict__)
    with pytest.raises(ValueError, match="report must be"):
        ReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="source_age_hours must be a Decimal"):
        freshness_input(source_age_hours="2.000000")
    with pytest.raises(ValueError, match="official_source_lag_hours must be nonnegative"):
        freshness_input(official_source_lag_hours=d("-1.000000"))
    with pytest.raises(ValueError, match="probability_move_magnitude must be between"):
        freshness_input(probability_move_magnitude=d("1.000001"))
    with pytest.raises(ValueError, match="hours_to_resolution must not exceed six"):
        freshness_input(hours_to_resolution=d("1.1234567"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        freshness_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_packet_source_freshness_alert_score_v2_report((), config=object())
    with pytest.raises(ValueError, match="rows must be"):
        module.build_research_packet_source_freshness_alert_score_v2_report(object())
    with pytest.raises(ValueError, match="report must be"):
        module.research_packet_source_freshness_alert_score_v2_payload(object())

    duplicate = freshness_input(packet_ref="packet-duplicate", question_ref="question-duplicate")
    with pytest.raises(ValueError, match="unique by packet_ref and question_ref"):
        build(duplicate, duplicate)

    for forbidden_value in (
        "live-surface",
        "auth-callback",
        "wallet-field",
        "order-detail",
        "network-call",
        "database-row",
        "persist-record",
        "signing-request",
        "mutation-path",
        "buy-button",
        "sell-action",
        "trade-route",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            freshness_input(question_ref=forbidden_value)

    for forbidden_key in (
        "live_ref",
        "auth_ref",
        "wallet_ref",
        "order_ref",
        "network_ref",
        "database_ref",
        "persist_ref",
        "signing_ref",
        "mutation_ref",
        "buy_ref",
        "sell_ref",
        "trade_ref",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            module._reject_unsafe_public_payload("payload", {forbidden_key: "safe"})


def test_module_is_isolated_decimal_only_report_only_and_unwired() -> None:
    module = api()
    source = inspect.getsource(module)

    assert module.ResearchPacketSourceFreshnessAlertScoreV2Config.__dataclass_params__.frozen
    assert module.ResearchPacketSourceFreshnessAlertScoreV2Input.__dataclass_params__.frozen
    assert module.ResearchPacketSourceFreshnessAlertScoreV2Row.__dataclass_params__.frozen
    assert module.ResearchPacketSourceFreshnessAlertScoreV2Report.__dataclass_params__.frozen
    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_ALERT_SCORE_V2_CONFIG_VERSION",
        "REASON_CODES",
        "ResearchPacketSourceFreshnessAlertScoreV2Config",
        "ResearchPacketSourceFreshnessAlertScoreV2Input",
        "ResearchPacketSourceFreshnessAlertScoreV2Report",
        "ResearchPacketSourceFreshnessAlertScoreV2Row",
        "STATUSES",
        "build_research_packet_source_freshness_alert_score_v2_report",
        "research_packet_source_freshness_alert_score_v2_payload",
    )

    forbidden_import_roots = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
    )
    forbidden_call_names = {
        "authenticate",
        "cancel_order",
        "create_order",
        "open",
        "place_order",
        "read_text",
        "submit_order",
        "write_text",
    }

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", *forbidden_call_names}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_names

    assert {name.split(".", 1)[0] for name in imported_modules}.isdisjoint(
        forbidden_import_roots,
    )
    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
