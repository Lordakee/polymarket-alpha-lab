from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_learning_dashboard_report.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_learning_dashboard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    *,
    team_scorecard_ready: bool = True,
    postmortem_ready: bool = True,
    memory_update_queue_ready: bool = True,
    learning_feedback_ready: bool = True,
    operating_cycle_ready: bool = True,
    domain_risk_register_ready: bool = True,
    research_queue_ready: bool = True,
    supabase_memory_ready: bool = True,
) -> Any:
    module = api()
    return module.SpecialistTeamLearningDashboardSignal(
        team_scorecard_ready=team_scorecard_ready,
        postmortem_ready=postmortem_ready,
        memory_update_queue_ready=memory_update_queue_ready,
        learning_feedback_ready=learning_feedback_ready,
        operating_cycle_ready=operating_cycle_ready,
        domain_risk_register_ready=domain_risk_register_ready,
        research_queue_ready=research_queue_ready,
        supabase_memory_ready=supabase_memory_ready,
    )


def build_report(*signals: Any) -> Any:
    module = api()
    return module.build_specialist_team_learning_dashboard_report(signals)


def test_dashboard_report_exports_frozen_readonly_decimal_only_api() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_SPECIALIST_TEAM_LEARNING_DASHBOARD_CONFIG_VERSION",
        "SPECIALIST_TEAM_LEARNING_DASHBOARD_BANDS",
        "SpecialistTeamLearningDashboardSignal",
        "SpecialistTeamLearningDashboardRow",
        "SpecialistTeamLearningDashboardReport",
        "build_specialist_team_learning_dashboard_report",
        "specialist_team_learning_dashboard_report_payload",
        "specialist_team_learning_dashboard_report_digest",
    )
    assert module.SPECIALIST_TEAM_LEARNING_DASHBOARD_BANDS == (
        "ready",
        "attention",
        "blocked",
    )

    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    report = build_report(signal())
    assert report.config_version == "specialist-team-learning-dashboard-report-v0"
    assert report.signal_count == d("1.000000")
    assert report.ready_signal_count == d("8.000000")
    assert report.required_signal_count == d("8.000000")
    assert report.ready_ratio == d("1.000000")
    assert report.learning_dashboard_ready is True
    assert report.dashboard_band == "ready"
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert row.ready_signal_count == d("8.000000")
    assert row.required_signal_count == d("8.000000")
    assert row.ready_ratio == d("1.000000")
    assert row.learning_dashboard_ready is True
    assert row.dashboard_band == "ready"

    for value in (signal(), row, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name.endswith(("_count", "_ratio")):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.dashboard_band = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_dashboard_report_scores_attention_and_blocked_learning_states() -> None:
    report = build_report(
        signal(),
        signal(
            team_scorecard_ready=False,
            postmortem_ready=False,
            memory_update_queue_ready=False,
            learning_feedback_ready=False,
        ),
        signal(
            operating_cycle_ready=False,
            domain_risk_register_ready=False,
            research_queue_ready=False,
            supabase_memory_ready=False,
        ),
    )

    assert report.signal_count == d("3.000000")
    assert report.ready_signal_count == d("16.000000")
    assert report.required_signal_count == d("24.000000")
    assert report.ready_ratio == d("0.666667")
    assert report.learning_dashboard_ready is False
    assert report.dashboard_band == "blocked"
    assert report.blocked_reason_codes == (
        "operating_cycle_not_ready",
        "domain_risk_register_not_ready",
        "research_queue_not_ready",
        "supabase_memory_not_ready",
    )
    assert report.attention_reason_codes == (
        "team_scorecard_not_ready",
        "postmortem_not_ready",
        "memory_update_queue_not_ready",
        "learning_feedback_not_ready",
    )

    ready, attention, blocked = report.rows
    assert tuple(row.dashboard_band for row in report.rows) == (
        "ready",
        "attention",
        "blocked",
    )
    assert ready.ready_ratio == d("1.000000")
    assert ready.learning_dashboard_ready is True
    assert attention.ready_signal_count == d("4.000000")
    assert attention.ready_ratio == d("0.500000")
    assert attention.learning_dashboard_ready is False
    assert attention.attention_reason_codes == (
        "team_scorecard_not_ready",
        "postmortem_not_ready",
        "memory_update_queue_not_ready",
        "learning_feedback_not_ready",
    )
    assert blocked.ready_signal_count == d("4.000000")
    assert blocked.ready_ratio == d("0.500000")
    assert blocked.learning_dashboard_ready is False
    assert blocked.blocked_reason_codes == (
        "operating_cycle_not_ready",
        "domain_risk_register_not_ready",
        "research_queue_not_ready",
        "supabase_memory_not_ready",
    )


def test_empty_dashboard_report_is_report_only_not_operationally_ready() -> None:
    report = build_report()

    assert report.signal_count == d("0.000000")
    assert report.ready_signal_count == d("0.000000")
    assert report.required_signal_count == d("0.000000")
    assert report.ready_ratio == d("0.000000")
    assert report.learning_dashboard_ready is False
    assert report.dashboard_band == "blocked"
    assert report.blocked_reason_codes == ("learning_dashboard_no_signals",)
    assert report.attention_reason_codes == ()
    assert report.rows == ()


def test_public_payload_and_digest_are_json_safe_and_deterministic() -> None:
    module = api()
    report = build_report(
        signal(),
        signal(
            team_scorecard_ready=False,
            postmortem_ready=False,
            memory_update_queue_ready=False,
            learning_feedback_ready=False,
        ),
    )

    payload = report.public_payload
    digest = report.digest

    assert payload == module.specialist_team_learning_dashboard_report_payload(report)
    assert digest == module.specialist_team_learning_dashboard_report_digest(report)
    assert payload["ready_ratio"] == "0.750000"
    assert payload["rows"][1]["ready_signal_count"] == "4.000000"
    assert payload["rows"][1]["ready_ratio"] == "0.500000"
    assert payload["digest"] == digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    assert _unsafe_key_paths(payload) == ()

    payload_without_digest = dict(payload)
    payload_without_digest.pop("digest")
    expected_digest = hashlib.sha256(
        json.dumps(payload_without_digest, sort_keys=True, separators=(",", ":")).encode(
            "utf-8",
        ),
    ).hexdigest()
    assert digest == expected_digest
    json.dumps(payload, sort_keys=True)


def test_validation_rejects_non_bool_non_decimal_and_inconsistent_reports() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_scorecard_ready must be a bool"):
        signal(team_scorecard_ready=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="signal_count must be a Decimal"):
        replace(build_report(signal()), signal_count=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="ready_ratio must match readiness signals"):
        replace(build_report(signal()).rows[0], ready_ratio=d("0.500000"))

    with pytest.raises(ValueError, match="learning_dashboard_ready must match rows"):
        replace(build_report(signal()), learning_dashboard_ready=False)

    with pytest.raises(ValueError, match="dashboard_band must match rows"):
        replace(build_report(signal()), dashboard_band="attention")

    with pytest.raises(ValueError, match="paper_only"):
        replace(signal(), paper_only=False)

    with pytest.raises(ValueError, match="report must be a SpecialistTeamLearningDashboardReport"):
        module.specialist_team_learning_dashboard_report_payload(signal())


def test_module_source_is_readonly_report_only_paper_only_and_side_effect_free() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()

    assert "dataclass(frozen=true)" in lowered
    assert "decimal(" in lowered
    for forbidden in (
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "supabase.create_client",
        "subprocess",
        "open(",
        "read_text",
        "write_text",
        "connect(",
        "execute(",
        "insert(",
        "upsert(",
        "delete(",
        "post(",
        "put(",
        "live_trading",
        "wallet",
        "auth",
        "order",
    ):
        assert forbidden not in lowered

    module = api()
    module_source = inspect.getsource(module).lower()
    assert "create_client" not in module_source


def _float_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) is float:
        return (path or "<root>",)
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            found.extend(_float_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(found)
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(found)
    return ()


def _unsafe_key_paths(value: object, path: str = "") -> tuple[str, ...]:
    unsafe_fragments = ("auth", "wallet", "order", "trade", "token", "dsn")
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            next_path = f"{path}.{key}" if path else str(key)
            if any(fragment in str(key).lower() for fragment in unsafe_fragments):
                found.append(next_path)
            found.extend(_unsafe_key_paths(item, next_path))
        return tuple(found)
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found.extend(_unsafe_key_paths(item, f"{path}[{index}]"))
        return tuple(found)
    return ()
