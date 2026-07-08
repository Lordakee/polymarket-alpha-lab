from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_resolution_latency_monitor_report import (
    ResearchResolutionLatencyMonitorConfig,
    ResearchResolutionLatencyMonitorObservation,
    ResearchResolutionLatencyMonitorReasonCodeCount,
    ResearchResolutionLatencyMonitorReport,
    ResearchResolutionLatencyMonitorRow,
    build_research_resolution_latency_monitor_report,
    research_resolution_latency_monitor_digest,
    research_resolution_latency_monitor_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionLatencyMonitorConfig:
    values = {
        "config_version": "research-resolution-latency-monitor-v0",
        "watch_after_seconds": d("86400.000000"),
        "block_after_seconds": d("259200.000000"),
    }
    values.update(overrides)
    return ResearchResolutionLatencyMonitorConfig(**values)


def observation(
    public_event_ref: str,
    *,
    expected_end_at: datetime,
    confirmed_at: datetime | None = None,
    review_completed_at: datetime | None = None,
    raw_candidate_id: str | None = None,
    market_id: str | None = None,
    market_slug: str | None = None,
    market_question: str | None = None,
    source_ref: str | None = None,
    source_url: str | None = None,
    source_text: str | None = None,
) -> ResearchResolutionLatencyMonitorObservation:
    return ResearchResolutionLatencyMonitorObservation(
        public_event_ref=public_event_ref,
        expected_end_at=expected_end_at,
        confirmed_at=confirmed_at,
        review_completed_at=review_completed_at,
        raw_candidate_id=raw_candidate_id,
        market_id=market_id,
        market_slug=market_slug,
        market_question=market_question,
        source_ref=source_ref,
        source_url=source_url,
        source_text=source_text,
    )


def report(
    rows: tuple[ResearchResolutionLatencyMonitorObservation, ...],
    *,
    cfg: ResearchResolutionLatencyMonitorConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionLatencyMonitorReport:
    return build_research_resolution_latency_monitor_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_pass_watch_and_block_rows_roll_up_to_public_status() -> None:
    pass_end = GENERATED_AT - timedelta(days=1)
    watch_end = GENERATED_AT - timedelta(days=2)
    block_end = GENERATED_AT - timedelta(days=5)

    latency_report = report(
        (
            observation("ref-watch", expected_end_at=watch_end),
            observation(
                "ref-pass",
                expected_end_at=pass_end,
                confirmed_at=pass_end + timedelta(minutes=30),
                review_completed_at=pass_end + timedelta(hours=1),
            ),
            observation(
                "ref-block",
                expected_end_at=block_end,
                confirmed_at=block_end + timedelta(hours=12),
            ),
        ),
    )

    assert latency_report.status == "block"
    assert latency_report.candidate_count == d("3.000000")
    assert latency_report.pass_count == d("1.000000")
    assert latency_report.watch_count == d("1.000000")
    assert latency_report.block_count == d("1.000000")
    assert tuple(row.public_event_ref for row in latency_report.rows) == (
        "ref-block",
        "ref-watch",
        "ref-pass",
    )
    assert tuple(row.status for row in latency_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert latency_report.rows[0].delay_seconds == d("432000.000000")
    assert latency_report.rows[0].reason_codes == (
        "review_completion_missing_block",
    )
    assert latency_report.rows[1].delay_seconds == d("172800.000000")
    assert latency_report.rows[1].reason_codes == (
        "outcome_confirmation_missing_watch",
    )
    assert latency_report.rows[2].delay_seconds == d("3600.000000")
    assert latency_report.rows[2].reason_codes == (
        "resolution_review_completed_pass",
    )


def test_decimal_type_datetime_and_sequence_validation_rejections() -> None:
    expected_end = GENERATED_AT - timedelta(days=1)

    with pytest.raises(ValueError, match="watch_after_seconds"):
        config(watch_after_seconds=86400)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_after_seconds"):
        config(block_after_seconds=_DecimalSubclass("259200.000000"))
    with pytest.raises(ValueError, match="watch_after_seconds"):
        config(watch_after_seconds=d("259200.000001"))
    with pytest.raises(ValueError, match="public_event_ref"):
        observation(" ref-pass", expected_end_at=expected_end)
    with pytest.raises(ValueError, match="expected_end_at"):
        observation("ref-pass", expected_end_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation("ref-pass", expected_end_at=expected_end),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="confirmed_at"):
        observation(
            "ref-pass",
            expected_end_at=expected_end,
            confirmed_at=expected_end - timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="review_completed_at"):
        observation(
            "ref-pass",
            expected_end_at=expected_end,
            confirmed_at=expected_end + timedelta(seconds=1),
            review_completed_at=expected_end,
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation("ref-pass", expected_end_at=expected_end), paper_only=False)
    with pytest.raises(ValueError, match="observations"):
        report((object(),))  # type: ignore[arg-type]


def test_public_payload_omits_sensitive_inputs_and_rejects_public_leaks() -> None:
    ended_at = GENERATED_AT - timedelta(hours=2)
    latency_report = report(
        (
            observation(
                "public-ref",
                expected_end_at=ended_at,
                confirmed_at=ended_at + timedelta(minutes=10),
                review_completed_at=ended_at + timedelta(minutes=20),
                raw_candidate_id="raw-candidate-secret",
                market_id="market-secret-id",
                market_slug="secret-market-slug",
                market_question="Will the secret event resolve yes?",
                source_ref="source-secret-ref",
                source_url="https://secret.example/resolution",
                source_text="secret source text",
            ),
        ),
    )

    payload = research_resolution_latency_monitor_report_payload(latency_report)
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert "raw-candidate-secret" not in encoded
    assert "market-secret-id" not in encoded
    assert "secret-market-slug" not in encoded
    assert "will the secret event" not in encoded
    assert "source-secret-ref" not in encoded
    assert "https://secret.example" not in encoded
    assert "secret source text" not in encoded
    assert all(
        fragment not in encoded
        for fragment in (
            "raw_candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "source_ref",
            "source_url",
            "source_text",
            "wallet",
            "order",
            "trade",
            "position",
            "buy",
            "sell",
            "recommend",
            "dsn",
            "token",
        )
    )

    with pytest.raises(ValueError, match="public_event_ref"):
        replace(latency_report.rows[0], public_event_ref="market-secret-id")


def test_public_dataclasses_are_frozen_and_hard_flags_are_enforced() -> None:
    ended_at = GENERATED_AT - timedelta(hours=2)
    latency_report = report(
        (
            observation(
                "public-ref",
                expected_end_at=ended_at,
                confirmed_at=ended_at + timedelta(minutes=10),
                review_completed_at=ended_at + timedelta(minutes=20),
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        latency_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        latency_report.rows[0].delay_seconds = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(latency_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(latency_report, status="blocked")
    with pytest.raises(ValueError, match="readonly"):
        replace(latency_report.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="report_only"):
        ResearchResolutionLatencyMonitorConfig(report_only=False)


def test_payload_and_digest_are_deterministic_and_consistent_without_float_values() -> None:
    pass_end = GENERATED_AT - timedelta(hours=4)
    watch_end = GENERATED_AT - timedelta(days=2)
    block_end = GENERATED_AT - timedelta(days=4)
    observations = (
        observation("z-pass", expected_end_at=pass_end, review_completed_at=pass_end),
        observation("a-block", expected_end_at=block_end),
        observation("m-watch", expected_end_at=watch_end),
    )

    first_report = report(observations)
    second_report = report(tuple(reversed(observations)))
    first_payload = research_resolution_latency_monitor_report_payload(first_report)
    second_payload = research_resolution_latency_monitor_report_payload(second_report)
    digest = research_resolution_latency_monitor_digest(first_report)

    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )
    assert digest["generated_at"] == first_payload["generated_at"]
    assert digest["status"] == first_payload["status"]
    assert digest["candidate_count"] == first_payload["candidate_count"]
    assert digest["pass_count"] == first_payload["pass_count"]
    assert digest["watch_count"] == first_payload["watch_count"]
    assert digest["block_count"] == first_payload["block_count"]
    assert digest["reason_codes"] == first_payload["reason_codes"]
    assert digest["reason_code_counts"] == first_payload["reason_code_counts"]
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, float) for value in _walk_payload_values(digest))
    assert all(row["status"] in {"pass", "watch", "block"} for row in first_payload["rows"])


def test_owned_module_has_no_network_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_resolution_latency_monitor_report.py"
    )
    if not module_path.exists():
        pytest.skip("module not implemented yet")
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
