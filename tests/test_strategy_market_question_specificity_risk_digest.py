from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_market_question_specificity_risk_digest import (
    DEFAULT_STRATEGY_MARKET_QUESTION_SPECIFICITY_RISK_DIGEST_CONFIG_VERSION,
    StrategyMarketQuestionSpecificityRiskDigestConfig,
    StrategyMarketQuestionSpecificityRiskDigestReport,
    StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount,
    StrategyMarketQuestionSpecificityRiskFinding,
    build_strategy_market_question_specificity_risk_digest,
    strategy_market_question_specificity_risk_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 14, 30, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyMarketQuestionSpecificityRiskDigestConfig:
    values = {
        "config_version": (
            DEFAULT_STRATEGY_MARKET_QUESTION_SPECIFICITY_RISK_DIGEST_CONFIG_VERSION
        ),
        "min_rule_clarity_score": d("0.700000"),
        "min_measurable_endpoint_coverage_ratio": d("0.750000"),
        "min_deadline_clarity_score": d("0.800000"),
        "max_ambiguous_term_count": d("1.000000"),
        "min_source_coverage_ratio": d("0.500000"),
    }
    values.update(overrides)
    return StrategyMarketQuestionSpecificityRiskDigestConfig(**values)


def finding(
    market_reference: str = "market_alpha_redacted",
    *,
    strategy_reference: str = "strategy_core_redacted",
    rule_clarity_score: Decimal = d("0.900000"),
    measurable_endpoint_coverage_ratio: Decimal = d("1.000000"),
    deadline_clarity_score: Decimal = d("0.900000"),
    ambiguous_term_count: Decimal = d("0.000000"),
    source_mapping: tuple[tuple[str, str], ...] = (
        ("official_rules", "source_rules_redacted"),
        ("settlement_source", "source_settlement_redacted"),
    ),
    source_config_version: str = "strategy-question-specificity-source-v0",
) -> StrategyMarketQuestionSpecificityRiskFinding:
    return StrategyMarketQuestionSpecificityRiskFinding(
        strategy_reference=strategy_reference,
        market_reference=market_reference,
        rule_clarity_score=rule_clarity_score,
        measurable_endpoint_coverage_ratio=measurable_endpoint_coverage_ratio,
        deadline_clarity_score=deadline_clarity_score,
        ambiguous_term_count=ambiguous_term_count,
        source_mapping=source_mapping,
        source_config_version=source_config_version,
    )


def report(
    *rows: StrategyMarketQuestionSpecificityRiskFinding,
    cfg: StrategyMarketQuestionSpecificityRiskDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyMarketQuestionSpecificityRiskDigestReport:
    return build_strategy_market_question_specificity_risk_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_strategy_specificity_digest_passes_clear_questions_and_enforces_flags() -> None:
    digest_report = report(
        finding("market_beta_redacted", strategy_reference="strategy_beta_redacted"),
        finding(
            "market_alpha_redacted",
            strategy_reference="strategy_alpha_redacted",
            rule_clarity_score=d("0.800000"),
            measurable_endpoint_coverage_ratio=d("0.900000"),
            deadline_clarity_score=d("0.850000"),
            ambiguous_term_count=d("1.000000"),
        ),
    )

    assert isinstance(digest_report, StrategyMarketQuestionSpecificityRiskDigestReport)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.config_version == (
        DEFAULT_STRATEGY_MARKET_QUESTION_SPECIFICITY_RISK_DIGEST_CONFIG_VERSION
    )
    assert digest_report.specificity_risk_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_strategy_question_specificity_diagnostics"
    )
    assert digest_report.finding_count == d("2.000000")
    assert digest_report.pass_finding_count == d("2.000000")
    assert digest_report.watch_finding_count == d("0.000000")
    assert digest_report.blocked_finding_count == d("0.000000")
    assert digest_report.average_rule_clarity_score == d("0.850000")
    assert digest_report.average_measurable_endpoint_coverage_ratio == d("0.950000")
    assert digest_report.average_deadline_clarity_score == d("0.875000")
    assert digest_report.total_ambiguous_term_count == d("1.000000")
    assert digest_report.source_coverage_ratio == d("1.000000")
    assert digest_report.reason_codes == (
        "strategy_market_question_specificity_risk_passed",
    )
    assert digest_report.reason_code_counts == (
        StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount(
            reason_code="strategy_market_question_specificity_risk_passed",
            count=d("2.000000"),
        ),
    )
    assert digest_report.source_config_versions == (
        (
            "strategy_alpha_redacted",
            "market_alpha_redacted",
            "strategy-question-specificity-source-v0",
        ),
        (
            "strategy_beta_redacted",
            "market_beta_redacted",
            "strategy-question-specificity-source-v0",
        ),
    )
    assert tuple((row.strategy_reference, row.market_reference) for row in digest_report.findings) == (
        ("strategy_alpha_redacted", "market_alpha_redacted"),
        ("strategy_beta_redacted", "market_beta_redacted"),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.findings)


def test_strategy_specificity_digest_blocks_low_scores_and_tamper_checks() -> None:
    digest_report = report(
        finding(
            "market_risky_redacted",
            strategy_reference="strategy_risky_redacted",
            rule_clarity_score=d("0.600000"),
            measurable_endpoint_coverage_ratio=d("0.500000"),
            deadline_clarity_score=d("0.750000"),
            ambiguous_term_count=d("3.000000"),
            source_mapping=(("official_rules", "source_rules_redacted"),),
        ),
    )

    assert digest_report.specificity_risk_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_strategy_question_specificity_diagnostics"
    )
    assert digest_report.blocked_finding_count == d("1.000000")
    assert digest_report.readiness_gap_count == d("4.000000")
    assert digest_report.derived_validation_digest == (
        "strategy_market_question_specificity_risk_digest_v0|"
        "status=blocked|findings=1.000000|blocked=1.000000|watch=0.000000|"
        "pass=0.000000|gaps=4.000000|reasons="
        "strategy_market_question_specificity_risk_ambiguous_terms,"
        "strategy_market_question_specificity_risk_deadline_unclear,"
        "strategy_market_question_specificity_risk_endpoint_not_measurable,"
        "strategy_market_question_specificity_risk_rule_unclear"
    )

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(digest_report, derived_validation_digest="tampered")
    with pytest.raises(ValueError, match="blocked_finding_count must match"):
        replace(digest_report, blocked_finding_count=d("0.000000"))
    with pytest.raises(ValueError, match="specificity_risk_status must match"):
        replace(digest_report.findings[0], specificity_risk_status="pass")
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            digest_report.findings[0],
            reason_codes=("strategy_market_question_specificity_risk_passed",),
        )


