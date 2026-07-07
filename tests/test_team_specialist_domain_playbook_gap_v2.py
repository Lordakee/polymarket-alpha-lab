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
    / "team_specialist_domain_playbook_gap_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_domain_playbook_gap_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def memory(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "team_id": "alpha_specialists",
        "specialist_id": "calibration_lead",
        "domain_id": "macro_rates",
        "memory_key": "macro-rate-cycle",
        "observed_at": GENERATED_AT - timedelta(hours=4),
        "last_lesson_reviewed_at": GENERATED_AT - timedelta(days=5),
        "baseline_calibration_score": d("0.900000"),
        "current_calibration_score": d("0.880000"),
        "stale_lesson_count": d("0"),
        "required_source_family_count": d("3"),
        "observed_source_family_count": d("3"),
        "contradiction_miss_count": d("0"),
        "resolution_rule_error_count": d("0"),
        "recent_forecast_error": d("0.050000"),
        "upcoming_event_count": d("1"),
        "public_memory_refs": ("memory:macro-rate-cycle",),
    }
    values.update(overrides)
    return module.TeamSpecialistDomainPlaybookGapV2Memory(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    config = overrides.pop("config", None)
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items:
        items = (
            memory(),
            memory(
                team_id="beta_specialists",
                specialist_id="source_lead",
                domain_id="macro_rates",
                memory_key="macro-labor-cycle",
                observed_at=GENERATED_AT - timedelta(hours=8),
                last_lesson_reviewed_at=GENERATED_AT - timedelta(days=20),
                baseline_calibration_score=d("0.850000"),
                current_calibration_score=d("0.700000"),
                stale_lesson_count=d("2"),
                required_source_family_count=d("4"),
                observed_source_family_count=d("2"),
                contradiction_miss_count=d("1"),
                resolution_rule_error_count=d("0"),
                recent_forecast_error=d("0.180000"),
                upcoming_event_count=d("4"),
                public_memory_refs=("memory:macro-labor-cycle",),
            ),
            memory(
                team_id="gamma_specialists",
                specialist_id="resolution_lead",
                domain_id="crypto_btc",
                memory_key="crypto-etf-resolution",
                observed_at=GENERATED_AT - timedelta(hours=2),
                last_lesson_reviewed_at=GENERATED_AT - timedelta(days=40),
                baseline_calibration_score=d("0.900000"),
                current_calibration_score=d("0.400000"),
                stale_lesson_count=d("5"),
                required_source_family_count=d("5"),
                observed_source_family_count=d("1"),
                contradiction_miss_count=d("3"),
                resolution_rule_error_count=d("2"),
                recent_forecast_error=d("0.450000"),
                upcoming_event_count=d("8"),
                public_memory_refs=("memory:crypto-etf-resolution",),
            ),
        )
    return module.build_team_specialist_domain_playbook_gap_v2_report(
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


def test_builds_decimal_gap_report_and_public_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.gap_status == "blocked"
    assert report.team_count == d("3")
    assert report.domain_count == d("2")
    assert report.memory_count == d("3")
    assert report.pass_memory_count == d("1")
    assert report.watch_memory_count == d("1")
    assert report.blocked_memory_count == d("1")
    assert report.average_playbook_gap_score == d("0.373167")
    assert report.max_playbook_gap_score == d("0.815000")
    assert report.reason_codes == (
        "team_specialist_domain_playbook_gap_blocked_rows",
        "team_specialist_domain_playbook_gap_watch_rows",
    )

    assert tuple(row.team_id for row in report.rows) == (
        "gamma_specialists",
        "beta_specialists",
        "alpha_specialists",
    )
    assert tuple(row.rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.gap_status for row in report.rows) == ("blocked", "watch", "pass")
    assert tuple(row.playbook_gap_score for row in report.rows) == (
        d("0.815000"),
        d("0.283000"),
        d("0.021500"),
    )
    assert report.rows[0].reason_codes == (
        "team_specialist_domain_playbook_calibration_decay",
        "team_specialist_domain_playbook_stale_lessons",
        "team_specialist_domain_playbook_missing_source_families",
        "team_specialist_domain_playbook_contradiction_misses",
        "team_specialist_domain_playbook_resolution_rule_errors",
        "team_specialist_domain_playbook_recent_forecast_error",
        "team_specialist_domain_playbook_upcoming_event_load",
    )

    payload = report.payload
    assert payload["team_count"] == "3"
    assert payload["average_playbook_gap_score"] == "0.373167"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["playbook_gap_score"] == "0.815000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_empty_report_is_digest_backed_and_report_only() -> None:
    module = api()
    report = module.build_team_specialist_domain_playbook_gap_v2_report(
        (),
        generated_at=GENERATED_AT,
    )

    assert report.gap_status == "blocked"
    assert report.team_count == d("0")
    assert report.domain_count == d("0")
    assert report.memory_count == d("0")
    assert report.average_playbook_gap_score == d("0.000000")
    assert report.max_playbook_gap_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("team_specialist_domain_playbook_gap_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistDomainPlaybookGapV2Config()
    sample = memory()
    report = build_report(sample)
    row = report.rows[0]

    decimal_fields = {
        "calibration_decay_weight",
        "stale_lesson_weight",
        "missing_source_family_weight",
        "contradiction_miss_weight",
        "resolution_rule_error_weight",
        "recent_forecast_error_weight",
        "upcoming_event_load_weight",
        "max_stale_lesson_count",
        "max_contradiction_miss_count",
        "max_resolution_rule_error_count",
        "max_upcoming_event_count",
        "pass_gap_score_floor",
        "watch_gap_score_floor",
        "baseline_calibration_score",
        "current_calibration_score",
        "stale_lesson_count",
        "required_source_family_count",
        "observed_source_family_count",
        "contradiction_miss_count",
        "resolution_rule_error_count",
        "recent_forecast_error",
        "upcoming_event_count",
        "rank",
        "calibration_decay_gap",
        "stale_lesson_gap",
        "missing_source_family_count",
        "missing_source_family_gap",
        "contradiction_miss_gap",
        "resolution_rule_error_gap",
        "recent_forecast_error_gap",
        "upcoming_event_load_gap",
        "playbook_gap_score",
        "team_count",
        "domain_count",
        "memory_count",
        "pass_memory_count",
        "watch_memory_count",
        "blocked_memory_count",
        "average_playbook_gap_score",
        "max_playbook_gap_score",
    }

    for item in (config, sample, row, report):
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
            "current_calibration_score",
            _DecimalSubclass("0.900000"),
            "current_calibration_score must be exactly Decimal",
        ),
        (
            "baseline_calibration_score",
            d("1.000001"),
            "baseline_calibration_score must be <= 1.000000",
        ),
        (
            "recent_forecast_error",
            d("0.8500004"),
            "recent_forecast_error must use six decimal places or fewer",
        ),
        (
            "upcoming_event_count",
            Decimal("NaN"),
            "upcoming_event_count must be finite",
        ),
        (
            "stale_lesson_count",
            d("1.5"),
            "stale_lesson_count must be an integral Decimal",
        ),
        (
            "contradiction_miss_count",
            d("-1"),
            "contradiction_miss_count must be >= 0.000000",
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

    with pytest.raises(ValueError, match="calibration_decay_weight must be exactly Decimal"):
        module.TeamSpecialistDomainPlaybookGapV2Config(
            calibration_decay_weight=0,
        )
    with pytest.raises(ValueError, match="gap weights must sum to 1.000000"):
        module.TeamSpecialistDomainPlaybookGapV2Config(
            upcoming_event_load_weight=d("0.090000"),
        )
    with pytest.raises(ValueError, match="pass_gap_score_floor must not exceed watch_gap_score_floor"):
        module.TeamSpecialistDomainPlaybookGapV2Config(
            pass_gap_score_floor=d("0.700000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistDomainPlaybookGapV2Config(paper_only=False)


def test_build_validation_rejects_wrong_types_dates_and_disabled_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_memories must be an iterable"):
        module.build_team_specialist_domain_playbook_gap_v2_report(
            object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="team memory items must be TeamSpecialistDomainPlaybookGapV2Memory",
    ):
        module.build_team_specialist_domain_playbook_gap_v2_report(
            [object()],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_domain_playbook_gap_v2_report(
            [memory()],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="observed_at must be on or before generated_at"):
        module.build_team_specialist_domain_playbook_gap_v2_report(
            [memory(observed_at=GENERATED_AT + timedelta(seconds=1))],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        memory(readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_playbook_gap_score=d("0.400000"))
    with pytest.raises(ValueError, match="derived_validation_digest must match row fields"):
        replace(report.rows[0], playbook_gap_score=d("0.800000"))


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


def test_report_revalidates_row_order_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by gap score and rank"):
        replace(
            report,
            rows=(report.rows[1], report.rows[0], report.rows[2]),
        )
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(report, pass_memory_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match gap_status"):
        replace(
            report,
            reason_codes=("team_specialist_domain_playbook_gap_passed",),
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
        "DEFAULT_TEAM_SPECIALIST_DOMAIN_PLAYBOOK_GAP_V2_CONFIG_VERSION",
        "TeamSpecialistDomainPlaybookGapV2Config",
        "TeamSpecialistDomainPlaybookGapV2Memory",
        "TeamSpecialistDomainPlaybookGapV2Report",
        "TeamSpecialistDomainPlaybookGapV2Row",
        "build_team_specialist_domain_playbook_gap_v2_report",
        "team_specialist_domain_playbook_gap_v2_payload",
    )
