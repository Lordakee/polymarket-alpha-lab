from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab."
        "research_strategy_team_specialist_signal_drift_gate_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "watch_absolute_signal_drift": d("0.150000"),
        "block_absolute_signal_drift": d("0.300000"),
        "watch_rank_drift": d("3.000000"),
        "block_rank_drift": d("6.000000"),
        "min_specialist_quorum_count": d("2.000000"),
        "max_observation_age_seconds": d("86400.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchStrategyTeamSpecialistSignalDriftGateConfig(**values)


def signal_input(**overrides: object) -> Any:
    module = api()
    values = {
        "candidate_ref": "raw-candidate-alpha-secret",
        "specialist_key": "macro_specialist",
        "observed_at": GENERATED_AT - timedelta(minutes=30),
        "prior_signal_score": d("0.420000"),
        "current_signal_score": d("0.430000"),
        "prior_rank": d("4.000000"),
        "current_rank": d("5.000000"),
        "specialist_quorum_count": d("3.000000"),
        "upstream_reason_codes": (),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchStrategyTeamSpecialistSignalDriftGateInput(**values)


def report(rows: list[object] | tuple[object, ...], *, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_strategy_team_specialist_signal_drift_gate_report(
        rows,
        config=cfg,
        generated_at=GENERATED_AT,
    )


def test_report_sorts_rows_and_rolls_up_pass_watch_and_block_statuses() -> None:
    module = api()
    cfg = config()
    passed = signal_input(
        candidate_ref="raw-candidate-pass-secret",
        specialist_key="macro_specialist",
        prior_signal_score=d("0.420000"),
        current_signal_score=d("0.430000"),
        prior_rank=d("4.000000"),
        current_rank=d("5.000000"),
    )
    watched = signal_input(
        candidate_ref="raw-candidate-watch-secret",
        specialist_key="liquidity_specialist",
        prior_signal_score=d("0.200000"),
        current_signal_score=d("0.410000"),
        prior_rank=d("9.000000"),
        current_rank=d("13.000000"),
        upstream_reason_codes=("manual_recheck_requested",),
    )
    blocked = signal_input(
        candidate_ref="raw-candidate-block-secret",
        specialist_key="resolution_specialist",
        observed_at=GENERATED_AT - timedelta(hours=27),
        prior_signal_score=d("0.900000"),
        current_signal_score=d("0.520000"),
        prior_rank=d("1.000000"),
        current_rank=d("9.000000"),
        specialist_quorum_count=d("1.000000"),
    )

    drift_report = report([passed, watched, blocked], cfg=cfg)
    repeated_report = report([blocked, passed, watched], cfg=cfg)

    assert type(drift_report) is module.ResearchStrategyTeamSpecialistSignalDriftGateReport
    assert is_dataclass(drift_report)
    assert drift_report.generated_at == GENERATED_AT
    assert drift_report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_SIGNAL_DRIFT_GATE_REPORT_CONFIG_VERSION
    )
    assert drift_report.status == "block"
    assert drift_report.row_count == d("3.000000")
    assert drift_report.pass_count == d("1.000000")
    assert drift_report.watch_count == d("1.000000")
    assert drift_report.block_count == d("1.000000")
    assert drift_report.quorum_gap_count == d("1.000000")
    assert drift_report.stale_observation_count == d("1.000000")
    assert drift_report.average_absolute_signal_drift == d("0.200000")
    assert drift_report.max_absolute_signal_drift == d("0.380000")
    assert drift_report.max_rank_drift == d("8.000000")
    assert [row.status for row in drift_report.rows] == ["block", "watch", "pass"]
    assert [row.specialist_key for row in drift_report.rows] == [
        "resolution_specialist",
        "liquidity_specialist",
        "macro_specialist",
    ]
    assert drift_report.rows[0].candidate_digest.startswith("sha256:")
    assert drift_report.rows[0].absolute_signal_drift == d("0.380000")
    assert drift_report.rows[0].rank_drift == d("8.000000")
    assert drift_report.rows[0].observation_age_seconds == d("97200.000000")
    assert drift_report.rows[0].reason_codes == (
        "signal_drift_gate_block",
        "absolute_signal_drift_block",
        "rank_drift_block",
        "specialist_quorum_gap",
        "stale_signal_observation",
    )
    assert drift_report.rows[1].reason_codes == (
        "signal_drift_gate_watch",
        "absolute_signal_drift_watch",
        "rank_drift_watch",
        "upstream_manual_recheck_requested",
    )
    assert drift_report.rows[2].reason_codes == ("signal_drift_gate_pass",)
    assert drift_report.derived_validation_digest == repeated_report.derived_validation_digest
    assert len(drift_report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in drift_report.derived_validation_digest
    )
    assert drift_report.paper_only is True
    assert drift_report.report_only is True
    assert drift_report.readonly is True


def test_empty_input_uses_pass_status_and_zero_decimal_rollups() -> None:
    module = api()

    drift_report = report(())

    assert drift_report.status == "pass"
    assert drift_report.rows == ()
    assert drift_report.row_count == d("0.000000")
    assert drift_report.pass_count == d("0.000000")
    assert drift_report.watch_count == d("0.000000")
    assert drift_report.block_count == d("0.000000")
    assert drift_report.average_absolute_signal_drift == d("0.000000")
    assert drift_report.max_absolute_signal_drift == d("0.000000")
    assert drift_report.max_rank_drift == d("0.000000")
    assert drift_report.reason_code_counts == (
        module.ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount(
            reason_code="signal_drift_gate_pass",
            row_count=d("0.000000"),
        ),
    )


def test_custom_threshold_config_drives_gate_reason_codes() -> None:
    cfg = config(
        watch_absolute_signal_drift=d("0.050000"),
        block_absolute_signal_drift=d("0.100000"),
        watch_rank_drift=d("1.000000"),
        block_rank_drift=d("2.000000"),
        min_specialist_quorum_count=d("1.000000"),
        max_observation_age_seconds=d("3600.000000"),
    )

    drift_report = report(
        [
            signal_input(
                candidate_ref="raw-candidate-custom-threshold-secret",
                prior_signal_score=d("0.200000"),
                current_signal_score=d("0.320000"),
                prior_rank=d("3.000000"),
                current_rank=d("5.000000"),
                specialist_quorum_count=d("1.000000"),
            ),
        ],
        cfg=cfg,
    )

    assert drift_report.status == "block"
    assert drift_report.block_count == d("1.000000")
    assert drift_report.rows[0].absolute_signal_drift == d("0.120000")
    assert drift_report.rows[0].rank_drift == d("2.000000")
    assert drift_report.rows[0].reason_codes == (
        "signal_drift_gate_block",
        "absolute_signal_drift_block",
        "rank_drift_block",
    )


def test_payload_is_json_safe_immutable_digest_backed_and_redacted() -> None:
    module = api()
    drift_report = report(
        [
            signal_input(
                candidate_ref="candidate-private-123",
                specialist_key="macro_specialist",
                prior_signal_score=d("0.100000"),
                current_signal_score=d("0.290000"),
            ),
        ],
    )

    payload = module.research_strategy_team_specialist_signal_drift_gate_report_payload(
        drift_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["candidate_digest"].startswith("sha256:")
    assert payload["rows"][0]["absolute_signal_drift"] == "0.190000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert not _contains_float(payload)
    assert "candidate-private-123" not in encoded
    assert "raw-candidate" not in encoded
    assert "market" not in encoded.lower()
    assert "http" not in encoded.lower()
    assert "postgres" not in encoded.lower()
    assert "token" not in encoded.lower()

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["row_count"] = "9.000000"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(drift_report, derived_validation_digest="0" * 64)


def test_public_payload_validator_enforces_canonical_nested_schema_and_digest() -> None:
    module = api()
    drift_report = report(
        [
            signal_input(
                candidate_ref="candidate-private-schema-check",
                prior_signal_score=d("0.100000"),
                current_signal_score=d("0.290000"),
            ),
        ],
    )
    payload = _mutable_payload(module, drift_report)

    assert hasattr(
        module,
        "validate_research_strategy_team_specialist_signal_drift_gate_public_payload",
    )
    validator = (
        module.validate_research_strategy_team_specialist_signal_drift_gate_public_payload
    )
    assert validator(payload) is True
    assert payload["derived_validation_digest"] == _canonical_payload_digest(payload)
    assert payload["rows"][0]["derived_validation_digest"] == _canonical_payload_digest(
        payload["rows"][0],
    )

    extra_top_level = json.loads(json.dumps(payload))
    extra_top_level["unexpected"] = "value"
    with pytest.raises(ValueError, match="public payload keys"):
        validator(extra_top_level)

    missing_nested_key = json.loads(json.dumps(payload))
    del missing_nested_key["rows"][0]["rank_drift"]
    with pytest.raises(ValueError, match="row payload keys"):
        validator(missing_nested_key)

    extra_reason_count_key = json.loads(json.dumps(payload))
    extra_reason_count_key["reason_code_counts"][0]["unexpected"] = "value"
    with pytest.raises(ValueError, match="reason code count payload keys"):
        validator(extra_reason_count_key)


def test_public_payload_validator_rejects_non_decimal_values_and_semantic_tampering() -> None:
    module = api()
    validator_name = (
        "validate_research_strategy_team_specialist_signal_drift_gate_public_payload"
    )
    assert hasattr(module, validator_name)
    validator = getattr(module, validator_name)
    payload = _mutable_payload(module, report([signal_input()]))

    integer_count = json.loads(json.dumps(payload))
    integer_count["row_count"] = 1
    with pytest.raises(ValueError, match="row_count must be a Decimal string"):
        validator(integer_count)

    false_row_flag = json.loads(json.dumps(payload))
    false_row_flag["rows"][0]["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only must be True"):
        validator(false_row_flag)

    tampered_rollup = json.loads(json.dumps(payload))
    tampered_rollup["row_count"] = "2.000000"
    tampered_rollup["derived_validation_digest"] = _canonical_payload_digest(
        tampered_rollup,
    )
    with pytest.raises(ValueError, match="row_count must match rows"):
        validator(tampered_rollup)

    tampered_observation_age = json.loads(json.dumps(payload))
    tampered_observation_age["rows"][0]["observation_age_seconds"] = "0.000000"
    tampered_observation_age["rows"][0]["derived_validation_digest"] = (
        _canonical_payload_digest(tampered_observation_age["rows"][0])
    )
    tampered_observation_age["derived_validation_digest"] = _canonical_payload_digest(
        tampered_observation_age,
    )
    with pytest.raises(ValueError, match="observation_age_seconds must match"):
        validator(tampered_observation_age)


@pytest.mark.parametrize(
    "reason_code",
    (
        "recommendation_ready",
        "position_sizing_ready",
    ),
)
def test_upstream_reason_codes_reject_recommendation_and_sizing_surfaces(
    reason_code: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public text"):
        signal_input(upstream_reason_codes=(reason_code,))


def test_validation_is_strict_frozen_decimal_only_and_paper_only() -> None:
    module = api()
    row_input = signal_input()
    drift_report = report([row_input])

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_SIGNAL_DRIFT_GATE_REPORT_CONFIG_VERSION",
        "ResearchStrategyTeamSpecialistSignalDriftGateConfig",
        "ResearchStrategyTeamSpecialistSignalDriftGateInput",
        "ResearchStrategyTeamSpecialistSignalDriftGateRow",
        "ResearchStrategyTeamSpecialistSignalDriftGateReasonCodeCount",
        "ResearchStrategyTeamSpecialistSignalDriftGateReport",
        "build_research_strategy_team_specialist_signal_drift_gate_report",
        "research_strategy_team_specialist_signal_drift_gate_report_payload",
        "validate_research_strategy_team_specialist_signal_drift_gate_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    with pytest.raises(FrozenInstanceError):
        row_input.candidate_ref = "mutated"  # type: ignore[misc]
    with pytest.raises(ValueError, match="candidate_ref"):
        signal_input(candidate_ref=_StringSubclass("candidate"))
    with pytest.raises(ValueError, match="prior_signal_score"):
        signal_input(prior_signal_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="current_signal_score"):
        signal_input(current_signal_score=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="prior_rank"):
        signal_input(prior_rank=d("1.500000"))
    with pytest.raises(ValueError, match="observed_at"):
        signal_input(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_strategy_team_specialist_signal_drift_gate_report(
            [row_input],
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report([signal_input(observed_at=GENERATED_AT + timedelta(seconds=1))])
    with pytest.raises(ValueError, match="paper_only"):
        replace(row_input, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(drift_report, readonly=False)
    with pytest.raises(ValueError, match="watch_absolute_signal_drift"):
        config(watch_absolute_signal_drift=d("0.400000"))
    with pytest.raises(ValueError, match="upstream_reason_codes"):
        signal_input(upstream_reason_codes=("source_url_http_leak",))


def test_manual_rows_and_reports_validate_consistency_and_public_payload_safety() -> None:
    module = api()
    drift_report = report([signal_input()])
    row = drift_report.rows[0]

    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(row, status="watch", derived_validation_digest="")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            row,
            reason_codes=("signal_drift_gate_watch", "absolute_signal_drift_watch"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="rows"):
        module.ResearchStrategyTeamSpecialistSignalDriftGateReport(
            generated_at=drift_report.generated_at,
            config_version=drift_report.config_version,
            status=drift_report.status,
            row_count=drift_report.row_count,
            pass_count=drift_report.pass_count,
            watch_count=drift_report.watch_count,
            block_count=drift_report.block_count,
            quorum_gap_count=drift_report.quorum_gap_count,
            stale_observation_count=drift_report.stale_observation_count,
            average_absolute_signal_drift=drift_report.average_absolute_signal_drift,
            max_absolute_signal_drift=drift_report.max_absolute_signal_drift,
            max_rank_drift=drift_report.max_rank_drift,
            rows=list(reversed((row, drift_report.rows[0]))),
            reason_code_counts=drift_report.reason_code_counts,
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="public payload"):
        module.ResearchStrategyTeamSpecialistSignalDriftGateRow(
            candidate_digest="sha256:" + "1" * 64,
            specialist_key="market_slug_leak",
            observed_at=GENERATED_AT,
            observation_age_seconds=d("0.000000"),
            prior_signal_score=d("0.100000"),
            current_signal_score=d("0.100000"),
            absolute_signal_drift=d("0.000000"),
            prior_rank=d("1.000000"),
            current_rank=d("1.000000"),
            rank_drift=d("0.000000"),
            specialist_quorum_count=d("2.000000"),
            status="pass",
            reason_codes=("signal_drift_gate_pass",),
        )


def test_manual_row_reason_codes_are_canonicalized_before_digesting() -> None:
    module = api()
    row_values = {
        "candidate_digest": "sha256:" + "1" * 64,
        "specialist_key": "macro_specialist",
        "observed_at": GENERATED_AT,
        "observation_age_seconds": d("0.000000"),
        "prior_signal_score": d("0.100000"),
        "current_signal_score": d("0.290000"),
        "absolute_signal_drift": d("0.190000"),
        "prior_rank": d("1.000000"),
        "current_rank": d("4.000000"),
        "rank_drift": d("3.000000"),
        "specialist_quorum_count": d("2.000000"),
        "status": "watch",
    }

    canonical_row = module.ResearchStrategyTeamSpecialistSignalDriftGateRow(
        **row_values,
        reason_codes=(
            "signal_drift_gate_watch",
            "absolute_signal_drift_watch",
            "rank_drift_watch",
        ),
    )
    reordered_row = module.ResearchStrategyTeamSpecialistSignalDriftGateRow(
        **row_values,
        reason_codes=(
            "signal_drift_gate_watch",
            "rank_drift_watch",
            "absolute_signal_drift_watch",
        ),
    )

    assert reordered_row.reason_codes == canonical_row.reason_codes
    assert reordered_row.derived_validation_digest == canonical_row.derived_validation_digest


def test_source_file_exposes_no_live_storage_or_trading_capability_surface() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_team_specialist_signal_drift_gate_report.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    banned_fragments = (
        "network",
        "socket",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "auth",
        "wallet",
        "account",
        "broker",
        "trade",
        "trading",
        "order",
        "database",
        "db",
        "dsn",
        "token",
        "sizing",
        "recommendation",
        "execute",
        "execution",
        "live",
        "persist",
        "storage",
        "supabase",
        "postgres",
        "psycopg",
    )
    banned_import_roots = {
        "aiohttp",
        "asyncpg",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "supabase",
        "urllib",
    }
    banned_call_names = {"compile", "eval", "exec", "open", "__import__"}
    banned_call_attributes = {
        "commit",
        "connect",
        "delete",
        "execute",
        "post",
        "put",
        "request",
        "rollback",
        "send",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(
                alias.name.partition(".")[0] not in banned_import_roots
                for alias in node.names
            )
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.partition(".")[0] not in banned_import_roots
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in banned_fragments)
        if isinstance(node, ast.arg):
            lowered = node.arg.lower()
            assert not any(fragment in lowered for fragment in banned_fragments)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_call_names
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in banned_call_attributes


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False


def _mutable_payload(module: Any, drift_report: object) -> dict[str, Any]:
    frozen_payload = (
        module.research_strategy_team_specialist_signal_drift_gate_report_payload(
            drift_report,
        )
    )
    return json.loads(json.dumps(frozen_payload))


def _canonical_payload_digest(payload: dict[str, Any]) -> str:
    value = dict(payload)
    value.pop("derived_validation_digest")
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
