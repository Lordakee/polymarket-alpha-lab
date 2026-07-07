from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_domain_memory_summary.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_memory_summary",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-domain-memory-summary-test",
        "domain_ids": ("politics", "macro", "crypto"),
        "min_pass_experience_count": d("20"),
        "min_watch_experience_count": d("5"),
        "max_pass_error_pattern_rate": d("0.100000"),
        "max_watch_error_pattern_rate": d("0.250000"),
        "min_pass_postmortem_quality_rate": d("0.800000"),
        "min_watch_postmortem_quality_rate": d("0.500000"),
        "min_pass_memory_quality_score": d("0.750000"),
        "min_watch_memory_quality_score": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainMemorySummaryConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "domain_id": "politics",
        "team_id": "research_team_alpha",
        "experience_count": d("30"),
        "error_pattern_count": d("2"),
        "postmortem_count": d("10"),
        "high_quality_postmortem_count": d("9"),
        "memory_quality_score": d("0.800000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainMemoryObservation(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_memory_summary(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if isinstance(value, datetime):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate_id",
        "candidate",
        "market_id",
        "market_slug",
        "market_question",
        "question",
        "http://",
        "https://",
        "source_ref",
        "source_refs",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def test_public_api_declares_report_only_domain_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SUMMARY_CONFIG_VERSION == (
        "research-team-domain-memory-summary-v0"
    )
    assert module.DEFAULT_RESEARCH_TEAM_MEMORY_DOMAINS == (
        "politics",
        "macro",
        "crypto",
        "equity_index",
        "gold",
        "soccer",
        "basketball",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SUMMARY_CONFIG_VERSION",
        "DEFAULT_RESEARCH_TEAM_MEMORY_DOMAINS",
        "ResearchTeamDomainMemorySummaryConfig",
        "ResearchTeamDomainMemoryObservation",
        "ResearchTeamDomainMemorySummaryRow",
        "ResearchTeamDomainMemorySummaryReport",
        "build_research_team_domain_memory_summary",
        "research_team_domain_memory_summary_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(module.ResearchTeamDomainMemorySummaryConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True


def test_aggregates_domain_memory_into_pass_watch_block_rows() -> None:
    report = build_report(
        observation(domain_id="politics", team_id="team_politics"),
        observation(
            domain_id="macro",
            team_id="team_macro",
            experience_count=d("12"),
            error_pattern_count=d("2"),
            postmortem_count=d("6"),
            high_quality_postmortem_count=d("4"),
            memory_quality_score=d("0.700000"),
        ),
        observation(
            domain_id="crypto",
            team_id="team_crypto",
            experience_count=d("4"),
            error_pattern_count=d("2"),
            postmortem_count=d("3"),
            high_quality_postmortem_count=d("1"),
            memory_quality_score=d("0.400000"),
        ),
    )

    assert is_dataclass(report)
    assert report.report_status == "block"
    assert report.domain_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.total_experience_count == d("46.000000")
    assert report.total_error_pattern_count == d("6.000000")
    assert report.total_postmortem_count == d("19.000000")
    assert report.total_high_quality_postmortem_count == d("14.000000")
    assert report.average_domain_memory_score == d("0.555555")
    assert report.lowest_domain_memory_score == d("0.233333")
    assert report.reason_codes == (
        "domain_memory_summary_report_block_rows",
        "domain_memory_summary_report_watch_rows",
    )

    assert tuple(row.domain_id for row in report.rows) == (
        "politics",
        "macro",
        "crypto",
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert tuple(row.experience_count for row in report.rows) == (
        d("30.000000"),
        d("12.000000"),
        d("4.000000"),
    )
    assert tuple(row.error_pattern_rate for row in report.rows) == (
        d("0.066667"),
        d("0.166667"),
        d("0.500000"),
    )
    assert tuple(row.postmortem_quality_rate for row in report.rows) == (
        d("0.900000"),
        d("0.666667"),
        d("0.333333"),
    )
    assert tuple(row.domain_memory_score for row in report.rows) == (
        d("0.858333"),
        d("0.575000"),
        d("0.233333"),
    )
    assert report.rows[0].reason_codes == (
        "domain_memory_summary_pass",
        "experience_depth_pass",
        "error_pattern_rate_pass",
        "postmortem_quality_pass",
        "memory_quality_pass",
    )
    assert report.rows[1].reason_codes == (
        "domain_memory_summary_watch",
        "experience_depth_watch",
        "error_pattern_rate_watch",
        "postmortem_quality_watch",
        "memory_quality_watch",
    )
    assert report.rows[2].reason_codes == (
        "domain_memory_summary_block",
        "experience_depth_low",
        "error_pattern_rate_high",
        "postmortem_quality_low",
        "memory_quality_low",
    )


def test_missing_domain_memory_blocks_without_exposing_team_identifiers() -> None:
    report = build_report(
        observation(domain_id="politics", team_id="team_politics"),
        cfg=config(domain_ids=("politics", "basketball")),
    )

    assert report.report_status == "block"
    assert tuple(row.domain_id for row in report.rows) == ("politics", "basketball")
    assert report.rows[1].status == "block"
    assert report.rows[1].observation_count == d("0.000000")
    assert report.rows[1].contributing_team_count == d("0.000000")
    assert report.rows[1].reason_codes == (
        "domain_memory_summary_block",
        "missing_domain_memory",
        "experience_depth_low",
        "error_pattern_rate_pass",
        "postmortem_quality_low",
        "memory_quality_low",
    )
    assert "team_id" not in report.payload["rows"][0]
    assert "team_ids" not in report.payload["rows"][0]


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: observation(experience_count=30),
            "experience_count must be exactly Decimal",
        ),
        (
            lambda: observation(memory_quality_score=_DecimalSubclass("0.800000")),
            "memory_quality_score must be exactly Decimal",
        ),
        (
            lambda: observation(memory_quality_score=d("0.8000001")),
            "memory_quality_score must use six decimal places or fewer",
        ),
        (
            lambda: config(min_pass_experience_count=d("20.500000")),
            "min_pass_experience_count must be a whole number",
        ),
        (
            lambda: build_report(observation(), generated_at=datetime(2026, 7, 7, 12, 0)),
            "generated_at must be timezone-aware",
        ),
    ),
)
def test_strict_type_validation_rejects_numeric_shortcuts(
    factory: Any,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()


def test_public_payload_rejects_leaky_identifiers_and_execution_surface() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public payload"):
        observation(domain_id="market_id")

    with pytest.raises(ValueError, match="unsafe public payload"):
        observation(team_id="wallet_keeper")

    report = build_report(observation())
    payload = dict(report.payload)
    payload["candidate_id"] = "candidate-alpha"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_domain_memory_summary_payload(payload)

    row_payload = dict(report.payload)
    row_payload["rows"] = [dict(row_payload["rows"][0])]
    row_payload["rows"][0]["source_ref"] = "research-note"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_domain_memory_summary_payload(row_payload)

    assert_public_payload_has_no_forbidden_surface(report.payload)


def test_hard_flags_are_enforced_and_dataclasses_are_frozen() -> None:
    module = api()
    cfg = config()
    item = observation()
    report = build_report(item)
    row = report.rows[0]

    for value in (cfg, item, row, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchTeamDomainMemorySummaryConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_payload_is_decimal_stringed_deterministic_and_status_limited() -> None:
    left = observation(domain_id="politics", team_id="team_left")
    right = observation(domain_id="macro", team_id="team_right")

    report_a = build_report(right, left, cfg=config(domain_ids=("politics", "macro")))
    report_b = build_report(left, right, cfg=config(domain_ids=("politics", "macro")))

    assert report_a.payload == report_b.payload
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert report_a.payload["domain_count"] == "2.000000"
    assert report_a.payload["rows"][0]["domain_memory_score"] == "0.858333"
    assert report_a.payload["rows"][0]["error_pattern_rate"] == "0.066667"
    assert report_a.payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert_no_float_values(report_a.payload)
    json.dumps(report_a.payload, sort_keys=True)

    statuses = {report_a.report_status}
    statuses.update(row.status for row in report_a.rows)
    assert statuses <= {"pass", "watch", "block"}
    assert "blocked" not in statuses
    assert "ready" not in statuses
    assert "matched" not in statuses


def test_report_consistency_and_digest_validation_reject_tampering() -> None:
    module = api()
    report = build_report(observation())

    with pytest.raises(ValueError, match="pass_count must match rows"):
        replace(report, pass_count=d("0"))

    with pytest.raises(ValueError, match="average_domain_memory_score must match rows"):
        replace(report, average_domain_memory_score=d("0.500000"))

    payload = dict(report.payload)
    payload["report_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest must match payload fields"):
        module.research_team_domain_memory_summary_payload(payload)


def test_module_stays_report_only_without_network_or_persistence_imports() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module.split(".")[0])

    assert imported_names.isdisjoint(
        {
            "httpx",
            "requests",
            "socket",
            "urllib",
            "psycopg",
            "psycopg2",
            "supabase",
            "sqlalchemy",
        },
    )
