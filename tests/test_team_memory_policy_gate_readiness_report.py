from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.team_memory_policy_gate_readiness_report import (
    TeamMemoryPolicyGateCandidate,
    TeamMemoryPolicyGateReadinessConfig,
    TeamMemoryPolicyGateReadinessReasonCodeCount,
    TeamMemoryPolicyGateReadinessReport,
    TeamMemoryPolicyGateReadinessRow,
    build_team_memory_policy_gate_readiness_report,
    team_memory_policy_gate_readiness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 12, 9, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> TeamMemoryPolicyGateReadinessConfig:
    values = {
        "config_version": "team-memory-policy-gate-readiness-v0",
        "allow_context_floor": d("0.800000"),
        "throttle_context_floor": d("0.500000"),
        "manual_follow_up_floor": d("0.500000"),
    }
    values.update(overrides)
    return TeamMemoryPolicyGateReadinessConfig(**values)


def candidate(
    candidate_id: str,
    *,
    memory_context_score: str,
    memory_gap_score: str = "0.000000",
    redaction_confirmed: bool = True,
    stale_memory_flag: bool = False,
    conflicting_memory_flag: bool = False,
    reason_codes: tuple[str, ...] = (),
) -> TeamMemoryPolicyGateCandidate:
    return TeamMemoryPolicyGateCandidate(
        candidate_id=candidate_id,
        memory_context_score=d(memory_context_score),
        memory_gap_score=d(memory_gap_score),
        redaction_confirmed=redaction_confirmed,
        stale_memory_flag=stale_memory_flag,
        conflicting_memory_flag=conflicting_memory_flag,
        reason_codes=reason_codes,
    )


def report(
    candidates: tuple[object, ...],
    *,
    cfg: TeamMemoryPolicyGateReadinessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> TeamMemoryPolicyGateReadinessReport:
    return build_team_memory_policy_gate_readiness_report(
        candidates,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_allow_throttle_block_rows_are_context_gate_only_and_deterministic() -> None:
    readiness_report = report(
        (
            candidate("candidate-allow", memory_context_score="0.900000"),
            candidate(
                "candidate-throttle",
                memory_context_score="0.650000",
                memory_gap_score="0.600000",
                stale_memory_flag=True,
            ),
            candidate(
                "candidate-block",
                memory_context_score="0.950000",
                redaction_confirmed=False,
                conflicting_memory_flag=True,
            ),
        ),
    )

    assert type(readiness_report) is TeamMemoryPolicyGateReadinessReport
    assert readiness_report.generated_at == GENERATED_AT
    assert readiness_report.config_version == "team-memory-policy-gate-readiness-v0"
    assert readiness_report.candidate_count == d("3")
    assert readiness_report.allow_count == d("1")
    assert readiness_report.throttle_count == d("1")
    assert readiness_report.block_count == d("1")
    assert readiness_report.manual_follow_up_count == d("2")
    assert readiness_report.gate_status == "block"
    assert readiness_report.reason_codes == (
        "memory_policy_allow_context",
        "memory_policy_block_context",
        "memory_policy_throttle_context",
    )
    assert readiness_report.reason_code_counts == (
        TeamMemoryPolicyGateReadinessReasonCodeCount(
            reason_code="memory_policy_allow_context",
            count=d("1"),
        ),
        TeamMemoryPolicyGateReadinessReasonCodeCount(
            reason_code="memory_policy_block_context",
            count=d("1"),
        ),
        TeamMemoryPolicyGateReadinessReasonCodeCount(
            reason_code="memory_policy_throttle_context",
            count=d("1"),
        ),
    )
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True

    rows = readiness_report.rows
    assert tuple(row.candidate_id for row in rows) == (
        "candidate-allow",
        "candidate-block",
        "candidate-throttle",
    )
    assert tuple(type(row) for row in rows) == (
        TeamMemoryPolicyGateReadinessRow,
        TeamMemoryPolicyGateReadinessRow,
        TeamMemoryPolicyGateReadinessRow,
    )
    assert rows[0].policy_status == "allow"
    assert rows[0].gate_status == "pass"
    assert rows[0].manual_follow_up is False
    assert rows[0].reason_codes == ("memory_policy_allow_context",)
    assert rows[1].policy_status == "block"
    assert rows[1].gate_status == "block"
    assert rows[1].manual_follow_up is True
    assert rows[1].reason_codes == (
        "memory_context_redaction_not_confirmed",
        "memory_policy_block_context",
        "memory_policy_conflicting_context",
    )
    assert rows[2].policy_status == "throttle"
    assert rows[2].gate_status == "watch"
    assert rows[2].manual_follow_up is True
    assert rows[2].reason_codes == (
        "memory_context_gap_follow_up",
        "memory_policy_stale_context",
        "memory_policy_throttle_context",
    )
    assert all(row.paper_only and row.report_only and row.readonly for row in rows)


def test_empty_input_returns_block_report_only_context_gate() -> None:
    readiness_report = report(())

    assert readiness_report.candidate_count == d("0")
    assert readiness_report.allow_count == d("0")
    assert readiness_report.throttle_count == d("0")
    assert readiness_report.block_count == d("0")
    assert readiness_report.manual_follow_up_count == d("0")
    assert readiness_report.gate_status == "block"
    assert readiness_report.reason_codes == ("no_memory_policy_candidates",)
    assert readiness_report.reason_code_counts == (
        TeamMemoryPolicyGateReadinessReasonCodeCount(
            reason_code="no_memory_policy_candidates",
            count=d("1"),
        ),
    )
    assert readiness_report.rows == ()
    assert readiness_report.paper_only is True
    assert readiness_report.report_only is True
    assert readiness_report.readonly is True


def test_payload_is_json_ready_and_excludes_ranking_position_approval_fields() -> None:
    readiness_report = report(
        (
            candidate("candidate-allow", memory_context_score="0.900000"),
            candidate(
                "candidate-throttle",
                memory_context_score="0.650000",
                memory_gap_score="0.600000",
                reason_codes=("analyst_context_review_requested",),
            ),
        ),
    )
    payload = team_memory_policy_gate_readiness_report_payload(readiness_report)
    encoded = json.dumps(payload, sort_keys=True)
    encoded_lower = encoded.lower()

    assert payload["generated_at"] == "2026-07-12T09:30:00+00:00"
    assert payload["rows"][0]["policy_status"] == "allow"
    assert payload["rows"][1]["manual_follow_up"] is True
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0." not in encoded
    for forbidden in (
        "rank",
        "ranking",
        "position",
        "notional",
        "approved",
        "approval",
        "authorize",
        "wallet",
        "order",
        "auth",
        "live",
        "private_key",
        "token",
        "dsn",
        "database_url",
        "postgres://",
        "postgresql://",
        "supabase.co",
    ):
        assert forbidden not in encoded_lower


def test_validation_rejects_bad_types_secret_text_bad_flags_and_thresholds() -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="team memory policy gate")
    with pytest.raises(ValueError, match="allow_context_floor"):
        config(allow_context_floor=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="throttle_context_floor"):
        config(throttle_context_floor=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="allow_context_floor"):
        config(allow_context_floor=d("0.400000"), throttle_context_floor=d("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=datetime(2026, 7, 12, 9, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=_DatetimeSubclass(2026, 7, 12, 9, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="candidate_id"):
        candidate("market-alpha", memory_context_score="0.900000")
    with pytest.raises(ValueError, match="memory_context_score"):
        candidate("candidate-alpha", memory_context_score="1.000001")
    with pytest.raises(ValueError, match="memory_gap_score"):
        replace(candidate("candidate-alpha", memory_context_score="0.900000"), memory_gap_score=1)
    with pytest.raises(ValueError, match="redaction_confirmed"):
        replace(candidate("candidate-alpha", memory_context_score="0.900000"), redaction_confirmed=1)
    with pytest.raises(ValueError, match="stale_memory_flag"):
        replace(candidate("candidate-alpha", memory_context_score="0.900000"), stale_memory_flag=0)
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(
            "candidate-alpha",
            memory_context_score="0.900000",
            reason_codes=("Needs Review",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate("candidate-alpha", memory_context_score="0.900000"), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    readiness_report = report((candidate("candidate-alpha", memory_context_score="0.900000"),))

    with pytest.raises(FrozenInstanceError):
        readiness_report.gate_status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        readiness_report.rows[0].policy_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="policy_status"):
        replace(readiness_report.rows[0], policy_status="block")
    with pytest.raises(ValueError, match="gate_status"):
        replace(readiness_report, gate_status="block")


def test_owned_module_has_no_persistence_network_execution_or_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "team_memory_policy_gate_readiness_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "psycopg",
        "asyncpg",
        "sqlalchemy",
        "create_client",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "write(",
        "connect(",
        "execute(",
        "wallet",
        "order",
        "private_key",
        "live",
        "auth",
        "rank",
        "position",
        "approval",
        "approve",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
