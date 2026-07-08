from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_outcome_dependency_graph_report import (
    DEFAULT_RESEARCH_MARKET_OUTCOME_DEPENDENCY_GRAPH_REPORT_VERSION,
    ResearchMarketOutcomeDependencyGraphConfig,
    ResearchMarketOutcomeDependencyGraphObservation,
    ResearchMarketOutcomeDependencyGraphPairRow,
    ResearchMarketOutcomeDependencyGraphReasonCodeCount,
    ResearchMarketOutcomeDependencyGraphReport,
    build_research_market_outcome_dependency_graph_report,
    research_market_outcome_dependency_graph_report_digest,
    research_market_outcome_dependency_graph_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_market_outcome_dependency_graph_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketOutcomeDependencyGraphConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_MARKET_OUTCOME_DEPENDENCY_GRAPH_REPORT_VERSION,
        "event_overlap_watch": d("0.500000"),
        "event_overlap_block": d("0.800000"),
        "resolution_overlap_watch": d("0.500000"),
        "resolution_overlap_block": d("0.800000"),
        "evidence_overlap_watch": d("0.400000"),
        "evidence_overlap_block": d("0.700000"),
        "semantic_overlap_watch": d("0.450000"),
        "semantic_overlap_block": d("0.750000"),
        "timing_overlap_watch": d("0.500000"),
        "timing_overlap_block": d("0.800000"),
    }
    values.update(overrides)
    return ResearchMarketOutcomeDependencyGraphConfig(**values)