def test_strategy_specificity_digest_watches_partial_sources_and_handles_empty_input() -> None:
    watch_report = report(
        finding(
            "market_zeta_redacted",
            strategy_reference="strategy_zeta_redacted",
        ),
        finding(
            "market_alpha_redacted",
            strategy_reference="strategy_alpha_redacted",
            source_mapping=(("official_rules", "source_rules_redacted"),),
        ),
        cfg=config(min_source_coverage_ratio=d("0.750000")),
    )

    assert watch_report.specificity_risk_status == "watch"
    assert watch_report.recommended_next_step == (
        "review_report_only_strategy_question_specificity_sources"
    )
    assert watch_report.pass_finding_count == d("1.000000")
    assert watch_report.watch_finding_count == d("1.000000")
    assert watch_report.reason_codes == (
        "strategy_market_question_specificity_risk_sources_partial",
    )
    assert tuple(row.specificity_risk_status for row in watch_report.findings) == (
        "watch",
        "pass",
    )

    empty_report = report()
    assert empty_report.specificity_risk_status == "blocked"
    assert empty_report.finding_count == d("0.000000")
    assert empty_report.reason_codes == (
        "strategy_market_question_specificity_risk_empty_findings",
    )
    assert empty_report.reason_code_counts == (
        StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount(
            "strategy_market_question_specificity_risk_empty_findings",
            d("1.000000"),
        ),
    )


