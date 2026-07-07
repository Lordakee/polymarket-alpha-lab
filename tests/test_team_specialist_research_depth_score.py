from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
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
    / "team_specialist_research_depth_score.py"
)
NOW = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_research_depth_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "team-specialist-research-depth-score-test",
        "evidence_depth_weight": d("0.300000"),
        "viewpoint_depth_weight": d("0.200000"),
        "contradiction_depth_weight": d("0.150000"),
        "synthesis_quality_weight": d("0.200000"),
        "rank_context_weight": d("0.100000"),
        "freshness_weight": d("0.050000"),
        "min_pass_depth_score": d("0.850000"),
        "min_watch_depth_score": d("0.650000"),
        "min_evidence_item_count": d("4.000000"),
        "min_viewpoint_count": d("2.000000"),
        "min_contradiction_check_count": d("1.000000"),
        "max_pass_stale_evidence_ratio": d("0.250000"),
        "max_watch_stale_evidence_ratio": d("0.500000"),
        "min_pass_rank_context_score": d("0.700000"),
        "min_watch_rank_context_score": d("0.500000"),
    }
    values.update(overrides)
    return module.TeamSpecialistResearchDepthScoreConfig(**values)


def depth_input(**overrides: object):
    module = api()
    values = {
        "team_key": "team_alpha",
        "specialist_key": "specialist_alpha",
        "category_key": "category_macro",
        "evidence_item_count": d("6.000000"),
        "viewpoint_count": d("3.000000"),
        "contradiction_check_count": d("2.000000"),
        "synthesis_quality_score": d("0.900000"),
        "rank_context_score": d("0.900000"),
        "stale_evidence_ratio": d("0.100000"),
    }
    values.update(overrides)
    return module.TeamSpecialistResearchDepthInput(**values)


def build_report(*rows: object, cfg=None, generated_at: datetime = NOW):
    module = api()
    return module.build_team_specialist_research_depth_score_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def test_public_api_declares_readonly_contract() -> None:
    module = api()

    assert module.DEFAULT_TEAM_SPECIALIST_RESEARCH_DEPTH_SCORE_CONFIG_VERSION == (
        "team-specialist-research-depth-score-v1"
    )
    assert module.TEAM_SPECIALIST_RESEARCH_DEPTH_SCORE_FACTORS == (
        "evidence_depth",
        "viewpoint_depth",
        "contradiction_depth",
        "synthesis_quality",
        "rank_context",
        "freshness",
    )
    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_RESEARCH_DEPTH_SCORE_CONFIG_VERSION",
        "TEAM_SPECIALIST_RESEARCH_DEPTH_SCORE_FACTORS",
        "TeamSpecialistResearchDepthScoreConfig",
        "TeamSpecialistResearchDepthInput",
        "TeamSpecialistResearchDepthReasonCodeCount",
        "TeamSpecialistResearchDepthRow",
        "TeamSpecialistResearchDepthReport",
        "build_team_specialist_research_depth_score_report",
        "team_specialist_research_depth_score_payload",
    )

    defaults = {
        field.name: field.default
        for field in fields(module.TeamSpecialistResearchDepthScoreConfig)
    }
    assert defaults["paper_only"] is True
    assert defaults["report_only"] is True
    assert defaults["readonly"] is True


