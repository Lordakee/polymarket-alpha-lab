from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_probability_event_playbook_rank_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_probability_event_playbook_rank_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "candidate_id": "candidate_macro_cpi_july",
        "category_id": "macro_rates",
        "event_archetype": "cpi_surprise",
        "required_source_families": (
            "official_release",
            "economic_calendar",
            "market_price",
        ),
    }
    values.update(overrides)
    return module.TeamSpecialistProbabilityEventCandidateV2(**values)


def playbook(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "team_id": "alpha_specialists",
        "specialist_id": "macro_calibration_lead",
        "playbook_id": "macro_cpi_surprise_playbook",
        "category_ids": ("macro_rates", "labor_market"),
        "event_archetypes": ("cpi_surprise", "fed_meeting"),
        "archetype_recurrence_count": d("8"),
        "calibration_memory_score": d("0.900000"),
        "source_family_ids": (
            "official_release",
            "economic_calendar",
            "market_price",
        ),
        "recent_forecast_error": d("0.050000"),
        "observed_at": GENERATED_AT - timedelta(hours=2),
    }
    values.update(overrides)
    return module.TeamSpecialistProbabilityEventPlaybookV2(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    event_candidate = overrides.pop("event_candidate", candidate())
    config = overrides.pop("config", None)
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            playbook(),
            playbook(
                team_id="beta_specialists",
                specialist_id="macro_source_lead",
                playbook_id="macro_release_confirmation_playbook",
                archetype_recurrence_count=d("3"),
                calibration_memory_score=d("0.700000"),
                source_family_ids=("official_release", "economic_calendar"),
                recent_forecast_error=d("0.200000"),
                observed_at=GENERATED_AT - timedelta(hours=5),
            ),
            playbook(
                team_id="gamma_specialists",
                specialist_id="sports_rotation_lead",
                playbook_id="basketball_injury_playbook",
                category_ids=("sports_basketball",),
                event_archetypes=("injury_status_change",),
                archetype_recurrence_count=d("6"),
                calibration_memory_score=d("0.400000"),
                source_family_ids=("official_release",),
                recent_forecast_error=d("0.550000"),
                observed_at=GENERATED_AT - timedelta(hours=1),
            ),
        )
    return module.build_team_specialist_probability_event_playbook_rank_v2_report(
        event_candidate=event_candidate,
        playbooks=items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_builds_ranked_decimal_playbook_report_and_public_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.rank_status == "apply"
    assert report.candidate_id == "candidate_macro_cpi_july"
    assert report.category_id == "macro_rates"
    assert report.event_archetype == "cpi_surprise"
    assert report.playbook_count == d("3")
    assert report.apply_count == d("1")
    assert report.watch_count == d("1")
    assert report.skip_count == d("1")
    assert report.average_playbook_apply_score == d("0.635000")
    assert report.top_playbook_apply_score == d("0.967500")
    assert report.reason_codes == (
        "team_specialist_probability_event_playbook_rank_apply_rows",
        "team_specialist_probability_event_playbook_rank_watch_rows",
        "team_specialist_probability_event_playbook_rank_skip_rows",
    )

    rows = report.rows
    assert tuple(row.playbook_id for row in rows) == (
        "macro_cpi_surprise_playbook",
        "macro_release_confirmation_playbook",
        "basketball_injury_playbook",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.playbook_status for row in rows) == ("apply", "watch", "skip")
    assert tuple(row.playbook_apply_score for row in rows) == (
        d("0.967500"),
        d("0.720000"),
        d("0.217500"),
    )
    assert rows[0].category_match_score == d("1.000000")
    assert rows[0].archetype_recurrence_score == d("1.000000")
    assert rows[0].source_coverage_score == d("1.000000")
    assert rows[0].forecast_accuracy_score == d("0.950000")
    assert rows[2].reason_codes == (
        "team_specialist_probability_event_playbook_category_mismatch",
        "team_specialist_probability_event_playbook_archetype_gap",
        "team_specialist_probability_event_playbook_calibration_memory_weak",
        "team_specialist_probability_event_playbook_source_coverage_gap",
        "team_specialist_probability_event_playbook_recent_error_high",
        "team_specialist_probability_event_playbook_skip",
    )

    payload = report.payload
    assert payload["playbook_count"] == "3"
    assert payload["average_playbook_apply_score"] == "0.635000"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["playbook_apply_score"] == "0.967500"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_empty_rank_is_digest_backed_and_report_only() -> None:
    module = api()

    report = module.build_team_specialist_probability_event_playbook_rank_v2_report(
        event_candidate=candidate(),
        playbooks=(),
        generated_at=GENERATED_AT,
    )

    assert report.rank_status == "skip"
    assert report.playbook_count == d("0")
    assert report.apply_count == d("0")
    assert report.watch_count == d("0")
    assert report.skip_count == d("0")
    assert report.average_playbook_apply_score == d("0.000000")
    assert report.top_playbook_apply_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "team_specialist_probability_event_playbook_rank_empty",
    )
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistProbabilityEventPlaybookRankV2Config()
    event_candidate = candidate()
    sample = playbook()
    report = build_report(sample, event_candidate=event_candidate)
    row = report.rows[0]

    decimal_fields = {
        "category_match_weight",
        "archetype_recurrence_weight",
        "calibration_memory_weight",
        "source_coverage_weight",
        "forecast_accuracy_weight",
        "max_archetype_recurrence_count",
        "apply_score_floor",
        "watch_score_floor",
        "archetype_recurrence_count",
        "calibration_memory_score",
        "recent_forecast_error",
        "rank",
        "category_match_score",
        "archetype_recurrence_score",
        "source_coverage_score",
        "forecast_accuracy_score",
        "matched_source_family_count",
        "required_source_family_count",
        "playbook_apply_score",
        "playbook_count",
        "apply_count",
        "watch_count",
        "skip_count",
        "average_playbook_apply_score",
        "top_playbook_apply_score",
    }

    for item in (config, event_candidate, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in decimal_fields:
                assert type(getattr(item, field.name)) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "calibration_memory_score",
            _DecimalSubclass("0.900000"),
            "calibration_memory_score must be exactly Decimal",
        ),
        (
            "recent_forecast_error",
            d("1.000001"),
            "recent_forecast_error must be <= 1.000000",
        ),
        (
            "calibration_memory_score",
            d("0.8500004"),
            "calibration_memory_score must use six decimal places or fewer",
        ),
        (
            "archetype_recurrence_count",
            Decimal("NaN"),
            "archetype_recurrence_count must be finite",
        ),
        (
            "archetype_recurrence_count",
            d("1.5"),
            "archetype_recurrence_count must be an integral Decimal",
        ),
        (
            "archetype_recurrence_count",
            d("-1"),
            "archetype_recurrence_count must be >= 0.000000",
        ),
    ),
)
def test_playbook_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        playbook(**{field_name: bad_value})


