from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.candidate_decision_resolution_source_latency_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(
    redacted_candidate_ref: str = (
        "candidate_ref_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    ),
    **overrides: object,
):
    module = api()
    values: dict[str, object] = {
        "redacted_candidate_ref": redacted_candidate_ref,
        "official_source_latency_minutes": d("10"),
        "independent_source_latency_minutes": d("20"),
        "settlement_delay_hours": d("6"),
        "latency_variability_score": d("0.050000"),
        "source_reliability_score": d("0.950000"),
        "ambiguity_score": d("0.020000"),
    }
    values.update(overrides)
    return module.CandidateDecisionResolutionSourceLatencyScoreInput(**values)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_RESOLUTION_SOURCE_LATENCY_SCORE_CONFIG_VERSION
        ),
        "min_pass_latency_score": d("0.800000"),
        "min_watch_latency_score": d("0.500000"),
        "max_pass_official_source_latency_minutes": d("30"),
        "max_watch_official_source_latency_minutes": d("240"),
        "max_pass_independent_source_latency_minutes": d("60"),
        "max_watch_independent_source_latency_minutes": d("360"),
        "max_pass_settlement_delay_hours": d("24"),
        "max_watch_settlement_delay_hours": d("72"),
        "max_pass_latency_variability_score": d("0.200000"),
        "max_watch_latency_variability_score": d("0.600000"),
        "min_pass_source_reliability_score": d("0.800000"),
        "min_watch_source_reliability_score": d("0.500000"),
        "max_pass_ambiguity_score": d("0.100000"),
        "max_watch_ambiguity_score": d("0.400000"),
        "official_source_latency_weight": d("0.250000"),
        "independent_source_latency_weight": d("0.200000"),
        "settlement_delay_weight": d("0.150000"),
        "latency_variability_weight": d("0.150000"),
        "source_reliability_weight": d("0.150000"),
        "ambiguity_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.CandidateDecisionResolutionSourceLatencyScoreConfig(**values)


