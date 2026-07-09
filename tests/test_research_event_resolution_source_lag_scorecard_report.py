from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_resolution_source_lag_scorecard_report import (
    DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_LAG_SCORECARD_REPORT_CONFIG_VERSION,
    ResearchEventResolutionSourceLagObservation,
    ResearchEventResolutionSourceLagScorecardConfig,
    ResearchEventResolutionSourceLagScorecardReasonCodeCount,
    ResearchEventResolutionSourceLagScorecardReport,
    ResearchEventResolutionSourceLagScorecardRow,
    build_research_event_resolution_source_lag_scorecard_report,
    research_event_resolution_source_lag_scorecard_report_digest,
    research_event_resolution_source_lag_scorecard_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventResolutionSourceLagScorecardConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_LAG_SCORECARD_REPORT_CONFIG_VERSION,
        "watch_lag_seconds": d("900"),
        "block_lag_seconds": d("3600"),
        "min_evidence_count": d("2"),
        "min_parser_confidence": d("0.650000"),
        "dispute_block_count": d("1"),
    }
    values.update(overrides)
    return ResearchEventResolutionSourceLagScorecardConfig(**values)


def observation(
    event_fingerprint: str,
    *,
    reference_age: timedelta,
    resolution_age: timedelta,
    evidence_count: Decimal = d("3"),
    parser_confidence: Decimal = d("0.900000"),
    dispute_count: Decimal = d("0"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchEventResolutionSourceLagObservation:
    return ResearchEventResolutionSourceLagObservation(
        event_fingerprint=event_fingerprint,
        reference_available_at=GENERATED_AT - reference_age,
        resolution_available_at=GENERATED_AT - resolution_age,
        evidence_count=evidence_count,
        parser_confidence=parser_confidence,
        dispute_count=dispute_count,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchEventResolutionSourceLagObservation, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    cfg: ResearchEventResolutionSourceLagScorecardConfig | None = None,
) -> ResearchEventResolutionSourceLagScorecardReport:
    return build_research_event_resolution_source_lag_scorecard_report(
        rows,
        generated_at=generated_at,
        config=cfg or config(),
    )


def test_builds_pass_watch_block_scorecard_with_decimal_rollups() -> None:
    scorecard = report(
        (
            observation(
                "sha256:aaaaaaaaaaaa",
                reference_age=timedelta(minutes=35),
                resolution_age=timedelta(minutes=30),
            ),
            observation(
                "sha256:bbbbbbbbbbbb",
                reference_age=timedelta(hours=2),
                resolution_age=timedelta(minutes=75),
                evidence_count=d("1"),
                parser_confidence=d("0.600000"),
                reason_codes=("operator_reviewed",),
            ),
            observation(
                "sha256:cccccccccccc",
                reference_age=timedelta(hours=4),
                resolution_age=timedelta(hours=2, minutes=30),
                dispute_count=d("1"),
            ),
        ),
    )

    assert type(scorecard) is ResearchEventResolutionSourceLagScorecardReport
    assert scorecard.status == "block"
    assert scorecard.event_count == d("3")
    assert scorecard.pass_count == d("1")
    assert scorecard.watch_count == d("1")
    assert scorecard.block_count == d("1")
    assert scorecard.mean_source_lag_seconds == d("2800")
    assert scorecard.max_source_lag_seconds == d("5400")
    assert tuple(row.status for row in scorecard.rows) == ("block", "watch", "pass")

    blocked, watched, passed = scorecard.rows
    assert type(blocked) is ResearchEventResolutionSourceLagScorecardRow
    assert blocked.event_fingerprint == "sha256:cccccccccccc"
    assert blocked.source_lag_seconds == d("5400")
    assert blocked.reason_codes == (
        "resolution_lag_block",
        "source_dispute_block",
    )
    assert watched.source_lag_seconds == d("2700")
    assert watched.reason_codes == (
        "input_operator_reviewed",
        "low_parser_confidence_watch",
        "resolution_lag_watch",
        "thin_evidence_watch",
    )
    assert passed.source_lag_seconds == d("300")
    assert passed.reason_codes == ("resolution_source_lag_clear",)
    assert scorecard.reason_code_counts[0] == ResearchEventResolutionSourceLagScorecardReasonCodeCount(
        reason_code="input_operator_reviewed",
        count=d("1"),
    )
    assert scorecard.paper_only is True
    assert scorecard.report_only is True
    assert scorecard.readonly is True


def test_payload_is_deterministic_digest_backed_and_has_no_raw_secret_surface() -> None:
    first = report(
        (
            observation(
                "sha256:bbbbbbbbbbbb",
                reference_age=timedelta(hours=2),
                resolution_age=timedelta(minutes=75),
                evidence_count=d("1"),
                parser_confidence=d("0.600000"),
            ),
            observation(
                "sha256:aaaaaaaaaaaa",
                reference_age=timedelta(minutes=35),
                resolution_age=timedelta(minutes=30),
            ),
        ),
    )
    second = report(tuple(reversed(first.observations)))

    first_payload = research_event_resolution_source_lag_scorecard_report_payload(first)
    second_payload = research_event_resolution_source_lag_scorecard_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert research_event_resolution_source_lag_scorecard_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first_payload["rows"][0]["source_lag_seconds"] == "2700.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(type(value) in (int, float) for value in _walk_payload_values(first_payload))
    assert "blocked" not in encoded
    for raw_fragment in (
        "https://",
        "candidate",
        "market",
        "source_url",
        "source_text",
        "postgres://",
        "dsn",
        "table",
        "token",
    ):
        assert raw_fragment not in encoded.lower()


def test_input_reason_codes_are_context_only_and_do_not_control_status() -> None:
    scorecard = report(
        (
            observation(
                "sha256:dddddddddddd",
                reference_age=timedelta(minutes=35),
                resolution_age=timedelta(minutes=30),
                reason_codes=("manual_block", "manual_watch"),
            ),
        ),
    )

    row = scorecard.rows[0]
    assert row.status == "pass"
    assert row.reason_codes == (
        "input_manual_block",
        "input_manual_watch",
        "resolution_source_lag_clear",
    )


def test_public_reason_text_rejects_execution_and_raw_context_surfaces() -> None:
    for reason_code in (
        "wallet_probe",
        "auth_probe",
        "order_flow",
        "trade_signal",
        "recommendation_note",
        "sizing_note",
        "question_text",
        "slug_value",
    ):
        with pytest.raises(ValueError, match="raw private surface"):
            observation(
                "sha256:dddddddddddd",
                reference_age=timedelta(minutes=35),
                resolution_age=timedelta(minutes=30),
                reason_codes=(reason_code,),
            )


def test_source_lag_seconds_preserves_long_span_microseconds_as_decimal() -> None:
    scorecard = report(
        (
            observation(
                "sha256:eeeeeeeeeeee",
                reference_age=timedelta(days=100000, microseconds=1),
                resolution_age=timedelta(0),
            ),
        ),
    )

    assert scorecard.rows[0].source_lag_seconds == d("8640000000.000001")
    assert scorecard.max_source_lag_seconds == d("8640000000.000001")
    assert scorecard.mean_source_lag_seconds == d("8640000000.000001")


def test_validation_rejects_float_subclasses_bad_statuses_bad_flags_and_raw_ids() -> None:
    with pytest.raises(ValueError, match="watch_lag_seconds"):
        config(watch_lag_seconds=900)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_parser_confidence"):
        config(min_parser_confidence=_DecimalSubclass("0.650000"))
    with pytest.raises(ValueError, match="reference_available_at"):
        observation(
            "sha256:aaaaaaaaaaaa",
            reference_age=timedelta(minutes=35),
            resolution_age=timedelta(minutes=30),
        ).__class__(
            event_fingerprint="sha256:bbbbbbbbbbbb",
            reference_available_at=datetime(2026, 7, 8, 11, 25),
            resolution_available_at=GENERATED_AT - timedelta(minutes=30),
            evidence_count=d("3"),
            parser_confidence=d("0.900000"),
            dispute_count=d("0"),
            reason_codes=(),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="event_fingerprint"):
        observation(
            "https://example.test/raw-candidate-market-source",
            reference_age=timedelta(minutes=35),
            resolution_age=timedelta(minutes=30),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        observation(
            "sha256:dddddddddddd",
            reference_age=timedelta(minutes=35),
            resolution_age=timedelta(minutes=30),
            reason_codes=("Needs Review",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            observation(
                "sha256:eeeeeeeeeeee",
                reference_age=timedelta(minutes=35),
                resolution_age=timedelta(minutes=30),
            ),
            paper_only=False,
        )

    scorecard = report(
        (
            observation(
                "sha256:ffffffffffff",
                reference_age=timedelta(minutes=35),
                resolution_age=timedelta(minutes=30),
            ),
        ),
    )
    with pytest.raises(ValueError, match="status"):
        replace(scorecard.rows[0], status="blocked")
    with pytest.raises(ValueError, match="source_lag_seconds"):
        replace(scorecard.rows[0], source_lag_seconds=d("1"))


def test_frozen_report_and_digest_validation_reject_tampering() -> None:
    scorecard = report(
        (
            observation(
                "sha256:aaaaaaaaaaaa",
                reference_age=timedelta(minutes=35),
                resolution_age=timedelta(minutes=30),
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        scorecard.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        scorecard.rows[0].source_lag_seconds = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(scorecard, derived_validation_digest="0" * 64)

    object.__setattr__(scorecard, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_resolution_source_lag_scorecard_report_payload(scorecard)


def test_owned_module_has_no_execution_or_trading_surface_terms() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_resolution_source_lag_scorecard_report.py"
    )
    module_source = module_path.read_text(encoding="utf-8").lower()

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
        "wallet",
        "auth",
        "order",
        "live trading",
        "sizing",
        "recommendation",
        "database",
        "supabase",
        "sqlalchemy",
        "psycopg",
        "web3",
    )
    assert all(term not in module_source for term in forbidden_terms)


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
