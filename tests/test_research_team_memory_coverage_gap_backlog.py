from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import research_team_memory_coverage_gap_backlog as api


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def _snapshot(
    *,
    team_key: str,
    memory_scope: str,
    covered: str,
    required: str = "10",
    durable: str = "3",
    stale: str = "0",
    days_old: int | None = 1,
    reason_codes: tuple[str, ...] = (),
) -> api.ResearchTeamMemoryCoverageSnapshot:
    return api.ResearchTeamMemoryCoverageSnapshot(
        team_key=team_key,
        memory_scope=memory_scope,
        covered_topic_count=Decimal(covered),
        required_topic_count=Decimal(required),
        durable_memory_count=Decimal(durable),
        stale_memory_count=Decimal(stale),
        latest_memory_at=(
            None if days_old is None else NOW - timedelta(days=days_old)
        ),
        reason_codes=reason_codes,
    )


def _report(
    snapshots: tuple[api.ResearchTeamMemoryCoverageSnapshot, ...],
) -> api.ResearchTeamMemoryCoverageGapBacklogReport:
    return api.build_research_team_memory_coverage_gap_backlog_report(
        snapshots,
        config=api.ResearchTeamMemoryCoverageGapBacklogConfig(),
        generated_at=NOW,
    )


def _walk_values(value: object) -> list[object]:
    if isinstance(value, dict):
        values: list[object] = list(value.keys())
        for item in value.values():
            values.extend(_walk_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_values(item))
        return values
    return [value]


def _assert_decimal_string_only_payload(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_decimal_string_only_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_decimal_string_only_payload(item)
        return
    assert type(value) is not int
    assert type(value) is not float


def test_builds_pass_watch_and_block_gap_backlog_statuses() -> None:
    report = _report(
        (
            _snapshot(
                team_key="macro_team",
                memory_scope="event_playbooks",
                covered="10",
            ),
            _snapshot(
                team_key="credit_team",
                memory_scope="counterparty_patterns",
                covered="6",
                stale="1",
                days_old=20,
            ),
            _snapshot(
                team_key="policy_team",
                memory_scope="calendar_protocols",
                covered="1",
                durable="0",
                days_old=None,
            ),
        ),
    )

    rows = {(row.team_key, row.memory_scope): row for row in report.backlog_rows}

    assert rows[("macro_team", "event_playbooks")].coverage_status == "pass"
    assert rows[("credit_team", "counterparty_patterns")].coverage_status == "watch"
    assert rows[("policy_team", "calendar_protocols")].coverage_status == "block"
    assert report.status == "block"
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_rejects_wrong_types_and_keeps_public_dataclasses_frozen() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        api.ResearchTeamMemoryCoverageSnapshot(
            team_key="macro_team",
            memory_scope="event_playbooks",
            covered_topic_count=0.5,  # type: ignore[arg-type]
            required_topic_count=Decimal("10"),
            durable_memory_count=Decimal("3"),
            stale_memory_count=Decimal("0"),
            latest_memory_at=NOW,
        )

    with pytest.raises(ValueError, match="ResearchTeamMemoryCoverageSnapshot"):
        api.build_research_team_memory_coverage_gap_backlog_report(
            [object()],
            config=api.ResearchTeamMemoryCoverageGapBacklogConfig(),
            generated_at=NOW,
        )

    with pytest.raises(TypeError):
        class BadSnapshot(api.ResearchTeamMemoryCoverageSnapshot):
            pass

    snapshot = _snapshot(
        team_key="macro_team",
        memory_scope="event_playbooks",
        covered="10",
    )
    with pytest.raises(FrozenInstanceError):
        snapshot.team_key = "other_team"  # type: ignore[misc]


def test_rejects_public_leaks_and_payload_omits_sensitive_surface() -> None:
    with pytest.raises(ValueError, match="unsafe public value"):
        _snapshot(
            team_key="raw_candidate_1",
            memory_scope="event_playbooks",
            covered="10",
        )

    with pytest.raises(ValueError, match="unsafe public value|supported"):
        _snapshot(
            team_key="macro_team",
            memory_scope="source_url_trace",
            covered="10",
        )

    report = _report(
        (
            _snapshot(
                team_key="macro_team",
                memory_scope="event_playbooks",
                covered="10",
            ),
            _snapshot(
                team_key="credit_team",
                memory_scope="counterparty_patterns",
                covered="5",
            ),
        ),
    )
    payload = api.research_team_memory_coverage_gap_backlog_report_payload(report)

    forbidden_terms = (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "ref",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    public_values = json.dumps(payload, sort_keys=True).lower()
    for term in forbidden_terms:
        assert term not in public_values


def test_payload_is_deterministic_and_uses_decimal_strings_only() -> None:
    snapshots = (
        _snapshot(
            team_key="zeta_team",
            memory_scope="operator_notes",
            covered="5",
        ),
        _snapshot(
            team_key="alpha_team",
            memory_scope="event_playbooks",
            covered="10",
        ),
        _snapshot(
            team_key="beta_team",
            memory_scope="calendar_protocols",
            covered="1",
            durable="0",
            days_old=None,
        ),
    )

    payload_a = api.research_team_memory_coverage_gap_backlog_report_payload(
        _report(snapshots),
    )
    payload_b = api.research_team_memory_coverage_gap_backlog_report_payload(
        _report(tuple(reversed(snapshots))),
    )

    assert payload_a == payload_b
    assert json.dumps(payload_a, sort_keys=True) == json.dumps(
        payload_b,
        sort_keys=True,
    )
    assert payload_a["team_scope_count"] == "3.000000"
    _assert_decimal_string_only_payload(payload_a)


def test_report_digest_matches_public_payload_and_changes_with_report() -> None:
    pass_report = _report(
        (
            _snapshot(
                team_key="macro_team",
                memory_scope="event_playbooks",
                covered="10",
            ),
        ),
    )
    watch_report = _report(
        (
            _snapshot(
                team_key="macro_team",
                memory_scope="event_playbooks",
                covered="5",
            ),
        ),
    )

    pass_payload: dict[str, Any] = (
        api.research_team_memory_coverage_gap_backlog_report_payload(pass_report)
    )
    watch_payload = api.research_team_memory_coverage_gap_backlog_report_payload(
        watch_report,
    )

    assert pass_report.public_digest == pass_payload["public_digest"]
    assert pass_report.public_digest == (
        api.research_team_memory_coverage_gap_backlog_digest(pass_report)
    )
    assert watch_report.public_digest == watch_payload["public_digest"]
    assert pass_report.public_digest != watch_report.public_digest
