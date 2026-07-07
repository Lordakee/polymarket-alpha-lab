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
    / "team_specialist_domain_rotation_score.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_domain_rotation_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def domain_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "team_id": "team-alpha",
        "specialist_id": "specialist-rates-alpha",
        "primary_domain_id": "macro-rates",
        "covered_domain_count": d("6"),
        "primary_domain_case_count": d("18"),
        "total_case_count": d("60"),
        "rotation_gap_count": d("1"),
        "undercovered_domain_count": d("1"),
        "recent_rotation_count": d("4"),
        "target_rotation_count": d("4"),
        "category_coverage_score": d("0.900000"),
    }
    values.update(overrides)
    return module.TeamSpecialistDomainRotationScoreInput(**values)


def score(**overrides: object) -> Any:
    module = api()
    return module.score_team_specialist_domain_rotation(
        domain_input(**overrides),
        config=module.TeamSpecialistDomainRotationScoreConfig(),
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
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("_status"):
                assert item in {"pass", "watch", "block"}
            assert_status_vocabulary(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_status_vocabulary(item)


def test_balanced_domain_rotation_passes_report() -> None:
    report = score()

    assert is_dataclass(report)
    assert report.team_id == "team-alpha"
    assert report.specialist_id == "specialist-rates-alpha"
    assert report.covered_domain_count == d("6.000000")
    assert report.primary_domain_concentration_score == d("0.300000")
    assert report.rotation_gap_score == d("0.166667")
    assert report.undercovered_domain_score == d("0.166667")
    assert report.rotation_completion_score == d("1.000000")
    assert report.domain_rotation_risk_score == d("0.160000")
    assert report.domain_rotation_status == "pass"
    assert report.report_status == "pass"
    assert report.hard_flag is False
    assert report.reason_codes == (
        "domain_rotation_pass",
        "primary_domain_concentration_clear",
        "rotation_gap_clear",
        "undercovered_domain_clear",
        "rotation_completion_met",
        "category_coverage_strong",
        "domain_depth_sufficient",
        "case_depth_sufficient",
        "hard_flag_clear",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_moderate_domain_concentration_watches_report() -> None:
    report = score(
        primary_domain_case_count=d("42"),
        rotation_gap_count=d("2"),
        undercovered_domain_count=d("2"),
        recent_rotation_count=d("2"),
        category_coverage_score=d("0.700000"),
    )

    assert report.primary_domain_concentration_score == d("0.700000")
    assert report.rotation_gap_score == d("0.333333")
    assert report.undercovered_domain_score == d("0.333333")
    assert report.rotation_completion_score == d("0.500000")
    assert report.domain_rotation_risk_score == d("0.470000")
    assert report.domain_rotation_status == "watch"
    assert report.report_status == "watch"
    assert report.hard_flag is False
    assert report.reason_codes == (
        "domain_rotation_watch",
        "primary_domain_concentration_watch",
        "rotation_gap_watch",
        "undercovered_domain_watch",
        "rotation_completion_partial",
        "category_coverage_watch",
        "domain_depth_sufficient",
        "case_depth_sufficient",
        "hard_flag_clear",
    )


def test_single_domain_overconcentration_blocks_report() -> None:
    report = score(
        covered_domain_count=d("2"),
        primary_domain_case_count=d("56"),
        rotation_gap_count=d("4"),
        undercovered_domain_count=d("4"),
        recent_rotation_count=d("0"),
        category_coverage_score=d("0.350000"),
    )

    assert report.primary_domain_concentration_score == d("0.933333")
    assert report.rotation_gap_score == d("1.000000")
    assert report.undercovered_domain_score == d("1.000000")
    assert report.rotation_completion_score == d("0.000000")
    assert report.domain_rotation_risk_score == d("0.910000")
    assert report.domain_rotation_status == "block"
    assert report.report_status == "block"
    assert report.hard_flag is True
    assert report.reason_codes == (
        "domain_rotation_block",
        "primary_domain_concentration_high",
        "rotation_gap_high",
        "undercovered_domain_high",
        "rotation_completion_low",
        "category_coverage_weak",
        "domain_depth_low",
        "case_depth_sufficient",
        "hard_flag_present",
    )


def test_decimal_exact_type_validation_rejects_int_float_and_subclass_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="covered_domain_count must be exactly Decimal"):
        domain_input(covered_domain_count=6)

    with pytest.raises(ValueError, match="category_coverage_score must be exactly Decimal"):
        domain_input(category_coverage_score=0.9)

    with pytest.raises(ValueError, match="total_case_count must be exactly Decimal"):
        domain_input(total_case_count=_DecimalSubclass("60"))

    with pytest.raises(ValueError, match="rotation_gap_count must be integral"):
        domain_input(rotation_gap_count=d("1.500000"))

    with pytest.raises(ValueError, match="category_coverage_score must use six decimal places or fewer"):
        domain_input(category_coverage_score=d("0.9000001"))

    with pytest.raises(ValueError, match="primary_domain_case_count must not exceed total_case_count"):
        domain_input(primary_domain_case_count=d("61"))

    with pytest.raises(ValueError, match="score weights must sum to 1.000000"):
        module.TeamSpecialistDomainRotationScoreConfig(
            concentration_weight=d("0.410000"),
        )

    with pytest.raises(ValueError, match="score watch threshold must not exceed block threshold"):
        module.TeamSpecialistDomainRotationScoreConfig(
            score_watch_floor=d("0.800000"),
        )


def test_public_payload_rejects_leaks_and_non_public_status_words() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public value"):
        domain_input(team_id=f"team-{hidden_word('77616c6c6574')}")

    payload = score().payload
    assert_status_vocabulary(payload)
    payload_text = json.dumps(payload, sort_keys=True)
    for hidden in (
        "63616e6469646174655f6964",
        "6d61726b65745f6964",
        "6d61726b65745f736c7567",
        "7175657374696f6e",
        "736f757263655f726566",
        "75726c",
        "736f757263655f74657874",
        "64736e",
        "7461626c655f6e616d65",
        "746f6b656e",
        "61757468",
        "77616c6c6574",
        "6f72646572",
        "7472616465",
        "627579",
        "73656c6c",
        "7265636f6d6d656e646174696f6e",
        "706f736974696f6e",
    ):
        assert hidden_word(hidden) not in payload_text.lower()

    tampered_payload = dict(payload)
    tampered_payload[hidden_word("6d61726b65745f6964")] = "redacted"
    with pytest.raises(ValueError, match="unsafe public key"):
        module.team_specialist_domain_rotation_score_payload(tampered_payload)

    tampered_payload = dict(payload)
    tampered_payload["team_id"] = f"team-{hidden_word('7472616465')}"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.team_specialist_domain_rotation_score_payload(tampered_payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistDomainRotationScoreConfig()
    input_signal = domain_input()
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
        module.TeamSpecialistDomainRotationScoreInput(
            team_id="team-alpha",
            specialist_id="specialist-rates-alpha",
            primary_domain_id="macro-rates",
            covered_domain_count=d("6"),
            primary_domain_case_count=d("18"),
            total_case_count=d("60"),
            rotation_gap_count=d("1"),
            undercovered_domain_count=d("1"),
            recent_rotation_count=d("4"),
            target_rotation_count=d("4"),
            category_coverage_score=d("0.900000"),
            paper_only=False,
        )


def test_low_case_depth_sets_hard_flag_and_report_block() -> None:
    report = score(
        total_case_count=d("8"),
        primary_domain_case_count=d("2"),
    )

    assert report.domain_rotation_risk_score == d("0.145000")
    assert report.domain_rotation_status == "pass"
    assert report.report_status == "block"
    assert report.hard_flag is True
    assert "case_depth_low" in report.reason_codes
    assert "hard_flag_present" in report.reason_codes


def test_payload_is_deterministic_and_json_ready() -> None:
    left = score().payload
    right = score().payload

    assert left == right
    assert left["derived_validation_digest"] == right["derived_validation_digest"]
    assert left["domain_rotation_risk_score"] == "0.160000"
    assert_no_float_or_int_values(left)
    json.dumps(left, sort_keys=True)


def test_report_and_digest_consistency_rejects_tampering() -> None:
    report = score()

    assert report.payload["derived_validation_digest"] == report.derived_validation_digest

    with pytest.raises(ValueError, match="report_status must match hard flag and domain rotation status"):
        replace(report, report_status="watch")

    with pytest.raises(ValueError, match="domain_rotation_risk_score does not match inputs"):
        replace(report, domain_rotation_risk_score=d("0.150000"))

    with pytest.raises(ValueError, match="derived_validation_digest does not match report payload"):
        replace(report, derived_validation_digest="0" * 64)


def test_module_is_pure_report_only_without_io_imports_or_trading_surface() -> None:
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
        "pathlib",
    }
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".")[0] for alias in node.names}
            assert imported_roots.isdisjoint(forbidden_import_roots)
        elif isinstance(node, ast.ImportFrom):
            imported_roots = {("" if node.module is None else node.module.split(".")[0])}
            assert imported_roots.isdisjoint(forbidden_import_roots)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_or_attribute_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_or_attribute_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_call_or_attribute_names
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not float_constants
