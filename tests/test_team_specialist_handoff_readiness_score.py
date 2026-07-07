from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, replace
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
    / "team_specialist_handoff_readiness_score.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
PUBLIC_STATUSES = {"pass", "watch", "block"}


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_handoff_readiness_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "team-specialist-handoff-readiness-score-test",
        "packet_completeness_weight": d("0.250000"),
        "unresolved_question_weight": d("0.150000"),
        "evidence_gap_weight": d("0.150000"),
        "reviewer_confidence_weight": d("0.200000"),
        "context_freshness_weight": d("0.100000"),
        "calibration_weight": d("0.150000"),
        "min_pass_handoff_readiness_score": d("0.800000"),
        "min_watch_handoff_readiness_score": d("0.600000"),
        "min_pass_packet_completeness_score": d("0.850000"),
        "min_watch_packet_completeness_score": d("0.650000"),
        "max_pass_unresolved_question_count": d("0"),
        "max_watch_unresolved_question_count": d("3"),
        "max_pass_evidence_gap_count": d("0"),
        "max_watch_evidence_gap_count": d("3"),
        "min_pass_reviewer_confidence_score": d("0.800000"),
        "min_watch_reviewer_confidence_score": d("0.600000"),
        "max_pass_stale_context_hours": d("24.000000"),
        "max_watch_stale_context_hours": d("72.000000"),
        "min_pass_calibration_score": d("0.800000"),
        "min_watch_calibration_score": d("0.600000"),
    }
    values.update(overrides)
    return module.TeamSpecialistHandoffReadinessScoreConfig(**values)


def packet(**overrides: object):
    module = api()
    values = {
        "team_id": "politics_ops",
        "specialist_id": "resolver_alpha",
        "packet_completeness_score": d("0.940000"),
        "unresolved_question_count": d("0"),
        "evidence_gap_count": d("0"),
        "reviewer_confidence_score": d("0.900000"),
        "stale_context_hours": d("12.000000"),
        "calibration_score": d("0.880000"),
    }
    values.update(overrides)
    return module.TeamSpecialistHandoffReadinessScoreInput(**values)


def build_report(**overrides: object):
    module = api()
    return module.build_team_specialist_handoff_readiness_score_report(
        packet(**overrides),
        config=config(),
        generated_at=GENERATED_AT,
    )


def assert_no_int_or_float(value: Any) -> None:
    assert type(value) is not int
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float(item)


