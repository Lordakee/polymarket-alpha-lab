from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_research_review_checklist import (
    DEFAULT_TEAM_RESEARCH_REVIEW_CHECKLIST_CONFIG_VERSION,
    TeamResearchReviewChecklistConfig,
    TeamResearchReviewChecklistItem,
    TeamResearchReviewChecklistReasonCodeCount,
    TeamResearchReviewChecklistReport,
    TeamResearchReviewChecklistTeamSummary,
    build_team_research_review_checklist_report,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def _config(**overrides: object) -> TeamResearchReviewChecklistConfig:
    values = {
        "config_version": DEFAULT_TEAM_RESEARCH_REVIEW_CHECKLIST_CONFIG_VERSION,
        "max_source_age_seconds": Decimal("86400.000000"),
    }
    values.update(overrides)
    return TeamResearchReviewChecklistConfig(**values)


def _item(
    packet_id: str,
    *,
    team_id: str = "politics",
    evidence_completion_ratio: Decimal = Decimal("1.000000"),
    latest_source_observed_at: datetime | None = GENERATED_AT - timedelta(hours=1),
    memory_ready: bool = True,
    calibration_available: bool = True,
    blocker_codes: tuple[str, ...] = (),
    reviewer_notes: tuple[str, ...] = ("packet reviewed; token=secret-token",),
) -> TeamResearchReviewChecklistItem:
    return TeamResearchReviewChecklistItem(
        team_id=team_id,
        packet_id=packet_id,
        evidence_completion_ratio=evidence_completion_ratio,
        latest_source_observed_at=latest_source_observed_at,
        memory_ready=memory_ready,
        calibration_available=calibration_available,
        blocker_codes=blocker_codes,
        reviewer_notes=reviewer_notes,
    )


def test_checklist_passes_complete_fresh_memory_and_calibration_ready_packets() -> None:
    report = build_team_research_review_checklist_report(
        (
            _item("packet_b", latest_source_observed_at=GENERATED_AT - timedelta(seconds=90)),
            _item("packet_a", latest_source_observed_at=GENERATED_AT - timedelta(seconds=30)),
        ),
        config=_config(max_source_age_seconds=Decimal("3600.000000")),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, TeamResearchReviewChecklistReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_TEAM_RESEARCH_REVIEW_CHECKLIST_CONFIG_VERSION
    assert report.summary_status == "pass"
    assert report.review_next_step == "review_complete"
    assert report.packet_count == Decimal("2.000000")
    assert report.complete_evidence_count == Decimal("2.000000")
    assert report.fresh_source_count == Decimal("2.000000")
    assert report.memory_ready_count == Decimal("2.000000")
    assert report.calibration_available_count == Decimal("2.000000")
    assert report.blocked_packet_count == Decimal("0.000000")
    assert report.incomplete_evidence_count == Decimal("0.000000")
    assert report.stale_or_missing_source_count == Decimal("0.000000")
    assert report.memory_not_ready_count == Decimal("0.000000")
    assert report.calibration_missing_count == Decimal("0.000000")
    assert report.evidence_completion_ratio == Decimal("1.000000")
    assert report.reason_codes == ("team_research_review_checklist_passed",)
    assert report.reason_code_counts == (
        TeamResearchReviewChecklistReasonCodeCount(
            reason_code="team_research_review_checklist_passed",
            count=Decimal("1.000000"),
        ),
    )
    assert tuple((row.team_id, row.packet_id) for row in report.items) == (
        ("politics", "packet_a"),
        ("politics", "packet_b"),
    )
    assert report.items[0].source_age_seconds == Decimal("30.000000")
    assert report.items[1].source_age_seconds == Decimal("90.000000")
    assert report.items[0].redacted_reviewer_notes == (
        "packet reviewed; sensitive=<redacted>",
    )
    assert report.team_summaries == (
        TeamResearchReviewChecklistTeamSummary(
            team_id="politics",
            packet_count=Decimal("2.000000"),
            complete_evidence_count=Decimal("2.000000"),
            fresh_source_count=Decimal("2.000000"),
            memory_ready_count=Decimal("2.000000"),
            calibration_available_count=Decimal("2.000000"),
            blocked_packet_count=Decimal("0.000000"),
            evidence_completion_ratio=Decimal("1.000000"),
            summary_status="pass",
            reason_codes=("team_research_review_checklist_passed",),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_checklist_blocks_incomplete_stale_missing_readiness_and_explicit_blockers() -> None:
    report = build_team_research_review_checklist_report(
        (
            _item(
                "complete_stale",
                team_id="crypto_btc",
                latest_source_observed_at=GENERATED_AT - timedelta(seconds=7_200),
            ),
            _item(
                "missing_memory",
                team_id="politics",
                evidence_completion_ratio=Decimal("0.750000"),
                latest_source_observed_at=None,
                memory_ready=False,
                calibration_available=False,
                blocker_codes=("needs_specialist_followup",),
                reviewer_notes=(
                    "dsn=postgresql://user:pass@localhost/db",
                    "api_key=secret-value",
                    "private" + "_key=0xabcdef",
                ),
            ),
        ),
        config=_config(max_source_age_seconds=Decimal("3600.000000")),
        generated_at=GENERATED_AT,
    )

    assert report.summary_status == "blocked"
    assert report.review_next_step == "resolve_research_review_blockers"
    assert report.packet_count == Decimal("2.000000")
    assert report.complete_evidence_count == Decimal("1.000000")
    assert report.fresh_source_count == Decimal("0.000000")
    assert report.memory_ready_count == Decimal("1.000000")
    assert report.calibration_available_count == Decimal("1.000000")
    assert report.blocked_packet_count == Decimal("1.000000")
    assert report.incomplete_evidence_count == Decimal("1.000000")
    assert report.stale_or_missing_source_count == Decimal("2.000000")
    assert report.memory_not_ready_count == Decimal("1.000000")
    assert report.calibration_missing_count == Decimal("1.000000")
    assert report.evidence_completion_ratio == Decimal("0.875000")
    assert report.reason_codes == (
        "team_research_review_blockers_present",
        "team_research_review_calibration_missing",
        "team_research_review_evidence_incomplete",
        "team_research_review_memory_not_ready",
        "team_research_review_source_not_fresh",
    )
    assert report.reason_code_counts == (
        TeamResearchReviewChecklistReasonCodeCount(
            reason_code="team_research_review_blockers_present",
                count=Decimal("1.000000"),
        ),
        TeamResearchReviewChecklistReasonCodeCount(
            reason_code="team_research_review_calibration_missing",
                count=Decimal("1.000000"),
        ),
        TeamResearchReviewChecklistReasonCodeCount(
            reason_code="team_research_review_evidence_incomplete",
                count=Decimal("1.000000"),
        ),
        TeamResearchReviewChecklistReasonCodeCount(
            reason_code="team_research_review_memory_not_ready",
                count=Decimal("1.000000"),
        ),
        TeamResearchReviewChecklistReasonCodeCount(
            reason_code="team_research_review_source_not_fresh",
                count=Decimal("1.000000"),
        ),
    )
    assert tuple((row.team_id, row.packet_id) for row in report.items) == (
        ("crypto_btc", "complete_stale"),
        ("politics", "missing_memory"),
    )
    assert report.items[0].source_status == "stale"
    assert report.items[0].source_age_seconds == Decimal("7200.000000")
    assert report.items[1].source_status == "missing"
    assert report.items[1].source_age_seconds is None
    assert report.items[1].redacted_reviewer_notes == (
        "sensitive=<redacted>",
        "sensitive=<redacted>",
        "sensitive=<redacted>",
    )
    serialized_report = repr(report).lower()
    for fragment in (
        "postgresql://",
        "secret-value",
        "0xabcdef",
        "api_key=secret",
        "private_key=0x",
    ):
        assert fragment not in serialized_report
    assert tuple((row.team_id, row.summary_status) for row in report.team_summaries) == (
        ("crypto_btc", "blocked"),
        ("politics", "blocked"),
    )


def test_checklist_normalizes_utc_and_uses_decimal_ratios() -> None:
    generated_at = datetime(
        2026,
        7,
        2,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    observed_at = datetime(
        2026,
        7,
        2,
        13,
        30,
        tzinfo=timezone(timedelta(hours=2)),
    )

    report = build_team_research_review_checklist_report(
        (
            _item(
                "packet_offset",
                evidence_completion_ratio=Decimal("0.3333334"),
                latest_source_observed_at=observed_at,
            ),
        ),
        config=_config(max_source_age_seconds=Decimal("3600.000000")),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.items[0].latest_source_observed_at == datetime(
        2026,
        7,
        2,
        11,
        30,
        tzinfo=UTC,
    )
    assert report.items[0].source_age_seconds == Decimal("1800.000000")
    assert report.items[0].evidence_completion_ratio == Decimal("0.333333")
    assert report.evidence_completion_ratio == Decimal("0.333333")

    with pytest.raises(ValueError, match="future"):
        build_team_research_review_checklist_report(
            (
                _item(
                    "future_packet",
                    latest_source_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_checklist_blocks_empty_packets() -> None:
    report = build_team_research_review_checklist_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.summary_status == "blocked"
    assert report.packet_count == Decimal("0.000000")
    assert report.evidence_completion_ratio is None
    assert report.items == ()
    assert report.team_summaries == ()
    assert report.reason_codes == ("team_research_review_empty_packets",)


def test_checklist_validates_exact_types_consistency_and_hard_flags() -> None:
    with pytest.raises(ValueError, match="config_version"):
        TeamResearchReviewChecklistConfig(
            config_version=_StringSubclass(
                DEFAULT_TEAM_RESEARCH_REVIEW_CHECKLIST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="max_source_age_seconds"):
        TeamResearchReviewChecklistConfig(max_source_age_seconds=_IntSubclass(3_600))
    with pytest.raises(ValueError, match="max_source_age_seconds"):
        TeamResearchReviewChecklistConfig(max_source_age_seconds=3_600)
    with pytest.raises(ValueError, match="generated_at"):
        build_team_research_review_checklist_report(
            (_item("packet"),),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="team_id"):
        _item("packet", team_id="unknown_team")
    with pytest.raises(ValueError, match="packet_id"):
        _item(_StringSubclass("packet"))
    with pytest.raises(ValueError, match="evidence_completion_ratio"):
        _item("packet", evidence_completion_ratio=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="reviewer_notes"):
        _item("packet", reviewer_notes=("ok", _StringSubclass("secret=bad")))
    with pytest.raises(ValueError, match="items"):
        build_team_research_review_checklist_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique"):
        build_team_research_review_checklist_report(
            (_item("duplicate"), _item("duplicate")),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_item("non_paper"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(_item("non_report"), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_item("non_readonly"), readonly=False)

    report = build_team_research_review_checklist_report(
        (_item("packet"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="packet_count"):
        TeamResearchReviewChecklistReport(
            **{**report.__dict__, "packet_count": 2},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        TeamResearchReviewChecklistReport(
            **{
                **report.__dict__,
                "reason_code_counts": (
                    TeamResearchReviewChecklistReasonCodeCount(
                        reason_code="team_research_review_checklist_passed",
                            count=Decimal("2.000000"),
                        ),
                    ),
            },
        )


def test_checklist_dataclasses_are_frozen() -> None:
    values = (
        _config(),
        _item("packet"),
        TeamResearchReviewChecklistReasonCodeCount(
            reason_code="team_research_review_checklist_passed",
            count=Decimal("1.000000"),
        ),
        TeamResearchReviewChecklistTeamSummary(
            team_id="politics",
            packet_count=Decimal("1.000000"),
            complete_evidence_count=Decimal("1.000000"),
            fresh_source_count=Decimal("1.000000"),
            memory_ready_count=Decimal("1.000000"),
            calibration_available_count=Decimal("1.000000"),
            blocked_packet_count=Decimal("0.000000"),
            evidence_completion_ratio=Decimal("1.000000"),
            summary_status="pass",
            reason_codes=("team_research_review_checklist_passed",),
        ),
        build_team_research_review_checklist_report(
            (_item("packet"),),
            config=_config(),
            generated_at=GENERATED_AT,
        ),
    )

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_checklist_exposes_decimal_payload_digest_and_rejects_unsafe_payloads() -> None:
    report = build_team_research_review_checklist_report(
        (_item("packet"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    exposed_numeric_values = (
        report.packet_count,
        report.complete_evidence_count,
        report.fresh_source_count,
        report.memory_ready_count,
        report.calibration_available_count,
        report.blocked_packet_count,
        report.incomplete_evidence_count,
        report.stale_or_missing_source_count,
        report.memory_not_ready_count,
        report.calibration_missing_count,
        report.items[0].source_age_seconds,
        report.team_summaries[0].packet_count,
        report.reason_code_counts[0].count,
    )
    assert all(type(value) is Decimal for value in exposed_numeric_values)
    assert isinstance(report.derived_validation_digest, str)
    assert len(report.derived_validation_digest) == 64

    payload = report.payload
    assert payload["packet_count"] == "1.000000"
    assert payload["items"][0]["source_age_seconds"] == "3600.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest

    def assert_no_public_int_or_float(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                assert_no_public_int_or_float(item)
            return
        if isinstance(value, list):
            for item in value:
                assert_no_public_int_or_float(item)
            return
        assert type(value) not in (int, float)

    assert_no_public_int_or_float(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        TeamResearchReviewChecklistReport(
            **{
                **report.__dict__,
                "config_version": "team-research-review-checklist-v0-tampered",
            },
        )
    with pytest.raises(ValueError, match="unsafe public payload"):
        TeamResearchReviewChecklistReport(
            **{
                **report.__dict__,
                "items": (replace(report.items[0], packet_id="wallet_surface"),),
            },
        )


def test_checklist_module_scope_excludes_execution_advice_io_and_db_imports() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.team_research_review_checklist",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_literals = (
        "market_slug",
        "question",
        "investment",
        "trade",
        "buy",
        "sell",
        "order",
        "wallet",
        "auth",
        "private_key",
        "ranking",
        "position",
        "strategy_weight",
    )
    lowered_source = source.lower()
    assert not any(token in lowered_source for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = ("db", "env", "cli", "psycopg", "requests", "socket")
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    assert module.__all__ == (
        "DEFAULT_TEAM_RESEARCH_REVIEW_CHECKLIST_CONFIG_VERSION",
        "TeamResearchReviewChecklistConfig",
        "TeamResearchReviewChecklistItem",
        "TeamResearchReviewChecklistReasonCodeCount",
        "TeamResearchReviewChecklistReport",
        "TeamResearchReviewChecklistTeamSummary",
        "build_team_research_review_checklist_report",
    )
