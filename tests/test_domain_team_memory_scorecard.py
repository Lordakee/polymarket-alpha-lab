from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.domain_team_memory_scorecard import (
    DEFAULT_SCORECARD_DOMAIN_TEAM_IDS,
    DomainTeamMemoryScorecardConfig,
    DomainTeamMemoryScorecardReport,
    DomainTeamMemoryScorecardRow,
    build_domain_team_memory_scorecard_report,
)
from polymarket_alpha_lab.team_memory_readiness_digest import (
    TeamMemoryReadinessDigestReasonCodeCount,
    TeamMemoryReadinessDigestReport,
    TeamMemoryReadinessDigestSourceStatus,
)
from polymarket_alpha_lab.team_memory_readiness_digest_history import (
    TeamMemoryReadinessDigestHistoryReport,
    TeamMemoryReadinessDigestHistoryStatusRow,
)


GENERATED_AT = datetime(2026, 7, 2, 18, 0, tzinfo=UTC)
MODULE_PATH = Path("src/polymarket_alpha_lab/domain_team_memory_scorecard.py")


def test_builds_readonly_decimal_scorecard_for_phase_1_domains() -> None:
    report = build_domain_team_memory_scorecard_report(
        latest_digest=_digest(
            (
                _source_status("politics", "pass"),
                _source_status("crypto_btc", "watch"),
                _source_status("macro_rates", "blocked"),
                _source_status("sports_soccer", "pass"),
                _source_status("sports_basketball", "pass"),
            ),
        ),
        history=_history(history_status="observed"),
        config=DomainTeamMemoryScorecardConfig(),
        generated_at=GENERATED_AT,
    )

    assert report == DomainTeamMemoryScorecardReport(
        generated_at=GENERATED_AT,
        config_version="domain-team-memory-scorecard-v0",
        source_digest_config_version="digest-test-v0",
        source_history_config_version="history-test-v0",
        scorecard_status="blocked",
        domain_count=Decimal("4"),
        pass_domain_count=Decimal("1"),
        watch_domain_count=Decimal("0"),
        blocked_domain_count=Decimal("3"),
        configured_team_count=Decimal("6"),
        latest_team_count=Decimal("5"),
        missing_team_count=Decimal("1"),
        average_memory_score=Decimal("0.541667"),
        lowest_memory_score=Decimal("0.000000"),
        history_status="observed",
        history_report_count=Decimal("2"),
        history_required_report_count=Decimal("2"),
        rows=(
            DomainTeamMemoryScorecardRow(
                domain_id="politics",
                team_ids=("politics",),
                configured_team_count=Decimal("1"),
                latest_team_count=Decimal("1"),
                pass_count=Decimal("1"),
                watch_count=Decimal("0"),
                blocked_count=Decimal("0"),
                missing_team_count=Decimal("0"),
                raw_memory_score=Decimal("1.000000"),
                history_penalty=Decimal("0.000000"),
                memory_score=Decimal("1.000000"),
                memory_status="pass",
                reason_codes=("domain_team_memory_ready",),
            ),
            DomainTeamMemoryScorecardRow(
                domain_id="crypto_btc",
                team_ids=("crypto_btc",),
                configured_team_count=Decimal("1"),
                latest_team_count=Decimal("1"),
                pass_count=Decimal("0"),
                watch_count=Decimal("1"),
                blocked_count=Decimal("0"),
                missing_team_count=Decimal("0"),
                raw_memory_score=Decimal("0.500000"),
                history_penalty=Decimal("0.000000"),
                memory_score=Decimal("0.500000"),
                memory_status="blocked",
                reason_codes=("domain_team_memory_watch",),
            ),
            DomainTeamMemoryScorecardRow(
                domain_id="macro_rates",
                team_ids=("macro_rates",),
                configured_team_count=Decimal("1"),
                latest_team_count=Decimal("1"),
                pass_count=Decimal("0"),
                watch_count=Decimal("0"),
                blocked_count=Decimal("1"),
                missing_team_count=Decimal("0"),
                raw_memory_score=Decimal("0.000000"),
                history_penalty=Decimal("0.000000"),
                memory_score=Decimal("0.000000"),
                memory_status="blocked",
                reason_codes=("domain_team_memory_blocked",),
            ),
            DomainTeamMemoryScorecardRow(
                domain_id="sports",
                team_ids=("sports_soccer", "sports_basketball", "sports_other"),
                configured_team_count=Decimal("3"),
                latest_team_count=Decimal("2"),
                pass_count=Decimal("2"),
                watch_count=Decimal("0"),
                blocked_count=Decimal("0"),
                missing_team_count=Decimal("1"),
                raw_memory_score=Decimal("0.666667"),
                history_penalty=Decimal("0.000000"),
                memory_score=Decimal("0.666667"),
                memory_status="blocked",
                reason_codes=("domain_team_memory_missing",),
            ),
        ),
        reason_codes=(
            "domain_team_memory_scorecard_blocked_rows",
        ),
        derived_validation_digest=report.derived_validation_digest,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(isinstance(value, Decimal) for value in _decimal_report_values(report))
    assert tuple(domain for domain, _teams in DEFAULT_SCORECARD_DOMAIN_TEAM_IDS) == (
        "politics",
        "crypto_btc",
        "macro_rates",
        "sports",
    )


def test_report_exposes_deterministic_safe_payload_and_digest() -> None:
    report = build_domain_team_memory_scorecard_report(
        latest_digest=_digest(
            (
                _source_status("politics", "pass"),
                _source_status("crypto_btc", "pass"),
                _source_status("macro_rates", "pass"),
                _source_status("sports_soccer", "pass"),
                _source_status("sports_basketball", "pass"),
                _source_status("sports_other", "pass"),
            ),
        ),
        history=_history(history_status="observed"),
        config=DomainTeamMemoryScorecardConfig(),
        generated_at=GENERATED_AT,
    )
    rebuilt = build_domain_team_memory_scorecard_report(
        latest_digest=_digest(
            (
                _source_status("sports_other", "pass"),
                _source_status("sports_basketball", "pass"),
                _source_status("sports_soccer", "pass"),
                _source_status("macro_rates", "pass"),
                _source_status("crypto_btc", "pass"),
                _source_status("politics", "pass"),
            ),
        ),
        history=_history(history_status="observed"),
        config=DomainTeamMemoryScorecardConfig(),
        generated_at=GENERATED_AT,
    )

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert rebuilt.derived_validation_digest == report.derived_validation_digest

    payload = report.payload
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["generated_at"] == "2026-07-02T18:00:00+00:00"
    assert payload["domain_count"] == "4"
    assert payload["average_memory_score"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["memory_score"] == "1.000000"
    assert payload["rows"][0]["paper_only"] is True
    _assert_no_float_values(payload)


def test_payload_helper_rejects_unsafe_public_payload_and_flag_downgrades() -> None:
    import polymarket_alpha_lab.domain_team_memory_scorecard as api

    report = build_domain_team_memory_scorecard_report(
        latest_digest=_digest((_source_status("politics", "pass"),)),
        history=_history(history_status="observed"),
        config=DomainTeamMemoryScorecardConfig(),
        generated_at=GENERATED_AT,
    )

    payload = api.domain_team_memory_scorecard_payload(report)
    assert payload == report.payload
    assert api.domain_team_memory_scorecard_payload(payload) == payload

    with pytest.raises(ValueError, match="unsafe public payload"):
        api.domain_team_memory_scorecard_payload({**payload, "wallet_id": "redacted"})

    with pytest.raises(ValueError, match="unsafe public payload"):
        api.domain_team_memory_scorecard_payload({**payload, "safe_key": "network note"})

    with pytest.raises(ValueError, match="readonly"):
        api.domain_team_memory_scorecard_payload({**payload, "readonly": False})

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, average_memory_score=Decimal("0.500000"))


def test_scorecard_dataclasses_reject_unsafe_public_identifiers() -> None:
    with pytest.raises(ValueError, match="unsafe public payload"):
        DomainTeamMemoryScorecardConfig(config_version="live_config")

    with pytest.raises(ValueError, match="unsafe public payload"):
        DomainTeamMemoryScorecardConfig(
            domain_team_ids=(("wallet_domain", ("politics",)),),
        )

    safe_row = DomainTeamMemoryScorecardRow(
        domain_id="politics",
        team_ids=("politics",),
        configured_team_count=Decimal("1"),
        latest_team_count=Decimal("1"),
        pass_count=Decimal("1"),
        watch_count=Decimal("0"),
        blocked_count=Decimal("0"),
        missing_team_count=Decimal("0"),
        raw_memory_score=Decimal("1.000000"),
        history_penalty=Decimal("0.000000"),
        memory_score=Decimal("1.000000"),
        memory_status="pass",
        reason_codes=("domain_team_memory_ready",),
    )
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(safe_row, domain_id="network_domain")


def test_history_blocked_penalty_flows_to_rows_and_report_reason_codes() -> None:
    report = build_domain_team_memory_scorecard_report(
        latest_digest=_digest(
            (
                _source_status("politics", "pass"),
                _source_status("crypto_btc", "pass"),
                _source_status("macro_rates", "pass"),
                _source_status("sports_soccer", "pass"),
                _source_status("sports_basketball", "pass"),
                _source_status("sports_other", "pass"),
            ),
        ),
        history=_history(history_status="blocked"),
        config=DomainTeamMemoryScorecardConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.scorecard_status == "blocked"
    assert report.reason_codes == (
        "domain_team_memory_scorecard_history_blocked",
        "domain_team_memory_scorecard_watch_rows",
    )
    assert report.average_memory_score == Decimal("0.750000")
    assert all(row.history_penalty == Decimal("0.250000") for row in report.rows)
    assert all(row.memory_score == Decimal("0.750000") for row in report.rows)
    assert all(row.memory_status == "watch" for row in report.rows)
    assert all(
        row.reason_codes == ("domain_team_memory_history_blocked",)
        for row in report.rows
    )


def test_config_rejects_non_decimal_thresholds_duplicate_teams_and_unsafe_flags() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        DomainTeamMemoryScorecardConfig(watch_threshold=0.75)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="watch_threshold"):
        DomainTeamMemoryScorecardConfig(
            watch_threshold=Decimal("1.000000"),
            pass_threshold=Decimal("0.750000"),
        )

    with pytest.raises(ValueError, match="unique"):
        DomainTeamMemoryScorecardConfig(
            domain_team_ids=(
                ("politics", ("politics",)),
                ("politics_copy", ("politics",)),
            ),
        )

    with pytest.raises(ValueError, match="paper_only"):
        DomainTeamMemoryScorecardConfig(paper_only=False)


def test_dataclasses_are_frozen_and_validate_decimal_consistency() -> None:
    row = DomainTeamMemoryScorecardRow(
        domain_id="politics",
        team_ids=("politics",),
        configured_team_count=Decimal("1"),
        latest_team_count=Decimal("1"),
        pass_count=Decimal("1"),
        watch_count=Decimal("0"),
        blocked_count=Decimal("0"),
        missing_team_count=Decimal("0"),
        raw_memory_score=Decimal("1.000000"),
        history_penalty=Decimal("0.000000"),
        memory_score=Decimal("1.000000"),
        memory_status="pass",
        reason_codes=("domain_team_memory_ready",),
    )

    with pytest.raises(FrozenInstanceError):
        row.memory_score = Decimal("0.500000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        replace(row, memory_score=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="integral"):
        replace(row, configured_team_count=Decimal("1.100000"))

    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("domain_team_memory_watch",))

    with pytest.raises(ValueError, match="memory_score"):
        replace(row, memory_score=Decimal("0.500000"))


def test_rejects_non_report_inputs_and_non_canonical_generated_at() -> None:
    with pytest.raises(ValueError, match="latest_digest"):
        build_domain_team_memory_scorecard_report(
            latest_digest=object(),  # type: ignore[arg-type]
            history=_history(history_status="observed"),
            config=DomainTeamMemoryScorecardConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        build_domain_team_memory_scorecard_report(
            latest_digest=_digest((_source_status("politics", "pass"),)),
            history=_history(history_status="observed"),
            config=DomainTeamMemoryScorecardConfig(),
            generated_at=datetime(2026, 7, 2, 18, 0),
        )

    with pytest.raises(ValueError, match="readonly"):
        build_domain_team_memory_scorecard_report(
            latest_digest=replace(_digest((_source_status("politics", "pass"),)), readonly=False),
            history=_history(history_status="observed"),
            config=DomainTeamMemoryScorecardConfig(),
            generated_at=GENERATED_AT,
        )


def test_public_surface_is_pure_readonly_and_advice_free() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {"__import__", "eval", "exec", "open", "print"}
    forbidden_source_fragments = (
        "account",
        "advice",
        "auth",
        "buy",
        "cancel",
        "credential",
        "dotenv",
        "environ",
        "fast",
        "file",
        "invest",
        "live",
        "order",
        "private_key",
        "rank",
        "recommend",
        "request",
        "sell",
        "socket",
        "store",
        "submit",
        "supabase",
        "trade",
        "urllib",
        "wallet",
    )

    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module] if node.module is not None else []
        else:
            names = []
        for name in names:
            root = name.split(".", maxsplit=1)[0]
            if root in forbidden_import_roots:
                violations.append(f"forbidden import {name}")

        if isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in forbidden_call_names:
                violations.append(f"forbidden call {call_name}")

    lowered_source = source.lower()
    for fragment in forbidden_source_fragments:
        if fragment in lowered_source:
            violations.append(f"forbidden source fragment {fragment}")

    assert sorted(set(violations)) == []

    import polymarket_alpha_lab.domain_team_memory_scorecard as api

    assert api.__all__ == (
        "DEFAULT_DOMAIN_TEAM_MEMORY_SCORECARD_CONFIG_VERSION",
        "DEFAULT_SCORECARD_DOMAIN_TEAM_IDS",
        "DomainTeamMemoryScorecardConfig",
        "DomainTeamMemoryScorecardReport",
        "DomainTeamMemoryScorecardRow",
        "build_domain_team_memory_scorecard_report",
        "domain_team_memory_scorecard_payload",
    )
    row_fields = {field.name for field in fields(api.DomainTeamMemoryScorecardRow)}
    report_fields = {field.name for field in fields(api.DomainTeamMemoryScorecardReport)}
    assert "question" not in row_fields
    assert "question" not in report_fields


def _digest(
    statuses: tuple[TeamMemoryReadinessDigestSourceStatus, ...],
) -> TeamMemoryReadinessDigestReport:
    pass_count = sum(1 for status in statuses if status.gate_status == "pass")
    watch_count = sum(1 for status in statuses if status.gate_status == "watch")
    blocked_count = sum(1 for status in statuses if status.gate_status == "blocked")
    if blocked_count:
        digest_status = "blocked"
        reason_code = "team_memory_readiness_digest_blocked_sources_present"
    elif watch_count:
        digest_status = "watch"
        reason_code = "team_memory_readiness_digest_watch_sources_present"
    elif statuses:
        digest_status = "pass"
        reason_code = "team_memory_readiness_digest_passed"
    else:
        digest_status = "blocked"
        reason_code = "team_memory_readiness_digest_empty_sources"
    return TeamMemoryReadinessDigestReport(
        generated_at=GENERATED_AT - timedelta(minutes=5),
        config_version="digest-test-v0",
        digest_status=digest_status,
        recommended_next_step={
            "pass": "allow_team_memory_readiness_use",
            "watch": "throttle_team_memory_readiness_use",
            "blocked": "block_team_memory_readiness_use",
        }[digest_status],
        team_count=len(statuses),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        source_statuses=statuses,
        source_config_versions=tuple(
            sorted(
                (status.team_id, status.source_config_version)
                for status in statuses
            ),
        ),
        reason_code_counts=(
            TeamMemoryReadinessDigestReasonCodeCount(
                reason_code=reason_code,
                count=1,
            ),
        ),
        reason_codes=(reason_code,),
    )


def _source_status(
    team_id: str,
    gate_status: str,
) -> TeamMemoryReadinessDigestSourceStatus:
    return TeamMemoryReadinessDigestSourceStatus(
        team_id=team_id,
        gate_status=gate_status,
        recommended_next_step={
            "pass": "allow_team_memory_readiness_use",
            "watch": "throttle_team_memory_readiness_use",
            "blocked": "block_team_memory_readiness_use",
        }[gate_status],
        source_config_version=f"{team_id}-memory-source-v0",
        latest_snapshot_age_seconds=60,
        source_snapshot_count=2,
        source_required_snapshot_count=2,
        source_status="ready" if gate_status == "pass" else gate_status,
    )


def _history(history_status: str) -> TeamMemoryReadinessDigestHistoryReport:
    reason_codes = () if history_status == "observed" else ("insufficient_history",)
    return TeamMemoryReadinessDigestHistoryReport(
        generated_at=GENERATED_AT - timedelta(minutes=1),
        config_version="history-test-v0",
        history_status=history_status,
        report_count=2 if history_status == "observed" else 1,
        required_report_count=2,
        first_report_generated_at=GENERATED_AT - timedelta(minutes=10),
        latest_report_generated_at=GENERATED_AT - timedelta(minutes=5),
        status_rows=(
            TeamMemoryReadinessDigestHistoryStatusRow(
                digest_status="pass",
                report_count=2 if history_status == "observed" else 1,
            ),
            TeamMemoryReadinessDigestHistoryStatusRow(
                digest_status="watch",
                report_count=0,
            ),
            TeamMemoryReadinessDigestHistoryStatusRow(
                digest_status="blocked",
                report_count=0,
            ),
        ),
        latest_digest_status="pass",
        latest_team_count=6,
        latest_pass_count=6,
        latest_watch_count=0,
        latest_blocked_count=0,
        team_count_delta=0,
        pass_count_delta=0,
        watch_count_delta=0,
        blocked_count_delta=0,
        duplicate_latest_generated_at=False,
        reason_codes=reason_codes,
    )


def _decimal_report_values(
    report: DomainTeamMemoryScorecardReport,
) -> tuple[Decimal, ...]:
    values = [
        report.domain_count,
        report.pass_domain_count,
        report.watch_domain_count,
        report.blocked_domain_count,
        report.configured_team_count,
        report.latest_team_count,
        report.missing_team_count,
        report.average_memory_score,
        report.lowest_memory_score,
        report.history_report_count,
        report.history_required_report_count,
    ]
    for row in report.rows:
        values.extend(
            (
                row.configured_team_count,
                row.latest_team_count,
                row.pass_count,
                row.watch_count,
                row.blocked_count,
                row.missing_team_count,
                row.raw_memory_score,
                row.history_penalty,
                row.memory_score,
            ),
        )
    return tuple(values)


def _assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for nested_value in value.values():
            _assert_no_float_values(nested_value)
    if isinstance(value, (list, tuple)):
        for nested_value in value:
            _assert_no_float_values(nested_value)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