def signed_payload(payload: dict[str, Any]) -> dict[str, Any]:
    ready = dict(payload)
    without_digest = {
        key: value for key, value in ready.items() if key != "derived_validation_digest"
    }
    canonical = json.dumps(
        without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    ready["derived_validation_digest"] = hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return ready


def status_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("status"):
                values.append(item)
            values.extend(status_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(status_values(item))
    return values


def test_complete_packet_passes_with_decimal_payload_and_digest() -> None:
    module = api()
    report = build_report()

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "team-specialist-handoff-readiness-score-test"
    assert report.team_id == "politics_ops"
    assert report.specialist_id == "resolver_alpha"
    assert report.handoff_status == "pass"
    assert report.handoff_readiness_score == d("0.930333")
    assert report.reason_codes == ("handoff_packet_clear",)
    assert report.component_count == d("6")
    assert report.pass_component_count == d("6")
    assert report.watch_component_count == d("0")
    assert report.block_component_count == d("0")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.component_id for row in report.component_rows) == (
        "packet_completeness",
        "unresolved_questions",
        "evidence_gaps",
        "reviewer_confidence",
        "context_freshness",
        "calibration",
    )
    assert all(row.component_status == "pass" for row in report.component_rows)
    assert tuple(row.component_score for row in report.component_rows) == (
        d("0.940000"),
        d("1.000000"),
        d("1.000000"),
        d("0.900000"),
        d("0.833333"),
        d("0.880000"),
    )

    payload = module.team_specialist_handoff_readiness_score_payload(report)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["handoff_status"] == "pass"
    assert payload["handoff_readiness_score"] == "0.930333"
    assert payload["unresolved_question_count"] == "0"
    assert payload["component_rows"][4]["component_score"] == "0.833333"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert set(status_values(payload)) == {"pass"}
    assert_no_int_or_float(payload)
    assert (
        module.validate_team_specialist_handoff_readiness_score_payload(payload)
        == payload
    )


def test_gap_heavy_packet_blocks_with_deterministic_reasons() -> None:
    report = build_report(
        packet_completeness_score=d("0.580000"),
        unresolved_question_count=d("4"),
        evidence_gap_count=d("5"),
        reviewer_confidence_score=d("0.550000"),
        stale_context_hours=d("100.000000"),
        calibration_score=d("0.500000"),
    )

    assert report.handoff_status == "block"
    assert report.pass_component_count == d("0")
    assert report.watch_component_count == d("0")
    assert report.block_component_count == d("6")
    assert report.reason_codes == (
        "packet_completeness_block",
        "unresolved_questions_block",
        "evidence_gaps_block",
        "reviewer_confidence_block",
        "context_stale_block",
        "calibration_block",
        "handoff_score_block",
    )
    assert tuple(row.component_status for row in report.component_rows) == (
        "block",
        "block",
        "block",
        "block",
        "block",
        "block",
    )


def test_stale_context_only_watches_without_blocking() -> None:
    report = build_report(stale_context_hours=d("48.000000"))

    assert report.handoff_status == "watch"
    assert report.handoff_readiness_score == d("0.880333")
    assert report.reason_codes == ("context_stale_watch",)
    assert report.pass_component_count == d("5")
    assert report.watch_component_count == d("1")
    assert report.block_component_count == d("0")
    assert report.component_rows[4].component_id == "context_freshness"
    assert report.component_rows[4].component_status == "watch"


def test_decimal_exact_type_rejection() -> None:
    module = api()

    with pytest.raises(ValueError, match="packet_completeness_score"):
        packet(packet_completeness_score=0.94)
    with pytest.raises(ValueError, match="unresolved_question_count"):
        packet(unresolved_question_count=1)
    with pytest.raises(ValueError, match="reviewer_confidence_score"):
        packet(reviewer_confidence_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="evidence_gap_count"):
        packet(evidence_gap_count=d("1.500000"))
    with pytest.raises(ValueError, match="config"):
        module.TeamSpecialistHandoffReadinessScoreConfig(
            packet_completeness_weight=d("0.200000"),
        )


def test_public_payload_leak_rejection() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public"):
        packet(team_id="candidate_case")
    with pytest.raises(ValueError, match="unsafe public"):
        packet(specialist_id="reviewer_auth")
    with pytest.raises(ValueError, match="unsafe public"):
        config(config_version="https://internal.example/config")

    leaked = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "candidate_id": "candidate_case",
        "derived_validation_digest": "0" * 64,
    }
    with pytest.raises(ValueError, match="unsafe public"):
        module.team_specialist_handoff_readiness_score_payload(leaked)


def test_hard_flags_are_required_and_dataclasses_are_frozen() -> None:
    module = api()
    report = build_report()

    with pytest.raises(FrozenInstanceError):
        report.handoff_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        module.TeamSpecialistHandoffReadinessScoreInput(
            team_id="politics_ops",
            specialist_id="resolver_alpha",
            packet_completeness_score=d("0.940000"),
            unresolved_question_count=d("0"),
            evidence_gap_count=d("0"),
            reviewer_confidence_score=d("0.900000"),
            stale_context_hours=d("12.000000"),
            calibration_score=d("0.880000"),
            paper_only=False,
        )
    payload = module.team_specialist_handoff_readiness_score_payload(report)
    tampered_flags = signed_payload({**payload, "report_only": False})
    with pytest.raises(ValueError, match="report_only"):
        module.team_specialist_handoff_readiness_score_payload(tampered_flags)


def test_payload_is_deterministic_and_uses_public_status_vocabulary() -> None:
    module = api()
    first = module.team_specialist_handoff_readiness_score_payload(build_report())
    second = module.team_specialist_handoff_readiness_score_payload(build_report())

    assert first == second
    assert first["derived_validation_digest"] == second["derived_validation_digest"]
    assert set(status_values(first)) <= PUBLIC_STATUSES
    assert "ready" not in status_values(first)
    assert "blocked" not in status_values(first)
    assert "matched" not in status_values(first)
    assert "supported" not in status_values(first)


def test_report_consistency_rejects_tampering() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="handoff_status"):
        replace(report, handoff_status="ready")
    with pytest.raises(ValueError, match="component_count"):
        replace(report, component_count=d("5"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.team_specialist_handoff_readiness_score_payload(report)
    inconsistent = signed_payload({**payload, "pass_component_count": "5"})
    with pytest.raises(ValueError, match="pass_component_count"):
        module.validate_team_specialist_handoff_readiness_score_payload(inconsistent)


def test_module_remains_pure_report_only_static_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    banned_import_roots = {
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "supabase",
        "urllib",
    }
    imported_roots: set[str] = set()
    called_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    assert imported_roots.isdisjoint(banned_import_roots)
    assert not {"connect", "execute", "open", "request", "send"}.intersection(
        called_names,
    )
