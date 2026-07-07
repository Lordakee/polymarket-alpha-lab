from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
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
    / "team_specialist_research_quality_coach_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_research_quality_coach_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def memory(**overrides: object):
    module = api()
    values = {
        "team_id": "alpha_specialists",
        "specialist_id": "macro_research",
        "research_lane": "rates_policy",
        "calibration_miss_severity": d("0.080000"),
        "source_family_gap_count": d("0"),
        "stale_playbook_age_days": d("5"),
        "contradiction_miss_count": d("0"),
        "resolution_rule_error_count": d("0"),
        "oldest_postmortem_action_age_days": d("2"),
        "upcoming_event_load": d("1"),
    }
    values.update(overrides)
    return module.TeamSpecialistResearchQualityMemoryV2Input(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop(
        "generated_at",
        datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
    )
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            memory(team_id="alpha_specialists", specialist_id="macro_research"),
            memory(
                team_id="beta_specialists",
                specialist_id="evidence_research",
                research_lane="energy_weather",
                calibration_miss_severity=d("0.240000"),
                source_family_gap_count=d("2"),
                stale_playbook_age_days=d("35"),
                contradiction_miss_count=d("1"),
                resolution_rule_error_count=d("0"),
                oldest_postmortem_action_age_days=d("21"),
                upcoming_event_load=d("4"),
            ),
            memory(
                team_id="gamma_specialists",
                specialist_id="rules_research",
                research_lane="election_rules",
                calibration_miss_severity=d("0.650000"),
                source_family_gap_count=d("4"),
                stale_playbook_age_days=d("90"),
                contradiction_miss_count=d("3"),
                resolution_rule_error_count=d("2"),
                oldest_postmortem_action_age_days=d("60"),
                upcoming_event_load=d("9"),
            ),
        )
    return module.build_team_specialist_research_quality_coach_v2(
        items,
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


def test_builds_ranked_decimal_coaching_report_and_public_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.coach_status == "blocked"
    assert report.memory_count == d("3")
    assert report.pass_memory_count == d("1")
    assert report.watch_memory_count == d("1")
    assert report.blocked_memory_count == d("1")
    assert report.average_quality_risk_score == d("0.427231")
    assert report.top_quality_risk_score == d("0.895000")
    assert report.bottom_quality_risk_score == d("0.044694")
    assert report.reason_codes == (
        "team_specialist_research_quality_coach_blocked_rows",
        "team_specialist_research_quality_coach_watch_rows",
    )

    rows = report.rows
    assert tuple(row.team_id for row in rows) == (
        "gamma_specialists",
        "beta_specialists",
        "alpha_specialists",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.quality_risk_score for row in rows) == (
        d("0.895000"),
        d("0.342000"),
        d("0.044694"),
    )
    assert tuple(row.coaching_status for row in rows) == ("blocked", "watch", "pass")
    assert rows[0].recommended_actions == (
        "refresh_playbook",
        "expand_source_families",
        "tighten_contradiction_checks",
        "review_resolution_rules",
        "close_postmortem_actions",
        "triage_upcoming_event_load",
        "recalibrate_probability_ranges",
    )

    payload = report.payload
    assert payload["memory_count"] == "3"
    assert payload["average_quality_risk_score"] == "0.427231"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["quality_risk_score"] == "0.895000"
    assert len(report.derived_validation_digest) == 64
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert_no_float_values(payload)


def test_empty_coaching_report_is_report_only_and_digest_backed() -> None:
    report = build_report(
        *(),
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
        use_default_items=False,
    )

    assert report.coach_status == "blocked"
    assert report.memory_count == d("0")
    assert report.average_quality_risk_score == d("0.000000")
    assert report.top_quality_risk_score == d("0.000000")
    assert report.bottom_quality_risk_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("team_specialist_research_quality_coach_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistResearchQualityCoachV2Config()
    sample = memory()
    report = build_report(sample)
    row = report.rows[0]

    decimal_fields = {
        "calibration_miss_weight",
        "source_family_gap_weight",
        "stale_playbook_weight",
        "contradiction_miss_weight",
        "resolution_rule_error_weight",
        "postmortem_action_age_weight",
        "upcoming_event_load_weight",
        "max_source_family_gap_count",
        "stale_playbook_block_days",
        "max_contradiction_miss_count",
        "max_resolution_rule_error_count",
        "postmortem_action_block_days",
        "high_upcoming_event_load_count",
        "pass_risk_ceiling",
        "watch_risk_ceiling",
        "calibration_miss_severity",
        "source_family_gap_count",
        "stale_playbook_age_days",
        "contradiction_miss_count",
        "resolution_rule_error_count",
        "oldest_postmortem_action_age_days",
        "upcoming_event_load",
        "rank",
        "calibration_miss_risk",
        "source_family_gap_risk",
        "stale_playbook_risk",
        "contradiction_miss_risk",
        "resolution_rule_error_risk",
        "postmortem_action_age_risk",
        "upcoming_event_load_risk",
        "quality_risk_score",
        "memory_count",
        "pass_memory_count",
        "watch_memory_count",
        "blocked_memory_count",
        "average_quality_risk_score",
        "top_quality_risk_score",
        "bottom_quality_risk_score",
    }

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in decimal_fields:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "calibration_miss_severity",
            _DecimalSubclass("0.100000"),
            "calibration_miss_severity must be exactly Decimal",
        ),
        (
            "calibration_miss_severity",
            d("1.000001"),
            "calibration_miss_severity must be <= 1.000000",
        ),
        (
            "source_family_gap_count",
            d("1.5"),
            "source_family_gap_count must be an integral Decimal",
        ),
        (
            "stale_playbook_age_days",
            d("-1"),
            "stale_playbook_age_days must be >= 0.000000",
        ),
        (
            "contradiction_miss_count",
            Decimal("NaN"),
            "contradiction_miss_count must be finite",
        ),
        (
            "oldest_postmortem_action_age_days",
            d("2.0000004"),
            "oldest_postmortem_action_age_days must use six decimal places or fewer",
        ),
    ),
)
def test_input_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        memory(**{field_name: bad_value})


