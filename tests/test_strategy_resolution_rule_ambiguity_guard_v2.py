from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_resolution_rule_ambiguity_guard_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(
    market_id: str,
    *,
    event_slug: str,
    category: str = "crypto",
    rule_text_quality_score: Decimal = d("0.950000"),
    official_resolution_source_count: int = 2,
    conflicting_interpretation_count: int = 0,
    missing_deadline_flag: bool = False,
    manual_review_required: bool = False,
):
    guard = module()
    return guard.StrategyResolutionRuleAmbiguityGuardV2Input(
        market_id=market_id,
        event_slug=event_slug,
        category=category,
        rule_text_quality_score=rule_text_quality_score,
        official_resolution_source_count=official_resolution_source_count,
        conflicting_interpretation_count=conflicting_interpretation_count,
        missing_deadline_flag=missing_deadline_flag,
        manual_review_required=manual_review_required,
    )


def build_report(*inputs):
    guard = module()
    return guard.build_strategy_resolution_rule_ambiguity_guard_v2_report(
        inputs,
        config=guard.StrategyResolutionRuleAmbiguityGuardV2Config(
            config_version="resolution-rule-ambiguity-guard-test-v0",
            watch_ambiguity_score=d("0.250000"),
            block_ambiguity_score=d("0.700000"),
        ),
        generated_at=GENERATED_AT,
    )


def test_builds_report_only_resolution_rule_guard_in_deterministic_risk_order() -> None:
    clear = candidate(
        "condition-clear",
        event_slug="btc-clear-resolution",
        category="crypto",
        rule_text_quality_score=d("0.950000"),
        official_resolution_source_count=2,
    )
    watch = candidate(
        "condition-watch",
        event_slug="btc-watch-resolution",
        category="crypto",
        rule_text_quality_score=d("0.640000"),
        official_resolution_source_count=1,
    )
    blocked = candidate(
        "condition-block",
        event_slug="btc-block-resolution",
        category="crypto",
        rule_text_quality_score=d("0.420000"),
        official_resolution_source_count=0,
        conflicting_interpretation_count=2,
        missing_deadline_flag=True,
        manual_review_required=True,
    )

    report = build_report(clear, blocked, watch)

    assert tuple(row.market_id for row in report.rows) == (
        "condition-block",
        "condition-watch",
        "condition-clear",
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.ambiguity_score for row in report.rows) == (
        d("1.000000"),
        d("0.460000"),
        d("0.050000"),
    )
    assert report.report_status == "block"
    assert report.candidate_count == 3
    assert report.pass_count == 1
    assert report.watch_count == 1
    assert report.block_count == 1
    assert report.ambiguous_candidate_count == 2
    assert report.missing_deadline_count == 1
    assert report.conflicting_interpretation_count == 2
    assert report.max_ambiguity_score == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert report.rows[0].reason_codes == (
        "resolution_rule_ambiguity_block",
        "manual_review_required",
        "missing_resolution_deadline",
        "no_official_resolution_sources",
        "conflicting_interpretations_present",
        "low_rule_text_quality_score",
    )
    assert report.rows[1].reason_codes == (
        "resolution_rule_ambiguity_watch",
        "limited_official_resolution_sources",
        "low_rule_text_quality_score",
    )
    assert tuple((item.reason_code, item.count) for item in report.reason_code_counts) == (
        ("low_rule_text_quality_score", 2),
        ("conflicting_interpretations_present", 1),
        ("limited_official_resolution_sources", 1),
        ("manual_review_required", 1),
        ("missing_resolution_deadline", 1),
        ("no_official_resolution_sources", 1),
        ("resolution_criteria_clear", 1),
        ("resolution_rule_ambiguity_block", 1),
        ("resolution_rule_ambiguity_watch", 1),
    )


