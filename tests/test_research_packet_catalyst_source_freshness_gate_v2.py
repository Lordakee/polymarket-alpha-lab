from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.research_packet_catalyst_source_freshness_gate_v2",
    )


def catalyst_input(**overrides: Any):
    values: dict[str, Any] = {
        "packet_ref": "packet-alpha",
        "question_ref": "question-alpha",
        "catalyst_ref": "catalyst-alpha",
        "latest_official_source_at": GENERATED_AT - timedelta(hours=3),
        "latest_catalyst_source_at": GENERATED_AT - timedelta(hours=4),
        "official_source_count": d("1.000000"),
        "source_count": d("3.000000"),
        "fresh_source_count": d("2.000000"),
        "reason_codes": ("source_packet_input",),
    }
    values.update(overrides)
    return api().ResearchPacketCatalystSourceFreshnessGateV2Input(**values)


def build(*rows: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_research_packet_catalyst_source_freshness_gate_v2_report(
        rows,
        config=cfg if cfg is not None else module.ResearchPacketCatalystSourceFreshnessGateV2Config(),
        generated_at=generated_at,
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


def test_catalyst_source_freshness_gate_scores_and_sorts_rows() -> None:
    module = api()
    report = build(
        catalyst_input(
            packet_ref="packet-pass",
            question_ref="question-pass",
            catalyst_ref="catalyst-pass",
            latest_official_source_at=GENERATED_AT - timedelta(hours=3),
            latest_catalyst_source_at=GENERATED_AT - timedelta(hours=4),
            official_source_count=d("1.000000"),
            source_count=d("3.000000"),
            fresh_source_count=d("2.000000"),
        ),
        catalyst_input(
            packet_ref="packet-watch",
            question_ref="question-watch",
            catalyst_ref="catalyst-watch",
            latest_official_source_at=GENERATED_AT - timedelta(hours=18),
            latest_catalyst_source_at=GENERATED_AT - timedelta(hours=30),
            official_source_count=d("1.000000"),
            source_count=d("2.000000"),
            fresh_source_count=d("1.000000"),
        ),
        catalyst_input(
            packet_ref="packet-block",
            question_ref="question-block",
            catalyst_ref="catalyst-block",
            latest_official_source_at=GENERATED_AT - timedelta(hours=30),
            latest_catalyst_source_at=GENERATED_AT - timedelta(hours=60),
            official_source_count=d("1.000000"),
            source_count=d("3.000000"),
            fresh_source_count=d("0.000000"),
        ),
    )

    assert report == module.ResearchPacketCatalystSourceFreshnessGateV2Report(
        generated_at=GENERATED_AT,
        config_version=module.DEFAULT_RESEARCH_PACKET_CATALYST_SOURCE_FRESHNESS_GATE_V2_CONFIG_VERSION,
        status="blocked",
        recommended_next_step="collect_catalyst_sources_for_paper_report",
        input_count=d("3.000000"),
        blocked_count=d("1.000000"),
        watch_count=d("1.000000"),
        pass_count=d("1.000000"),
        missing_official_source_count=ZERO,
        stale_official_source_count=d("2.000000"),
        stale_catalyst_source_count=d("2.000000"),
        insufficient_fresh_source_count=d("2.000000"),
        highest_freshness_risk_score=d("1.000000"),
        max_latest_official_source_age_hours=d("30.000000"),
        max_latest_catalyst_source_age_hours=d("60.000000"),
        min_fresh_source_ratio=ZERO,
        rows=report.rows,
        reason_codes=(
            "catalyst_source_freshness_gate_status_blocked",
            "stale_official_source_watch",
            "stale_official_source_blocked",
            "stale_catalyst_source_watch",
            "stale_catalyst_source_blocked",
            "insufficient_fresh_sources_watch",
            "insufficient_fresh_sources_blocked",
            "weak_fresh_source_ratio_watch",
            "weak_fresh_source_ratio_blocked",
        ),
        derived_validation_digest=report.derived_validation_digest,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert tuple(row.source_status for row in report.rows) == ("blocked", "watch", "pass")
    blocked, watched, passed = report.rows
    assert blocked.packet_ref == "packet-block"
    assert blocked.latest_official_source_age_hours == d("30.000000")
    assert blocked.latest_catalyst_source_age_hours == d("60.000000")
    assert blocked.fresh_source_ratio == ZERO
    assert blocked.freshness_risk_score == d("1.000000")
    assert blocked.recommended_research_action == "catalyst_source_freshness_research_first"
    assert blocked.reason_codes == (
        "source_packet_input",
        "catalyst_source_freshness_gate_status_blocked",
        "stale_official_source_blocked",
        "stale_catalyst_source_blocked",
        "insufficient_fresh_sources_blocked",
        "weak_fresh_source_ratio_blocked",
    )
    assert watched.source_status == "watch"
    assert watched.latest_official_source_age_hours == d("18.000000")
    assert watched.latest_catalyst_source_age_hours == d("30.000000")
    assert watched.fresh_source_ratio == d("0.500000")
    assert watched.reason_codes == (
        "source_packet_input",
        "catalyst_source_freshness_gate_status_watch",
        "stale_official_source_watch",
        "stale_catalyst_source_watch",
        "insufficient_fresh_sources_watch",
        "weak_fresh_source_ratio_watch",
    )
    assert passed.source_status == "pass"
    assert passed.fresh_source_ratio == d("0.666667")
    assert passed.reason_codes == (
        "source_packet_input",
        "catalyst_source_freshness_gate_status_pass",
    )


def test_official_recency_requirement_and_missing_official_blocking() -> None:
    missing = build(
        catalyst_input(
            latest_official_source_at=None,
            official_source_count=ZERO,
            source_count=d("2.000000"),
            fresh_source_count=d("2.000000"),
        ),
    )
    blocked = missing.rows[0]

    assert missing.status == "blocked"
    assert missing.missing_official_source_count == d("1.000000")
    assert blocked.source_status == "blocked"
    assert blocked.latest_official_source_age_hours == d("25.000000")
    assert blocked.reason_codes == (
        "source_packet_input",
        "catalyst_source_freshness_gate_status_blocked",
        "missing_official_source",
    )

    official_watch = build(
        catalyst_input(
            latest_official_source_at=GENERATED_AT - timedelta(hours=18),
            latest_catalyst_source_at=GENERATED_AT - timedelta(hours=4),
            source_count=d("3.000000"),
            fresh_source_count=d("2.000000"),
        ),
    )
    assert official_watch.status == "watch"
    assert official_watch.rows[0].reason_codes == (
        "source_packet_input",
        "catalyst_source_freshness_gate_status_watch",
        "stale_official_source_watch",
    )


def test_stale_catalyst_blocks_even_with_fresh_official_source() -> None:
    report = build(
        catalyst_input(
            latest_official_source_at=GENERATED_AT - timedelta(hours=3),
            latest_catalyst_source_at=GENERATED_AT - timedelta(hours=72),
            official_source_count=d("1.000000"),
            source_count=d("4.000000"),
            fresh_source_count=d("3.000000"),
        ),
    )

    assert report.status == "blocked"
    assert report.stale_catalyst_source_count == d("1.000000")
    assert report.rows[0].source_status == "blocked"
    assert report.rows[0].reason_codes == (
        "source_packet_input",
        "catalyst_source_freshness_gate_status_blocked",
        "stale_catalyst_source_blocked",
    )


def test_serialization_decimal_strings_and_digest_tamper_rejection() -> None:
    module = api()
    report = build(catalyst_input())
    payload = module.research_packet_catalyst_source_freshness_gate_v2_payload(report)

    assert payload == report.payload
    assert payload["input_count"] == "1.000000"
    assert payload["highest_freshness_risk_score"] == "0.000000"
    assert payload["rows"][0]["fresh_source_ratio"] == "0.666667"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["derived_validation_digest"])
    assert_payload_has_no_numeric_values(payload)

    restored = module.ResearchPacketCatalystSourceFreshnessGateV2Report.from_payload(payload)
    assert restored == report

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, derived_validation_digest="0" * 64)
    tampered = dict(payload)
    tampered["generated_at"] = (GENERATED_AT + timedelta(hours=1)).isoformat()
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.ResearchPacketCatalystSourceFreshnessGateV2Report.from_payload(tampered)
    mutated = build(catalyst_input())
    object.__setattr__(mutated.rows[0], "freshness_risk_score", d("0.500000"))
    with pytest.raises(ValueError, match="freshness_risk_score must match"):
        module.research_packet_catalyst_source_freshness_gate_v2_payload(mutated)


def test_frozen_dataclasses_hard_flags_and_decimal_type_rejection() -> None:
    module = api()
    subject = catalyst_input()
    report = build(subject)

    class InputSubclass(module.ResearchPacketCatalystSourceFreshnessGateV2Input):
        pass

    class ReportSubclass(module.ResearchPacketCatalystSourceFreshnessGateV2Report):
        pass

    assert module.ResearchPacketCatalystSourceFreshnessGateV2Config.__dataclass_params__.frozen
    assert module.ResearchPacketCatalystSourceFreshnessGateV2Input.__dataclass_params__.frozen
    assert module.ResearchPacketCatalystSourceFreshnessGateV2Row.__dataclass_params__.frozen
    assert module.ResearchPacketCatalystSourceFreshnessGateV2Report.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        subject.packet_ref = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="subject must be"):
        InputSubclass(**subject.__dict__)
    with pytest.raises(ValueError, match="report must be"):
        ReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        catalyst_input(source_count="3.000000")
    with pytest.raises(ValueError, match="fresh_source_count must be integral"):
        catalyst_input(fresh_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="latest_official_source_at is required"):
        catalyst_input(latest_official_source_at=None)
    with pytest.raises(ValueError, match="latest_official_source_at requires"):
        catalyst_input(latest_official_source_at=GENERATED_AT, official_source_count=ZERO)
    with pytest.raises(ValueError, match="paper_only must be True"):
        catalyst_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_packet_catalyst_source_freshness_gate_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="rows must be"):
        module.build_research_packet_catalyst_source_freshness_gate_v2_report(
            object(),
            config=module.ResearchPacketCatalystSourceFreshnessGateV2Config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="report must be"):
        module.research_packet_catalyst_source_freshness_gate_v2_payload(object())


def test_unsafe_payload_rejection_for_keys_and_values() -> None:
    module = api()
    for forbidden_value in (
        "live surface",
        "auth callback",
        "wallet field",
        "order detail",
        "network call",
        "database row",
        "persist record",
        "signing request",
        "mutation path",
        "buy button",
        "sell action",
        "trade route",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            catalyst_input(packet_ref=forbidden_value)

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


def test_module_has_no_unsafe_runtime_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_CATALYST_SOURCE_FRESHNESS_GATE_V2_CONFIG_VERSION",
        "REASON_CODES",
        "ResearchPacketCatalystSourceFreshnessGateV2Config",
        "ResearchPacketCatalystSourceFreshnessGateV2Input",
        "ResearchPacketCatalystSourceFreshnessGateV2Report",
        "ResearchPacketCatalystSourceFreshnessGateV2Row",
        "STATUSES",
        "build_research_packet_catalyst_source_freshness_gate_v2_report",
        "research_packet_catalyst_source_freshness_gate_v2_payload",
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

    assert not any(
        imported_module.split(".")[0] in forbidden_import_roots
        for imported_module in imported_modules
    )
