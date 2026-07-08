from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_politics_event_team_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_pass_memory_confidence_ratio": d("0.700000"),
        "min_watch_memory_confidence_ratio": d("0.500000"),
        "blocked_contradiction_count": d("2.000000"),
        "blocked_unresolved_gap_count": d("3.000000"),
    }
    values.update(overrides)
    return module.ResearchPoliticsEventTeamMemoryConfig(**values)


def memory_input(
    label: str,
    *,
    prior_event_count: Decimal = d("3.000000"),
    resolved_precedent_count: Decimal = d("2.000000"),
    unresolved_gap_count: Decimal = d("0.000000"),
    contradiction_count: Decimal = d("0.000000"),
    memory_confidence_ratio: Decimal = d("0.850000"),
) -> Any:
    module = api()
    return module.ResearchPoliticsEventTeamMemoryInput(
        event_ref_sha256=sha(f"raw politics event {label}"),
        cluster_ref_sha256=sha(f"raw participant cluster {label}"),
        evidence_ref_sha256=sha(f"https://private.example.invalid/{label}"),
        prior_event_count=prior_event_count,
        resolved_precedent_count=resolved_precedent_count,
        unresolved_gap_count=unresolved_gap_count,
        contradiction_count=contradiction_count,
        memory_confidence_ratio=memory_confidence_ratio,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_politics_event_team_memory_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def assert_no_float_values(value: object) -> None:
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_empty_report_blocks_with_decimal_zeroes_and_report_only_flags() -> None:
    module = api()
    report = build_report()
    payload = module.research_politics_event_team_memory_report_payload(report)

    assert type(report) is module.ResearchPoliticsEventTeamMemoryReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.reason_codes == ("politics_event_team_memory_empty",)
    assert report.event_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_memory_confidence_ratio == d("0.000000")
    assert report.highest_unresolved_gap_count == d("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert payload["status"] == "block"
    assert payload["event_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_builds_deterministic_public_payload_and_digest_without_raw_refs() -> None:
    module = api()
    pass_row = memory_input("pass")
    watch_row = memory_input(
        "watch",
        unresolved_gap_count=d("1.000000"),
        memory_confidence_ratio=d("0.650000"),
    )
    block_row = memory_input(
        "block",
        resolved_precedent_count=d("0.000000"),
        contradiction_count=d("2.000000"),
        memory_confidence_ratio=d("0.400000"),
    )

    report = build_report(pass_row, block_row, watch_row)
    same_report = build_report(watch_row, pass_row, block_row)
    payload = module.research_politics_event_team_memory_report_payload(report)

    assert report.status == "block"
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.reason_codes for row in report.rows) == (
        (
            "politics_event_team_memory_no_precedent_block",
            "politics_event_team_memory_contradiction_block",
            "politics_event_team_memory_low_confidence_block",
        ),
        (
            "politics_event_team_memory_low_confidence_watch",
            "politics_event_team_memory_unresolved_gap_watch",
        ),
        ("politics_event_team_memory_pass",),
    )
    assert report.event_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_memory_confidence_ratio == d("0.633333")
    assert report.highest_unresolved_gap_count == d("1.000000")
    assert payload == module.research_politics_event_team_memory_report_payload(
        same_report,
    )
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["average_memory_confidence_ratio"] == "0.633333"
    assert payload["rows"][0]["memory_confidence_ratio"] == "0.400000"
    assert payload["rows"][0]["event_ref_sha256"] == block_row.event_ref_sha256
    assert_no_float_values(payload)
    json.dumps(payload)

    raw_public_surface = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "raw politics event",
        "raw participant cluster",
        "private.example.invalid",
        "http://",
        "https://",
    ):
        assert forbidden not in raw_public_surface

    expected_digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert module.research_politics_event_team_memory_report_digest(report) == expected_digest
    assert (
        module.research_politics_event_team_memory_report_digest(report)
        == module.research_politics_event_team_memory_report_digest(same_report)
    )


def test_frozen_dataclasses_reject_non_decimal_statuses_raw_refs_and_false_flags() -> None:
    module = api()
    report = build_report(memory_input("frozen"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_POLITICS_EVENT_TEAM_MEMORY_CONFIG_VERSION",
        "RESEARCH_POLITICS_EVENT_TEAM_MEMORY_REPORT_SLUG",
        "ResearchPoliticsEventTeamMemoryConfig",
        "ResearchPoliticsEventTeamMemoryInput",
        "ResearchPoliticsEventTeamMemoryReport",
        "ResearchPoliticsEventTeamMemoryRow",
        "build_research_politics_event_team_memory_report",
        "research_politics_event_team_memory_report_digest",
        "research_politics_event_team_memory_report_payload",
    )
    assert is_dataclass(config())
    assert is_dataclass(memory_input("dataclass"))
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="min_pass_memory_confidence_ratio must be a Decimal"):
        config(min_pass_memory_confidence_ratio=DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="event_ref_sha256 must be a sha256 digest"):
        module.ResearchPoliticsEventTeamMemoryInput(
            event_ref_sha256="raw-politics-event",
            cluster_ref_sha256=sha("cluster"),
            evidence_ref_sha256=sha("evidence"),
            prior_event_count=d("1.000000"),
            resolved_precedent_count=d("1.000000"),
            unresolved_gap_count=d("0.000000"),
            contradiction_count=d("0.000000"),
            memory_confidence_ratio=d("0.900000"),
        )


def test_module_scope_has_no_db_network_wallet_order_or_raw_public_surface() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/research_politics_event_team_memory_report.py",
    )
    module_text = module_path.read_text(encoding="utf-8")
    lowered = module_text.lower()
    for forbidden in (
        "market_slug",
        "candidate_id",
        "source_id",
        "question",
        "http://",
        "https://",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "private_key",
        "credential",
        "read_text",
        "write_text",
    ):
        assert forbidden not in lowered

    tree = ast.parse(module_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