def test_report_has_stable_validation_digest_and_safe_json_payload() -> None:
    first = candidate(
        "condition-a",
        event_slug="same-event",
        category="politics",
        rule_text_quality_score=d("0.550000"),
        official_resolution_source_count=1,
    )
    second = candidate(
        "condition-b",
        event_slug="same-event",
        category="politics",
        rule_text_quality_score=d("0.950000"),
        official_resolution_source_count=2,
    )

    report = build_report(first, second)
    same_report = build_report(second, first)
    different_report = build_report(second)
    payload = module().strategy_resolution_rule_ambiguity_guard_v2_payload(report)

    assert report.validation_digest == same_report.validation_digest
    assert report.validation_digest != different_report.validation_digest
    assert len(report.validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.validation_digest)
    assert payload == report.payload
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    assert payload["validation_digest"] == report.validation_digest
    assert payload["max_ambiguity_score"] == "0.550000"
    assert payload["rows"][0]["ambiguity_score"] == "0.550000"
    assert payload["rows"][0]["reason_codes"] == [
        "resolution_rule_ambiguity_watch",
        "limited_official_resolution_sources",
        "low_rule_text_quality_score",
    ]
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_empty_input_returns_empty_status_and_zero_decimals() -> None:
    report = build_report()

    assert report.report_status == "empty"
    assert report.candidate_count == 0
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.block_count == 0
    assert report.ambiguous_candidate_count == 0
    assert report.missing_deadline_count == 0
    assert report.conflicting_interpretation_count == 0
    assert report.max_ambiguity_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == ()
    assert report.payload["max_ambiguity_score"] == "0.000000"
    assert report.payload["report_status"] == "empty"


def test_dataclasses_are_frozen_decimal_only_and_public_api_is_local() -> None:
    guard = module()

    assert guard.__all__ == (
        "DEFAULT_STRATEGY_RESOLUTION_RULE_AMBIGUITY_GUARD_V2_CONFIG_VERSION",
        "StrategyResolutionRuleAmbiguityGuardV2Config",
        "StrategyResolutionRuleAmbiguityGuardV2Input",
        "StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount",
        "StrategyResolutionRuleAmbiguityGuardV2Report",
        "StrategyResolutionRuleAmbiguityGuardV2Row",
        "build_strategy_resolution_rule_ambiguity_guard_v2_report",
        "strategy_resolution_rule_ambiguity_guard_v2_payload",
    )
    for exported_name in guard.__all__:
        value = getattr(guard, exported_name)
        if isinstance(value, type) and is_dataclass(value):
            assert all(field.default is not None for field in fields(value))

    report = build_report(
        candidate(
            "condition-frozen",
            event_slug="frozen-resolution",
            rule_text_quality_score=d("0.950000"),
        ),
    )
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"  # type: ignore[misc]

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="rule_text_quality_score must be a Decimal"):
        candidate(
            "condition-derived-decimal",
            event_slug="derived-decimal-resolution",
            rule_text_quality_score=DerivedDecimal("0.950000"),
        )
    with pytest.raises(ValueError, match="rule_text_quality_score must be a Decimal"):
        candidate(
            "condition-float",
            event_slug="float-resolution",
            rule_text_quality_score=0.95,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="manual_review_required must be a bool"):
        candidate(
            "condition-bad-flag",
            event_slug="bad-flag-resolution",
            manual_review_required=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        guard.StrategyResolutionRuleAmbiguityGuardV2Input(
            market_id="condition-live",
            event_slug="live-resolution",
            category="crypto",
            rule_text_quality_score=d("0.950000"),
            official_resolution_source_count=2,
            conflicting_interpretation_count=0,
            missing_deadline_flag=False,
            manual_review_required=False,
            paper_only=False,
        )


def test_generated_at_is_normalized_to_utc_and_naive_datetimes_are_rejected() -> None:
    guard = module()

    report = guard.build_strategy_resolution_rule_ambiguity_guard_v2_report(
        (
            candidate(
                "condition-time",
                event_slug="time-resolution",
                rule_text_quality_score=d("0.950000"),
            ),
        ),
        config=guard.StrategyResolutionRuleAmbiguityGuardV2Config(),
        generated_at=datetime(2026, 7, 7, 8, 0, tzinfo=timezone.utc),
    )

    assert report.generated_at == datetime(2026, 7, 7, 8, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        guard.build_strategy_resolution_rule_ambiguity_guard_v2_report(
            (
                candidate(
                    "condition-naive-time",
                    event_slug="naive-time-resolution",
                    rule_text_quality_score=d("0.950000"),
                ),
            ),
            config=guard.StrategyResolutionRuleAmbiguityGuardV2Config(),
            generated_at=datetime(2026, 7, 7, 8, 0),
        )
