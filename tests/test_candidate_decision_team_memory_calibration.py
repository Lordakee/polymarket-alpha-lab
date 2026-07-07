from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.candidate_decision_team_memory_calibration",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def joined(*parts: str) -> str:
    return "".join(parts)


def config(**overrides: object):
    calibration = api()
    values = {
        "watch_mean_brier_error_at_or_above": d("0.010000"),
        "blocked_mean_brier_error_at_or_above": d("0.250000"),
    }
    values.update(overrides)
    return calibration.CandidateDecisionTeamMemoryCalibrationConfig(**values)


def input_row(
    team_id: str,
    ref: str,
    forecast_probability: str,
    settled_outcome: str,
    *,
    redacted_candidate_ref: str | None = None,
    redacted_market_ref: str | None = None,
):
    calibration = api()
    return calibration.CandidateDecisionTeamMemoryCalibrationInputRow(
        team_id=team_id,
        redacted_candidate_ref=(
            redacted_candidate_ref
            if redacted_candidate_ref is not None
            else f"redacted_candidate_{ref}"
        ),
        redacted_market_ref=(
            redacted_market_ref
            if redacted_market_ref is not None
            else f"redacted_market_{ref}"
        ),
        forecast_probability=d(forecast_probability),
        settled_outcome=d(settled_outcome),
    )


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    calibration = api()
    return calibration.build_candidate_decision_team_memory_calibration_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)
        return
    assert type(value) is not float


def test_empty_input_returns_clear_readonly_decimal_report() -> None:
    calibration_report = report()

    assert is_dataclass(calibration_report)
    assert calibration_report.generated_at == GENERATED_AT
    assert calibration_report.config_version == (
        "candidate-decision-team-memory-calibration-v0"
    )
    assert calibration_report.input_row_count == d("0.000000")
    assert calibration_report.team_count == d("0.000000")
    assert calibration_report.blocked_team_count == d("0.000000")
    assert calibration_report.watch_team_count == d("0.000000")
    assert calibration_report.pass_team_count == d("0.000000")
    assert calibration_report.mean_brier_error == d("0.000000")
    assert calibration_report.max_team_mean_brier_error == d("0.000000")
    assert calibration_report.report_status == "pass"
    assert calibration_report.reason_codes == (
        "candidate_decision_team_memory_calibration_clear",
    )
    assert calibration_report.team_rows == ()
    assert calibration_report.paper_only is True
    assert calibration_report.report_only is True
    assert calibration_report.readonly is True


def test_team_rows_are_aggregated_and_sorted_deterministically() -> None:
    calibration_report = report(
        input_row("sports_soccer", "soccer_pass", "0.950000", "1.000000"),
        input_row("macro_rates", "rates_watch_a", "0.900000", "1.000000"),
        input_row("politics", "politics_block", "0.500000", "1.000000"),
        input_row("crypto_btc", "btc_block", "0.500000", "0.000000"),
        input_row("macro_rates", "rates_watch_b", "0.900000", "1.000000"),
    )

    assert tuple(row.team_id for row in calibration_report.team_rows) == (
        "crypto_btc",
        "politics",
        "macro_rates",
        "sports_soccer",
    )
    assert tuple(row.team_rank for row in calibration_report.team_rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
        d("4.000000"),
    )

    rows = {row.team_id: row for row in calibration_report.team_rows}
    assert rows["macro_rates"].settled_row_count == d("2.000000")
    assert rows["macro_rates"].positive_outcome_count == d("2.000000")
    assert rows["macro_rates"].negative_outcome_count == d("0.000000")
    assert rows["macro_rates"].mean_forecast_probability == d("0.900000")
    assert rows["macro_rates"].mean_outcome_value == d("1.000000")
    assert rows["macro_rates"].mean_brier_error == d("0.010000")
    assert rows["macro_rates"].max_brier_error == d("0.010000")
    assert rows["macro_rates"].calibration_status == "watch"

    assert calibration_report.input_row_count == d("5.000000")
    assert calibration_report.team_count == d("4.000000")
    assert calibration_report.blocked_team_count == d("2.000000")
    assert calibration_report.watch_team_count == d("1.000000")
    assert calibration_report.pass_team_count == d("1.000000")
    assert calibration_report.mean_brier_error == d("0.104500")
    assert calibration_report.max_team_mean_brier_error == d("0.250000")
    assert calibration_report.report_status == "blocked"
    assert calibration_report.reason_codes == (
        "candidate_decision_team_memory_calibration_blocked",
        "team_calibration_error_blocked_present",
        "team_calibration_error_watch_present",
    )


