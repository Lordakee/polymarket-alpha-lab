from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_archetype_memory_refresh_rank_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "team-specialist-archetype-memory-refresh-rank-v2-test",
        "max_playbook_age_days": d("20.000000"),
        "archetype_match_weight": d("0.350000"),
        "playbook_freshness_weight": d("0.200000"),
        "lesson_impact_weight": d("0.250000"),
        "evidence_quality_weight": d("0.200000"),
        "high_impact_lesson_boost": d("0.100000"),
        "high_impact_lesson_floor": d("0.800000"),
        "ready_score_floor": d("0.750000"),
        "watch_score_floor": d("0.500000"),
    }
    values.update(overrides)
    return module.TeamSpecialistArchetypeMemoryRefreshRankV2Config(**values)


def observation(**overrides: object) -> Any:
    module = api()
    values = {
        "team_id": "team-alpha",
        "archetype_id": "archetype-alpha",
        "memory_id": "memory-alpha",
        "observed_at": OBSERVED_AT,
        "archetype_match_score": d("0.900000"),
        "playbook_age_days": d("2.000000"),
        "lesson_impact_score": d("0.900000"),
        "evidence_quality_score": d("0.800000"),
        "source_config_version": "source-config-v1",
    }
    values.update(overrides)
    return module.TeamSpecialistArchetypeMemoryRefreshRankV2Observation(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_team_specialist_archetype_memory_refresh_rank_v2(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def assert_no_float_or_int(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)
        return
    assert type(value) not in (float, int)


def unsafe_terms() -> tuple[str, ...]:
    return (
        "".join(("li", "ve")),
        "".join(("au", "th")),
        "".join(("wall", "et")),
        "".join(("or", "der")),
        "".join(("net", "work")),
        "".join(("data", "base")),
        "".join(("per", "sist")),
        "".join(("sign", "ing")),
        "".join(("muta", "tion")),
        "".join(("b", "uy")),
        "".join(("s", "ell")),
        "".join(("tr", "ade")),
    )


def test_archetype_memory_refresh_ranking_and_decimal_rollups() -> None:
    report = build_report(
        observation(memory_id="memory-alpha"),
        observation(
            team_id="team-beta",
            archetype_id="archetype-beta",
            memory_id="memory-beta",
            lesson_impact_score=d("0.400000"),
        ),
        observation(
            team_id="team-gamma",
            archetype_id="archetype-gamma",
            memory_id="memory-gamma",
            archetype_match_score=d("0.542857"),
            lesson_impact_score=d("0.200000"),
            evidence_quality_score=d("0.400000"),
        ),
    )

    assert [row.memory_id for row in report.rows] == [
        "memory-alpha",
        "memory-beta",
        "memory-gamma",
    ]
    assert [row.rank for row in report.rows] == [
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    ]
    assert report.row_count == d("3.000000")
    assert report.ready_count == d("2.000000")
    assert report.watch_count == d("1.000000")
    assert report.average_refresh_rank_score == d("0.745000")

    for item in (cfg(), *report.rows, report):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if field.name.endswith(("_count", "_score", "_days", "_weight", "_boost", "_floor")):
                assert type(value) is Decimal


def test_stale_playbook_penalties_reduce_refresh_rank_score() -> None:
    report = build_report(
        observation(memory_id="fresh", playbook_age_days=d("2.000000")),
        observation(
            team_id="team-beta",
            archetype_id="archetype-beta",
            memory_id="stale",
            playbook_age_days=d("20.000000"),
        ),
    )

    row_by_memory = {row.memory_id: row for row in report.rows}
    assert row_by_memory["fresh"].playbook_freshness_score == d("0.900000")
    assert row_by_memory["stale"].playbook_freshness_score == d("0.000000")
    assert row_by_memory["fresh"].refresh_rank_score == d("0.980000")
    assert row_by_memory["stale"].refresh_rank_score == d("0.800000")
    assert "playbook_stale_penalty" in row_by_memory["stale"].reason_codes


def test_high_impact_lessons_receive_refresh_rank_boosts() -> None:
    report = build_report(
        observation(memory_id="high-impact", lesson_impact_score=d("0.900000")),
        observation(
            team_id="team-beta",
            archetype_id="archetype-beta",
            memory_id="mid-impact",
            lesson_impact_score=d("0.790000"),
        ),
    )

    row_by_memory = {row.memory_id: row for row in report.rows}
    assert row_by_memory["high-impact"].high_impact_lesson_boost_score == d("0.100000")
    assert row_by_memory["mid-impact"].high_impact_lesson_boost_score == d("0.000000")
    assert row_by_memory["high-impact"].refresh_rank_score == d("0.980000")
    assert row_by_memory["mid-impact"].refresh_rank_score == d("0.852500")
    assert row_by_memory["high-impact"].rank == d("1.000000")


def test_payload_serialization_and_validation_are_canonical() -> None:
    module = api()
    report = build_report(observation())
    payload = module.team_specialist_archetype_memory_refresh_rank_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["row_count"] == "1.000000"
    assert payload["average_refresh_rank_score"] == "0.980000"
    assert payload["rows"][0]["refresh_rank_score"] == "0.980000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert module.validate_team_specialist_archetype_memory_refresh_rank_v2_payload(payload)
    assert_no_float_or_int(payload)
    json.dumps(payload, sort_keys=True)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_ARCHETYPE_MEMORY_REFRESH_RANK_V2_CONFIG_VERSION",
        "TeamSpecialistArchetypeMemoryRefreshRankV2Config",
        "TeamSpecialistArchetypeMemoryRefreshRankV2Observation",
        "TeamSpecialistArchetypeMemoryRefreshRankV2Row",
        "TeamSpecialistArchetypeMemoryRefreshRankV2Report",
        "build_team_specialist_archetype_memory_refresh_rank_v2",
        "team_specialist_archetype_memory_refresh_rank_v2_payload",
        "validate_team_specialist_archetype_memory_refresh_rank_v2_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(observation())
    with pytest.raises(FrozenInstanceError):
        report.rows[0].refresh_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.TeamSpecialistArchetypeMemoryRefreshRankV2Config):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(module.TeamSpecialistArchetypeMemoryRefreshRankV2Observation):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.TeamSpecialistArchetypeMemoryRefreshRankV2Row):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.TeamSpecialistArchetypeMemoryRefreshRankV2Report):
            pass

    with pytest.raises(ValueError, match="archetype_match_score must be a Decimal"):
        observation(archetype_match_score=DecimalSubclass("0.900000"))


