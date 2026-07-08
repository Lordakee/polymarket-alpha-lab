from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_tennis_event_team_memory_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_tennis_event_team_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(**overrides: object) -> Any:
    module = api()
    values = {
        "team_id": "sports_other",
        "category_id": "sports.other",
        "event_group": "grand_slam_final_profile",
        "specialist_role": "tennis_event_specialist",
        "evidence_family": "player_form",
        "last_refreshed_at": GENERATED_AT - timedelta(minutes=30),
        "evidence_count": d("2.000000"),
        "calibration_sample_count": d("12.000000"),
        "brier_like_error": d("0.030000"),
    }
    values.update(overrides)
    return module.ResearchTennisEventTeamMemoryObservation(**values)


def build_report(*items: object, **overrides: object) -> Any:
    module = api()
    values = {
        "observations": items,
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.build_research_tennis_event_team_memory_report(**values)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def sample_observations() -> tuple[Any, ...]:
    return (
        observation(
            evidence_family="player_form",
            last_refreshed_at=GENERATED_AT - timedelta(minutes=30),
        ),
        observation(
            evidence_family="injury",
            last_refreshed_at=GENERATED_AT - timedelta(minutes=45),
        ),
        observation(
            evidence_family="news",
            last_refreshed_at=GENERATED_AT - timedelta(minutes=60),
        ),
        observation(
            event_group="tour_final_profile",
            specialist_role="tennis_injury_specialist",
            evidence_family="player_form",
            last_refreshed_at=GENERATED_AT - timedelta(minutes=50),
            calibration_sample_count=d("12.000000"),
            brier_like_error=d("0.080000"),
        ),
        observation(
            event_group="tour_final_profile",
            specialist_role="tennis_injury_specialist",
            evidence_family="injury",
            last_refreshed_at=GENERATED_AT - timedelta(hours=3),
            calibration_sample_count=d("12.000000"),
            brier_like_error=d("0.080000"),
        ),
        observation(
            event_group="tour_final_profile",
            specialist_role="tennis_injury_specialist",
            evidence_family="news",
            last_refreshed_at=GENERATED_AT - timedelta(hours=3),
            calibration_sample_count=d("12.000000"),
            brier_like_error=d("0.080000"),
        ),
        observation(
            event_group="hardcourt_injury_watch",
            specialist_role="tennis_news_specialist",
            evidence_family="player_form",
            last_refreshed_at=GENERATED_AT - timedelta(hours=8),
            calibration_sample_count=d("2.000000"),
            brier_like_error=d("0.200000"),
        ),
        observation(
            event_group="hardcourt_injury_watch",
            specialist_role="tennis_news_specialist",
            evidence_family="injury",
            last_refreshed_at=None,
            evidence_count=d("0.000000"),
            calibration_sample_count=d("2.000000"),
            brier_like_error=d("0.200000"),
        ),
        observation(
            event_group="hardcourt_injury_watch",
            specialist_role="tennis_news_specialist",
            evidence_family="news",
            last_refreshed_at=GENERATED_AT - timedelta(hours=9),
            calibration_sample_count=d("2.000000"),
            brier_like_error=d("0.200000"),
        ),
    )


def test_builds_all_pass_tennis_event_memory_report() -> None:
    module = api()

    report = build_report(
        observation(
            evidence_family="player_form",
            last_refreshed_at=GENERATED_AT - timedelta(minutes=15),
            evidence_count=d("3.000000"),
            calibration_sample_count=d("12.000000"),
            brier_like_error=d("0.020000"),
        ),
        observation(
            evidence_family="injury",
            last_refreshed_at=GENERATED_AT - timedelta(minutes=20),
            evidence_count=d("3.000000"),
            calibration_sample_count=d("12.000000"),
            brier_like_error=d("0.020000"),
        ),
        observation(
            evidence_family="news",
            last_refreshed_at=GENERATED_AT - timedelta(minutes=25),
            evidence_count=d("3.000000"),
            calibration_sample_count=d("12.000000"),
            brier_like_error=d("0.020000"),
        ),
    )

    assert report.readiness_status == "pass"
    assert report.row_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.reason_codes == (module.PASS_REASON,)
    assert report.reason_code_counts == (
        module.ResearchTennisEventTeamMemoryReasonCodeCount(
            reason_code=module.PASS_REASON,
            count=d("1.000000"),
        ),
    )
    assert report.rows[0].readiness_status == "pass"
    assert module.PASS_REASON in report.rows[0].reason_codes


def test_builds_tennis_event_memory_readiness_report() -> None:
    module = api()

    report = build_report(*sample_observations())

    assert type(report) is module.ResearchTennisEventTeamMemoryReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == module.DEFAULT_CONFIG_VERSION
    assert module.READINESS_STATUSES == ("pass", "watch", "block")
    assert report.readiness_status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.observation_count == d("9.000000")
    assert report.fresh_family_count == d("4.000000")
    assert report.aging_family_count == d("2.000000")
    assert report.stale_family_count == d("2.000000")
    assert report.missing_family_count == d("1.000000")
    assert report.player_form_fresh_count == d("2.000000")
    assert report.injury_fresh_count == d("1.000000")
    assert report.news_fresh_count == d("1.000000")
    assert report.average_readiness_score == d("0.535555")
    assert report.average_calibration_score == d("0.586667")
    assert report.reason_codes == (
        "tennis_event_team_memory_watch_rows",
        "tennis_event_team_memory_block_rows",
        "tennis_event_team_memory_aging_evidence",
        "tennis_event_team_memory_stale_evidence",
        "tennis_event_team_memory_missing_evidence",
        "tennis_event_team_memory_calibration_sample_gap",
    )

    assert tuple(
        (row.readiness_status, row.event_group, row.specialist_role)
        for row in report.rows
    ) == (
        ("block", "hardcourt_injury_watch", "tennis_news_specialist"),
        ("watch", "tour_final_profile", "tennis_injury_specialist"),
        ("pass", "grand_slam_final_profile", "tennis_event_specialist"),
    )

    blocked, watched, passed = report.rows
    assert blocked.reason_codes == (
        "tennis_event_team_memory_block",
        "tennis_event_team_memory_stale_evidence",
        "tennis_event_team_memory_missing_evidence",
        "tennis_event_team_memory_calibration_sample_gap",
    )
    assert blocked.fresh_family_count == d("0.000000")
    assert blocked.stale_family_count == d("2.000000")
    assert blocked.missing_family_count == d("1.000000")
    assert blocked.calibration_sample_count == d("6.000000")
    assert blocked.readiness_score == d("0.100000")

    assert watched.reason_codes == (
        "tennis_event_team_memory_watch",
        "tennis_event_team_memory_aging_evidence",
        "tennis_event_team_memory_player_form_fresh",
        "tennis_event_team_memory_calibration_ready",
    )
    assert watched.freshness_score == d("0.333333")
    assert watched.calibration_score == d("0.680000")
    assert watched.readiness_score == d("0.506666")

    assert passed.readiness_score == d("1.000000")
    assert passed.player_form_fresh_count == d("1.000000")
    assert passed.injury_fresh_count == d("1.000000")
    assert passed.news_fresh_count == d("1.000000")
    assert passed.reason_codes == (
        "tennis_event_team_memory_pass",
        "tennis_event_team_memory_player_form_fresh",
        "tennis_event_team_memory_injury_fresh",
        "tennis_event_team_memory_news_fresh",
        "tennis_event_team_memory_calibration_ready",
    )

    assert report.reason_code_counts == (
        module.ResearchTennisEventTeamMemoryReasonCodeCount(
            reason_code="tennis_event_team_memory_watch_rows",
            count=d("1.000000"),
        ),
        module.ResearchTennisEventTeamMemoryReasonCodeCount(
            reason_code="tennis_event_team_memory_block_rows",
            count=d("1.000000"),
        ),
        module.ResearchTennisEventTeamMemoryReasonCodeCount(
            reason_code="tennis_event_team_memory_aging_evidence",
            count=d("1.000000"),
        ),
        module.ResearchTennisEventTeamMemoryReasonCodeCount(
            reason_code="tennis_event_team_memory_stale_evidence",
            count=d("1.000000"),
        ),
        module.ResearchTennisEventTeamMemoryReasonCodeCount(
            reason_code="tennis_event_team_memory_missing_evidence",
            count=d("1.000000"),
        ),
        module.ResearchTennisEventTeamMemoryReasonCodeCount(
            reason_code="tennis_event_team_memory_calibration_sample_gap",
            count=d("1.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_report_is_blocked_report_only_and_digest_backed() -> None:
    report = build_report()

    assert report.readiness_status == "block"
    assert report.row_count == d("0.000000")
    assert report.rows == ()
    assert report.average_readiness_score == d("0.000000")
    assert report.reason_codes == ("tennis_event_team_memory_empty_observations",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64


def test_payload_is_deterministic_json_ready_and_omits_raw_identifiers() -> None:
    first = build_report(*sample_observations())
    second = build_report(*reversed(sample_observations()))

    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest

    payload = api().research_tennis_event_team_memory_report_payload(first)
    encoded = json.dumps(payload, sort_keys=True)
    assert payload["row_count"] == "3.000000"
    assert payload["average_readiness_score"] == "0.535555"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    assert json.loads(encoded) == payload

    for forbidden in (
        "match_id",
        "match_slug",
        "player_id",
        "player_name",
        "source_id",
        "source_key",
        "raw_match",
        "raw_player",
        "raw_source",
    ):
        assert forbidden not in encoded


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.ResearchTennisEventTeamMemoryReportConfig()
    sample = observation()
    report = build_report(sample)
    row = report.rows[0]

    public_types = (
        module.ResearchTennisEventTeamMemoryReportConfig,
        module.ResearchTennisEventTeamMemoryObservation,
        module.ResearchTennisEventTeamMemoryRow,
        module.ResearchTennisEventTeamMemoryReasonCodeCount,
        module.ResearchTennisEventTeamMemoryReport,
    )
    for public_type in public_types:
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        field_names = {field.name for field in fields(public_type)}
        assert not (
            field_names
            & {
                "match_id",
                "match_slug",
                "player_id",
                "player_name",
                "source_id",
                "source_key",
            }
        )

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_score")
                or field.name.endswith("_seconds")
                or field.name.endswith("_error")
            ):
                assert type(value) is Decimal


def test_validation_rejects_bad_inputs_flag_downgrades_and_digest_tampering() -> None:
    module = api()

    with pytest.raises(ValueError, match="category_id must match team_id"):
        observation(category_id="sports.soccer")
    with pytest.raises(ValueError, match="evidence_family must be a tennis evidence family"):
        observation(evidence_family="lineup")
    with pytest.raises(ValueError, match="last_refreshed_at must be timezone-aware"):
        observation(last_refreshed_at=datetime(2026, 7, 8, 13, 0))
    with pytest.raises(ValueError, match="evidence_count must be exactly Decimal"):
        observation(evidence_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="brier_like_error must be between zero and one"):
        observation(brier_like_error=d("1.000001"))
    with pytest.raises(ValueError, match="event_group has raw identifier surface"):
        observation(event_group="raw_match_9823")
    with pytest.raises(ValueError, match="readonly must be True"):
        observation(readonly=False)

    report = build_report(observation())
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="float"):
        module.research_tennis_event_team_memory_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "score": 0.1,
            },
        )


def test_static_module_surface_is_pure_report_only() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "aiohttp",
        "http",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "delete",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "update",
        "upsert",
        "write",
    }

    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not float_constants
    assert not any(
        imported == forbidden or imported.startswith(f"{forbidden}.")
        for imported in imports
        for forbidden in forbidden_modules
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert "paper_only: bool = True" in source
    assert "report_only: bool = True" in source
    assert "readonly: bool = True" in source
