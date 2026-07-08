from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(hours=3)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_technology_event_team_memory_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_technology_event_team_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    report = api()
    values = {
        "config_version": "research-technology-event-team-memory-report-v0",
        "watch_min_specialist_count": d("2"),
        "block_min_specialist_count": d("1"),
        "watch_min_playbook_count": d("2"),
        "block_min_playbook_count": d("1"),
        "watch_min_calibration_sample_count": d("30"),
        "block_min_calibration_sample_count": d("10"),
        "watch_max_latest_source_age_hours": d("24.000000"),
        "block_max_latest_source_age_hours": d("72.000000"),
        "watch_min_source_freshness_ratio": d("0.800000"),
        "block_min_source_freshness_ratio": d("0.400000"),
        "watch_min_evidence_reuse_ratio": d("0.700000"),
        "block_min_evidence_reuse_ratio": d("0.300000"),
        "watch_max_calibration_error_ratio": d("0.120000"),
        "block_max_calibration_error_ratio": d("0.250000"),
    }
    values.update(overrides)
    return report.ResearchTechnologyEventTeamMemoryConfig(**values)


def memory_input(**overrides: object):
    report = api()
    values = {
        "team_label": "technology_ai_research",
        "event_family_label": "ai_product_regulatory",
        "specialist_count": d("3"),
        "playbook_count": d("3"),
        "calibration_sample_count": d("48"),
        "latest_source_age_hours": d("6.000000"),
        "source_freshness_ratio": d("0.920000"),
        "evidence_reuse_ratio": d("0.800000"),
        "calibration_error_ratio": d("0.050000"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return report.ResearchTechnologyEventTeamMemoryInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_technology_event_team_memory_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_technology_event_team_memory_scores_pass_watch_and_block_readiness() -> None:
    report = build_report(
        memory_input(
            team_label="technology_regulatory_response",
            event_family_label="regulatory_policy",
            specialist_count=d("0"),
            playbook_count=d("0"),
            calibration_sample_count=d("8"),
            latest_source_age_hours=d("100.000000"),
            source_freshness_ratio=d("0.200000"),
            evidence_reuse_ratio=d("0.100000"),
            calibration_error_ratio=d("0.350000"),
        ),
        memory_input(
            team_label="technology_product_launch",
            event_family_label="product_policy",
            specialist_count=d("1"),
            playbook_count=d("1"),
            calibration_sample_count=d("20"),
            latest_source_age_hours=d("30.000000"),
            source_freshness_ratio=d("0.700000"),
            evidence_reuse_ratio=d("0.550000"),
            calibration_error_ratio=d("0.160000"),
        ),
        memory_input(
            team_label="technology_ai_research",
            event_family_label="ai_model_release",
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "research-technology-event-team-memory-report-v0"
    assert report.team_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.status == "block"
    assert report.paper_queue_action == "paper_technology_event_team_memory_block"
    assert report.reason_codes == (
        "technology_event_team_memory_queue_block",
        "technology_specialist_coverage_block",
        "technology_playbook_coverage_block",
        "source_freshness_block",
        "evidence_reuse_block",
        "calibration_sample_block",
        "calibration_error_block",
        "technology_specialist_coverage_watch",
        "technology_playbook_coverage_watch",
        "source_freshness_watch",
        "evidence_reuse_watch",
        "calibration_sample_watch",
        "calibration_error_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    blocked, watched, passed = report.rows
    assert tuple(row.memory_status for row in report.rows) == ("block", "watch", "pass")
    assert blocked.team_label == "technology_regulatory_response"
    assert blocked.reason_codes == (
        "technology_specialist_coverage_block",
        "technology_playbook_coverage_block",
        "source_freshness_block",
        "evidence_reuse_block",
        "calibration_sample_block",
        "calibration_error_block",
    )
    assert watched.team_label == "technology_product_launch"
    assert watched.reason_codes == (
        "technology_specialist_coverage_watch",
        "technology_playbook_coverage_watch",
        "source_freshness_watch",
        "evidence_reuse_watch",
        "calibration_sample_watch",
        "calibration_error_watch",
    )
    assert passed.reason_codes == ("technology_event_team_memory_ready",)

    assert report.min_specialist_count == d("0")
    assert report.min_playbook_count == d("0")
    assert report.min_calibration_sample_count == d("8")
    assert report.max_latest_source_age_hours == d("100.000000")
    assert report.min_source_freshness_ratio == d("0.200000")
    assert report.min_evidence_reuse_ratio == d("0.100000")
    assert report.max_calibration_error_ratio == d("0.350000")

    assert report.reason_code_counts[0].reason_code == (
        "technology_event_team_memory_ready"
    )
    assert report.reason_code_counts[0].count == d("1")
    assert report.reason_code_counts[0].team_ratio == d("0.333333")


def test_empty_inputs_block_without_raw_identifiers_or_source_text() -> None:
    report = build_report()

    assert report.team_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.status == "block"
    assert report.paper_queue_action == "paper_technology_event_team_memory_block"
    assert report.reason_codes == ("technology_event_team_memory_no_inputs",)
    assert report.reason_code_counts == ()
    assert report.rows == ()

    populated = build_report(memory_input())
    for value in (report, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(("_count", "_hours", "_ratio")):
                assert type(item_value) is Decimal


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    report = api()
    first = build_report(
        memory_input(
            team_label="technology_product_launch",
            event_family_label="product_policy",
            specialist_count=d("1"),
            playbook_count=d("1"),
            calibration_sample_count=d("20"),
            latest_source_age_hours=d("30.000000"),
            source_freshness_ratio=d("0.700000"),
            evidence_reuse_ratio=d("0.550000"),
            calibration_error_ratio=d("0.160000"),
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        memory_input(
            team_label="technology_ai_research",
            event_family_label="ai_model_release",
        ),
        generated_at=datetime(
            2026,
            7,
            8,
            7,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = build_report(
        memory_input(
            team_label="technology_ai_research",
            event_family_label="ai_model_release",
        ),
        memory_input(
            team_label="technology_product_launch",
            event_family_label="product_policy",
            specialist_count=d("1"),
            playbook_count=d("1"),
            calibration_sample_count=d("20"),
            latest_source_age_hours=d("30.000000"),
            source_freshness_ratio=d("0.700000"),
            evidence_reuse_ratio=d("0.550000"),
            calibration_error_ratio=d("0.160000"),
            observed_at=datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
        ),
    )

    payload = report.research_technology_event_team_memory_report_payload(first)
    repeat_payload = report.research_technology_event_team_memory_report_payload(second)

    assert first.generated_at == GENERATED_AT
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T14:00:00+00:00"
    assert payload["team_count"] == "2"
    assert payload["rows"][0]["team_label"] == "technology_product_launch"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T11:00:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_int_or_float_values(payload)
    json.dumps(payload, sort_keys=True)

    unsafe_identifier_keys = {
        "market_id",
        "market_slug",
        "candidate_id",
        "source_id",
        "source_reference",
        "source_url",
        "raw_event_identifier",
        "raw_source_identifier",
        "raw_text",
    }
    assert unsafe_identifier_keys.isdisjoint(payload_keys(payload))
    payload_text = repr(payload).lower()
    for token in (
        "model-release-2026-07",
        "source_reference",
        "market_slug",
        "candidate_id",
        "private-url",
        "wallet",
        "order",
        "trade",
        "live execution",
    ):
        assert token not in payload_text

    tampered = dict(payload)
    tampered["pass_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report.research_technology_event_team_memory_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2"))


def test_public_payload_rejects_raw_identifier_keys_unsafe_flags_and_numbers() -> None:
    report = api()
    payload = report.research_technology_event_team_memory_report_payload(
        build_report(memory_input()),
    )

    for key in (
        "market_id",
        "market_slug",
        "candidate_id",
        "source_id",
        "source_reference",
        "source_url",
        "raw_event_identifier",
        "raw_source_identifier",
        "raw_text",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            report.research_technology_event_team_memory_report_payload(unsafe)

    for value in (
        "model-release-2026-07 event id",
        "vendor feed source reference",
        "market slug",
        "candidate id",
        "raw source text",
        "https://private-url.example/source",
        "wallet signer",
        "order route",
        "trade route",
        "live execution",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            report.research_technology_event_team_memory_report_payload(unsafe)

    numeric = dict(payload)
    numeric["team_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        report.research_technology_event_team_memory_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        report.research_technology_event_team_memory_report_payload(downgraded)


def test_dataclasses_are_frozen_and_enforce_exact_decimal_inputs() -> None:
    row = memory_input()

    with pytest.raises(FrozenInstanceError):
        row.specialist_count = d("4")  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        memory_input(specialist_count=3)
    with pytest.raises(ValueError, match="Decimal"):
        memory_input(source_freshness_ratio=0.12)
    with pytest.raises(ValueError, match="Decimal"):
        memory_input(latest_source_age_hours=_DecimalSubclass("12.000000"))
    with pytest.raises(ValueError, match="integral"):
        memory_input(specialist_count=d("3.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(memory_input(), generated_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="observed_at"):
        memory_input(observed_at=datetime(2026, 7, 8, 13, 0))
    with pytest.raises(ValueError, match="observed_at"):
        memory_input(observed_at=_DatetimeSubclass(2026, 7, 8, 13, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        build_report(memory_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        build_report(memory_input(), memory_input())
    with pytest.raises(ValueError, match="paper_only"):
        memory_input(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(memory_input(), cfg=object())


def test_statuses_materialized_fields_and_report_only_surface() -> None:
    report = api()
    digest = build_report(memory_input())
    row = digest.rows[0]

    assert report.STATUSES == ("pass", "watch", "block")
    assert "ready" not in report.STATUSES
    assert "blocked" not in report.STATUSES

    with pytest.raises(ValueError, match="memory_status"):
        report.ResearchTechnologyEventTeamMemoryRow(
            **{
                **row.__dict__,
                "memory_status": "blocked",
            },
        )

    with pytest.raises(ValueError, match="status"):
        report.ResearchTechnologyEventTeamMemoryReport(
            **{
                **digest.__dict__,
                "status": "watch",
            },
        )

    object.__setattr__(digest.rows[0], "source_freshness_ratio", d("0.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report.research_technology_event_team_memory_report_payload(digest)

    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
    }
    forbidden_terms = (
        "wallet",
        "broker",
        "signing",
        "order",
        "trade",
        "account",
        "network",
        "database",
        "live",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names

    source = MODULE_PATH.read_text().lower()
    assert not any(term in source for term in forbidden_terms)

    for cls in (
        report.ResearchTechnologyEventTeamMemoryConfig,
        report.ResearchTechnologyEventTeamMemoryInput,
        report.ResearchTechnologyEventTeamMemoryRow,
        report.ResearchTechnologyEventTeamMemoryReasonCodeCount,
        report.ResearchTechnologyEventTeamMemoryReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
