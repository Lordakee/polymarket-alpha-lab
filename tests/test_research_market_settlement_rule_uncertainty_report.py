from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_settlement_rule_uncertainty_report import (
    DEFAULT_RESEARCH_MARKET_SETTLEMENT_RULE_UNCERTAINTY_CONFIG_VERSION,
    ResearchMarketSettlementRuleUncertaintyCandidate,
    ResearchMarketSettlementRuleUncertaintyConfig,
    ResearchMarketSettlementRuleUncertaintyReasonCodeCount,
    ResearchMarketSettlementRuleUncertaintyReport,
    ResearchMarketSettlementRuleUncertaintyRow,
    build_research_market_settlement_rule_uncertainty_report,
    research_market_settlement_rule_uncertainty_digest,
    research_market_settlement_rule_uncertainty_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_market_settlement_rule_uncertainty_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketSettlementRuleUncertaintyConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_MARKET_SETTLEMENT_RULE_UNCERTAINTY_CONFIG_VERSION
        ),
        "pass_max_uncertainty_score": d("0.250000"),
        "watch_max_uncertainty_score": d("0.550000"),
        "dependent_outcome_watch_count": d("3.000000"),
        "dependent_outcome_block_count": d("6.000000"),
        "rule_ambiguity_weight": d("0.300000"),
        "official_source_staleness_weight": d("0.200000"),
        "dependent_outcome_weight": d("0.150000"),
        "contradiction_pressure_weight": d("0.200000"),
        "manual_review_urgency_weight": d("0.150000"),
        "hard_rule_ambiguity_floor": d("0.850000"),
        "hard_source_freshness_ceiling": d("0.150000"),
        "hard_contradiction_pressure_floor": d("0.850000"),
    }
    values.update(overrides)
    return ResearchMarketSettlementRuleUncertaintyConfig(**values)


