from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.research_source_freshness_scheduler import (
    ResearchSourceFreshnessSchedulerConfig,
    ResearchSourceFreshnessSchedulerInput,
    build_research_source_freshness_schedule_report,
    research_source_freshness_schedule_payload,
)


def _input(
    source_ref: str,
    *,
    source_lag_hours: Decimal,
    revision_frequency_hours: Decimal,
    evidence_age_hours: Decimal,
    team_sla_hours: Decimal,
) -> ResearchSourceFreshnessSchedulerInput:
    return ResearchSourceFreshnessSchedulerInput(
        source_ref=source_ref,
        source_lag_hours=source_lag_hours,
        revision_frequency_hours=revision_frequency_hours,
        evidence_age_hours=evidence_age_hours,
        team_sla_hours=team_sla_hours,
    )


def test_build_report_assigns_pass_watch_and_block_refresh_priorities() -> None:
    report = build_research_source_freshness_schedule_report(
        (
            _input(
                "src-pass",
                source_lag_hours=Decimal("1"),
                revision_frequency_hours=Decimal("168"),
                evidence_age_hours=Decimal("2"),
                team_sla_hours=Decimal("72"),
            ),
            _input(
                "src-watch",
                source_lag_hours=Decimal("36"),
                revision_frequency_hours=Decimal("48"),
                evidence_age_hours=Decimal("30"),
                team_sla_hours=Decimal("24"),
            ),
            _input(
                "src-block",
                source_lag_hours=Decimal("144"),
                revision_frequency_hours=Decimal("6"),
                evidence_age_hours=Decimal("96"),
                team_sla_hours=Decimal("12"),
            ),
        ),
    )

    assert report.status == "block"
    assert report.input_count == Decimal("3")
    assert report.pass_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.block_count == Decimal("1")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.refresh_slot_ref for row in report.rows) == (
        "refresh-slot-000001",
        "refresh-slot-000002",
        "refresh-slot-000003",
    )
    assert tuple(row.priority_rank for row in report.rows) == (
        Decimal("1"),
        Decimal("2"),
        Decimal("3"),
    )
    assert report.rows[0].refresh_action == "refresh_first"
    assert "source_lag_over_sla" in report.rows[0].reason_codes
    assert "evidence_stale_against_sla" in report.rows[0].reason_codes


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("source_lag_hours", "1"),
        ("revision_frequency_hours", 24),
        ("evidence_age_hours", 1.5),
        ("team_sla_hours", None),
    ),
)
def test_input_rejects_non_decimal_driver_types(field_name: str, value: object) -> None:
    values = {
        "source_ref": "src-decimal",
        "source_lag_hours": Decimal("1"),
        "revision_frequency_hours": Decimal("24"),
        "evidence_age_hours": Decimal("1"),
        "team_sla_hours": Decimal("24"),
    }
    values[field_name] = value

    with pytest.raises(ValueError, match=f"{field_name} must be a Decimal"):
        ResearchSourceFreshnessSchedulerInput(**values)


@pytest.mark.parametrize(
    "unsafe_source_ref",
    (
        "candidate_123",
        "market_slug_abc",
        "question_will-this-resolve",
        "source_url_https_example",
        "dsn_main",
        "orders_table",
        "token_secret",
        "wallet_alpha",
        "buy_refresh_now",
        "sell_refresh_now",
        "recommendation_refresh",
    ),
)
def test_public_payload_rejects_leaky_source_references(unsafe_source_ref: str) -> None:
    with pytest.raises(ValueError, match="unsafe text"):
        _input(
            unsafe_source_ref,
            source_lag_hours=Decimal("1"),
            revision_frequency_hours=Decimal("24"),
            evidence_age_hours=Decimal("1"),
            team_sla_hours=Decimal("24"),
        )


def test_report_requires_hard_paper_report_readonly_flags() -> None:
    config = ResearchSourceFreshnessSchedulerConfig()
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True

    report = build_research_source_freshness_schedule_report(
        (
            _input(
                "src-safe",
                source_lag_hours=Decimal("1"),
                revision_frequency_hours=Decimal("24"),
                evidence_age_hours=Decimal("1"),
                team_sla_hours=Decimal("24"),
            ),
        ),
        config=config,
    )
    payload = research_source_freshness_schedule_payload(report)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    encoded_payload = json.dumps(payload, sort_keys=True)
    assert "src-safe" not in encoded_payload
    assert "source_ref" not in encoded_payload

    with pytest.raises(FrozenInstanceError):
        report.readonly = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_report_payload_and_digest_are_deterministic() -> None:
    rows = (
        _input(
            "src-b",
            source_lag_hours=Decimal("36"),
            revision_frequency_hours=Decimal("48"),
            evidence_age_hours=Decimal("30"),
            team_sla_hours=Decimal("24"),
        ),
        _input(
            "src-a",
            source_lag_hours=Decimal("36"),
            revision_frequency_hours=Decimal("48"),
            evidence_age_hours=Decimal("30"),
            team_sla_hours=Decimal("24"),
        ),
    )

    left = research_source_freshness_schedule_payload(
        build_research_source_freshness_schedule_report(rows),
    )
    right = research_source_freshness_schedule_payload(
        build_research_source_freshness_schedule_report(tuple(reversed(rows))),
    )

    assert left == right
    assert len(left["derived_validation_digest"]) == 64
    assert json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)
    assert tuple(row["refresh_slot_ref"] for row in left["rows"]) == (
        "refresh-slot-000001",
        "refresh-slot-000002",
    )


def test_module_is_pure_report_only_without_io_persistence_or_trading_imports() -> None:
    import polymarket_alpha_lab.research_source_freshness_scheduler as scheduler

    with open(scheduler.__file__, encoding="utf-8") as source_file:
        module_source = source_file.read()

    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "subprocess",
        "open(",
        "Path(",
        "Order",
        "Trade",
    )
    for term in forbidden_terms:
        assert term not in module_source