def test_config_validation_rejects_bad_weights_thresholds_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="calibration_miss_weight must be exactly Decimal"):
        module.TeamSpecialistResearchQualityCoachV2Config(
            calibration_miss_weight=0,
        )
    with pytest.raises(
        ValueError,
        match="coach weights must sum to 1.000000",
    ):
        module.TeamSpecialistResearchQualityCoachV2Config(
            calibration_miss_weight=d("0.310000"),
        )
    with pytest.raises(ValueError, match="pass_risk_ceiling must not exceed watch_risk_ceiling"):
        module.TeamSpecialistResearchQualityCoachV2Config(
            pass_risk_ceiling=d("0.600000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistResearchQualityCoachV2Config(paper_only=False)


def test_build_validation_rejects_wrong_types_and_disabled_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="quality_memories must be an iterable"):
        module.build_team_specialist_research_quality_coach_v2(
            object(),
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="quality memory items must be TeamSpecialistResearchQualityMemoryV2Input",
    ):
        module.build_team_specialist_research_quality_coach_v2(
            [object()],
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_research_quality_coach_v2(
            [memory()],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        memory(readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(
            report,
            average_quality_risk_score=d("0.420000"),
        )


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
            memory(team_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_report_revalidates_row_order_counts_reason_codes_and_recommendations() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by quality risk and rank"):
        replace(
            report,
            rows=(report.rows[1], report.rows[0], report.rows[2]),
        )
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(
            report,
            pass_memory_count=d("2"),
        )
    with pytest.raises(ValueError, match="reason_codes must match coach_status"):
        replace(
            report,
            reason_codes=("team_specialist_research_quality_coach_passed",),
        )
    with pytest.raises(ValueError, match="recommended_actions must match row risks"):
        replace(
            report.rows[0],
            recommended_actions=("refresh_playbook",),
        )


def test_module_scope_has_no_file_database_network_or_order_surface() -> None:
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