def test_config_validation_rejects_bad_weights_thresholds_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="category_match_weight must be exactly Decimal"):
        module.TeamSpecialistProbabilityEventPlaybookRankV2Config(
            category_match_weight=0,
        )
    with pytest.raises(ValueError, match="rank weights must sum to 1.000000"):
        module.TeamSpecialistProbabilityEventPlaybookRankV2Config(
            forecast_accuracy_weight=d("0.100000"),
        )
    with pytest.raises(ValueError, match="watch_score_floor must not exceed apply_score_floor"):
        module.TeamSpecialistProbabilityEventPlaybookRankV2Config(
            watch_score_floor=d("0.800000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistProbabilityEventPlaybookRankV2Config(paper_only=False)


def test_build_validation_rejects_wrong_types_dates_duplicates_and_disabled_flags() -> None:
    module = api()

    with pytest.raises(
        ValueError,
        match="event_candidate must be TeamSpecialistProbabilityEventCandidateV2",
    ):
        module.build_team_specialist_probability_event_playbook_rank_v2_report(
            event_candidate=object(),
            playbooks=(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="playbooks must be a list or tuple"):
        module.build_team_specialist_probability_event_playbook_rank_v2_report(
            event_candidate=candidate(),
            playbooks=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="playbooks must contain TeamSpecialistProbabilityEventPlaybookV2 values",
    ):
        module.build_team_specialist_probability_event_playbook_rank_v2_report(
            event_candidate=candidate(),
            playbooks=[object()],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_probability_event_playbook_rank_v2_report(
            event_candidate=candidate(),
            playbooks=[playbook()],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="observed_at must be on or before generated_at"):
        module.build_team_specialist_probability_event_playbook_rank_v2_report(
            event_candidate=candidate(),
            playbooks=[playbook(observed_at=GENERATED_AT + timedelta(seconds=1))],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="playbooks must have unique public keys"):
        module.build_team_specialist_probability_event_playbook_rank_v2_report(
            event_candidate=candidate(),
            playbooks=(playbook(), playbook()),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="required_source_families must not be empty"):
        candidate(required_source_families=())
    with pytest.raises(ValueError, match="readonly must be True"):
        playbook(readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_playbook_apply_score=d("0.600000"))
    with pytest.raises(ValueError, match="derived_validation_digest must match row fields"):
        replace(report.rows[0], playbook_apply_score=d("0.900000"))


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live_team",
        "auth_team",
        "wallet_team",
        "order_team",
        "network_team",
        "database_team",
        "persist_team",
        "signing_team",
        "mutation_team",
        "buy_team",
        "sell_team",
        "trade_team",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            playbook(team_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_report_revalidates_row_order_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by apply score and rank"):
        replace(
            report,
            rows=(report.rows[1], report.rows[0], report.rows[2]),
        )
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(report, apply_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match rank_status"):
        replace(
            report,
            reason_codes=("team_specialist_probability_event_playbook_rank_empty",),
        )


def test_public_surface_is_readonly_report_only_and_has_no_live_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
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

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])

    module = api()
    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_PROBABILITY_EVENT_PLAYBOOK_RANK_V2_CONFIG_VERSION",
        "TeamSpecialistProbabilityEventCandidateV2",
        "TeamSpecialistProbabilityEventPlaybookRankV2Config",
        "TeamSpecialistProbabilityEventPlaybookRankV2Report",
        "TeamSpecialistProbabilityEventPlaybookRankV2Row",
        "TeamSpecialistProbabilityEventPlaybookV2",
        "build_team_specialist_probability_event_playbook_rank_v2_report",
        "team_specialist_probability_event_playbook_rank_v2_payload",
    )
