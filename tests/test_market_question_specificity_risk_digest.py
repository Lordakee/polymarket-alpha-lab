from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timezone, timedelta, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_question_specificity_risk_digest import (
    DEFAULT_MARKET_QUESTION_SPECIFICITY_RISK_DIGEST_CONFIG_VERSION,
    MarketQuestionSpecificityRiskDigestConfig,
    MarketQuestionSpecificityRiskDigestReport,
    MarketQuestionSpecificityRiskDigestReasonCodeCount,
    MarketQuestionSpecificityRiskFinding,
    build_market_question_specificity_risk_digest,
    market_question_specificity_risk_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def _config(**overrides: object) -> MarketQuestionSpecificityRiskDigestConfig:
    values = {
        "config_version": DEFAULT_MARKET_QUESTION_SPECIFICITY_RISK_DIGEST_CONFIG_VERSION,
        "min_rule_clarity_score": Decimal("0.700000"),
        "min_measurable_endpoint_coverage_ratio": Decimal("0.750000"),
        "min_deadline_clarity_score": Decimal("0.800000"),
        "max_ambiguous_term_count": Decimal("1"),
        "min_authoritative_source_coverage_ratio": Decimal("0.500000"),
    }
    values.update(overrides)
    return MarketQuestionSpecificityRiskDigestConfig(**values)


def _finding(
    market_reference: str,
    *,
    rule_clarity_score: Decimal = Decimal("0.900000"),
    measurable_endpoint_coverage_ratio: Decimal = Decimal("1.000000"),
    deadline_clarity_score: Decimal = Decimal("0.900000"),
    ambiguous_term_count: Decimal = Decimal("0"),
    authoritative_source_mapping: tuple[tuple[str, str], ...] = (
        ("official_rules", "source_rules_redacted"),
        ("settlement_source", "source_settlement_redacted"),
    ),
    source_config_version: str = "question-specificity-source-v0",
) -> MarketQuestionSpecificityRiskFinding:
    return MarketQuestionSpecificityRiskFinding(
        market_reference=market_reference,
        rule_clarity_score=rule_clarity_score,
        measurable_endpoint_coverage_ratio=measurable_endpoint_coverage_ratio,
        deadline_clarity_score=deadline_clarity_score,
        ambiguous_term_count=ambiguous_term_count,
        authoritative_source_mapping=authoritative_source_mapping,
        source_config_version=source_config_version,
    )


def _assert_no_public_int_or_float(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"public numeric was not serialized as a string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_int_or_float(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_public_int_or_float(item)


def test_specificity_digest_passes_clear_questions_and_keeps_report_only_flags() -> None:
    report = build_market_question_specificity_risk_digest(
        (
            _finding("market_alpha"),
            _finding(
                "market_beta",
                rule_clarity_score=Decimal("0.800000"),
                measurable_endpoint_coverage_ratio=Decimal("0.900000"),
                deadline_clarity_score=Decimal("0.850000"),
                ambiguous_term_count=Decimal("1"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, MarketQuestionSpecificityRiskDigestReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_MARKET_QUESTION_SPECIFICITY_RISK_DIGEST_CONFIG_VERSION
    assert report.specificity_risk_status == "pass"
    assert report.recommended_next_step == "allow_report_only_question_specificity_diagnostics"
    assert report.finding_count == 2
    assert report.pass_finding_count == 2
    assert report.watch_finding_count == 0
    assert report.blocked_finding_count == 0
    assert report.average_rule_clarity_score == Decimal("0.850000")
    assert report.average_measurable_endpoint_coverage_ratio == Decimal("0.950000")
    assert report.average_deadline_clarity_score == Decimal("0.875000")
    assert report.total_ambiguous_term_count == Decimal("1")
    assert report.authoritative_source_coverage_ratio == Decimal("1.000000")
    assert report.reason_codes == ("market_question_specificity_risk_passed",)
    assert report.reason_code_counts == (
        MarketQuestionSpecificityRiskDigestReasonCodeCount(
            reason_code="market_question_specificity_risk_passed",
            count=Decimal("2"),
        ),
    )
    assert report.source_config_versions == (
        ("market_alpha", "question-specificity-source-v0"),
        ("market_beta", "question-specificity-source-v0"),
    )
    assert tuple(row.market_reference for row in report.findings) == (
        "market_alpha",
        "market_beta",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_specificity_digest_caps_extra_authoritative_sources_at_full_coverage() -> None:
    report = build_market_question_specificity_risk_digest(
        (
            _finding(
                "market_alpha",
                authoritative_source_mapping=(
                    ("appeals_process", "source_appeals_redacted"),
                    ("official_rules", "source_rules_redacted"),
                    ("settlement_source", "source_settlement_redacted"),
                ),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.specificity_risk_status == "pass"
    assert report.authoritative_source_coverage_ratio == Decimal("1.000000")
    assert report.findings[0].reason_codes == (
        "market_question_specificity_risk_passed",
    )


def test_specificity_digest_blocks_low_scores_ambiguous_terms_and_missing_sources() -> None:
    report = build_market_question_specificity_risk_digest(
        (
            _finding(
                "market_beta",
                rule_clarity_score=Decimal("0.600000"),
                measurable_endpoint_coverage_ratio=Decimal("0.500000"),
                deadline_clarity_score=Decimal("0.750000"),
                ambiguous_term_count=Decimal("3"),
                authoritative_source_mapping=(("official_rules", "source_rules_redacted"),),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.specificity_risk_status == "blocked"
    assert report.recommended_next_step == "block_report_only_question_specificity_diagnostics"
    assert report.pass_finding_count == 0
    assert report.blocked_finding_count == 1
    assert report.total_ambiguous_term_count == Decimal("3")
    assert report.authoritative_source_coverage_ratio == Decimal("0.500000")
    assert report.reason_codes == (
        "market_question_specificity_risk_ambiguous_terms",
        "market_question_specificity_risk_deadline_unclear",
        "market_question_specificity_risk_endpoint_not_measurable",
        "market_question_specificity_risk_rule_unclear",
    )
    assert report.derived_validation_digest == (
        "market_question_specificity_risk_digest_v0|"
        "status=blocked|findings=1|blocked=1|watch=0|pass=0|gaps=4|"
        "reasons=market_question_specificity_risk_ambiguous_terms,"
        "market_question_specificity_risk_deadline_unclear,"
        "market_question_specificity_risk_endpoint_not_measurable,"
        "market_question_specificity_risk_rule_unclear"
    )
    assert report.findings[0].specificity_risk_status == "blocked"
    assert report.findings[0].reason_codes == report.reason_codes
    assert report.readiness_gap_count == Decimal("4")
    assert report.reason_code_counts == (
        MarketQuestionSpecificityRiskDigestReasonCodeCount(
            "market_question_specificity_risk_ambiguous_terms",
            Decimal("1"),
        ),
        MarketQuestionSpecificityRiskDigestReasonCodeCount(
            "market_question_specificity_risk_deadline_unclear",
            Decimal("1"),
        ),
        MarketQuestionSpecificityRiskDigestReasonCodeCount(
            "market_question_specificity_risk_endpoint_not_measurable",
            Decimal("1"),
        ),
        MarketQuestionSpecificityRiskDigestReasonCodeCount(
            "market_question_specificity_risk_rule_unclear",
            Decimal("1"),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, derived_validation_digest="tampered")


def test_specificity_digest_watches_partial_authoritative_source_coverage_and_sorts() -> None:
    report = build_market_question_specificity_risk_digest(
        (
            _finding("market_zeta"),
            _finding(
                "market_alpha",
                authoritative_source_mapping=(("official_rules", "source_rules_redacted"),),
            ),
        ),
        config=_config(
            min_authoritative_source_coverage_ratio=Decimal("0.750000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.specificity_risk_status == "watch"
    assert report.recommended_next_step == "review_report_only_question_specificity_sources"
    assert report.pass_finding_count == 1
    assert report.watch_finding_count == 1
    assert report.blocked_finding_count == 0
    assert report.reason_codes == (
        "market_question_specificity_risk_authoritative_sources_partial",
    )
    assert tuple(row.market_reference for row in report.findings) == (
        "market_alpha",
        "market_zeta",
    )
    assert tuple(row.specificity_risk_status for row in report.findings) == (
        "watch",
        "pass",
    )


def test_specificity_digest_empty_input_returns_blocked_diagnostic_report() -> None:
    report = build_market_question_specificity_risk_digest(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.specificity_risk_status == "blocked"
    assert report.recommended_next_step == "block_report_only_question_specificity_diagnostics"
    assert report.finding_count == 0
    assert report.average_rule_clarity_score == Decimal("0")
    assert report.average_measurable_endpoint_coverage_ratio == Decimal("0")
    assert report.average_deadline_clarity_score == Decimal("0")
    assert report.authoritative_source_coverage_ratio == Decimal("0")
    assert report.reason_codes == ("market_question_specificity_risk_empty_findings",)


def test_specificity_digest_normalizes_utc_datetimes_and_rejects_float_public_numbers() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    report = build_market_question_specificity_risk_digest(
        (_finding("market_alpha"),),
        config=_config(),
        generated_at=generated_at,
    )
    assert report.generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="generated_at"):
        build_market_question_specificity_risk_digest(
            (_finding("market_alpha"),),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        build_market_question_specificity_risk_digest(
            (_finding("market_alpha"),),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        build_market_question_specificity_risk_digest(
            (_finding("market_alpha"),),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="rule_clarity_score"):
        _finding("market_alpha", rule_clarity_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_rule_clarity_score"):
        _config(min_rule_clarity_score=0.7)
    with pytest.raises(ValueError, match="ambiguous_term_count"):
        _finding("market_alpha", ambiguous_term_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_ambiguous_term_count"):
        _config(max_ambiguous_term_count=1)
    with pytest.raises(ValueError, match="finite"):
        _finding("market_alpha", deadline_clarity_score=Decimal("NaN"))


def test_specificity_digest_validates_exact_types_redaction_flags_and_consistency() -> None:
    with pytest.raises(ValueError, match="config_version"):
        MarketQuestionSpecificityRiskDigestConfig(config_version=_StringSubclass("v0"))
    with pytest.raises(ValueError, match="max_ambiguous_term_count"):
        MarketQuestionSpecificityRiskDigestConfig(
            max_ambiguous_term_count=Decimal("1.5"),
        )
    with pytest.raises(ValueError, match="redacted"):
        _finding("market_0xabc")
    with pytest.raises(ValueError, match="redacted"):
        _finding("market_alpha", authoritative_source_mapping=(("account", "source_alpha"),))
    with pytest.raises(ValueError, match="authoritative_source_mapping"):
        _finding(
            "market_alpha",
            authoritative_source_mapping=(
                ("settlement_source", "source_settlement_redacted"),
                ("official_rules", "source_rules_redacted"),
            ),
        )
    with pytest.raises(ValueError, match="unique"):
        build_market_question_specificity_risk_digest(
            (_finding("market_alpha"), _finding("market_alpha")),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_finding("market_alpha"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(_finding("market_alpha"), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_finding("market_alpha"), readonly=False)
    with pytest.raises(ValueError, match="source_config_version"):
        _finding("market_alpha", source_config_version="secret-version")


def test_specificity_digest_public_numerics_are_decimals_and_payload_strings() -> None:
    report = build_market_question_specificity_risk_digest(
        (
            _finding(
                "market_alpha",
                ambiguous_term_count=Decimal("2"),
                authoritative_source_mapping=(("official_rules", "source_rules_redacted"),),
            ),
        ),
        config=_config(max_ambiguous_term_count=Decimal("1")),
        generated_at=GENERATED_AT,
    )

    for value in (_config(), report.findings[0], report.reason_code_counts[0], report):
        for field in fields(value):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_score")
                or field.name.startswith("min_")
                or field.name.startswith("max_")
            ):
                assert type(getattr(value, field.name)) is Decimal

    payload = market_question_specificity_risk_digest_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["finding_count"] == "1"
    assert payload["blocked_finding_count"] == "1"
    assert payload["average_rule_clarity_score"] == "0.900000"
    assert payload["total_ambiguous_term_count"] == "2"
    assert payload["readiness_gap_count"] == "1"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["findings"][0]["ambiguous_term_count"] == "2"
    assert payload["reason_code_counts"][0]["count"] == "1"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_public_int_or_float(payload)
    json.dumps(payload, sort_keys=True)

    object.__setattr__(report, "derived_validation_digest", "tampered")
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        market_question_specificity_risk_digest_payload(report)

    with pytest.raises(ValueError, match="report must be"):
        market_question_specificity_risk_digest_payload(report="bad")  # type: ignore[arg-type]


def test_specificity_digest_dataclasses_are_frozen() -> None:
    values = (
        _config(),
        _finding("market_alpha"),
        MarketQuestionSpecificityRiskDigestReasonCodeCount(
            "market_question_specificity_risk_passed",
            Decimal("1"),
        ),
        build_market_question_specificity_risk_digest(
            (_finding("market_alpha"),),
            config=_config(),
            generated_at=GENERATED_AT,
        ),
    )

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_specificity_digest_module_scope_excludes_execution_io_db_and_advice() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_question_specificity_risk_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_literals = (
        "investment",
        "trade",
        "buy",
        "sell",
        "order",
        "wallet",
        "authentication",
        "private_key",
        "account",
    )
    lowered_source = source.lower()
    assert not any(token in lowered_source for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "socket",
        "pathlib",
        "os",
        "http",
        "urllib",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
