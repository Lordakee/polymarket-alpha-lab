from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass
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
    / "team_specialist_recent_error_pattern_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_recent_error_pattern_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "team-specialist-recent-error-pattern-gate-v2-test",
        "recent_window_seconds": d("2592000.000000"),
        "watch_recent_pattern_count": d("2"),
        "blocked_recent_pattern_count": d("3"),
        "watch_brier_like_error": d("0.200000"),
        "blocked_brier_like_error": d("0.300000"),
        "watch_miss_count": d("2"),
        "blocked_miss_count": d("3"),
        "watch_contradiction_mishandled_count": d("1"),
        "blocked_contradiction_mishandled_count": d("2"),
        "watch_source_family_weakness": d("0.500000"),
        "blocked_source_family_weakness": d("0.700000"),
        "watch_resolution_lag_seconds": d("172800.000000"),
        "blocked_resolution_lag_seconds": d("604800.000000"),
    }
    values.update(overrides)
    return module.TeamSpecialistRecentErrorPatternGateV2Config(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "error_id": "recent-error-base",
        "team_id": "macro_rates",
        "category_id": "finance.macro.rates",
        "specialist_id": "rates-event-specialist",
        "event_archetype": "macro-cpi-print",
        "evaluated_at": GENERATED_AT - timedelta(days=1),
        "brier_like_error": d("0.150000"),
        "miss_count": d("0"),
        "contradiction_mishandled_count": d("0"),
        "source_family_weakness_score": d("0.200000"),
        "resolution_lag_seconds": d("86400.000000"),
    }
    values.update(overrides)
    return module.TeamSpecialistRecentErrorPatternGateV2Observation(**values)


