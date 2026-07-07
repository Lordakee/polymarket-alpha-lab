from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.research_news_coverage_gap_score"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_news_coverage_gap_score.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "min_pass_source_family_count": d("3"),
        "min_watch_source_family_count": d("2"),
        "watch_source_age_seconds": d("86400.000000"),
        "block_source_age_seconds": d("259200.000000"),
        "watch_conflict_ratio": d("0.100000"),
        "block_conflict_ratio": d("0.500000"),
        "watch_attention_gap_ratio": d("0.250000"),
        "block_attention_gap_ratio": d("0.750000"),
    }
    values.update(overrides)
    return module.ResearchNewsCoverageGapScoreConfig(**values)


def summary(
    label: str,
    *,
    topic_bucket: str = "macro-policy",
    source_family_count: Decimal = d("3"),
    fresh_source_count: Decimal = d("3"),
    total_summary_count: Decimal = d("6"),
    conflicting_summary_count: Decimal = d("0"),
    attention_baseline_count: Decimal = d("8"),
    coverage_mention_count: Decimal = d("8"),
    latest_source_age_seconds: Decimal = d("3600.000000"),
):
    module = api()
    return module.ResearchNewsCoverageSummary(
        redacted_coverage_label=label,
        public_topic_bucket=topic_bucket,
        source_family_count=source_family_count,
        fresh_source_count=fresh_source_count,
        total_summary_count=total_summary_count,
        conflicting_summary_count=conflicting_summary_count,
        attention_baseline_count=attention_baseline_count,
        coverage_mention_count=coverage_mention_count,
        latest_source_age_seconds=latest_source_age_seconds,
    )


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_news_coverage_gap_score_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_scores_pass_watch_and_block_rows_and_payload() -> None:
    module = api()

    report = build_report(
        summary("alpha-pass", topic_bucket="macro-policy"),
        summary(
            "beta-watch",
            topic_bucket="weather-risk",
            source_family_count=d("2"),
            fresh_source_count=d("1"),
            total_summary_count=d("10"),
            conflicting_summary_count=d("2"),
            attention_baseline_count=d("20"),
            coverage_mention_count=d("14"),
            latest_source_age_seconds=d("90000.000000"),
        ),
        summary(
            "gamma-block",
            topic_bucket="public-health",
            source_family_count=d("1"),
            fresh_source_count=d("0"),
            total_summary_count=d("8"),
            conflicting_summary_count=d("5"),
            attention_baseline_count=d("40"),
            coverage_mention_count=d("5"),
            latest_source_age_seconds=d("300000.000000"),
        ),
    )

    assert type(report) is module.ResearchNewsCoverageGapScoreReport
    assert report.status == "block"
    assert report.summary_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.low_source_diversity_count == d("2")
    assert report.stale_coverage_count == d("2")
    assert report.conflict_count == d("2")
    assert report.attention_gap_count == d("2")
    assert report.max_attention_gap_ratio == d("0.875000")
    assert report.max_conflict_ratio == d("0.625000")
    assert report.max_coverage_gap_score == d("1.000000")
    assert report.reason_codes == (
        "news_coverage_low_source_diversity",
        "news_coverage_stale_public_coverage",
        "news_coverage_conflicting_summaries",
        "news_coverage_attention_gap",
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert report.rows[0].redacted_coverage_label == "gamma-block"
    assert report.rows[0].coverage_gap_score == d("1.000000")
    assert report.rows[1].attention_gap_ratio == d("0.300000")
    assert report.rows[2].status == "pass"
    assert report.rows[2].reason_codes == ()

    payload = module.research_news_coverage_gap_score_report_payload(report)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["summary_count"] == "3"
    assert payload["max_coverage_gap_score"] == "1.000000"
    assert payload["rows"][0]["coverage_gap_score"] == "1.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert module.validate_research_news_coverage_gap_score_public_payload(payload)
    assert_no_numeric_payload(payload)
    assert_no_unsafe_public_surface(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_dataclasses_are_frozen_decimal_exact_and_hard_flagged() -> None:
    module = api()

    for klass in (
        module.ResearchNewsCoverageGapScoreConfig,
        module.ResearchNewsCoverageSummary,
        module.ResearchNewsCoverageGapScoreReasonCodeCount,
        module.ResearchNewsCoverageGapScoreRow,
        module.ResearchNewsCoverageGapScoreReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(ValueError, match="min_pass_source_family_count"):
        config(min_pass_source_family_count=3)
    with pytest.raises(ValueError, match="watch_source_age_seconds"):
        config(watch_source_age_seconds=_DecimalSubclass("86400.000000"))
    with pytest.raises(ValueError, match="source_family_count"):
        summary("bad-decimal", source_family_count=Decimal("3.1"))

    item = summary("frozen-item")
    with pytest.raises(FrozenInstanceError):
        item.redacted_coverage_label = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    report = build_report(item)
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    for field in fields(report):
        if field.name.endswith("_count") or field.name.endswith("_ratio") or (
            field.name.endswith("_score")
        ):
            assert type(getattr(report, field.name)) is Decimal
    for row in report.rows:
        for field in fields(row):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_score")
                or field.name.endswith("_seconds")
            ):
                assert type(getattr(row, field.name)) is Decimal


def test_rejects_leaks_in_inputs_and_public_payload() -> None:
    module = api()

    for leaked_label in (
        "candidate-123",
        "market_slug_event",
        "will-this-question-resolve",
        "source_ref_abc",
        "https://example.invalid/story",
        "database_dsn",
        "api_token",
        "wallet-address",
        "auth-header",
        "order-ticket",
        "trade-log",
        "position-size",
        "buy-signal",
        "sell-signal",
        "recommendation-ready",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            summary(leaked_label)

    payload = module.research_news_coverage_gap_score_report_payload(
        build_report(summary("safe-public-label")),
    )
    for forbidden_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "database_dsn",
        "table_name",
        "wallet_address",
        "auth_token",
        "order_id",
        "trade_id",
        "position_size",
        "buy_action",
        "sell_action",
        "recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            module.validate_research_news_coverage_gap_score_public_payload(
                {**payload, forbidden_key: "unsafe"},
            )

    with pytest.raises(ValueError, match="Decimal strings"):
        module.validate_research_news_coverage_gap_score_public_payload(
            {**payload, "summary_count": 1},
        )


def test_hard_flags_required_on_public_payload() -> None:
    module = api()
    payload = module.research_news_coverage_gap_score_report_payload(
        build_report(summary("hard-flags")),
    )

    for flag in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=flag):
            module.validate_research_news_coverage_gap_score_public_payload(
                {**payload, flag: False},
            )


def test_report_and_digest_are_deterministic() -> None:
    module = api()
    first = build_report(
        summary("zeta-pass", topic_bucket="z-bucket"),
        summary(
            "alpha-watch",
            topic_bucket="a-bucket",
            source_family_count=d("2"),
            fresh_source_count=d("1"),
            total_summary_count=d("4"),
            conflicting_summary_count=d("1"),
            attention_baseline_count=d("10"),
            coverage_mention_count=d("6"),
            latest_source_age_seconds=d("90000.000000"),
        ),
    )
    second = build_report(
        summary(
            "alpha-watch",
            topic_bucket="a-bucket",
            source_family_count=d("2"),
            fresh_source_count=d("1"),
            total_summary_count=d("4"),
            conflicting_summary_count=d("1"),
            attention_baseline_count=d("10"),
            coverage_mention_count=d("6"),
            latest_source_age_seconds=d("90000.000000"),
        ),
        summary("zeta-pass", topic_bucket="z-bucket"),
    )

    assert first == second
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_news_coverage_gap_score_report_payload(
        first,
    ) == module.research_news_coverage_gap_score_report_payload(second)


def assert_no_numeric_payload(value: Any) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int | float | Decimal):
        raise AssertionError(f"numeric payload value leaked: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_payload(item)
    if isinstance(value, list | tuple):
        for item in value:
            assert_no_numeric_payload(item)


def assert_no_unsafe_public_surface(payload: dict[str, Any]) -> None:
    payload_text = repr(payload).casefold()
    for forbidden in (
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert forbidden not in payload_text
