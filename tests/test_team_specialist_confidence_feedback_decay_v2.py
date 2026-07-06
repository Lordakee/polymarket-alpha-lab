from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
MODULE_PATH = "src/polymarket_alpha_lab/team_specialist_confidence_feedback_decay_v2.py"


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module("polymarket_alpha_lab.team_specialist_confidence_feedback_decay_v2")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_TEAM_SPECIALIST_CONFIDENCE_FEEDBACK_DECAY_V2_CONFIG_VERSION,
        "feedback_decay_window_seconds": d("1209600.000000"),
        "stale_feedback_after_seconds": d("604800.000000"),
        "stale_feedback_penalty": d("0.150000"),
        "recent_calibration_window_seconds": d("172800.000000"),
        "recent_calibration_boost": d("0.100000"),
        "min_recent_calibration_score": d("0.750000"),
        "min_pass_confidence_score": d("0.700000"),
        "min_watch_confidence_score": d("0.400000"),
    }
    values.update(overrides)
    return module.TeamSpecialistConfidenceFeedbackDecayConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "team_id": "macro_rates",
        "specialist_id": "rates_specialist",
        "subject_id": "fed_path",
        "feedback_observed_at": GENERATED_AT,
        "base_confidence_score": d("0.500000"),
        "feedback_confidence_score": d("0.800000"),
        "calibration_observed_at": None,
        "calibration_score": d("0.000000"),
        "public_note": None,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.TeamSpecialistConfidenceFeedbackObservation(**values)


def public_payload_item(key: str = "safe_key", value: str = "safe value"):
    module = api()
    return module.TeamSpecialistConfidenceFeedbackPublicPayloadItem(key=key, value=value)