def build_report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_recent_error_pattern_gate_v2(
        rows,
        config=cfg if cfg is not None else config(),
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


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def recent_error_pattern_observations():
    return (
        observation(
            error_id="err-block-1",
            evaluated_at=GENERATED_AT - timedelta(days=2),
            brier_like_error=d("0.320000"),
            miss_count=d("1"),
            contradiction_mishandled_count=d("1"),
            source_family_weakness_score=d("0.740000"),
            resolution_lag_seconds=d("691200.000000"),
        ),
        observation(
            error_id="err-block-2",
            evaluated_at=GENERATED_AT - timedelta(days=5),
            brier_like_error=d("0.280000"),
            miss_count=d("1"),
            contradiction_mishandled_count=d("1"),
            source_family_weakness_score=d("0.710000"),
            resolution_lag_seconds=d("604800.000000"),
        ),
        observation(
            error_id="err-block-3",
            evaluated_at=GENERATED_AT - timedelta(days=7),
            brier_like_error=d("0.260000"),
            miss_count=d("1"),
            source_family_weakness_score=d("0.690000"),
            resolution_lag_seconds=d("172800.000000"),
        ),
        observation(
            error_id="err-watch-1",
            event_archetype="macro-fed-guidance",
            evaluated_at=GENERATED_AT - timedelta(days=1),
            brier_like_error=d("0.210000"),
            miss_count=d("1"),
            contradiction_mishandled_count=d("1"),
            source_family_weakness_score=d("0.550000"),
            resolution_lag_seconds=d("259200.000000"),
        ),
        observation(
            error_id="err-watch-2",
            event_archetype="macro-fed-guidance",
            evaluated_at=GENERATED_AT - timedelta(days=3),
            brier_like_error=d("0.190000"),
            miss_count=d("1"),
            source_family_weakness_score=d("0.450000"),
            resolution_lag_seconds=d("172800.000000"),
        ),
        observation(
            error_id="err-clear-1",
            event_archetype="macro-auction-demand",
        ),
    )


def test_recent_repeated_error_patterns_block_watch_and_summarize_by_archetype() -> None:
    report = build_report(*reversed(recent_error_pattern_observations()))

    assert report.gate_status == "blocked"
    assert report.source_error_count == d("6")
    assert report.row_count == d("3")
    assert report.team_count == d("1")
    assert report.specialist_count == d("1")
    assert report.event_archetype_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.blocked_count == d("1")
    assert report.repeated_pattern_count == d("2")
    assert report.brier_like_error_pattern_count == d("2")
    assert report.miss_count_pattern_count == d("2")
    assert report.contradiction_mishandling_pattern_count == d("2")
    assert report.source_family_weakness_pattern_count == d("2")
    assert report.resolution_lag_pattern_count == d("2")
    assert report.reason_codes == (
        "blocked_recent_error_patterns_present",
        "watch_recent_error_patterns_present",
        "brier_like_error_patterns_present",
        "miss_count_patterns_present",
        "contradiction_mishandling_patterns_present",
        "source_family_weakness_patterns_present",
        "resolution_lag_patterns_present",
    )

    blocked, watched, passed = report.rows
    assert (blocked.event_archetype, blocked.gate_status) == (
        "macro-cpi-print",
        "blocked",
    )
    assert blocked.source_error_count == d("3")
    assert blocked.recent_error_count == d("3")
    assert blocked.latest_recent_error_age_seconds == d("172800.000000")
    assert blocked.oldest_recent_error_age_seconds == d("604800.000000")
    assert blocked.max_brier_like_error == d("0.320000")
    assert blocked.total_miss_count == d("3")
    assert blocked.contradiction_mishandled_count == d("2")
    assert blocked.max_source_family_weakness_score == d("0.740000")
    assert blocked.max_resolution_lag_seconds == d("691200.000000")
    assert blocked.contributing_error_ids == (
        "err-block-1",
        "err-block-2",
        "err-block-3",
    )
    assert blocked.reason_codes == (
        "recent_repeated_error_pattern",
        "brier_like_error_blocked",
        "miss_count_blocked",
        "contradiction_mishandling_blocked",
        "source_family_weakness_blocked",
        "resolution_lag_blocked",
    )

    assert (watched.event_archetype, watched.gate_status) == (
        "macro-fed-guidance",
        "watch",
    )
    assert watched.recent_error_count == d("2")
    assert watched.max_brier_like_error == d("0.210000")
    assert watched.total_miss_count == d("2")
    assert watched.contradiction_mishandled_count == d("1")
    assert watched.max_source_family_weakness_score == d("0.550000")
    assert watched.max_resolution_lag_seconds == d("259200.000000")
    assert watched.reason_codes == (
        "recent_repeated_error_pattern",
        "brier_like_error_watch",
        "miss_count_watch",
        "contradiction_mishandling_watch",
        "source_family_weakness_watch",
        "resolution_lag_watch",
    )

    assert (passed.event_archetype, passed.gate_status) == (
        "macro-auction-demand",
        "pass",
    )
    assert passed.recent_error_count == d("1")
    assert passed.reason_codes == ("recent_error_pattern_clear",)


def test_old_repeated_errors_outside_recency_window_pass_even_when_severe() -> None:
    report = build_report(
        observation(
            error_id="old-1",
            evaluated_at=GENERATED_AT - timedelta(days=45),
            brier_like_error=d("0.900000"),
            miss_count=d("1"),
            contradiction_mishandled_count=d("1"),
            source_family_weakness_score=d("0.900000"),
            resolution_lag_seconds=d("900000.000000"),
        ),
        observation(
            error_id="old-2",
            evaluated_at=GENERATED_AT - timedelta(days=46),
            brier_like_error=d("0.900000"),
            miss_count=d("1"),
            contradiction_mishandled_count=d("1"),
            source_family_weakness_score=d("0.900000"),
            resolution_lag_seconds=d("900000.000000"),
        ),
        observation(
            error_id="old-3",
            evaluated_at=GENERATED_AT - timedelta(days=47),
            brier_like_error=d("0.900000"),
            miss_count=d("1"),
            contradiction_mishandled_count=d("1"),
            source_family_weakness_score=d("0.900000"),
            resolution_lag_seconds=d("900000.000000"),
        ),
    )

    assert report.gate_status == "pass"
    assert report.reason_codes == ("recent_error_patterns_clear",)
    row = report.rows[0]
    assert row.gate_status == "pass"
    assert row.source_error_count == d("3")
    assert row.recent_error_count == d("0")
    assert row.latest_recent_error_age_seconds is None
    assert row.oldest_recent_error_age_seconds is None
    assert row.max_brier_like_error == d("0.000000")
    assert row.total_miss_count == d("0")
    assert row.reason_codes == ("recent_error_pattern_clear",)


def test_empty_evidence_report_is_deterministic_pass() -> None:
    report = build_report()

    assert report.gate_status == "pass"
    assert report.source_error_count == d("0")
    assert report.row_count == d("0")
    assert report.reason_codes == ("no_recent_error_patterns_supplied",)
    assert isinstance(report.derived_validation_digest, str)
    assert len(report.derived_validation_digest) == 64


def test_payload_serializes_decimals_as_strings_and_validates_digest() -> None:
    module = api()
    report = build_report(*recent_error_pattern_observations())

    payload = module.team_specialist_recent_error_pattern_gate_v2_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["source_error_count"] == "6"
    assert payload["rows"][0]["max_brier_like_error"] == "0.320000"
    assert payload["rows"][0]["latest_recent_error_age_seconds"] == "172800.000000"
    assert payload["rows"][0]["contributing_error_ids"] == [
        "err-block-1",
        "err-block-2",
        "err-block-3",
    ]
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_float_values(payload)

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_recent_error_pattern_gate_v2_payload(tampered)


def test_digest_and_row_order_are_stable_for_input_order() -> None:
    rows = recent_error_pattern_observations()
    forward = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert tuple(row.event_archetype for row in forward.rows) == tuple(
        row.event_archetype for row in reversed_report.rows
    )
    assert forward.derived_validation_digest == reversed_report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_observation = observation()
    sample_report = build_report(sample_observation)
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_observation, sample_row, sample_report):
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="Decimal"):
        observation(miss_count=1)
    with pytest.raises(ValueError, match="timezone-aware"):
        build_report(observation(), generated_at=datetime(2026, 7, 7, 12, 0))


