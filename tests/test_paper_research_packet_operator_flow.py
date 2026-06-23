from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import inspect

import pytest

from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketReport,
    PaperResearchPacketRow,
)
from polymarket_alpha_lab.paper_research_packet_quality import (
    PaperResearchPacketQualityCheckRow,
    PaperResearchPacketQualityReasonCodeCount,
    PaperResearchPacketQualityReport,
)
from polymarket_alpha_lab.paper_research_packet_quality_history import (
    PaperResearchPacketQualityHistoryCheckSummaryRow,
    PaperResearchPacketQualityHistoryRecurringReasonCodeRow,
    PaperResearchPacketQualityHistoryReport,
    PaperResearchPacketQualityHistoryStatusRow,
)


PACKET_AT = datetime(2026, 6, 23, 12, 0)
QUALITY_AT = datetime(2026, 6, 23, 12, 30)
HISTORY_AT = datetime(2026, 6, 23, 13, 0)
GENERATED_AT = datetime(2026, 6, 23, 13, 5)


def _packet_report() -> PaperResearchPacketReport:
    return PaperResearchPacketReport(
        generated_at=PACKET_AT,
        config_version="paper-research-packet-v1",
        input_row_count=2,
        packet_row_count=1,
        included_count=1,
        skipped_count=0,
        high_priority_count=1,
        medium_priority_count=0,
        low_priority_count=0,
        packet_rows=(
            PaperResearchPacketRow(
                packet_rank=1,
                market_slug="election-alpha",
                question="Will election alpha resolve yes?",
                side="yes",
                research_priority="high",
                required_checks=(
                    "outcome_definition",
                    "liquidity_depth",
                    "cost_sensitivity",
                    "settlement_timing",
                ),
                reason_codes=("positive_edge",),
                recommendation_score=Decimal("0.910000"),
                net_edge=Decimal("0.080000"),
                allocated_notional=Decimal("12.500000"),
                requested_notional=Decimal("15.000000"),
            ),
        ),
    )


def _quality_check_rows(
    status: str,
    *,
    source_age_seconds: int,
) -> tuple[PaperResearchPacketQualityCheckRow, ...]:
    source_status = status if status in {"watch", "blocked"} else "pass"
    source_reason = {
        "pass": "source_freshness_passed",
        "watch": "source_report_stale",
        "blocked": "source_report_expired",
    }[source_status]
    return (
        PaperResearchPacketQualityCheckRow(
            check_name="source_freshness",
            status=source_status,
            observed_value=source_age_seconds,
            threshold=21_600 if source_status != "blocked" else 86_400,
            reason_codes=(source_reason,),
        ),
        PaperResearchPacketQualityCheckRow(
            check_name="packet_population",
            status="pass",
            observed_value=1,
            threshold=1,
            reason_codes=("packet_population_passed",),
        ),
        PaperResearchPacketQualityCheckRow(
            check_name="skip_pressure",
            status="pass",
            observed_value=Decimal("0.000000"),
            threshold=Decimal("0.500000"),
            reason_codes=("skip_pressure_passed",),
        ),
    )


def _quality_report(status: str = "pass") -> PaperResearchPacketQualityReport:
    source_age_seconds = {
        "pass": 1_800,
        "watch": 30_000,
        "blocked": 90_000,
    }[status]
    generated_at = PACKET_AT + timedelta(seconds=source_age_seconds)
    check_rows = _quality_check_rows(status, source_age_seconds=source_age_seconds)
    reason_codes = sorted(
        {"positive_edge"}
        | {reason_code for row in check_rows for reason_code in row.reason_codes},
    )
    return PaperResearchPacketQualityReport(
        generated_at=generated_at,
        config_version="paper-research-packet-quality-v1",
        source_generated_at=PACKET_AT,
        source_config_version="paper-research-packet-v1",
        input_row_count=2,
        packet_row_count=1,
        included_count=1,
        skipped_count=0,
        high_priority_count=1,
        medium_priority_count=0,
        low_priority_count=0,
        source_age_seconds=source_age_seconds,
        included_share=Decimal("1.000000"),
        skipped_share=Decimal("0.000000"),
        check_count=3,
        pass_count=sum(1 for row in check_rows if row.status == "pass"),
        watch_count=sum(1 for row in check_rows if row.status == "watch"),
        blocked_count=sum(1 for row in check_rows if row.status == "blocked"),
        quality_status=status,
        check_rows=check_rows,
        reason_code_counts=tuple(
            PaperResearchPacketQualityReasonCodeCount(
                reason_code=reason_code,
                count=1,
            )
            for reason_code in reason_codes
        ),
    )


