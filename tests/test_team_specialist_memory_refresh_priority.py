from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import importlib
import json
import re
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_memory_refresh_priority",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "team-specialist-memory-refresh-priority-test",
        "stale_memory_weight": d("0.300000"),
        "unresolved_feedback_weight": d("0.250000"),
        "memory_age_weight": d("0.200000"),
        "accuracy_risk_weight": d("0.150000"),
        "coverage_gap_weight": d("0.100000"),
        "max_average_memory_age_days": d("30.000000"),
        "stale_memory_watch_ratio": d("0.250000"),
        "stale_memory_block_ratio": d("0.500000"),
        "unresolved_feedback_watch_count": d("1.000000"),
        "unresolved_feedback_block_count": d("3.000000"),
        "average_memory_age_watch_days": d("14.000000"),
        "average_memory_age_block_days": d("30.000000"),
        "recent_accuracy_watch_floor": d("0.700000"),
        "recent_accuracy_block_floor": d("0.500000"),
        "coverage_gap_watch_score": d("0.500000"),
        "coverage_gap_block_score": d("0.850000"),
        "watch_score_floor": d("0.300000"),
        "block_score_floor": d("0.700000"),
    }
    values.update(overrides)
    return module.TeamSpecialistMemoryRefreshPriorityConfig(**values)


def memory_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "team_id": "team-alpha",
        "specialist_id": "specialist-alpha",
        "memory_item_count": d("20.000000"),
        "stale_memory_count": d("1.000000"),
        "unresolved_feedback_count": d("0.000000"),
        "average_memory_age_days": d("3.000000"),
        "recent_accuracy_score": d("0.900000"),
        "coverage_gap_score": d("0.100000"),
    }
    values.update(overrides)
    return module.TeamSpecialistMemoryRefreshPriorityInput(**values)


def build_report(*items: Any) -> Any:
    module = api()
    return module.build_team_specialist_memory_refresh_priority(
        items,
        config=config(),
        generated_at=GENERATED_AT,
    )


