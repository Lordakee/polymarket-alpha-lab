from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_resolution_evidence_source_rank_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observed_at(hours_ago: str) -> datetime:
    return GENERATED_AT - timedelta(seconds=int(d(hours_ago) * d("3600")))


def evidence(**overrides: object):
    module = api()
    values = {
        "candidate_key": "candidate-raw-alpha-should-not-leak",
        "source_key": "source-raw-official-should-not-leak",
        "source_family": "official_results",
        "source_kind": "official",
        "authority_score": d("0.950000"),
        "observed_at": observed_at("1"),
        "corroborating_evidence_count": d("4"),
        "independent_source_family_count": d("3"),
        "contradiction_count": d("0"),
    }
    values.update(overrides)
    return module.ResearchEventResolutionEvidenceSourceRankInput(**values)


def build_report(*rows: object, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_event_resolution_evidence_source_rank_report(
        rows,
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


def walk_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        return tuple(value.keys()) + tuple(
            key for item in value.values() for key in walk_keys(item)
        )
    if isinstance(value, list):
        return tuple(key for item in value for key in walk_keys(item))
    return ()


def test_builds_ranked_report_without_public_raw_identifier_leakage() -> None:
    report = build_report(
        evidence(),
        evidence(
            candidate_key="candidate-raw-beta-should-not-leak",
            source_key="source-raw-context-should-not-leak",
            source_family="context_archive",
            source_kind="secondary",
            authority_score=d("0.500000"),
            observed_at=observed_at("12"),
            corroborating_evidence_count=d("1"),
            independent_source_family_count=d("1"),
        ),
        evidence(
            candidate_key="candidate-raw-gamma-should-not-leak",
            source_key="source-raw-conflict-should-not-leak",
            source_family="rumor_watch",
            source_kind="secondary",
            authority_score=d("0.200000"),
            observed_at=observed_at("240"),
            corroborating_evidence_count=d("0"),
            independent_source_family_count=d("0"),
            contradiction_count=d("2"),
        ),
    )

    assert report.report_status == "block"
    assert report.candidate_count == d("3")
    assert report.source_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_source_rank_score == d("0.503542")
    assert tuple(row.rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.source_rank_score for row in report.rows) == (
        d("0.981458"),
        d("0.529167"),
        d("0.000000"),
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert report.reason_codes == (
        "source_rank_report_watch_rows",
        "source_rank_report_block_rows",
        "contradiction_penalty_present",
        "stale_evidence_present",
    )

    payload_json = json.dumps(report.payload, sort_keys=True)
    for forbidden in (
        "candidate-raw-alpha-should-not-leak",
        "candidate-raw-beta-should-not-leak",
        "candidate-raw-gamma-should-not-leak",
        "source-raw-official-should-not-leak",
        "source-raw-context-should-not-leak",
        "source-raw-conflict-should-not-leak",
    ):
        assert forbidden not in payload_json
    assert all(len(row.candidate_digest) == 64 for row in report.rows)
    assert all(len(row.source_digest) == 64 for row in report.rows)
    assert all(len(row.row_digest) == 64 for row in report.rows)


def test_payload_is_deterministic_decimal_string_only_and_digest_validated() -> None:
    module = api()
    report = build_report(
        evidence(source_key="source-z"),
        evidence(source_key="source-a", authority_score=d("0.950000")),
    )
    reversed_report = build_report(
        *reversed(
            (
                evidence(source_key="source-z"),
                evidence(source_key="source-a", authority_score=d("0.950000")),
            ),
        ),
    )

    payload = module.research_event_resolution_evidence_source_rank_report_payload(report)

    assert payload == reversed_report.payload
    assert report.derived_validation_digest == reversed_report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["source_count"] == "2"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["source_rank_score"] == "0.981458"
    assert len(payload["derived_validation_digest"]) == 64
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert_no_float_values(payload)

    assert module.research_event_resolution_evidence_source_rank_report_payload(payload) == payload

    tampered = dict(payload)
    tampered["source_count"] = "99"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_resolution_evidence_source_rank_report_payload(tampered)


def test_non_default_status_thresholds_preserve_report_consistency() -> None:
    module = api()
    config = module.ResearchEventResolutionEvidenceSourceRankConfig(
        pass_score_floor=d("0.990000"),
        watch_score_floor=d("0.500000"),
    )

    report = module.build_research_event_resolution_evidence_source_rank_report(
        (evidence(),),
        generated_at=GENERATED_AT,
        config=config,
    )

    assert report.report_status == "watch"
    assert report.rows[0].source_rank_score == d("0.981458")
    assert report.rows[0].status == "watch"
    assert report.reason_codes == ("source_rank_report_watch_rows",)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.ResearchEventResolutionEvidenceSourceRankConfig()
    sample = evidence()
    report = build_report(sample)
    row = report.rows[0]

    for item in (config, sample, row, report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchEventResolutionEvidenceSourceRankConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        evidence(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="f" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(row, status="blocked")


def test_rejects_unsafe_public_payload_surfaces() -> None:
    module = api()
    report = build_report(evidence())
    payload = report.payload

    forbidden_key_fragments = (
        "candidate_key",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_key",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )
    for key in walk_keys(payload):
        lowered = key.lower()
        assert not any(fragment in lowered for fragment in forbidden_key_fragments)

    with pytest.raises(ValueError, match="unsafe public"):
        module.research_event_resolution_evidence_source_rank_report_payload(
            {**payload, "market_id": "should-not-surface"},
        )
    with pytest.raises(ValueError, match="unsafe"):
        evidence(source_key="https://example.invalid/resolution")


def test_module_imports_no_db_network_wallet_or_live_trading_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_event_resolution_evidence_source_rank_report.py",
    ).read_text()
    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "socket",
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "psycopg2",
        "sqlite3",
        "sqlalchemy",
        "web3",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".", 1)[0] not in forbidden_imports