def _history_check_rows(
    latest_quality_status: str,
) -> tuple[PaperResearchPacketQualityHistoryCheckSummaryRow, ...]:
    source_status = latest_quality_status if latest_quality_status != "pass" else "pass"
    source_reason = {
        "pass": "source_freshness_passed",
        "watch": "source_report_stale",
        "blocked": "source_report_expired",
    }[source_status]
    return (
        PaperResearchPacketQualityHistoryCheckSummaryRow(
            check_name="source_freshness",
            status=source_status,
            reason_codes=(source_reason,),
        ),
        PaperResearchPacketQualityHistoryCheckSummaryRow(
            check_name="packet_population",
            status="pass",
            reason_codes=("packet_population_passed",),
        ),
        PaperResearchPacketQualityHistoryCheckSummaryRow(
            check_name="skip_pressure",
            status="pass",
            reason_codes=("skip_pressure_passed",),
        ),
    )


def _history_report(
    status: str = "pass",
    *,
    quality_report: PaperResearchPacketQualityReport | None = None,
) -> PaperResearchPacketQualityHistoryReport:
    source_quality = quality_report or _quality_report()
    latest_quality_status = source_quality.quality_status
    latest_check_rows = _history_check_rows(latest_quality_status)
    generated_at = source_quality.generated_at + timedelta(minutes=30)
    reason_codes = {
        "pass": ("paper_research_packet_quality_history_passed",),
        "watch": ("duplicate_generated_at_threshold_exceeded",),
        "blocked": ("blocked_quality_report_threshold_exceeded",),
    }[status]
    recurring_rows = (
        (
            PaperResearchPacketQualityHistoryRecurringReasonCodeRow(
                check_status="blocked",
                reason_code="source_report_expired",
                report_count=2,
            ),
        )
        if status == "blocked"
        else ()
    )
    return PaperResearchPacketQualityHistoryReport(
        generated_at=generated_at,
        config_version="paper-research-packet-quality-history-v1",
        history_status=status,
        source_report_count=3,
        first_source_generated_at=source_quality.generated_at - timedelta(hours=2),
        latest_source_generated_at=source_quality.generated_at,
        latest_quality_status=latest_quality_status,
        latest_source_age_seconds=source_quality.source_age_seconds,
        latest_included_share=source_quality.included_share,
        latest_skipped_share=source_quality.skipped_share,
        latest_check_rows=latest_check_rows,
        quality_status_rows=(
            PaperResearchPacketQualityHistoryStatusRow(
                quality_status="pass",
                status_count=2 if latest_quality_status != "pass" else 3,
            ),
            PaperResearchPacketQualityHistoryStatusRow(
                quality_status="watch",
                status_count=1 if latest_quality_status == "watch" else 0,
            ),
            PaperResearchPacketQualityHistoryStatusRow(
                quality_status="blocked",
                status_count=1 if latest_quality_status == "blocked" else 0,
            ),
        ),
        duplicate_generated_at_count=1 if status == "watch" else 0,
        recurring_reason_code_rows=recurring_rows,
        reason_codes=reason_codes,
    )