def assert_no_numeric_payload_values(value: object) -> None:
    if type(value) is dict:
        for item in value.values():
            assert_no_numeric_payload_values(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_numeric_payload_values(item)
        return
    assert type(value) not in (Decimal, float, int)


def assert_no_forbidden_public_surface(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, sort_keys=True).lower()
    for phrase in ("http://", "https://", "position sizing", "position-sizing"):
        assert phrase not in serialized
    tokens = set(re.findall(r"[a-z0-9]+", serialized))
    forbidden = {
        "market",
        "candidate",
        "slug",
        "question",
        "source",
        "ref",
        "refs",
        "dsn",
        "table",
        "tables",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position",
        "ready",
        "blocked",
        "matched",
        "supported",
    }
    for term in forbidden:
        assert term not in tokens


def test_fresh_memory_pass_report() -> None:
    module = api()
    report = build_report(memory_input())
    payload = module.team_specialist_memory_refresh_priority_payload(report)

    assert report.status == "pass"
    assert report.row_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_refresh_priority_score == d("0.060000")
    assert report.top_refresh_priority_score == d("0.060000")
    assert report.reason_codes == ("memory_refresh_pass",)

    row = report.rows[0]
    assert row.refresh_status == "pass"
    assert row.stale_memory_ratio == d("0.050000")
    assert row.unresolved_feedback_score == d("0.000000")
    assert row.memory_age_risk_score == d("0.100000")
    assert row.accuracy_risk_score == d("0.100000")
    assert row.refresh_priority_score == d("0.060000")
    assert row.reason_codes == ("memory_refresh_pass",)
    assert payload["status"] == "pass"
    assert payload["rows"][0]["refresh_status"] == "pass"
    assert_no_numeric_payload_values(payload)
    assert_no_forbidden_public_surface(payload)


def test_stale_unresolved_memory_blocks_before_more_research() -> None:
    report = build_report(
        memory_input(
            memory_item_count=d("10.000000"),
            stale_memory_count=d("6.000000"),
            unresolved_feedback_count=d("3.000000"),
            average_memory_age_days=d("35.000000"),
            recent_accuracy_score=d("0.450000"),
            coverage_gap_score=d("0.200000"),
        ),
    )

    row = report.rows[0]
    assert report.status == "block"
    assert report.block_count == d("1.000000")
    assert row.refresh_status == "block"
    assert row.stale_memory_ratio == d("0.600000")
    assert row.unresolved_feedback_score == d("1.000000")
    assert row.memory_age_risk_score == d("1.000000")
    assert row.accuracy_risk_score == d("0.550000")
    assert row.refresh_priority_score == d("0.732500")
    assert "stale_memory_limit" in row.reason_codes
    assert "unresolved_feedback_limit" in row.reason_codes
    assert "memory_age_limit" in row.reason_codes
    assert "accuracy_limit" in row.reason_codes


def test_coverage_gap_sets_watch_without_blocking() -> None:
    report = build_report(memory_input(coverage_gap_score=d("0.600000")))

    row = report.rows[0]
    assert report.status == "watch"
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("0.000000")
    assert row.refresh_status == "watch"
    assert row.refresh_priority_score == d("0.110000")
    assert row.reason_codes == ("memory_refresh_watch", "coverage_gap_watch")


def test_decimal_exact_type_rejection() -> None:
    with pytest.raises(ValueError, match="memory_item_count must be a Decimal"):
        memory_input(memory_item_count=DecimalSubclass("20.000000"))
    with pytest.raises(ValueError, match="average_memory_age_days must be a Decimal"):
        memory_input(average_memory_age_days=3)
    with pytest.raises(ValueError, match="coverage_gap_score must be a Decimal"):
        memory_input(coverage_gap_score=0.1)
    with pytest.raises(ValueError, match="stale_memory_weight must be a Decimal"):
        config(stale_memory_weight="0.300000")


def test_public_payload_leak_rejection() -> None:
    module = api()
    with pytest.raises(ValueError, match="unsafe public surface"):
        memory_input(team_id=f"team-{hidden_word('6d61726b6574')}")
    with pytest.raises(ValueError, match="unsafe public surface"):
        memory_input(specialist_id=f"specialist-{hidden_word('63616e646964617465')}")
    with pytest.raises(ValueError, match="unsafe public surface"):
        config(config_version=f"refresh-{hidden_word('746f6b656e')}")

    payload = module.team_specialist_memory_refresh_priority_payload(
        build_report(memory_input()),
    )
    for key, value in (
        ("candidate_id", "candidate-alpha"),
        ("market_url", "https://example.test/item"),
        ("source_ref", "analyst-note"),
        ("wallet_hint", "paper-wallet"),
    ):
        tampered = dict(payload)
        tampered[key] = value
        with pytest.raises(ValueError, match="unsafe public surface"):
            module.validate_team_specialist_memory_refresh_priority_payload(tampered)


def test_hard_flags_are_enforced() -> None:
    module = api()
    with pytest.raises(ValueError, match="paper_only must be True"):
        memory_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        config(readonly=False)

    report = build_report(memory_input())
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert module.team_specialist_memory_refresh_priority_payload(report)["paper_only"] is True
    assert module.team_specialist_memory_refresh_priority_payload(report)["report_only"] is True
    assert module.team_specialist_memory_refresh_priority_payload(report)["readonly"] is True


def test_deterministic_payload_and_public_dataclasses() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_MEMORY_REFRESH_PRIORITY_CONFIG_VERSION",
        "MEMORY_REFRESH_STATUSES",
        "TeamSpecialistMemoryRefreshPriorityConfig",
        "TeamSpecialistMemoryRefreshPriorityInput",
        "TeamSpecialistMemoryRefreshPriorityRow",
        "TeamSpecialistMemoryRefreshPriorityReport",
        "build_team_specialist_memory_refresh_priority",
        "team_specialist_memory_refresh_priority_payload",
        "validate_team_specialist_memory_refresh_priority_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    alpha = memory_input(team_id="team-alpha", specialist_id="specialist-alpha")
    beta = memory_input(team_id="team-beta", specialist_id="specialist-beta")
    report = build_report(beta, alpha)
    reversed_report = build_report(alpha, beta)

    assert [row.team_id for row in report.rows] == ["team-alpha", "team-beta"]
    assert [row.rank for row in report.rows] == [d("1.000000"), d("2.000000")]
    assert report.payload == reversed_report.payload
    assert report.derived_validation_digest == reversed_report.derived_validation_digest
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)

    with pytest.raises(FrozenInstanceError):
        report.rows[0].refresh_status = "block"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeInput(module.TeamSpecialistMemoryRefreshPriorityInput):
            pass


def test_report_consistency_and_digest_validation() -> None:
    module = api()
    report = build_report(
        memory_input(team_id="team-alpha", specialist_id="specialist-alpha"),
        memory_input(
            team_id="team-gamma",
            specialist_id="specialist-gamma",
            coverage_gap_score=d("0.600000"),
        ),
    )

    assert report.status == "watch"
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("0.000000")
    assert report.average_refresh_priority_score == d("0.085000")
    assert report.reason_codes == ("memory_refresh_watch",)

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="pass")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.team_specialist_memory_refresh_priority_payload(report)
    assert module.validate_team_specialist_memory_refresh_priority_payload(payload)
    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "3.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_team_specialist_memory_refresh_priority_payload(tampered_payload)

    json.dumps(payload, sort_keys=True)
    assert_no_forbidden_public_surface(payload)


def test_report_uses_only_pass_watch_block_status_values() -> None:
    report = build_report(
        memory_input(team_id="team-pass", specialist_id="specialist-pass"),
        memory_input(
            team_id="team-watch",
            specialist_id="specialist-watch",
            coverage_gap_score=d("0.600000"),
        ),
        memory_input(
            team_id="team-block",
            specialist_id="specialist-block",
            unresolved_feedback_count=d("3.000000"),
        ),
    )
    payload = report.payload

    assert report.status == "block"
    assert payload["status"] == "block"
    assert {row["refresh_status"] for row in payload["rows"]} == {
        "pass",
        "watch",
        "block",
    }
    assert_no_forbidden_public_surface(payload)
