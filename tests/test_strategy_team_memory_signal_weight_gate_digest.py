from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_memory_signal_weight_gate_digest.py"
)
GENERATED_AT = datetime(2026, 7, 4, 16, 30, tzinfo=timezone(timedelta(hours=2)))
OBSERVED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_memory_signal_weight_gate_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    digest = api()
    values: dict[str, object] = {
        "config_version": "strategy-team-memory-signal-weight-gate-digest-test-v0",
        "min_pass_team_memory_signal_weight": d("0.700000"),
        "min_watch_team_memory_signal_weight": d("0.450000"),
        "min_component_pass_score": d("0.650000"),
        "min_component_watch_score": d("0.400000"),
        "max_pass_disagreement_pressure": d("0.250000"),
        "max_watch_disagreement_pressure": d("0.500000"),
    }
    values.update(overrides)
    return digest.StrategyTeamMemorySignalWeightGateDigestConfig(**values)


def signal(**overrides: object):
    digest = api()
    values: dict[str, object] = {
        "candidate_id": "candidate_macro",
        "team_id": "macro_team",
        "category_id": "macro_rates",
        "observed_at": OBSERVED_AT,
        "forecast_calibration_memory_score": d("0.900000"),
        "resolution_accuracy_memory_score": d("0.850000"),
        "source_reliability_score": d("0.900000"),
        "information_velocity_score": d("0.800000"),
        "disagreement_pressure": d("0.100000"),
        "conflict_arbitration_score": d("0.850000"),
        "workload_capacity_score": d("0.800000"),
        "public_reference": "paper://candidate/macro?token=paper-secret",
    }
    values.update(overrides)
    return digest.StrategyTeamMemorySignalWeightGateInput(**values)