def test_decimal_normalization_and_json_payload_do_not_leak_candidate_or_market_refs() -> None:
    source_row = input_row("politics", "decimal", "0.3333334", "1")
    assert source_row.forecast_probability == d("0.333333")
    assert source_row.settled_outcome == d("1.000000")

    calibration_report = report(source_row)
    team_row = calibration_report.team_rows[0]

    assert team_row.mean_forecast_probability == d("0.333333")
    assert team_row.mean_outcome_value == d("1.000000")
    assert team_row.mean_brier_error == d("0.444445")
    assert all(
        "candidate" not in field.name and "market" not in field.name
        for field in fields(team_row)
    )

    payload = api().candidate_decision_team_memory_calibration_report_to_jsonable(
        calibration_report,
    )
    assert_no_float_values(payload)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["input_row_count"] == "1.000000"
    assert payload["team_rows"][0]["mean_brier_error"] == "0.444445"
    assert "redacted_candidate_ref" not in payload["team_rows"][0]
    assert "redacted_market_ref" not in payload["team_rows"][0]
    json.dumps(payload, sort_keys=True)
    json_payload = api().candidate_decision_team_memory_calibration_report_to_json(
        calibration_report,
    )
    assert type(json_payload) is str
    decoded_payload = json.loads(json_payload)
    assert decoded_payload == payload
    assert_no_float_values(decoded_payload)


def test_blocked_watch_and_pass_threshold_boundaries() -> None:
    calibration_report = report(
        input_row("politics", "pass", "0.950000", "1.000000"),
        input_row("crypto_btc", "watch", "0.900000", "1.000000"),
        input_row("macro_rates", "blocked", "0.500000", "1.000000"),
    )

    rows = {row.team_id: row for row in calibration_report.team_rows}
    assert rows["politics"].mean_brier_error == d("0.002500")
    assert rows["politics"].calibration_status == "pass"
    assert rows["politics"].reason_codes == ("team_calibration_error_pass",)

    assert rows["crypto_btc"].mean_brier_error == d("0.010000")
    assert rows["crypto_btc"].calibration_status == "watch"
    assert rows["crypto_btc"].reason_codes == ("team_calibration_error_watch",)

    assert rows["macro_rates"].mean_brier_error == d("0.250000")
    assert rows["macro_rates"].calibration_status == "blocked"
    assert rows["macro_rates"].reason_codes == ("team_calibration_error_blocked",)