def report(*observations: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_confidence_feedback_decay_v2_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_confidence_feedback_decay_moves_confidence_toward_recent_feedback() -> None:
    cfg = config(
        feedback_decay_window_seconds=d("120.000000"),
        stale_feedback_after_seconds=d("600.000000"),
    )

    decay_report = report(
        observation(feedback_observed_at=GENERATED_AT - timedelta(seconds=60)),
        cfg=cfg,
    )

    row = decay_report.rows[0]
    assert row.feedback_age_seconds == d("60.000000")
    assert row.feedback_decay_multiplier == d("0.500000")
    assert row.decayed_confidence_score == d("0.650000")
    assert row.confidence_status == "watch"
    assert "confidence_feedback_decay_applied" in row.reason_codes
    assert decay_report.average_decayed_confidence_score == d("0.650000")


def test_stale_feedback_penalties_lower_confidence_and_block_weak_rows() -> None:
    cfg = config(
        feedback_decay_window_seconds=d("120.000000"),
        stale_feedback_after_seconds=d("60.000000"),
        stale_feedback_penalty=d("0.150000"),
    )

    stale_report = report(
        observation(
            feedback_observed_at=GENERATED_AT - timedelta(seconds=180),
            base_confidence_score=d("0.500000"),
            feedback_confidence_score=d("0.900000"),
        ),
        cfg=cfg,
    )

    row = stale_report.rows[0]
    assert row.feedback_decay_multiplier == d("0.000000")
    assert row.stale_feedback_penalty == d("0.150000")
    assert row.decayed_confidence_score == d("0.350000")
    assert row.confidence_status == "blocked"
    assert row.reason_codes == (
        "confidence_feedback_decay_applied",
        "stale_feedback_penalty",
        "specialist_confidence_blocked",
    )
    assert stale_report.blocked_count == d("1")
    assert stale_report.max_stale_feedback_penalty == d("0.150000")


def test_recent_calibration_boosts_confidence_when_calibration_is_fresh() -> None:
    cfg = config(
        recent_calibration_window_seconds=d("3600.000000"),
        recent_calibration_boost=d("0.100000"),
        min_recent_calibration_score=d("0.750000"),
    )

    boosted_report = report(
        observation(
            base_confidence_score=d("0.500000"),
            feedback_confidence_score=d("0.650000"),
            calibration_observed_at=GENERATED_AT - timedelta(seconds=1800),
            calibration_score=d("0.900000"),
        ),
        cfg=cfg,
    )

    row = boosted_report.rows[0]
    assert row.calibration_age_seconds == d("1800.000000")
    assert row.recent_calibration_boost == d("0.100000")
    assert row.decayed_confidence_score == d("0.750000")
    assert row.confidence_status == "pass"
    assert "recent_calibration_boost" in row.reason_codes
    assert boosted_report.report_status == "pass"
    assert boosted_report.max_recent_calibration_boost == d("0.100000")


def test_payload_serializes_decimals_as_strings_and_is_json_ready() -> None:
    module = api()
    decay_report = module.build_team_specialist_confidence_feedback_decay_v2_report(
        (
            observation(
                feedback_observed_at=GENERATED_AT - timedelta(seconds=60),
                calibration_observed_at=GENERATED_AT - timedelta(seconds=30),
                calibration_score=d("0.900000"),
            ),
        ),
        config=config(
            feedback_decay_window_seconds=d("120.000000"),
            recent_calibration_window_seconds=d("120.000000"),
        ),
        generated_at=GENERATED_AT,
        public_payload=(public_payload_item(),),
    )

    payload = decay_report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["source_row_count"] == "1"
    assert payload["average_decayed_confidence_score"] == "0.750000"
    assert payload["rows"][0]["feedback_age_seconds"] == "60.000000"
    assert payload["rows"][0]["feedback_decay_multiplier"] == "0.500000"
    assert payload["rows"][0]["recent_calibration_boost"] == "0.100000"
    assert payload["public_payload"][0]["key"] == "safe_key"
    assert payload["derived_validation_digest"] == decay_report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(decay_report)
    _assert_no_decimal_objects(payload)


def test_dataclasses_are_frozen_and_reject_subclassing_and_subclass_values() -> None:
    module = api()
    decay_report = report(observation())

    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_CONFIDENCE_FEEDBACK_DECAY_V2_CONFIG_VERSION",
        "TeamSpecialistConfidenceFeedbackDecayConfig",
        "TeamSpecialistConfidenceFeedbackObservation",
        "TeamSpecialistConfidenceFeedbackPublicPayloadItem",
        "TeamSpecialistConfidenceFeedbackDecayRow",
        "TeamSpecialistConfidenceFeedbackDecayReport",
        "build_team_specialist_confidence_feedback_decay_v2_report",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    with pytest.raises(FrozenInstanceError):
        decay_report.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.TeamSpecialistConfidenceFeedbackDecayConfig):
            pass

    with pytest.raises(ValueError, match="Decimal"):
        observation(base_confidence_score=_DecimalSubclass("0.500000"))

    with pytest.raises(ValueError, match="team_id"):
        observation(team_id=_StringSubclass("macro_rates"))


def test_hard_flags_are_enforced_on_config_observation_payload_and_report() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        public_payload_item().__class__(key="safe_key", value="safe value", readonly=False)

    decay_report = report(observation())
    with pytest.raises(ValueError, match="readonly"):
        replace(decay_report, readonly=False)


def test_derived_validation_digest_rejects_report_tampering() -> None:
    decay_report = report(observation())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(decay_report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            decay_report,
            public_payload=(public_payload_item("safe_key", "changed safe value"),),
        )


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            public_payload_item(f"{term}_key", "safe value")
        with pytest.raises(ValueError, match="unsafe public"):
            public_payload_item("safe_key", f"{term} value")
        with pytest.raises(ValueError, match="unsafe public"):
            observation(team_id=f"{term}_team")


def test_module_scope_stays_report_only_and_has_no_unsafe_surfaces() -> None:
    module = api()
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for public_name, public_value in vars(module).items():
        if not public_name.startswith("_"):
            lowered = public_name.lower()
            assert not any(term in lowered for term in unsafe_terms)
            if isinstance(public_value, type) and is_dataclass(public_value):
                for field in fields(public_value):
                    field_name = field.name.lower()
                    assert not any(term in field_name for term in unsafe_terms)

    source = Path(MODULE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "ccxt",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "supabase",
        "urllib",
        "web3",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
