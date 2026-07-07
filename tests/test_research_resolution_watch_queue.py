from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_resolution_watch_queue"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_resolution_watch_queue.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "url",
    "URL",
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
    "recommend",
)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": module.DEFAULT_RESEARCH_RESOLUTION_WATCH_QUEUE_CONFIG_VERSION,
        "max_pass_combined_watch_score": d("0.250000"),
        "max_watch_combined_watch_score": d("0.550000"),
        "max_pass_settlement_monitoring_priority_score": d("0.250000"),
        "max_watch_settlement_monitoring_priority_score": d("0.600000"),
        "max_pass_resolution_quality_risk_score": d("0.250000"),
        "max_watch_resolution_quality_risk_score": d("0.550000"),
        "max_pass_rule_risk_score": d("0.250000"),
        "max_watch_rule_risk_score": d("0.550000"),
        "min_pass_review_readiness_score": d("0.850000"),
        "min_watch_review_readiness_score": d("0.600000"),
        "settlement_monitoring_weight": d("0.300000"),
        "resolution_quality_weight": d("0.300000"),
        "rule_risk_weight": d("0.200000"),
        "review_readiness_gap_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchResolutionWatchQueueConfig(**values)


def item(**overrides: object) -> Any:
    module = api()
    values = {
        "research_item_reference": "research_ref_pass",
        "settlement_monitoring_status": "pass",
        "settlement_monitoring_priority_score": d("0.050000"),
        "resolution_quality_risk_score": d("0.080000"),
        "rule_risk_score": d("0.100000"),
        "review_readiness_score": d("0.950000"),
    }
    values.update(overrides)
    return module.ResearchResolutionWatchQueueItem(**values)


