from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_team_queue_load_balancer import (
    DEFAULT_RESEARCH_TEAM_QUEUE_LOAD_BALANCER_CONFIG_VERSION,
    ResearchTeamQueueLoadBalancerConfig,
    ResearchTeamQueueLoadBalancerInputRow,
    ResearchTeamQueueLoadBalancerReport,
    ResearchTeamQueueLoadBalancerRoutedRow,
    ResearchTeamQueueLoadBalancerTeamLoad,
    ResearchTeamQueueLoadBalancerTeamRow,
    build_research_team_queue_load_balancer_report,
    format_research_team_queue_load_balancer_digest,
    research_team_queue_load_balancer_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path("src/polymarket_alpha_lab/research_team_queue_load_balancer.py")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchTeamQueueLoadBalancerConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_TEAM_QUEUE_LOAD_BALANCER_CONFIG_VERSION,
        "team_ids": ("politics", "crypto", "macro", "gold", "soccer", "basketball"),
        "pass_load_ratio_threshold": d("0.800000"),
        "block_load_ratio_threshold": d("1.000000"),
        "min_evidence_count": d("2.000000"),
        "stale_queue_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return ResearchTeamQueueLoadBalancerConfig(**values)


def team_load(
    team_id: str,
    *,
    open_load_points: Decimal = ZERO,
    capacity_points: Decimal = d("10.000000"),
    open_item_count: Decimal = ZERO,
) -> ResearchTeamQueueLoadBalancerTeamLoad:
    return ResearchTeamQueueLoadBalancerTeamLoad(
        team_id=team_id,
        open_load_points=open_load_points,
        capacity_points=capacity_points,
        open_item_count=open_item_count,
    )


def queue_item(
    private_queue_key: str = "raw-candidate-alpha",
    *,
    research_group: str = "politics",
    queued_at: datetime | None = None,
    effort_points: Decimal = d("1.000000"),
    priority_score: Decimal = d("0.500000"),
    evidence_count: Decimal = d("2.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamQueueLoadBalancerInputRow:
    return ResearchTeamQueueLoadBalancerInputRow(
        private_queue_key=private_queue_key,
        research_group=research_group,
        queued_at=queued_at or GENERATED_AT - timedelta(minutes=30),
        effort_points=effort_points,
        priority_score=priority_score,
        evidence_count=evidence_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    loads: tuple[ResearchTeamQueueLoadBalancerTeamLoad, ...],
    rows: tuple[ResearchTeamQueueLoadBalancerInputRow, ...],
    *,
    cfg: ResearchTeamQueueLoadBalancerConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamQueueLoadBalancerReport:
    return build_research_team_queue_load_balancer_report(
        loads,
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
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_count", "_points", "_ratio", "_score", "_seconds")):
            assert type(item) is Decimal


def base_loads() -> tuple[ResearchTeamQueueLoadBalancerTeamLoad, ...]:
    return (
        team_load("politics", open_load_points=d("2.000000"), open_item_count=d("2.000000")),
        team_load("crypto", open_load_points=d("9.000000"), open_item_count=d("6.000000")),
        team_load("macro", open_load_points=d("4.000000"), open_item_count=d("3.000000")),
        team_load("gold", open_load_points=d("1.000000"), open_item_count=d("1.000000")),
        team_load("soccer", open_load_points=d("1.000000"), open_item_count=d("1.000000")),
        team_load("basketball", open_load_points=d("0.000000"), open_item_count=d("0.000000")),
    )


def test_queue_load_balancer_routes_overflow_and_preserves_public_loads() -> None:
    summary = report(
        base_loads(),
        (
            queue_item(
                "raw-crypto-overflow-42",
                research_group="crypto",
                queued_at=GENERATED_AT - timedelta(hours=2),
                effort_points=d("4.000000"),
                priority_score=d("0.950000"),
            ),
            queue_item(
                "raw-politics-briefing-17",
                research_group="politics",
                effort_points=d("2.000000"),
                priority_score=d("0.400000"),
            ),
            queue_item(
                "raw-macro-calendar-08",
                research_group="macro",
                effort_points=d("4.000000"),
                priority_score=d("0.700000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == DEFAULT_RESEARCH_TEAM_QUEUE_LOAD_BALANCER_CONFIG_VERSION
    assert summary.report_status == "watch"
    assert summary.next_step == "review_watch_research_team_queue_load"
    assert summary.team_count == d("6.000000")
    assert summary.queued_item_count == d("3.000000")
    assert summary.pass_team_count == d("5.000000")
    assert summary.watch_team_count == d("1.000000")
    assert summary.block_team_count == ZERO
    assert summary.total_open_load_points == d("17.000000")
    assert summary.total_assigned_load_points == d("10.000000")
    assert summary.max_projected_load_ratio == d("0.900000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.team_id for row in summary.team_rows) == (
        "basketball",
        "crypto",
        "gold",
        "macro",
        "politics",
        "soccer",
    )
    assert tuple((row.team_id, row.team_status) for row in summary.team_rows) == (
        ("basketball", "pass"),
        ("crypto", "watch"),
        ("gold", "pass"),
        ("macro", "pass"),
        ("politics", "pass"),
        ("soccer", "pass"),
    )

    routed = tuple(
        (row.research_group, row.routed_team_id, row.assignment_status)
        for row in summary.routed_rows
    )
    assert routed == (
        ("crypto", "basketball", "pass"),
        ("macro", "macro", "pass"),
        ("politics", "politics", "pass"),
    )
    assert summary.team_rows[0].assigned_load_points == d("4.000000")
    assert summary.team_rows[3].projected_load_ratio == d("0.800000")
    assert summary.reason_codes == (
        "research_team_queue_load_balancer_load_watch",
    )
    assert summary.public_digest.startswith("sha256:")

    public = repr(asdict(summary)).lower()
    for value in (
        "raw-crypto-overflow-42",
        "raw-politics-briefing-17",
        "raw-macro-calendar-08",
    ):
        assert value not in public


def test_queue_load_balancer_statuses_are_pass_watch_and_block_only() -> None:
    pass_summary = report(
        (team_load("politics", open_load_points=d("1.000000")),),
        (queue_item("pass-item", research_group="politics"),),
        cfg=config(team_ids=("politics",)),
    )
    watch_summary = report(
        (team_load("politics", open_load_points=d("9.000000")),),
        (),
        cfg=config(team_ids=("politics",)),
    )
    block_summary = report(
        (team_load("politics", open_load_points=d("11.000000")),),
        (),
        cfg=config(team_ids=("politics",)),
    )

    assert pass_summary.report_status == "pass"
    assert watch_summary.report_status == "watch"
    assert block_summary.report_status == "block"
    assert pass_summary.team_rows[0].team_status == "pass"
    assert watch_summary.team_rows[0].team_status == "watch"
    assert block_summary.team_rows[0].team_status == "block"
    assert {
        pass_summary.report_status,
        watch_summary.report_status,
        block_summary.report_status,
        pass_summary.routed_rows[0].assignment_status,
    } <= {"pass", "watch", "block"}


def test_queue_load_balancer_rejects_non_decimal_and_mutation() -> None:
    cfg = config()
    load = team_load("politics")
    source_row = queue_item()
    summary = report((load,), (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        load.open_load_points = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.effort_points = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.team_rows[0].team_status = "block"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("research-team-queue-load-balancer-v0"))
    with pytest.raises(ValueError, match="team_ids"):
        config(team_ids=("politics", "politics"))
    with pytest.raises(ValueError, match="pass_load_ratio_threshold"):
        config(pass_load_ratio_threshold=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="block_load_ratio_threshold"):
        config(
            pass_load_ratio_threshold=d("1.100000"),
            block_load_ratio_threshold=d("1.000000"),
        )
    with pytest.raises(ValueError, match="min_evidence_count"):
        config(min_evidence_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="team_id"):
        team_load(" bad")
    with pytest.raises(ValueError, match="open_load_points"):
        team_load("politics", open_load_points=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="capacity_points"):
        team_load("politics", capacity_points=d("-0.000001"))
    with pytest.raises(ValueError, match="private_queue_key"):
        queue_item("")
    with pytest.raises(ValueError, match="research_group"):
        queue_item(research_group="live_surface")
    with pytest.raises(ValueError, match="queued_at"):
        queue_item(queued_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="effort_points"):
        queue_item(effort_points=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="priority_score"):
        queue_item(priority_score=d("1.000001"))
    with pytest.raises(ValueError, match="evidence_count"):
        queue_item(evidence_count=d("1.5"))
    with pytest.raises(ValueError, match="team loads"):
        report((object(),), ())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="input rows"):
        report((team_load("politics"),), (object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        build_research_team_queue_load_balancer_report(
            (team_load("politics"),),
            (),
            config=config(team_ids=("politics",)),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )


def test_queue_load_balancer_payload_rejects_public_leaks() -> None:
    summary = report(
        (team_load("crypto"),),
        (
            queue_item(
                "raw_candidate_id=abc123 market_id=0xabc market_slug=secret-question "
                "source_url=https://source.example/a?token=hidden",
                research_group="crypto",
            ),
        ),
        cfg=config(team_ids=("crypto",)),
    )
    payload = research_team_queue_load_balancer_payload(summary)
    public = repr(payload).lower()

    for value in (
        "raw_candidate_id",
        "abc123",
        "market_id",
        "market_slug",
        "secret-question",
        "source_url",
        "source.example",
        "https://",
        "token=hidden",
        "dsn",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert value not in public

    assert payload["routed_rows"][0]["public_queue_key"].startswith("sha256:")
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(type(value) is int for value in walk_values(payload))

    with pytest.raises(ValueError, match="unsafe"):
        replace(
            summary.routed_rows[0],
            public_queue_key="https://source.example/raw_candidate_id=abc123",
        )


def test_queue_load_balancer_payload_is_deterministic_for_reordered_inputs() -> None:
    rows = (
        queue_item(
            "raw-crypto-overflow-42",
            research_group="crypto",
            queued_at=GENERATED_AT - timedelta(hours=2),
            effort_points=d("4.000000"),
            priority_score=d("0.950000"),
        ),
        queue_item(
            "raw-politics-briefing-17",
            research_group="politics",
            effort_points=d("2.000000"),
            priority_score=d("0.400000"),
        ),
        queue_item(
            "raw-macro-calendar-08",
            research_group="macro",
            effort_points=d("4.000000"),
            priority_score=d("0.700000"),
        ),
    )

    left = research_team_queue_load_balancer_payload(report(base_loads(), rows))
    right = research_team_queue_load_balancer_payload(report(tuple(reversed(base_loads())), tuple(reversed(rows))))

    assert left == right
    assert json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


def test_queue_load_balancer_report_and_digest_are_consistent() -> None:
    summary = report((team_load("politics"),), (queue_item("digest-row", research_group="politics"),), cfg=config(team_ids=("politics",)))
    payload = research_team_queue_load_balancer_payload(summary)
    digest = format_research_team_queue_load_balancer_digest(summary)

    assert payload["public_digest"] == summary.public_digest
    assert f"status={summary.report_status}" in digest
    assert f"queued_items={summary.queued_item_count}" in digest
    assert f"public_digest={summary.public_digest}" in digest

    with pytest.raises(ValueError, match="public_digest"):
        replace(summary, public_digest="sha256:bad")
    with pytest.raises(ValueError, match="report_status"):
        replace(summary, report_status="ready")
    with pytest.raises(ValueError, match="queued_item_count"):
        replace(summary, queued_item_count=ZERO)


def test_queue_load_balancer_public_numeric_fields_are_decimals() -> None:
    summary = report((team_load("politics"),), (queue_item("decimal-row", research_group="politics"),), cfg=config(team_ids=("politics",)))

    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.team_rows[0])
    assert_decimal_numeric_fields(summary.routed_rows[0])


def test_queue_load_balancer_module_has_no_io_or_execution_surfaces() -> None:
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
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        " buy",
        " sell",
        "recommend",
        "live_trading",
        "auth",
        "client",
        "network",
        "database",
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
