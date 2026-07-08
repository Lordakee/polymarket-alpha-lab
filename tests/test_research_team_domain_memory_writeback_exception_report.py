from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_team_domain_memory_writeback_exception_report as api
from polymarket_alpha_lab.research_team_domain_memory_writeback_exception_report import (
    ResearchTeamDomainMemoryWritebackExceptionReport,
    ResearchTeamDomainMemoryWritebackExceptionReportConfig,
    ResearchTeamDomainMemoryWritebackExceptionRow,
    ResearchTeamDomainMemoryWritebackSnapshot,
    ResearchTeamDomainMemoryWritebackTeamDomainRollup,
    build_research_team_domain_memory_writeback_exception_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _snapshot(
    *,
    team_id: str = "macro_team",
    domain_id: str = "rates",
    case_key: str = "case_a",
    observed_at: datetime = NOW - timedelta(days=2),
    writeback_at: datetime | None = NOW - timedelta(hours=1),
    outcome_link_resolved: bool = True,
    calibration_feedback_backlog_count: Decimal = Decimal("0"),
    manual_review_urgency: Decimal = Decimal("0.000000"),
) -> ResearchTeamDomainMemoryWritebackSnapshot:
    return ResearchTeamDomainMemoryWritebackSnapshot(
        team_id=team_id,
        domain_id=domain_id,
        case_key=case_key,
        observed_at=observed_at,
        writeback_at=writeback_at,
        outcome_link_resolved=outcome_link_resolved,
        calibration_feedback_backlog_count=calibration_feedback_backlog_count,
        manual_review_urgency=manual_review_urgency,
    )


def _report(
    snapshots: tuple[ResearchTeamDomainMemoryWritebackSnapshot, ...],
    *,
    config: ResearchTeamDomainMemoryWritebackExceptionReportConfig | None = None,
) -> ResearchTeamDomainMemoryWritebackExceptionReport:
    return build_research_team_domain_memory_writeback_exception_report(
        snapshots,
        generated_at=NOW,
        config=config,
    )


def test_aggregates_writeback_exceptions_and_redacts_case_context() -> None:
    raw_sensitive_case = (
        "candidate:raw-candidate-123|market:raw-market-slug|"
        "question:Will it resolve?|https://example.test/source?token=secret"
    )
    config = ResearchTeamDomainMemoryWritebackExceptionReportConfig(
        stale_writeback_watch_after_seconds=Decimal("86400.000000"),
        stale_writeback_block_after_seconds=Decimal("172800.000000"),
        calibration_feedback_watch_threshold=Decimal("1"),
        calibration_feedback_block_threshold=Decimal("3"),
        manual_review_watch_urgency=Decimal("0.500000"),
        manual_review_block_urgency=Decimal("0.800000"),
    )

    report = _report(
        (
            _snapshot(
                team_id="team_b",
                domain_id="crypto",
                case_key=raw_sensitive_case,
                writeback_at=None,
                outcome_link_resolved=False,
                calibration_feedback_backlog_count=Decimal("4"),
                manual_review_urgency=Decimal("0.900000"),
            ),
            _snapshot(
                team_id="team_a",
                domain_id="rates",
                case_key="case_stale",
                writeback_at=NOW - timedelta(seconds=90_000),
                calibration_feedback_backlog_count=Decimal("1"),
                manual_review_urgency=Decimal("0.600000"),
            ),
            _snapshot(
                team_id="team_a",
                domain_id="rates",
                case_key="case_pass",
                writeback_at=NOW - timedelta(seconds=3_600),
            ),
        ),
        config=config,
    )

    assert report.status == "block"
    assert report.input_count == Decimal("3.000000")
    assert report.row_count == Decimal("3.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.missing_writeback_count == Decimal("1.000000")
    assert report.stale_writeback_count == Decimal("1.000000")
    assert report.unresolved_outcome_link_count == Decimal("1.000000")
    assert report.calibration_feedback_backlog_count == Decimal("2.000000")
    assert report.manual_review_urgent_count == Decimal("2.000000")
    assert report.max_writeback_age_seconds == Decimal("90000.000000")
    assert report.max_manual_review_urgency == Decimal("0.900000")
    assert report.reason_codes == (
        "missing_writeback",
        "stale_writeback_age",
        "unresolved_outcome_link",
        "calibration_feedback_backlog",
        "manual_review_urgency",
    )

    block_row = report.rows[0]
    watch_row = report.rows[1]
    pass_row = report.rows[2]
    assert block_row.status == "block"
    assert watch_row.status == "watch"
    assert pass_row.status == "pass"
    assert block_row.memory_case_ref.startswith("memory_case_")
    assert raw_sensitive_case not in json.dumps(report.payload, sort_keys=True)
    assert "raw-candidate-123" not in json.dumps(report.payload, sort_keys=True)
    assert "raw-market-slug" not in json.dumps(report.payload, sort_keys=True)
    assert "Will it resolve" not in json.dumps(report.payload, sort_keys=True)
    assert "https://example.test" not in json.dumps(report.payload, sort_keys=True)
    assert "token=secret" not in json.dumps(report.payload, sort_keys=True)

    rollup = report.team_domain_rollups[0]
    assert rollup.team_id == "team_b"
    assert rollup.domain_id == "crypto"
    assert rollup.status == "block"
    assert rollup.missing_writeback_count == Decimal("1.000000")


def test_payload_is_deterministic_decimal_string_only_and_digest_validated() -> None:
    first = _report(
        (
            _snapshot(team_id="team_b", domain_id="crypto", case_key="case_b"),
            _snapshot(team_id="team_a", domain_id="rates", case_key="case_a"),
        ),
    )
    second = _report(
        (
            _snapshot(team_id="team_a", domain_id="rates", case_key="case_a"),
            _snapshot(team_id="team_b", domain_id="crypto", case_key="case_b"),
        ),
    )

    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    json.dumps(first.payload, sort_keys=True)
    assert first.payload["input_count"] == "2.000000"
    assert first.payload["rows"][0]["writeback_age_seconds"] == "3600.000000"
    assert first.payload["derived_validation_digest"] == first.derived_validation_digest
    _assert_no_decimal_objects(first.payload)
    _assert_no_non_decimal_public_numbers(first)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_empty_report_passes_with_report_only_scope() -> None:
    report = _report(())

    assert report.status == "pass"
    assert report.input_count == Decimal("0.000000")
    assert report.row_count == Decimal("0.000000")
    assert report.reason_codes == ("no_domain_memory_writeback_exceptions_detected",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_exact_and_hard_flagged() -> None:
    report = _report((_snapshot(),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadSnapshot(ResearchTeamDomainMemoryWritebackSnapshot):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchTeamDomainMemoryWritebackExceptionReportConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        ResearchTeamDomainMemoryWritebackSnapshot(
            team_id="macro_team",
            domain_id="rates",
            case_key="case_a",
            observed_at=NOW,
            writeback_at=NOW,
            outcome_link_resolved=True,
            calibration_feedback_backlog_count=Decimal("0"),
            manual_review_urgency=Decimal("0.000000"),
            report_only=False,
        )

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_rejects_unsafe_public_payload_and_invalid_temporal_inputs() -> None:
    with pytest.raises(ValueError, match="status"):
        replace(_report((_snapshot(),)), status="blocked")

    with pytest.raises(ValueError, match="writeback_at"):
        _report((_snapshot(writeback_at=NOW + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="observed_at"):
        _report((_snapshot(observed_at=NOW + timedelta(seconds=1), writeback_at=None),))

    with pytest.raises(ValueError, match="writeback_at"):
        ResearchTeamDomainMemoryWritebackSnapshot(
            team_id="macro_team",
            domain_id="rates",
            case_key="case_a",
            observed_at=NOW,
            writeback_at=NOW - timedelta(seconds=1),
            outcome_link_resolved=True,
            calibration_feedback_backlog_count=Decimal("0"),
            manual_review_urgency=Decimal("0.000000"),
        )


def test_public_api_exposes_no_execution_or_sensitive_surfaces() -> None:
    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "auth",
        "wallet",
        "order",
        "live",
        "trade",
        "sizing",
        "recommendation",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        ResearchTeamDomainMemoryWritebackExceptionReportConfig,
        ResearchTeamDomainMemoryWritebackSnapshot,
        ResearchTeamDomainMemoryWritebackExceptionRow,
        ResearchTeamDomainMemoryWritebackTeamDomainRollup,
        ResearchTeamDomainMemoryWritebackExceptionReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