def report(*items: object, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_resolution_watch_queue(
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
        for nested in value.values():
            assert_no_numeric_payload_values(nested)
    if isinstance(value, list):
        for nested in value:
            assert_no_numeric_payload_values(nested)


def assert_no_forbidden_public_surface(value: Any) -> None:
    rendered = json.dumps(value, sort_keys=True).lower()
    for forbidden in FORBIDDEN_PUBLIC_FRAGMENTS:
        assert forbidden.lower() not in rendered


def test_builds_deterministic_pass_watch_block_resolution_watch_queue() -> None:
    module = api()
    result = report(
        item(research_item_reference="research_ref_pass"),
        item(
            research_item_reference="research_ref_watch",
            settlement_monitoring_status="watch",
            settlement_monitoring_priority_score=d("0.350000"),
            resolution_quality_risk_score=d("0.300000"),
            rule_risk_score=d("0.400000"),
            review_readiness_score=d("0.750000"),
        ),
        item(
            research_item_reference="research_ref_block",
            settlement_monitoring_status="block",
            settlement_monitoring_priority_score=d("0.900000"),
            resolution_quality_risk_score=d("0.700000"),
            rule_risk_score=d("0.800000"),
            review_readiness_score=d("0.300000"),
        ),
    )

    assert type(result) is module.ResearchResolutionWatchQueueReport
    assert result.generated_at == GENERATED_AT
    assert result.item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.max_combined_watch_score == d("0.780000")
    assert result.average_combined_watch_score == d("0.391333")
    assert result.status == "block"
    assert result.reason_codes == (
        "resolution_watch_queue_block_present",
        "resolution_watch_queue_watch_present",
        "settlement_monitoring_block_present",
        "resolution_quality_block_present",
        "rule_risk_block_present",
        "review_readiness_block_present",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_sha256(result.derived_validation_digest)

    assert tuple(row.research_item_reference for row in result.rows) == (
        "research_ref_block",
        "research_ref_watch",
        "research_ref_pass",
    )
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert tuple(row.desensitized_monitoring_priority for row in result.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    blocked, watched, passed = result.rows
    assert blocked.review_readiness_gap_score == d("0.700000")
    assert blocked.combined_watch_score == d("0.780000")
    assert blocked.reason_codes == (
        "resolution_watch_queue_block",
        "settlement_monitoring_block",
        "resolution_quality_block",
        "rule_risk_block",
        "review_readiness_block",
    )
    assert watched.combined_watch_score == d("0.325000")
    assert watched.reason_codes == (
        "resolution_watch_queue_watch",
        "settlement_monitoring_watch",
        "resolution_quality_watch",
        "rule_risk_watch",
        "review_readiness_watch",
    )
    assert passed.combined_watch_score == d("0.069000")
    assert passed.reason_codes == ("resolution_watch_queue_pass",)

    payload = module.research_resolution_watch_queue_payload(result)
    module.validate_research_resolution_watch_queue_public_payload(payload)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["max_combined_watch_score"] == "0.780000"
    assert payload["rows"][0]["desensitized_monitoring_priority"] == "1.000000"
    assert payload["rows"][0]["combined_watch_score"] == "0.780000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_numeric_payload_values(payload)
    assert_no_forbidden_public_surface(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    shuffled_payload = module.research_resolution_watch_queue_payload(
        report(result.rows[2], result.rows[0], result.rows[1]),
    )
    assert shuffled_payload == payload


def test_empty_queue_passes_without_private_identifiers() -> None:
    result = report()

    assert result.status == "pass"
    assert result.item_count == d("0.000000")
    assert result.reason_codes == ("resolution_watch_queue_no_items",)
    assert result.rows == ()
    assert result.max_combined_watch_score == d("0.000000")
    assert result.average_combined_watch_score == d("0.000000")


def test_frozen_dataclasses_strict_decimal_types_and_flags() -> None:
    module = api()
    result = report(item())

    for cls in (
        module.ResearchResolutionWatchQueueConfig,
        module.ResearchResolutionWatchQueueItem,
        module.ResearchResolutionWatchQueueRow,
        module.ResearchResolutionWatchQueueReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="settlement_monitoring_priority_score"):
        item(settlement_monitoring_priority_score=1)
    with pytest.raises(ValueError, match="resolution_quality_risk_score"):
        item(resolution_quality_risk_score=0.1)
    with pytest.raises(ValueError, match="rule_risk_score"):
        item(rule_risk_score=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="review_readiness_score"):
        item(review_readiness_score=d("1.0000001"))
    with pytest.raises(ValueError, match="settlement_monitoring_status"):
        item(settlement_monitoring_status="ready")
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        item(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result.rows[0], readonly=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)


def test_threshold_validation_datetime_normalization_and_tamper_checks() -> None:
    module = api()
    offset_time = datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7)))
    result = report(item(), generated_at=offset_time)

    assert result.generated_at == GENERATED_AT
    assert module.research_resolution_watch_queue_payload(result)["generated_at"] == (
        "2026-07-07T12:00:00+00:00"
    )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(item(), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="max_pass_combined_watch_score"):
        config(max_pass_combined_watch_score=d("0.700000"))
    with pytest.raises(ValueError, match="max_pass_resolution_quality_risk_score"):
        config(max_pass_resolution_quality_risk_score=d("0.700000"))
    with pytest.raises(ValueError, match="min_pass_review_readiness_score"):
        config(min_pass_review_readiness_score=d("0.500000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(review_readiness_gap_weight=d("0.100000"))
    with pytest.raises(ValueError, match="items must be"):
        report(object())
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_resolution_watch_queue(
            (item(),),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="item_count"):
        replace(result, item_count=d("2.000000"), derived_validation_digest="")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            result,
            reason_codes=("resolution_watch_queue_clear", "rule_risk_watch_present"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)


def test_public_payload_rejects_sensitive_keys_values_numerics_and_trading_language() -> None:
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
        "URL_value",
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

    payload = module.research_resolution_watch_queue_payload(report(item()))
    module.validate_research_resolution_watch_queue_public_payload(payload)

    for leaky_payload in (
        {**payload, "raw_candidate_id": "abc"},
        {**payload, "market_id": "abc"},
        {**payload, "market_slug": "abc"},
        {**payload, "question": "will it resolve"},
        {**payload, "source_ref": "official"},
        {**payload, "source_url": "https://example.invalid"},
        {**payload, "URL": "https://example.invalid"},
        {**payload, "dsn": "postgres://example"},
        {**payload, "table": "real_table"},
        {**payload, "rows": [{**payload["rows"][0], "audit_note": "wallet token"}]},
        {**payload, "rows": [{**payload["rows"][0], "audit_note": "buy this"}]},
        {**payload, "rows": [{**payload["rows"][0], "audit_note": "sell this"}]},
        {**payload, "rows": [{**payload["rows"][0], "audit_note": "recommendation"}]},
    ):
        with pytest.raises(ValueError):
            module.validate_research_resolution_watch_queue_public_payload(leaky_payload)

    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_research_resolution_watch_queue_public_payload(
            {**payload, "item_count": 1},
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.validate_research_resolution_watch_queue_public_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_resolution_watch_queue_public_payload(
            {**payload, "item_count": "9.000000"},
        )


def test_module_scope_is_pure_report_only_research_and_external_io_free() -> None:
    module = api()
    source = MODULE_PATH.read_text()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_RESOLUTION_WATCH_QUEUE_CONFIG_VERSION",
        "ResearchResolutionWatchQueueConfig",
        "ResearchResolutionWatchQueueItem",
        "ResearchResolutionWatchQueueRow",
        "ResearchResolutionWatchQueueReport",
        "build_research_resolution_watch_queue",
        "research_resolution_watch_queue_payload",
        "validate_research_resolution_watch_queue_public_payload",
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
