from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_source_quorum import (
    DEFAULT_TEAM_SOURCE_QUORUM_CONFIG_VERSION,
    TeamSourceQuorumConfig,
    TeamSourceQuorumItem,
    TeamSourceQuorumItemStatus,
    TeamSourceQuorumReasonCodeCount,
    TeamSourceQuorumReport,
    TeamSourceQuorumSource,
    TeamSourceQuorumSourceStatus,
    build_team_source_quorum_summary,
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


class _NonAwareTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _config(**overrides: object) -> TeamSourceQuorumConfig:
    values = {
        "config_version": DEFAULT_TEAM_SOURCE_QUORUM_CONFIG_VERSION,
        "max_source_age_seconds": Decimal("3600.000000"),
        "min_independent_source_families": Decimal("2.000000"),
        "min_current_source_count": Decimal("2.000000"),
        "min_corroboration_coverage_ratio": Decimal("0.5"),
    }
    values.update(overrides)
    for key in (
        "max_source_age_seconds",
        "min_independent_source_families",
        "min_current_source_count",
    ):
        if type(values[key]) is int:
            values[key] = Decimal(values[key]).quantize(Decimal("0.000001"))
    return TeamSourceQuorumConfig(**values)


def _source(
    source_id: str,
    *,
    team_id: str = "politics",
    item_id: str = "item_alpha",
    source_family: str = "official",
    observed_at: datetime | None = None,
    corroborates_item: bool = True,
    missing_reason: str | None = None,
    blocked_reason: str | None = None,
) -> TeamSourceQuorumSource:
    return TeamSourceQuorumSource(
        team_id=team_id,
        item_id=item_id,
        source_id=source_id,
        source_family=source_family,
        observed_at=observed_at,
        corroborates_item=corroborates_item,
        source_config_version="quorum-source-v0",
        missing_reason=missing_reason,
        blocked_reason=blocked_reason,
    )


def test_source_quorum_passes_with_independent_current_corroborated_sources() -> None:
    report = build_team_source_quorum_summary(
        (
            _source(
                "source_alpha",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(seconds=60),
            ),
            _source(
                "source_beta",
                source_family="specialist_model",
                observed_at=GENERATED_AT - timedelta(seconds=120),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, TeamSourceQuorumReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_TEAM_SOURCE_QUORUM_CONFIG_VERSION
    assert report.team_id == "politics"
    assert report.summary_status == "pass"
    assert report.recommended_next_step == "allow_report_only_research_item_summary"
    assert report.item_count == 1
    assert report.pass_item_count == 1
    assert report.watch_item_count == 0
    assert report.blocked_item_count == 0
    assert report.required_source_family_count == 2
    assert report.required_current_source_count == 2
    assert report.min_corroboration_coverage_ratio == Decimal("0.5")
    assert report.current_source_count == 2
    assert report.stale_source_count == 0
    assert report.missing_source_count == 0
    assert report.blocked_source_count == 0
    assert report.corroborating_current_source_count == 2
    assert report.corroboration_coverage_ratio == Decimal("1")
    assert report.max_source_age_seconds == 3_600
    assert report.max_observed_source_age_seconds == 120
    assert report.reason_codes == ("team_source_quorum_passed",)
    assert report.reason_code_counts == (
        TeamSourceQuorumReasonCodeCount(
            reason_code="team_source_quorum_passed",
            count=Decimal("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("source_alpha", "quorum-source-v0"),
        ("source_beta", "quorum-source-v0"),
    )
    assert report.item_statuses == (
        TeamSourceQuorumItemStatus(
            team_id="politics",
            item_id="item_alpha",
            summary_status="pass",
            required_source_family_count=Decimal("2.000000"),
            observed_source_family_count=Decimal("2.000000"),
            current_source_family_count=Decimal("2.000000"),
            required_current_source_count=Decimal("2.000000"),
            current_source_count=Decimal("2.000000"),
            stale_source_count=Decimal("0.000000"),
            missing_source_count=Decimal("0.000000"),
            blocked_source_count=Decimal("0.000000"),
            corroborating_current_source_count=Decimal("2.000000"),
            corroboration_coverage_ratio=Decimal("1"),
            max_source_age_seconds=Decimal("120.000000"),
            reason_codes=("team_source_quorum_passed",),
        ),
    )
    assert report.source_statuses == (
        TeamSourceQuorumSourceStatus(
            team_id="politics",
            item_id="item_alpha",
            source_id="source_alpha",
            source_family="official",
            source_status="current",
            observed_at=GENERATED_AT - timedelta(seconds=60),
            source_age_seconds=Decimal("60.000000"),
            corroborates_item=True,
            source_config_version="quorum-source-v0",
            missing_reason=None,
            blocked_reason=None,
            reason_codes=("team_source_quorum_passed",),
        ),
        TeamSourceQuorumSourceStatus(
            team_id="politics",
            item_id="item_alpha",
            source_id="source_beta",
            source_family="specialist_model",
            source_status="current",
            observed_at=GENERATED_AT - timedelta(seconds=120),
            source_age_seconds=Decimal("120.000000"),
            corroborates_item=True,
            source_config_version="quorum-source-v0",
            missing_reason=None,
            blocked_reason=None,
            reason_codes=("team_source_quorum_passed",),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_source_quorum_blocks_insufficient_families_current_sources_and_corroboration() -> None:
    report = build_team_source_quorum_summary(
        (
            _source(
                "source_alpha",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(seconds=60),
                corroborates_item=False,
            ),
            _source(
                "source_beta",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(seconds=120),
                corroborates_item=True,
            ),
        ),
        config=_config(
            min_independent_source_families=2,
            min_current_source_count=3,
            min_corroboration_coverage_ratio=Decimal("0.75"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.summary_status == "blocked"
    assert report.recommended_next_step == "block_report_only_research_item_summary"
    assert report.readiness_gap_count == 3
    assert report.current_source_count == 2
    assert report.corroborating_current_source_count == 1
    assert report.corroboration_coverage_ratio == Decimal("0.5")
    assert report.reason_codes == (
        "team_source_quorum_insufficient_source_families",
        "team_source_quorum_insufficient_current_sources",
        "team_source_quorum_insufficient_corroboration",
    )
    assert report.item_statuses[0].readiness_gap_count == 3
    assert report.item_statuses[0].current_source_family_count == 1
    assert report.item_statuses[0].corroboration_coverage_ratio == Decimal("0.5")


def test_source_quorum_watches_stale_extra_sources_and_sorts_deterministically() -> None:
    report = build_team_source_quorum_summary(
        (
            _source(
                "zeta_current",
                source_family="model",
                observed_at=GENERATED_AT - timedelta(seconds=60),
            ),
            _source(
                "alpha_stale",
                source_family="archive",
                observed_at=GENERATED_AT - timedelta(seconds=3_601),
            ),
            _source(
                "beta_current",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(seconds=120),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.summary_status == "watch"
    assert report.recommended_next_step == "refresh_report_only_research_item_sources"
    assert report.reason_codes == ("team_source_quorum_stale_sources_present",)
    assert report.max_observed_source_age_seconds == 3_601
    assert tuple(row.source_id for row in report.source_statuses) == (
        "alpha_stale",
        "zeta_current",
        "beta_current",
    )
    assert tuple(row.source_status for row in report.source_statuses) == (
        "stale",
        "current",
        "current",
    )
    assert report.reason_code_counts == (
        TeamSourceQuorumReasonCodeCount(
            reason_code="team_source_quorum_stale_sources_present",
            count=Decimal("1.000000"),
        ),
    )


def test_source_quorum_blocks_missing_blocked_and_empty_expected_items() -> None:
    report = build_team_source_quorum_summary(
        (
            _source(
                "fresh_source",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(seconds=60),
            ),
            _source(
                "missing_source",
                source_family="model",
                missing_reason="source_not_collected",
                corroborates_item=False,
            ),
            _source(
                "blocked_source",
                source_family="specialist",
                blocked_reason="source_access_blocked",
                corroborates_item=False,
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
        expected_items=(TeamSourceQuorumItem(team_id="politics", item_id="item_beta"),),
    )

    assert report.summary_status == "blocked"
    assert report.item_count == 2
    assert report.pass_item_count == 0
    assert report.blocked_item_count == 2
    assert report.missing_source_count == 1
    assert report.blocked_source_count == 1
    assert report.reason_codes == (
        "team_source_quorum_blocked_sources_present",
        "team_source_quorum_missing_sources_present",
        "team_source_quorum_insufficient_source_families",
        "team_source_quorum_insufficient_current_sources",
        "team_source_quorum_empty_items",
    )
    assert tuple(row.item_id for row in report.item_statuses) == ("item_alpha", "item_beta")
    assert report.item_statuses[1].reason_codes == (
        "team_source_quorum_empty_items",
        "team_source_quorum_insufficient_source_families",
        "team_source_quorum_insufficient_current_sources",
    )
    assert tuple(row.source_id for row in report.source_statuses) == (
        "blocked_source",
        "missing_source",
        "fresh_source",
    )
    assert report.source_statuses[0].blocked_reason == "source_access_blocked"
    assert report.source_statuses[1].missing_reason == "source_not_collected"


def test_source_quorum_reason_code_counts_count_each_item_occurrence() -> None:
    report = build_team_source_quorum_summary(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
        expected_items=(
            TeamSourceQuorumItem(team_id="politics", item_id="item_alpha"),
            TeamSourceQuorumItem(team_id="politics", item_id="item_beta"),
        ),
    )

    assert report.summary_status == "blocked"
    assert report.item_count == 2
    assert report.reason_codes == (
        "team_source_quorum_empty_items",
        "team_source_quorum_insufficient_source_families",
        "team_source_quorum_insufficient_current_sources",
    )
    assert report.reason_code_counts == (
        TeamSourceQuorumReasonCodeCount(
            reason_code="team_source_quorum_empty_items",
            count=Decimal("2.000000"),
        ),
        TeamSourceQuorumReasonCodeCount(
            reason_code="team_source_quorum_insufficient_current_sources",
            count=Decimal("2.000000"),
        ),
        TeamSourceQuorumReasonCodeCount(
            reason_code="team_source_quorum_insufficient_source_families",
            count=Decimal("2.000000"),
        ),
    )


def test_source_quorum_summarizes_multiple_teams_and_normalizes_datetimes() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 2, 13, 30, tzinfo=timezone(timedelta(hours=2)))

    report = build_team_source_quorum_summary(
        (
            _source(
                "politics_a",
                source_family="official",
                observed_at=observed_at,
            ),
            _source(
                "politics_b",
                source_family="model",
                observed_at=GENERATED_AT - timedelta(seconds=60),
            ),
            _source(
                "btc_a",
                team_id="crypto_btc",
                item_id="item_btc",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(seconds=60),
            ),
            _source(
                "btc_b",
                team_id="crypto_btc",
                item_id="item_btc",
                source_family="model",
                observed_at=GENERATED_AT - timedelta(seconds=7_200),
            ),
        ),
        config=_config(),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.team_id is None
    assert report.summary_status == "blocked"
    assert report.item_count == 2
    assert report.pass_item_count == 1
    assert report.blocked_item_count == 1
    assert report.reason_codes == (
        "team_source_quorum_stale_sources_present",
        "team_source_quorum_insufficient_source_families",
        "team_source_quorum_insufficient_current_sources",
    )
    assert tuple((row.team_id, row.item_id, row.summary_status) for row in report.item_statuses) == (
        ("crypto_btc", "item_btc", "blocked"),
        ("politics", "item_alpha", "pass"),
    )
    politics_offset_source = next(
        row for row in report.source_statuses if row.source_id == "politics_a"
    )
    assert politics_offset_source.observed_at == datetime(2026, 7, 2, 11, 30, tzinfo=UTC)
    assert politics_offset_source.source_age_seconds == 1_800


def test_source_quorum_validates_exact_types_redaction_flags_and_future_sources() -> None:
    with pytest.raises(ValueError, match="config_version"):
        TeamSourceQuorumConfig(config_version=_StringSubclass("team-source-quorum-v0"))
    with pytest.raises(ValueError, match="max_source_age_seconds"):
        TeamSourceQuorumConfig(max_source_age_seconds=_IntSubclass(3_600))
    with pytest.raises(ValueError, match="min_corroboration_coverage_ratio"):
        TeamSourceQuorumConfig(min_corroboration_coverage_ratio=0.5)
    with pytest.raises(ValueError, match="min_corroboration_coverage_ratio"):
        TeamSourceQuorumConfig(min_corroboration_coverage_ratio=_DecimalSubclass("0.5"))
    with pytest.raises(ValueError, match="finite"):
        TeamSourceQuorumConfig(min_corroboration_coverage_ratio=Decimal("NaN"))
    with pytest.raises(ValueError, match="generated_at"):
        build_team_source_quorum_summary(
            (_source("fresh_source", observed_at=GENERATED_AT),),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        _source("naive_source", observed_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        build_team_source_quorum_summary(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NonAwareTz()),
        )
    with pytest.raises(ValueError, match="team_id"):
        TeamSourceQuorumSource(
            team_id="unknown_team",
            item_id="item_alpha",
            source_id="source",
            source_family="official",
            observed_at=GENERATED_AT,
            source_config_version="quorum-source-v0",
        )
    with pytest.raises(ValueError, match="redacted"):
        _source("wallet_0xabc", observed_at=GENERATED_AT)
    with pytest.raises(ValueError, match="redacted"):
        _source("source", item_id="account_email", observed_at=GENERATED_AT)
    with pytest.raises(ValueError, match="redacted"):
        _source("source", source_family="email_feed", observed_at=GENERATED_AT)
    with pytest.raises(ValueError, match="redacted"):
        _source(
            "blocked_source",
            blocked_reason="contains secret token",
            corroborates_item=False,
        )
    with pytest.raises(ValueError, match="only observed"):
        _source("missing_source", missing_reason="missing", corroborates_item=True)
    with pytest.raises(ValueError, match="source status"):
        _source("bad_shape", observed_at=GENERATED_AT, missing_reason="missing")
    with pytest.raises(ValueError, match="sources"):
        build_team_source_quorum_summary((object(),), config=_config(), generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="future"):
        build_team_source_quorum_summary(
            (_source("future_source", observed_at=GENERATED_AT + timedelta(seconds=1)),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_source("non_paper", observed_at=GENERATED_AT), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(_source("non_report", observed_at=GENERATED_AT), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_source("non_readonly", observed_at=GENERATED_AT), readonly=False)


def test_source_quorum_requires_decimal_only_public_numeric_surface() -> None:
    with pytest.raises(ValueError, match="max_source_age_seconds"):
        TeamSourceQuorumConfig(max_source_age_seconds=3_600)
    with pytest.raises(ValueError, match="min_independent_source_families"):
        TeamSourceQuorumConfig(
            max_source_age_seconds=Decimal("3600.000000"),
            min_independent_source_families=2,
        )
    with pytest.raises(ValueError, match="min_current_source_count"):
        TeamSourceQuorumConfig(
            max_source_age_seconds=Decimal("3600.000000"),
            min_independent_source_families=Decimal("2.000000"),
            min_current_source_count=2,
        )
    with pytest.raises(ValueError, match="source_age_seconds"):
        TeamSourceQuorumSourceStatus(
            team_id="politics",
            item_id="item_alpha",
            source_id="source_alpha",
            source_family="official",
            source_status="current",
            observed_at=GENERATED_AT,
            source_age_seconds=0,
            corroborates_item=True,
            source_config_version="quorum-source-v0",
            missing_reason=None,
            blocked_reason=None,
            reason_codes=("team_source_quorum_passed",),
        )
    with pytest.raises(ValueError, match="required_source_family_count"):
        TeamSourceQuorumItemStatus(
            team_id="politics",
            item_id="item_alpha",
            summary_status="pass",
            required_source_family_count=1,
            observed_source_family_count=Decimal("1.000000"),
            current_source_family_count=Decimal("1.000000"),
            required_current_source_count=Decimal("1.000000"),
            current_source_count=Decimal("1.000000"),
            stale_source_count=Decimal("0.000000"),
            missing_source_count=Decimal("0.000000"),
            blocked_source_count=Decimal("0.000000"),
            corroborating_current_source_count=Decimal("1.000000"),
            corroboration_coverage_ratio=Decimal("1.000000"),
            max_source_age_seconds=Decimal("0.000000"),
            reason_codes=("team_source_quorum_passed",),
        )
    with pytest.raises(ValueError, match="count"):
        TeamSourceQuorumReasonCodeCount(
            reason_code="team_source_quorum_passed",
            count=1,
        )
    with pytest.raises(ValueError, match="min_independent_source_families"):
        TeamSourceQuorumConfig(
            max_source_age_seconds=Decimal("3600.000000"),
            min_independent_source_families=Decimal("2.500000"),
        )
    with pytest.raises(ValueError, match="min_current_source_count"):
        TeamSourceQuorumConfig(
            max_source_age_seconds=Decimal("3600.000000"),
            min_independent_source_families=Decimal("2.000000"),
            min_current_source_count=Decimal("2.500000"),
        )

    report = build_team_source_quorum_summary(
        (
            _source(
                "source_alpha",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(seconds=60),
            ),
            _source(
                "source_beta",
                source_family="specialist_model",
                observed_at=GENERATED_AT - timedelta(seconds=120),
            ),
        ),
        config=TeamSourceQuorumConfig(
            max_source_age_seconds=Decimal("3600.000000"),
            min_independent_source_families=Decimal("2.000000"),
            min_current_source_count=Decimal("2.000000"),
            min_corroboration_coverage_ratio=Decimal("0.500000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.item_count == Decimal("1.000000")
    assert report.current_source_count == Decimal("2.000000")
    assert report.max_source_age_seconds == Decimal("3600.000000")
    assert report.max_observed_source_age_seconds == Decimal("120.000000")
    assert report.item_statuses[0].required_source_family_count == Decimal("2.000000")
    assert report.source_statuses[0].source_age_seconds == Decimal("60.000000")
    assert report.reason_code_counts == (
        TeamSourceQuorumReasonCodeCount(
            reason_code="team_source_quorum_passed",
            count=Decimal("1.000000"),
        ),
    )

    with pytest.raises(ValueError, match="item_count"):
        TeamSourceQuorumReport(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_TEAM_SOURCE_QUORUM_CONFIG_VERSION,
            team_id="politics",
            summary_status="pass",
            recommended_next_step="allow_report_only_research_item_summary",
            item_count=1,
            pass_item_count=Decimal("1.000000"),
            watch_item_count=Decimal("0.000000"),
            blocked_item_count=Decimal("0.000000"),
            required_source_family_count=Decimal("2.000000"),
            required_current_source_count=Decimal("2.000000"),
            min_corroboration_coverage_ratio=Decimal("0.500000"),
            current_source_count=Decimal("2.000000"),
            stale_source_count=Decimal("0.000000"),
            missing_source_count=Decimal("0.000000"),
            blocked_source_count=Decimal("0.000000"),
            corroborating_current_source_count=Decimal("2.000000"),
            corroboration_coverage_ratio=Decimal("1.000000"),
            max_source_age_seconds=Decimal("3600.000000"),
            max_observed_source_age_seconds=Decimal("120.000000"),
            source_statuses=report.source_statuses,
            item_statuses=report.item_statuses,
            source_config_versions=report.source_config_versions,
            reason_code_counts=report.reason_code_counts,
            reason_codes=report.reason_codes,
        )


def test_source_quorum_report_reason_codes_follow_canonical_order_across_items() -> None:
    report = build_team_source_quorum_summary(
        (
            _source(
                "blocked_source",
                item_id="item_alpha",
                source_family="specialist",
                blocked_reason="source_access_blocked",
                corroborates_item=False,
            ),
            _source(
                "fresh_source",
                item_id="item_beta",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(seconds=60),
                corroborates_item=False,
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.reason_codes == (
        "team_source_quorum_blocked_sources_present",
        "team_source_quorum_insufficient_source_families",
        "team_source_quorum_insufficient_current_sources",
        "team_source_quorum_insufficient_corroboration",
    )


def test_source_quorum_rejects_nondeterministic_item_reason_order() -> None:
    with pytest.raises(ValueError, match="reason_codes"):
        TeamSourceQuorumItemStatus(
            team_id="politics",
            item_id="item_alpha",
            summary_status="blocked",
            required_source_family_count=Decimal("2.000000"),
            observed_source_family_count=Decimal("1.000000"),
            current_source_family_count=Decimal("1.000000"),
            required_current_source_count=Decimal("2.000000"),
            current_source_count=Decimal("1.000000"),
            stale_source_count=Decimal("0.000000"),
            missing_source_count=Decimal("0.000000"),
            blocked_source_count=Decimal("0.000000"),
            corroborating_current_source_count=Decimal("1.000000"),
            corroboration_coverage_ratio=Decimal("1"),
            max_source_age_seconds=Decimal("0.000000"),
            reason_codes=(
                "team_source_quorum_insufficient_current_sources",
                "team_source_quorum_insufficient_source_families",
            ),
            readiness_gap_count=Decimal("2.000000"),
        )


def test_source_quorum_blocked_item_status_requires_count_derived_reasons() -> None:
    valid_kwargs = dict(
        team_id="politics",
        item_id="item_alpha",
        summary_status="blocked",
        required_source_family_count=Decimal("1.000000"),
        observed_source_family_count=Decimal("0.000000"),
        current_source_family_count=Decimal("0.000000"),
        required_current_source_count=Decimal("1.000000"),
        current_source_count=Decimal("0.000000"),
        stale_source_count=Decimal("0.000000"),
        missing_source_count=Decimal("0.000000"),
        blocked_source_count=Decimal("1.000000"),
        corroborating_current_source_count=Decimal("0.000000"),
        corroboration_coverage_ratio=Decimal("0.000000"),
        max_source_age_seconds=None,
        reason_codes=(
            "team_source_quorum_blocked_sources_present",
            "team_source_quorum_insufficient_source_families",
            "team_source_quorum_insufficient_current_sources",
        ),
        readiness_gap_count=Decimal("3.000000"),
    )

    assert TeamSourceQuorumItemStatus(**valid_kwargs).reason_codes == (
        "team_source_quorum_blocked_sources_present",
        "team_source_quorum_insufficient_source_families",
        "team_source_quorum_insufficient_current_sources",
    )

    with pytest.raises(ValueError, match="reason_codes"):
        TeamSourceQuorumItemStatus(
            **{
                **valid_kwargs,
                "reason_codes": ("team_source_quorum_insufficient_current_sources",),
                "readiness_gap_count": Decimal("1.000000"),
            },
        )


def test_source_quorum_rejects_duplicate_source_and_bad_report_consistency() -> None:
    with pytest.raises(ValueError, match="unique"):
        build_team_source_quorum_summary(
            (
                _source("duplicate_source", observed_at=GENERATED_AT),
                _source("duplicate_source", observed_at=GENERATED_AT),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    source_statuses = (
        TeamSourceQuorumSourceStatus(
            team_id="politics",
            item_id="item_alpha",
            source_id="source_alpha",
            source_family="official",
            source_status="current",
            observed_at=GENERATED_AT,
            source_age_seconds=Decimal("0.000000"),
            corroborates_item=True,
            source_config_version="quorum-source-v0",
            missing_reason=None,
            blocked_reason=None,
            reason_codes=("team_source_quorum_passed",),
        ),
        TeamSourceQuorumSourceStatus(
            team_id="politics",
            item_id="item_alpha",
            source_id="source_beta",
            source_family="specialist_model",
            source_status="current",
            observed_at=GENERATED_AT,
            source_age_seconds=Decimal("0.000000"),
            corroborates_item=True,
            source_config_version="quorum-source-v0",
            missing_reason=None,
            blocked_reason=None,
            reason_codes=("team_source_quorum_passed",),
        ),
    )
    item_statuses = (
        TeamSourceQuorumItemStatus(
            team_id="politics",
            item_id="item_alpha",
            summary_status="pass",
            required_source_family_count=Decimal("2.000000"),
            observed_source_family_count=Decimal("2.000000"),
            current_source_family_count=Decimal("2.000000"),
            required_current_source_count=Decimal("2.000000"),
            current_source_count=Decimal("2.000000"),
            stale_source_count=Decimal("0.000000"),
            missing_source_count=Decimal("0.000000"),
            blocked_source_count=Decimal("0.000000"),
            corroborating_current_source_count=Decimal("2.000000"),
            corroboration_coverage_ratio=Decimal("1"),
            max_source_age_seconds=Decimal("0.000000"),
            reason_codes=("team_source_quorum_passed",),
        ),
    )
    reason_count = TeamSourceQuorumReasonCodeCount(
        reason_code="team_source_quorum_passed",
        count=Decimal("1.000000"),
    )
    kwargs = dict(
        generated_at=GENERATED_AT,
        config_version=DEFAULT_TEAM_SOURCE_QUORUM_CONFIG_VERSION,
        team_id="politics",
        summary_status="pass",
        recommended_next_step="allow_report_only_research_item_summary",
        item_count=Decimal("1.000000"),
        pass_item_count=Decimal("1.000000"),
        watch_item_count=Decimal("0.000000"),
        blocked_item_count=Decimal("0.000000"),
        required_source_family_count=Decimal("2.000000"),
        required_current_source_count=Decimal("2.000000"),
        min_corroboration_coverage_ratio=Decimal("0.5"),
        current_source_count=Decimal("2.000000"),
        stale_source_count=Decimal("0.000000"),
        missing_source_count=Decimal("0.000000"),
        blocked_source_count=Decimal("0.000000"),
        corroborating_current_source_count=Decimal("2.000000"),
        corroboration_coverage_ratio=Decimal("1"),
        max_source_age_seconds=Decimal("3600.000000"),
        max_observed_source_age_seconds=Decimal("0.000000"),
        source_statuses=source_statuses,
        item_statuses=item_statuses,
        source_config_versions=(
            ("source_alpha", "quorum-source-v0"),
            ("source_beta", "quorum-source-v0"),
        ),
        reason_code_counts=(reason_count,),
        reason_codes=("team_source_quorum_passed",),
    )

    assert TeamSourceQuorumReport(**kwargs).summary_status == "pass"

    with pytest.raises(ValueError, match="current_source_count"):
        TeamSourceQuorumReport(**{**kwargs, "current_source_count": 1})
    with pytest.raises(ValueError, match="summary_status"):
        TeamSourceQuorumReport(**{**kwargs, "summary_status": "watch"})
    with pytest.raises(ValueError, match="recommended_next_step"):
        TeamSourceQuorumReport(
            **{**kwargs, "recommended_next_step": "block_report_only_research_item_summary"},
        )
    with pytest.raises(ValueError, match="source_config_versions"):
        TeamSourceQuorumReport(
            **{**kwargs, "source_config_versions": (("source_alpha", "different"),)},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        TeamSourceQuorumReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    TeamSourceQuorumReasonCodeCount(
                        reason_code="team_source_quorum_passed",
                        count=Decimal("2.000000"),
                    ),
                ),
            },
        )


def test_source_quorum_normalizes_source_config_versions_to_tuple_pairs() -> None:
    source_statuses = (
        TeamSourceQuorumSourceStatus(
            team_id="politics",
            item_id="item_alpha",
            source_id="source_alpha",
            source_family="official",
            source_status="current",
            observed_at=GENERATED_AT,
            source_age_seconds=Decimal("0.000000"),
            corroborates_item=True,
            source_config_version="quorum-source-v0",
            missing_reason=None,
            blocked_reason=None,
            reason_codes=("team_source_quorum_passed",),
        ),
        TeamSourceQuorumSourceStatus(
            team_id="politics",
            item_id="item_alpha",
            source_id="source_beta",
            source_family="specialist_model",
            source_status="current",
            observed_at=GENERATED_AT,
            source_age_seconds=Decimal("0.000000"),
            corroborates_item=True,
            source_config_version="quorum-source-v0",
            missing_reason=None,
            blocked_reason=None,
            reason_codes=("team_source_quorum_passed",),
        ),
    )
    item_statuses = (
        TeamSourceQuorumItemStatus(
            team_id="politics",
            item_id="item_alpha",
            summary_status="pass",
            required_source_family_count=Decimal("2.000000"),
            observed_source_family_count=Decimal("2.000000"),
            current_source_family_count=Decimal("2.000000"),
            required_current_source_count=Decimal("2.000000"),
            current_source_count=Decimal("2.000000"),
            stale_source_count=Decimal("0.000000"),
            missing_source_count=Decimal("0.000000"),
            blocked_source_count=Decimal("0.000000"),
            corroborating_current_source_count=Decimal("2.000000"),
            corroboration_coverage_ratio=Decimal("1"),
            max_source_age_seconds=Decimal("0.000000"),
            reason_codes=("team_source_quorum_passed",),
        ),
    )
    mutable_source_config_versions = [
        ["source_alpha", "quorum-source-v0"],
        ["source_beta", "quorum-source-v0"],
    ]

    report = TeamSourceQuorumReport(
        generated_at=GENERATED_AT,
        config_version=DEFAULT_TEAM_SOURCE_QUORUM_CONFIG_VERSION,
        team_id="politics",
        summary_status="pass",
        recommended_next_step="allow_report_only_research_item_summary",
        item_count=Decimal("1.000000"),
        pass_item_count=Decimal("1.000000"),
        watch_item_count=Decimal("0.000000"),
        blocked_item_count=Decimal("0.000000"),
        required_source_family_count=Decimal("2.000000"),
        required_current_source_count=Decimal("2.000000"),
        min_corroboration_coverage_ratio=Decimal("0.5"),
        current_source_count=Decimal("2.000000"),
        stale_source_count=Decimal("0.000000"),
        missing_source_count=Decimal("0.000000"),
        blocked_source_count=Decimal("0.000000"),
        corroborating_current_source_count=Decimal("2.000000"),
        corroboration_coverage_ratio=Decimal("1"),
        max_source_age_seconds=Decimal("3600.000000"),
        max_observed_source_age_seconds=Decimal("0.000000"),
        source_statuses=source_statuses,
        item_statuses=item_statuses,
        source_config_versions=mutable_source_config_versions,
        reason_code_counts=(
            TeamSourceQuorumReasonCodeCount(
                reason_code="team_source_quorum_passed",
                count=Decimal("1.000000"),
            ),
        ),
        reason_codes=("team_source_quorum_passed",),
    )

    mutable_source_config_versions[0][1] = "mutated-source-config-v0"

    assert report.source_config_versions == (
        ("source_alpha", "quorum-source-v0"),
        ("source_beta", "quorum-source-v0"),
    )
    assert tuple(type(pair) for pair in report.source_config_versions) == (tuple, tuple)


def test_source_quorum_dataclasses_are_frozen() -> None:
    values = (
        _config(),
        TeamSourceQuorumItem(team_id="politics", item_id="item_alpha"),
        _source("fresh_source", observed_at=GENERATED_AT),
        TeamSourceQuorumSourceStatus(
            team_id="politics",
            item_id="item_alpha",
            source_id="fresh_source",
            source_family="official",
            source_status="current",
            observed_at=GENERATED_AT,
            source_age_seconds=Decimal("0.000000"),
            corroborates_item=True,
            source_config_version="quorum-source-v0",
            missing_reason=None,
            blocked_reason=None,
            reason_codes=("team_source_quorum_passed",),
        ),
        TeamSourceQuorumReasonCodeCount(
            reason_code="team_source_quorum_passed",
            count=Decimal("1.000000"),
        ),
        TeamSourceQuorumItemStatus(
            team_id="politics",
            item_id="item_alpha",
            summary_status="pass",
            required_source_family_count=Decimal("1.000000"),
            observed_source_family_count=Decimal("1.000000"),
            current_source_family_count=Decimal("1.000000"),
            required_current_source_count=Decimal("1.000000"),
            current_source_count=Decimal("1.000000"),
            stale_source_count=Decimal("0.000000"),
            missing_source_count=Decimal("0.000000"),
            blocked_source_count=Decimal("0.000000"),
            corroborating_current_source_count=Decimal("1.000000"),
            corroboration_coverage_ratio=Decimal("1"),
            max_source_age_seconds=Decimal("0.000000"),
            reason_codes=("team_source_quorum_passed",),
        ),
        build_team_source_quorum_summary(
            (_source("fresh_source", observed_at=GENERATED_AT),),
            config=_config(min_independent_source_families=1, min_current_source_count=1),
            generated_at=GENERATED_AT,
        ),
    )

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_source_quorum_module_scope_excludes_advice_execution_io_and_db_imports() -> None:
    module = importlib.import_module("polymarket_alpha_lab.team_source_quorum")
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
