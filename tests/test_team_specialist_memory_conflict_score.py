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
    / "team_specialist_memory_conflict_score.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_memory_conflict_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def memory_signal(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "team_id": "team-alpha",
        "specialist_id": "specialist-policy-alpha",
        "memory_case_family": "rate-cut-path",
        "similar_case_count": d("20"),
        "conflicting_case_count": d("1"),
        "conclusion_diversity_score": d("0.050000"),
        "contradiction_severity_score": d("0.040000"),
        "stale_resolution_ratio": d("0.020000"),
        "unresolved_conflict_ratio": d("0.030000"),
    }
    values.update(overrides)
    return module.TeamSpecialistMemoryConflictScoreInput(**values)


def score(**overrides: object) -> Any:
    module = api()
    return module.score_team_specialist_memory_conflict(
        memory_signal(**overrides),
        config=module.TeamSpecialistMemoryConflictScoreConfig(),
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


def assert_public_numeric_fields_are_decimal(value: Any) -> None:
    for field in fields(value):
        field_value = getattr(value, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_score")
            or field.name.endswith("_ratio")
            or field.name.endswith("_weight")
            or field.name.endswith("_floor")
        ):
            assert type(field_value) is Decimal


def test_stable_memory_cases_pass_conflict_score() -> None:
    report = score()

    assert is_dataclass(report)
    assert report.team_id == "team-alpha"
    assert report.specialist_id == "specialist-policy-alpha"
    assert report.memory_case_family == "rate-cut-path"
    assert report.similar_case_count == d("20.000000")
    assert report.conflicting_case_count == d("1.000000")
    assert report.conflict_case_ratio == d("0.050000")
    assert report.memory_conflict_score == d("0.043500")
    assert report.memory_conflict_status == "pass"
    assert report.report_status == "pass"
    assert report.hard_flag is False
    assert report.reason_codes == (
        "memory_conflict_pass",
        "conflict_ratio_clear",
        "conclusion_diversity_clear",
        "contradiction_severity_clear",
        "unresolved_conflict_clear",
        "resolution_recency_clear",
        "memory_depth_sufficient",
        "hard_flag_clear",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_moderate_memory_conflicts_watch_research_priority() -> None:
    report = score(
        conflicting_case_count=d("6"),
        conclusion_diversity_score=d("0.300000"),
        contradiction_severity_score=d("0.250000"),
        stale_resolution_ratio=d("0.100000"),
        unresolved_conflict_ratio=d("0.200000"),
    )

    assert report.conflict_case_ratio == d("0.300000")
    assert report.memory_conflict_score == d("0.267500")
    assert report.memory_conflict_status == "watch"
    assert report.report_status == "watch"
    assert report.hard_flag is False
    assert report.reason_codes == (
        "memory_conflict_watch",
        "conflict_ratio_watch",
        "conclusion_diversity_watch",
        "contradiction_severity_watch",
        "unresolved_conflict_watch",
        "resolution_recency_clear",
        "memory_depth_sufficient",
        "hard_flag_clear",
    )


def test_severe_memory_conflicts_block_research_use() -> None:
    report = score(
        similar_case_count=d("10"),
        conflicting_case_count=d("8"),
        conclusion_diversity_score=d("0.700000"),
        contradiction_severity_score=d("0.750000"),
        stale_resolution_ratio=d("0.700000"),
        unresolved_conflict_ratio=d("0.700000"),
    )

    assert report.conflict_case_ratio == d("0.800000")
    assert report.memory_conflict_score == d("0.747500")
    assert report.memory_conflict_status == "block"
    assert report.report_status == "block"
    assert report.hard_flag is True
    assert report.reason_codes == (
        "memory_conflict_block",
        "conflict_ratio_high",
        "conclusion_diversity_high",
        "contradiction_severity_high",
        "unresolved_conflict_high",
        "resolution_recency_stale",
        "memory_depth_sufficient",
        "hard_flag_present",
    )


def test_low_memory_depth_sets_hard_flag_without_changing_conflict_score() -> None:
    report = score(similar_case_count=d("3"), conflicting_case_count=d("0"))

    assert report.conflict_case_ratio == d("0.000000")
    assert report.memory_conflict_score == d("0.026000")
    assert report.memory_conflict_status == "pass"
    assert report.report_status == "block"
    assert report.hard_flag is True
    assert report.reason_codes == (
        "memory_conflict_pass",
        "conflict_ratio_clear",
        "conclusion_diversity_clear",
        "contradiction_severity_clear",
        "unresolved_conflict_clear",
        "resolution_recency_clear",
        "memory_depth_low",
        "hard_flag_present",
    )


def test_decimal_exact_type_validation_rejects_int_float_and_subclass_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="similar_case_count must be exactly Decimal"):
        memory_signal(similar_case_count=20)

    with pytest.raises(ValueError, match="conclusion_diversity_score must be exactly Decimal"):
        memory_signal(conclusion_diversity_score=0.05)

    with pytest.raises(ValueError, match="conflicting_case_count must be exactly Decimal"):
        memory_signal(conflicting_case_count=_DecimalSubclass("1"))

    with pytest.raises(ValueError, match="unresolved_conflict_ratio must use six decimal places or fewer"):
        memory_signal(unresolved_conflict_ratio=d("0.1234567"))

    with pytest.raises(ValueError, match="stale_resolution_ratio must be <= 1.000000"):
        memory_signal(stale_resolution_ratio=d("1.000001"))

    with pytest.raises(ValueError, match="conflicting_case_count must not exceed similar_case_count"):
        memory_signal(similar_case_count=d("4"), conflicting_case_count=d("5"))

    with pytest.raises(ValueError, match="score weights must sum to 1.000000"):
        module.TeamSpecialistMemoryConflictScoreConfig(
            conflict_ratio_weight=d("0.360000"),
        )

    with pytest.raises(ValueError, match="score watch threshold must not exceed block threshold"):
        module.TeamSpecialistMemoryConflictScoreConfig(
            score_watch_floor=d("0.700000"),
        )


def test_public_payload_rejects_leaks_and_non_public_status_words() -> None:
    module = api()
    leak = hidden_word("77616c6c6574")

    with pytest.raises(ValueError, match="unsafe public value"):
        memory_signal(team_id=f"team-{leak}")

    payload = score().payload
    assert_status_vocabulary(payload)
    payload_text = json.dumps(payload, sort_keys=True)
    for hidden in (
        "7261775f63616e6469646174655f6964",
        "6d61726b65745f6964",
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
        "706f736974696f6e",
        "706f736974696f6e5f73697a696e67",
    ):
        assert hidden_word(hidden) not in payload_text.lower()

    tampered_payload = dict(payload)
    tampered_payload[hidden_word("6d61726b65745f6964")] = "redacted"
    with pytest.raises(ValueError, match="unsafe public key"):
        module.team_specialist_memory_conflict_score_payload(tampered_payload)

    tampered_payload = dict(payload)
    tampered_payload["team_id"] = f"team-{hidden_word('7472616465')}"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.team_specialist_memory_conflict_score_payload(tampered_payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistMemoryConflictScoreConfig()
    input_signal = memory_signal()
    report = score()

    for item in (config, input_signal, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        assert_public_numeric_fields_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistMemoryConflictScoreInput(
            team_id="team-alpha",
            specialist_id="specialist-policy-alpha",
            memory_case_family="rate-cut-path",
            similar_case_count=d("20"),
            conflicting_case_count=d("1"),
            conclusion_diversity_score=d("0.050000"),
            contradiction_severity_score=d("0.040000"),
            stale_resolution_ratio=d("0.020000"),
            unresolved_conflict_ratio=d("0.030000"),
            paper_only=False,
        )


def test_payload_is_deterministic_and_json_ready() -> None:
    left = score().payload
    right = score().payload

    assert left == right
    assert left["derived_validation_digest"] == right["derived_validation_digest"]
    assert left["memory_conflict_score"] == "0.043500"
    assert_no_float_or_int_values(left)
    json.dumps(left, sort_keys=True)


def test_report_consistency_rejects_tampering() -> None:
    report = score()

    with pytest.raises(ValueError, match="report_status must match hard flag and conflict status"):
        replace(report, report_status="watch")

    with pytest.raises(ValueError, match="memory_conflict_score does not match inputs"):
        replace(report, memory_conflict_score=d("0.050000"))

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
