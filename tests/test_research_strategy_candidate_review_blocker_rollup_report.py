from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_strategy_candidate_review_blocker_rollup_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_candidate_review_blocker_rollup_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_CANDIDATE_REVIEW_BLOCKER_ROLLUP_REPORT_CONFIG_VERSION
        ),
    }
    values.update(overrides)
    return module.ResearchStrategyCandidateReviewBlockerRollupConfig(**values)


def blocker_input(
    module: Any,
    review_key: str = "review-alpha",
    *,
    evidence_status: str = "pass",
    source_coverage_status: str = "pass",
    cost_freshness_status: str = "pass",
    settlement_clarity_status: str = "pass",
    domain_memory_status: str = "pass",
    forecast_rationale_status: str = "pass",
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module.ResearchStrategyCandidateReviewBlockerInput(
        review_key=review_key,
        evidence_status=evidence_status,
        source_coverage_status=source_coverage_status,
        cost_freshness_status=cost_freshness_status,
        settlement_clarity_status=settlement_clarity_status,
        domain_memory_status=domain_memory_status,
        forecast_rationale_status=forecast_rationale_status,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    module: Any,
    *items: Any,
    config: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_candidate_review_blocker_rollup_report(
        items,
        config=cfg(module) if config is None else config,
        generated_at=generated_at,
    )


def assert_no_numeric_payload_values(value: Any) -> None:
    assert type(value) not in (int, float, Decimal)
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_numeric_payload_values(item)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def digest_from_payload(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("public_digest")
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_blocker_rollup_aggregates_sanitized_rows_payload_and_digest() -> None:
    module = api()
    passing = blocker_input(module, "alpha-pass-key")
    watched = blocker_input(
        module,
        "alpha-watch-key",
        evidence_status="watch",
        source_coverage_status="watch",
        domain_memory_status="watch",
    )
    blocked = blocker_input(
        module,
        "alpha-block-key",
        evidence_status="block",
        source_coverage_status="block",
        cost_freshness_status="watch",
        settlement_clarity_status="block",
        forecast_rationale_status="block",
    )

    report = build_report(module, watched, blocked, passing)
    permuted = build_report(module, passing, watched, blocked)
    payload = module.research_strategy_candidate_review_blocker_rollup_report_payload(
        report,
    )
    permuted_payload = (
        module.research_strategy_candidate_review_blocker_rollup_report_payload(
            permuted,
        )
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_CANDIDATE_REVIEW_BLOCKER_ROLLUP_REPORT_CONFIG_VERSION
    )
    assert report.review_count == d("3.000000")
    assert report.pass_count == ONE
    assert report.watch_count == ONE
    assert report.block_count == ONE
    assert report.status == "block"
    assert report.blocker_dimension_count == d("4.000000")
    assert report.watch_dimension_count == d("4.000000")
    assert report.attention_dimension_count == d("8.000000")
    assert report.evidence_block_count == ONE
    assert report.evidence_watch_count == ONE
    assert report.source_coverage_block_count == ONE
    assert report.source_coverage_watch_count == ONE
    assert report.cost_freshness_block_count == ZERO
    assert report.cost_freshness_watch_count == ONE
    assert report.settlement_clarity_block_count == ONE
    assert report.settlement_clarity_watch_count == ZERO
    assert report.domain_memory_block_count == ZERO
    assert report.domain_memory_watch_count == ONE
    assert report.forecast_rationale_block_count == ONE
    assert report.forecast_rationale_watch_count == ZERO
    assert report.mean_blocker_pressure_score == d("0.333333")
    assert report.max_blocker_pressure_score == d("0.750000")
    assert report.reason_codes == (
        "review_blocker_rollup_block",
        "evidence_block",
        "evidence_watch",
        "source_coverage_block",
        "source_coverage_watch",
        "cost_freshness_watch",
        "settlement_clarity_block",
        "domain_memory_watch",
        "forecast_rationale_block",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    blocked_row, watched_row, passing_row = report.rows
    assert blocked_row.row_number == ONE
    assert blocked_row.review_hash == hashlib.sha256(
        b"alpha-block-key",
    ).hexdigest()
    assert blocked_row.blocker_dimension_count == d("4.000000")
    assert blocked_row.watch_dimension_count == ONE
    assert blocked_row.blocker_pressure_score == d("0.750000")
    assert blocked_row.reason_codes == (
        "cost_freshness_watch",
        "evidence_block",
        "forecast_rationale_block",
        "settlement_clarity_block",
        "source_coverage_block",
    )
    assert watched_row.blocker_pressure_score == d("0.250000")
    assert passing_row.reason_codes == ("review_blocker_rollup_pass",)
    assert not hasattr(blocked_row, "review_key")

    assert payload == permuted_payload
    assert payload["review_count"] == "3.000000"
    assert payload["rows"][0]["row_number"] == "1.000000"
    assert payload["rows"][0]["blocker_pressure_score"] == "0.750000"
    assert payload["public_digest"] == report.public_digest
    assert report.public_digest == (
        module.research_strategy_candidate_review_blocker_rollup_report_digest(
            report,
        )
    )
    assert report.public_digest == digest_from_payload(payload)
    assert_digest(report.public_digest)
    assert "review_key" not in json.dumps(payload, sort_keys=True)
    assert "alpha-block-key" not in json.dumps(payload, sort_keys=True)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_numeric_payload_values(payload)


def test_empty_rollup_blocks_with_no_inputs_reason() -> None:
    module = api()

    report = build_report(
        module,
        generated_at=datetime(2026, 7, 8, 14, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    payload = module.research_strategy_candidate_review_blocker_rollup_report_payload(
        report,
    )

    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.review_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.blocker_dimension_count == ZERO
    assert report.watch_dimension_count == ZERO
    assert report.attention_dimension_count == ZERO
    assert report.mean_blocker_pressure_score == ZERO
    assert report.max_blocker_pressure_score == ZERO
    assert report.reason_codes == ("review_blocker_rollup_no_inputs",)
    assert report.reason_code_counts == (
        module.ResearchStrategyCandidateReviewBlockerReasonCodeCount(
            reason_code="review_blocker_rollup_no_inputs",
            count=ONE,
        ),
    )
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert payload["rows"] == []
    assert payload["public_digest"] == report.public_digest


def test_status_decimal_frozen_flags_and_digest_validation() -> None:
    module = api()
    report = build_report(module, blocker_input(module, "review-frozen"))

    assert is_dataclass(module.ResearchStrategyCandidateReviewBlockerRollupConfig)
    assert is_dataclass(module.ResearchStrategyCandidateReviewBlockerInput)
    assert is_dataclass(module.ResearchStrategyCandidateReviewBlockerRow)
    assert is_dataclass(module.ResearchStrategyCandidateReviewBlockerReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyCandidateReviewBlockerRollupReport)
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        blocker_input(module, evidence_status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        blocker_input(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        cfg(module, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="review_count"):
        replace(report, review_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="blocker_pressure_score"):
        replace(
            report.rows[0],
            blocker_pressure_score=_DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="public_digest"):
        replace(report, public_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(report, status="review")
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            module,
            blocker_input(module, "naive-time"),
            generated_at=datetime(2026, 7, 8, 18, 0),
        )


def test_public_leak_rejection_at_input_and_payload_boundaries() -> None:
    module = api()
    for unsafe_value in (
        "raw_candidate_id:abc",
        "candidate_id:abc",
        "market_id:123",
        "market_slug:event",
        "question:will-it-happen",
        "source_url:https://example.invalid",
        "source_text:verbatim",
        "dsn=postgres://example",
        "table_name:research",
        "private_token=secret",
        "wallet-address",
        "order-ticket",
        "trade-ticket",
        "buy-note",
        "sell-note",
        "recommendation-note",
        "sizing-note",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            blocker_input(module, review_key=unsafe_value)
        with pytest.raises(ValueError, match="unsafe"):
            blocker_input(module, reason_codes=(unsafe_value,))

    report = build_report(module, blocker_input(module, "safe-review-key"))
    object.__setattr__(report.rows[0], "review_hash", "market_id:123")
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_candidate_review_blocker_rollup_report_payload(report)


def test_public_payload_exports_and_static_scope_stay_report_only() -> None:
    module = api()
    report = build_report(module, blocker_input(module, "review-static"))
    payload = module.research_strategy_candidate_review_blocker_rollup_report_payload(
        report,
    )
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_REVIEW_BLOCKER_ROLLUP_REPORT_CONFIG_VERSION",
        "ResearchStrategyCandidateReviewBlockerInput",
        "ResearchStrategyCandidateReviewBlockerReasonCodeCount",
        "ResearchStrategyCandidateReviewBlockerRollupConfig",
        "ResearchStrategyCandidateReviewBlockerRollupReport",
        "ResearchStrategyCandidateReviewBlockerRow",
        "build_research_strategy_candidate_review_blocker_rollup_report",
        "research_strategy_candidate_review_blocker_rollup_report_digest",
        "research_strategy_candidate_review_blocker_rollup_report_payload",
    )
    for forbidden in (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "sizing",
    ):
        assert forbidden not in encoded

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    public_forbidden = (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "sizing",
    )
    runtime_forbidden = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "ccxt",
        "open",
        "connect",
        "execute",
        "request",
        "write_text",
        "write_bytes",
    }

    for public_name in module.__all__:
        lowered_name = public_name.lower()
        assert not any(term in lowered_name for term in public_forbidden)
    for cls in (
        module.ResearchStrategyCandidateReviewBlockerInput,
        module.ResearchStrategyCandidateReviewBlockerReasonCodeCount,
        module.ResearchStrategyCandidateReviewBlockerRollupConfig,
        module.ResearchStrategyCandidateReviewBlockerRollupReport,
        module.ResearchStrategyCandidateReviewBlockerRow,
    ):
        for field in fields(cls):
            lowered_name = field.name.lower()
            assert not any(term in lowered_name for term in public_forbidden)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
                assert func.id not in runtime_forbidden
            elif isinstance(func, ast.Attribute):
                assert func.attr not in runtime_forbidden
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in runtime_forbidden
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in runtime_forbidden
