from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_recommendation_evidence_trace_digest"
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-recommendation-evidence-trace-digest-v0",
        "min_traceable_source_count": d("2"),
        "min_source_family_count": d("2"),
        "max_evidence_age_hours": d("24"),
        "require_conflict_notes": True,
    }
    values.update(overrides)
    return module.StrategyRecommendationEvidenceTraceDigestConfig(**values)


def evidence(
    candidate_reference: str,
    evidence_reference: str,
    source_family: str,
    *,
    observed_at: datetime = GENERATED_AT - timedelta(hours=2),
    source_trace_present: bool = True,
    conflict_flagged: bool = False,
    conflict_note_present: bool = False,
    reason_codes: tuple[str, ...] = ("evidence_trace_input",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.StrategyRecommendationEvidenceTraceDigestInput(
        candidate_reference=candidate_reference,
        evidence_reference=evidence_reference,
        source_family=source_family,
        observed_at=observed_at,
        source_trace_present=source_trace_present,
        conflict_flagged=conflict_flagged,
        conflict_note_present=conflict_note_present,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*rows: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_recommendation_evidence_trace_digest_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def ready_candidate(candidate_reference: str = "candidate-ready") -> tuple[object, ...]:
    return (
        evidence(
            candidate_reference,
            "https://example.test/official?token=alpha",
            "official",
            conflict_flagged=True,
            conflict_note_present=True,
        ),
        evidence(candidate_reference, "public-news-ref", "news"),
    )


def test_digest_blocks_or_watches_until_trace_freshness_and_conflict_notes_are_ready() -> None:
    digest = report(
        evidence("candidate-stale", "fresh-official", "official"),
        evidence("candidate-stale", "fresh-news", "news"),
        evidence(
            "candidate-stale",
            "old-official",
            "official",
            observed_at=GENERATED_AT - timedelta(hours=30),
        ),
        *ready_candidate("candidate-ready"),
        evidence("candidate-blocked", "missing-trace", "news", source_trace_present=False),
        evidence(
            "candidate-blocked",
            "unnoted-conflict",
            "official",
            conflict_flagged=True,
            conflict_note_present=False,
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.input_count == d("7")
    assert digest.candidate_count == d("3")
    assert digest.research_ready_candidate_count == d("1")
    assert digest.watch_candidate_count == d("1")
    assert digest.blocked_candidate_count == d("1")
    assert digest.traceability_gap_candidate_count == d("1")
    assert digest.stale_candidate_count == d("1")
    assert digest.missing_conflict_note_candidate_count == d("1")
    assert digest.status == "blocked"
    assert digest.reason_codes == (
        "evidence_trace_digest_blocked",
        "evidence_trace_traceability_gaps_present",
        "evidence_trace_freshness_gaps_present",
        "evidence_trace_conflict_note_gaps_present",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    blocked, stale, ready = digest.rows
    assert blocked.readiness_status == "blocked"
    assert blocked.traceable_source_count == d("1")
    assert blocked.fresh_traceable_source_count == d("1")
    assert blocked.source_family_count == d("1")
    assert blocked.conflict_flagged_evidence_count == d("1")
    assert blocked.conflict_note_count == d("0")
    assert blocked.reason_codes == (
        "evidence_trace_source_trace_missing",
        "evidence_trace_traceable_sources_below_minimum",
        "evidence_trace_source_family_diversity_below_minimum",
        "evidence_trace_conflict_notes_missing",
    )

    assert stale.readiness_status == "watch"
    assert stale.stale_source_count == d("1")
    assert stale.reason_codes == ("evidence_trace_stale_evidence",)

    assert ready.readiness_status == "research_ready"
    assert ready.traceability_ratio == d("1.000000")
    assert ready.source_family_ratio == d("1.000000")
    assert ready.freshness_ratio == d("1.000000")
    assert ready.source_families == ("news", "official")
    assert ready.reason_codes == ("evidence_trace_ready",)


def test_references_are_redacted_from_inputs_rows_payload_and_errors() -> None:
    module = api()
    raw_candidate = "https://example.test/candidate/public?token=super-secret-token"
    raw_evidence = "https://example.test/evidence/public?token=super-secret-token"

    row = evidence(raw_candidate, raw_evidence, "official")
    rendered_input = repr(row).lower()
    assert "super-secret-token" not in rendered_input
    assert "example.test" not in rendered_input
    assert row.candidate_reference.startswith("candidate_ref_")
    assert row.evidence_reference.startswith("evidence_ref_")

    digest = report(row, evidence(raw_candidate, "second-public-reference", "news"))
    payload = module.strategy_recommendation_evidence_trace_digest_payload(digest)
    rendered_payload = repr(payload).lower()
    assert "super-secret-token" not in rendered_payload
    assert "example.test" not in rendered_payload
    assert payload["rows"][0]["redacted_candidate_reference"].startswith("candidate_ref_")
    assert payload["rows"][0]["redacted_evidence_references"][0].startswith(
        "evidence_ref_",
    )

    with pytest.raises(ValueError) as excinfo:
        evidence(raw_candidate, "", "official")
    assert raw_candidate not in str(excinfo.value)


def test_payload_uses_decimal_strings_iso_datetimes_and_rejects_public_numeric_values() -> None:
    module = api()
    digest = report(*ready_candidate())

    payload = module.strategy_recommendation_evidence_trace_digest_payload(digest)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["input_count"] == "2"
    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["evidence_count"] == "2"
    assert payload["rows"][0]["latest_observed_at"] == (
        GENERATED_AT - timedelta(hours=2)
    ).isoformat()
    assert payload["rows"][0]["traceability_ratio"] == "1.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert_no_public_numbers(payload)
    json.dumps(payload, sort_keys=True)

    with pytest.raises(ValueError, match="candidate_count"):
        module.strategy_recommendation_evidence_trace_digest_payload(
            {
                "candidate_count": 1,
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    with pytest.raises(ValueError, match="candidate_count"):
        module.strategy_recommendation_evidence_trace_digest_payload(
            {
                "candidate_count": 1.0,
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.strategy_recommendation_evidence_trace_digest_payload(
            {
                "generated_at": datetime(2026, 7, 4, 12, 0),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_recommendation_evidence_trace_digest_payload(
            {
                "rows": [{"evidence_count": "1"}],
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_exact_datetime_decimal_bool_and_flag_validation() -> None:
    module = api()

    with pytest.raises(ValueError, match="observed_at"):
        evidence(
            "candidate-time",
            "evidence-time",
            "official",
            observed_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        evidence(
            "candidate-time",
            "evidence-time",
            "official",
            observed_at=datetime(2026, 7, 4, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at"):
        evidence(
            "candidate-time",
            "evidence-time",
            "official",
            observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTZ()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(
            evidence(
                "candidate-future",
                "future-evidence",
                "official",
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="min_traceable_source_count"):
        config(min_traceable_source_count=2)
    with pytest.raises(ValueError, match="source_trace_present"):
        evidence(
            "candidate-bool",
            "evidence-bool",
            "official",
            source_trace_present=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="paper_only"):
        evidence("candidate-flag", "evidence-flag", "official", paper_only=False)

    digest = report(*ready_candidate())
    with pytest.raises(ValueError, match="report_only"):
        module.strategy_recommendation_evidence_trace_digest_payload(
            replace(digest, report_only=False),
        )


def test_dataclasses_are_frozen_and_public_numeric_fields_are_decimal() -> None:
    module = api()
    digest = report(*ready_candidate())

    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    for item in (
        config(),
        digest,
        *digest.rows,
        *digest.reason_code_counts,
    ):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name
            if field.name.endswith(("_count", "_ratio", "_hours")):
                assert field.type in {"Decimal", Decimal}
                assert type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        digest.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.rows[0].traceability_ratio = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(digest.rows[0], readonly=False)


def test_deterministic_reason_code_counts_and_manual_report_consistency() -> None:
    module = api()
    digest = report(
        *ready_candidate("candidate-zeta"),
        evidence("candidate-alpha", "missing-trace", "news", source_trace_present=False),
        evidence(
            "candidate-alpha",
            "unnoted-conflict",
            "official",
            conflict_flagged=True,
            conflict_note_present=False,
        ),
    )

    assert tuple(row.readiness_status for row in digest.rows) == (
        "blocked",
        "research_ready",
    )
    assert tuple(count.reason_code for count in digest.reason_code_counts) == (
        "evidence_trace_conflict_notes_missing",
        "evidence_trace_ready",
        "evidence_trace_source_family_diversity_below_minimum",
        "evidence_trace_source_trace_missing",
        "evidence_trace_traceable_sources_below_minimum",
    )
    assert all(count.count == d("1") for count in digest.reason_code_counts)

    with pytest.raises(ValueError, match="reason_codes"):
        module.StrategyRecommendationEvidenceTraceDigestRow(
            redacted_candidate_reference="candidate_ref_manual",
            evidence_count=d("1"),
            traceable_source_count=d("1"),
            fresh_traceable_source_count=d("1"),
            stale_source_count=d("0"),
            source_family_count=d("1"),
            conflict_flagged_evidence_count=d("0"),
            conflict_note_count=d("0"),
            traceability_ratio=d("1.000000"),
            source_family_ratio=d("1.000000"),
            freshness_ratio=d("1.000000"),
            latest_observed_at=GENERATED_AT,
            oldest_observed_at=GENERATED_AT,
            source_families=("official",),
            redacted_evidence_references=("evidence_ref_manual",),
            readiness_status="research_ready",
            reason_codes=("evidence_trace_ready", "evidence_trace_ready"),
        )


def test_module_has_no_static_forbidden_surface_or_io_terms() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_recommendation_evidence_trace_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        "read(",
        "write(",
        "live",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "auth",
        "private_key",
        "api_key",
        "network",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"__import__", "open", "read", "write", "float"}
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "connect",
                    "execute",
                    "open",
                    "read",
                    "read_text",
                    "request",
                    "write",
                    "write_text",
                }
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in {
                    "httpx",
                    "os",
                    "pathlib",
                    "psycopg",
                    "requests",
                    "socket",
                    "sqlite3",
                    "subprocess",
                    "supabase",
                }
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in {
                "httpx",
                "os",
                "pathlib",
                "psycopg",
                "requests",
                "socket",
                "sqlite3",
                "subprocess",
                "supabase",
            }


def assert_no_public_numbers(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"public number found in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numbers(item)
