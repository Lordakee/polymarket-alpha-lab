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
    / "team_specialist_calibration_followup_scheduler_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_calibration_followup_scheduler_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object):
    module = api()
    values = {
        "config_version": "team-specialist-calibration-followup-scheduler-v2-test",
        "recent_forecast_miss_severity_weight": d("0.260000"),
        "domain_calibration_decay_weight": d("0.190000"),
        "stale_playbook_risk_weight": d("0.170000"),
        "source_quality_failure_rate_weight": d("0.150000"),
        "unresolved_postmortem_pressure_weight": d("0.130000"),
        "upcoming_event_load_weight": d("0.100000"),
        "max_domain_calibration_age_seconds": d("2592000.000000"),
        "max_unresolved_postmortem_count": d("4"),
        "max_upcoming_event_count": d("8"),
        "urgent_priority_floor": d("0.700000"),
        "watch_priority_floor": d("0.400000"),
        "urgent_followup_due_after_seconds": d("86400.000000"),
        "watch_followup_due_after_seconds": d("259200.000000"),
        "routine_followup_due_after_seconds": d("604800.000000"),
    }
    values.update(overrides)
    return module.TeamSpecialistCalibrationFollowupSchedulerV2Config(**values)


def memory(**overrides: object):
    module = api()
    values = {
        "team_id": "alpha_specialists",
        "specialist_id": "rates_lead",
        "domain_id": "macro_rates",
        "recent_forecast_miss_severity": d("0.800000"),
        "domain_calibration_age_seconds": d("2592000.000000"),
        "stale_playbook_risk": d("0.700000"),
        "source_quality_failure_rate": d("0.600000"),
        "unresolved_postmortem_count": d("4"),
        "upcoming_event_count": d("8"),
    }
    values.update(overrides)
    return module.TeamSpecialistCalibrationFollowupMemoryV2Input(**values)


