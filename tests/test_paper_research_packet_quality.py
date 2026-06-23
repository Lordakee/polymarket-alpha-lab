from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketConfig,
    PaperResearchPacketInputRow,
    PaperResearchPacketReport,
    build_paper_research_packet_report,
)


GENERATED_AT = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 6, 23, 11, 55, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return import_module("polymarket_alpha_lab.paper_research_packet_quality")


def _packet_config() -> PaperResearchPacketConfig:
    return PaperResearchPacketConfig(
        config_version="paper-research-packet-v0",
        max_packet_rows=10,
        min_score=d("0.200000"),
    )


def _input_row(
    market_slug: str,
    *,
    side: str = "yes",
    action: str = "recommend",
    queue_status: str = "ready",
    recommendation_score: Decimal = d("0.800000"),
    net_edge: Decimal = d("0.060000"),
    reason_codes: tuple[str, ...] = ("positive_edge",),
) -> PaperResearchPacketInputRow:
    return PaperResearchPacketInputRow(
        market_slug=market_slug,
        question=f"Will {market_slug} resolve yes?",
        side=side,
        action=action,
        queue_status=queue_status,
        recommendation_score=recommendation_score,
        net_edge=net_edge,
        allocated_notional=d("5.000000") if side != "none" else None,
        requested_notional=d("8.000000") if side != "none" else None,
        reason_codes=reason_codes,
    )


def _skip_row(
    market_slug: str,
    *,
    reason_codes: tuple[str, ...] = ("manual_reject",),
) -> PaperResearchPacketInputRow:
    return _input_row(
        market_slug,
        side="none",
        action="reject",
        queue_status="blocked",
        recommendation_score=d("0.000000"),
        net_edge=d("0.000000"),
        reason_codes=reason_codes,
    )


def _packet_report(
    rows: tuple[PaperResearchPacketInputRow, ...],
    *,
    generated_at: datetime = SOURCE_AT,
) -> PaperResearchPacketReport:
    return build_paper_research_packet_report(
        rows,
        config=_packet_config(),
        generated_at=generated_at,
    )


def _quality_report(
    packet_report: PaperResearchPacketReport,
    *,
    cfg=None,
    generated_at: datetime = GENERATED_AT,
):
    api = _api()
    return api.build_paper_research_packet_quality_report(
        packet_report,
        config=cfg or api.PaperResearchPacketQualityConfig(),
        generated_at=generated_at,
    )


def test_quality_config_defaults_match_public_api_and_hard_flags():
    api = _api()

    assert api.DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_CONFIG_VERSION == (
        "paper-research-packet-quality-v0"
    )
    assert api.__all__ == (
        "DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_CONFIG_VERSION",
        "PaperResearchPacketQualityConfig",
        "PaperResearchPacketQualityCheckRow",
        "PaperResearchPacketQualityReasonCodeCount",
        "PaperResearchPacketQualityReport",
        "build_paper_research_packet_quality_report",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(api.PaperResearchPacketQualityConfig)
    }
    assert field_defaults["config_version"] == (
        api.DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_CONFIG_VERSION
    )
    assert field_defaults["max_source_age_seconds"] == 21600
    assert field_defaults["blocked_source_age_seconds"] == 86400
    assert field_defaults["min_included_count"] == 1
    assert field_defaults["max_skipped_share"] == d("0.500000")
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True

    config = api.PaperResearchPacketQualityConfig()
    assert config.config_version == "paper-research-packet-quality-v0"
    assert config.max_skipped_share == d("0.500000")
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True


