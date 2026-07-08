from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_resolution_rule_ambiguity_report import (
    DEFAULT_RESEARCH_MARKET_RESOLUTION_RULE_AMBIGUITY_CONFIG_VERSION,
    ResearchMarketResolutionRuleAmbiguityCandidate,
    ResearchMarketResolutionRuleAmbiguityConfig,
    ResearchMarketResolutionRuleAmbiguityReasonCodeCount,
    ResearchMarketResolutionRuleAmbiguityReport,
    ResearchMarketResolutionRuleAmbiguityRow,
    build_research_market_resolution_rule_ambiguity_report,
    research_market_resolution_rule_ambiguity_digest,
    research_market_resolution_rule_ambiguity_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_market_resolution_rule_ambiguity_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketResolutionRuleAmbiguityConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_MARKET_RESOLUTION_RULE_AMBIGUITY_CONFIG_VERSION,
        "pass_max_ambiguity_score": d("0.250000"),
        "watch_max_ambiguity_score": d("0.550000"),
        "rule_ambiguity_weight": d("0.400000"),
        "source_disagreement_weight": d("0.250000"),
        "edge_case_weight": d("0.200000"),
        "manual_review_weight": d("0.150000"),
        "hard_rule_clarity_floor": d("0.200000"),
        "hard_source_disagreement_floor": d("0.850000"),
        "hard_edge_case_floor": d("0.900000"),
    }
    values.update(overrides)
    return ResearchMarketResolutionRuleAmbiguityConfig(**values)


