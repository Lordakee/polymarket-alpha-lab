from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_information_collection_tool_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _capability(
    tool_name: str,
    task_family: str,
    *,
    coverage_score: Decimal = d("0.920000"),
    extraction_score: Decimal = d("0.910000"),
    verification_score: Decimal = d("0.900000"),
    stability_score: Decimal = d("0.890000"),
    gap_count: Decimal = d("0"),
    hard_gap_count: Decimal = d("0"),
):
    module = api()
    return module.ResearchInformationCollectionToolReadinessInput(
        tool_name=tool_name,
        task_family=task_family,
        coverage_score=coverage_score,
        extraction_score=extraction_score,
        verification_score=verification_score,
        stability_score=stability_score,
        gap_count=gap_count,
        hard_gap_count=hard_gap_count,
    )


def _config(**overrides: object):
    module = api()
    return module.ResearchInformationCollectionToolReadinessConfig(**overrides)


def _build_report(*capabilities, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_information_collection_tool_readiness_report(
        capabilities,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_report_rolls_up_pass_watch_block_and_public_digest_consistently() -> None:
    module = api()
    pass_row = _capability("agent-reach", "news_verification")
    watch_row = _capability(
        "scrapling",
        "dynamic_page_review",
        verification_score=d("0.700000"),
        gap_count=d("1"),
    )
    block_row = _capability(
        "agent-reach",
        "long_pdf_review",
        coverage_score=d("0.400000"),
        hard_gap_count=d("1"),
    )

    report = _build_report(pass_row, watch_row, block_row)
    permuted_report = _build_report(block_row, pass_row, watch_row)
    payload = module.research_information_collection_tool_readiness_report_to_payload(
        report,
    )
    permuted_payload = (
        module.research_information_collection_tool_readiness_report_to_payload(
            permuted_report,
        )
    )
    digest = module.research_information_collection_tool_readiness_digest(report)
    digest_payload = (
        module.research_information_collection_tool_readiness_digest_to_payload(
            digest,
        )
    )

    assert is_dataclass(report)
    assert report.status == "block"
    assert report.reason_codes == (
        "research_information_collection_tool_readiness_block",
        "research_information_collection_tool_readiness_watch",
        "research_information_collection_tool_readiness_pass",
    )
    assert report.tool_task_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.pass_ratio == d("0.333333")
    assert report.watch_ratio == d("0.333333")
    assert report.block_ratio == d("0.333333")
    assert report.mean_readiness_score == d("0.823333")
    assert report.min_readiness_score == d("0.745000")
    assert report.max_readiness_score == d("0.905000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.external_collection_allowed is False
    assert report.network_write_allowed is False

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.tool_name for row in report.rows) == (
        "agent-reach",
        "scrapling",
        "agent-reach",
    )
    assert report.rows[0].reason_codes == (
        "research_information_collection_tool_readiness_block_hard_gap",
        "research_information_collection_tool_readiness_block_score",
    )
    assert report.rows[1].reason_codes == (
        "research_information_collection_tool_readiness_watch_gap",
        "research_information_collection_tool_readiness_watch_score",
    )
    assert report.rows[2].reason_codes == (
        "research_information_collection_tool_readiness_pass",
    )

    assert payload == permuted_payload
    assert payload["public_digest"] == digest.public_digest
    assert digest_payload["public_digest"] == report.public_digest
    assert digest_payload["status"] == payload["status"] == "block"
    assert digest_payload["tool_task_count"] == payload["tool_task_count"] == "3"
    assert _float_paths(payload) == ()
    assert _float_paths(digest_payload) == ()
    json.dumps(payload, sort_keys=True)
    json.dumps(digest_payload, sort_keys=True)


def test_empty_report_is_pass_report_only_and_json_ready() -> None:
    module = api()
    local_generated_at = datetime(
        2026,
        7,
        8,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    report = _build_report(generated_at=local_generated_at)
    payload = module.research_information_collection_tool_readiness_report_to_payload(
        report,
    )

    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.reason_codes == (
        "research_information_collection_tool_readiness_pass",
    )
    assert report.tool_task_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.mean_readiness_score == d("0.000000")
    assert report.min_readiness_score == d("0.000000")
    assert report.max_readiness_score == d("0.000000")
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["status"] == "pass"
    assert payload["tool_task_count"] == "0"
    assert payload["rows"] == []
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_status_type_decimal_frozen_and_hard_flags_are_validated() -> None:
    module = api()
    report = _build_report(_capability("agent-reach", "policy_event_review"))

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report, status="clear")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="coverage_score must be a Decimal"):
        _capability("agent-reach", "policy_event_review", coverage_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="pass_count must be a Decimal"):
        replace(report, pass_count=1)
    with pytest.raises(ValueError, match="coverage_score must be between 0 and 1"):
        _capability(
            "agent-reach",
            "policy_event_review",
            coverage_score=d("1.000001"),
        )
    with pytest.raises(ValueError, match="gap_count must be integral"):
        _capability(
            "agent-reach",
            "policy_event_review",
            gap_count=d("1.250000"),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_information_collection_tool_readiness_report(
            (_capability("agent-reach", "policy_event_review"),),
            config=_config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="external_collection_allowed must be False"):
        replace(report, external_collection_allowed=True)
    with pytest.raises(ValueError, match="network_write_allowed must be False"):
        module.ResearchInformationCollectionToolReadinessConfig(
            network_write_allowed=True,
        )


def test_public_leak_rejection_blocks_sensitive_values_and_reason_codes() -> None:
    unsafe_values = (
        "raw_" + "candidate_" + "id",
        "market_" + "id",
        "market_" + "slug",
        "question",
        "source_" + "ref",
        "source_" + "url",
        "source_" + "text",
        "dsn",
        "table",
        "token",
        "wal" + "let",
        "ord" + "er",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    module = api()
    report = _build_report(_capability("agent-reach", "policy_event_review"))

    for unsafe_value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public value"):
            _capability(unsafe_value, "policy_event_review")
        with pytest.raises(ValueError, match="unsafe public value"):
            _capability("agent-reach", unsafe_value)
        with pytest.raises(ValueError, match="unsafe public value"):
            replace(report, reason_codes=(unsafe_value,))

    with pytest.raises(ValueError, match="duplicate tool/task"):
        _build_report(
            _capability("agent-reach", "policy_event_review"),
            _capability("agent-reach", "policy_event_review"),
        )
    with pytest.raises(ValueError, match="report must be"):
        module.research_information_collection_tool_readiness_report_to_payload(object())
    with pytest.raises(ValueError, match="digest must be"):
        module.research_information_collection_tool_readiness_digest_to_payload(object())


def test_public_api_stays_report_only_without_external_call_surfaces() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_INFORMATION_COLLECTION_TOOL_READINESS_CONFIG_VERSION",
        "ResearchInformationCollectionToolReadinessConfig",
        "ResearchInformationCollectionToolReadinessDigest",
        "ResearchInformationCollectionToolReadinessInput",
        "ResearchInformationCollectionToolReadinessReport",
        "ResearchInformationCollectionToolReadinessRow",
        "build_research_information_collection_tool_readiness_report",
        "research_information_collection_tool_readiness_digest",
        "research_information_collection_tool_readiness_digest_to_payload",
        "research_information_collection_tool_readiness_report_to_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _float_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if isinstance(value, float):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    return ()
