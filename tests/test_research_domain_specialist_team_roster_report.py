from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_domain_specialist_team_roster_report import (
    DEFAULT_RESEARCH_DOMAIN_SPECIALIST_TEAM_ROSTER_CONFIG_VERSION,
    ResearchDomainSpecialistTeamRosterConfig,
    ResearchDomainSpecialistTeamRosterInputRow,
    ResearchDomainSpecialistTeamRosterReasonCodeCount,
    ResearchDomainSpecialistTeamRosterReport,
    ResearchDomainSpecialistTeamRosterRow,
    build_research_domain_specialist_team_roster_report,
    research_domain_specialist_team_roster_report_digest,
    research_domain_specialist_team_roster_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_domain_specialist_team_roster_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchDomainSpecialistTeamRosterConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_DOMAIN_SPECIALIST_TEAM_ROSTER_CONFIG_VERSION
        ),
        "min_specialists_per_domain": d("2"),
        "min_active_researchers_per_domain": d("1"),
        "max_assignments_per_specialist": d("4.000000"),
        "max_review_backlog_per_domain": d("3"),
        "watch_gap_threshold": d("1"),
        "block_gap_threshold": d("2"),
    }
    values.update(overrides)
    return ResearchDomainSpecialistTeamRosterConfig(**values)


