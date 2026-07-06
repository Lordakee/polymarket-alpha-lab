from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_memory_playbook_decay_alert_v10.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_memory_playbook_decay_alert_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def playbook_signal(**overrides: object):
    module = api()
    values = {
        "specialist_id": "macro-rates-specialist",
        "playbook_id": "fomc-dot-plot-playbook",
        "domain_id": "macro-rates",
        "days_since_update": d("5.000000"),
        "recent_forecast_error": d("0.020000"),
        "source_failure_rate": d("0.000000"),
        "domain_drift": d("0.040000"),
        "reuse_frequency": d("10.000000"),
    }
    values.update(overrides)
    return module.StrategyTeamMemoryPlaybookDecayAlertV10Input(**values)


def evaluate(**overrides: object):
    module = api()
    return module.evaluate_strategy_team_memory_playbook_decay_alert_v10(
        playbook_signal(**overrides),
    )


def assert_no_float_or_integer_values(value: Any) -> None:
    if type(value) is float:
        raise AssertionError(f"unexpected float value {value!r}")
    if type(value) is int:
        raise AssertionError(f"unexpected integer value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_integer_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_integer_values(item)


def test_critical_decay_alert_combines_stale_error_failure_drift_and_low_reuse() -> None:
    result = evaluate(
        specialist_id="election-resolution-specialist",
        playbook_id="late-ballot-resolution-playbook",
        domain_id="politics-elections",
        days_since_update=d("90.000000"),
        recent_forecast_error=d("0.300000"),
        source_failure_rate=d("0.400000"),
        domain_drift=d("0.600000"),
        reuse_frequency=d("0.000000"),
    )

    assert is_dataclass(result)
    assert result.specialist_id == "election-resolution-specialist"
    assert result.playbook_id == "late-ballot-resolution-playbook"
    assert result.domain_id == "politics-elections"
    assert result.decay_score == d("80.000000")
    assert result.alert_status == "critical"
    assert result.recommended_actions == (
        "escalate_specialist_playbook_rebuild",
        "recalibrate_forecast_examples",
        "repair_source_checklist",
        "refresh_domain_assumptions",
        "seed_specialist_reuse_trial",
    )
    assert result.reason_codes == (
        "playbook_update_stale",
        "forecast_error_high",
        "source_failure_high",
        "domain_drift_high",
        "playbook_reuse_low",
        "decay_alert_status_critical",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_refresh_and_healthy_statuses_are_distinct_and_decimal_scored() -> None:
    refresh = evaluate(
        days_since_update=d("50.000000"),
        recent_forecast_error=d("0.120000"),
        source_failure_rate=d("0.100000"),
        domain_drift=d("0.150000"),
        reuse_frequency=d("3.000000"),
    )
    healthy = evaluate()

    assert refresh.decay_score == d("48.250000")
    assert refresh.alert_status == "refresh"
    assert refresh.recommended_actions == (
        "queue_playbook_refresh",
        "recalibrate_forecast_examples",
        "repair_source_checklist",
        "refresh_domain_assumptions",
    )
    assert refresh.reason_codes == (
        "playbook_update_stale",
        "forecast_error_moderate",
        "source_failure_elevated",
        "domain_drift_moderate",
        "playbook_reuse_moderate",
        "decay_alert_status_refresh",
    )

    assert healthy.decay_score == d("6.587879")
    assert healthy.alert_status == "healthy"
    assert healthy.recommended_actions == ("continue_playbook_monitoring",)
    assert healthy.reason_codes == (
        "playbook_update_recent",
        "forecast_error_low",
        "source_failure_low",
        "domain_drift_low",
        "playbook_reuse_active",
        "decay_alert_status_healthy",
    )


def test_payload_uses_decimal_strings_and_readonly_flags_without_numeric_leakage() -> None:
    module = api()
    result = evaluate(
        days_since_update=d("50.000000"),
        recent_forecast_error=d("0.120000"),
        source_failure_rate=d("0.100000"),
        domain_drift=d("0.150000"),
        reuse_frequency=d("3.000000"),
    )

    payload = module.strategy_team_memory_playbook_decay_alert_v10_payload(result)
    encoded = json.dumps(payload, sort_keys=True)

    assert result.payload == payload
    assert (
        payload["config_version"]
        == "strategy-team-memory-playbook-decay-alert-v10"
    )
    assert payload["days_since_update"] == "50.000000"
    assert payload["recent_forecast_error"] == "0.120000"
    assert payload["source_failure_rate"] == "0.100000"
    assert payload["domain_drift"] == "0.150000"
    assert payload["reuse_frequency"] == "3.000000"
    assert payload["decay_score"] == "48.250000"
    assert payload["alert_status"] == "refresh"
    assert type(result.validation_digest) is str
    assert len(result.validation_digest) == 64
    assert payload["validation_digest"] == result.validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"48.250000"' in encoded
    assert_no_float_or_integer_values(payload)


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    numeric_fields = {
        "days_since_update",
        "recent_forecast_error",
        "source_failure_rate",
        "domain_drift",
        "reuse_frequency",
        "decay_score",
    }

    for cls in (
        module.StrategyTeamMemoryPlaybookDecayAlertV10Input,
        module.StrategyTeamMemoryPlaybookDecayAlertV10Result,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal


def test_validation_rejects_bad_types_ranges_flags_and_derived_results() -> None:
    module = api()

    with pytest.raises(ValueError, match="specialist_id"):
        playbook_signal(specialist_id=_StringSubclass("macro-rates-specialist"))

    with pytest.raises(ValueError, match="days_since_update must be a Decimal"):
        playbook_signal(days_since_update=5)

    with pytest.raises(ValueError, match="recent_forecast_error must be a Decimal"):
        playbook_signal(recent_forecast_error=0.02)

    with pytest.raises(ValueError, match="source_failure_rate must be a Decimal"):
        playbook_signal(source_failure_rate=_DecimalSubclass("0.100000"))

    with pytest.raises(ValueError, match="days_since_update must be nonnegative"):
        playbook_signal(days_since_update=d("-0.000001"))

    with pytest.raises(ValueError, match="domain_drift must be between 0 and 1"):
        playbook_signal(domain_drift=d("1.000001"))

    with pytest.raises(ValueError, match="reuse_frequency must be finite"):
        playbook_signal(reuse_frequency=Decimal("NaN"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(playbook_signal(), paper_only=False)

    result = evaluate()
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="decay_score must match"):
        replace(result, decay_score=d("7.000000"))

    with pytest.raises(ValueError, match="recommended_actions must be unique"):
        replace(
            result,
            recommended_actions=(
                "continue_playbook_monitoring",
                "continue_playbook_monitoring",
            ),
        )

    with pytest.raises(FrozenInstanceError):
        result.alert_status = "critical"  # type: ignore[misc]

    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)

    with pytest.raises(
        ValueError,
        match="result must be a StrategyTeamMemoryPlaybookDecayAlertV10Result",
    ):
        module.strategy_team_memory_playbook_decay_alert_v10_payload(
            playbook_signal(),
        )


def test_public_strings_reject_secret_like_values_before_payload_leakage() -> None:
    with pytest.raises(ValueError, match="must not contain sensitive material"):
        playbook_signal(playbook_id="api_key=secret")


def test_public_payload_revalidates_mutated_derived_payload_and_unsafe_fields() -> None:
    module = api()

    tampered_payload_result = evaluate()
    tampered_payload = dict(tampered_payload_result.payload)
    tampered_payload["decay_score"] = "0.000000"
    object.__setattr__(tampered_payload_result, "payload", tampered_payload)
    with pytest.raises(ValueError, match="payload must match|validation_digest"):
        module.strategy_team_memory_playbook_decay_alert_v10_payload(
            tampered_payload_result,
        )

    unsafe_payload_result = evaluate()
    unsafe_payload = dict(unsafe_payload_result.payload)
    unsafe_payload["wallet_address"] = "redacted"
    object.__setattr__(unsafe_payload_result, "payload", unsafe_payload)
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_team_memory_playbook_decay_alert_v10_payload(
            unsafe_payload_result,
        )


def test_module_scope_is_readonly_report_only_and_free_of_external_surfaces() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "broker",
        "live trading",
        "order placement",
        "submit",
        "cancel",
        "network",
        "database",
        "durable",
        "store",
        "open(",
        "write(",
        "read_text",
        "pathlib",
        "requests",
        "http",
        "urllib",
        "socket",
        "postgres",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "execute(",
        "subprocess",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