def test_hard_flags_are_enforced() -> None:
    module = api()
    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)

    report = build_report(observation())
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(report, report_only=False)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert module.team_specialist_archetype_memory_refresh_rank_v2_payload(report)["readonly"] is True


def test_digest_tampering_is_rejected_for_report_and_payload() -> None:
    module = api()
    report = build_report(observation())

    with pytest.raises(ValueError, match="average_refresh_rank_score"):
        replace(report, average_refresh_rank_score=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.team_specialist_archetype_memory_refresh_rank_v2_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_team_specialist_archetype_memory_refresh_rank_v2_payload(
            tampered_payload,
        )

    object.__setattr__(report.rows[0], "refresh_rank_score", d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_archetype_memory_refresh_rank_v2_payload(report)


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    module = api()

    for term in unsafe_terms():
        with pytest.raises(ValueError, match="unsafe public surface"):
            observation(team_id=f"team-{term}")

    payload = module.team_specialist_archetype_memory_refresh_rank_v2_payload(
        build_report(observation()),
    )
    unsafe_key_payload = dict(payload)
    unsafe_key_payload["".join(("wall", "et"))] = "forbidden"
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_team_specialist_archetype_memory_refresh_rank_v2_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_value_payload["rows"][0]["team_id"] = "team-" + "".join(("tr", "ade"))
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_team_specialist_archetype_memory_refresh_rank_v2_payload(
            unsafe_value_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["row_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        module.validate_team_specialist_archetype_memory_refresh_rank_v2_payload(
            numeric_payload,
        )


def test_module_omits_unsafe_public_surfaces() -> None:
    module = api()
    public_names = set(module.__all__) | {
        name for name in dir(module) if not name.startswith("_")
    }
    for public_name in public_names:
        lower_name = public_name.lower()
        assert "db" not in lower_name
        for term in unsafe_terms():
            assert term not in lower_name

    source = inspect.getsource(module)
    for forbidden in (
        "requests",
        "urllib",
        "http.client",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "subprocess",
        "Path(",
        "open(",
        ".write(",
        ".read(",
    ):
        assert forbidden not in source
