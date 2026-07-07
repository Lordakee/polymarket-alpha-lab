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


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_category_playbook_reuse_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_category_playbook_reuse_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def context(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "event_id": "event_macro_cpi_july",
        "category_id": "macro_rates",
        "event_archetype": "cpi_surprise",
        "required_source_families": (
            "official_release",
            "market_price",
            "expert_analysis",
        ),
        "resolution_rule_id": "official_bls_release_rule",
    }
    values.update(overrides)
    return module.TeamSpecialistCategoryPlaybookReuseGateV2Context(**values)


def playbook(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "team_id": "macro_rates_team",
        "specialist_id": "macro_calibration_lead",
        "playbook_id": "macro_cpi_reuse_playbook",
        "category_id": "macro_rates",
        "event_archetypes": ("cpi_surprise", "fed_meeting"),
        "calibration_quality_score": d("0.900000"),
        "outcome_sample_size": d("24"),
        "source_family_ids": (
            "official_release",
            "market_price",
            "expert_analysis",
        ),
        "resolution_rule_ids": ("official_bls_release_rule",),
        "updated_at": GENERATED_AT - timedelta(days=5),
    }
    values.update(overrides)
    return module.TeamSpecialistCategoryPlaybookReuseGateV2Playbook(**values)


def build_report(**overrides: object) -> Any:
    module = api()
    values = {
        "event_context": overrides.pop("event_context", context()),
        "category_playbook": overrides.pop("category_playbook", playbook()),
        "generated_at": overrides.pop("generated_at", GENERATED_AT),
        "config": overrides.pop("config", None),
    }
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    return module.build_team_specialist_category_playbook_reuse_gate_v2(**values)


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
    if value is None or type(value) is bool:
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


def test_builds_reuse_watch_and_skip_gate_reports_with_decimal_payloads() -> None:
    reuse_report = build_report()
    watch_report = build_report(
        category_playbook=playbook(
            playbook_id="macro_cpi_watch_playbook",
            calibration_quality_score=d("0.700000"),
            outcome_sample_size=d("12"),
            source_family_ids=("official_release", "market_price"),
            updated_at=GENERATED_AT - timedelta(days=45),
        ),
    )
    skip_report = build_report(
        category_playbook=playbook(
            playbook_id="macro_cpi_skip_playbook",
            event_archetypes=("fed_meeting",),
        ),
    )

    assert reuse_report.gate_status == "reuse"
    assert reuse_report.event_archetype_match_score == d("1.000000")
    assert reuse_report.calibration_quality_score == d("0.900000")
    assert reuse_report.outcome_sample_size == d("24")
    assert reuse_report.outcome_sample_size_score == d("1.000000")
    assert reuse_report.source_family_match_score == d("1.000000")
    assert reuse_report.required_source_family_count == d("3")
    assert reuse_report.matched_source_family_count == d("3")
    assert reuse_report.matched_source_families == (
        "expert_analysis",
        "market_price",
        "official_release",
    )
    assert reuse_report.resolution_rule_match_score == d("1.000000")
    assert reuse_report.recency_age_days == d("5.000000")
    assert reuse_report.recency_score == d("0.944444")
    assert reuse_report.reuse_score == d("0.971667")
    assert reuse_report.reason_codes == (
        "team_specialist_category_playbook_reuse_event_archetype_match",
        "team_specialist_category_playbook_reuse_calibration_strong",
        "team_specialist_category_playbook_reuse_outcome_sample_full",
        "team_specialist_category_playbook_reuse_source_family_match",
        "team_specialist_category_playbook_reuse_resolution_rule_match",
        "team_specialist_category_playbook_reuse_recent",
        "team_specialist_category_playbook_reuse_reuse",
    )

    assert watch_report.gate_status == "watch"
    assert watch_report.outcome_sample_size_score == d("0.600000")
    assert watch_report.source_family_match_score == d("0.666667")
    assert watch_report.recency_score == d("0.500000")
    assert watch_report.reuse_score == d("0.755000")
    assert watch_report.reason_codes == (
        "team_specialist_category_playbook_reuse_event_archetype_match",
        "team_specialist_category_playbook_reuse_calibration_watch",
        "team_specialist_category_playbook_reuse_outcome_sample_watch",
        "team_specialist_category_playbook_reuse_source_family_partial",
        "team_specialist_category_playbook_reuse_resolution_rule_match",
        "team_specialist_category_playbook_reuse_recency_watch",
        "team_specialist_category_playbook_reuse_watch",
    )

    assert skip_report.gate_status == "skip"
    assert skip_report.event_archetype_match_score == d("0.000000")
    assert "team_specialist_category_playbook_reuse_event_archetype_gap" in (
        skip_report.reason_codes
    )
    assert skip_report.reason_codes[-1] == (
        "team_specialist_category_playbook_reuse_skip"
    )

    payload = api().team_specialist_category_playbook_reuse_gate_v2_payload(
        reuse_report,
    )
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["outcome_sample_size"] == "24"
    assert payload["reuse_score"] == "0.971667"
    assert payload["gate_status"] == "reuse"
    assert payload["derived_validation_digest"] == reuse_report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(reuse_report.derived_validation_digest) == 64
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)


