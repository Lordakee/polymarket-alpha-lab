from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_reliability_drift_report import (
    ResearchSourceReliabilityDriftConfig,
    ResearchSourceReliabilityDriftReasonCodeCount,
    ResearchSourceReliabilityDriftReport,
    ResearchSourceReliabilityDriftRow,
    ResearchSourceReliabilityHistoryPoint,
    build_research_source_reliability_drift_report,
    research_source_reliability_drift_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceReliabilityDriftConfig:
    values = {
        "config_version": "research-source-reliability-drift-report-v0",
        "min_history_points": d("3"),
        "quality_drop_watch": d("0.100000"),
        "quality_drop_block": d("0.250000"),
        "failure_rate_increase_watch": d("0.050000"),
        "failure_rate_increase_block": d("0.150000"),
        "stale_age_watch_seconds": d("86400"),
        "stale_age_block_seconds": d("259200"),
    }
    values.update(overrides)
    return ResearchSourceReliabilityDriftConfig(**values)


def history(
    source_family: str,
    days_ago: int,
    quality_score: str,
    failure_rate: str,
    stale_age_seconds: str,
    *,
    reason_codes: tuple[str, ...] = (),
) -> ResearchSourceReliabilityHistoryPoint:
    return ResearchSourceReliabilityHistoryPoint(
        source_family=source_family,
        observed_at=GENERATED_AT - timedelta(days=days_ago),
        quality_score=d(quality_score),
        failure_rate=d(failure_rate),
        stale_age_seconds=d(stale_age_seconds),
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchSourceReliabilityHistoryPoint, ...],
    *,
    cfg: ResearchSourceReliabilityDriftConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceReliabilityDriftReport:
    return build_research_source_reliability_drift_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_summary() -> None:
    drift_report = report(())

    assert type(drift_report) is ResearchSourceReliabilityDriftReport
    assert drift_report.generated_at == GENERATED_AT
    assert drift_report.config_version == "research-source-reliability-drift-report-v0"
    assert drift_report.source_family_count == d("0")
    assert drift_report.observation_count == d("0")
    assert drift_report.pass_count == d("0")
    assert drift_report.watch_count == d("0")
    assert drift_report.blocked_count == d("0")
    assert drift_report.average_latest_quality_score is None
    assert drift_report.average_quality_score_drop is None
    assert drift_report.average_failure_rate_increase is None
    assert drift_report.max_latest_stale_age_seconds is None
    assert drift_report.status == "blocked"
    assert drift_report.rows == ()
    assert drift_report.reason_codes == ("no_reliability_history",)
    assert drift_report.reason_code_counts == (
        ResearchSourceReliabilityDriftReasonCodeCount(
            reason_code="no_reliability_history",
            count=d("1"),
        ),
    )
    assert drift_report.explanations == ("No reliability history was supplied.",)
    assert drift_report.paper_only is True
    assert drift_report.report_only is True
    assert drift_report.readonly is True


def test_stable_decimal_history_passes_with_deterministic_scores() -> None:
    drift_report = report(
        (
            history("official-feed", 3, "0.880000", "0.040000", "3600"),
            history("official-feed", 2, "0.860000", "0.050000", "7200"),
            history("official-feed", 0, "0.840000", "0.050000", "1800"),
        ),
    )

    assert drift_report.status == "pass"
    assert drift_report.source_family_count == d("1")
    assert drift_report.observation_count == d("3")
    assert drift_report.pass_count == d("1")
    assert drift_report.watch_count == d("0")
    assert drift_report.blocked_count == d("0")
    assert drift_report.average_latest_quality_score == d("0.840000")
    assert drift_report.average_quality_score_drop == d("0.030000")
    assert drift_report.average_failure_rate_increase == d("0.005000")
    assert drift_report.max_latest_stale_age_seconds == d("1800")
    assert drift_report.reason_codes == ("reliability_drift_pass",)

    row = drift_report.rows[0]
    assert type(row) is ResearchSourceReliabilityDriftRow
    assert row.source_family == "official-feed"
    assert row.observation_count == d("3")
    assert row.first_observed_at == GENERATED_AT - timedelta(days=3)
    assert row.latest_observed_at == GENERATED_AT
    assert row.historical_quality_score == d("0.870000")
    assert row.latest_quality_score == d("0.840000")
    assert row.quality_score_drop == d("0.030000")
    assert row.historical_failure_rate == d("0.045000")
    assert row.latest_failure_rate == d("0.050000")
    assert row.failure_rate_increase == d("0.005000")
    assert row.latest_stale_age_seconds == d("1800")
    assert row.status == "pass"
    assert row.reason_codes == ("reliability_drift_pass",)
    assert row.explanations == ("Reliability drift is within configured bounds.",)


def test_quality_failure_and_staleness_drift_escalate_watch_and_block() -> None:
    drift_report = report(
        (
            history("watch-family", 4, "0.860000", "0.040000", "3600"),
            history("watch-family", 2, "0.840000", "0.050000", "7200"),
            history(
                "watch-family",
                0,
                "0.720000",
                "0.070000",
                "90000",
                reason_codes=("manual_reviewed",),
            ),
            history("blocked-family", 4, "0.820000", "0.040000", "3600"),
            history("blocked-family", 2, "0.780000", "0.060000", "7200"),
            history("blocked-family", 0, "0.500000", "0.220000", "300000"),
        ),
    )

    assert drift_report.status == "blocked"
    assert tuple(row.source_family for row in drift_report.rows) == (
        "blocked-family",
        "watch-family",
    )
    assert drift_report.pass_count == d("0")
    assert drift_report.watch_count == d("1")
    assert drift_report.blocked_count == d("1")
    assert drift_report.average_latest_quality_score == d("0.610000")
    assert drift_report.average_quality_score_drop == d("0.215000")
    assert drift_report.average_failure_rate_increase == d("0.097500")
    assert drift_report.max_latest_stale_age_seconds == d("300000")
    assert drift_report.reason_codes == (
        "failure_rate_increase_block",
        "input_manual_reviewed",
        "quality_score_drop_block",
        "quality_score_drop_watch",
        "reliability_drift_blocked",
        "reliability_drift_watch",
        "stale_age_block",
        "stale_age_watch",
    )

    blocked_row = drift_report.rows[0]
    assert blocked_row.status == "blocked"
    assert blocked_row.historical_quality_score == d("0.800000")
    assert blocked_row.quality_score_drop == d("0.300000")
    assert blocked_row.historical_failure_rate == d("0.050000")
    assert blocked_row.failure_rate_increase == d("0.170000")
    assert blocked_row.reason_codes == (
        "failure_rate_increase_block",
        "quality_score_drop_block",
        "reliability_drift_blocked",
        "stale_age_block",
    )
    assert blocked_row.explanations == (
        "Quality score dropped by 0.300000.",
        "Failure rate increased by 0.170000.",
        "Latest observation age is 300000 seconds.",
    )


def test_payload_is_json_ready_decimal_only_and_excludes_sensitive_source_material() -> None:
    drift_report = report(
        (
            history("official-feed", 3, "0.880000", "0.040000", "3600"),
            history("official-feed", 2, "0.860000", "0.050000", "7200"),
            history("official-feed", 0, "0.840000", "0.050000", "1800"),
        ),
    )

    payload = research_source_reliability_drift_report_payload(drift_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["rows"][0]["latest_quality_score"] == "0.840000"
    assert payload["rows"][0]["quality_score_drop"] == "0.030000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded

    forbidden_fragments = (
        "source_url",
        "source_text",
        "source_ref",
        "source_table",
        "http://",
        "https://",
        "dsn",
        "token",
    )
    assert all(fragment not in encoded.lower() for fragment in forbidden_fragments)


def test_validation_rejects_bad_types_unsafe_public_values_future_times_and_flags() -> None:
    with pytest.raises(ValueError, match="quality_drop_watch"):
        config(quality_drop_watch=Decimal("0.300000"))
    with pytest.raises(ValueError, match="quality_drop_watch"):
        config(quality_drop_watch=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="failure_rate_increase_watch"):
        config(failure_rate_increase_watch=_DecimalSubclass("0.050000"))
    with pytest.raises(ValueError, match="stale_age_block_seconds"):
        config(stale_age_block_seconds=d("86400"))
    with pytest.raises(ValueError, match="config"):
        build_research_source_reliability_drift_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report((history("official-feed", 1, "0.8", "0.1", "1"),), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (history("official-feed", 1, "0.8", "0.1", "1"),),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_family"):
        history("https://private.example/source", 1, "0.8", "0.1", "1")
    with pytest.raises(ValueError, match="quality_score"):
        ResearchSourceReliabilityHistoryPoint(
            source_family="official-feed",
            observed_at=GENERATED_AT - timedelta(days=1),
            quality_score=0.8,  # type: ignore[arg-type]
            failure_rate=d("0.100000"),
            stale_age_seconds=d("1"),
        )
    with pytest.raises(ValueError, match="failure_rate"):
        ResearchSourceReliabilityHistoryPoint(
            source_family="official-feed",
            observed_at=GENERATED_AT - timedelta(days=1),
            quality_score=d("0.800000"),
            failure_rate=_DecimalSubclass("0.100000"),
            stale_age_seconds=d("1"),
        )
    with pytest.raises(ValueError, match="stale_age_seconds"):
        history("official-feed", 1, "0.8", "0.1", "-1")
    with pytest.raises(ValueError, match="observed_at"):
        report((history("official-feed", -1, "0.8", "0.1", "1"),))
    with pytest.raises(ValueError, match="reason_codes"):
        history("official-feed", 1, "0.8", "0.1", "1", reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(history("official-feed", 1, "0.8", "0.1", "1"), paper_only=False)
    with pytest.raises(ValueError, match="history_points"):
        report((object(),))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        type(
            "HistoryPointSubclass",
            (ResearchSourceReliabilityHistoryPoint,),
            {},
        )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    drift_report = report(
        (
            history("official-feed", 3, "0.880000", "0.040000", "3600"),
            history("official-feed", 2, "0.860000", "0.050000", "7200"),
            history("official-feed", 0, "0.840000", "0.050000", "1800"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        drift_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        drift_report.rows[0].quality_score_drop = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="quality_score_drop"):
        replace(drift_report.rows[0], quality_score_drop=d("0.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(drift_report, status="watch")


def test_owned_module_has_no_network_trading_filesystem_or_db_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_reliability_drift_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "psycopg",
        "sqlalchemy",
        "sqlite",
        "supabase",
        "trade",
        "order",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
