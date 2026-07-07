from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_team_queue_load_balancer_report import (
    DEFAULT_RESEARCH_TEAM_QUEUE_LOAD_BALANCER_REPORT_CONFIG_VERSION,
    ResearchTeamQueueLoadBalancerConfig,
    ResearchTeamQueueLoadBalancerInputRow,
    ResearchTeamQueueLoadBalancerReasonCodeCount,
    ResearchTeamQueueLoadBalancerReport,
    ResearchTeamQueueLoadBalancerReportRow,
    build_research_team_queue_load_balancer_report,
    research_team_queue_load_balancer_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_queue_load_balancer_report.py",
)


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
        "config_version": (
            DEFAULT_RESEARCH_TEAM_QUEUE_LOAD_BALANCER_REPORT_CONFIG_VERSION
        ),
        "max_pass_pending_review_count": d("5"),
        "max_watch_pending_review_count": d("12"),
        "urgency_watch_threshold": d("0.700000"),
        "urgency_block_threshold": d("0.900000"),
        "max_pass_evidence_gap_count": d("0"),
        "max_watch_evidence_gap_count": d("2"),
        "min_pass_domain_expertise_match_score": d("0.750000"),
        "min_block_domain_expertise_match_score": d("0.500000"),
    }
    values.update(overrides)
    return ResearchTeamQueueLoadBalancerConfig(**values)