def observation(
    left_key: str = "left-internal",
    right_key: str = "right-internal",
    *,
    event_overlap_ratio: Decimal = d("0.100000"),
    resolution_overlap_ratio: Decimal = d("0.100000"),
    evidence_overlap_ratio: Decimal = d("0.100000"),
    semantic_overlap_ratio: Decimal = d("0.100000"),
    timing_overlap_ratio: Decimal = d("0.100000"),
    hard_dependency_flag: bool = False,
    duplicate_research_flag: bool = False,
    correlation_crowding_flag: bool = False,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketOutcomeDependencyGraphObservation:
    return ResearchMarketOutcomeDependencyGraphObservation(
        left_key=left_key,
        right_key=right_key,
        event_overlap_ratio=event_overlap_ratio,
        resolution_overlap_ratio=resolution_overlap_ratio,
        evidence_overlap_ratio=evidence_overlap_ratio,
        semantic_overlap_ratio=semantic_overlap_ratio,
        timing_overlap_ratio=timing_overlap_ratio,
        hard_dependency_flag=hard_dependency_flag,
        duplicate_research_flag=duplicate_research_flag,
        correlation_crowding_flag=correlation_crowding_flag,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchMarketOutcomeDependencyGraphObservation,
    cfg: ResearchMarketOutcomeDependencyGraphConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketOutcomeDependencyGraphReport:
    return build_research_market_outcome_dependency_graph_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list | tuple):
        for item in value:
            assert_no_float(item)


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for key, item in value.items():
            values.append(key)
            values.extend(walk_values(item))
    elif isinstance(value, list | tuple):
        for item in value:
            values.extend(walk_values(item))
    else:
        values.append(value)
    return tuple(values)


def test_pass_report_uses_only_public_labels_and_decimal_payload_strings() -> None:
    dependency_report = report(
        observation(
            "raw-candidate-a",
            "market-slug-b",
            reason_codes=("manual_reviewed",),
        ),
    )

    assert is_dataclass(dependency_report)
    assert dependency_report.generated_at == GENERATED_AT
    assert dependency_report.config_version == (
        DEFAULT_RESEARCH_MARKET_OUTCOME_DEPENDENCY_GRAPH_REPORT_VERSION
    )
    assert dependency_report.pair_count == d("1.000000")
    assert dependency_report.pass_count == d("1.000000")
    assert dependency_report.watch_count == ZERO
    assert dependency_report.block_count == ZERO
    assert dependency_report.status == "pass"
    assert dependency_report.reason_codes == (
        "outcome_dependency_graph_report_pass",
        "dependency_overlap_clear",
    )
    assert dependency_report.paper_only is True
    assert dependency_report.report_only is True
    assert dependency_report.readonly is True

    row = dependency_report.pair_rows[0]
    assert row.pair_label == "pair-000001"
    assert row.left_node_label == "node-000001"
    assert row.right_node_label == "node-000002"
    assert row.dependency_status == "pass"
    assert row.dependency_score == d("0.100000")
    assert row.reason_codes == ("dependency_overlap_clear", "input_manual_reviewed")

    payload = research_market_outcome_dependency_graph_report_payload(dependency_report)
    encoded = json.dumps(payload, sort_keys=True)
    assert payload["pair_count"] == "1.000000"
    assert payload["pair_rows"][0]["dependency_score"] == "0.100000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["pair_rows"][0]["left_node_label"] == "node-000001"
    assert "raw-candidate-a" not in encoded
    assert "market-slug-b" not in encoded
    assert_no_float(payload)


def test_empty_input_blocks_with_no_inputs_reason_count() -> None:
    dependency_report = report()

    assert dependency_report.status == "block"
    assert dependency_report.pair_count == ZERO
    assert dependency_report.pass_count == ZERO
    assert dependency_report.watch_count == ZERO
    assert dependency_report.block_count == ZERO
    assert dependency_report.mean_dependency_score == ZERO
    assert dependency_report.max_dependency_score == ZERO
    assert dependency_report.reason_codes == ("outcome_dependency_graph_no_inputs",)
    assert dependency_report.reason_code_counts == (
        ResearchMarketOutcomeDependencyGraphReasonCodeCount(
            reason_code="outcome_dependency_graph_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert dependency_report.pair_rows == ()


def test_watch_and_block_statuses_roll_up_from_overlap_and_flags() -> None:
    dependency_report = report(
        observation(
            "watch-a",
            "watch-b",
            event_overlap_ratio=d("0.600000"),
            correlation_crowding_flag=True,
        ),
        observation(
            "block-a",
            "block-b",
            resolution_overlap_ratio=d("0.900000"),
            duplicate_research_flag=True,
        ),
    )

    assert dependency_report.status == "block"
    assert dependency_report.pass_count == ZERO
    assert dependency_report.watch_count == d("1.000000")
    assert dependency_report.block_count == d("1.000000")
    assert dependency_report.duplicate_research_count == d("1.000000")
    assert dependency_report.correlation_crowding_count == d("1.000000")
    assert dependency_report.mean_dependency_score == d("0.800000")
    assert dependency_report.reason_codes == (
        "outcome_dependency_graph_report_block",
        "duplicate_research_block",
        "resolution_overlap_block",
        "correlation_crowding_watch",
        "event_overlap_watch",
    )

    first, second = dependency_report.pair_rows
    assert first.dependency_status == "block"
    assert first.dependency_score == ONE
    assert first.reason_codes == (
        "duplicate_research_block",
        "resolution_overlap_block",
    )
    assert second.dependency_status == "watch"
    assert second.reason_codes == (
        "correlation_crowding_watch",
        "event_overlap_watch",
    )


def test_hard_dependency_flag_blocks_even_with_low_ratios() -> None:
    dependency_report = report(
        observation(
            "hard-a",
            "hard-b",
            hard_dependency_flag=True,
            reason_codes=("same_resolution_path",),
        ),
    )

    row = dependency_report.pair_rows[0]
    assert dependency_report.status == "block"
    assert dependency_report.hard_dependency_count == d("1.000000")
    assert row.dependency_status == "block"
    assert row.dependency_score == ONE
    assert row.reason_codes == (
        "hard_dependency_block",
        "input_same_resolution_path",
    )


def test_deterministic_rows_counts_payload_and_digest_are_consistent() -> None:
    dependency_report = report(
        observation(
            "z-left",
            "z-right",
            semantic_overlap_ratio=d("0.800000"),
        ),
        observation(
            "a-left",
            "a-right",
            event_overlap_ratio=d("0.600000"),
            reason_codes=("analyst_tag",),
        ),
        observation(
            "m-left",
            "m-right",
            evidence_overlap_ratio=d("0.700000"),
        ),
    )

    payload = research_market_outcome_dependency_graph_report_payload(dependency_report)
    digest = research_market_outcome_dependency_graph_report_digest(dependency_report)
    encoded_payload = json.dumps(payload, sort_keys=True)
    encoded_digest = json.dumps(digest, sort_keys=True)

    assert tuple(row.pair_label for row in dependency_report.pair_rows) == (
        "pair-000003",
        "pair-000002",
        "pair-000001",
    )
    assert tuple(row.dependency_status for row in dependency_report.pair_rows) == (
        "block",
        "block",
        "watch",
    )
    assert dependency_report.reason_code_counts == (
        ResearchMarketOutcomeDependencyGraphReasonCodeCount(
            reason_code="event_overlap_watch",
            count=d("1.000000"),
        ),
        ResearchMarketOutcomeDependencyGraphReasonCodeCount(
            reason_code="evidence_overlap_block",
            count=d("1.000000"),
        ),
        ResearchMarketOutcomeDependencyGraphReasonCodeCount(
            reason_code="input_analyst_tag",
            count=d("1.000000"),
        ),
        ResearchMarketOutcomeDependencyGraphReasonCodeCount(
            reason_code="outcome_dependency_graph_report_block",
            count=d("1.000000"),
        ),
        ResearchMarketOutcomeDependencyGraphReasonCodeCount(
            reason_code="semantic_overlap_block",
            count=d("1.000000"),
        ),
    )
    assert digest["status"] == payload["status"] == dependency_report.status
    assert digest["pair_count"] == payload["pair_count"]
    assert digest["reason_codes"] == payload["reason_codes"]
    assert digest["reason_code_counts"] == payload["reason_code_counts"]
    assert digest["pair_rows"][0]["pair_label"] == payload["pair_rows"][0]["pair_label"]
    assert "z-left" not in encoded_payload
    assert "a-right" not in encoded_digest
    assert_no_float(payload)
    assert_no_float(digest)


def test_decimal_and_type_rejections_are_strict() -> None:
    with pytest.raises(ValueError, match="event_overlap_watch"):
        config(event_overlap_watch=d("-0.000001"))
    with pytest.raises(ValueError, match="event_overlap_watch"):
        config(event_overlap_watch=d("0.900000"), event_overlap_block=d("0.800000"))
    with pytest.raises(ValueError, match="semantic_overlap_block"):
        config(semantic_overlap_block=_DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="event_overlap_ratio"):
        observation(event_overlap_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolution_overlap_ratio"):
        observation(resolution_overlap_ratio=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_overlap_ratio"):
        observation(evidence_overlap_ratio=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="hard_dependency_flag"):
        observation(hard_dependency_flag=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            observation(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    normalized_time_report = report(
        observation(),
        generated_at=datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    assert normalized_time_report.generated_at == GENERATED_AT


def test_public_leak_rejection_covers_values_keys_and_tampered_payloads() -> None:
    dependency_report = report(observation("private-left", "private-right"))
    payload = research_market_outcome_dependency_graph_report_payload(dependency_report)

    assert not any(
        isinstance(value, str)
        and any(
            marker in value.lower()
            for marker in (
                "private-left",
                "private-right",
                "raw",
                "candidate",
                "market_slug",
                "question",
                "source_url",
                "dsn",
                "wallet",
                "order",
                "position",
                "buy",
                "sell",
                "recommend",
            )
        )
        for value in walk_values(payload)
    )

    object.__setattr__(
        dependency_report.pair_rows[0],
        "left_node_label",
        "raw-candidate-123",
    )
    with pytest.raises(ValueError, match="unsafe public value"):
        research_market_outcome_dependency_graph_report_payload(dependency_report)

    clean_report = report(observation("clean-left", "clean-right"))
    object.__setattr__(
        clean_report.pair_rows[0],
        "reason_codes",
        ("source_url_leak",),
    )
    with pytest.raises(ValueError, match="unsafe public value"):
        research_market_outcome_dependency_graph_report_payload(clean_report)


def test_hard_flags_frozen_dataclasses_and_manual_consistency_validation() -> None:
    dependency_report = report(
        observation("frozen-left", "frozen-right"),
        observation(
            "frozen-watch-left",
            "frozen-watch-right",
            event_overlap_ratio=d("0.600000"),
        ),
    )

    assert is_dataclass(ResearchMarketOutcomeDependencyGraphConfig)
    assert is_dataclass(ResearchMarketOutcomeDependencyGraphObservation)
    assert is_dataclass(ResearchMarketOutcomeDependencyGraphPairRow)
    assert is_dataclass(ResearchMarketOutcomeDependencyGraphReasonCodeCount)
    assert is_dataclass(ResearchMarketOutcomeDependencyGraphReport)
    with pytest.raises(FrozenInstanceError):
        dependency_report.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        dependency_report.pair_rows[0].dependency_score = ONE  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(dependency_report, report_only=False)
    with pytest.raises(ValueError, match="pair_count"):
        replace(dependency_report, pair_count=d("3.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(dependency_report, status="block")
    with pytest.raises(ValueError, match="pair_rows"):
        replace(dependency_report, pair_rows=tuple(reversed(dependency_report.pair_rows)))

    for item in (
        dependency_report,
        *dependency_report.pair_rows,
        *dependency_report.reason_code_counts,
    ):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_payload_revalidates_after_decimal_time_and_shape_tampering() -> None:
    dependency_report = report(observation("tampered-decimal-left", "tampered-decimal-right"))
    object.__setattr__(dependency_report.pair_rows[0], "dependency_score", d("0.1000000"))
    with pytest.raises(ValueError, match="six decimal"):
        research_market_outcome_dependency_graph_report_payload(dependency_report)

    dependency_report = report(observation("tampered-time-left", "tampered-time-right"))
    object.__setattr__(
        dependency_report,
        "generated_at",
        datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="UTC"):
        research_market_outcome_dependency_graph_report_payload(dependency_report)

    dependency_report = report(observation("tampered-shape-left", "tampered-shape-right"))
    row_payload = research_market_outcome_dependency_graph_report_payload(dependency_report)[
        "pair_rows"
    ][0]
    object.__setattr__(dependency_report, "pair_rows", (row_payload,))
    with pytest.raises(ValueError, match="pair_rows"):
        research_market_outcome_dependency_graph_report_payload(dependency_report)


def test_public_statuses_exports_and_static_report_only_surface() -> None:
    import polymarket_alpha_lab.research_market_outcome_dependency_graph_report as module

    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_OUTCOME_DEPENDENCY_GRAPH_REPORT_VERSION",
        "ResearchMarketOutcomeDependencyGraphConfig",
        "ResearchMarketOutcomeDependencyGraphObservation",
        "ResearchMarketOutcomeDependencyGraphPairRow",
        "ResearchMarketOutcomeDependencyGraphReasonCodeCount",
        "ResearchMarketOutcomeDependencyGraphReport",
        "build_research_market_outcome_dependency_graph_report",
        "research_market_outcome_dependency_graph_report_digest",
        "research_market_outcome_dependency_graph_report_payload",
    )
    dependency_report = report(
        observation("pass-left", "pass-right"),
        observation("watch-left", "watch-right", timing_overlap_ratio=d("0.600000")),
        observation("block-left", "block-right", hard_dependency_flag=True),
    )
    statuses = {dependency_report.status}
    statuses.update(row.dependency_status for row in dependency_report.pair_rows)
    assert statuses <= {"pass", "watch", "block"}
    assert "blocked" not in json.dumps(
        research_market_outcome_dependency_graph_report_payload(dependency_report),
        sort_keys=True,
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "order",
        "cancel",
        "replace",
        "private_key",
        "api_key",
        "secret",
        "position",
        "trade",
        "stake",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__", "asdict"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
