from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import inspect
import json
from typing import Any

import pytest

import polymarket_alpha_lab.cross_team_disagreement_escalation_report as api
from polymarket_alpha_lab.cross_team_disagreement_escalation_report import (
    CROSS_TEAM_DISAGREEMENT_ESCALATION_STATUSES,
    CrossTeamDisagreementEscalationInput,
    CrossTeamDisagreementEscalationReport,
    build_cross_team_disagreement_escalation_report,
    cross_team_disagreement_escalation_report_digest,
    cross_team_disagreement_escalation_report_payload,
)


GENERATED_AT = datetime(2026, 7, 11, 17, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def disagreement_input(**overrides: object) -> CrossTeamDisagreementEscalationInput:
    values = {
        "observed_at": datetime(2026, 7, 11, 17, 25, tzinfo=UTC),
        "primary_team_probability": d("0.610000"),
        "advisory_team_probabilities": (d("0.600000"), d("0.620000")),
        "source_quality_status": "clear",
        "memory_policy_status": "clear",
    }
    values.update(overrides)
    return CrossTeamDisagreementEscalationInput(**values)


def report(
    *inputs: CrossTeamDisagreementEscalationInput,
    generated_at: datetime = GENERATED_AT,
) -> CrossTeamDisagreementEscalationReport:
    return build_cross_team_disagreement_escalation_report(
        inputs,
        generated_at=generated_at,
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def resign_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    signed = json.loads(json.dumps(payload))
    for row in signed.get("rows", []):
        row.pop("derived_validation_digest", None)
        row["derived_validation_digest"] = hashlib.sha256(
            json.dumps(
                row,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8"),
        ).hexdigest()
    signed.pop("derived_validation_digest", None)
    signed["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            signed,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    return signed


def test_report_escalates_high_disagreement_and_blocks_unsafe_context() -> None:
    summary = report(
        disagreement_input(
            primary_team_probability=d("0.710000"),
            advisory_team_probabilities=(d("0.560000"), d("0.540000")),
            source_quality_status="clear",
            memory_policy_status="clear",
        ),
        disagreement_input(
            primary_team_probability=d("0.580000"),
            advisory_team_probabilities=(d("0.510000"), d("0.520000")),
            source_quality_status="clear",
            memory_policy_status="clear",
        ),
        disagreement_input(
            primary_team_probability=d("0.620000"),
            advisory_team_probabilities=(d("0.610000"), d("0.630000")),
            source_quality_status="clear",
            memory_policy_status="clear",
        ),
        disagreement_input(
            primary_team_probability=d("0.610000"),
            advisory_team_probabilities=(d("0.590000"), d("0.620000")),
            source_quality_status="degraded",
            memory_policy_status="stale",
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is CrossTeamDisagreementEscalationReport
    assert summary.generated_at == GENERATED_AT
    assert summary.input_count == d("4.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("2.000000")
    assert summary.blocked_count == d("1.000000")
    assert summary.status == "blocked"
    assert summary.reason_codes == (
        "cross_team_disagreement_report_blocked",
        "high_disagreement_blocked_review",
        "medium_disagreement_watch_review",
        "memory_policy_watch_review",
        "source_quality_watch_review",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64

    blocked, medium, context_watch, passed = summary.rows
    assert blocked.primary_team_probability == d("0.710000")
    assert blocked.advisory_mean_probability == d("0.550000")
    assert blocked.max_probability_gap == d("0.170000")
    assert blocked.disagreement_level == "high"
    assert blocked.escalation_status == "blocked"
    assert blocked.reason_codes == ("high_disagreement_blocked",)
    assert blocked.manual_next_step == "manual_probability_reconciliation_required"

    assert medium.max_probability_gap == d("0.070000")
    assert medium.disagreement_level == "medium"
    assert medium.escalation_status == "watch"
    assert medium.reason_codes == ("medium_disagreement_watch",)
    assert medium.manual_next_step == "manual_advisory_review_required"

    assert context_watch.disagreement_level == "low"
    assert context_watch.escalation_status == "watch"
    assert context_watch.reason_codes == (
        "memory_policy_stale_watch",
        "source_quality_degraded_watch",
    )
    assert context_watch.manual_next_step == "manual_source_memory_review_required"

    assert passed.disagreement_level == "low"
    assert passed.escalation_status == "pass"
    assert passed.reason_codes == ("cross_team_disagreement_pass",)
    assert passed.manual_next_step == "no_manual_escalation_required"


def test_empty_report_blocks_as_missing_readonly_inputs() -> None:
    summary = report()

    assert summary.status == "blocked"
    assert summary.input_count == d("0.000000")
    assert summary.pass_count == d("0.000000")
    assert summary.watch_count == d("0.000000")
    assert summary.blocked_count == d("0.000000")
    assert summary.max_probability_gap == d("0.000000")
    assert summary.reason_codes == ("cross_team_disagreement_report_empty",)
    assert summary.reason_code_counts == (("cross_team_disagreement_report_empty", d("1.000000")),)
    assert summary.rows == ()


def test_payload_digest_are_public_safe_deterministic_and_guarded() -> None:
    generated_at = datetime(2026, 7, 11, 13, 30, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = cross_team_disagreement_escalation_report_payload(
        report(disagreement_input(), generated_at=generated_at),
    )
    second_payload = cross_team_disagreement_escalation_report_payload(
        report(disagreement_input(), generated_at=generated_at),
    )
    digest = cross_team_disagreement_escalation_report_digest(
        report(disagreement_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-11T17:30:00+00:00"
    assert first_payload["input_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["primary_team_probability"] == "0.610000"
    assert first_payload["rows"][0]["advisory_mean_probability"] == "0.610000"
    assert first_payload["rows"][0]["max_probability_gap"] == "0.010000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert digest == {
        "generated_at": "2026-07-11T17:30:00+00:00",
        "status": "pass",
        "input_count": "1.000000",
        "pass_count": "1.000000",
        "watch_count": "0.000000",
        "blocked_count": "0.000000",
        "max_probability_gap": "0.010000",
        "reason_codes": ["cross_team_disagreement_report_pass"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "derived_validation_digest": first_payload["derived_validation_digest"],
    }
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )

    payload_text = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "execute",
        "execution",
        "database",
        "network",
        "persist",
        "live",
    ):
        assert forbidden not in payload_text

    tampered = json.loads(json.dumps(first_payload))
    tampered["rows"][0]["max_probability_gap"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        cross_team_disagreement_escalation_report_payload(tampered)

    execution_surface = resign_public_payload({**first_payload, "execution_mode": "paper"})
    with pytest.raises(ValueError, match="public"):
        cross_team_disagreement_escalation_report_payload(execution_surface)


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    summary = report(disagreement_input())

    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        disagreement_input(primary_team_probability=0.61)

    with pytest.raises(ValueError, match="advisory_team_probabilities"):
        disagreement_input(advisory_team_probabilities=(d("0.600000"), 0.62))

    with pytest.raises(ValueError, match="paper_only"):
        replace(disagreement_input(), paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(summary.rows[0], readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary.rows[0], max_probability_gap=d("0.999999"))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, watch_count=d("1.000000"))


def test_no_io_execution_or_trading_surface_is_exposed() -> None:
    assert set(CROSS_TEAM_DISAGREEMENT_ESCALATION_STATUSES) == {
        "pass",
        "watch",
        "blocked",
    }

    unsafe_terms = (
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "execute",
        "execution",
        "database",
        "network",
        "persist",
        "live",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        CrossTeamDisagreementEscalationInput,
        CrossTeamDisagreementEscalationReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    tree = ast.parse(inspect.getsource(api))
    imported_modules = {
        node.module.split(".")[0] if isinstance(node, ast.ImportFrom) else alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(node.module or "")])
    }
    assert imported_modules.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "supabase",
            "web3",
            "ccxt",
            "subprocess",
            "pathlib",
        },
    )
