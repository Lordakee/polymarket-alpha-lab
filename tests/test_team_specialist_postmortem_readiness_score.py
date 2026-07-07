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
    / "team_specialist_postmortem_readiness_score.py"
)
GENERATED_AT = datetime(2026, 7, 7, 16, 0, tzinfo=UTC)
PUBLIC_STATUSES = {"pass", "watch", "block"}


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_postmortem_readiness_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "team-specialist-postmortem-readiness-score-test",
        "timeline_weight": d("0.200000"),
        "decision_log_weight": d("0.200000"),
        "outcome_evidence_weight": d("0.200000"),
        "root_cause_weight": d("0.150000"),
        "action_item_weight": d("0.150000"),
        "memory_update_weight": d("0.100000"),
        "min_pass_postmortem_readiness_score": d("0.850000"),
        "min_watch_postmortem_readiness_score": d("0.650000"),
        "min_pass_timeline_completeness_score": d("0.900000"),
        "min_watch_timeline_completeness_score": d("0.700000"),
        "min_pass_decision_log_score": d("0.900000"),
        "min_watch_decision_log_score": d("0.700000"),
        "min_pass_outcome_evidence_score": d("0.900000"),
        "min_watch_outcome_evidence_score": d("0.700000"),
        "min_pass_root_cause_score": d("0.850000"),
        "min_watch_root_cause_score": d("0.650000"),
        "min_pass_action_item_score": d("0.850000"),
        "min_watch_action_item_score": d("0.650000"),
        "min_pass_memory_update_score": d("0.800000"),
        "min_watch_memory_update_score": d("0.600000"),
    }
    values.update(overrides)
    return module.TeamSpecialistPostmortemReadinessScoreConfig(**values)


def packet(**overrides: object):
    module = api()
    values = {
        "team_id": "research_ops",
        "specialist_id": "reviewer_alpha",
        "timeline_completeness_score": d("0.960000"),
        "decision_log_score": d("0.940000"),
        "outcome_evidence_score": d("0.930000"),
        "root_cause_score": d("0.900000"),
        "action_item_score": d("0.880000"),
        "memory_update_score": d("0.860000"),
    }
    values.update(overrides)
    return module.TeamSpecialistPostmortemReadinessScoreInput(**values)


def build_report(**overrides: object):
    module = api()
    return module.build_team_specialist_postmortem_readiness_score_report(
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


def test_complete_postmortem_materials_pass_with_decimal_payload_and_digest() -> None:
    module = api()
    report = build_report()

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "team-specialist-postmortem-readiness-score-test"
    assert report.team_id == "research_ops"
    assert report.specialist_id == "reviewer_alpha"
    assert report.postmortem_status == "pass"
    assert report.postmortem_readiness_score == d("0.919000")
    assert report.reason_codes == ("postmortem_materials_complete",)
    assert report.component_count == d("6")
    assert report.pass_component_count == d("6")
    assert report.watch_component_count == d("0")
    assert report.block_component_count == d("0")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.component_id for row in report.component_rows) == (
        "timeline",
        "decision_log",
        "outcome_evidence",
        "root_cause",
        "action_items",
        "memory_update",
    )
    assert all(row.component_status == "pass" for row in report.component_rows)

    payload = module.team_specialist_postmortem_readiness_score_payload(report)

    assert payload["generated_at"] == "2026-07-07T16:00:00+00:00"
    assert payload["postmortem_status"] == "pass"
    assert payload["postmortem_readiness_score"] == "0.919000"
    assert payload["decision_log_score"] == "0.940000"
    assert payload["component_rows"][5]["component_score"] == "0.860000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert set(status_values(payload)) == {"pass"}
    assert_no_int_or_float(payload)
    assert (
        module.validate_team_specialist_postmortem_readiness_score_payload(payload)
        == payload
    )


