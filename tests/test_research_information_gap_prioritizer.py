from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
MODULE_PATH = Path("src/polymarket_alpha_lab/research_information_gap_prioritizer.py")


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_information_gap_prioritizer",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def gap(
    gap_id: str,
    *,
    research_area: str = "policy_timing",
    public_gap_summary: str = "Public filing timestamp needs confirmation",
    impact_score: str = "0.100000",
    time_sensitivity_score: str = "0.100000",
    availability_score: str = "0.200000",
    conflict_risk_score: str = "0.000000",
):
    mod = api()
    return mod.ResearchInformationGapInput(
        gap_id=gap_id,
        research_area=research_area,
        public_gap_summary=public_gap_summary,
        impact_score=d(impact_score),
        time_sensitivity_score=d(time_sensitivity_score),
        availability_score=d(availability_score),
        conflict_risk_score=d(conflict_risk_score),
    )


def report(*gaps):
    mod = api()
    return mod.build_research_information_gap_prioritizer_report(
        gaps,
        config=mod.ResearchInformationGapPrioritizerConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def walk_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from walk_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_values(item)
    else:
        yield value


def test_prioritizes_information_gaps_by_decimal_scores_and_status() -> None:
    summary = report(
        gap(
            "gap-clear",
            research_area="calendar",
            public_gap_summary="Public calendar is current",
        ),
        gap(
            "gap-conflict",
            research_area="rules",
            public_gap_summary="Public sources disagree on rule timing",
            impact_score="0.800000",
            time_sensitivity_score="0.700000",
            availability_score="0.600000",
            conflict_risk_score="0.900000",
        ),
        gap(
            "gap-impact",
            research_area="filing",
            public_gap_summary="Public filing details affect event interpretation",
            impact_score="0.900000",
            time_sensitivity_score="0.200000",
            availability_score="0.900000",
            conflict_risk_score="0.100000",
        ),
        gap(
            "gap-time",
            research_area="deadline",
            public_gap_summary="Public deadline update needs fast collection",
            impact_score="0.600000",
            time_sensitivity_score="0.900000",
            availability_score="0.800000",
            conflict_risk_score="0.200000",
        ),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == "research-information-gap-prioritizer-v0"
    assert summary.report_status == "blocked"
    assert summary.next_step == "collect_blocking_information_gaps"
    assert summary.gap_count == d("4")
    assert summary.pass_gap_count == d("1")
    assert summary.watch_gap_count == d("2")
    assert summary.blocked_gap_count == d("1")
    assert summary.high_impact_count == d("3")
    assert summary.high_time_sensitivity_count == d("2")
    assert summary.high_availability_count == d("2")
    assert summary.high_conflict_risk_count == d("1")
    assert summary.max_priority_score == d("0.750000")
    assert summary.average_priority_score == d("0.528750")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64

    assert tuple((row.collection_priority, row.gap_id) for row in summary.rows) == (
        (d("1"), "gap-conflict"),
        (d("2"), "gap-time"),
        (d("3"), "gap-impact"),
        (d("4"), "gap-clear"),
    )

    blocked = summary.rows[0]
    assert blocked.priority_score == d("0.750000")
    assert blocked.gap_status == "blocked"
    assert blocked.reason_codes == (
        "priority_block",
        "impact_watch",
        "time_sensitivity_watch",
        "conflict_risk_block",
    )

    urgent = summary.rows[1]
    assert urgent.priority_score == d("0.655000")
    assert urgent.gap_status == "watch"
    assert urgent.reason_codes == (
        "priority_watch",
        "impact_watch",
        "time_sensitivity_watch",
        "availability_watch",
    )

    easy = summary.rows[2]
    assert easy.priority_score == d("0.605000")
    assert easy.gap_status == "watch"
    assert easy.reason_codes == (
        "priority_watch",
        "impact_watch",
        "availability_watch",
    )

    clear = summary.rows[3]
    assert clear.priority_score == d("0.105000")
    assert clear.gap_status == "pass"
    assert clear.reason_codes == ("priority_pass",)
    assert summary.reason_codes == (
        "information_gap_block",
        "priority_block",
        "priority_watch",
        "impact_watch",
        "time_sensitivity_watch",
        "availability_watch",
        "conflict_risk_block",
    )


def test_sorting_is_deterministic_for_equal_decimal_priority() -> None:
    summary = report(
        gap(
            "gap-b",
            research_area="same",
            impact_score="0.600000",
            time_sensitivity_score="0.600000",
            availability_score="0.600000",
            conflict_risk_score="0.600000",
        ),
        gap(
            "gap-a",
            research_area="same",
            impact_score="0.600000",
            time_sensitivity_score="0.600000",
            availability_score="0.600000",
            conflict_risk_score="0.600000",
        ),
    )

    assert tuple(row.gap_id for row in summary.rows) == ("gap-a", "gap-b")
    assert tuple(row.collection_priority for row in summary.rows) == (d("1"), d("2"))
    assert summary.rows[0].priority_score == summary.rows[1].priority_score


def test_empty_report_passes_without_collection_rows() -> None:
    summary = report()

    assert summary.report_status == "pass"
    assert summary.next_step == "archive_report_only_information_gap_priorities"
    assert summary.gap_count == d("0")
    assert summary.pass_gap_count == d("0")
    assert summary.watch_gap_count == d("0")
    assert summary.blocked_gap_count == d("0")
    assert summary.average_priority_score == d("0.000000")
    assert summary.max_priority_score == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == ("no_information_gaps",)


def test_payload_is_public_json_ready_and_digest_checked() -> None:
    mod = api()
    summary = report(
        gap(
            "gap-conflict",
            research_area="rules",
            impact_score="0.800000",
            time_sensitivity_score="0.700000",
            availability_score="0.600000",
            conflict_risk_score="0.900000",
        ),
    )

    payload = mod.research_information_gap_prioritizer_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["gap_count"] == "1"
    assert payload["max_priority_score"] == "0.750000"
    assert payload["rows"][0]["impact_score"] == "0.800000"
    assert payload["rows"][0]["collection_priority"] == "1"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "https://" not in repr(payload).lower()
    assert "secret" not in repr(payload).lower()

    tampered = dict(payload)
    tampered["gap_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        mod.research_information_gap_prioritizer_payload(tampered)

    tampered_rows = dict(payload)
    tampered_rows["rows"] = [dict(payload["rows"][0])]
    tampered_rows["rows"][0]["priority_score"] = "0.100000"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        mod.research_information_gap_prioritizer_payload(tampered_rows)

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(summary, gap_count=d("2"))

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(summary.rows[0], priority_score=d("0.100000"))


def test_validates_decimal_contracts_flags_duplicates_and_public_text() -> None:
    mod = api()

    assert is_dataclass(mod.ResearchInformationGapPrioritizerConfig)
    assert is_dataclass(mod.ResearchInformationGapInput)
    assert is_dataclass(mod.ResearchInformationGapRow)
    assert is_dataclass(mod.ResearchInformationGapPrioritizerReport)

    item = gap("gap-frozen")
    summary = report(item)
    with pytest.raises(FrozenInstanceError):
        item.gap_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].priority_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.gap_count = d("9")  # type: ignore[misc]

    with pytest.raises(ValueError, match="impact_score must be a Decimal"):
        gap("gap-float", impact_score="0.100000").__class__(
            gap_id="gap-float",
            research_area="policy_timing",
            public_gap_summary="Public filing timestamp needs confirmation",
            impact_score=0.1,
            time_sensitivity_score=d("0.100000"),
            availability_score=d("0.200000"),
            conflict_risk_score=d("0.000000"),
        )
    with pytest.raises(ValueError, match="time_sensitivity_score"):
        gap("gap-precision", time_sensitivity_score="0.1000001")
    with pytest.raises(ValueError, match="availability_score"):
        gap("gap-infinity", availability_score="Infinity")
    with pytest.raises(ValueError, match="conflict_risk_score"):
        gap("gap-negative", conflict_risk_score="-0.000001")
    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="config"):
        mod.build_research_information_gap_prioritizer_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        mod.build_research_information_gap_prioritizer_report(
            (),
            config=mod.ResearchInformationGapPrioritizerConfig(),
            generated_at=datetime(2026, 7, 7, 12, 0),
        )
    with pytest.raises(ValueError, match="duplicate gap_id"):
        report(gap("gap-dupe"), gap("gap-dupe"))
    with pytest.raises(ValueError, match="unsafe public value"):
        gap("gap-unsafe", public_gap_summary="See https://example.invalid/detail")
    with pytest.raises(ValueError, match="paper_only"):
        mod.ResearchInformationGapPrioritizerConfig(paper_only=False)
    with pytest.raises(ValueError, match="weight"):
        mod.ResearchInformationGapPrioritizerConfig(
            impact_weight=d("0.500000"),
            time_sensitivity_weight=d("0.250000"),
            availability_weight=d("0.200000"),
            conflict_risk_weight=d("0.150000"),
        )


def test_module_has_no_external_io_or_float_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "os",
        "pathlib",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "post",
        "put",
        "request",
        "send",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }

    lowered_source = source.lower()
    assert "investment_advice" not in lowered_source
    assert "trade_recommendation" not in lowered_source

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
