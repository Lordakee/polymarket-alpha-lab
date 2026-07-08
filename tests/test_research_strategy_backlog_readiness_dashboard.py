from __future__ import annotations

import ast
import dataclasses
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_strategy_backlog_readiness_dashboard import (
    DEFAULT_RESEARCH_STRATEGY_BACKLOG_READINESS_DASHBOARD_CONFIG_VERSION,
    ResearchStrategyBacklogReadinessCandidate,
    ResearchStrategyBacklogReadinessDashboardConfig,
    ResearchStrategyBacklogReadinessDashboardReport,
    ResearchStrategyBacklogReadinessDashboardRow,
    build_research_strategy_backlog_readiness_dashboard,
    research_strategy_backlog_readiness_dashboard_digest,
    research_strategy_backlog_readiness_dashboard_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _candidate(**overrides: object) -> ResearchStrategyBacklogReadinessCandidate:
    values = {
        "private_ref": "private-candidate-alpha",
        "private_context": (
            "raw-candidate-id=alpha-123",
            "private-event-key=market-123",
            "private-label=will this example resolve yes?",
            "https://example.invalid/private/source",
        ),
        "evidence_quality_score": d("0.920000"),
        "evidence_item_count": d("6"),
        "evidence_family_count": d("3"),
        "cost_drag_score": d("0.020000"),
        "team_coverage_score": d("1.000000"),
        "team_count": d("3"),
        "covered_team_count": d("3"),
        "review_status": "complete",
        "review_age_seconds": d("600"),
        "postmortem_status": "complete",
        "hard_flag_codes": (),
    }
    values.update(overrides)
    return ResearchStrategyBacklogReadinessCandidate(**values)


def _report(
    *candidates: ResearchStrategyBacklogReadinessCandidate,
) -> ResearchStrategyBacklogReadinessDashboardReport:
    return build_research_strategy_backlog_readiness_dashboard(
        candidates or (_candidate(),),
        config=ResearchStrategyBacklogReadinessDashboardConfig(),
        generated_at=GENERATED_AT,
    )


def test_dashboard_rolls_up_pass_watch_and_block_statuses() -> None:
    pass_report = _report(_candidate(private_ref="private-pass"))
    assert pass_report.public_status == "pass"
    assert pass_report.pass_count == d("1")
    assert pass_report.watch_count == d("0")
    assert pass_report.block_count == d("0")
    assert pass_report.reason_codes == ("backlog_all_pass",)
    assert pass_report.rows[0].human_next_step == "ready_for_human_review"

    watch_report = _report(
        _candidate(
            private_ref="private-watch",
            evidence_quality_score=d("0.700000"),
            cost_drag_score=d("0.080000"),
            review_status="in_progress",
            postmortem_status="pending",
        ),
    )
    assert watch_report.public_status == "watch"
    assert watch_report.pass_count == d("0")
    assert watch_report.watch_count == d("1")
    assert watch_report.block_count == d("0")
    assert watch_report.rows[0].public_status == "watch"
    assert watch_report.rows[0].reason_codes == (
        "evidence_quality_watch",
        "cost_drag_watch",
        "review_watch",
        "postmortem_pending",
    )

    block_report = _report(
        _candidate(
            private_ref="private-block",
            evidence_quality_score=d("0.300000"),
            team_coverage_score=d("0.250000"),
            hard_flag_codes=("manual_blocker",),
        ),
    )
    assert block_report.public_status == "block"
    assert block_report.block_count == d("1")
    assert block_report.rows[0].public_status == "block"
    assert block_report.rows[0].human_next_step == "blocked_until_manual_clearance"
    assert "hard_flags_present" in block_report.rows[0].reason_codes


def test_dashboard_uses_decimal_only_and_rejects_bad_types() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        _candidate(evidence_quality_score=0.92)
    with pytest.raises(ValueError, match="Decimal"):
        _candidate(evidence_item_count=6)
    with pytest.raises(ValueError, match="Decimal"):
        _candidate(cost_drag_score=_DecimalSubclass("0.020000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_strategy_backlog_readiness_dashboard(
            (_candidate(),),
            config=ResearchStrategyBacklogReadinessDashboardConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 14, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        build_research_strategy_backlog_readiness_dashboard(
            (_candidate(),),
            config=ResearchStrategyBacklogReadinessDashboardConfig(),
            generated_at=datetime(2026, 7, 8, 14, 30),
        )
    with pytest.raises(ValueError, match="public_status"):
        replace(_report().rows[0], public_status="needs_review")
    with pytest.raises(ValueError, match="paper_only"):
        replace(ResearchStrategyBacklogReadinessDashboardConfig(), paper_only=False)


def test_dashboard_public_payload_rejects_leaks_and_redacts_private_inputs() -> None:
    candidate = _candidate(
        private_ref="raw-candidate-id-secret",
        private_context=(
            "market-id-secret",
            "secret-market-slug",
            "Will the private question leak?",
            "https://source.example/private",
            "dsn=postgres://secret",
            "private_table_name",
            "token=secret-token",
        ),
    )
    report = _report(candidate)
    payload = research_strategy_backlog_readiness_dashboard_payload(report)
    rendered_payload = repr(payload).lower()
    rendered_report = repr(report).lower()

    for leak in (
        "raw-candidate-id-secret",
        "market-id-secret",
        "secret-market-slug",
        "will the private question leak",
        "https://source.example/private",
        "postgres://secret",
        "private_table_name",
        "secret-token",
    ):
        assert leak.lower() not in rendered_payload
        assert leak.lower() not in rendered_report

    assert payload["rows"][0]["public_candidate_ref"].startswith("candidate_sha256:")
    assert payload["rows"][0]["public_status"] == "pass"

    unsafe_payload = dict(payload)
    unsafe_payload["source_url"] = "https://example.invalid"
    with pytest.raises(ValueError, match="unsafe public"):
        research_strategy_backlog_readiness_dashboard_payload(unsafe_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(row) for row in payload["rows"]]
    unsafe_value_payload["rows"][0]["human_next_step"] = "buy now"
    with pytest.raises(ValueError, match="unsafe public"):
        research_strategy_backlog_readiness_dashboard_payload(unsafe_value_payload)


def test_dashboard_hard_flags_block_and_flags_are_required() -> None:
    report = _report(
        _candidate(
            private_ref="private-hard-flag",
            hard_flag_codes=("conflict_unresolved", "manual_blocker"),
        ),
    )

    assert report.public_status == "block"
    assert report.hard_flag_count == d("2")
    assert report.rows[0].public_status == "block"
    assert report.rows[0].hard_flag_count == d("2")
    assert report.rows[0].reason_codes[:3] == (
        "hard_flags_present",
        "conflict_unresolved",
        "manual_blocker",
    )

    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)


def test_dashboard_payload_is_deterministic_and_decimal_string_only() -> None:
    first = build_research_strategy_backlog_readiness_dashboard(
        (
            _candidate(private_ref="private-z", evidence_quality_score=d("0.700000")),
            _candidate(private_ref="private-a", cost_drag_score=d("0.090000")),
        ),
        config=ResearchStrategyBacklogReadinessDashboardConfig(),
        generated_at=datetime(2026, 7, 8, 10, 30, tzinfo=timezone(timedelta(hours=-4))),
    )
    second = build_research_strategy_backlog_readiness_dashboard(
        (
            _candidate(private_ref="private-a", cost_drag_score=d("0.090000")),
            _candidate(private_ref="private-z", evidence_quality_score=d("0.700000")),
        ),
        config=ResearchStrategyBacklogReadinessDashboardConfig(),
        generated_at=GENERATED_AT,
    )

    first_payload = research_strategy_backlog_readiness_dashboard_payload(first)
    second_payload = research_strategy_backlog_readiness_dashboard_payload(second)
    assert first_payload == second_payload
    assert tuple(row.public_candidate_ref for row in first.rows) == tuple(
        sorted(row.public_candidate_ref for row in first.rows)
    )
    assert first_payload["candidate_count"] == "2"
    assert first_payload["mean_evidence_quality_score"] == "0.810000"
    assert first_payload["rows"][0]["cost_drag_score"] == "0.090000"

    def assert_no_float_or_int(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float_or_int(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_float_or_int(item)
        elif type(value) is bool or value is None:
            return
        else:
            assert type(value) not in (float, int)

    assert_no_float_or_int(first_payload)
    raw_numeric_payload = dict(first_payload)
    raw_numeric_payload["candidate_count"] = 2
    with pytest.raises(ValueError, match="Decimal"):
        research_strategy_backlog_readiness_dashboard_payload(raw_numeric_payload)


def test_dashboard_report_and_digest_consistency() -> None:
    report = _report(_candidate(private_ref="private-digest"))
    payload = research_strategy_backlog_readiness_dashboard_payload(report)

    assert len(report.validation_digest) == 64
    assert payload["validation_digest"] == report.validation_digest
    assert research_strategy_backlog_readiness_dashboard_digest(report) == report.validation_digest
    assert research_strategy_backlog_readiness_dashboard_digest(payload) == report.validation_digest
    assert payload["rows"][0]["validation_digest"] == report.rows[0].validation_digest

    tampered_payload = dict(payload)
    tampered_payload["public_status"] = "watch"
    with pytest.raises(ValueError, match="validation_digest"):
        research_strategy_backlog_readiness_dashboard_payload(tampered_payload)

    tampered_rows_payload = dict(payload)
    tampered_rows_payload["rows"] = [dict(row) for row in payload["rows"]]
    tampered_rows_payload["rows"][0]["public_status"] = "block"
    with pytest.raises(ValueError, match="validation_digest"):
        research_strategy_backlog_readiness_dashboard_payload(tampered_rows_payload)


def test_dashboard_dataclasses_are_frozen_and_module_scope_is_report_only() -> None:
    row = _report().rows[0]
    with pytest.raises(FrozenInstanceError):
        row.public_status = "watch"

    payload = research_strategy_backlog_readiness_dashboard_payload(_report())
    assert dataclasses.is_dataclass(row)
    assert not dataclasses.is_dataclass(payload)

    import polymarket_alpha_lab.research_strategy_backlog_readiness_dashboard as api

    source = inspect.getsource(api)
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "aiohttp",
        "eth_account",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "web3",
    }
    forbidden_fragments = (
        "wallet",
        "private_key",
        "live_trading",
        "position_sizing",
        "selected_position",
    )
    assert all(fragment not in source.lower() for fragment in forbidden_fragments)
    assert api.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_BACKLOG_READINESS_DASHBOARD_CONFIG_VERSION",
        "ResearchStrategyBacklogReadinessCandidate",
        "ResearchStrategyBacklogReadinessDashboardConfig",
        "ResearchStrategyBacklogReadinessDashboardReasonCodeCount",
        "ResearchStrategyBacklogReadinessDashboardReport",
        "ResearchStrategyBacklogReadinessDashboardRow",
        "build_research_strategy_backlog_readiness_dashboard",
        "research_strategy_backlog_readiness_dashboard_digest",
        "research_strategy_backlog_readiness_dashboard_payload",
    )