def report(*rows: object, cfg: object | None = None):
    return api().build_candidate_decision_resolution_source_latency_score_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def payload_digest(payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded_payload = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def walk_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for child in value.values():
            walk_public_payload(child)
    elif isinstance(value, list):
        for child in value:
            walk_public_payload(child)
    else:
        assert type(value) not in (Decimal, datetime, float, int)
        if type(value) is str:
            assert value not in {"ready", "blocked", "matched", "supported"}


def test_low_latency_resolution_sources_pass_and_payload_is_safe() -> None:
    module = api()
    latency_report = report(candidate())

    assert type(latency_report) is module.CandidateDecisionResolutionSourceLatencyScoreReport
    assert latency_report.generated_at == GENERATED_AT
    assert latency_report.status == "pass"
    assert latency_report.candidate_count == d("1.000000")
    assert latency_report.pass_count == d("1.000000")
    assert latency_report.watch_count == d("0.000000")
    assert latency_report.block_count == d("0.000000")
    assert latency_report.reason_codes == ("resolution_source_latency_pass",)

    row = latency_report.rows[0]
    assert row.redacted_candidate_ref == (
        "candidate_ref_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    )
    assert row.latency_score == d("1.000000")
    assert row.status == "pass"
    assert row.reason_codes == ("resolution_source_latency_pass",)
    assert row.hard_blocker_codes == ()

    payload = module.candidate_decision_resolution_source_latency_score_payload(
        latency_report,
    )
    json.dumps(payload, sort_keys=True)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["latency_score"] == "1.000000"
    assert "market_slug" not in payload["rows"][0]
    assert "source_ref" not in payload["rows"][0]
    walk_public_payload(payload)


def test_severe_resolution_source_delay_blocks_manual_priority() -> None:
    latency_report = report(
        candidate(
            official_source_latency_minutes=d("500"),
            independent_source_latency_minutes=d("700"),
            settlement_delay_hours=d("96"),
        ),
    )

    assert latency_report.status == "block"
    assert latency_report.block_count == d("1.000000")
    row = latency_report.rows[0]
    assert row.status == "block"
    assert row.hard_blocker_codes == (
        "official_source_latency_minutes_block",
        "independent_source_latency_minutes_block",
        "settlement_delay_hours_block",
    )
    assert row.reason_codes == row.hard_blocker_codes


def test_variable_latency_is_watch_without_hard_blockers() -> None:
    latency_report = report(
        candidate(
            latency_variability_score=d("0.450000"),
        ),
    )

    assert latency_report.status == "watch"
    assert latency_report.watch_count == d("1.000000")
    row = latency_report.rows[0]
    assert row.status == "watch"
    assert row.latency_score == d("0.906250")
    assert row.reason_codes == ("latency_variability_score_watch",)
    assert row.hard_blocker_codes == ()


def test_decimal_exact_types_are_required() -> None:
    with pytest.raises(ValueError, match="official_source_latency_minutes must be a Decimal"):
        candidate(official_source_latency_minutes=1)
    with pytest.raises(
        ValueError,
        match="independent_source_latency_minutes must be a Decimal",
    ):
        candidate(independent_source_latency_minutes=1.0)
    with pytest.raises(ValueError, match="ambiguity_score must be a Decimal"):
        candidate(ambiguity_score=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="source_reliability_weight must be a Decimal"):
        config(source_reliability_weight=DecimalSubclass("0.150000"))
    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        config(ambiguity_weight=d("0.200000"))


def test_public_payload_rejects_leaks_status_aliases_and_numeric_values() -> None:
    module = api()
    valid_payload = module.candidate_decision_resolution_source_latency_score_payload(
        report(candidate()),
    )
    assert module.validate_candidate_decision_resolution_source_latency_score_public_payload(
        valid_payload,
    )

    unsafe_payloads = (
        ({"raw_candidate_id": "abc"}, "raw candidate"),
        ({"candidate_id": "abc"}, "raw candidate"),
        ({"market_slug": "will-x-happen"}, "market"),
        ({"question": "Will X happen?"}, "market"),
        ({"source_url": "https://example.test/result"}, "source"),
        ({"safe_key": "https://example.test/result"}, "source"),
        ({"safe_key": "source_ref:abc123"}, "source"),
        ({"safe_key": "postgres://user@host/db"}, "source"),
        ({"safe_key": "orders table"}, "unsafe"),
        ({"safe_key": "buy now"}, "unsafe"),
        ({"status": "ready"}, "status"),
        ({"status": "blocked"}, "status"),
        ({"status": "matched"}, "status"),
        ({"status": "supported"}, "status"),
        ({"candidate_count": 1}, "decimal strings"),
        ({"candidate_count": 1.0}, "decimal strings"),
        ({"redacted_candidate_ref": "candidate_ref_not-a-digest"}, "raw candidate"),
    )
    for payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_resolution_source_latency_score_public_payload(
                payload,
            )


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    module = api()
    latency_report = report(candidate())

    assert latency_report.paper_only is True
    assert latency_report.report_only is True
    assert latency_report.readonly is True
    with pytest.raises(FrozenInstanceError):
        latency_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        candidate(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.CandidateDecisionResolutionSourceLatencyScoreReport(
            generated_at=GENERATED_AT,
            config_version=(
                module.DEFAULT_CANDIDATE_DECISION_RESOLUTION_SOURCE_LATENCY_SCORE_CONFIG_VERSION
            ),
            candidate_count=d("0"),
            pass_count=d("0"),
            watch_count=d("0"),
            block_count=d("0"),
            max_latency_score=d("0"),
            min_latency_score=d("0"),
            status="watch",
            reason_codes=("resolution_source_latency_no_candidates",),
            reason_code_counts=(),
            rows=(),
            readonly=False,
        )


def test_rows_payload_and_reason_counts_are_deterministic() -> None:
    first = report(
        candidate(
            "candidate_ref_cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        ),
        candidate(
            "candidate_ref_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            official_source_latency_minutes=d("500"),
        ),
        candidate(
            "candidate_ref_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            latency_variability_score=d("0.450000"),
        ),
    )
    second = report(
        candidate(
            "candidate_ref_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            latency_variability_score=d("0.450000"),
        ),
        candidate(
            "candidate_ref_cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        ),
        candidate(
            "candidate_ref_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            official_source_latency_minutes=d("500"),
        ),
    )

    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert tuple(row.redacted_candidate_ref for row in first.rows) == (
        "candidate_ref_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "candidate_ref_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "candidate_ref_cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    )
    assert tuple(count.reason_code for count in first.reason_code_counts) == (
        "official_source_latency_minutes_block",
        "latency_variability_score_watch",
        "resolution_source_latency_pass",
    )
    assert first == second
    assert api().candidate_decision_resolution_source_latency_score_payload(first) == (
        api().candidate_decision_resolution_source_latency_score_payload(second)
    )
    assert {row.status for row in first.rows} <= {"pass", "watch", "block"}


def test_report_digest_payload_and_consistency_are_checked() -> None:
    module = api()
    latency_report = report(candidate())
    payload = module.candidate_decision_resolution_source_latency_score_payload(
        latency_report,
    )

    assert latency_report.derived_validation_digest == payload_digest(payload)
    assert payload["derived_validation_digest"] == payload_digest(payload)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(latency_report.rows[0], derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(latency_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match rows"):
        replace(latency_report, pass_count=d("0"))


def test_module_has_no_network_persistence_or_runtime_mutation_surface() -> None:
    source = inspect.getsource(api())
    tree = ast.parse(source)
    forbidden_import_roots = {
        "boto3",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "commit",
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "urlopen",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