def candidate(
    candidate_id: str,
    *,
    observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    rule_ambiguity: Decimal = d("0.100000"),
    official_source_freshness: Decimal = d("0.900000"),
    dependent_outcome_count: Decimal = d("0.000000"),
    contradiction_pressure: Decimal = d("0.100000"),
    manual_review_urgency: Decimal = d("0.100000"),
    market_id: str | None = "market-private-id",
    market_slug: str | None = "market-private-slug",
    market_question: str | None = "Will the private settlement happen?",
    source_url: str | None = "https://example.invalid/private-source",
    source_text: str | None = "private source text",
    dsn: str | None = "postgres://private/db",
    table_name: str | None = "private_table",
    private_token: str | None = "private-token",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketSettlementRuleUncertaintyCandidate:
    return ResearchMarketSettlementRuleUncertaintyCandidate(
        candidate_id=candidate_id,
        observed_at=observed_at,
        rule_ambiguity=rule_ambiguity,
        official_source_freshness=official_source_freshness,
        dependent_outcome_count=dependent_outcome_count,
        contradiction_pressure=contradiction_pressure,
        manual_review_urgency=manual_review_urgency,
        market_id=market_id,
        market_slug=market_slug,
        market_question=market_question,
        source_url=source_url,
        source_text=source_text,
        dsn=dsn,
        table_name=table_name,
        private_token=private_token,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchMarketSettlementRuleUncertaintyCandidate,
    cfg: ResearchMarketSettlementRuleUncertaintyConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketSettlementRuleUncertaintyReport:
    return build_research_market_settlement_rule_uncertainty_report(
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


def test_clear_settlement_rule_candidate_passes_with_decimal_public_payload() -> None:
    uncertainty_report = report(candidate("candidate-pass"))

    assert type(uncertainty_report) is ResearchMarketSettlementRuleUncertaintyReport
    assert uncertainty_report.generated_at == GENERATED_AT
    assert uncertainty_report.config_version == (
        DEFAULT_RESEARCH_MARKET_SETTLEMENT_RULE_UNCERTAINTY_CONFIG_VERSION
    )
    assert uncertainty_report.candidate_count == ONE
    assert uncertainty_report.pass_count == ONE
    assert uncertainty_report.watch_count == ZERO
    assert uncertainty_report.block_count == ZERO
    assert uncertainty_report.manual_review_urgent_count == ZERO
    assert uncertainty_report.mean_uncertainty_score == d("0.085000")
    assert uncertainty_report.max_manual_review_urgency == d("0.100000")
    assert uncertainty_report.status == "pass"
    assert uncertainty_report.reason_codes == ("settlement_rule_uncertainty_report_pass",)
    assert uncertainty_report.paper_only is True
    assert uncertainty_report.report_only is True
    assert uncertainty_report.readonly is True

    row = uncertainty_report.rows[0]
    assert type(row) is ResearchMarketSettlementRuleUncertaintyRow
    assert row.row_number == ONE
    assert row.rule_ambiguity_score == d("0.100000")
    assert row.official_source_staleness_score == d("0.100000")
    assert row.dependent_outcome_score == ZERO
    assert row.contradiction_pressure_score == d("0.100000")
    assert row.manual_review_urgency_score == d("0.100000")
    assert row.uncertainty_score == d("0.085000")
    assert row.status == "pass"
    assert row.reason_codes == (
        "contradiction_pressure_low",
        "dependent_outcome_count_low",
        "manual_review_urgency_low",
        "official_source_freshness_current",
        "rule_ambiguity_low",
        "settlement_rule_uncertainty_pass",
    )

    payload = research_market_settlement_rule_uncertainty_report_payload(
        uncertainty_report,
    )
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["uncertainty_score"] == "0.085000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["public_report_digest"] == uncertainty_report.public_report_digest
    assert research_market_settlement_rule_uncertainty_digest(uncertainty_report) == (
        uncertainty_report.public_report_digest
    )
    assert_no_float(payload)
    json.dumps(payload, sort_keys=True)


def test_watch_and_block_rows_roll_up_with_manual_review_urgency() -> None:
    uncertainty_report = report(
        candidate(
            "candidate-watch",
            rule_ambiguity=d("0.450000"),
            official_source_freshness=d("0.600000"),
            dependent_outcome_count=d("3.000000"),
            contradiction_pressure=d("0.300000"),
            manual_review_urgency=d("0.700000"),
        ),
        candidate(
            "candidate-block",
            rule_ambiguity=d("0.900000"),
            official_source_freshness=d("0.100000"),
            dependent_outcome_count=d("8.000000"),
            contradiction_pressure=d("0.900000"),
            manual_review_urgency=d("0.800000"),
        ),
    )

    assert uncertainty_report.status == "block"
    assert uncertainty_report.pass_count == ZERO
    assert uncertainty_report.watch_count == ONE
    assert uncertainty_report.block_count == ONE
    assert uncertainty_report.manual_review_urgent_count == d("2.000000")
    assert tuple(row.status for row in uncertainty_report.rows) == ("block", "watch")
    assert uncertainty_report.rows[0].hard_flags == (
        "contradiction_pressure_hard_block",
        "official_source_stale_hard_block",
        "rule_ambiguity_hard_block",
    )
    assert uncertainty_report.rows[0].dependent_outcome_score == ONE
    assert uncertainty_report.rows[0].reason_codes == (
        "contradiction_pressure_hard_block",
        "contradiction_pressure_high",
        "dependent_outcome_count_high",
        "manual_review_urgency_high",
        "official_source_freshness_stale",
        "official_source_stale_hard_block",
        "rule_ambiguity_hard_block",
        "rule_ambiguity_high",
        "settlement_rule_uncertainty_block",
    )
    assert uncertainty_report.rows[1].status == "watch"
    assert "settlement_rule_uncertainty_watch" in uncertainty_report.rows[1].reason_codes
    assert uncertainty_report.reason_codes == (
        "contradiction_pressure_hard_block",
        "manual_review_urgency_present",
        "official_source_stale_hard_block",
        "rule_ambiguity_hard_block",
        "settlement_rule_uncertainty_report_block",
    )


def test_empty_inputs_block_with_no_candidates_reason_count() -> None:
    uncertainty_report = report()

    assert uncertainty_report.status == "block"
    assert uncertainty_report.candidate_count == ZERO
    assert uncertainty_report.reason_codes == ("no_settlement_rule_candidates_block",)
    assert uncertainty_report.reason_code_counts == (
        ResearchMarketSettlementRuleUncertaintyReasonCodeCount(
            reason_code="no_settlement_rule_candidates_block",
            count=ONE,
        ),
    )
    assert uncertainty_report.rows == ()


def test_decimal_type_datetime_and_flag_rejections() -> None:
    with pytest.raises(ValueError, match="pass_max_uncertainty_score"):
        config(pass_max_uncertainty_score=0.25)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_max_uncertainty_score"):
        config(watch_max_uncertainty_score=_DecimalSubclass("0.550000"))
    with pytest.raises(ValueError, match="rule_ambiguity_weight"):
        config(rule_ambiguity_weight=d("0.290000"))
    with pytest.raises(ValueError, match="rule_ambiguity"):
        candidate("bad-float", rule_ambiguity=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="dependent_outcome_count"):
        candidate("bad-int", dependent_outcome_count=1)  # type: ignore[arg-type]
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
    uncertainty_report = report(
        candidate(
            "raw-candidate-secret-001",
            market_id="market-secret-id-001",
            market_slug="market-secret-slug",
            market_question="Will this private question settle yes?",
            source_url="https://example.invalid/source-secret-url",
            source_text=(
                "source secret text with dsn postgres://host/db table fills "
                "token abc wallet order position buy sell recommend"
            ),
            dsn="postgres://host/db",
            table_name="private_fills",
            private_token="token-abc",
        ),
    )

    payload = research_market_settlement_rule_uncertainty_report_payload(
        uncertainty_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    for sensitive_value in (
        "raw-candidate-secret-001",
        "market-secret-id-001",
        "market-secret-slug",
        "Will this private question settle yes?",
        "https://example.invalid/source-secret-url",
        "source secret text",
        "postgres://host/db",
        "private_fills",
        "token-abc",
    ):
        assert sensitive_value not in encoded
    for sensitive_key in (
        "candidate_id",
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "table_name",
        "token",
        "private_token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert sensitive_key not in encoded

    object.__setattr__(uncertainty_report, "public_report_digest", "0" * 64)
    with pytest.raises(ValueError, match="digest"):
        research_market_settlement_rule_uncertainty_report_payload(uncertainty_report)


def test_deterministic_payload_and_reason_counts_are_input_order_independent() -> None:
    first = report(
        candidate("z-pass"),
        candidate("a-block", rule_ambiguity=d("0.900000")),
        candidate("m-watch", rule_ambiguity=d("0.450000")),
    )
    second = report(
        candidate("m-watch", rule_ambiguity=d("0.450000")),
        candidate("z-pass"),
        candidate("a-block", rule_ambiguity=d("0.900000")),
    )

    first_payload = research_market_settlement_rule_uncertainty_report_payload(first)
    second_payload = research_market_settlement_rule_uncertainty_report_payload(second)

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
    uncertainty_report = report(candidate("consistent"))
    assert research_market_settlement_rule_uncertainty_digest(uncertainty_report) == (
        uncertainty_report.public_report_digest
    )

    with pytest.raises(FrozenInstanceError):
        uncertainty_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        uncertainty_report.rows[0].uncertainty_score = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="max_manual_review_urgency"):
        replace(uncertainty_report, max_manual_review_urgency=d("0.500000"))

    object.__setattr__(uncertainty_report.rows[0], "uncertainty_score", d("0.500000"))
    with pytest.raises(ValueError, match="uncertainty_score"):
        research_market_settlement_rule_uncertainty_report_payload(uncertainty_report)


def test_public_exports_are_exact() -> None:
    import polymarket_alpha_lab.research_market_settlement_rule_uncertainty_report as api

    assert api.__all__ == (
        "DEFAULT_RESEARCH_MARKET_SETTLEMENT_RULE_UNCERTAINTY_CONFIG_VERSION",
        "ResearchMarketSettlementRuleUncertaintyCandidate",
        "ResearchMarketSettlementRuleUncertaintyConfig",
        "ResearchMarketSettlementRuleUncertaintyReasonCodeCount",
        "ResearchMarketSettlementRuleUncertaintyReport",
        "ResearchMarketSettlementRuleUncertaintyRow",
        "build_research_market_settlement_rule_uncertainty_report",
        "research_market_settlement_rule_uncertainty_digest",
        "research_market_settlement_rule_uncertainty_report_payload",
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
