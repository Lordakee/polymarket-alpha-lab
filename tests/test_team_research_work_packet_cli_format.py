from __future__ import annotations

import builtins
import importlib
import sys
from decimal import Decimal
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.team_research_work_packet_cli_format import (
    format_team_research_work_packet_cli_stdout,
)


def test_format_team_research_work_packet_cli_stdout_formats_report_only_packets() -> None:
    report = SimpleNamespace(
        packet_status="watch",
        team_packet_count=Decimal("2"),
        research_assignment_count=Decimal("3"),
        assigned_count=Decimal("2"),
        watch_count=Decimal("1"),
        blocked_count=Decimal("0"),
        team_packets=(
            SimpleNamespace(
                team_id="crypto_btc",
                packet_status="watch",
                memory_readiness_status="watch",
                memory_use_policy="throttle",
                assignment_count=Decimal("2"),
                research_domains=("finance",),
                research_horizons=("long_term",),
                research_modes=("phase_1_report_only",),
                research_task_codes=(
                    "resolution_criteria_review",
                    "source_map_update",
                    "base_rate_context",
                    "uncertainty_log",
                    "counterevidence_scan",
                    "filing_calendar_scan",
                ),
                assigned_count=Decimal("1"),
                watch_count=Decimal("1"),
                blocked_count=Decimal("0"),
                evidence_gap_codes=(
                    "thin_segment_probability_samples",
                    "missing_calibration_report",
                ),
                assignment_reason_codes=(
                    "team_research_assignment_assigned",
                    "team_memory_readiness_watch",
                ),
                source_reason_codes=("candidate_research_ready",),
                paper_only=True,
                report_only=True,
                readonly=True,
                rows=(
                    SimpleNamespace(
                        research_rank=1,
                        market_slug="btc-alpha",
                        category_id="finance.crypto.btc",
                        assignment_status="assigned",
                        memory_use_policy="allow",
                        research_domain="finance",
                        research_horizon="long_term",
                        research_mode="phase_1_report_only",
                        research_task_codes=(
                            "resolution_criteria_review",
                            "source_map_update",
                        ),
                        evidence_gap_codes=(),
                        assignment_reason_codes=("team_research_assignment_assigned",),
                        paper_only=True,
                        report_only=True,
                        readonly=True,
                    ),
                    SimpleNamespace(
                        research_rank=3,
                        market_slug="btc-beta",
                        category_id="finance.crypto.btc",
                        assignment_status="watch",
                        memory_use_policy="throttle",
                        research_domain="finance",
                        research_horizon="long_term",
                        research_mode="phase_1_report_only",
                        research_task_codes=(
                            "base_rate_context",
                            "uncertainty_log",
                        ),
                        evidence_gap_codes=("missing_calibration_report",),
                        assignment_reason_codes=("team_memory_readiness_watch",),
                        paper_only=True,
                        report_only=True,
                        readonly=True,
                    ),
                ),
            ),
            SimpleNamespace(
                team_id="politics",
                packet_status="assigned",
                memory_readiness_status="pass",
                memory_use_policy="allow",
                assignment_count=Decimal("1"),
                research_domains=("politics",),
                research_horizons=("long_term",),
                research_modes=("phase_1_report_only",),
                research_task_codes=(
                    "resolution_criteria_review",
                    "polling_method_review",
                ),
                assigned_count=Decimal("1"),
                watch_count=Decimal("0"),
                blocked_count=Decimal("0"),
                evidence_gap_codes=(),
                assignment_reason_codes=("team_research_assignment_assigned",),
                source_reason_codes=("candidate_research_ready",),
                paper_only=True,
                report_only=True,
                readonly=True,
                rows=(
                    SimpleNamespace(
                        research_rank=2,
                        market_slug="politics-alpha",
                        category_id="politics",
                        assignment_status="assigned",
                        memory_use_policy="allow",
                        research_domain="politics",
                        research_horizon="long_term",
                        research_mode="phase_1_report_only",
                        research_task_codes=(
                            "resolution_criteria_review",
                            "polling_method_review",
                        ),
                        evidence_gap_codes=(),
                        assignment_reason_codes=("team_research_assignment_assigned",),
                        paper_only=True,
                        report_only=True,
                        readonly=True,
                    ),
                ),
            ),
        ),
        reason_codes=("team_research_work_packet_watch",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = format_team_research_work_packet_cli_stdout(report)

    assert stdout == (
        "team-research-work-packet: "
        "packet_status=watch "
        "team_packet_count=2 "
        "research_assignment_count=3 "
        "assigned_count=2 "
        "watch_count=1 "
        "blocked_count=0 "
        "team_packets=crypto_btc:watch:watch:throttle:2:"
        "finance:long_term:phase_1_report_only:"
        "resolution_criteria_review|source_map_update|base_rate_context|"
        "uncertainty_log|counterevidence_scan|filing_calendar_scan:"
        "1/1/0:"
        "thin_segment_probability_samples|missing_calibration_report:"
        "team_research_assignment_assigned|team_memory_readiness_watch:"
        "candidate_research_ready:"
        "<redacted-market>:finance.crypto.btc:finance:long_term:phase_1_report_only:"
        "assigned:allow:resolution_criteria_review|source_map_update:none:"
        "team_research_assignment_assigned+"
        "<redacted-market>:finance.crypto.btc:finance:long_term:phase_1_report_only:"
        "watch:throttle:base_rate_context|uncertainty_log:"
        "missing_calibration_report:"
        "team_memory_readiness_watch,"
        "politics:assigned:pass:allow:1:"
        "politics:long_term:phase_1_report_only:"
        "resolution_criteria_review|polling_method_review:1/0/0:none:"
        "team_research_assignment_assigned:candidate_research_ready:"
        "<redacted-market>:politics:politics:long_term:phase_1_report_only:"
        "assigned:allow:resolution_criteria_review|polling_method_review:none:"
        "team_research_assignment_assigned "
        "reason_codes=team_research_work_packet_watch "
        "paper_only=True "
        "report_only=True "
        "readonly=True\n"
    )
    forbidden_fragments = (
        "market_slug",
        "market slug",
        "question",
        "payload_json",
        "payload",
        "dsn",
        "table",
        "wallet",
        "auth",
        "trade",
        "order",
        "recommendation",
        "recommend",
        "rank",
        "position",
        "sizing",
        "notional",
        "shares",
        "buy",
        "sell",
    )
    assert all(fragment not in stdout.lower() for fragment in forbidden_fragments)
    assert "operator_next_step" not in stdout
    assert "dispatch" not in stdout.lower()
    assert "research_rank" not in stdout
    assert ":1:btc-alpha" not in stdout
    assert ":2:politics-alpha" not in stdout
    assert ":3:btc-beta" not in stdout
    assert "btc-alpha" not in stdout
    assert "btc-beta" not in stdout
    assert "politics-alpha" not in stdout
    assert stdout.count("<redacted-market>") == 3


def test_format_team_research_work_packet_cli_stdout_rejects_unsafe_public_values() -> None:
    report = SimpleNamespace(
        packet_status="watch",
        team_packet_count=Decimal("1"),
        research_assignment_count=Decimal("1"),
        assigned_count=Decimal("1"),
        watch_count=Decimal("0"),
        blocked_count=Decimal("0"),
        team_packets=(
            SimpleNamespace(
                team_id="wallet-team",
                packet_status="recommendation-ready",
                memory_readiness_status="auth-required",
                memory_use_policy="position-policy",
                assignment_count=Decimal("1"),
                research_domains=("order-book", "macro"),
                research_horizons=("long_term",),
                research_modes=("phase_1_report_only",),
                research_task_codes=("payload_json_review", "safe_context"),
                assigned_count=Decimal("1"),
                watch_count=Decimal("0"),
                blocked_count=Decimal("0"),
                evidence_gap_codes=("market_slug_gap",),
                assignment_reason_codes=("question_missing",),
                source_reason_codes=("private_table_lookup",),
                paper_only=True,
                report_only=True,
                readonly=True,
                rows=(
                    SimpleNamespace(
                        research_rank=1,
                        market_slug="leaked-market-alpha",
                        question="Will the hidden market resolve yes?",
                        payload_json={"market_slug": "leaked-market-alpha"},
                        dsn="postgresql://user:secret@localhost/db",
                        table_name="private_table",
                        wallet_id="wallet-123",
                        api_key="api-key-123",
                        password="password-123",
                        condition_id="condition-123",
                        token_id="token-123",
                        order_id="order-123",
                        auth_token="auth-123",
                        recommendation_id="recommendation-123",
                        position_id="position-123",
                        category_id="market_slug.category",
                        assignment_status="assigned",
                        memory_use_policy="allow",
                        research_domain="finance",
                        research_horizon="long_term",
                        research_mode="phase_1_report_only",
                        research_task_codes=("resolution_criteria_review",),
                        evidence_gap_codes=("payload_json_gap",),
                        assignment_reason_codes=("team_research_assignment_assigned",),
                        paper_only=True,
                        report_only=True,
                        readonly=True,
                    ),
                ),
            ),
        ),
        reason_codes=("auth_required",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    with pytest.raises(ValueError, match="unsafe public payload"):
        format_team_research_work_packet_cli_stdout(report)


def test_format_team_research_work_packet_cli_stdout_prints_none_for_empty_values() -> None:
    report = SimpleNamespace(
        packet_status="blocked",
        team_packet_count=Decimal("0"),
        research_assignment_count=Decimal("0"),
        assigned_count=Decimal("0"),
        watch_count=Decimal("0"),
        blocked_count=Decimal("0"),
        team_packets=(),
        reason_codes=(),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    stdout = format_team_research_work_packet_cli_stdout(report)

    assert "team_packets=none" in stdout
    assert "reason_codes=none" in stdout


def test_format_team_research_work_packet_cli_stdout_requires_decimal_counts() -> None:
    report = SimpleNamespace(
        packet_status="blocked",
        team_packet_count=0,
        research_assignment_count=Decimal("0"),
        assigned_count=Decimal("0"),
        watch_count=Decimal("0"),
        blocked_count=Decimal("0"),
        team_packets=(),
        reason_codes=(),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    with pytest.raises(ValueError, match="team_packet_count must use Decimal"):
        format_team_research_work_packet_cli_stdout(report)


def test_format_team_research_work_packet_cli_stdout_rejects_false_hard_flags() -> None:
    report = SimpleNamespace(
        packet_status="blocked",
        team_packet_count=Decimal("0"),
        research_assignment_count=Decimal("0"),
        assigned_count=Decimal("0"),
        watch_count=Decimal("0"),
        blocked_count=Decimal("0"),
        team_packets=(),
        reason_codes=(),
        paper_only=True,
        report_only=False,
        readonly=True,
    )

    with pytest.raises(ValueError, match="report_only must be True"):
        format_team_research_work_packet_cli_stdout(report)


def test_format_team_research_work_packet_cli_stdout_rejects_tampered_derived_counts() -> None:
    report = SimpleNamespace(
        packet_status="assigned",
        team_packet_count=Decimal("1"),
        research_assignment_count=Decimal("2"),
        assigned_count=Decimal("1"),
        watch_count=Decimal("0"),
        blocked_count=Decimal("0"),
        team_packets=(
            SimpleNamespace(
                team_id="research_team",
                packet_status="assigned",
                memory_readiness_status="pass",
                memory_use_policy="allow",
                assignment_count=Decimal("1"),
                research_domains=("finance",),
                research_horizons=("long_term",),
                research_modes=("phase_1_report_only",),
                research_task_codes=("resolution_criteria_review",),
                assigned_count=Decimal("1"),
                watch_count=Decimal("0"),
                blocked_count=Decimal("0"),
                evidence_gap_codes=(),
                assignment_reason_codes=("team_research_assignment_assigned",),
                source_reason_codes=("candidate_research_ready",),
                paper_only=True,
                report_only=True,
                readonly=True,
                rows=(
                    SimpleNamespace(
                        market_slug="alpha",
                        category_id="finance",
                        assignment_status="assigned",
                        memory_use_policy="allow",
                        research_domain="finance",
                        research_horizon="long_term",
                        research_mode="phase_1_report_only",
                        research_task_codes=("resolution_criteria_review",),
                        evidence_gap_codes=(),
                        assignment_reason_codes=("team_research_assignment_assigned",),
                        paper_only=True,
                        report_only=True,
                        readonly=True,
                    ),
                ),
            ),
        ),
        reason_codes=("team_research_work_packet_assigned",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    with pytest.raises(ValueError, match="research_assignment_count must match"):
        format_team_research_work_packet_cli_stdout(report)


def test_work_packet_formatter_imports_no_db_env_cli_network_or_filesystem_modules(
    monkeypatch: Any,
) -> None:
    disallowed_import_roots = {
        "asyncpg",
        "dotenv",
        "os",
        "pathlib",
        "polymarket_alpha_lab.cli",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
    }
    imported_names: list[str] = []
    original_import = builtins.__import__

    def tracking_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> ModuleType:
        if level == 0:
            imported_names.append(name)
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", tracking_import)
    sys.modules.pop("polymarket_alpha_lab.team_research_work_packet_cli_format", None)

    importlib.import_module("polymarket_alpha_lab.team_research_work_packet_cli_format")

    imported_roots = {name.partition(".")[0] for name in imported_names}
    assert imported_roots.isdisjoint(disallowed_import_roots)
    assert "polymarket_alpha_lab.cli" not in imported_names
