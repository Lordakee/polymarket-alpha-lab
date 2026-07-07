from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_resolution_quality_matrix"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_RESEARCH_RESOLUTION_QUALITY_MATRIX_CONFIG_VERSION,
        "max_pass_resolution_quality_risk_score": d("0.250000"),
        "max_watch_resolution_quality_risk_score": d("0.550000"),
        "min_pass_rule_clarity_score": d("0.900000"),
        "min_watch_rule_clarity_score": d("0.650000"),
        "max_pass_dispute_risk_score": d("0.250000"),
        "max_watch_dispute_risk_score": d("0.550000"),
        "max_pass_path_ambiguity_score": d("0.250000"),
        "max_watch_path_ambiguity_score": d("0.550000"),
        "min_pass_settlement_monitoring_readiness_score": d("0.850000"),
        "min_watch_settlement_monitoring_readiness_score": d("0.600000"),
        "rule_uncertainty_weight": d("0.300000"),
        "dispute_risk_weight": d("0.250000"),
        "path_ambiguity_weight": d("0.250000"),
        "settlement_monitoring_gap_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchResolutionQualityMatrixConfig(**values)


def item(**overrides: object):
    module = api()
    values = {
        "research_item_reference": "research_ref_alpha",
        "rule_clarity_score": d("0.950000"),
        "dispute_risk_score": d("0.100000"),
        "path_ambiguity_score": d("0.100000"),
        "settlement_monitoring_readiness_score": d("0.950000"),
    }
    values.update(overrides)
    return module.ResearchResolutionQualityMatrixInput(**values)


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_resolution_quality_matrix(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_no_numeric_payload_values(value: Any) -> None:
    if type(value) in (Decimal, float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_numeric_payload_values(item_value)
    if isinstance(value, list):
        for item_value in value:
            assert_no_numeric_payload_values(item_value)


def test_pass_watch_block_resolution_quality_matrix_for_human_research() -> None:
    result = report(
        item(
            research_item_reference="research_ref_pass",
            rule_clarity_score=d("0.950000"),
            dispute_risk_score=d("0.100000"),
            path_ambiguity_score=d("0.100000"),
            settlement_monitoring_readiness_score=d("0.950000"),
        ),
        item(
            research_item_reference="research_ref_watch",
            rule_clarity_score=d("0.780000"),
            dispute_risk_score=d("0.300000"),
            path_ambiguity_score=d("0.300000"),
            settlement_monitoring_readiness_score=d("0.750000"),
        ),
        item(
            research_item_reference="research_ref_block",
            rule_clarity_score=d("0.400000"),
            dispute_risk_score=d("0.700000"),
            path_ambiguity_score=d("0.900000"),
            settlement_monitoring_readiness_score=d("0.200000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.max_resolution_quality_risk_score == d("0.740000")
    assert result.average_resolution_quality_risk_score == d("0.360333")
    assert result.status == "block"
    assert result.human_research_priority == "urgent"
    assert result.reason_codes == (
        "resolution_quality_matrix_block_present",
        "resolution_quality_matrix_watch_present",
        "rule_clarity_block_present",
        "dispute_risk_block_present",
        "path_ambiguity_block_present",
        "settlement_monitoring_readiness_block_present",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_sha256(result.report_sha256)
    assert_sha256(result.derived_validation_digest)

    assert tuple(row.status for row in result.results) == ("block", "watch", "pass")
    blocked, watched, passed = result.results

    assert blocked.research_item_reference == "research_ref_block"
    assert blocked.rule_uncertainty_score == d("0.600000")
    assert blocked.settlement_monitoring_gap_score == d("0.800000")
    assert blocked.resolution_quality_risk_score == d("0.740000")
    assert blocked.human_research_priority == "urgent"
    assert blocked.reason_codes == (
        "resolution_quality_matrix_block",
        "rule_clarity_block",
        "dispute_risk_block",
        "path_ambiguity_block",
        "settlement_monitoring_readiness_block",
    )
    assert_sha256(blocked.result_sha256)
    assert_sha256(blocked.derived_validation_digest)

    assert watched.resolution_quality_risk_score == d("0.266000")
    assert watched.status == "watch"
    assert watched.human_research_priority == "elevated"
    assert watched.reason_codes == (
        "resolution_quality_matrix_watch",
        "rule_clarity_watch",
        "dispute_risk_watch",
        "path_ambiguity_watch",
        "settlement_monitoring_readiness_watch",
    )

    assert passed.resolution_quality_risk_score == d("0.075000")
    assert passed.status == "pass"
    assert passed.human_research_priority == "routine"
    assert passed.reason_codes == ("resolution_quality_matrix_pass",)


def test_decimal_exact_type_rejection_and_frozen_public_dataclasses() -> None:
    module = api()
    result = report(item()).results[0]

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="rule_clarity_score must be a Decimal"):
        item(rule_clarity_score=1)
    with pytest.raises(ValueError, match="dispute_risk_score must be a Decimal"):
        item(dispute_risk_score=0.1)
    with pytest.raises(ValueError, match="path_ambiguity_score must be a Decimal"):
        item(path_ambiguity_score=DecimalSubclass("0.100000"))
    with pytest.raises(
        ValueError,
        match="settlement_monitoring_readiness_score must be a Decimal",
    ):
        item(settlement_monitoring_readiness_score=DecimalSubclass("0.900000"))
    with pytest.raises(
        ValueError,
        match="max_pass_resolution_quality_risk_score must be a Decimal",
    ):
        config(max_pass_resolution_quality_risk_score=0.25)
    with pytest.raises(ValueError, match="weights must sum"):
        config(settlement_monitoring_gap_weight=d("0.150000"))
    with pytest.raises(ValueError, match="inputs items must be"):
        report(object())
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_resolution_quality_matrix(
            (item(),),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_public_payload_rejects_sensitive_keys_values_and_trading_language() -> None:
    module = api()

    for forbidden_reference in (
        "raw_candidate_id_123",
        "candidate_id_123",
        "market_id_123",
        "market_slug_alpha",
        "market_question_text",
        "source_ref_alpha",
        "source_url_alpha",
        "source_text_alpha",
        "https_example",
        "postgres_dsn",
        "table_name",
        "token_value",
        "wallet_auth",
        "order_trade",
        "position_size",
        "buy_sell_recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            item(research_item_reference=forbidden_reference)

    result = report(item())
    payload = module.research_resolution_quality_matrix_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    for forbidden in (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "http",
        "url=",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert forbidden not in rendered

    with pytest.raises(ValueError, match="unsafe public"):
        module.validate_research_resolution_quality_matrix_public_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "market_id": "leak"},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.validate_research_resolution_quality_matrix_public_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "safe": "buy now"},
        )


def test_hard_paper_report_readonly_flags_are_enforced() -> None:
    result = report(item())

    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.results[0].paper_only is True
    assert result.results[0].report_only is True
    assert result.results[0].readonly is True

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        item(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result.results[0], readonly=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)


def test_report_and_digest_are_deterministic_decimal_string_public_payloads() -> None:
    module = api()
    first = report(
        item(
            research_item_reference="research_ref_watch",
            rule_clarity_score=d("0.780000"),
            dispute_risk_score=d("0.300000"),
            path_ambiguity_score=d("0.300000"),
            settlement_monitoring_readiness_score=d("0.750000"),
        ),
        generated_at=datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    second = report(
        item(
            research_item_reference="research_ref_watch",
            rule_clarity_score=d("0.780000"),
            dispute_risk_score=d("0.300000"),
            path_ambiguity_score=d("0.300000"),
            settlement_monitoring_readiness_score=d("0.750000"),
        ),
        generated_at=GENERATED_AT,
    )

    first_payload = module.research_resolution_quality_matrix_payload(first)
    second_payload = module.research_resolution_quality_matrix_payload(second)

    assert first == second
    assert first_payload == second_payload
    assert first.report_sha256 == second.report_sha256
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert first_payload["item_count"] == "1.000000"
    assert first_payload["average_resolution_quality_risk_score"] == "0.266000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert first_payload["results"][0]["resolution_quality_risk_score"] == "0.266000"
    assert first_payload["results"][0]["status"] == "watch"
    assert first_payload["results"][0]["human_research_priority"] == "elevated"
    assert_no_numeric_payload_values(first_payload)
    assert json.dumps(first_payload, allow_nan=False, sort_keys=True)


def test_report_consistency_rejects_tampering() -> None:
    result = report(item())

    with pytest.raises(ValueError, match="status"):
        replace(result.results[0], status="ready")
    with pytest.raises(ValueError, match="rule_uncertainty_score must match"):
        replace(
            result.results[0],
            rule_uncertainty_score=d("0.400000"),
            result_sha256="",
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="settlement_monitoring_gap_score must match"):
        replace(
            result.results[0],
            settlement_monitoring_gap_score=d("0.400000"),
            result_sha256="",
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="item_count must match"):
        replace(result, item_count=d("2.000000"), report_sha256="", derived_validation_digest="")
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            result,
            reason_codes=("resolution_quality_matrix_clear", "rule_clarity_watch_present"),
            report_sha256="",
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="report_sha256 mismatch"):
        replace(result, report_sha256="0" * 64)


def test_module_is_pure_research_only_decimal_only_and_not_wired_to_live_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)  # type: ignore[union-attr]
    assert source is not None

    assert module.ResearchResolutionQualityMatrixConfig.__dataclass_params__.frozen
    assert module.ResearchResolutionQualityMatrixInput.__dataclass_params__.frozen
    assert module.ResearchResolutionQualityMatrixResult.__dataclass_params__.frozen
    assert module.ResearchResolutionQualityMatrixReport.__dataclass_params__.frozen
    assert module.__all__ == (
        "DEFAULT_RESEARCH_RESOLUTION_QUALITY_MATRIX_CONFIG_VERSION",
        "ResearchResolutionQualityMatrixConfig",
        "ResearchResolutionQualityMatrixInput",
        "ResearchResolutionQualityMatrixResult",
        "ResearchResolutionQualityMatrixReport",
        "build_research_resolution_quality_matrix",
        "validate_research_resolution_quality_matrix_report",
        "validate_research_resolution_quality_matrix_public_payload",
        "research_resolution_quality_matrix_payload",
    )
    assert "paper_only" in source
    assert "report_only" in source
    assert "readonly" in source

    forbidden_import_roots = (
        "boto3",
        "http",
        "httpx",
        "io",
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
    forbidden_call_names = {
        "authenticate",
        "cancel_order",
        "commit",
        "connect",
        "create_order",
        "execute",
        "fetch",
        "input",
        "open",
        "order",
        "patch",
        "place_order",
        "post",
        "print",
        "put",
        "read_text",
        "request",
        "submit_order",
        "trade",
        "urlopen",
        "write_text",
    }
    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", *forbidden_call_names}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_names

    assert {name.split(".", 1)[0] for name in imported_modules}.isdisjoint(
        forbidden_import_roots,
    )
    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
