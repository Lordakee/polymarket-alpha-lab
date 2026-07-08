from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.research_news_signal_freshness_gate_report",
    )


def signal_input(**overrides: Any):
    values: dict[str, Any] = {
        "research_scope_ref": "event-research-alpha",
        "latest_update_at": GENERATED_AT - timedelta(hours=2),
        "latest_corroboration_at": GENERATED_AT - timedelta(hours=4),
        "latest_conflict_check_at": GENERATED_AT - timedelta(hours=3),
        "next_recheck_due_at": GENERATED_AT + timedelta(hours=3),
        "corroborating_signal_count": d("3.000000"),
        "fresh_corroborating_signal_count": d("2.000000"),
        "unresolved_conflict_count": ZERO,
        "reason_codes": ("news_signal_input",),
    }
    values.update(overrides)
    return api().ResearchNewsSignalFreshnessGateInput(**values)


def build(*rows: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_research_news_signal_freshness_gate_report(
        rows,
        config=cfg if cfg is not None else module.ResearchNewsSignalFreshnessGateConfig(),
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


def assert_payload_excludes_raw_identifiers(value: Any) -> None:
    forbidden = (
        "://",
        "www.",
        "polymarket",
        "market_slug",
        "market_id",
        "condition_id",
        "token_id",
        "source_text",
        "raw_url",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(term in lowered_key for term in forbidden)
            assert_payload_excludes_raw_identifiers(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_payload_excludes_raw_identifiers(item)
    elif type(value) is str:
        lowered_value = value.lower()
        assert not any(term in lowered_value for term in forbidden)


def test_news_signal_freshness_gate_aggregates_and_sorts_readiness() -> None:
    module = api()
    report = build(
        signal_input(
            research_scope_ref="scope-pass",
            latest_update_at=GENERATED_AT - timedelta(hours=2),
            latest_corroboration_at=GENERATED_AT - timedelta(hours=4),
            latest_conflict_check_at=GENERATED_AT - timedelta(hours=3),
            next_recheck_due_at=GENERATED_AT + timedelta(hours=3),
            corroborating_signal_count=d("3.000000"),
            fresh_corroborating_signal_count=d("2.000000"),
            unresolved_conflict_count=ZERO,
        ),
        signal_input(
            research_scope_ref="scope-watch",
            latest_update_at=GENERATED_AT - timedelta(hours=10),
            latest_corroboration_at=GENERATED_AT - timedelta(hours=20),
            latest_conflict_check_at=GENERATED_AT - timedelta(hours=14),
            next_recheck_due_at=GENERATED_AT - timedelta(hours=2),
            corroborating_signal_count=d("2.000000"),
            fresh_corroborating_signal_count=d("1.000000"),
            unresolved_conflict_count=d("1.000000"),
        ),
        signal_input(
            research_scope_ref="scope-block",
            latest_update_at=GENERATED_AT - timedelta(hours=30),
            latest_corroboration_at=GENERATED_AT - timedelta(hours=50),
            latest_conflict_check_at=GENERATED_AT - timedelta(hours=30),
            next_recheck_due_at=GENERATED_AT - timedelta(hours=9),
            corroborating_signal_count=d("2.000000"),
            fresh_corroborating_signal_count=ZERO,
            unresolved_conflict_count=d("3.000000"),
        ),
    )

    assert report == module.ResearchNewsSignalFreshnessGateReport(
        generated_at=GENERATED_AT,
        config_version=module.DEFAULT_RESEARCH_NEWS_SIGNAL_FRESHNESS_GATE_CONFIG_VERSION,
        status="block",
        recommended_next_step="pause_event_research_for_news_signal_refresh",
        input_count=d("3.000000"),
        block_count=d("1.000000"),
        watch_count=d("1.000000"),
        pass_count=d("1.000000"),
        stale_update_count=d("2.000000"),
        stale_corroboration_count=d("2.000000"),
        stale_conflict_check_count=d("2.000000"),
        urgent_recheck_count=d("2.000000"),
        unresolved_conflict_scope_count=d("2.000000"),
        highest_recheck_urgency_score=d("1.000000"),
        max_update_age_hours=d("30.000000"),
        max_corroboration_age_hours=d("50.000000"),
        max_conflict_check_age_hours=d("30.000000"),
        max_recheck_overdue_hours=d("9.000000"),
        rows=report.rows,
        reason_codes=(
            "news_signal_freshness_gate_status_block",
            "news_update_stale_watch",
            "news_update_stale_block",
            "corroboration_stale_watch",
            "corroboration_stale_block",
            "corroboration_insufficient_watch",
            "corroboration_insufficient_block",
            "conflict_check_stale_watch",
            "conflict_check_stale_block",
            "unresolved_conflict_watch",
            "unresolved_conflict_block",
            "recheck_overdue_watch",
            "recheck_overdue_block",
        ),
        derived_validation_digest=report.derived_validation_digest,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert tuple(row.gate_status for row in report.rows) == ("block", "watch", "pass")

    blocked, watched, passed = report.rows
    assert blocked.research_scope_ref == "scope-block"
    assert blocked.update_age_hours == d("30.000000")
    assert blocked.corroboration_age_hours == d("50.000000")
    assert blocked.conflict_check_age_hours == d("30.000000")
    assert blocked.recheck_overdue_hours == d("9.000000")
    assert blocked.recheck_urgency_score == d("1.000000")
    assert blocked.recommended_research_action == "refresh_news_signals_before_research"
    assert blocked.reason_codes == (
        "news_signal_input",
        "news_signal_freshness_gate_status_block",
        "news_update_stale_block",
        "corroboration_stale_block",
        "corroboration_insufficient_block",
        "conflict_check_stale_block",
        "unresolved_conflict_block",
        "recheck_overdue_block",
    )

    assert watched.gate_status == "watch"
    assert watched.update_age_hours == d("10.000000")
    assert watched.corroboration_age_hours == d("20.000000")
    assert watched.conflict_check_age_hours == d("14.000000")
    assert watched.recheck_overdue_hours == d("2.000000")
    assert watched.recheck_urgency_score == d("0.500000")
    assert watched.reason_codes == (
        "news_signal_input",
        "news_signal_freshness_gate_status_watch",
        "news_update_stale_watch",
        "corroboration_stale_watch",
        "corroboration_insufficient_watch",
        "conflict_check_stale_watch",
        "unresolved_conflict_watch",
        "recheck_overdue_watch",
    )

    assert passed.gate_status == "pass"
    assert passed.recheck_overdue_hours == ZERO
    assert passed.recheck_urgency_score == ZERO
    assert passed.reason_codes == (
        "news_signal_input",
        "news_signal_freshness_gate_status_pass",
    )


def test_missing_corroboration_and_conflict_checks_control_gate_readiness() -> None:
    missing_corroboration = build(
        signal_input(
            latest_corroboration_at=None,
            corroborating_signal_count=d("2.000000"),
            fresh_corroborating_signal_count=ZERO,
        ),
    )
    row = missing_corroboration.rows[0]

    assert missing_corroboration.status == "block"
    assert row.corroboration_age_hours == d("37.000000")
    assert row.gate_status == "block"
    assert row.reason_codes == (
        "news_signal_input",
        "news_signal_freshness_gate_status_block",
        "corroboration_missing_block",
        "corroboration_insufficient_block",
    )

    stale_conflict_check = build(
        signal_input(
            latest_conflict_check_at=None,
            unresolved_conflict_count=d("1.000000"),
        ),
    )

    assert stale_conflict_check.status == "block"
    assert stale_conflict_check.stale_conflict_check_count == d("1.000000")
    assert stale_conflict_check.rows[0].reason_codes == (
        "news_signal_input",
        "news_signal_freshness_gate_status_block",
        "conflict_check_missing_block",
        "unresolved_conflict_watch",
    )


def test_serialization_decimal_strings_digest_and_round_trip() -> None:
    module = api()
    report = build(signal_input())
    payload = module.research_news_signal_freshness_gate_report_payload(report)

    assert payload == report.payload
    assert payload["input_count"] == "1.000000"
    assert payload["highest_recheck_urgency_score"] == "0.000000"
    assert payload["rows"][0]["update_age_hours"] == "2.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["derived_validation_digest"])
    assert_payload_has_no_numeric_values(payload)
    assert_payload_excludes_raw_identifiers(payload)

    restored = module.ResearchNewsSignalFreshnessGateReport.from_payload(payload)
    assert restored == report

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, derived_validation_digest="0" * 64)
    tampered = dict(payload)
    tampered["generated_at"] = (GENERATED_AT + timedelta(hours=1)).isoformat()
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.ResearchNewsSignalFreshnessGateReport.from_payload(tampered)
    mutated = build(signal_input())
    object.__setattr__(mutated.rows[0], "recheck_urgency_score", d("0.500000"))
    with pytest.raises(ValueError, match="recheck_urgency_score must match"):
        module.research_news_signal_freshness_gate_report_payload(mutated)


def test_frozen_dataclasses_hard_flags_decimal_only_and_identifier_rejection() -> None:
    module = api()
    subject = signal_input()
    report = build(subject)

    class InputSubclass(module.ResearchNewsSignalFreshnessGateInput):
        pass

    class ReportSubclass(module.ResearchNewsSignalFreshnessGateReport):
        pass

    assert module.ResearchNewsSignalFreshnessGateConfig.__dataclass_params__.frozen
    assert module.ResearchNewsSignalFreshnessGateInput.__dataclass_params__.frozen
    assert module.ResearchNewsSignalFreshnessGateRow.__dataclass_params__.frozen
    assert module.ResearchNewsSignalFreshnessGateReport.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        subject.research_scope_ref = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="subject must be"):
        InputSubclass(**subject.__dict__)
    with pytest.raises(ValueError, match="report must be"):
        ReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="corroborating_signal_count must be a Decimal"):
        signal_input(corroborating_signal_count="3.000000")
    with pytest.raises(ValueError, match="fresh_corroborating_signal_count must be integral"):
        signal_input(fresh_corroborating_signal_count=d("1.500000"))
    with pytest.raises(ValueError, match="fresh_corroborating_signal_count must be at most"):
        signal_input(
            corroborating_signal_count=d("1.000000"),
            fresh_corroborating_signal_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="raw identifiers are not allowed"):
        signal_input(research_scope_ref="https://example.test/story")
    with pytest.raises(ValueError, match="market identifiers are not allowed"):
        signal_input(research_scope_ref="market_slug:fed-cut")
    with pytest.raises(ValueError, match="paper_only must be True"):
        signal_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_news_signal_freshness_gate_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="rows must be"):
        module.build_research_news_signal_freshness_gate_report(
            object(),
            config=module.ResearchNewsSignalFreshnessGateConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="report must be"):
        module.research_news_signal_freshness_gate_report_payload(object())


def test_module_has_no_unsafe_runtime_or_storage_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_NEWS_SIGNAL_FRESHNESS_GATE_CONFIG_VERSION",
        "REASON_CODES",
        "ResearchNewsSignalFreshnessGateConfig",
        "ResearchNewsSignalFreshnessGateInput",
        "ResearchNewsSignalFreshnessGateReport",
        "ResearchNewsSignalFreshnessGateRow",
        "STATUSES",
        "build_research_news_signal_freshness_gate_report",
        "research_news_signal_freshness_gate_report_payload",
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
    forbidden_payload_field_terms = (
        "raw_url",
        "source_text",
        "market_slug",
        "market_id",
        "condition_id",
        "token_id",
    )
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
            if type(node.value) is str:
                lowered = node.value.lower()
                assert not any(term in lowered for term in forbidden_payload_field_terms)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", *forbidden_call_names}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_names

    assert not any(
        imported_module.split(".")[0] in forbidden_import_roots
        for imported_module in imported_modules
    )