def _build_report(
    *,
    packet_report: PaperResearchPacketReport | object | None = None,
    packet_persisted: bool = True,
    quality_report: PaperResearchPacketQualityReport | object | None = None,
    quality_persisted: bool = True,
    history_report: PaperResearchPacketQualityHistoryReport | object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    from polymarket_alpha_lab.paper_research_packet_operator_flow import (
        PaperResearchPacketOperatorFlowConfig,
        build_paper_research_packet_operator_flow_report,
    )

    resolved_quality = quality_report if quality_report is not None else _quality_report()
    return build_paper_research_packet_operator_flow_report(
        packet_report=packet_report if packet_report is not None else _packet_report(),
        packet_persisted=packet_persisted,
        quality_report=resolved_quality,
        quality_persisted=quality_persisted,
        quality_history_report=(
            history_report
            if history_report is not None
            else _history_report(quality_report=resolved_quality)  # type: ignore[arg-type]
        ),
        config=PaperResearchPacketOperatorFlowConfig(),
        generated_at=generated_at,
    )


def test_public_exports_include_report_config_builder_and_default_version() -> None:
    import polymarket_alpha_lab.paper_research_packet_operator_flow as module

    assert module.DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_CONFIG_VERSION == (
        "paper-research-packet-operator-flow-v0"
    )
    assert {
        "DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_CONFIG_VERSION",
        "PaperResearchPacketOperatorFlowConfig",
        "PaperResearchPacketOperatorFlowReport",
        "build_paper_research_packet_operator_flow_report",
    }.issubset(set(module.__all__))


def test_config_defaults_are_frozen_paper_only_report_only_and_readonly() -> None:
    from polymarket_alpha_lab.paper_research_packet_operator_flow import (
        PaperResearchPacketOperatorFlowConfig,
    )

    config = PaperResearchPacketOperatorFlowConfig()

    assert config.config_version == "paper-research-packet-operator-flow-v0"
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True
    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]