def test_fresh_populated_packet_returns_pass_with_fixed_checks_and_ratios():
    report = _quality_report(
        _packet_report(
            (
                _input_row("alpha", reason_codes=("shared_reason", "alpha_edge")),
                _input_row(
                    "beta",
                    recommendation_score=d("0.700000"),
                    net_edge=d("0.030000"),
                    reason_codes=("shared_reason", "beta_edge"),
                ),
                _skip_row("gamma", reason_codes=("manual_reject",)),
            ),
        ),
        generated_at=datetime(2026, 6, 23, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    api = _api()

    assert isinstance(report, api.PaperResearchPacketQualityReport)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "paper-research-packet-quality-v0"
    assert report.source_generated_at == SOURCE_AT
    assert report.source_config_version == "paper-research-packet-v0"
    assert report.input_row_count == 3
    assert report.packet_row_count == 3
    assert report.included_count == 2
    assert report.skipped_count == 1
    assert report.high_priority_count == 1
    assert report.medium_priority_count == 1
    assert report.low_priority_count == 0
    assert report.source_age_seconds == 300
    assert report.included_share == d("0.666667")
    assert report.skipped_share == d("0.333333")
    assert report.check_count == 3
    assert report.pass_count == 3
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.quality_status == "pass"
    assert tuple(row.check_name for row in report.check_rows) == (
        "source_freshness",
        "packet_population",
        "skip_pressure",
    )
    assert tuple(row.status for row in report.check_rows) == ("pass", "pass", "pass")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_stale_packet_returns_watch_or_blocked_from_freshness_thresholds():
    api = _api()
    config = api.PaperResearchPacketQualityConfig(
        max_source_age_seconds=3600,
        blocked_source_age_seconds=10800,
    )

    watch = _quality_report(
        _packet_report((_input_row("watch-age"),), generated_at=GENERATED_AT - timedelta(hours=2)),
        cfg=config,
    )
    blocked = _quality_report(
        _packet_report(
            (_input_row("blocked-age"),),
            generated_at=GENERATED_AT - timedelta(hours=4),
        ),
        cfg=config,
    )

    assert watch.check_rows[0].check_name == "source_freshness"
    assert watch.check_rows[0].status == "watch"
    assert watch.check_rows[0].observed_value == 7200
    assert watch.quality_status == "watch"
    assert api.PaperResearchPacketQualityReasonCodeCount(
        reason_code="positive_edge",
        count=1,
    ) in watch.reason_code_counts
    assert "source_report_stale" in tuple(
        row.reason_code for row in watch.reason_code_counts
    )

    assert blocked.check_rows[0].status == "blocked"
    assert blocked.check_rows[0].observed_value == 14400
    assert blocked.quality_status == "blocked"
    assert "source_report_expired" in tuple(
        row.reason_code for row in blocked.reason_code_counts
    )


def test_future_source_packet_timestamp_is_rejected():
    packet_report = _packet_report(
        (_input_row("future-source"),),
        generated_at=GENERATED_AT + timedelta(seconds=1),
    )

    with pytest.raises(ValueError, match="source generated_at"):
        _quality_report(packet_report)


def test_zero_packet_rows_and_low_included_count_block_population():
    api = _api()

    empty = _quality_report(_packet_report(()))
    below_minimum = _quality_report(
        _packet_report((_input_row("single-included"),)),
        cfg=api.PaperResearchPacketQualityConfig(min_included_count=2),
    )

    assert empty.packet_row_count == 0
    assert empty.included_share is None
    assert empty.skipped_share is None
    assert empty.check_rows[1].check_name == "packet_population"
    assert empty.check_rows[1].status == "blocked"
    assert empty.check_rows[1].reason_codes == ("packet_rows_missing",)
    assert empty.quality_status == "blocked"

    assert below_minimum.included_count == 1
    assert below_minimum.check_rows[1].status == "blocked"
    assert below_minimum.check_rows[1].reason_codes == (
        "included_count_below_minimum",
    )
    assert below_minimum.quality_status == "blocked"


def test_skipped_share_over_threshold_returns_watch_without_floats():
    api = _api()
    report = _quality_report(
        _packet_report(
            (
                _input_row("included"),
                _skip_row("skipped", reason_codes=("bad_resolution_source",)),
            ),
        ),
        cfg=api.PaperResearchPacketQualityConfig(max_skipped_share=d("0.250000")),
    )

    assert report.skipped_share == d("0.500000")
    assert isinstance(report.skipped_share, Decimal)
    assert report.check_rows[2].check_name == "skip_pressure"
    assert report.check_rows[2].status == "watch"
    assert report.check_rows[2].threshold == d("0.250000")
    assert report.check_rows[2].reason_codes == ("skipped_share_above_threshold",)
    assert report.quality_status == "watch"

    with pytest.raises(ValueError, match="max_skipped_share"):
        api.PaperResearchPacketQualityConfig(max_skipped_share=0.25)


def test_reason_code_counts_are_sorted_by_count_descending_then_code():
    api = _api()
    report = _quality_report(
        _packet_report(
            (
                _input_row("alpha", reason_codes=("shared_reason", "alpha_edge")),
                _input_row(
                    "beta",
                    recommendation_score=d("0.700000"),
                    net_edge=d("0.030000"),
                    reason_codes=("shared_reason", "beta_edge"),
                ),
            ),
        ),
    )

    assert report.reason_code_counts == (
        api.PaperResearchPacketQualityReasonCodeCount(
            reason_code="shared_reason",
            count=2,
        ),
        api.PaperResearchPacketQualityReasonCodeCount(
            reason_code="alpha_edge",
            count=1,
        ),
        api.PaperResearchPacketQualityReasonCodeCount(
            reason_code="beta_edge",
            count=1,
        ),
        api.PaperResearchPacketQualityReasonCodeCount(
            reason_code="packet_population_passed",
            count=1,
        ),
        api.PaperResearchPacketQualityReasonCodeCount(
            reason_code="skip_pressure_passed",
            count=1,
        ),
        api.PaperResearchPacketQualityReasonCodeCount(
            reason_code="source_freshness_passed",
            count=1,
        ),
    )


def test_quality_dataclasses_are_frozen_and_validate_hard_flags():
    api = _api()
    report = _quality_report(_packet_report((_input_row("frozen"),)))

    with pytest.raises(FrozenInstanceError):
        report.quality_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        report.check_rows[0].status = "blocked"
    with pytest.raises(FrozenInstanceError):
        report.reason_code_counts[0].count = 99
    with pytest.raises(FrozenInstanceError):
        api.PaperResearchPacketQualityConfig().min_included_count = 2

    with pytest.raises(ValueError, match="config must be paper_only"):
        api.PaperResearchPacketQualityConfig(paper_only=False)
    with pytest.raises(ValueError, match="check row must be report_only"):
        api.PaperResearchPacketQualityCheckRow(
            check_name="source_freshness",
            status="pass",
            observed_value=0,
            threshold=21600,
            reason_codes=("source_freshness_passed",),
            report_only=False,
        )
    with pytest.raises(ValueError, match="reason count row must be readonly"):
        api.PaperResearchPacketQualityReasonCodeCount(
            reason_code="source_freshness_passed",
            count=1,
            readonly=False,
        )
    with pytest.raises(ValueError, match="quality report must be paper_only"):
        replace(report, paper_only=False)


def test_reducer_rejects_wrong_report_type_subclasses_config_subclass_and_bad_flags():
    api = _api()
    packet_report = _packet_report((_input_row("valid"),))

    class ReportSubclass(PaperResearchPacketReport):
        pass

    class ConfigSubclass(api.PaperResearchPacketQualityConfig):
        pass

    report_subclass = ReportSubclass(
        generated_at=packet_report.generated_at,
        config_version=packet_report.config_version,
        input_row_count=packet_report.input_row_count,
        packet_row_count=packet_report.packet_row_count,
        included_count=packet_report.included_count,
        skipped_count=packet_report.skipped_count,
        high_priority_count=packet_report.high_priority_count,
        medium_priority_count=packet_report.medium_priority_count,
        low_priority_count=packet_report.low_priority_count,
        packet_rows=packet_report.packet_rows,
    )
    bad_flags_report = _packet_report((_input_row("bad-flags"),))
    object.__setattr__(bad_flags_report, "readonly", False)

    with pytest.raises(ValueError, match="packet_report must be a PaperResearchPacketReport"):
        _quality_report(object())
    with pytest.raises(ValueError, match="packet_report must be a PaperResearchPacketReport"):
        _quality_report(report_subclass)
    with pytest.raises(ValueError, match="config must be a PaperResearchPacketQualityConfig"):
        _quality_report(packet_report, cfg=ConfigSubclass())
    with pytest.raises(ValueError, match="packet report must be readonly"):
        _quality_report(bad_flags_report)
    with pytest.raises(ValueError, match="generated_at"):
        _quality_report(packet_report, generated_at="bad")
    with pytest.raises(ValueError, match="generated_at"):
        _quality_report(
            packet_report,
            generated_at=_DatetimeSubclass(2026, 6, 23, 12, 0, tzinfo=UTC),
        )