def build_report(*items: object, config: object | None = None, generated_at=GENERATED_AT):
    module = api()
    if not items:
        items = (
            memory(team_id="alpha_specialists", specialist_id="rates_lead"),
            memory(
                team_id="beta_specialists",
                specialist_id="inflation_lead",
                domain_id="macro_inflation",
                recent_forecast_miss_severity=d("0.450000"),
                domain_calibration_age_seconds=d("1296000.000000"),
                stale_playbook_risk=d("0.500000"),
                source_quality_failure_rate=d("0.300000"),
                unresolved_postmortem_count=d("1"),
                upcoming_event_count=d("4"),
            ),
            memory(
                team_id="gamma_specialists",
                specialist_id="labor_lead",
                domain_id="macro_labor",
                recent_forecast_miss_severity=d("0.050000"),
                domain_calibration_age_seconds=d("86400.000000"),
                stale_playbook_risk=d("0.100000"),
                source_quality_failure_rate=d("0.050000"),
                unresolved_postmortem_count=d("0"),
                upcoming_event_count=d("1"),
            ),
        )
    return module.build_team_specialist_calibration_followup_scheduler_v2(
        items,
        config=config or cfg(),
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


def test_builds_priority_sorted_decimal_followup_report_and_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.schedule_status == "urgent"
    assert report.specialist_count == d("3")
    assert report.urgent_followup_count == d("1")
    assert report.watch_followup_count == d("1")
    assert report.routine_followup_count == d("1")
    assert report.average_followup_priority_score == d("0.439278")
    assert report.top_followup_priority_score == d("0.837000")
    assert report.bottom_followup_priority_score == d("0.056333")
    assert report.reason_codes == (
        "urgent_specialist_calibration_followups_present",
        "watch_specialist_calibration_followups_present",
        "routine_specialist_calibration_followups_present",
    )

    rows = report.rows
    assert tuple(row.specialist_id for row in rows) == (
        "rates_lead",
        "inflation_lead",
        "labor_lead",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.followup_status for row in rows) == (
        "urgent",
        "watch",
        "routine",
    )
    assert tuple(row.followup_priority_score for row in rows) == (
        d("0.837000"),
        d("0.424500"),
        d("0.056333"),
    )
    assert tuple(row.domain_calibration_decay_score for row in rows) == (
        d("1.000000"),
        d("0.500000"),
        d("0.033333"),
    )
    assert rows[0].scheduled_followup_due_at.isoformat() == "2026-07-07T12:00:00+00:00"
    assert rows[1].scheduled_followup_due_at.isoformat() == "2026-07-09T12:00:00+00:00"
    assert rows[2].scheduled_followup_due_at.isoformat() == "2026-07-13T12:00:00+00:00"

    payload = report.payload
    assert payload["specialist_count"] == "3"
    assert payload["average_followup_priority_score"] == "0.439278"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["followup_priority_score"] == "0.837000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_empty_report_is_readonly_report_only_and_digest_backed() -> None:
    module = api()
    report = module.build_team_specialist_calibration_followup_scheduler_v2(
        (),
        config=cfg(),
        generated_at=GENERATED_AT,
    )

    assert report.schedule_status == "routine"
    assert report.specialist_count == d("0")
    assert report.average_followup_priority_score == d("0.000000")
    assert report.top_followup_priority_score == d("0.000000")
    assert report.bottom_followup_priority_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("team_specialist_calibration_followup_scheduler_empty",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = cfg()
    sample = memory()
    report = build_report(sample)
    row = report.rows[0]

    numeric_fields = {
        "recent_forecast_miss_severity_weight",
        "domain_calibration_decay_weight",
        "stale_playbook_risk_weight",
        "source_quality_failure_rate_weight",
        "unresolved_postmortem_pressure_weight",
        "upcoming_event_load_weight",
        "max_domain_calibration_age_seconds",
        "max_unresolved_postmortem_count",
        "max_upcoming_event_count",
        "urgent_priority_floor",
        "watch_priority_floor",
        "urgent_followup_due_after_seconds",
        "watch_followup_due_after_seconds",
        "routine_followup_due_after_seconds",
        "recent_forecast_miss_severity",
        "domain_calibration_age_seconds",
        "stale_playbook_risk",
        "source_quality_failure_rate",
        "unresolved_postmortem_count",
        "upcoming_event_count",
        "rank",
        "domain_calibration_decay_score",
        "unresolved_postmortem_pressure_score",
        "upcoming_event_load_score",
        "followup_priority_score",
        "scheduled_followup_lag_seconds",
        "specialist_count",
        "urgent_followup_count",
        "watch_followup_count",
        "routine_followup_count",
        "average_followup_priority_score",
        "top_followup_priority_score",
        "bottom_followup_priority_score",
    }

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in numeric_fields:
                assert type(getattr(item, field.name)) is Decimal

    with pytest.raises(TypeError):
        type(
            "UnsafeSubclass",
            (module.TeamSpecialistCalibrationFollowupMemoryV2Input,),
            {},
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "recent_forecast_miss_severity",
            _DecimalSubclass("0.500000"),
            "recent_forecast_miss_severity must be exactly Decimal",
        ),
        (
            "stale_playbook_risk",
            d("1.000001"),
            "stale_playbook_risk must be <= 1.000000",
        ),
        (
            "source_quality_failure_rate",
            d("0.5000004"),
            "source_quality_failure_rate must use six decimal places or fewer",
        ),
        (
            "domain_calibration_age_seconds",
            Decimal("NaN"),
            "domain_calibration_age_seconds must be finite",
        ),
        (
            "unresolved_postmortem_count",
            d("1.5"),
            "unresolved_postmortem_count must be an integral Decimal",
        ),
        (
            "upcoming_event_count",
            d("-1"),
            "upcoming_event_count must be >= 0.000000",
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


def test_config_validation_rejects_bad_weights_thresholds_order_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="recent_forecast_miss_severity_weight"):
        cfg(recent_forecast_miss_severity_weight=0)
    with pytest.raises(ValueError, match="scheduler weights must sum to 1.000000"):
        cfg(upcoming_event_load_weight=d("0.110000"))
    with pytest.raises(
        ValueError,
        match="watch_priority_floor must not exceed urgent_priority_floor",
    ):
        cfg(watch_priority_floor=d("0.800000"))
    with pytest.raises(
        ValueError,
        match="followup due lags must be urgent <= watch <= routine",
    ):
        cfg(watch_followup_due_after_seconds=d("3600.000000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistCalibrationFollowupSchedulerV2Config(paper_only=False)


def test_build_validation_rejects_wrong_types_duplicates_future_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_memories must be an iterable"):
        module.build_team_specialist_calibration_followup_scheduler_v2(
            object(),
            config=cfg(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="team memory items must be TeamSpecialistCalibrationFollowupMemoryV2Input",
    ):
        module.build_team_specialist_calibration_followup_scheduler_v2(
            [object()],
            config=cfg(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate team/specialist/domain"):
        build_report(memory(), memory())
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(memory(), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="readonly must be True"):
        memory(readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(
            report,
            average_followup_priority_score=d("0.400000"),
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


def test_report_revalidates_row_order_counts_reason_codes_and_digest() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by priority and rank"):
        replace(
            report,
            rows=(report.rows[1], report.rows[0], report.rows[2]),
        )
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(
            report,
            urgent_followup_count=d("2"),
        )
    with pytest.raises(ValueError, match="reason_codes must match rows"):
        replace(
            report,
            reason_codes=("team_specialist_calibration_followup_scheduler_empty",),
        )


def test_module_scope_has_no_file_database_network_or_trading_surface() -> None:
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