def test_deep_research_passes_with_decimal_rollups() -> None:
    result = build_report(depth_input())

    assert result.report_status == "pass"
    assert result.item_count == d("1.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.average_research_depth_score == d("0.965000")
    assert result.minimum_research_depth_score == d("0.965000")
    assert result.reason_code_counts == (
        api().TeamSpecialistResearchDepthReasonCodeCount(
            "team_specialist_research_depth_pass",
            d("1.000000"),
        ),
    )

    row = result.rows[0]
    assert row.rank == d("1.000000")
    assert row.evidence_depth_ratio == d("1.000000")
    assert row.viewpoint_depth_ratio == d("1.000000")
    assert row.contradiction_depth_ratio == d("1.000000")
    assert row.freshness_score == d("0.900000")
    assert row.research_depth_score == d("0.965000")
    assert row.status == "pass"
    assert row.reason_codes == ("team_specialist_research_depth_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_stale_otherwise_deep_research_watches() -> None:
    result = build_report(
        depth_input(
            stale_evidence_ratio=d("0.400000"),
            synthesis_quality_score=d("0.950000"),
            rank_context_score=d("0.950000"),
        ),
    )

    row = result.rows[0]
    assert row.freshness_score == d("0.600000")
    assert row.research_depth_score == d("0.965000")
    assert row.status == "watch"
    assert row.reason_codes == ("stale_evidence_depth",)
    assert result.report_status == "watch"
    assert result.watch_count == d("1.000000")


def test_shallow_research_blocks_candidate_sorting_support() -> None:
    result = build_report(
        depth_input(
            evidence_item_count=d("1.000000"),
            viewpoint_count=d("1.000000"),
            contradiction_check_count=d("0.000000"),
            synthesis_quality_score=d("0.500000"),
            rank_context_score=d("0.500000"),
            stale_evidence_ratio=d("0.600000"),
        ),
    )

    row = result.rows[0]
    assert row.evidence_depth_ratio == d("0.250000")
    assert row.viewpoint_depth_ratio == d("0.500000")
    assert row.contradiction_depth_ratio == d("0.000000")
    assert row.research_depth_score == d("0.345000")
    assert row.status == "block"
    assert row.reason_codes == (
        "insufficient_evidence_depth",
        "insufficient_viewpoint_depth",
        "insufficient_contradiction_review",
        "stale_evidence_depth",
        "research_depth_score_block",
    )
    assert result.report_status == "block"
    assert result.block_count == d("1.000000")


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: depth_input(evidence_item_count=6),
            "evidence_item_count must be exactly Decimal",
        ),
        (
            lambda: depth_input(synthesis_quality_score=_DecimalSubclass("0.900000")),
            "synthesis_quality_score must be exactly Decimal",
        ),
        (
            lambda: config(evidence_depth_weight=0.3),
            "evidence_depth_weight must be exactly Decimal",
        ),
        (
            lambda: depth_input(stale_evidence_ratio=d("0.1000001")),
            "stale_evidence_ratio must use six decimal places or fewer",
        ),
    ),
)
def test_decimal_exact_type_validation_rejects_numeric_shortcuts(
    factory: Any,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()


def test_public_payload_rejects_leaky_identifiers_and_live_surface_terms() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public"):
        depth_input(team_key="candidate_abc123")
    with pytest.raises(ValueError, match="unsafe public"):
        depth_input(specialist_key="wallet_auth")
    with pytest.raises(ValueError, match="unsafe public"):
        depth_input(category_key="https://example.invalid/case")

    result = build_report(depth_input())
    payload = dict(result.payload)
    payload["market_id"] = "raw-market-id"
    with pytest.raises(ValueError, match="unsafe public"):
        module.team_specialist_research_depth_score_payload(payload)

    assert_public_payload_has_no_forbidden_surface(result.payload)


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    module = api()
    result = build_report(depth_input())
    values = (
        config(),
        depth_input(),
        result.reason_code_counts[0],
        result.rows[0],
        result,
    )

    for value in values:
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        module.TeamSpecialistResearchDepthScoreConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        depth_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result.rows[0], readonly=False)


def test_payload_is_deterministic_and_json_safe() -> None:
    first = build_report(
        depth_input(team_key="team_b", specialist_key="specialist_b", category_key="category_b"),
        depth_input(team_key="team_a", specialist_key="specialist_a", category_key="category_a"),
    )
    second = build_report(
        depth_input(team_key="team_a", specialist_key="specialist_a", category_key="category_a"),
        depth_input(team_key="team_b", specialist_key="specialist_b", category_key="category_b"),
    )

    assert tuple((row.team_key, row.specialist_key, row.category_key) for row in first.rows) == (
        ("team_a", "specialist_a", "category_a"),
        ("team_b", "specialist_b", "category_b"),
    )
    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    json.dumps(first.payload, sort_keys=True)
    _assert_no_decimal_objects(first.payload)
    _assert_no_non_decimal_public_numbers(first)
    assert_public_payload_has_no_forbidden_surface(first.payload)


def test_report_and_digest_consistency_rejects_tampering() -> None:
    result = build_report(
        depth_input(team_key="team_pass", specialist_key="specialist_a", category_key="cat_a"),
        depth_input(
            team_key="team_watch",
            specialist_key="specialist_b",
            category_key="cat_b",
            stale_evidence_ratio=d("0.400000"),
        ),
        depth_input(
            team_key="team_block",
            specialist_key="specialist_c",
            category_key="cat_c",
            evidence_item_count=d("1.000000"),
        ),
    )

    assert result.report_status == "block"
    assert result.item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count"):
        replace(
            result,
            pass_count=d("2.000000"),
            derived_validation_digest=result.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="rows"):
        replace(result, rows=tuple(reversed(result.rows)))


def test_module_has_no_network_storage_or_live_trading_dependencies() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
        "websocket",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "exec", "eval", "compile"}
    assert imported_roots.isdisjoint(forbidden_import_roots)


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "candidate",
        "market",
        "slug",
        "question",
        "http://",
        "https://",
        "://",
        "source_ref",
        "source_url",
        "source_text",
        "url",
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


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if type(value) is Decimal:
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public dataclass contains non-Decimal number: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
