from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_team_memory_health_report import (
    ResearchTeamMemoryHealthConfig,
    ResearchTeamMemoryHealthReasonCodeCount,
    ResearchTeamMemoryHealthReport,
    ResearchTeamMemoryHealthRow,
    ResearchTeamMemoryObservation,
    build_research_team_memory_health_report,
    research_team_memory_health_report_payload,
    research_team_memory_health_report_text,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchTeamMemoryHealthConfig:
    values = {
        "config_version": "research-team-memory-health-report-v0",
        "fresh_age_seconds": d("604800"),
        "stale_age_seconds": d("2592000"),
        "pass_health_score": d("0.750000"),
        "watch_health_score": d("0.500000"),
        "pass_coverage_score": d("0.700000"),
        "min_traceability_score": d("0.600000"),
        "blocking_conflict_count": d("3"),
        "coverage_weight": d("0.300000"),
        "freshness_weight": d("0.250000"),
        "conflict_weight": d("0.200000"),
        "traceability_weight": d("0.250000"),
        "conflict_penalty": d("0.250000"),
    }
    values.update(overrides)
    return ResearchTeamMemoryHealthConfig(**values)


def memory(
    index: int,
    *,
    team_domain: str = "financial",
    memory_topic: str = "macro-risk",
    coverage_score: Decimal = d("0.950000"),
    last_reviewed_at: datetime | None = None,
    conflict_count: Decimal = d("0"),
    traceability_score: Decimal = d("0.900000"),
    public_summary: str = "coverage checked",
) -> ResearchTeamMemoryObservation:
    return ResearchTeamMemoryObservation(
        team_domain=team_domain,
        memory_topic=memory_topic,
        memory_record_key=f"internal-record-{index:03d}",
        coverage_score=coverage_score,
        last_reviewed_at=(
            last_reviewed_at
            if last_reviewed_at is not None
            else GENERATED_AT - timedelta(days=1)
        ),
        conflict_count=conflict_count,
        traceability_score=traceability_score,
        public_summary=public_summary,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchTeamMemoryHealthConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamMemoryHealthReport:
    return build_research_team_memory_health_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_with_memory_planning_text() -> None:
    health_report = report(())
    rendered = research_team_memory_health_report_text(health_report)

    assert type(health_report) is ResearchTeamMemoryHealthReport
    assert health_report.generated_at == GENERATED_AT
    assert health_report.team_count == d("0")
    assert health_report.pass_count == d("0")
    assert health_report.watch_count == d("0")
    assert health_report.blocked_count == d("0")
    assert health_report.average_health_score is None
    assert health_report.status == "blocked"
    assert health_report.reason_codes == ("no_memory_rows",)
    assert health_report.reason_code_counts == (
        ResearchTeamMemoryHealthReasonCodeCount(
            reason_code="no_memory_rows",
            count=d("1"),
        ),
    )
    assert health_report.rows == ()
    assert "Local Supabase/Postgres memory planning fields" in rendered
    assert "memory_key" in rendered
    assert "traceability_score" in rendered
    assert "connect(" not in rendered.lower()


def test_team_memory_health_scores_pass_watch_and_block_deterministically() -> None:
    health_report = report(
        (
            memory(
                3,
                team_domain="sports",
                memory_topic="injury-news",
                coverage_score=d("0.200000"),
                last_reviewed_at=GENERATED_AT - timedelta(days=45),
                conflict_count=d("4"),
                traceability_score=d("0.200000"),
            ),
            memory(
                2,
                team_domain="political",
                memory_topic="election-integrity",
                coverage_score=d("0.650000"),
                last_reviewed_at=GENERATED_AT - timedelta(days=14),
                conflict_count=d("1"),
                traceability_score=d("0.700000"),
            ),
            memory(1),
        ),
    )

    assert tuple(
        (row.team_domain, row.memory_topic) for row in health_report.rows
    ) == (
        ("financial", "macro-risk"),
        ("political", "election-integrity"),
        ("sports", "injury-news"),
    )
    assert health_report.status == "blocked"
    assert health_report.team_count == d("3")
    assert health_report.pass_count == d("1")
    assert health_report.watch_count == d("1")
    assert health_report.blocked_count == d("1")
    assert health_report.average_health_score == d("0.587971")

    financial, political, sports = health_report.rows
    assert financial.health_score == d("0.960000")
    assert financial.status == "pass"
    assert financial.reason_codes == (
        "conflict_free",
        "fresh_memory",
        "memory_health_pass",
        "strong_coverage",
        "traceability_ready",
    )
    assert political.freshness_score == d("0.695652")
    assert political.conflict_score == d("0.750000")
    assert political.health_score == d("0.693913")
    assert political.status == "watch"
    assert sports.freshness_score == d("0.000000")
    assert sports.conflict_score == d("0.000000")
    assert sports.health_score == d("0.110000")
    assert sports.status == "blocked"


def test_payload_uses_decimal_strings_and_excludes_internal_references() -> None:
    health_report = report(
        (
            memory(2, team_domain="sports", memory_topic="injury-news"),
            memory(1),
        ),
    )

    payload = research_team_memory_health_report_payload(health_report)
    encoded = json.dumps(payload, sort_keys=True)
    keys = tuple(key.lower() for key in _walk_payload_keys(payload))

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["rows"][0]["health_score"] == "0.960000"
    assert payload["rows"][0]["conflict_count"] == "0"
    assert payload["memory_plan_fields"] == [
        "memory_key",
        "team_domain",
        "memory_topic",
        "coverage_score",
        "last_reviewed_at",
        "conflict_count",
        "traceability_score",
        "public_summary",
        "review_status",
        "reviewed_at",
    ]
    assert "internal-record-001" not in encoded
    assert "memory_record_key" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(
        fragment in key
        for key in keys
        for fragment in ("source", "url", "table", "dsn", "token")
    )
    assert not any(key == "id" or key.endswith("_id") for key in keys)


def test_validation_rejects_bad_types_future_times_unsafe_text_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="coverage_weight"):
        config(coverage_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_health_score"):
        config(pass_health_score=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="coverage_score"):
        memory(1, coverage_score=_DecimalSubclass("0.950000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((memory(1),), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (memory(1),),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="team_domain"):
        memory(1, team_domain=" financial")
    with pytest.raises(ValueError, match="last_reviewed_at"):
        memory(1, last_reviewed_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="last_reviewed_at"):
        report((memory(1, last_reviewed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="conflict_count"):
        replace(memory(1), conflict_count=d("-1"))
    with pytest.raises(ValueError, match="public_summary"):
        replace(memory(1), public_summary="see https://private.example")
    with pytest.raises(ValueError, match="paper_only"):
        replace(memory(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    health_report = report((memory(1),))

    with pytest.raises(FrozenInstanceError):
        health_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        health_report.rows[0].health_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="health_score"):
        replace(health_report.rows[0], health_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(health_report, status="blocked")


def test_owned_module_has_no_database_network_filesystem_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_memory_health_report.py"
    )
    module_text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "psycopg",
        "sqlalchemy",
        "create_engine",
    )

    assert all(term not in module_text for term in forbidden_terms)


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


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