def test_report_rejects_digest_and_row_order_tampering() -> None:
    module = api()
    report = build_report(*recent_error_pattern_observations())
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["derived_validation_digest"] = "f" * 64

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.TeamSpecialistRecentErrorPatternGateV2Report(**values)

    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["rows"] = tuple(reversed(values["rows"]))
    values["derived_validation_digest"] = ""
    with pytest.raises(ValueError, match="sorted"):
        module.TeamSpecialistRecentErrorPatternGateV2Report(**values)


def test_rejects_duplicate_error_ids_and_unsafe_public_surface() -> None:
    module = api()

    with pytest.raises(ValueError, match="duplicate error_id"):
        build_report(
            observation(error_id="duplicate-error"),
            observation(error_id="duplicate-error", event_archetype="macro-fed-guidance"),
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        observation(error_id="live-error")
    with pytest.raises(ValueError, match="unsafe public value"):
        observation(event_archetype="sell-pressure")

    for payload in (
        {"paper_only": True, "report_only": True, "readonly": True, "wallet_id": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "buy signal"},
        {"paper_only": True, "report_only": True, "readonly": True, "network": "mainnet"},
        {"paper_only": True, "report_only": False, "readonly": True},
    ):
        with pytest.raises(ValueError):
            module.team_specialist_recent_error_pattern_gate_v2_payload(payload)


def test_module_scope_has_no_network_auth_wallet_order_db_or_trading_surface() -> None:
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
        "database",
        "db",
        "http",
        "network",
        "order",
        "persist",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "order",
        "persist",
        "rollback",
        "sell",
        "send",
        "sign",
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