def report(*signals: object, cfg=None, generated_at: datetime = GENERATED_AT):
    digest = api()
    return digest.build_strategy_team_memory_signal_weight_gate_digest(
        signals,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_public_numbers(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload contains public numeric {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numbers(item)


def test_digest_combines_team_memory_signals_into_candidate_team_weights() -> None:
    digest_report = report(
        signal(
            candidate_id="candidate_sports",
            team_id="sports_team",
            category_id="sports_soccer",
            forecast_calibration_memory_score=d("0.300000"),
            resolution_accuracy_memory_score=d("0.500000"),
            source_reliability_score=d("0.500000"),
            information_velocity_score=d("0.200000"),
            disagreement_pressure=d("0.700000"),
            conflict_arbitration_score=d("0.300000"),
            workload_capacity_score=d("0.300000"),
        ),
        signal(
            candidate_id="candidate_macro",
            team_id="macro_team",
            category_id="macro_rates",
            forecast_calibration_memory_score=d("0.900000"),
            resolution_accuracy_memory_score=d("0.850000"),
            source_reliability_score=d("0.900000"),
            information_velocity_score=d("0.800000"),
            disagreement_pressure=d("0.100000"),
            conflict_arbitration_score=d("0.850000"),
            workload_capacity_score=d("0.800000"),
        ),
        signal(
            candidate_id="candidate_crypto",
            team_id="crypto_team",
            category_id="crypto_btc",
            forecast_calibration_memory_score=d("0.650000"),
            resolution_accuracy_memory_score=d("0.600000"),
            source_reliability_score=d("0.700000"),
            information_velocity_score=d("0.500000"),
            disagreement_pressure=d("0.300000"),
            conflict_arbitration_score=d("0.650000"),
            workload_capacity_score=d("0.700000"),
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == datetime(2026, 7, 4, 14, 30, tzinfo=UTC)
    assert digest_report.config_version == (
        "strategy-team-memory-signal-weight-gate-digest-test-v0"
    )
    assert digest_report.input_count == d("3")
    assert digest_report.candidate_team_count == d("3")
    assert digest_report.team_count == d("3")
    assert digest_report.pass_count == d("1")
    assert digest_report.watch_count == d("1")
    assert digest_report.blocked_count == d("1")
    assert digest_report.average_team_memory_signal_weight == d("0.626667")
    assert digest_report.status == "blocked"
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple((row.team_id, row.candidate_id) for row in digest_report.rows) == (
        ("sports_team", "candidate_sports"),
        ("crypto_team", "candidate_crypto"),
        ("macro_team", "candidate_macro"),
    )
    assert tuple(row.status for row in digest_report.rows) == (
        "blocked",
        "watch",
        "pass",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.disagreement_alignment_score == d("0.300000")
    assert blocked.team_memory_signal_weight == d("0.370000")
    assert blocked.reason_codes == (
        "team_memory_signal_weight_blocked",
        "team_memory_signal_weight_below_watch",
        "forecast_calibration_memory_below_watch",
        "resolution_accuracy_memory_below_pass",
        "source_reliability_below_pass",
        "information_velocity_below_watch",
        "disagreement_pressure_above_watch",
        "conflict_arbitration_below_watch",
        "workload_capacity_below_watch",
    )

    assert watched.disagreement_alignment_score == d("0.700000")
    assert watched.team_memory_signal_weight == d("0.645000")
    assert watched.reason_codes == (
        "team_memory_signal_weight_watch",
        "team_memory_signal_weight_below_pass",
        "resolution_accuracy_memory_below_pass",
        "information_velocity_below_pass",
        "disagreement_pressure_above_pass",
    )

    assert passed.disagreement_alignment_score == d("0.900000")
    assert passed.team_memory_signal_weight == d("0.865000")
    assert passed.reason_codes == ("team_memory_signal_weight_pass",)

    assert digest_report.reason_codes == (
        "team_memory_signal_weight_blocked",
        "team_memory_signal_weight_watch",
        "team_memory_signal_weight_pass",
        "team_memory_signal_weight_below_watch",
        "team_memory_signal_weight_below_pass",
        "forecast_calibration_memory_below_watch",
        "resolution_accuracy_memory_below_pass",
        "source_reliability_below_pass",
        "information_velocity_below_watch",
        "information_velocity_below_pass",
        "disagreement_pressure_above_watch",
        "disagreement_pressure_above_pass",
        "conflict_arbitration_below_watch",
        "workload_capacity_below_watch",
    )
    assert tuple(count.reason_code for count in digest_report.reason_code_counts)[:3] == (
        "resolution_accuracy_memory_below_pass",
        "team_memory_signal_weight_blocked",
        "team_memory_signal_weight_watch",
    )
    assert digest_report.reason_code_counts[0].count == d("2")


def test_empty_digest_blocks_candidate_evaluation_with_zero_decimals() -> None:
    empty = report()

    assert empty.input_count == d("0")
    assert empty.candidate_team_count == d("0")
    assert empty.team_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.average_team_memory_signal_weight == ZERO
    assert empty.status == "blocked"
    assert empty.reason_codes == ("strategy_team_memory_signal_weight_gate_digest_empty",)
    assert empty.reason_code_counts == (
        api().StrategyTeamMemorySignalWeightGateReasonCodeCount(
            reason_code="strategy_team_memory_signal_weight_gate_digest_empty",
            count=d("1"),
        ),
    )
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_payload_uses_decimal_strings_utc_datetimes_flags_and_redacted_refs() -> None:
    digest = api()
    digest_report = report(
        signal(
            public_reference="https://example.invalid/private?api_key=paper-secret",
            observed_at=datetime(2026, 7, 4, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
        ),
    )

    assert "paper-secret" not in repr(digest_report).lower()
    payload = digest.strategy_team_memory_signal_weight_gate_digest_payload(digest_report)
    rendered = repr(payload).lower()
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T14:30:00+00:00"
    assert payload["input_count"] == "1"
    assert payload["average_team_memory_signal_weight"] == "0.865000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["rows"][0]["team_memory_signal_weight"] == "0.865000"
    assert payload["rows"][0]["redacted_public_reference"].startswith("reference_")
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numbers(payload)

    for forbidden in ("https", "api_key", "paper-secret", "private"):
        assert forbidden not in rendered


def test_validation_rejects_float_int_subclasses_bad_time_flags_and_duplicates() -> None:
    digest = api()

    with pytest.raises(ValueError, match="config"):
        digest.build_strategy_team_memory_signal_weight_gate_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="forecast_calibration_memory_score must be a Decimal"):
        signal(forecast_calibration_memory_score=1)
    with pytest.raises(ValueError, match="resolution_accuracy_memory_score must be a Decimal"):
        signal(resolution_accuracy_memory_score=0.6)
    with pytest.raises(ValueError, match="source_reliability_score must be a Decimal"):
        signal(source_reliability_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(
            signal(candidate_id="candidate_time"),
            generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(signal(), readonly=False)
    with pytest.raises(ValueError, match="signals must be unique"):
        report(signal(), signal())

    digest_report = report(signal())
    with pytest.raises(ValueError, match="input_count"):
        replace(digest_report, input_count=1)
    with pytest.raises(ValueError, match="rows"):
        replace(digest_report, rows=(object(),))
    with pytest.raises(FrozenInstanceError):
        digest_report.rows[0].status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError) as exc_info:
        signal(team_id="team_secret_marker")
    assert "team_secret_marker" not in str(exc_info.value)


def test_public_dataclasses_are_frozen_and_numeric_fields_are_decimal_only() -> None:
    digest = api()
    digest_report = report(signal())
    values = (
        config(),
        signal(candidate_id="candidate_numeric"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    )
    numeric_suffixes = (
        "_count",
        "_score",
        "_pressure",
        "_weight",
    )

    assert digest.__all__ == (
        "DEFAULT_STRATEGY_TEAM_MEMORY_SIGNAL_WEIGHT_GATE_DIGEST_CONFIG_VERSION",
        "StrategyTeamMemorySignalWeightGateDigestConfig",
        "StrategyTeamMemorySignalWeightGateInput",
        "StrategyTeamMemorySignalWeightGateReasonCodeCount",
        "StrategyTeamMemorySignalWeightGateReport",
        "StrategyTeamMemorySignalWeightGateRow",
        "build_strategy_team_memory_signal_weight_gate_digest",
        "strategy_team_memory_signal_weight_gate_digest_payload",
    )
    for exported_name in digest.__all__:
        exported = getattr(digest, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            if field.name.endswith(numeric_suffixes):
                assert type(getattr(value, field.name)) is Decimal

    for dataclass_type in (
        digest.StrategyTeamMemorySignalWeightGateDigestConfig,
        digest.StrategyTeamMemorySignalWeightGateInput,
        digest.StrategyTeamMemorySignalWeightGateRow,
        digest.StrategyTeamMemorySignalWeightGateReasonCodeCount,
        digest.StrategyTeamMemorySignalWeightGateReport,
    ):
        hints = get_type_hints(dataclass_type)
        for field in fields(dataclass_type):
            if field.name.endswith(numeric_suffixes):
                assert hints[field.name] is Decimal


def test_module_scope_stays_pure_report_only_and_without_forbidden_surface_terms() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "cancel",
        "replace",
        "network",
        "database",
        "durable",
        "store",
        "market_slug",
        "question",
        "payload_json",
        "private_key",
        "api_key",
        "secret",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "psycopg",
        "sqlite",
        "supabase",
        "execute(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }
    forbidden_call_names = {
        "__import__",
        "connect",
        "eval",
        "exec",
        "executemany",
        "float",
        "open",
        "print",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
