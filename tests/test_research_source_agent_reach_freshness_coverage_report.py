from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_agent_reach_freshness_coverage_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def api() -> Any:
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.research_source_agent_reach_freshness_coverage_report",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"expected report module to exist: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "watch_successful_retrieval_ratio": d("0.800000"),
        "block_successful_retrieval_ratio": d("0.500000"),
        "watch_recency_lag_seconds": d("86400.000000"),
        "block_recency_lag_seconds": d("259200.000000"),
        "watch_authority_confidence": d("0.700000"),
        "block_authority_confidence": d("0.400000"),
        "watch_conflict_coverage_ratio": d("0.750000"),
        "block_conflict_coverage_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchSourceAgentReachFreshnessCoverageConfig(**values)


def source_class_input(
    source_class: str,
    *,
    retrieval_attempt_count: Decimal = d("5.000000"),
    successful_retrieval_count: Decimal = d("5.000000"),
    recency_lag_seconds: Decimal = d("900.000000"),
    authority_confidence: Decimal = d("0.950000"),
    conflict_count: Decimal = d("2.000000"),
    covered_conflict_count: Decimal = d("2.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceAgentReachFreshnessCoverageInput(
        source_class=source_class,
        retrieval_attempt_count=retrieval_attempt_count,
        successful_retrieval_count=successful_retrieval_count,
        recency_lag_seconds=recency_lag_seconds,
        authority_confidence=authority_confidence,
        conflict_count=conflict_count,
        covered_conflict_count=covered_conflict_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_agent_reach_freshness_coverage_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _walk_payload_values(value: object) -> list[object]:
    values: list[object] = [value]
    if type(value) is dict:
        for key, item in value.items():
            values.extend(_walk_payload_values(key))
            values.extend(_walk_payload_values(item))
    elif type(value) is list:
        for item in value:
            values.extend(_walk_payload_values(item))
    return values


def _assert_payload_has_no_raw_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        pytest.fail(f"public payload leaked raw numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            _assert_payload_has_no_raw_numbers(item)
    elif type(value) is list:
        for item in value:
            _assert_payload_has_no_raw_numbers(item)


def _assert_payload_has_no_forbidden_text(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True).casefold()
    for forbidden in (
        "raw candidate",
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "www.",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live trading",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in rendered


def test_source_class_coverage_scoring_rolls_pass_watch_block_rows() -> None:
    module = api()
    report = build_report(
        source_class_input("official"),
        source_class_input(
            "news",
            retrieval_attempt_count=d("4.000000"),
            successful_retrieval_count=d("3.000000"),
            recency_lag_seconds=d("90000.000000"),
            authority_confidence=d("0.650000"),
            conflict_count=d("4.000000"),
            covered_conflict_count=d("3.000000"),
        ),
        source_class_input(
            "social",
            retrieval_attempt_count=d("4.000000"),
            successful_retrieval_count=d("1.000000"),
            recency_lag_seconds=d("300000.000000"),
            authority_confidence=d("0.350000"),
            conflict_count=d("4.000000"),
            covered_conflict_count=d("1.000000"),
        ),
    )

    assert type(report) is module.ResearchSourceAgentReachFreshnessCoverageReport
    assert is_dataclass(report)
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.attention_count == d("2.000000")
    assert report.avg_successful_retrieval_ratio == d("0.666667")
    assert report.max_recency_lag_seconds == d("300000.000000")
    assert report.avg_authority_confidence == d("0.650000")
    assert report.avg_conflict_coverage_ratio == d("0.666667")
    assert report.min_freshness_coverage_score == d("0.000000")
    assert report.reason_codes == (
        "successful_retrieval_ratio_below_block_threshold",
        "successful_retrieval_ratio_below_watch_threshold",
        "recency_lag_above_block_threshold",
        "recency_lag_above_watch_threshold",
        "authority_confidence_below_block_threshold",
        "authority_confidence_below_watch_threshold",
        "conflict_coverage_below_block_threshold",
        "freshness_coverage_block",
        "freshness_coverage_watch",
    )

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.source_class for row in report.rows) == ("social", "news", "official")
    assert tuple(row.successful_retrieval_ratio for row in report.rows) == (
        d("0.250000"),
        d("0.750000"),
        d("1.000000"),
    )
    assert tuple(row.conflict_coverage_ratio for row in report.rows) == (
        d("0.250000"),
        d("0.750000"),
        d("1.000000"),
    )
    assert tuple(row.freshness_coverage_score for row in report.rows) == (
        d("0.000000"),
        d("0.500000"),
        d("0.950000"),
    )
    assert report.rows[0].reason_codes == (
        "successful_retrieval_ratio_below_block_threshold",
        "recency_lag_above_block_threshold",
        "authority_confidence_below_block_threshold",
        "conflict_coverage_below_block_threshold",
        "freshness_coverage_block",
    )
    assert report.rows[1].reason_codes == (
        "successful_retrieval_ratio_below_watch_threshold",
        "recency_lag_above_watch_threshold",
        "authority_confidence_below_watch_threshold",
        "freshness_coverage_watch",
    )
    assert report.rows[2].reason_codes == ("freshness_coverage_pass",)


def test_stale_retrieval_recency_lag_penalizes_otherwise_covered_sources() -> None:
    report = build_report(
        source_class_input("watch-lag", recency_lag_seconds=d("90000.000000")),
        source_class_input("block-lag", recency_lag_seconds=d("300000.000000")),
    )

    block_row, watch_row = report.rows
    assert report.status == "block"
    assert block_row.source_class == "block-lag"
    assert block_row.status == "block"
    assert block_row.recency_freshness_score == d("0.000000")
    assert block_row.freshness_coverage_score == d("0.000000")
    assert block_row.reason_codes == (
        "recency_lag_above_block_threshold",
        "freshness_coverage_block",
    )
    assert watch_row.source_class == "watch-lag"
    assert watch_row.status == "watch"
    assert watch_row.recency_freshness_score == d("0.500000")
    assert watch_row.freshness_coverage_score == d("0.500000")
    assert watch_row.reason_codes == (
        "recency_lag_above_watch_threshold",
        "freshness_coverage_watch",
    )


def test_public_payload_is_deterministic_sanitized_and_digest_validated() -> None:
    module = api()
    report_a = build_report(
        source_class_input("official"),
        source_class_input("news", successful_retrieval_count=d("4.000000")),
    )
    report_b = build_report(
        source_class_input("news", successful_retrieval_count=d("4.000000")),
        source_class_input("official"),
    )

    payload_a = module.research_source_agent_reach_freshness_coverage_report_public_payload(
        report_a,
    )
    payload_b = module.research_source_agent_reach_freshness_coverage_report_public_payload(
        report_b,
    )

    assert payload_a == payload_b
    assert payload_a["derived_validation_digest"] == report_a.derived_validation_digest
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert module.validate_research_source_agent_reach_freshness_coverage_report_public_payload(
        payload_a,
    )
    _assert_payload_has_no_raw_numbers(payload_a)
    _assert_payload_has_no_forbidden_text(payload_a)
    assert all(
        value not in ("candidate-123", "market-slug", "Will this leak?")
        for value in _walk_payload_values(payload_a)
    )

    tampered = dict(payload_a)
    tampered["pass_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_agent_reach_freshness_coverage_report_public_payload(
            tampered,
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)

    for unsafe_key in (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order_id",
        "trade_id",
        "live_trading_surface",
        "sizing_hint",
        "recommendation",
    ):
        unsafe = dict(payload_a)
        unsafe[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="public"):
            module.research_source_agent_reach_freshness_coverage_report_public_payload(
                unsafe,
            )

    for unsafe_value in (
        "raw candidate id abc",
        "https://example.test/source",
        "primary source_url",
        "wallet auth token",
        "order trade surface",
        "sizing recommendation",
    ):
        unsafe = dict(payload_a)
        unsafe["operator_note"] = unsafe_value
        with pytest.raises(ValueError, match="public"):
            module.research_source_agent_reach_freshness_coverage_report_public_payload(
                unsafe,
            )


def test_decimal_only_frozen_exact_types_hard_flags_and_custom_config_validation() -> None:
    module = api()
    report = build_report(source_class_input("official"))

    assert module.STATUSES == ("pass", "watch", "block")
    assert module.ResearchSourceAgentReachFreshnessCoverageConfig.__dataclass_params__.frozen
    assert module.ResearchSourceAgentReachFreshnessCoverageInput.__dataclass_params__.frozen
    assert module.ResearchSourceAgentReachFreshnessCoverageRow.__dataclass_params__.frozen
    assert module.ResearchSourceAgentReachFreshnessCoverageReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):
        type(
            "DerivedFreshnessCoverageConfig",
            (module.ResearchSourceAgentReachFreshnessCoverageConfig,),
            {},
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_agent_reach_freshness_coverage_report(
            (source_class_input("time"),),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="watch_successful_retrieval_ratio"):
        config(watch_successful_retrieval_ratio=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="block_recency_lag_seconds"):
        config(block_recency_lag_seconds=259200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="successful_retrieval_count"):
        source_class_input("int-count", successful_retrieval_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_confidence"):
        source_class_input("float-authority", authority_confidence=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="recency_lag_seconds"):
        source_class_input("subclass-lag", recency_lag_seconds=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="successful_retrieval_count"):
        source_class_input("too-many-successes", successful_retrieval_count=d("6.000000"))
    with pytest.raises(ValueError, match="covered_conflict_count"):
        source_class_input("too-many-conflicts", covered_conflict_count=d("3.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        source_class_input("flag", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="unsafe public"):
        source_class_input("market_slug_real")
    with pytest.raises(ValueError, match="unsafe public"):
        source_class_input("https://example.test/retrieval")

    strict_cfg = config(
        watch_recency_lag_seconds=d("100.000000"),
        block_recency_lag_seconds=d("200.000000"),
    )
    strict_report = build_report(
        source_class_input("custom", recency_lag_seconds=d("150.000000")),
        cfg=strict_cfg,
    )
    assert strict_report.status == "watch"
    assert strict_report.rows[0].reason_codes == (
        "recency_lag_above_watch_threshold",
        "freshness_coverage_watch",
    )

    with pytest.raises(ValueError, match="watch_recency_lag_seconds"):
        config(watch_recency_lag_seconds=d("259200.000000"))
    with pytest.raises(ValueError, match="block_successful_retrieval_ratio"):
        config(block_successful_retrieval_ratio=d("0.900000"))
    with pytest.raises(ValueError, match="block_authority_confidence"):
        config(block_authority_confidence=d("0.800000"))
    with pytest.raises(ValueError, match="block_conflict_coverage_ratio"):
        config(block_conflict_coverage_ratio=d("0.900000"))


def test_empty_report_is_block_report_only_and_module_has_no_runtime_surfaces() -> None:
    module = api()
    report = build_report()

    assert report.status == "block"
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("agent_reach_freshness_coverage_no_inputs",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.research_source_agent_reach_freshness_coverage_report_public_payload(
        report,
    )
    assert payload["rows"] == []
    assert payload["input_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_text(payload)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