def test_source_family_input_order_does_not_change_digest_or_payload() -> None:
    left = build_report(
        event_context=context(
            required_source_families=(
                "official_release",
                "market_price",
                "expert_analysis",
            ),
        ),
        category_playbook=playbook(
            source_family_ids=(
                "official_release",
                "market_price",
                "expert_analysis",
            ),
        ),
    )
    right = build_report(
        event_context=context(
            required_source_families=(
                "expert_analysis",
                "official_release",
                "market_price",
            ),
        ),
        category_playbook=playbook(
            source_family_ids=(
                "market_price",
                "expert_analysis",
                "official_release",
            ),
        ),
    )

    assert left.matched_source_families == right.matched_source_families
    assert left.payload == right.payload
    assert left.derived_validation_digest == right.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_hard_flagged_and_final() -> None:
    module = api()
    config = module.TeamSpecialistCategoryPlaybookReuseGateV2Config()
    event_context = context()
    sample_playbook = playbook()
    report = build_report(event_context=event_context, category_playbook=sample_playbook)

    for item in (config, event_context, sample_playbook, report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.TeamSpecialistCategoryPlaybookReuseGateV2Config):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeContext(module.TeamSpecialistCategoryPlaybookReuseGateV2Context):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafePlaybook(module.TeamSpecialistCategoryPlaybookReuseGateV2Playbook):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.TeamSpecialistCategoryPlaybookReuseGateV2Report):
            pass


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "calibration_quality_score",
            _DecimalSubclass("0.900000"),
            "calibration_quality_score must be exactly Decimal",
        ),
        (
            "calibration_quality_score",
            d("1.000001"),
            "calibration_quality_score must be <= 1.000000",
        ),
        (
            "calibration_quality_score",
            d("0.9000004"),
            "calibration_quality_score must use six decimal places or fewer",
        ),
        (
            "outcome_sample_size",
            d("1.5"),
            "outcome_sample_size must be an integral Decimal",
        ),
        (
            "outcome_sample_size",
            Decimal("NaN"),
            "outcome_sample_size must be finite",
        ),
    ),
)
def test_playbook_validation_rejects_bad_decimal_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        playbook(**{field_name: bad_value})


def test_build_and_config_validation_rejects_bad_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="reuse gate weights must sum to 1.000000"):
        module.TeamSpecialistCategoryPlaybookReuseGateV2Config(
            recency_weight=d("0.100000"),
        )
    with pytest.raises(ValueError, match="watch_score_floor must not exceed reuse_score_floor"):
        module.TeamSpecialistCategoryPlaybookReuseGateV2Config(
            watch_score_floor=d("0.850000"),
        )
    with pytest.raises(ValueError, match="min_watch_calibration_quality"):
        module.TeamSpecialistCategoryPlaybookReuseGateV2Config(
            min_watch_calibration_quality=d("0.850000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistCategoryPlaybookReuseGateV2Config(paper_only=False)
    with pytest.raises(ValueError, match="required_source_families must not be empty"):
        context(required_source_families=())
    with pytest.raises(ValueError, match="required_source_families must be unique"):
        context(required_source_families=("official_release", "official_release"))
    with pytest.raises(
        ValueError,
        match="event_context must be TeamSpecialistCategoryPlaybookReuseGateV2Context",
    ):
        module.build_team_specialist_category_playbook_reuse_gate_v2(
            event_context=object(),
            category_playbook=playbook(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="category_playbook must be TeamSpecialistCategoryPlaybookReuseGateV2Playbook",
    ):
        module.build_team_specialist_category_playbook_reuse_gate_v2(
            event_context=context(),
            category_playbook=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="category_id must match event_context"):
        build_report(category_playbook=playbook(category_id="policy_rates"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="updated_at must be on or before generated_at"):
        build_report(
            category_playbook=playbook(updated_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        playbook(readonly=False)
    with pytest.raises(ValueError, match="report must be"):
        module.team_specialist_category_playbook_reuse_gate_v2_payload(object())


def test_digest_tampering_and_reason_consistency_are_rejected() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, reuse_score=d("0.900000"))
    with pytest.raises(ValueError, match="gate_status reason"):
        replace(
            report,
            reason_codes=tuple(
                reason
                for reason in report.reason_codes
                if reason != "team_specialist_category_playbook_reuse_reuse"
            ),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="matched_source_family_count"):
        replace(
            report,
            matched_source_family_count=d("2"),
            matched_source_families=report.matched_source_families,
            derived_validation_digest="",
        )


def test_rejects_unsafe_public_values_and_payload_numeric_downgrades() -> None:
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
        module.team_specialist_category_playbook_reuse_gate_v2_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "wallet_id": "x"},
        )
    with pytest.raises(ValueError, match="payload numeric values"):
        module.team_specialist_category_playbook_reuse_gate_v2_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "score": 0.1},
        )


def test_static_module_surface_has_no_io_network_auth_wallet_db_or_trading_surface() -> None:
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
        "open",
        "order",
        "persist",
        "place_order",
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

    module = api()
    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_CATEGORY_PLAYBOOK_REUSE_GATE_V2_CONFIG_VERSION",
        "TeamSpecialistCategoryPlaybookReuseGateV2Config",
        "TeamSpecialistCategoryPlaybookReuseGateV2Context",
        "TeamSpecialistCategoryPlaybookReuseGateV2Playbook",
        "TeamSpecialistCategoryPlaybookReuseGateV2Report",
        "build_team_specialist_category_playbook_reuse_gate_v2",
        "team_specialist_category_playbook_reuse_gate_v2_payload",
    )