def test_watch_and_block_statuses_capture_material_gaps() -> None:
    watch_report = build_report(memory_update_score=d("0.700000"))

    assert watch_report.postmortem_status == "watch"
    assert watch_report.postmortem_readiness_score == d("0.903000")
    assert watch_report.reason_codes == ("memory_update_watch",)
    assert watch_report.pass_component_count == d("5")
    assert watch_report.watch_component_count == d("1")
    assert watch_report.block_component_count == d("0")
    assert watch_report.component_rows[5].component_status == "watch"

    block_report = build_report(
        timeline_completeness_score=d("0.620000"),
        decision_log_score=d("0.500000"),
        outcome_evidence_score=d("0.540000"),
        root_cause_score=d("0.520000"),
        action_item_score=d("0.500000"),
        memory_update_score=d("0.400000"),
    )

    assert block_report.postmortem_status == "block"
    assert block_report.pass_component_count == d("0")
    assert block_report.watch_component_count == d("0")
    assert block_report.block_component_count == d("6")
    assert block_report.reason_codes == (
        "timeline_block",
        "decision_log_block",
        "outcome_evidence_block",
        "root_cause_block",
        "action_items_block",
        "memory_update_block",
        "postmortem_score_block",
    )


def test_decimal_exact_type_rejection() -> None:
    module = api()

    with pytest.raises(ValueError, match="timeline_completeness_score"):
        packet(timeline_completeness_score=0.96)
    with pytest.raises(ValueError, match="decision_log_score"):
        packet(decision_log_score=1)
    with pytest.raises(ValueError, match="outcome_evidence_score"):
        packet(outcome_evidence_score=_DecimalSubclass("0.930000"))
    with pytest.raises(ValueError, match="config"):
        module.TeamSpecialistPostmortemReadinessScoreConfig(
            timeline_weight=d("0.300000"),
        )


def test_public_payload_leak_rejection() -> None:
    module = api()

    blocked_values = (
        "candidate_alpha",
        "market_alpha",
        "resolution_slug",
        "question_text",
        "source_ref",
        "https://example.test/path",
        "postgres_dsn",
        "orders_table",
        "token_secret",
        "wallet_auth",
        "trade_position",
        "buy_recommendation",
        "sell_recommendation",
    )
    for leaked in blocked_values:
        with pytest.raises(ValueError, match="unsafe public"):
            packet(team_id=leaked)

    leaked_payload = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "candidate_id": "candidate_case",
        "derived_validation_digest": "0" * 64,
    }
    with pytest.raises(ValueError, match="unsafe public"):
        module.team_specialist_postmortem_readiness_score_payload(leaked_payload)


def test_hard_flags_are_required_and_dataclasses_are_frozen() -> None:
    module = api()
    report = build_report()

    with pytest.raises(FrozenInstanceError):
        report.postmortem_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        module.TeamSpecialistPostmortemReadinessScoreInput(
            team_id="research_ops",
            specialist_id="reviewer_alpha",
            timeline_completeness_score=d("0.960000"),
            decision_log_score=d("0.940000"),
            outcome_evidence_score=d("0.930000"),
            root_cause_score=d("0.900000"),
            action_item_score=d("0.880000"),
            memory_update_score=d("0.860000"),
            paper_only=False,
        )
    payload = module.team_specialist_postmortem_readiness_score_payload(report)
    tampered_flags = signed_payload({**payload, "report_only": False})
    with pytest.raises(ValueError, match="report_only"):
        module.team_specialist_postmortem_readiness_score_payload(tampered_flags)


def test_payload_is_deterministic_and_uses_public_status_vocabulary() -> None:
    module = api()
    first = module.team_specialist_postmortem_readiness_score_payload(build_report())
    second = module.team_specialist_postmortem_readiness_score_payload(build_report())

    assert first == second
    assert first["derived_validation_digest"] == second["derived_validation_digest"]
    assert set(status_values(first)) <= PUBLIC_STATUSES
    assert "ready" not in status_values(first)
    assert "blocked" not in status_values(first)
    assert "candidate" not in status_values(first)


def test_report_and_digest_consistency_rejects_tampering() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="postmortem_status"):
        replace(report, postmortem_status="ready")
    with pytest.raises(ValueError, match="component_count"):
        replace(report, component_count=d("5"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.team_specialist_postmortem_readiness_score_payload(report)
    inconsistent = signed_payload({**payload, "pass_component_count": "5"})
    with pytest.raises(ValueError, match="pass_component_count"):
        module.validate_team_specialist_postmortem_readiness_score_payload(inconsistent)


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
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    assert imported_roots.isdisjoint(banned_import_roots)
    assert not {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "send",
    }.intersection(called_names)
