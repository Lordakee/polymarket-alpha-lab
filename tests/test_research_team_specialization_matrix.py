from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = Path("src/polymarket_alpha_lab/research_team_specialization_matrix.py")
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
PUBLIC_STATES = {"pass", "watch", "block"}


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialization_matrix",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-specialization-matrix-test",
        "domain_ids": ("politics", "macro", "crypto"),
        "min_pass_role_coverage_ratio": d("1.000000"),
        "min_watch_role_coverage_ratio": d("0.800000"),
        "min_pass_memory_quality_score": d("0.750000"),
        "min_watch_memory_quality_score": d("0.500000"),
        "min_pass_capacity_ratio": d("0.250000"),
        "min_watch_capacity_ratio": d("0.100000"),
        "min_pass_review_quality_ratio": d("0.800000"),
        "min_watch_review_quality_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecializationMatrixConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "domain_id": "politics",
        "team_code": "politics_research",
        "covered_role_count": d("5.000000"),
        "required_role_count": d("5.000000"),
        "memory_quality_score": d("0.850000"),
        "available_capacity_count": d("4.000000"),
        "required_capacity_count": d("10.000000"),
        "review_count": d("10.000000"),
        "high_quality_review_count": d("9.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecializationObservation(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_specialization_matrix(
        items,
        generated_at=generated_at,
        config=cfg if cfg is not None else config(),
    )


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
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if isinstance(value, datetime):
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


