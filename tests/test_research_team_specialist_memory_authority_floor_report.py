from __future__ import annotations

import ast
import copy
from hashlib import sha256
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_specialist_memory_authority_floor_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_memory_authority_floor_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-specialist-memory-authority-floor-report-test",
        "min_pass_floor": d("0.700000"),
        "min_watch_floor": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistMemoryAuthorityFloorReportConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "team_id": "macro_rates",
        "specialist_id": "rates_research_specialist",
        "category_id": "finance.macro.rates",
        "memory_digest": "a" * 64,
        "authority_score": d("0.760000"),
        "evidence_quality_score": d("0.820000"),
        "calibration_score": d("0.790000"),
        "recency_score": d("0.810000"),
        "independence_score": d("0.880000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistMemoryAuthorityFloorReportObservation(**values)


def build_report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_specialist_memory_authority_floor_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
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


def iter_payload_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(iter_payload_keys(item))
        return tuple(keys)
    return ()


def resign_payload(payload: dict[str, Any]) -> None:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload["derived_validation_digest"] = sha256(
        canonical_payload.encode("utf-8"),
    ).hexdigest()


def test_authority_floor_report_sorts_and_summarizes_statuses() -> None:
    report = build_report(
        observation(memory_digest="b" * 64, authority_score=d("0.560000")),
        observation(memory_digest="c" * 64, authority_score=d("0.300000")),
        observation(memory_digest="a" * 64, authority_score=d("0.760000")),
    )

    assert report.report_status == "block"
    assert report.item_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_authority_floor_score == d("0.540000")
    assert report.minimum_authority_floor_score == d("0.300000")
    assert tuple(row.row_status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.memory_digest for row in report.rows) == (
        "c" * 64,
        "b" * 64,
        "a" * 64,
    )
    assert tuple(row.authority_floor_score for row in report.rows) == (
        d("0.300000"),
        d("0.560000"),
        d("0.760000"),
    )
    assert tuple(row.floor_gap_to_pass for row in report.rows) == (
        d("0.400000"),
        d("0.140000"),
        d("0.000000"),
    )
    assert report.reason_codes == (
        "authority_floor_block_present",
        "authority_floor_watch_present",
        "authority_floor_pass_present",
    )


def test_payload_is_deterministic_sanitized_and_digest_validated() -> None:
    module = api()
    first = build_report(
        observation(memory_digest="b" * 64, authority_score=d("0.560000")),
        observation(memory_digest="a" * 64, authority_score=d("0.760000")),
    )
    second = build_report(
        observation(memory_digest="a" * 64, authority_score=d("0.760000")),
        observation(memory_digest="b" * 64, authority_score=d("0.560000")),
    )

    first_payload = module.research_team_specialist_memory_authority_floor_report_payload(
        first,
    )
    second_payload = module.research_team_specialist_memory_authority_floor_report_payload(
        second,
    )

    assert first_payload == second_payload
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert first_payload["item_count"] == "2"
    assert first_payload["rows"][0]["authority_floor_score"] == "0.560000"
    assert isinstance(first_payload["derived_validation_digest"], str)
    assert len(first_payload["derived_validation_digest"]) == 64
    assert_no_float_values(first_payload)
    assert module.research_team_specialist_memory_authority_floor_report_payload(
        first_payload,
    ) == first_payload

    forbidden_public_key_fragments = (
        "candidate",
        "market",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "raw",
        "text",
    )
    assert not any(
        fragment in key.lower()
        for key in iter_payload_keys(first_payload)
        for fragment in forbidden_public_key_fragments
    )

    tampered = copy.deepcopy(first_payload)
    tampered["rows"][0]["row_status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_memory_authority_floor_report_payload(tampered)


def test_payload_revalidates_statuses_after_digest_recomputation() -> None:
    module = api()
    payload = module.research_team_specialist_memory_authority_floor_report_payload(
        build_report(observation()),
    )
    tampered = copy.deepcopy(payload)
    tampered["rows"][0]["row_status"] = "blocked"
    resign_payload(tampered)

    with pytest.raises(ValueError, match="row_status"):
        module.research_team_specialist_memory_authority_floor_report_payload(tampered)


def test_opaque_sha256_digest_contents_are_not_scanned_as_public_prose() -> None:
    report = build_report(observation(memory_digest="db" + ("a" * 62)))

    assert report.rows[0].memory_digest == "db" + ("a" * 62)


def test_dataclasses_are_frozen_decimal_only_hard_flagged_and_status_limited() -> None:
    module = api()
    sample_config = config()
    sample_observation = observation()
    sample_report = build_report(sample_observation)
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_observation, sample_row, sample_report):
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    assert sample_report.report_status in {"pass", "watch", "block"}
    assert sample_row.row_status in {"pass", "watch", "block"}
    assert "blocked" not in {sample_report.report_status, sample_row.row_status}

    values = {field.name: getattr(sample_row, field.name) for field in fields(sample_row)}
    values["row_status"] = "blocked"
    with pytest.raises(ValueError, match="row_status"):
        module.ResearchTeamSpecialistMemoryAuthorityFloorReportRow(**values)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(observation(readonly=False))


def test_validation_rejects_non_decimal_values_and_threshold_inversions() -> None:
    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        observation(authority_score=0.76)
    with pytest.raises(ValueError, match="min_watch_floor must not exceed min_pass_floor"):
        config(min_watch_floor=d("0.800000"))
    with pytest.raises(ValueError, match="memory_digest"):
        observation(memory_digest="raw-candidate-1")
    with pytest.raises(ValueError, match="rows"):
        build_report(object())


@pytest.mark.parametrize("score", (d("-0.0000004"), d("1.0000004")))
def test_validation_rejects_out_of_range_scores_before_quantization(
    score: Decimal,
) -> None:
    with pytest.raises(ValueError, match="authority_score"):
        observation(authority_score=score)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("config_version", "Will rates rise in 2026?"),
        ("team_id", "Will rates rise in 2026?"),
        ("specialist_id", "https://example.com/research"),
    ),
)
def test_public_identifiers_reject_question_and_url_shaped_text(
    field_name: str,
    value: str,
) -> None:
    constructor = config if field_name == "config_version" else observation

    with pytest.raises(ValueError, match=field_name):
        constructor(**{field_name: value})


@pytest.mark.parametrize(
    "payload",
    (
        {"paper_only": True, "report_only": True, "readonly": True, "candidate_text": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "source_url": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "market_id": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "dsn": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "table": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "token": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "live trade"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "size it"},
        {"paper_only": True, "report_only": False, "readonly": True},
    ),
)
def test_unsafe_public_payload_keys_values_and_flag_downgrades_rejected(
    payload: dict[str, object],
) -> None:
    module = api()

    with pytest.raises(ValueError):
        module.research_team_specialist_memory_authority_floor_report_payload(payload)


def test_module_scope_has_no_network_auth_wallet_order_db_or_decisioning_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
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

    forbidden_import_fragments = (
        "api",
        "broker",
        "client",
        "clob",
        "database",
        "db",
        "http",
        "network",
        "order",
        "persist",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "order",
        "persist",
        "rollback",
        "sell",
        "send",
        "sign",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
