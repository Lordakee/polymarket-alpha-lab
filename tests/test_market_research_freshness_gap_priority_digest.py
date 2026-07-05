from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

import polymarket_alpha_lab.market_research_freshness_gap_priority_digest as freshness_digest
from polymarket_alpha_lab.market_research_freshness_gap_priority_digest import (
    DEFAULT_MARKET_RESEARCH_FRESHNESS_GAP_PRIORITY_DIGEST_CONFIG_VERSION,
    MarketResearchFreshnessGapPriorityDigestConfig,
    MarketResearchFreshnessGapPriorityDigestInput,
    MarketResearchFreshnessGapPriorityDigestReport,
    MarketResearchFreshnessGapPriorityDigestRow,
    build_market_research_freshness_gap_priority_digest,
)


GENERATED_AT = datetime(2026, 7, 2, 17, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _input(**overrides: object) -> MarketResearchFreshnessGapPriorityDigestInput:
    values: dict[str, object] = {
        "market_ref": "raw-sensitive-market-ref-token",
        "research_topic": "resolution_source_recheck",
        "team_id": "politics",
        "latest_source_at": GENERATED_AT - timedelta(hours=20),
        "latest_evidence_at": GENERATED_AT - timedelta(hours=30),
        "latest_forecast_at": GENERATED_AT - timedelta(hours=28),
        "latest_source_age_hours": d("20.000000"),
        "evidence_age_hours": d("30.000000"),
        "forecast_age_hours": d("28.000000"),
        "probability_movement": d("0.120000"),
        "quorum_share": d("0.400000"),
    }
    values.update(overrides)
    return MarketResearchFreshnessGapPriorityDigestInput(**values)


def test_digest_prioritizes_freshness_gaps_with_decimal_metrics_and_reason_codes() -> None:
    report = build_market_research_freshness_gap_priority_digest(
        (
            _input(
                market_ref="least-sensitive-ref",
                research_topic="ready_topic",
                team_id="macro_rates",
                latest_source_age_hours=d("2.000000"),
                evidence_age_hours=d("3.000000"),
                forecast_age_hours=d("4.000000"),
                probability_movement=d("0.010000"),
                quorum_share=d("0.900000"),
            ),
            _input(
                market_ref="top-secret-wallet-order-ref",
                research_topic="resolution_source_recheck",
                team_id="politics",
                latest_source_age_hours=d("30.000000"),
                evidence_age_hours=d("40.000000"),
                forecast_age_hours=d("35.000000"),
                probability_movement=d("0.200000"),
                quorum_share=d("0.300000"),
            ),
            _input(
                market_ref="middle-sensitive-ref",
                research_topic="forecast_review",
                team_id="crypto_btc",
                latest_source_age_hours=d("30.000000"),
                evidence_age_hours=d("25.000000"),
                forecast_age_hours=d("32.000000"),
                probability_movement=d("0.180000"),
                quorum_share=d("0.300000"),
            ),
        ),
        config=MarketResearchFreshnessGapPriorityDigestConfig(
            config_version="market-research-gap-test-v0",
            source_age_blocked_threshold_hours=d("24.000000"),
            evidence_age_blocked_threshold_hours=d("36.000000"),
            forecast_age_blocked_threshold_hours=d("30.000000"),
            probability_movement_blocked_threshold=d("0.150000"),
            quorum_share_blocked_threshold=d("0.500000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert type(report) is MarketResearchFreshnessGapPriorityDigestReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-research-gap-test-v0"
    assert report.digest_status == "blocked"
    assert report.input_count == d("3")
    assert report.blocked_count == d("2")
    assert report.watch_count == d("0")
    assert report.ready_count == d("1")
    assert report.highest_freshness_gap_score == d("157.000000")
    assert report.average_freshness_gap_score == d("101.000000")
    assert report.blocked_ratio == d("0.666667")
    assert report.low_quorum_ratio == d("0.666667")
    assert report.reason_codes == (
        "freshness_gap_blocked_markets_present",
        "latest_source_stale_detected",
        "evidence_stale_detected",
        "forecast_stale_detected",
        "probability_movement_detected",
        "quorum_share_low_detected",
    )
    assert tuple(row.redacted_market_ref for row in report.priority_rows) == (
        "politics_research_gap_000001",
        "crypto_btc_research_gap_000002",
        "macro_rates_research_gap_000003",
    )
    assert tuple(row.freshness_gap_score for row in report.priority_rows) == (
        d("157.000000"),
        d("134.000000"),
        d("12.000000"),
    )

    top = report.priority_rows[0]
    assert type(top) is MarketResearchFreshnessGapPriorityDigestRow
    assert top.priority_status == "blocked"
    assert top.reason_codes == (
        "latest_source_stale",
        "evidence_stale",
        "forecast_stale",
        "probability_movement_high",
        "quorum_share_low",
    )
    assert top.priority_sequence == d("1")
    assert top.paper_only is True
    assert top.report_only is True
    assert top.readonly is True
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    serialized = repr(asdict(report)).lower()
    assert "top-secret-wallet-order-ref" not in serialized
    assert "middle-sensitive-ref" not in serialized
    assert "least-sensitive-ref" not in serialized
    assert "token" not in serialized
    assert "private" not in serialized
    assert "wallet" not in serialized
    assert "account" not in serialized
    assert "order" not in serialized
    assert "auth" not in serialized
    assert "advice" not in serialized


def test_digest_empty_and_ready_reports_are_report_only_diagnostics() -> None:
    empty = build_market_research_freshness_gap_priority_digest(
        (),
        config=MarketResearchFreshnessGapPriorityDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert empty.digest_status == "no_inputs"
    assert empty.input_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.ready_count == d("0")
    assert empty.highest_freshness_gap_score == d("0.000000")
    assert empty.average_freshness_gap_score == d("0.000000")
    assert empty.blocked_ratio == d("0.000000")
    assert empty.low_quorum_ratio == d("0.000000")
    assert empty.reason_codes == ("freshness_gap_no_inputs",)
    assert empty.priority_rows == ()

    ready = build_market_research_freshness_gap_priority_digest(
        (
            _input(
                latest_source_age_hours=d("1.000000"),
                evidence_age_hours=d("2.000000"),
                forecast_age_hours=d("3.000000"),
                probability_movement=d("0.010000"),
                quorum_share=d("0.900000"),
            ),
        ),
        config=MarketResearchFreshnessGapPriorityDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert ready.digest_status == "pass"
    assert ready.reason_codes == ("freshness_gap_digest_passed",)
    assert ready.ready_count == d("1")
    assert ready.priority_rows[0].priority_status == "ready"
    assert ready.priority_rows[0].reason_codes == ("freshness_gap_ready",)


def test_digest_reason_code_counts_are_deterministic_positive_and_serialized() -> None:
    reason_count_type = getattr(
        freshness_digest,
        "MarketResearchFreshnessGapPriorityDigestReasonCodeCount",
    )
    payload_fn = getattr(
        freshness_digest,
        "market_research_freshness_gap_priority_digest_payload",
    )
    report = build_market_research_freshness_gap_priority_digest(
        (
            _input(
                market_ref="least-sensitive-ref",
                research_topic="ready_topic",
                team_id="macro_rates",
                latest_source_age_hours=d("2.000000"),
                evidence_age_hours=d("3.000000"),
                forecast_age_hours=d("4.000000"),
                probability_movement=d("0.010000"),
                quorum_share=d("0.900000"),
            ),
            _input(
                market_ref="top-secret-wallet-order-ref",
                research_topic="resolution_source_recheck",
                team_id="politics",
                latest_source_age_hours=d("30.000000"),
                evidence_age_hours=d("40.000000"),
                forecast_age_hours=d("35.000000"),
                probability_movement=d("0.200000"),
                quorum_share=d("0.300000"),
            ),
            _input(
                market_ref="middle-sensitive-ref",
                research_topic="forecast_review",
                team_id="crypto_btc",
                latest_source_age_hours=d("30.000000"),
                evidence_age_hours=d("25.000000"),
                forecast_age_hours=d("32.000000"),
                probability_movement=d("0.180000"),
                quorum_share=d("0.300000"),
            ),
        ),
        config=MarketResearchFreshnessGapPriorityDigestConfig(
            config_version="market-research-gap-test-v0",
        ),
        generated_at=GENERATED_AT,
    )

    assert all(type(item) is reason_count_type for item in report.reason_code_counts)
    assert tuple(item.reason_code for item in report.reason_code_counts) == report.reason_codes
    assert tuple(
        (item.reason_code, item.count, item.row_ratio)
        for item in report.reason_code_counts
    ) == (
        (
            "freshness_gap_blocked_markets_present",
            d("2.000000"),
            d("0.666667"),
        ),
        ("latest_source_stale_detected", d("2.000000"), d("0.666667")),
        ("evidence_stale_detected", d("1.000000"), d("0.333333")),
        ("forecast_stale_detected", d("2.000000"), d("0.666667")),
        ("probability_movement_detected", d("2.000000"), d("0.666667")),
        ("quorum_share_low_detected", d("2.000000"), d("0.666667")),
    )

    payload = payload_fn(report)
    assert payload["generated_at"] == "2026-07-02T17:30:00+00:00"
    assert payload["input_count"] == "3.000000"
    assert payload["blocked_ratio"] == "0.666667"
    assert payload["priority_rows"][0]["priority_sequence"] == "1.000000"
    assert payload["priority_rows"][0]["freshness_gap_score"] == "157.000000"
    assert payload["reason_code_counts"][0]["count"] == "2.000000"
    assert payload["reason_code_counts"][2]["row_ratio"] == "0.333333"

    serialized = repr(payload).lower()
    assert "top-secret-wallet-order-ref" not in serialized
    assert "middle-sensitive-ref" not in serialized
    assert "least-sensitive-ref" not in serialized
    assert "token" not in serialized
    assert "wallet" not in serialized
    assert "order" not in serialized


def test_digest_payload_rejects_tampered_nested_public_values() -> None:
    report = build_market_research_freshness_gap_priority_digest(
        (_input(),),
        config=MarketResearchFreshnessGapPriorityDigestConfig(),
        generated_at=GENERATED_AT,
    )

    object.__setattr__(report.priority_rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        freshness_digest.market_research_freshness_gap_priority_digest_payload(report)
    object.__setattr__(report.priority_rows[0], "readonly", True)

    object.__setattr__(report.reason_code_counts[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        freshness_digest.market_research_freshness_gap_priority_digest_payload(report)
    object.__setattr__(report.reason_code_counts[0], "report_only", True)

    object.__setattr__(report.priority_rows[0], "freshness_gap_score", d("116.0000001"))
    with pytest.raises(ValueError, match="six decimals"):
        freshness_digest.market_research_freshness_gap_priority_digest_payload(report)


def test_digest_empty_reason_count_is_synthetic_but_manual_zero_count_is_rejected() -> None:
    reason_count_type = getattr(
        freshness_digest,
        "MarketResearchFreshnessGapPriorityDigestReasonCodeCount",
    )
    empty = build_market_research_freshness_gap_priority_digest(
        (),
        config=MarketResearchFreshnessGapPriorityDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert empty.digest_status == "no_inputs"
    assert empty.reason_codes == ("freshness_gap_no_inputs",)
    assert empty.reason_code_counts == (
        reason_count_type(
            reason_code="freshness_gap_no_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    with pytest.raises(ValueError, match="count"):
        reason_count_type(
            reason_code="freshness_gap_no_inputs",
            count=d("0.000000"),
            row_ratio=d("0.000000"),
        )


def test_digest_custom_thresholds_drive_status_without_breaking_row_validation() -> None:
    report = build_market_research_freshness_gap_priority_digest(
        (
            _input(
                latest_source_age_hours=d("5.000000"),
                evidence_age_hours=d("10.000000"),
                forecast_age_hours=d("5.000000"),
                probability_movement=d("0.010000"),
                quorum_share=d("0.600000"),
            ),
        ),
        config=MarketResearchFreshnessGapPriorityDigestConfig(
            source_age_blocked_threshold_hours=d("40.000000"),
            evidence_age_blocked_threshold_hours=d("50.000000"),
            forecast_age_blocked_threshold_hours=d("50.000000"),
            probability_movement_blocked_threshold=d("0.500000"),
            quorum_share_blocked_threshold=d("0.700000"),
            source_age_watch_threshold_hours=d("20.000000"),
            evidence_age_watch_threshold_hours=d("20.000000"),
            forecast_age_watch_threshold_hours=d("20.000000"),
            probability_movement_watch_threshold=d("0.250000"),
            quorum_share_watch_threshold=d("0.800000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "blocked"
    assert report.blocked_count == d("1.000000")
    assert report.low_quorum_ratio == d("1.000000")
    assert report.priority_rows[0].priority_status == "blocked"
    assert report.priority_rows[0].reason_codes == ("quorum_share_low",)
    assert report.priority_rows[0].freshness_gap_score == d("29.000000")
    assert report.reason_code_counts == (
        getattr(
            freshness_digest,
            "MarketResearchFreshnessGapPriorityDigestReasonCodeCount",
        )(
            reason_code="freshness_gap_blocked_markets_present",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
        getattr(
            freshness_digest,
            "MarketResearchFreshnessGapPriorityDigestReasonCodeCount",
        )(
            reason_code="quorum_share_low_detected",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )


def test_digest_public_constructors_reject_noncanonical_ordering() -> None:
    reason_count_type = getattr(
        freshness_digest,
        "MarketResearchFreshnessGapPriorityDigestReasonCodeCount",
    )
    report = build_market_research_freshness_gap_priority_digest(
        (
            _input(
                latest_source_age_hours=d("30.000000"),
                evidence_age_hours=d("40.000000"),
                forecast_age_hours=d("35.000000"),
                probability_movement=d("0.200000"),
                quorum_share=d("0.300000"),
            ),
            _input(
                team_id="crypto_btc",
                research_topic="forecast_review",
                latest_source_age_hours=d("13.000000"),
                evidence_age_hours=d("2.000000"),
                forecast_age_hours=d("3.000000"),
                probability_movement=d("0.010000"),
                quorum_share=d("0.900000"),
            ),
        ),
        config=MarketResearchFreshnessGapPriorityDigestConfig(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report.priority_rows[0],
            reason_codes=tuple(reversed(report.priority_rows[0].reason_codes)),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=tuple(reversed(report.reason_code_counts)))
    with pytest.raises(ValueError, match="exactly"):
        class BadReasonCount(reason_count_type):
            pass


def test_digest_normalizes_offset_datetimes_and_rejects_naive_datetimes() -> None:
    generated_at = datetime(2026, 7, 2, 13, 30, tzinfo=timezone(timedelta(hours=-4)))
    source_at = datetime(2026, 7, 2, 18, 0, tzinfo=timezone(timedelta(hours=2)))
    evidence_at = datetime(2026, 7, 2, 17, 0, tzinfo=timezone(timedelta(hours=1)))
    forecast_at = datetime(2026, 7, 2, 15, 0, tzinfo=UTC)

    report = build_market_research_freshness_gap_priority_digest(
        (
            _input(
                latest_source_at=source_at,
                latest_evidence_at=evidence_at,
                latest_forecast_at=forecast_at,
                latest_source_age_hours=d("1.500000"),
                evidence_age_hours=d("1.500000"),
                forecast_age_hours=d("2.500000"),
            ),
        ),
        config=MarketResearchFreshnessGapPriorityDigestConfig(),
        generated_at=generated_at,
    )

    row = report.priority_rows[0]
    assert report.generated_at == GENERATED_AT
    assert row.latest_source_at == datetime(2026, 7, 2, 16, 0, tzinfo=UTC)
    assert row.latest_evidence_at == datetime(2026, 7, 2, 16, 0, tzinfo=UTC)
    assert row.latest_forecast_at == datetime(2026, 7, 2, 15, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="timezone-aware"):
        build_market_research_freshness_gap_priority_digest(
            (),
            config=MarketResearchFreshnessGapPriorityDigestConfig(),
            generated_at=datetime(2026, 7, 2, 17, 30),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        _input(latest_source_at=datetime(2026, 7, 2, 17, 0))

    class MissingOffset(tzinfo):
        def utcoffset(self, dt: datetime | None) -> None:
            return None

    with pytest.raises(ValueError, match="timezone-aware"):
        _input(latest_source_at=datetime(2026, 7, 2, 17, 0, tzinfo=MissingOffset()))


def test_digest_rejects_float_nonfinite_flags_and_inconsistent_public_rows() -> None:
    with pytest.raises(ValueError, match="latest_source_age_hours"):
        _input(latest_source_age_hours=1.0)
    with pytest.raises(ValueError, match="probability_movement"):
        _input(probability_movement=Decimal("NaN"))
    with pytest.raises(ValueError, match="quorum_share"):
        _input(quorum_share=d("1.000001"))
    with pytest.raises(ValueError, match="config"):
        build_market_research_freshness_gap_priority_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="hard flags"):
        MarketResearchFreshnessGapPriorityDigestConfig(report_only=False)
    with pytest.raises(ValueError, match="reason_codes"):
        MarketResearchFreshnessGapPriorityDigestRow(
            priority_sequence=d("1"),
            redacted_market_ref="politics_research_gap_000001",
            research_topic="resolution_source_recheck",
            team_id="politics",
            latest_source_at=GENERATED_AT,
            latest_evidence_at=GENERATED_AT,
            latest_forecast_at=GENERATED_AT,
            latest_source_age_hours=d("30.000000"),
            evidence_age_hours=d("40.000000"),
            forecast_age_hours=d("35.000000"),
            probability_movement=d("0.200000"),
            quorum_share=d("0.300000"),
            freshness_gap_score=d("157.000000"),
            priority_status="blocked",
            reason_codes=("latest_source_stale",),
        )


def test_digest_dataclasses_are_frozen_exact_type_and_replace_revalidates() -> None:
    config = MarketResearchFreshnessGapPriorityDigestConfig()
    assert config.config_version == (
        DEFAULT_MARKET_RESEARCH_FRESHNESS_GAP_PRIORITY_DIGEST_CONFIG_VERSION
    )
    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]

    report = build_market_research_freshness_gap_priority_digest(
        (
            _input(team_id="politics"),
            _input(team_id="crypto_btc"),
        ),
        config=config,
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        report.priority_rows[0].priority_status = "ready"  # type: ignore[misc]
    with pytest.raises(ValueError, match="exactly"):
        class BadInput(MarketResearchFreshnessGapPriorityDigestInput):
            pass
    with pytest.raises(ValueError, match="blocked_count"):
        replace(report, blocked_count=d("0"))
    with pytest.raises(ValueError, match="priority_rows"):
        replace(report, priority_rows=tuple(reversed(report.priority_rows)))


def test_digest_public_surface_is_report_only_static_and_local() -> None:
    source = "src/polymarket_alpha_lab/market_research_freshness_gap_priority_digest.py"
    tree = ast.parse(open(source, encoding="utf-8").read())
    forbidden_calls = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "request",
        "submit",
        "trade",
        "recommend",
    }
    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "web3",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else None
            attr = func.attr if isinstance(func, ast.Attribute) else None
            assert name not in forbidden_calls
            assert attr not in forbidden_calls

    public_names = {
        name
        for name in dir(
            __import__(
                "polymarket_alpha_lab.market_research_freshness_gap_priority_digest",
                fromlist=["*"],
            )
        )
        if not name.startswith("_")
    }
    forbidden_public_fragments = (
        "wallet",
        "auth",
        "account",
        "order",
        "trade",
        "recommend",
        "advice",
    )
    assert not any(
        fragment in public_name.lower()
        for public_name in public_names
        for fragment in forbidden_public_fragments
    )