def assert_public_states_only(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("_status") or key.endswith("_state") or key == "status":
                assert item in PUBLIC_STATES
            assert_public_states_only(item)
    elif isinstance(value, list):
        for item in value:
            assert_public_states_only(item)


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate_id",
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "http://",
        "https://",
        "source_ref",
        "source_url",
        "source_text",
        "url",
        "dsn",
        "table_name",
        "table",
        "token",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "recommend",
        "position",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def test_public_api_declares_report_only_specialization_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_TEAM_SPECIALIZATION_MATRIX_CONFIG_VERSION == (
        "research-team-specialization-matrix-v1"
    )
    assert module.DEFAULT_RESEARCH_TEAM_SPECIALIZATION_DOMAINS == (
        "politics",
        "macro",
        "crypto",
        "equity_index",
        "gold",
        "soccer",
        "basketball",
    )
    assert module.RESEARCH_TEAM_SPECIALIZATION_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIZATION_DOMAINS",
        "DEFAULT_RESEARCH_TEAM_SPECIALIZATION_MATRIX_CONFIG_VERSION",
        "RESEARCH_TEAM_SPECIALIZATION_STATUSES",
        "ResearchTeamSpecializationMatrixConfig",
        "ResearchTeamSpecializationMatrixReport",
        "ResearchTeamSpecializationMatrixRow",
        "ResearchTeamSpecializationObservation",
        "build_research_team_specialization_matrix",
        "research_team_specialization_matrix_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(module.ResearchTeamSpecializationMatrixConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True


def test_aggregates_domain_specialization_into_pass_watch_block_rows() -> None:
    report = build_report(
        observation(domain_id="politics", team_code="team_politics"),
        observation(
            domain_id="macro",
            team_code="team_macro",
            covered_role_count=d("4.000000"),
            required_role_count=d("5.000000"),
            memory_quality_score=d("0.700000"),
            available_capacity_count=d("2.000000"),
            required_capacity_count=d("10.000000"),
            review_count=d("5.000000"),
            high_quality_review_count=d("3.000000"),
        ),
        observation(
            domain_id="crypto",
            team_code="team_crypto",
            covered_role_count=d("2.000000"),
            required_role_count=d("5.000000"),
            memory_quality_score=d("0.400000"),
            available_capacity_count=d("0.000000"),
            required_capacity_count=d("10.000000"),
            review_count=d("3.000000"),
            high_quality_review_count=d("1.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.report_status == "block"
    assert report.domain_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_specialization_score == d("0.548611")
    assert report.lowest_specialization_score == d("0.283333")
    assert report.reason_codes == (
        "specialization_matrix_report_block_rows",
        "specialization_matrix_report_watch_rows",
    )

    assert tuple(row.domain_id for row in report.rows) == (
        "politics",
        "macro",
        "crypto",
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert tuple(row.role_coverage_ratio for row in report.rows) == (
        d("1.000000"),
        d("0.800000"),
        d("0.400000"),
    )
    assert tuple(row.capacity_ratio for row in report.rows) == (
        d("0.400000"),
        d("0.200000"),
        d("0.000000"),
    )
    assert tuple(row.review_quality_ratio for row in report.rows) == (
        d("0.900000"),
        d("0.600000"),
        d("0.333333"),
    )
    assert tuple(row.specialization_score for row in report.rows) == (
        d("0.787500"),
        d("0.575000"),
        d("0.283333"),
    )
    assert report.rows[0].reason_codes == (
        "specialization_matrix_pass",
        "role_coverage_pass",
        "memory_quality_pass",
        "capacity_pass",
        "review_quality_pass",
    )
    assert report.rows[1].reason_codes == (
        "specialization_matrix_watch",
        "role_coverage_watch",
        "memory_quality_watch",
        "capacity_watch",
        "review_quality_watch",
    )
    assert report.rows[2].reason_codes == (
        "specialization_matrix_block",
        "role_coverage_low",
        "memory_quality_low",
        "capacity_low",
        "review_quality_low",
    )
    assert_public_numeric_values_are_decimal(report)


def test_missing_domain_specialization_blocks_without_exposing_team_codes() -> None:
    report = build_report(
        observation(domain_id="politics", team_code="team_politics"),
        cfg=config(domain_ids=("politics", "basketball")),
    )

    assert report.report_status == "block"
    assert tuple(row.domain_id for row in report.rows) == ("politics", "basketball")
    assert report.rows[1].status == "block"
    assert report.rows[1].observation_count == d("0.000000")
    assert report.rows[1].covered_role_count == d("0.000000")
    assert report.rows[1].required_role_count == d("0.000000")
    assert report.rows[1].reason_codes == (
        "specialization_matrix_block",
        "missing_domain_specialization",
        "role_coverage_low",
        "memory_quality_low",
        "capacity_low",
        "review_quality_low",
    )
    assert "team_code" not in report.payload["rows"][0]
    assert "team_codes" not in report.payload["rows"][0]


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: observation(covered_role_count=5),
            "covered_role_count must be exactly Decimal",
        ),
        (
            lambda: observation(memory_quality_score=_DecimalSubclass("0.850000")),
            "memory_quality_score must be exactly Decimal",
        ),
        (
            lambda: observation(memory_quality_score=d("0.8500001")),
            "memory_quality_score must use six decimal places or fewer",
        ),
        (
            lambda: observation(required_role_count=d("5.500000")),
            "required_role_count must be a whole number",
        ),
        (
            lambda: build_report(observation(), generated_at=datetime(2026, 7, 7, 12, 0)),
            "generated_at must be timezone-aware",
        ),
    ),
)
def test_strict_type_validation_rejects_numeric_shortcuts(
    factory: Any,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()


def test_validation_rejects_inconsistent_inputs_configs_and_sequences() -> None:
    module = api()

    with pytest.raises(ValueError, match="covered_role_count must not exceed"):
        observation(covered_role_count=d("6.000000"))
    with pytest.raises(ValueError, match="available_capacity_count must not exceed"):
        observation(available_capacity_count=d("11.000000"))
    with pytest.raises(ValueError, match="high_quality_review_count must not exceed"):
        observation(high_quality_review_count=d("11.000000"))
    with pytest.raises(ValueError, match="team_code must be a public identifier"):
        observation(team_code="macro research")
    with pytest.raises(ValueError, match="observations must be a sequence"):
        module.build_research_team_specialization_matrix(
            object(),
            generated_at=GENERATED_AT,
            config=config(),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        build_report(object())
    with pytest.raises(ValueError, match="duplicate domain/team observation"):
        build_report(observation(), observation())
    with pytest.raises(ValueError, match="min_watch_role_coverage_ratio must not exceed"):
        config(min_watch_role_coverage_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(build_report(observation()), derived_validation_digest="0" * 64)


def test_payload_has_hard_flags_decimal_strings_and_validated_digest() -> None:
    module = api()
    report = build_report(observation())

    payload = module.research_team_specialization_matrix_payload(report)

    assert payload == report.payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["domain_count"] == "3.000000"
    assert payload["average_specialization_score"] == "0.262500"
    assert payload["rows"][0]["role_coverage_ratio"] == "1.000000"
    assert payload["rows"][0]["capacity_ratio"] == "0.400000"
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert_no_float_values(payload)
    assert_public_states_only(payload)
    assert_public_payload_has_no_forbidden_surface(payload)
    json.dumps(payload, sort_keys=True)

    tampered = dict(payload)
    tampered["average_specialization_score"] = "0.990000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialization_matrix_payload(tampered)

    tampered_digest = dict(payload)
    tampered_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialization_matrix_payload(tampered_digest)


def test_hard_flags_are_enforced_and_dataclasses_are_frozen() -> None:
    module = api()
    cfg = config()
    item = observation()
    report = build_report(item)
    row = report.rows[0]

    for value in (cfg, item, row, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchTeamSpecializationMatrixConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_public_payload_rejects_leaky_identifiers_and_execution_language() -> None:
    module = api()

    for unsafe_value in (
        "raw_candidate_123",
        "market_alpha",
        "event_slug",
        "question_text",
        "source_ref",
        "https://example.test/data",
        "dsn_table",
        "token_wallet",
        "auth_order",
        "trade_position",
        "buy_signal",
        "sell_signal",
        "recommendation_text",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            observation(team_code=unsafe_value)

    report = build_report(observation())
    for unsafe_key in (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "URL",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth_header",
        "order_id",
        "trade_id",
        "position_size",
        "recommendation",
    ):
        payload = dict(report.payload)
        payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public payload"):
            module.research_team_specialization_matrix_payload(payload)

    payload = dict(report.payload)
    payload["safe_field"] = "buy yes"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_team_specialization_matrix_payload(payload)
    payload = dict(report.payload)
    payload["safe_field"] = 0.1
    with pytest.raises(ValueError, match="float"):
        module.research_team_specialization_matrix_payload(payload)


def test_input_order_does_not_change_rows_payload_or_digest() -> None:
    left = observation(domain_id="politics", team_code="team_left")
    right = observation(domain_id="macro", team_code="team_right")

    report_a = build_report(right, left, cfg=config(domain_ids=("politics", "macro")))
    report_b = build_report(left, right, cfg=config(domain_ids=("politics", "macro")))

    assert report_a.payload == report_b.payload
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert tuple(row.domain_id for row in report_a.rows) == ("politics", "macro")
    assert_public_states_only(report_a.payload)


def test_module_stays_report_only_without_network_persistence_or_execution_paths() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "aiohttp",
        "http",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    )
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
        "place_order",
        "rollback",
        "sell",
        "send",
        "sign",
        "trade",
        "write",
    }

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

    assert not float_constants
    assert not any(
        imported == forbidden or imported.startswith(f"{forbidden}.")
        for imported in imports
        for forbidden in forbidden_modules
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