def test_builder_creates_pass_report_with_normalized_source_fields() -> None:
    report = _build_report(generated_at=GENERATED_AT)

    assert report.generated_at == GENERATED_AT.replace(tzinfo=UTC)
    assert report.config_version == "paper-research-packet-operator-flow-v0"
    assert report.flow_status == "pass"
    assert report.packet_generated_at == PACKET_AT.replace(tzinfo=UTC)
    assert report.packet_config_version == "paper-research-packet-v1"
    assert report.packet_persisted is True
    assert report.packet_row_count == 1
    assert report.included_count == 1
    assert report.skipped_count == 0
    assert report.quality_generated_at == QUALITY_AT.replace(tzinfo=UTC)
    assert report.quality_config_version == "paper-research-packet-quality-v1"
    assert report.quality_status == "pass"
    assert report.quality_persisted is True
    assert report.quality_check_count == 3
    assert report.quality_pass_count == 3
    assert report.quality_watch_count == 0
    assert report.quality_blocked_count == 0
    assert report.history_generated_at == HISTORY_AT.replace(tzinfo=UTC)
    assert report.history_config_version == "paper-research-packet-quality-history-v1"
    assert report.history_status == "pass"
    assert report.history_source_report_count == 3
    assert report.history_latest_quality_status == "pass"
    assert report.reason_codes == ("operator_flow_passed",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_status_precedence_and_reason_codes_are_deterministic() -> None:
    watch_quality = _quality_report("watch")
    watch_history = _history_report(quality_report=watch_quality)
    assert (
        _build_report(
            quality_report=watch_quality,
            history_report=watch_history,
            generated_at=watch_history.generated_at + timedelta(minutes=5),
        ).flow_status
        == "watch"
    )
    assert (
        _build_report(
            history_report=_history_report("watch"),
        ).reason_codes
        == ("packet_quality_history_watch",)
    )

    blocked_quality = _quality_report("blocked")
    watch_history_for_blocked_quality = _history_report(
        "watch",
        quality_report=blocked_quality,
    )
    blocked_report = _build_report(
        packet_persisted=False,
        quality_report=blocked_quality,
        quality_persisted=False,
        history_report=watch_history_for_blocked_quality,
        generated_at=watch_history_for_blocked_quality.generated_at + timedelta(minutes=5),
    )

    assert blocked_report.flow_status == "blocked"
    assert blocked_report.reason_codes == (
        "packet_not_persisted",
        "packet_quality_blocked",
        "packet_quality_history_watch",
        "quality_not_persisted",
    )

    blocked_history = _history_report("blocked", quality_report=blocked_quality)
    assert (
        _build_report(
            quality_report=blocked_quality,
            history_report=blocked_history,
            generated_at=blocked_history.generated_at + timedelta(minutes=5),
        ).reason_codes
        == ("packet_quality_blocked", "packet_quality_history_blocked")
    )


def test_builder_rejects_non_exact_public_types_and_bad_flags() -> None:
    from polymarket_alpha_lab.paper_research_packet_operator_flow import (
        PaperResearchPacketOperatorFlowConfig,
        build_paper_research_packet_operator_flow_report,
    )

    class ConfigSubclass(PaperResearchPacketOperatorFlowConfig):
        pass

    class PacketReportSubclass(PaperResearchPacketReport):
        pass

    class QualityReportSubclass(PaperResearchPacketQualityReport):
        pass

    class HistoryReportSubclass(PaperResearchPacketQualityHistoryReport):
        pass

    packet = _packet_report()
    quality = _quality_report()
    history = _history_report(quality_report=quality)

    with pytest.raises(
        ValueError,
        match="config must be a PaperResearchPacketOperatorFlowConfig",
    ):
        build_paper_research_packet_operator_flow_report(
            packet_report=packet,
            packet_persisted=True,
            quality_report=quality,
            quality_persisted=True,
            quality_history_report=history,
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(
        ValueError,
        match="packet_report must be a PaperResearchPacketReport",
    ):
        _build_report(packet_report=PacketReportSubclass(**packet.__dict__))
    with pytest.raises(
        ValueError,
        match="quality_report must be a PaperResearchPacketQualityReport",
    ):
        _build_report(quality_report=QualityReportSubclass(**quality.__dict__))
    with pytest.raises(
        ValueError,
        match="quality_history_report must be a PaperResearchPacketQualityHistoryReport",
    ):
        _build_report(history_report=HistoryReportSubclass(**history.__dict__))

    bad_packet = _packet_report()
    object.__setattr__(bad_packet, "readonly", False)
    with pytest.raises(ValueError, match="packet report must be readonly"):
        _build_report(packet_report=bad_packet)

    bad_config = PaperResearchPacketOperatorFlowConfig()
    object.__setattr__(bad_config, "paper_only", False)
    with pytest.raises(ValueError, match="config must be paper_only"):
        build_paper_research_packet_operator_flow_report(
            packet_report=packet,
            packet_persisted=True,
            quality_report=quality,
            quality_persisted=True,
            quality_history_report=history,
            config=bad_config,
            generated_at=GENERATED_AT,
        )


def test_builder_rejects_bad_boundary_values_and_inconsistent_sources() -> None:
    bad_quality = replace(_quality_report(), source_config_version="other-packet-v1")
    with pytest.raises(
        ValueError,
        match="quality source_config_version must match packet config_version",
    ):
        _build_report(quality_report=bad_quality)

    quality = _quality_report()
    bad_history = replace(
        _history_report(quality_report=quality),
        latest_source_generated_at=quality.generated_at + timedelta(seconds=1),
    )
    with pytest.raises(
        ValueError,
        match="history latest_source_generated_at must match quality generated_at",
    ):
        _build_report(history_report=bad_history)

    report = _build_report()
    with pytest.raises(
        ValueError,
        match="history generated_at must not be after generated_at",
    ):
        replace(report, history_generated_at=GENERATED_AT + timedelta(seconds=1))

    with pytest.raises(ValueError, match="packet_persisted must be a bool"):
        _build_report(packet_persisted=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        _build_report(generated_at="2026-06-23")  # type: ignore[arg-type]


def test_direct_report_constructor_validates_consistency_reason_codes_and_flags() -> None:
    from polymarket_alpha_lab.paper_research_packet_operator_flow import (
        PaperResearchPacketOperatorFlowReport,
    )

    report = _build_report()

    with pytest.raises(ValueError, match="reason_codes must be deterministic"):
        replace(report, reason_codes=("z_reason", "a_reason"))
    with pytest.raises(ValueError, match="reason_codes must not be empty"):
        replace(report, reason_codes=())
    with pytest.raises(ValueError, match="flow_status must match reason_codes"):
        replace(report, flow_status="blocked")
    with pytest.raises(ValueError, match="operator flow report must be report_only"):
        replace(report, report_only=False)
    with pytest.raises(FrozenInstanceError):
        report.flow_status = "watch"  # type: ignore[misc]

    assert isinstance(report, PaperResearchPacketOperatorFlowReport)


def test_operator_flow_module_has_no_direct_storage_env_cli_or_network_imports() -> None:
    import polymarket_alpha_lab.paper_research_packet_operator_flow as module

    source = inspect.getsource(module)

    forbidden_tokens = (
        "psycopg",
        "supabase",
        "os.environ",
        "argparse",
        "PolymarketPublicClient",
        "requests",
        "httpx",
        "wallet",
        "private_key",
        "order",
        "trade",
    )
    for token in forbidden_tokens:
        assert token not in source
