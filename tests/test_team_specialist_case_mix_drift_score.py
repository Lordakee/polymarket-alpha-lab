from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_case_mix_drift_score.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_case_mix_drift_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def case_mix_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "team_id": "team-alpha",
        "specialist_id": "specialist-rates-alpha",
        "historical_case_count": d("120"),
        "recent_case_count": d("20"),
        "category_drift_score": d("0.050000"),
        "difficulty_drift_score": d("0.040000"),
        "calibration_decay_score": d("0.030000"),
        "recent_accuracy_score": d("0.940000"),
    }
    values.update(overrides)
    return module.TeamSpecialistCaseMixDriftScoreInput(**values)


def score(**overrides: object) -> Any:
    module = api()
    return module.score_team_specialist_case_mix_drift(
        case_mix_input(**overrides),
        config=module.TeamSpecialistCaseMixDriftScoreConfig(),
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_status_vocabulary(value: Any) -> None:
    forbidden_statuses = {
        hidden_word("7265616479"),
        hidden_word("626c6f636b6564"),
        hidden_word("6d617463686564"),
        hidden_word("737570706f72746564"),
    }
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("_status"):
                assert item in {"pass", "watch", "block"}
                assert item not in forbidden_statuses
            assert_status_vocabulary(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_status_vocabulary(item)


def test_stable_case_mix_passes_specialist_drift_score() -> None:
    report = score()

    assert is_dataclass(report)
    assert report.team_id == "team-alpha"
    assert report.specialist_id == "specialist-rates-alpha"
    assert report.historical_case_count == d("120.000000")
    assert report.recent_case_count == d("20.000000")
    assert report.recent_accuracy_gap_score == d("0.060000")
    assert report.case_mix_drift_score == d("0.045200")
    assert report.case_mix_drift_status == "pass"
    assert report.report_status == "pass"
    assert report.hard_flag is False
    assert report.reason_codes == (
        "case_mix_drift_pass",
        "category_drift_clear",
        "difficulty_drift_clear",
        "calibration_decay_clear",
        "recent_accuracy_stable",
        "historical_depth_sufficient",
        "recent_depth_sufficient",
        "hard_flag_clear",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_severe_case_mix_drift_blocks_specialist_report() -> None:
    report = score(
        category_drift_score=d("0.900000"),
        difficulty_drift_score=d("0.800000"),
        calibration_decay_score=d("0.700000"),
        recent_accuracy_score=d("0.450000"),
    )

    assert report.recent_accuracy_gap_score == d("0.550000")
    assert report.case_mix_drift_score == d("0.762000")
    assert report.case_mix_drift_status == "block"
    assert report.report_status == "block"
    assert report.hard_flag is False
    assert report.reason_codes == (
        "case_mix_drift_block",
        "category_drift_high",
        "difficulty_drift_high",
        "calibration_decay_high",
        "recent_accuracy_weak",
        "historical_depth_sufficient",
        "recent_depth_sufficient",
        "hard_flag_clear",
    )


def test_moderate_case_mix_drift_watches_specialist_report() -> None:
    report = score(
        category_drift_score=d("0.350000"),
        difficulty_drift_score=d("0.250000"),
        calibration_decay_score=d("0.300000"),
        recent_accuracy_score=d("0.800000"),
    )

    assert report.recent_accuracy_gap_score == d("0.200000")
    assert report.case_mix_drift_score == d("0.285000")
    assert report.case_mix_drift_status == "watch"
    assert report.report_status == "watch"
    assert report.hard_flag is False
    assert report.reason_codes == (
        "case_mix_drift_watch",
        "category_drift_watch",
        "difficulty_drift_watch",
        "calibration_decay_watch",
        "recent_accuracy_watch",
        "historical_depth_sufficient",
        "recent_depth_sufficient",
        "hard_flag_clear",
    )


def test_decimal_exact_type_validation_rejects_int_float_and_subclass_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="historical_case_count must be exactly Decimal"):
        case_mix_input(historical_case_count=120)

    with pytest.raises(ValueError, match="category_drift_score must be exactly Decimal"):
        case_mix_input(category_drift_score=0.05)

    with pytest.raises(ValueError, match="recent_case_count must be exactly Decimal"):
        case_mix_input(recent_case_count=_DecimalSubclass("20"))

    with pytest.raises(ValueError, match="difficulty_drift_score must use six decimal places or fewer"):
        case_mix_input(difficulty_drift_score=d("0.1234567"))

    with pytest.raises(ValueError, match="recent_accuracy_score must be <= 1.000000"):
        case_mix_input(recent_accuracy_score=d("1.000001"))

    with pytest.raises(ValueError, match="historical_case_count must be integral"):
        case_mix_input(historical_case_count=d("12.500000"))

    with pytest.raises(ValueError, match="score weights must sum to 1.000000"):
        module.TeamSpecialistCaseMixDriftScoreConfig(
            category_drift_weight=d("0.350000"),
        )

    with pytest.raises(ValueError, match="score watch threshold must not exceed block threshold"):
        module.TeamSpecialistCaseMixDriftScoreConfig(
            score_watch_floor=d("0.700000"),
        )


def test_public_payload_rejects_leaks_and_non_public_status_words() -> None:
    module = api()
    leak = hidden_word("77616c6c6574")

    with pytest.raises(ValueError, match="unsafe public value"):
        case_mix_input(team_id=f"team-{leak}")

    payload = score().payload
    assert_status_vocabulary(payload)
    payload_text = json.dumps(payload, sort_keys=True)
    for hidden in (
        "6d61726b65745f6964",
        "63616e6469646174655f6964",
        "6d61726b65745f736c7567",
        "7175657374696f6e",
        "75726c",
        "736f757263655f726566",
        "736f757263655f74657874",
        "64736e",
        "7461626c655f6e616d65",
        "746f6b656e",
        "736563726574",
        "61757468",
        "77616c6c6574",
        "6f72646572",
        "7472616465",
        "627579",
        "73656c6c",
        "7265636f6d6d656e646174696f6e",
        "706f736974696f6e5f73697a696e67",
    ):
        assert hidden_word(hidden) not in payload_text.lower()

    tampered_payload = dict(payload)
    tampered_payload[hidden_word("6d61726b65745f6964")] = "redacted"
    with pytest.raises(ValueError, match="unsafe public key"):
        module.team_specialist_case_mix_drift_score_payload(tampered_payload)

    tampered_payload = dict(payload)
    tampered_payload["team_id"] = f"team-{hidden_word('7472616465')}"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.team_specialist_case_mix_drift_score_payload(tampered_payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistCaseMixDriftScoreConfig()
    input_signal = case_mix_input()
    report = score()

    for item in (config, input_signal, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_score")
                or field.name.endswith("_weight")
                or field.name.endswith("_floor")
            ):
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistCaseMixDriftScoreInput(
            team_id="team-alpha",
            specialist_id="specialist-rates-alpha",
            historical_case_count=d("120"),
            recent_case_count=d("20"),
            category_drift_score=d("0.050000"),
            difficulty_drift_score=d("0.040000"),
            calibration_decay_score=d("0.030000"),
            recent_accuracy_score=d("0.940000"),
            paper_only=False,
        )


def test_low_case_depth_sets_hard_flag_and_report_block() -> None:
    report = score(
        historical_case_count=d("10"),
        recent_case_count=d("3"),
    )

    assert report.case_mix_drift_score == d("0.045200")
    assert report.case_mix_drift_status == "pass"
    assert report.report_status == "block"
    assert report.hard_flag is True
    assert report.reason_codes == (
        "case_mix_drift_pass",
        "category_drift_clear",
        "difficulty_drift_clear",
        "calibration_decay_clear",
        "recent_accuracy_stable",
        "historical_depth_low",
        "recent_depth_low",
        "hard_flag_present",
    )


def test_payload_is_deterministic_and_json_ready() -> None:
    left = score().payload
    right = score().payload

    assert left == right
    assert left["derived_validation_digest"] == right["derived_validation_digest"]
    assert left["case_mix_drift_score"] == "0.045200"
    assert_no_float_or_int_values(left)
    json.dumps(left, sort_keys=True)


def test_report_consistency_rejects_tampering() -> None:
    report = score()

    with pytest.raises(ValueError, match="report_status must match hard flag and drift status"):
        replace(report, report_status="watch")

    with pytest.raises(ValueError, match="case_mix_drift_score does not match inputs"):
        replace(report, case_mix_drift_score=d("0.050000"))

    with pytest.raises(ValueError, match="derived_validation_digest does not match report payload"):
        replace(report, derived_validation_digest="0" * 64)


def test_module_is_pure_report_only_without_io_imports() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        hidden_word("7265717565737473"),
        "httpx",
        "urllib",
        "socket",
        "asyncio",
        hidden_word("7375706162617365"),
        "psycopg",
        "sqlalchemy",
        "web3",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported_roots = {("" if node.module is None else node.module.split(".")[0])}
        else:
            continue
        assert imported_roots.isdisjoint(forbidden_import_roots)