def input_row(
    domain: str,
    *,
    team_key: str | None = None,
    specialist_count: Decimal = d("2"),
    active_researcher_count: Decimal = d("1"),
    weekly_research_slots: Decimal = d("8"),
    assigned_topic_count: Decimal = d("6"),
    review_backlog_count: Decimal = d("1"),
    skill_gap_count: Decimal = d("0"),
    last_roster_reviewed_at: datetime | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchDomainSpecialistTeamRosterInputRow:
    return ResearchDomainSpecialistTeamRosterInputRow(
        team_key=team_key or f"research.{domain}.specialists",
        domain=domain,
        specialist_count=specialist_count,
        active_researcher_count=active_researcher_count,
        weekly_research_slots=weekly_research_slots,
        assigned_topic_count=assigned_topic_count,
        review_backlog_count=review_backlog_count,
        skill_gap_count=skill_gap_count,
        last_roster_reviewed_at=(
            last_roster_reviewed_at or GENERATED_AT - timedelta(hours=2)
        ),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchDomainSpecialistTeamRosterConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchDomainSpecialistTeamRosterReport:
    return build_research_domain_specialist_team_roster_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {
            "paper_only",
            "report_only",
            "readonly",
            "reassignment_hint",
        }:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if (
            field.name.endswith(("_count", "_ratio", "_slots"))
            or field.name.startswith(("average_", "max_", "min_"))
            or "gap" in field.name
            or "specialist" in field.name
            or "researcher" in field.name
            or "assignment" in field.name
        ):
            assert type(item) is Decimal


def test_roster_report_covers_core_domains_gaps_and_reassignment_hints() -> None:
    summary = report(
        (
            input_row(
                "crypto",
                specialist_count=d("4"),
                active_researcher_count=d("3"),
                weekly_research_slots=d("18"),
                assigned_topic_count=d("7"),
            ),
            input_row(
                "soccer",
                specialist_count=d("1"),
                active_researcher_count=d("1"),
                weekly_research_slots=d("4"),
                assigned_topic_count=d("7"),
                review_backlog_count=d("4"),
                skill_gap_count=d("1"),
            ),
            input_row(
                "politics",
                specialist_count=d("2"),
                active_researcher_count=d("1"),
                weekly_research_slots=d("6"),
                assigned_topic_count=d("5"),
            ),
            input_row(
                "basketball",
                specialist_count=d("0"),
                active_researcher_count=d("0"),
                weekly_research_slots=d("0"),
                assigned_topic_count=d("5"),
                skill_gap_count=d("1"),
            ),
            input_row("equities"),
            input_row("gold"),
            input_row("other"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_DOMAIN_SPECIALIST_TEAM_ROSTER_CONFIG_VERSION
    )
    assert summary.roster_status == "block"
    assert summary.next_step == "block_report_only_domain_specialist_roster"
    assert summary.domain_count == d("7.000000")
    assert summary.pass_domain_count == d("5.000000")
    assert summary.watch_domain_count == d("1.000000")
    assert summary.block_domain_count == d("1.000000")
    assert summary.gap_domain_count == d("2.000000")
    assert summary.total_specialist_count == d("13.000000")
    assert summary.total_active_researcher_count == d("8.000000")
    assert summary.total_gap_count == d("6.000000")
    assert summary.average_gap_count == d("0.857143")
    assert summary.max_assignments_per_specialist_seen == d("7.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.coverage_status, row.domain) for row in summary.rows) == (
        ("block", "basketball"),
        ("watch", "soccer"),
        ("pass", "crypto"),
        ("pass", "equities"),
        ("pass", "gold"),
        ("pass", "other"),
        ("pass", "politics"),
    )

    blocked = summary.rows[0]
    assert blocked.required_specialist_gap == d("2.000000")
    assert blocked.active_researcher_gap == d("1.000000")
    assert blocked.total_gap_count == d("4.000000")
    assert blocked.assignments_per_specialist == ZERO
    assert blocked.reassignment_hint == "shift_report_only_research_capacity_from_crypto_to_basketball"
    assert blocked.reason_codes == (
        "research_domain_specialist_team_roster_active_gap",
        "research_domain_specialist_team_roster_block_gap",
        "research_domain_specialist_team_roster_specialist_gap",
        "research_domain_specialist_team_roster_skill_gap",
    )

    watched = summary.rows[1]
    assert watched.required_specialist_gap == ONE
    assert watched.active_researcher_gap == ZERO
    assert watched.total_gap_count == d("2.000000")
    assert watched.assignments_per_specialist == d("7.000000")
    assert watched.reassignment_hint == "shift_report_only_research_capacity_from_crypto_to_soccer"
    assert watched.reason_codes == (
        "research_domain_specialist_team_roster_specialist_gap",
        "research_domain_specialist_team_roster_skill_gap",
        "research_domain_specialist_team_roster_backlog_pressure",
        "research_domain_specialist_team_roster_load_pressure",
        "research_domain_specialist_team_roster_watch_gap",
    )

    assert summary.reason_code_counts == (
        ResearchDomainSpecialistTeamRosterReasonCodeCount(
            reason_code="research_domain_specialist_team_roster_active_gap",
            count=ONE,
            domain_ratio=d("0.142857"),
        ),
        ResearchDomainSpecialistTeamRosterReasonCodeCount(
            reason_code="research_domain_specialist_team_roster_block_gap",
            count=ONE,
            domain_ratio=d("0.142857"),
        ),
        ResearchDomainSpecialistTeamRosterReasonCodeCount(
            reason_code="research_domain_specialist_team_roster_specialist_gap",
            count=d("2.000000"),
            domain_ratio=d("0.285714"),
        ),
        ResearchDomainSpecialistTeamRosterReasonCodeCount(
            reason_code="research_domain_specialist_team_roster_skill_gap",
            count=d("2.000000"),
            domain_ratio=d("0.285714"),
        ),
        ResearchDomainSpecialistTeamRosterReasonCodeCount(
            reason_code="research_domain_specialist_team_roster_backlog_pressure",
            count=ONE,
            domain_ratio=d("0.142857"),
        ),
        ResearchDomainSpecialistTeamRosterReasonCodeCount(
            reason_code="research_domain_specialist_team_roster_load_pressure",
            count=ONE,
            domain_ratio=d("0.142857"),
        ),
        ResearchDomainSpecialistTeamRosterReasonCodeCount(
            reason_code="research_domain_specialist_team_roster_watch_gap",
            count=ONE,
            domain_ratio=d("0.142857"),
        ),
        ResearchDomainSpecialistTeamRosterReasonCodeCount(
            reason_code="research_domain_specialist_team_roster_pass",
            count=d("5.000000"),
            domain_ratio=d("0.714286"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for value in (
        "condition_id",
        "slug",
        "wallet",
        "private_key",
        "api_key",
        "secret",
        "credential",
    ):
        assert value not in public


def test_empty_roster_report_blocks_all_expected_domain_gaps() -> None:
    summary = report(())

    assert summary.roster_status == "block"
    assert summary.next_step == "block_report_only_domain_specialist_roster"
    assert summary.domain_count == d("7.000000")
    assert summary.pass_domain_count == ZERO
    assert summary.watch_domain_count == ZERO
    assert summary.block_domain_count == d("7.000000")
    assert summary.gap_domain_count == d("7.000000")
    assert summary.total_specialist_count == ZERO
    assert summary.total_active_researcher_count == ZERO
    assert summary.total_gap_count == d("21.000000")
    assert summary.average_gap_count == d("3.000000")
    assert summary.rows[0].domain == "basketball"
    assert summary.rows[-1].domain == "politics"
    assert all(row.coverage_status == "block" for row in summary.rows)
    assert all(row.reassignment_hint == "add_report_only_research_capacity" for row in summary.rows)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_roster_report_payload_and_digest_are_deterministic_public_and_decimal_safe() -> None:
    rows = (
        input_row("soccer", specialist_count=d("1"), assigned_topic_count=d("6")),
        input_row("crypto", specialist_count=d("4"), active_researcher_count=d("3")),
        input_row("politics"),
        input_row("equities"),
        input_row("gold"),
        input_row("basketball"),
        input_row("other"),
    )
    first = report(rows)
    second = report(tuple(reversed(rows)))

    first_payload = research_domain_specialist_team_roster_report_payload(first)
    second_payload = research_domain_specialist_team_roster_report_payload(second)
    json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_payload["domain_count"] == "7.000000"
    assert first_payload["rows"][0]["domain"] == "soccer"
    assert first_payload["rows"][0]["specialist_count"] == "1.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(first_payload))
    assert not any(isinstance(value, int) for value in walk_values(first_payload) if not isinstance(value, bool))
    assert research_domain_specialist_team_roster_report_digest(first) == (
        research_domain_specialist_team_roster_report_digest(second)
    )
    assert len(research_domain_specialist_team_roster_report_digest(first)) == 64

    public_text = repr(first_payload).lower()
    for value in (
        "condition_id",
        "market_id",
        "source_id",
        "slug",
        "wallet",
        "private_key",
        "api_key",
        "secret",
        "credential",
        "http",
    ):
        assert value not in public_text


def test_roster_report_validates_contracts_statuses_and_flags() -> None:
    assert is_dataclass(ResearchDomainSpecialistTeamRosterConfig)
    assert is_dataclass(ResearchDomainSpecialistTeamRosterInputRow)
    assert is_dataclass(ResearchDomainSpecialistTeamRosterRow)
    assert is_dataclass(ResearchDomainSpecialistTeamRosterReasonCodeCount)
    assert is_dataclass(ResearchDomainSpecialistTeamRosterReport)

    cfg = config()
    source_row = input_row("politics")
    summary = report((source_row,))

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.specialist_count = d("3")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].coverage_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("2")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.roster_status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("roster-v0"))
    with pytest.raises(ValueError, match="min_specialists_per_domain"):
        config(min_specialists_per_domain=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_active_researchers_per_domain"):
        config(min_active_researchers_per_domain=d("0.5"))
    with pytest.raises(ValueError, match="max_assignments_per_specialist"):
        config(max_assignments_per_specialist=_DecimalSubclass("4"))
    with pytest.raises(ValueError, match="watch_gap_threshold"):
        config(watch_gap_threshold=d("2"), block_gap_threshold=d("1"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="team_key"):
        input_row("politics", team_key=" wallet")
    with pytest.raises(ValueError, match="domain"):
        input_row("tennis")
    with pytest.raises(ValueError, match="specialist_count"):
        input_row("politics", specialist_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="active_researcher_count"):
        input_row("politics", active_researcher_count=d("2.5"))
    with pytest.raises(ValueError, match="weekly_research_slots"):
        input_row("politics", weekly_research_slots=d("-0.000001"))
    with pytest.raises(ValueError, match="assigned_topic_count"):
        input_row("politics", assigned_topic_count=Decimal("NaN"))
    with pytest.raises(ValueError, match="last_roster_reviewed_at"):
        input_row(
            "politics",
            last_roster_reviewed_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="last_roster_reviewed_at"):
        report(
            (
                input_row(
                    "politics",
                    last_roster_reviewed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        input_row("politics", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row("politics", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row("politics", readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_research_domain_specialist_team_roster_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_domain_specialist_team_roster_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))
    with pytest.raises(ValueError, match="duplicate"):
        report((input_row("politics"), input_row("politics")))


def test_roster_report_and_rows_reject_manual_drift() -> None:
    summary = report(
        (
            input_row("politics"),
            input_row("crypto"),
            input_row("equities"),
            input_row("gold"),
            input_row("soccer"),
            input_row("basketball"),
            input_row("other"),
        ),
    )
    ready = summary.rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "research_domain_specialist_team_roster_pass",
                "research_domain_specialist_team_roster_watch_gap",
            ),
        )
    with pytest.raises(ValueError, match="coverage_status"):
        replace(ready, coverage_status="ready")
    with pytest.raises(ValueError, match="total_gap_count"):
        replace(ready, total_gap_count=d("9.000000"))
    with pytest.raises(ValueError, match="reassignment_hint"):
        replace(ready, reassignment_hint="transfer_to_private_queue")
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="pass_domain_count"):
        replace(summary, pass_domain_count=ZERO)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary, paper_only=False)


def test_roster_report_public_numeric_fields_are_decimals() -> None:
    source_row = input_row("politics")
    summary = report((source_row,))

    assert_decimal_numeric_fields(config())
    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_roster_module_has_no_io_store_private_or_action_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "auth",
        "wallet",
        "broker",
        " order",
        "cancel",
        "replace",
        "signing",
        "market_id",
        "condition_id",
        "source_id",
        "slug",
        "private_key",
        "api_key",
        "secret",
        "position",
        "trade",
        "bet",
        "stake",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "database",
        "durable",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for value in forbidden_fragments:
        assert value not in lowered