def test_public_dataclasses_are_frozen_decimal_only_and_enforce_hard_flags() -> None:
    calibration = api()
    source_row = input_row("politics", "flags", "0.500000", "1.000000")
    calibration_report = report(source_row)

    with pytest.raises(FrozenInstanceError):
        source_row.team_id = "crypto_btc"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        calibration_report.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        calibration_report.team_rows[0].calibration_status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        calibration.CandidateDecisionTeamMemoryCalibrationConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        calibration.CandidateDecisionTeamMemoryCalibrationInputRow(
            team_id="politics",
            redacted_candidate_ref="redacted_candidate_bad_flag",
            redacted_market_ref="redacted_market_bad_flag",
            forecast_probability=d("0.500000"),
            settled_outcome=d("1.000000"),
            report_only=False,
        )

    checked_values: list[object] = []
    for item in (
        config(),
        source_row,
        calibration_report,
        calibration_report.team_rows[0],
    ):
        assert is_dataclass(item)
        for field in fields(item):
            value = getattr(item, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_probability")
                or field.name.endswith("_outcome")
                or field.name.endswith("_error")
                or field.name.endswith("_rank")
            ):
                checked_values.append(value)

    assert checked_values
    assert all(type(value) is Decimal for value in checked_values)

    object.__setattr__(calibration_report.team_rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        calibration.candidate_decision_team_memory_calibration_report_to_jsonable(
            calibration_report,
        )


def test_rejects_unsafe_values_and_invalid_public_metrics() -> None:
    calibration = api()

    with pytest.raises(ValueError, match="unsafe live surface value"):
        input_row(
            "politics",
            "unsafe",
            "0.500000",
            "1.000000",
            redacted_candidate_ref=joined("redacted_", "wal", "let"),
        )

    with pytest.raises(ValueError, match="redacted_candidate_ref must be redacted"):
        input_row(
            "politics",
            "raw",
            "0.500000",
            "1.000000",
            redacted_candidate_ref="candidate_raw_identifier",
        )

    with pytest.raises(ValueError, match="settled_outcome must be 0 or 1"):
        input_row("politics", "bad_outcome", "0.500000", "0.500000")

    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        calibration.CandidateDecisionTeamMemoryCalibrationInputRow(
            team_id="politics",
            redacted_candidate_ref="redacted_candidate_float",
            redacted_market_ref="redacted_market_float",
            forecast_probability=0.5,
            settled_outcome=d("1.000000"),
        )

    with pytest.raises(ValueError, match="blocked_mean_brier_error_at_or_above"):
        config(
            watch_mean_brier_error_at_or_above=d("0.300000"),
            blocked_mean_brier_error_at_or_above=d("0.200000"),
        )

    duplicate = input_row("politics", "duplicate", "0.500000", "1.000000")
    with pytest.raises(ValueError, match="unique"):
        report(duplicate, duplicate)


def test_jsonable_rejects_unsafe_payload_tampering_and_float_injection() -> None:
    calibration = api()
    calibration_report = report(input_row("politics", "json", "0.500000", "1.000000"))
    original_asdict = calibration.asdict
    try:
        calibration.asdict = lambda value: {  # type: ignore[method-assign]
            **original_asdict(value),
            "notes": [joined("private", "_key")],
        }
        with pytest.raises(ValueError, match="unsafe live surface value"):
            calibration.candidate_decision_team_memory_calibration_report_to_jsonable(
                calibration_report,
            )

        calibration.asdict = lambda value: {  # type: ignore[method-assign]
            **original_asdict(value),
            "mean_brier_error": 1.0,
        }
        with pytest.raises(ValueError, match="must not be a float"):
            calibration.candidate_decision_team_memory_calibration_report_to_jsonable(
                calibration_report,
            )
    finally:
        calibration.asdict = original_asdict  # type: ignore[method-assign]


def test_module_has_no_io_or_live_execution_boundary_imports() -> None:
    source = inspect.getsource(api()).lower()

    assert "float(" not in source
    assert ".total_seconds(" not in source
    assert "open(" not in source
    assert "path(" not in source
    assert "psycopg" not in source
    assert "sqlalchemy" not in source
    assert "os.environ" not in source
    assert "subprocess" not in source
    assert "argparse" not in source
    assert "click" not in source
    for fragment in (
        joined("net", "work"),
        joined("au", "th"),
        joined("wal", "let"),
        joined("acc", "ount"),
        joined("bro", "ker"),
        joined("ord", "er"),
        joined("sub", "mit"),
        joined("can", "cel"),
        joined("rep", "lace"),
        joined("sig", "n"),
        joined("ex", "change"),
        "socket",
        "requests",
        "http",
    ):
        assert fragment not in source

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    assert imported_modules <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "json",
        "typing",
        "polymarket_alpha_lab.team_paper_guard",
        "polymarket_alpha_lab.team_taxonomy",
    }
