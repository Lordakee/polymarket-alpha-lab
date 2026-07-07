from __future__ import annotations

import ast
import re
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 13, 45, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_category_resolution_rule_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def rule_row(
    category_id: str,
    *,
    market_count: str = "1",
    ambiguous_wording_count: str = "0",
    missing_authoritative_source_count: str = "0",
    rule_change_count: str = "0",
    disputed_outcome_count: str = "0",
    sensitive_reference_count: str = "0",
):
    digest = api()
    return digest.MarketCategoryResolutionRuleInput(
        category_id=category_id,
        market_count=d(market_count),
        ambiguous_wording_count=d(ambiguous_wording_count),
        missing_authoritative_source_count=d(missing_authoritative_source_count),
        rule_change_count=d(rule_change_count),
        disputed_outcome_count=d(disputed_outcome_count),
        sensitive_reference_count=d(sensitive_reference_count),
    )


def report(*rows):
    digest = api()
    return digest.build_market_category_resolution_rule_digest_report(
        rows,
        config=digest.MarketCategoryResolutionRuleDigestConfig(),
        generated_at=GENERATED_AT,
    )


def test_digest_summarizes_resolution_rule_risk_by_category() -> None:
    digest_report = report(
        rule_row(
            "crypto",
            market_count="10",
            ambiguous_wording_count="2",
            missing_authoritative_source_count="1",
            rule_change_count="3",
            disputed_outcome_count="2",
            sensitive_reference_count="2",
        ),
        rule_row(
            "politics",
            market_count="4",
            ambiguous_wording_count="0",
            missing_authoritative_source_count="0",
            rule_change_count="0",
            disputed_outcome_count="1",
        ),
        rule_row("sports", market_count="2"),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == "market-category-resolution-rule-digest-v0"
    assert digest_report.source_market_count == d("16")
    assert digest_report.category_count == d("3")
    assert digest_report.ambiguous_wording_rate == d("0.125000")
    assert digest_report.missing_authoritative_source_rate == d("0.062500")
    assert digest_report.rule_change_frequency == d("0.187500")
    assert digest_report.disputed_outcome_history_proxy == d("0.187500")
    assert digest_report.status == "blocked"
    assert digest_report.reason_codes == (
        "resolution_rule_ambiguity_present",
        "resolution_rule_disputes_present",
        "resolution_rule_mapping_gaps_present",
        "resolution_rule_review_blocked",
        "resolution_rule_sensitive_references_redacted",
        "resolution_rule_volatility_present",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple(row.category_id for row in digest_report.category_rows) == (
        "crypto",
        "politics",
        "sports",
    )
    crypto = digest_report.category_rows[0]
    assert crypto.market_count == d("10")
    assert crypto.ambiguous_wording_rate == d("0.200000")
    assert crypto.missing_authoritative_source_rate == d("0.100000")
    assert crypto.rule_change_frequency == d("0.300000")
    assert crypto.disputed_outcome_history_proxy == d("0.200000")
    assert crypto.readiness_status == "blocked"
    assert crypto.redacted_sensitive_reference_count == d("2")
    assert crypto.reason_codes == (
        "category_rule_ambiguity_present",
        "category_rule_disputes_present",
        "category_rule_mapping_gap_present",
        "category_rule_sensitive_references_redacted",
        "category_rule_volatility_present",
    )

    politics = digest_report.category_rows[1]
    assert politics.readiness_status == "watch"
    assert politics.reason_codes == ("category_rule_disputes_present",)

    sports = digest_report.category_rows[2]
    assert sports.readiness_status == "pass"
    assert sports.reason_codes == ("category_rule_ready",)


def test_empty_digest_is_pass_with_zero_decimal_ratios() -> None:
    digest_report = report()

    assert digest_report.source_market_count == d("0")
    assert digest_report.category_count == d("0")
    assert digest_report.ambiguous_wording_rate == d("0.000000")
    assert digest_report.missing_authoritative_source_rate == d("0.000000")
    assert digest_report.rule_change_frequency == d("0.000000")
    assert digest_report.disputed_outcome_history_proxy == d("0.000000")
    assert digest_report.status == "pass"
    assert digest_report.reason_codes == ("resolution_rule_digest_clear",)
    assert digest_report.category_rows == ()


def test_digest_rejects_floats_nonfinite_values_and_mutation() -> None:
    digest = api()

    with pytest.raises(ValueError, match="market_count must be a Decimal"):
        digest.MarketCategoryResolutionRuleInput(
            category_id="crypto",
            market_count=1.0,
            ambiguous_wording_count=d("0"),
            missing_authoritative_source_count=d("0"),
            rule_change_count=d("0"),
            disputed_outcome_count=d("0"),
            sensitive_reference_count=d("0"),
        )

    with pytest.raises(ValueError, match="market_count must be a Decimal"):
        digest.MarketCategoryResolutionRuleInput(
            category_id="crypto",
            market_count=1,
            ambiguous_wording_count=d("0"),
            missing_authoritative_source_count=d("0"),
            rule_change_count=d("0"),
            disputed_outcome_count=d("0"),
            sensitive_reference_count=d("0"),
        )

    with pytest.raises(ValueError, match="market_count must be exactly Decimal"):
        digest.MarketCategoryResolutionRuleInput(
            category_id="crypto",
            market_count=_DecimalSubclass("1"),
            ambiguous_wording_count=d("0"),
            missing_authoritative_source_count=d("0"),
            rule_change_count=d("0"),
            disputed_outcome_count=d("0"),
            sensitive_reference_count=d("0"),
        )

    with pytest.raises(ValueError, match="category_id must be one of"):
        digest.MarketCategoryResolutionRuleInput(
            category_id=_StringSubclass("crypto"),
            market_count=d("1"),
            ambiguous_wording_count=d("0"),
            missing_authoritative_source_count=d("0"),
            rule_change_count=d("0"),
            disputed_outcome_count=d("0"),
            sensitive_reference_count=d("0"),
        )

    with pytest.raises(ValueError, match="rule_change_count must be finite"):
        rule_row("crypto", rule_change_count="NaN")

    row = rule_row("sports")
    with pytest.raises(FrozenInstanceError):
        row.market_count = d("9")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        digest.MarketCategoryResolutionRuleDigestConfig(paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        digest.MarketCategoryResolutionRuleDigestConfig(readonly=False)


def test_digest_validates_counts_inputs_datetimes_and_deterministic_rows() -> None:
    digest = api()

    with pytest.raises(ValueError, match="market_count is required"):
        rule_row("crypto", market_count="0", ambiguous_wording_count="1")

    with pytest.raises(ValueError, match="ambiguous_wording_count must not exceed"):
        rule_row("crypto", market_count="1", ambiguous_wording_count="2")

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(rule_row("crypto"), rule_row("crypto"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_market_category_resolution_rule_digest_report(
            (rule_row("crypto"),),
            config=digest.MarketCategoryResolutionRuleDigestConfig(),
            generated_at=datetime(2026, 7, 2, 13, 45),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_market_category_resolution_rule_digest_report(
            (rule_row("crypto"),),
            config=digest.MarketCategoryResolutionRuleDigestConfig(),
            generated_at=datetime(2026, 7, 2, 13, 45, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest.build_market_category_resolution_rule_digest_report(
            (rule_row("crypto"),),
            config=digest.MarketCategoryResolutionRuleDigestConfig(),
            generated_at=_DatetimeSubclass(2026, 7, 2, 13, 45, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="category_rows must use deterministic ordering"):
        digest.MarketCategoryResolutionRuleDigestReport(
            generated_at=GENERATED_AT,
            config_version="market-category-resolution-rule-digest-v0",
            source_market_count=d("2"),
            category_count=d("2"),
            ambiguous_wording_rate=d("0.000000"),
            missing_authoritative_source_rate=d("0.000000"),
            rule_change_frequency=d("0.000000"),
            disputed_outcome_history_proxy=d("0.000000"),
            status="pass",
            reason_codes=("resolution_rule_digest_clear",),
            category_rows=(
                digest.MarketCategoryResolutionRuleCategoryRow(
                    category_id="sports",
                    market_count=d("1"),
                    ambiguous_wording_count=d("0"),
                    missing_authoritative_source_count=d("0"),
                    rule_change_count=d("0"),
                    disputed_outcome_count=d("0"),
                    redacted_sensitive_reference_count=d("0"),
                    ambiguous_wording_rate=d("0.000000"),
                    missing_authoritative_source_rate=d("0.000000"),
                    rule_change_frequency=d("0.000000"),
                    disputed_outcome_history_proxy=d("0.000000"),
                    readiness_status="pass",
                    reason_codes=("category_rule_ready",),
                ),
                digest.MarketCategoryResolutionRuleCategoryRow(
                    category_id="crypto",
                    market_count=d("1"),
                    ambiguous_wording_count=d("0"),
                    missing_authoritative_source_count=d("0"),
                    rule_change_count=d("0"),
                    disputed_outcome_count=d("0"),
                    redacted_sensitive_reference_count=d("0"),
                    ambiguous_wording_rate=d("0.000000"),
                    missing_authoritative_source_rate=d("0.000000"),
                    rule_change_frequency=d("0.000000"),
                    disputed_outcome_history_proxy=d("0.000000"),
                    readiness_status="pass",
                    reason_codes=("category_rule_ready",),
                ),
            ),
        )


def test_payload_is_redacted_json_ready_and_omits_sensitive_surfaces() -> None:
    payload = api().market_category_resolution_rule_digest_payload(
        report(
            rule_row(
                "crypto",
                market_count="2",
                ambiguous_wording_count="1",
                sensitive_reference_count="3",
            ),
        ),
    )

    payload_text = repr(payload).lower()
    for forbidden in (
        "market_slug",
        "question",
        "payload",
        "authentication",
        "wallet",
        "account",
        "order",
        "advice",
    ):
        assert forbidden not in payload_text
    assert payload["source_market_count"] == "2"
    assert payload["category_rows"][0]["category_id"] == "crypto"
    assert payload["category_rows"][0]["redacted_sensitive_reference_count"] == "3"


def test_derived_validation_digest_is_deterministic_and_payload_bound() -> None:
    digest = api()
    first = report(
        rule_row("sports", market_count="2"),
        rule_row(
            "crypto",
            market_count="4",
            ambiguous_wording_count="1",
            sensitive_reference_count="1",
        ),
    )
    reordered = report(
        rule_row(
            "crypto",
            market_count="4",
            ambiguous_wording_count="1",
            sensitive_reference_count="1",
        ),
        rule_row("sports", market_count="2"),
    )

    assert re.fullmatch(r"[0-9a-f]{64}", first.derived_validation_digest)
    assert first.derived_validation_digest == reordered.derived_validation_digest
    assert tuple(row.derived_validation_digest for row in first.category_rows) == tuple(
        row.derived_validation_digest for row in reordered.category_rows
    )

    payload = digest.market_category_resolution_rule_digest_payload(first)
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["category_rows"][0]["derived_validation_digest"] == (
        first.category_rows[0].derived_validation_digest
    )

    object.__setattr__(first.category_rows[0], "ambiguous_wording_count", d("0"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        digest.market_category_resolution_rule_digest_payload(first)


def test_payload_dict_path_rejects_numeric_drift_flags_and_unsafe_values() -> None:
    digest = api()
    payload = digest.market_category_resolution_rule_digest_payload(
        report(
            rule_row(
                "crypto",
                market_count="2",
                ambiguous_wording_count="1",
                sensitive_reference_count="1",
            ),
        ),
    )

    assert digest.market_category_resolution_rule_digest_payload(payload) == payload

    with pytest.raises(ValueError, match="Decimal"):
        digest.market_category_resolution_rule_digest_payload(
            {**payload, "source_market_count": 2},
        )

    with pytest.raises(ValueError, match="float"):
        digest.market_category_resolution_rule_digest_payload(
            {**payload, "ambiguous_wording_rate": 0.5},
        )

    with pytest.raises(ValueError, match="readonly"):
        digest.market_category_resolution_rule_digest_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON object keys"):
        digest.market_category_resolution_rule_digest_payload({1: "x", **payload})

    with pytest.raises(ValueError, match="timezone-aware"):
        digest.market_category_resolution_rule_digest_payload(
            {**payload, "generated_at": datetime(2026, 7, 2, 13, 45)},
        )

    with pytest.raises(ValueError, match="unsafe"):
        digest.market_category_resolution_rule_digest_payload(
            {**payload, "wallet": "paper"},
        )

    with pytest.raises(ValueError, match="unsafe"):
        digest.market_category_resolution_rule_digest_payload(
            {
                **payload,
                "category_rows": [
                    {
                        **payload["category_rows"][0],
                        "redacted_reference": "token=redacted",
                    },
                ],
            },
        )


def test_module_scope_has_no_live_network_storage_or_sensitive_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_category_resolution_rule_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "authentication",
        "wallet",
        "account",
        "market_slug",
        "question",
        "payload_json",
        "investment_recommendation",
        "network",
        "request",
        "http",
        "urllib",
        "open(",
        "read(",
        "write(",
        "db",
        "database",
        "fast",
        "advice",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