def candidate(
    candidate_id: str,
    *,
    observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    resolution_rule_clarity: Decimal = d("0.900000"),
    source_disagreement: Decimal = d("0.100000"),
    edge_case_exposure: Decimal = d("0.100000"),
    manual_review_signal: Decimal = d("0.100000"),
    market_id: str | None = "market-private-id",
    market_slug: str | None = "market-private-slug",
    market_question: str | None = "Will the private example resolve yes?",
    source_ref: str | None = "source-private-ref",
    source_url: str | None = "https://example.invalid/private-source",
    source_text: str | None = "private source text",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketResolutionRuleAmbiguityCandidate:
    return ResearchMarketResolutionRuleAmbiguityCandidate(
        candidate_id=candidate_id,
        observed_at=observed_at,
        resolution_rule_clarity=resolution_rule_clarity,
        source_disagreement=source_disagreement,
        edge_case_exposure=edge_case_exposure,
        manual_review_signal=manual_review_signal,
        market_id=market_id,
        market_slug=market_slug,
        market_question=market_question,
        source_ref=source_ref,
        source_url=source_url,
        source_text=source_text,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchMarketResolutionRuleAmbiguityCandidate,
    cfg: ResearchMarketResolutionRuleAmbiguityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketResolutionRuleAmbiguityReport:
    return build_research_market_resolution_rule_ambiguity_report(
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
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def test_clear_rule_candidate_passes_with_decimal_public_payload() -> None:
    ambiguity_report = report(candidate("candidate-pass"))

    assert type(ambiguity_report) is ResearchMarketResolutionRuleAmbiguityReport
    assert ambiguity_report.generated_at == GENERATED_AT
    assert ambiguity_report.config_version == (
        DEFAULT_RESEARCH_MARKET_RESOLUTION_RULE_AMBIGUITY_CONFIG_VERSION
    )
    assert ambiguity_report.candidate_count == ONE
    assert ambiguity_report.pass_count == ONE
    assert ambiguity_report.watch_count == ZERO
    assert ambiguity_report.block_count == ZERO
    assert ambiguity_report.hard_flag_count == ZERO
    assert ambiguity_report.mean_ambiguity_score == d("0.100000")
    assert ambiguity_report.max_review_priority_score == d("0.100000")
    assert ambiguity_report.status == "pass"
    assert ambiguity_report.reason_codes == ("resolution_rule_ambiguity_report_pass",)
    assert ambiguity_report.paper_only is True
    assert ambiguity_report.report_only is True
    assert ambiguity_report.readonly is True

    row = ambiguity_report.rows[0]
    assert type(row) is ResearchMarketResolutionRuleAmbiguityRow
    assert row.row_number == ONE
    assert row.rule_ambiguity_score == d("0.100000")
    assert row.source_disagreement_score == d("0.100000")
    assert row.edge_case_score == d("0.100000")
    assert row.manual_review_score == d("0.100000")
    assert row.ambiguity_score == d("0.100000")
    assert row.review_priority_score == d("0.100000")
    assert row.status == "pass"
    assert row.hard_flags == ()
    assert row.reason_codes == (
        "edge_case_low",
        "manual_review_low",
        "resolution_rule_ambiguity_pass",
        "rule_ambiguity_low",
        "source_disagreement_low",
    )

    payload = research_market_resolution_rule_ambiguity_report_payload(ambiguity_report)
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["ambiguity_score"] == "0.100000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["public_report_digest"] == ambiguity_report.public_report_digest
    assert research_market_resolution_rule_ambiguity_digest(ambiguity_report) == (
        ambiguity_report.public_report_digest
    )
    assert_no_float(payload)
    json.dumps(payload, sort_keys=True)


def test_watch_and_block_rows_roll_up_with_hard_flags() -> None:
    ambiguity_report = report(
        candidate(
            "candidate-watch",
            resolution_rule_clarity=d("0.550000"),
            source_disagreement=d("0.400000"),
            edge_case_exposure=d("0.200000"),
            manual_review_signal=d("0.100000"),
        ),
        candidate(
            "candidate-block",
            resolution_rule_clarity=d("0.100000"),
            source_disagreement=d("0.900000"),
            edge_case_exposure=d("0.950000"),
            manual_review_signal=d("0.800000"),
        ),
    )

    assert ambiguity_report.status == "block"
    assert ambiguity_report.pass_count == ZERO
    assert ambiguity_report.watch_count == ONE
    assert ambiguity_report.block_count == ONE
    assert ambiguity_report.hard_flag_count == d("3.000000")
    assert tuple(row.status for row in ambiguity_report.rows) == ("block", "watch")
    assert ambiguity_report.rows[0].hard_flags == (
        "edge_case_hard_block",
        "rule_clarity_hard_block",
        "source_disagreement_hard_block",
    )
    assert ambiguity_report.rows[0].reason_codes == (
        "edge_case_hard_block",
        "edge_case_high",
        "manual_review_high",
        "resolution_rule_ambiguity_block",
        "rule_ambiguity_high",
        "rule_clarity_hard_block",
        "source_disagreement_hard_block",
        "source_disagreement_high",
    )
    assert ambiguity_report.rows[1].status == "watch"
    assert "resolution_rule_ambiguity_watch" in ambiguity_report.rows[1].reason_codes
    assert ambiguity_report.reason_codes == (
        "edge_case_hard_block",
        "resolution_rule_ambiguity_report_block",
        "rule_clarity_hard_block",
        "source_disagreement_hard_block",
    )


def test_empty_inputs_block_with_no_candidates_reason_count() -> None:
    ambiguity_report = report()

    assert ambiguity_report.status == "block"
    assert ambiguity_report.candidate_count == ZERO
    assert ambiguity_report.reason_codes == ("no_resolution_rule_candidates_block",)
    assert ambiguity_report.reason_code_counts == (
        ResearchMarketResolutionRuleAmbiguityReasonCodeCount(
            reason_code="no_resolution_rule_candidates_block",
            count=ONE,
        ),
    )
    assert ambiguity_report.rows == ()


def test_decimal_type_datetime_and_flag_rejections() -> None:
    with pytest.raises(ValueError, match="pass_max_ambiguity_score"):
        config(pass_max_ambiguity_score=0.25)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_max_ambiguity_score"):
        config(watch_max_ambiguity_score=_DecimalSubclass("0.550000"))
    with pytest.raises(ValueError, match="rule_ambiguity_weight"):
        config(rule_ambiguity_weight=d("0.390000"))
    with pytest.raises(ValueError, match="resolution_rule_clarity"):
        candidate("bad-float", resolution_rule_clarity=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_disagreement"):
        candidate("bad-int", source_disagreement=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        candidate("bad-time", observed_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate("ok-time"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate("subclass-time"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        candidate("bad-flag", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(candidate("flag-report")), readonly=False)


def test_public_payload_rejects_private_identifier_and_operational_leaks() -> None:
    ambiguity_report = report(
        candidate(
            "raw-candidate-secret-001",
            market_id="market-secret-id-001",
            market_slug="market-secret-slug",
            market_question="Will this private question settle yes?",
            source_ref="source-secret-ref",
            source_url="https://example.invalid/source-secret-url",
            source_text=(
                "source secret text with dsn postgres://host/db table fills "
                "token abc wallet order position buy sell recommend"
            ),
        ),
    )

    payload = research_market_resolution_rule_ambiguity_report_payload(ambiguity_report)
    encoded = json.dumps(payload, sort_keys=True)

    for sensitive_value in (
        "raw-candidate-secret-001",
        "market-secret-id-001",
        "market-secret-slug",
        "Will this private question settle yes?",
        "source-secret-ref",
        "https://example.invalid/source-secret-url",
        "source secret text",
        "postgres://host/db",
        "fills",
        "abc",
    ):
        assert sensitive_value not in encoded
    for sensitive_key in (
        "candidate_id",
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert sensitive_key not in encoded

    object.__setattr__(ambiguity_report, "public_report_digest", "0" * 64)
    with pytest.raises(ValueError, match="digest"):
        research_market_resolution_rule_ambiguity_report_payload(ambiguity_report)


def test_deterministic_payload_and_reason_counts_are_input_order_independent() -> None:
    first = report(
        candidate("z-pass"),
        candidate("a-block", resolution_rule_clarity=d("0.100000")),
        candidate(
            "m-watch",
            resolution_rule_clarity=d("0.550000"),
            source_disagreement=d("0.400000"),
        ),
    )
    second = report(
        candidate(
            "m-watch",
            resolution_rule_clarity=d("0.550000"),
            source_disagreement=d("0.400000"),
        ),
        candidate("z-pass"),
        candidate("a-block", resolution_rule_clarity=d("0.100000")),
    )

    first_payload = research_market_resolution_rule_ambiguity_report_payload(first)
    second_payload = research_market_resolution_rule_ambiguity_report_payload(second)

    assert first_payload == second_payload
    assert tuple(row.row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert first.reason_code_counts == second.reason_code_counts
    assert first.public_report_digest == second.public_report_digest


def test_report_digest_consistency_revalidates_tampered_public_dataclasses() -> None:
    ambiguity_report = report(candidate("consistent"))
    assert research_market_resolution_rule_ambiguity_digest(ambiguity_report) == (
        ambiguity_report.public_report_digest
    )

    with pytest.raises(FrozenInstanceError):
        ambiguity_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        ambiguity_report.rows[0].ambiguity_score = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="max_review_priority_score"):
        replace(ambiguity_report, max_review_priority_score=d("0.500000"))

    object.__setattr__(ambiguity_report.rows[0], "ambiguity_score", d("0.500000"))
    with pytest.raises(ValueError, match="ambiguity_score"):
        research_market_resolution_rule_ambiguity_report_payload(ambiguity_report)


def test_public_exports_are_exact() -> None:
    import polymarket_alpha_lab.research_market_resolution_rule_ambiguity_report as api

    assert api.__all__ == (
        "DEFAULT_RESEARCH_MARKET_RESOLUTION_RULE_AMBIGUITY_CONFIG_VERSION",
        "ResearchMarketResolutionRuleAmbiguityCandidate",
        "ResearchMarketResolutionRuleAmbiguityConfig",
        "ResearchMarketResolutionRuleAmbiguityReasonCodeCount",
        "ResearchMarketResolutionRuleAmbiguityReport",
        "ResearchMarketResolutionRuleAmbiguityRow",
        "build_research_market_resolution_rule_ambiguity_report",
        "research_market_resolution_rule_ambiguity_digest",
        "research_market_resolution_rule_ambiguity_report_payload",
    )


def test_module_has_no_execution_surface_or_public_forbidden_terms() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "connect(",
        "open(",
        "write_text",
        "write_bytes",
        "create_order",
        "cancel_order",
        "private_key",
        "api_key",
        "secret",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "urllib",
        "httpx",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "post",
        "request",
        "send",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