def test_strategy_specificity_digest_rejects_non_decimal_values_and_bad_datetimes() -> None:
    generated_at = datetime(2026, 7, 6, 10, 30, tzinfo=timezone(timedelta(hours=-4)))
    assert report(finding(), generated_at=generated_at).generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(finding(), generated_at=_DateTimeSubclass(2026, 7, 6, 14, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(finding(), generated_at=datetime(2026, 7, 6, 14, 30))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            finding(),
            generated_at=datetime(2026, 7, 6, 14, 30, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="rule_clarity_score must be a Decimal"):
        finding(rule_clarity_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="rule_clarity_score must be exactly Decimal"):
        finding(rule_clarity_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="min_rule_clarity_score must be a Decimal"):
        config(min_rule_clarity_score=0.7)
    with pytest.raises(ValueError, match="ambiguous_term_count must be a Decimal"):
        finding(ambiguous_term_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_ambiguous_term_count must be a Decimal"):
        config(max_ambiguous_term_count=1)
    with pytest.raises(ValueError, match="deadline_clarity_score must be finite"):
        finding(deadline_clarity_score=Decimal("NaN"))


def test_strategy_specificity_digest_validates_exact_types_redaction_and_hard_flags() -> None:
    digest_report = report(finding())

    for public_record in (
        config(),
        finding(),
        digest_report.findings[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        digest_report.paper_only = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        StrategyMarketQuestionSpecificityRiskDigestConfig(config_version=_StringSubclass("v0"))
    with pytest.raises(ValueError, match="redacted"):
        finding(market_reference="market_0xabc")
    with pytest.raises(ValueError, match="unsafe surface"):
        finding(strategy_reference="strategy_live_redacted")
    with pytest.raises(ValueError, match="redacted"):
        finding(strategy_reference="strategy_live_account")
    with pytest.raises(ValueError, match="source_mapping must be sorted"):
        finding(
            source_mapping=(
                ("settlement_source", "source_settlement_redacted"),
                ("official_rules", "source_rules_redacted"),
            ),
        )
    with pytest.raises(ValueError, match="finding paper_only must be True"):
        replace(finding(), paper_only=False)
    with pytest.raises(ValueError, match="finding report_only must be True"):
        replace(finding(), report_only=False)
    with pytest.raises(ValueError, match="finding readonly must be True"):
        replace(finding(), readonly=False)
    with pytest.raises(ValueError, match="config paper_only must be True"):
        StrategyMarketQuestionSpecificityRiskDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="report readonly must be True"):
        replace(digest_report, readonly=False)
    with pytest.raises(ValueError, match="source_config_version"):
        finding(source_config_version="secret-version")
    with pytest.raises(ValueError, match="strategy/market pairs must be unique"):
        report(
            finding("market_dupe_redacted", strategy_reference="strategy_dupe_redacted"),
            finding("market_dupe_redacted", strategy_reference="strategy_dupe_redacted"),
        )


def test_strategy_specificity_digest_payload_uses_decimal_strings_and_is_json_ready() -> None:
    digest_report = report(
        finding(
            ambiguous_term_count=d("2.000000"),
            source_mapping=(("official_rules", "source_rules_redacted"),),
        ),
        cfg=config(max_ambiguous_term_count=d("1.000000")),
    )

    for public_record in (
        config(),
        digest_report.findings[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_score")
                or field.name.startswith("min_")
                or field.name.startswith("max_")
            ):
                assert type(field_value) is Decimal, field.name

    payload = strategy_market_question_specificity_risk_digest_payload(digest_report)

    assert payload["generated_at"] == "2026-07-06T14:30:00+00:00"
    assert payload["finding_count"] == "1.000000"
    assert payload["blocked_finding_count"] == "1.000000"
    assert payload["average_rule_clarity_score"] == "0.900000"
    assert payload["total_ambiguous_term_count"] == "2.000000"
    assert payload["readiness_gap_count"] == "1.000000"
    assert payload["derived_validation_digest"] == digest_report.derived_validation_digest
    assert payload["findings"][0]["ambiguous_term_count"] == "2.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                for forbidden in ("wallet", "order", "auth", "private_key", "database"):
                    assert forbidden not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))
            assert type(value) is not int

    walk_payload(payload)

    with pytest.raises(ValueError, match="report must be"):
        strategy_market_question_specificity_risk_digest_payload(report="bad")  # type: ignore[arg-type]


def test_strategy_specificity_digest_module_rejects_unsafe_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.strategy_market_question_specificity_risk_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "pathlib",
        "os",
        "sqlite",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    lowered_source = source.lower()
    for forbidden in (
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
        "wallet",
        "private_key",
        "authentication",
        "database",
        "persist",
        "network",
        "urlopen",
        "connect(",
        "execute(",
    ):
        assert forbidden not in lowered_source
