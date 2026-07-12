from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_source_quorum_readiness_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_source_quorum_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def generated_at():
    from datetime import UTC, datetime

    return datetime(2026, 7, 12, 9, 0, tzinfo=UTC)


def signal(**overrides: object):
    module = api()
    values = {
        "team_id": "team_politics",
        "category": "politics",
        "source_family_count": d("3.000000"),
        "official_anchor_present": True,
        "contradiction_status": "none",
        "specialist_ack_count": d("2.000000"),
    }
    values.update(overrides)
    return module.SpecialistTeamSourceQuorumSignal(**values)


def report(*signals: object):
    module = api()
    return module.build_specialist_team_source_quorum_readiness_report(
        signals,
        config=module.SpecialistTeamSourceQuorumReadinessConfig(),
        generated_at=generated_at(),
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_int_values(child)
    if isinstance(value, list):
        for child in value:
            assert_no_float_or_int_values(child)


def test_build_report_computes_quorum_statuses_and_follow_up_fields() -> None:
    module = api()
    rows = (
        signal(team_id="team_politics", category="politics"),
        signal(
            team_id="team_crypto",
            category="crypto",
            source_family_count=d("2.000000"),
            official_anchor_present=True,
            contradiction_status="minor",
            specialist_ack_count=d("1.000000"),
        ),
        signal(
            team_id="team_equities",
            category="equities",
            source_family_count=d("1.000000"),
            official_anchor_present=False,
            contradiction_status="major",
            specialist_ack_count=d("0.000000"),
        ),
    )

    result = report(*reversed(rows))

    assert is_dataclass(result)
    assert module.SPECIALIST_TEAM_SOURCE_QUORUM_STATUSES == (
        "ready",
        "watch",
        "blocked",
    )
    assert result.report_status == "blocked"
    assert result.row_count == d("3.000000")
    assert result.team_count == d("3.000000")
    assert result.category_count == d("3.000000")
    assert result.ready_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.blocked_count == d("1.000000")
    assert result.manual_follow_up_count == d("2.000000")
    assert result.total_missing_source_families == d("3.000000")
    assert result.total_specialist_ack_count == d("3.000000")
    assert [row.team_id for row in result.rows] == [
        "team_politics",
        "team_crypto",
        "team_equities",
    ]
    assert [row.quorum_status for row in result.rows] == [
        "ready",
        "watch",
        "blocked",
    ]
    assert [row.missing_source_families for row in result.rows] == [
        d("0.000000"),
        d("1.000000"),
        d("2.000000"),
    ]
    assert [row.manual_follow_up for row in result.rows] == [False, True, True]
    assert result.rows[1].reason_codes == (
        "source_quorum_watch",
        "source_family_gap",
        "specialist_ack_gap",
        "minor_contradiction",
    )
    assert result.rows[2].reason_codes == (
        "source_quorum_blocked",
        "source_family_gap",
        "official_anchor_missing",
        "specialist_ack_gap",
        "major_contradiction",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = module.specialist_team_source_quorum_readiness_report_payload(result)
    assert payload == result.payload
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)
    assert module.validate_specialist_team_source_quorum_readiness_report_payload(payload)


def test_payload_and_digest_are_deterministic_for_same_public_inputs() -> None:
    left = report(
        signal(team_id="team_crypto", category="crypto"),
        signal(team_id="team_politics", category="politics"),
    )
    right = report(
        signal(team_id="team_politics", category="politics"),
        signal(team_id="team_crypto", category="crypto"),
    )

    assert left.derived_validation_digest == right.derived_validation_digest
    assert left.payload == right.payload
    encoded = json.dumps(left.payload, sort_keys=True)
    assert left.derived_validation_digest in encoded


def test_validation_requires_decimal_counts_public_codes_flags_and_frozen_outputs() -> None:
    module = api()
    result = report(signal())

    with pytest.raises(FrozenInstanceError):
        result.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="source_family_count must be a Decimal"):
        signal(source_family_count=3)

    with pytest.raises(ValueError, match="specialist_ack_count must be a Decimal"):
        signal(specialist_ack_count=_DecimalSubclass("2.000000"))

    with pytest.raises(ValueError, match="source_family_count must be an integer Decimal"):
        signal(source_family_count=d("1.500000"))

    with pytest.raises(ValueError, match="contradiction_status must be supported"):
        signal(contradiction_status="unknown")

    with pytest.raises(ValueError, match="team_id must be a public code"):
        signal(team_id="Team Politics")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(signal(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="quorum_status must be supported"):
        module.SpecialistTeamSourceQuorumReadinessRow(
            team_id="team_macro",
            category="politics",
            source_family_count=d("3.000000"),
            official_anchor_present=True,
            contradiction_status="none",
            specialist_ack_count=d("2.000000"),
            quorum_status="clear",
            missing_source_families=d("0.000000"),
            manual_follow_up=False,
            reason_codes=("source_quorum_ready",),
        )


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    decimal_fields = {
        "source_family_count",
        "specialist_ack_count",
        "required_source_family_count",
        "required_specialist_ack_count",
        "missing_source_families",
        "row_count",
        "team_count",
        "category_count",
        "ready_count",
        "watch_count",
        "blocked_count",
        "manual_follow_up_count",
        "total_missing_source_families",
        "total_specialist_ack_count",
        "count",
    }

    for cls in (
        module.SpecialistTeamSourceQuorumReadinessConfig,
        module.SpecialistTeamSourceQuorumSignal,
        module.SpecialistTeamSourceQuorumReadinessRow,
        module.SpecialistTeamSourceQuorumReadinessReasonCodeCount,
        module.SpecialistTeamSourceQuorumReadinessReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in decimal_fields:
                assert hints[item.name] is Decimal


def test_payload_validation_rejects_tampering_and_unsafe_numeric_values() -> None:
    module = api()
    payload = report(signal()).payload

    tampered = dict(payload)
    tampered["report_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.validate_specialist_team_source_quorum_readiness_report_payload(tampered)

    with pytest.raises(ValueError, match="payload must be readonly"):
        module.validate_specialist_team_source_quorum_readiness_report_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.validate_specialist_team_source_quorum_readiness_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "row_count": 1.0,
            },
        )

    with pytest.raises(ValueError, match="JSON numeric value must use Decimal strings"):
        module.validate_specialist_team_source_quorum_readiness_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "row_count": 1,
            },
        )


def test_module_scope_is_readonly_report_only_without_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "source_url",
        "source_name",
        "source_text",
        "raw_source",
        "auth",
        "wallet",
        "order",
        "trade",
        "database",
        "network",
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "open(",
        "recommend",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
