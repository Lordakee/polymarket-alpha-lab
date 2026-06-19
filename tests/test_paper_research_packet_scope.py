from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketConfig,
    PaperResearchPacketInputRow,
    build_paper_research_packet_report,
)


GENERATED_AT = datetime(2026, 6, 18, 15, 30, tzinfo=UTC)


def _config(**overrides) -> PaperResearchPacketConfig:
    values = {
        "config_version": "paper-research-packet-v0",
        "max_packet_rows": 5,
        "min_score": Decimal("0.200000"),
    }
    values.update(overrides)
    return PaperResearchPacketConfig(**values)


def _row(**overrides) -> PaperResearchPacketInputRow:
    values = {
        "market_slug": "readonly-row",
        "question": "Will readonly row resolve yes?",
        "side": "yes",
        "action": "recommend",
        "queue_status": "ready",
        "recommendation_score": Decimal("0.700000"),
        "net_edge": Decimal("0.050000"),
        "allocated_notional": Decimal("10.000000"),
        "requested_notional": Decimal("12.000000"),
        "reason_codes": ("readonly_research",),
    }
    values.update(overrides)
    return PaperResearchPacketInputRow(**values)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_research_packet_config_rejects_disabled_hard_safety_flags(flag_name):
    with pytest.raises(ValueError, match=flag_name):
        _config(**{flag_name: False})


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_research_packet_input_rejects_disabled_hard_safety_flags(flag_name):
    with pytest.raises(ValueError, match=flag_name):
        _row(**{flag_name: False})


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_research_packet_report_rejects_disabled_hard_safety_flags(flag_name):
    report = build_paper_research_packet_report(
        (_row(),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match=flag_name):
        replace(report, **{flag_name: False})
    with pytest.raises(ValueError, match=flag_name):
        replace(report.packet_rows[0], **{flag_name: False})


def test_research_packet_rejects_unsafe_supplied_input_rows():
    row = _row()
    object.__setattr__(row, "paper_only", False)

    with pytest.raises(ValueError, match="input rows must be paper_only"):
        build_paper_research_packet_report(
            (row,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_research_packet_rejects_unsafe_config_and_non_rows():
    config = _config()
    object.__setattr__(config, "readonly", False)

    with pytest.raises(ValueError, match="config must be readonly"):
        build_paper_research_packet_report(
            (_row(),),
            config=config,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="rows must contain PaperResearchPacketInputRow"):
        build_paper_research_packet_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_research_packet_has_no_live_execution_or_cli_surface():
    import polymarket_alpha_lab.paper_research_packet as packet

    public_names = set(packet.__all__)
    forbidden_terms = (
        "client",
        "auth",
        "wallet",
        "order",
        "trade",
        "network",
        "execute",
        "cli",
        "main",
    )

    assert all(
        term not in name.lower()
        for name in public_names
        for term in forbidden_terms
    )
    assert not hasattr(packet, "main")