def input_row(
    team_key: str = "research.politics.primary",
    *,
    team_domain: str = "politics",
    observed_at: datetime | None = None,
    pending_review_count: Decimal = d("2"),
    urgency_score: Decimal = d("0.300000"),
    evidence_gap_count: Decimal = d("0"),
    domain_expertise_match_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamQueueLoadBalancerInputRow:
    return ResearchTeamQueueLoadBalancerInputRow(
        team_key=team_key,
        team_domain=team_domain,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=15),
        pending_review_count=pending_review_count,
        urgency_score=urgency_score,
        evidence_gap_count=evidence_gap_count,
        domain_expertise_match_score=domain_expertise_match_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchTeamQueueLoadBalancerConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamQueueLoadBalancerReport:
    return build_research_team_queue_load_balancer_report(
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
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_count", "_ratio", "_score", "_seconds")):
            assert type(item) is Decimal


def test_queue_load_balancer_report_reduces_teams_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "research.sports.primary",
                team_domain="sports",
                pending_review_count=d("2"),
                urgency_score=d("0.300000"),
                evidence_gap_count=d("0"),
                domain_expertise_match_score=d("0.900000"),
            ),
            input_row(
                "research.politics.primary",
                team_domain="politics",
                observed_at=GENERATED_AT - timedelta(hours=3),
                pending_review_count=d("14"),
                urgency_score=d("0.920000"),
                evidence_gap_count=d("3"),
                domain_expertise_match_score=d("0.450000"),
            ),
            input_row(
                "research.finance.primary",
                team_domain="finance",
                observed_at=GENERATED_AT - timedelta(hours=1),
                pending_review_count=d("7"),
                urgency_score=d("0.720000"),
                evidence_gap_count=d("1"),
                domain_expertise_match_score=d("0.700000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_TEAM_QUEUE_LOAD_BALANCER_REPORT_CONFIG_VERSION
    )
    assert summary.load_status == "block"
    assert summary.next_step == "block_report_only_research_team_queue_load_balancer"
    assert summary.team_count == d("3.000000")
    assert summary.pass_team_count == d("1.000000")
    assert summary.watch_team_count == d("1.000000")
    assert summary.block_team_count == d("1.000000")
    assert summary.total_pending_review_count == d("23.000000")
    assert summary.pending_pressure_team_count == d("2.000000")
    assert summary.urgent_team_count == d("2.000000")
    assert summary.evidence_gap_team_count == d("2.000000")
    assert summary.domain_expertise_gap_team_count == d("2.000000")
    assert summary.average_urgency_score == d("0.646667")
    assert summary.average_domain_expertise_match_score == d("0.683333")
    assert summary.max_pending_review_count == d("14.000000")
    assert summary.max_evidence_gap_count == d("3.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.team_status, row.team_domain) for row in summary.rows) == (
        ("block", "politics"),
        ("watch", "finance"),
        ("pass", "sports"),
    )

    blocked = summary.rows[0]
    assert blocked.observation_age_seconds == d("10800.000000")
    assert blocked.reason_codes == (
        "research_team_queue_load_balancer_report_pending_review_block",
        "research_team_queue_load_balancer_report_urgency_block",
        "research_team_queue_load_balancer_report_evidence_gap_block",
        "research_team_queue_load_balancer_report_domain_expertise_block",
    )

    watched = summary.rows[1]
    assert watched.observation_age_seconds == d("3600.000000")
    assert watched.reason_codes == (
        "research_team_queue_load_balancer_report_pending_review_pressure",
        "research_team_queue_load_balancer_report_urgency_watch",
        "research_team_queue_load_balancer_report_evidence_gap",
        "research_team_queue_load_balancer_report_domain_expertise_gap",
    )

    passed = summary.rows[2]
    assert passed.team_status == "pass"
    assert passed.reason_codes == (
        "research_team_queue_load_balancer_report_pass",
    )

    assert summary.reason_code_counts == (
        ResearchTeamQueueLoadBalancerReasonCodeCount(
            reason_code="research_team_queue_load_balancer_report_pending_review_block",
            count=d("1.000000"),
            team_ratio=d("0.333333"),
        ),
        ResearchTeamQueueLoadBalancerReasonCodeCount(
            reason_code="research_team_queue_load_balancer_report_urgency_block",
            count=d("1.000000"),
            team_ratio=d("0.333333"),
        ),
        ResearchTeamQueueLoadBalancerReasonCodeCount(
            reason_code="research_team_queue_load_balancer_report_evidence_gap_block",
            count=d("1.000000"),
            team_ratio=d("0.333333"),
        ),
        ResearchTeamQueueLoadBalancerReasonCodeCount(
            reason_code="research_team_queue_load_balancer_report_domain_expertise_block",
            count=d("1.000000"),
            team_ratio=d("0.333333"),
        ),
        ResearchTeamQueueLoadBalancerReasonCodeCount(
            reason_code="research_team_queue_load_balancer_report_pending_review_pressure",
            count=d("1.000000"),
            team_ratio=d("0.333333"),
        ),
        ResearchTeamQueueLoadBalancerReasonCodeCount(
            reason_code="research_team_queue_load_balancer_report_urgency_watch",
            count=d("1.000000"),
            team_ratio=d("0.333333"),
        ),
        ResearchTeamQueueLoadBalancerReasonCodeCount(
            reason_code="research_team_queue_load_balancer_report_evidence_gap",
            count=d("1.000000"),
            team_ratio=d("0.333333"),
        ),
        ResearchTeamQueueLoadBalancerReasonCodeCount(
            reason_code="research_team_queue_load_balancer_report_domain_expertise_gap",
            count=d("1.000000"),
            team_ratio=d("0.333333"),
        ),
        ResearchTeamQueueLoadBalancerReasonCodeCount(
            reason_code="research_team_queue_load_balancer_report_pass",
            count=d("1.000000"),
            team_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )


def test_empty_queue_load_balancer_report_blocks_as_report_only() -> None:
    summary = report(())

    assert summary.load_status == "block"
    assert summary.next_step == "block_report_only_research_team_queue_load_balancer"
    assert summary.team_count == ZERO
    assert summary.pass_team_count == ZERO
    assert summary.watch_team_count == ZERO
    assert summary.block_team_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchTeamQueueLoadBalancerReasonCodeCount(
            reason_code="research_team_queue_load_balancer_report_no_inputs",
            count=d("1.000000"),
            team_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "research_team_queue_load_balancer_report_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_queue_load_balancer_honors_custom_threshold_config() -> None:
    summary = report(
        (
            input_row(
                pending_review_count=d("7"),
                urgency_score=d("0.650000"),
                evidence_gap_count=d("1"),
                domain_expertise_match_score=d("0.720000"),
            ),
        ),
        cfg=config(
            max_pass_pending_review_count=d("8"),
            max_watch_pending_review_count=d("12"),
            urgency_watch_threshold=d("0.800000"),
            urgency_block_threshold=d("0.950000"),
            max_pass_evidence_gap_count=d("2"),
            max_watch_evidence_gap_count=d("3"),
            min_pass_domain_expertise_match_score=d("0.700000"),
            min_block_domain_expertise_match_score=d("0.400000"),
        ),
    )

    assert summary.load_status == "pass"
    assert summary.pass_team_count == d("1.000000")
    assert summary.rows[0].team_status == "pass"
    assert summary.rows[0].reason_codes == (
        "research_team_queue_load_balancer_report_pass",
    )


def test_queue_load_balancer_payload_uses_decimal_strings_and_public_values() -> None:
    summary = report((input_row(),))
    payload = research_team_queue_load_balancer_report_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["payload_kind"] == "research_team_queue_load_balancer_report"
    assert payload["team_count"] == "1.000000"
    assert payload["average_urgency_score"] == "0.300000"
    assert payload["rows"][0]["pending_review_count"] == "2.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(type(value) is int for value in walk_values(payload))


def test_queue_load_balancer_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(ResearchTeamQueueLoadBalancerConfig)
    assert is_dataclass(ResearchTeamQueueLoadBalancerInputRow)
    assert is_dataclass(ResearchTeamQueueLoadBalancerReportRow)
    assert is_dataclass(ResearchTeamQueueLoadBalancerReasonCodeCount)
    assert is_dataclass(ResearchTeamQueueLoadBalancerReport)

    cfg = config()
    source_row = input_row()
    summary = report((source_row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.pending_review_count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].pending_review_count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.team_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("queue-load-v0"))
    with pytest.raises(ValueError, match="max_pass_pending_review_count"):
        config(max_pass_pending_review_count=5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_watch_pending_review_count"):
        config(
            max_pass_pending_review_count=d("12"),
            max_watch_pending_review_count=d("5"),
        )
    with pytest.raises(ValueError, match="urgency_watch_threshold"):
        config(urgency_watch_threshold=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="urgency_block_threshold"):
        config(
            urgency_watch_threshold=d("0.950000"),
            urgency_block_threshold=d("0.900000"),
        )
    with pytest.raises(ValueError, match="max_pass_evidence_gap_count"):
        config(max_pass_evidence_gap_count=d("1.5"))
    with pytest.raises(ValueError, match="min_pass_domain_expertise_match_score"):
        config(min_pass_domain_expertise_match_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="team_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="team_domain"):
        input_row(team_domain="bad domain")
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="pending_review_count"):
        input_row(pending_review_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="urgency_score"):
        input_row(urgency_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="evidence_gap_count"):
        input_row(evidence_gap_count=d("-1"))
    with pytest.raises(ValueError, match="domain_expertise_match_score"):
        input_row(domain_expertise_match_score=d("-0.000001"))
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_research_team_queue_load_balancer_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_team_queue_load_balancer_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_queue_load_balancer_report_and_row_consistency_reject_drift() -> None:
    passed = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            passed,
            reason_codes=(
                "research_team_queue_load_balancer_report_pass",
                "research_team_queue_load_balancer_report_evidence_gap",
            ),
        )
    with pytest.raises(ValueError, match="team_status"):
        replace(passed, team_status="block")
    with pytest.raises(ValueError, match="observation_age_seconds"):
        replace(passed, observation_age_seconds=d("9.000000"))

    with pytest.raises(ValueError, match="pass_team_count"):
        replace(report((input_row(),)), pass_team_count=ZERO)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report((input_row(),)), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report((input_row(),)), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report((input_row(),)), readonly=False)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("research.politics.z", team_domain="politics"),
                input_row("research.politics.a", team_domain="politics"),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    source_row = input_row()
    summary = report((source_row,))

    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_queue_load_balancer_module_has_no_io_store_or_action_surfaces() -> None:
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
    parts = lambda *values: "".join(values)
    forbidden_fragments = (
        parts("live", "_", "trading"),
        parts("wa", "llet"),
        parts("bro", "ker"),
        parts("or", "der"),
        parts("can", "cel"),
        parts("rep", "lace"),
        parts("sign", "ing"),
        parts("ad", "vice"),
        parts("mar", "ket", "_", "slug"),
        parts("ques", "tion"),
        parts("pri", "vate", "_", "key"),
        parts("api", "_", "key"),
        parts("se", "cret"),
        parts("po", "sition"),
        parts("tr", "ade"),
        parts("b", "et"),
        parts("sta", "ke"),
        parts("cli", "ent"),
        parts("re", "quests"),
        parts("h", "ttp"),
        parts("so", "cket"),
        parts("sub", "process"),
        parts("op", "en("),
        parts("path", "lib"),
        parts("net", "work"),
        parts("data", "base"),
        parts("dur", "able"),
        parts("b", "uy"),
        parts("s", "ell"),
        parts("recom", "mend"),
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
