from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_event_cluster_attention_budget_report import (
    DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_ATTENTION_BUDGET_REPORT_CONFIG_VERSION,
    ResearchStrategyEventClusterAttentionBudgetCluster,
    ResearchStrategyEventClusterAttentionBudgetConfig,
    ResearchStrategyEventClusterAttentionBudgetReport,
    ResearchStrategyEventClusterAttentionBudgetRow,
    build_research_strategy_event_cluster_attention_budget_report,
    research_strategy_event_cluster_attention_budget_report_digest,
    research_strategy_event_cluster_attention_budget_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_event_cluster_attention_budget_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyEventClusterAttentionBudgetConfig:
    values = {
        "evidence_urgency_weight": d("0.350000"),
        "timing_risk_weight": d("0.250000"),
        "contradiction_pressure_weight": d("0.250000"),
        "domain_memory_gap_weight": d("0.150000"),
        "watch_attention_pressure_threshold": d("0.350000"),
        "block_attention_pressure_threshold": d("0.700000"),
        "watch_attention_share_threshold": d("0.250000"),
        "block_attention_share_threshold": d("0.400000"),
    }
    values.update(overrides)
    return ResearchStrategyEventClusterAttentionBudgetConfig(**values)


def cluster(
    cluster_ref: str = "private-cluster-alpha",
    *,
    evidence_urgency_score: Decimal = d("0.200000"),
    timing_risk_score: Decimal = d("0.200000"),
    contradiction_pressure_score: Decimal = d("0.200000"),
    domain_memory_gap_score: Decimal = d("0.200000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyEventClusterAttentionBudgetCluster:
    return ResearchStrategyEventClusterAttentionBudgetCluster(
        cluster_ref=cluster_ref,
        evidence_urgency_score=evidence_urgency_score,
        timing_risk_score=timing_risk_score,
        contradiction_pressure_score=contradiction_pressure_score,
        domain_memory_gap_score=domain_memory_gap_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *clusters: ResearchStrategyEventClusterAttentionBudgetCluster,
    cfg: ResearchStrategyEventClusterAttentionBudgetConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyEventClusterAttentionBudgetReport:
    return build_research_strategy_event_cluster_attention_budget_report(
        clusters,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_attention_budget_allocates_pressure_deterministically() -> None:
    pass_cluster = cluster("private-pass")
    watch_cluster = cluster(
        "private-watch",
        evidence_urgency_score=d("0.700000"),
        timing_risk_score=d("0.600000"),
        contradiction_pressure_score=d("0.400000"),
        domain_memory_gap_score=d("0.300000"),
    )
    block_cluster = cluster(
        "private-block",
        evidence_urgency_score=d("0.900000"),
        timing_risk_score=d("0.800000"),
        contradiction_pressure_score=d("0.700000"),
        domain_memory_gap_score=d("0.500000"),
    )

    first = report(pass_cluster, watch_cluster, block_cluster)
    second = report(block_cluster, watch_cluster, pass_cluster)

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_ATTENTION_BUDGET_REPORT_CONFIG_VERSION
    )
    assert first.cluster_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.total_attention_pressure == d("1.505000")
    assert first.max_attention_pressure == d("0.765000")
    assert first.average_attention_pressure == d("0.501667")
    assert first.max_attention_share == d("0.508306")
    assert first.status == "block"
    assert first.reason_codes == (
        "attention_share_block",
        "attention_pressure_block",
        "attention_share_watch",
        "attention_pressure_watch",
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert tuple(row.row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    blocked = first.rows[0]
    assert blocked.evidence_urgency_score == d("0.900000")
    assert blocked.timing_risk_score == d("0.800000")
    assert blocked.contradiction_pressure_score == d("0.700000")
    assert blocked.domain_memory_gap_score == d("0.500000")
    assert blocked.attention_pressure == d("0.765000")
    assert blocked.attention_share == d("0.508306")
    assert blocked.reason_codes == (
        "attention_share_block",
        "attention_pressure_block",
    )
    assert_digest(blocked.validation_digest)
    assert_digest(first.validation_digest)

    payload = research_strategy_event_cluster_attention_budget_report_payload(first)
    assert payload == research_strategy_event_cluster_attention_budget_report_payload(
        second,
    )
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    assert "private-pass" not in encoded
    assert "private-watch" not in encoded
    assert "private-block" not in encoded
    assert "market-" not in encoded
    assert "source" not in encoded.lower()
    assert payload["cluster_count"] == "3.000000"
    assert payload["rows"][0]["row_number"] == "1.000000"
    assert payload["rows"][0]["attention_share"] == "0.508306"
    assert payload["rows"][0]["validation_digest"] == blocked.validation_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    digest = research_strategy_event_cluster_attention_budget_report_digest(first)
    assert "rows" not in digest
    assert digest["cluster_count"] == payload["cluster_count"]
    assert digest["status"] == "block"
    assert digest["validation_digest"] == first.validation_digest
    assert_no_float_or_int_values(digest)


def test_empty_report_blocks_without_cluster_identifiers() -> None:
    result = report()

    assert result.cluster_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.total_attention_pressure == ZERO
    assert result.max_attention_pressure is None
    assert result.average_attention_pressure is None
    assert result.max_attention_share is None
    assert result.status == "block"
    assert result.reason_codes == ("attention_budget_no_clusters",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)


def test_decimal_only_frozen_flags_and_input_validation() -> None:
    result = report(cluster("private-frozen"))

    assert is_dataclass(ResearchStrategyEventClusterAttentionBudgetConfig)
    assert is_dataclass(ResearchStrategyEventClusterAttentionBudgetCluster)
    assert is_dataclass(ResearchStrategyEventClusterAttentionBudgetRow)
    assert is_dataclass(ResearchStrategyEventClusterAttentionBudgetReport)
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].attention_pressure = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        cluster(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="evidence_urgency_score"):
        cluster(evidence_urgency_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timing_risk_score"):
        cluster(timing_risk_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_pressure_score"):
        cluster(contradiction_pressure_score=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="cluster_ref values must be unique"):
        report(cluster("private-dupe"), cluster("private-dupe"))
    with pytest.raises(ValueError, match="generated_at"):
        report(cluster("private-time"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            cluster("private-time"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="block_attention_pressure_threshold"):
        config(block_attention_pressure_threshold=d("0.350000"))
    with pytest.raises(ValueError, match="attention weights must sum"):
        config(domain_memory_gap_weight=d("0.100000"))

    for item in (result, *result.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, tuple):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_validation_digest_and_payload_reject_tampering() -> None:
    result = report(cluster("private-consistent"))
    row = result.rows[0]

    with pytest.raises(ValueError, match="attention_pressure must match"):
        replace(row, attention_pressure=row.attention_pressure + d("0.100000"))
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="pass")
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(result, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(
            result,
            rows=(
                report(cluster("private-zeta")).rows[0],
                row,
            ),
        )
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)

    payload = research_strategy_event_cluster_attention_budget_report_payload(result)
    assert research_strategy_event_cluster_attention_budget_report_payload(payload) == payload
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_event_cluster_attention_budget_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_event_cluster_attention_budget_report_payload(
            {**payload, "candidate" "_" "id": "private-consistent"},
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_event_cluster_attention_budget_report_payload(
            {**payload, "market" "_" "slug": "market-hidden"},
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_event_cluster_attention_budget_report_payload(
            {**payload, "source_text": "hidden"},
        )
    with pytest.raises(ValueError, match="numeric"):
        research_strategy_event_cluster_attention_budget_report_payload(
            {**payload, "cluster_count": 1},
        )


def test_public_exports_and_static_report_only_surface() -> None:
    import polymarket_alpha_lab.research_strategy_event_cluster_attention_budget_report as module

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_ATTENTION_BUDGET_REPORT_CONFIG_VERSION",
        "ResearchStrategyEventClusterAttentionBudgetCluster",
        "ResearchStrategyEventClusterAttentionBudgetConfig",
        "ResearchStrategyEventClusterAttentionBudgetReport",
        "ResearchStrategyEventClusterAttentionBudgetRow",
        "build_research_strategy_event_cluster_attention_budget_report",
        "research_strategy_event_cluster_attention_budget_report_digest",
        "research_strategy_event_cluster_attention_budget_report_payload",
    )
    assert module.PUBLIC_STATUSES == ("pass", "watch", "block")

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "reco" "mmend",
        "siz" "ing",
        "b" "uy",
        "s" "ell",
        "wal" "let",
        "or" "der",
        "li" "ve " "trading",
    )
    assert [term for term in forbidden_terms if term in lowered] == []

    tree = ast.parse(source)
    forbidden_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "delete",
        "execute",
        "insert",
        "login",
        "open",
        "post",
        "request",
        "submit",
        "update",
        "urlopen",
        "write",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & forbidden_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_calls
