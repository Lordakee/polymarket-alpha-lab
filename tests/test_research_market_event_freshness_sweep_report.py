from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_event_freshness_sweep_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config():
    freshness_module = module()
    return freshness_module.ResearchMarketEventFreshnessSweepConfig(
        config_version="research-event-freshness-sweep-test-v0",
        information_refresh_watch_after_seconds=d("1800.000000"),
        information_refresh_block_after_seconds=d("7200.000000"),
        evidence_watch_after_seconds=d("3600.000000"),
        evidence_block_after_seconds=d("14400.000000"),
        settlement_watch_within_seconds=d("86400.000000"),
        settlement_block_within_seconds=d("1800.000000"),
    )


def item(
    queue_item_id: str,
    *,
    last_information_refresh_at: datetime | None = GENERATED_AT
    - timedelta(minutes=10),
    latest_evidence_observed_at: datetime | None = GENERATED_AT
    - timedelta(minutes=20),
    settlement_at: datetime | None = GENERATED_AT + timedelta(days=2),
    domain_owner_present: bool = True,
    manual_review_requested: bool = False,
    review_completed_at: datetime | None = None,
):
    freshness_module = module()
    return freshness_module.ResearchMarketEventFreshnessSweepInput(
        queue_item_id=queue_item_id,
        last_information_refresh_at=last_information_refresh_at,
        latest_evidence_observed_at=latest_evidence_observed_at,
        settlement_at=settlement_at,
        domain_owner_present=domain_owner_present,
        manual_review_requested=manual_review_requested,
        review_completed_at=review_completed_at,
    )


def build_report(*items):
    freshness_module = module()
    return freshness_module.build_research_market_event_freshness_sweep_report(
        items,
        config=config(),
        generated_at=GENERATED_AT,
    )


def test_classifies_refresh_evidence_settlement_owner_and_review_needs() -> None:
    report = build_report(
        item("event-pass"),
        item(
            "event-watch-refresh",
            last_information_refresh_at=GENERATED_AT - timedelta(seconds=5400),
            review_completed_at=GENERATED_AT - timedelta(minutes=5),
        ),
        item(
            "event-watch-settlement",
            settlement_at=GENERATED_AT + timedelta(seconds=7200),
        ),
        item(
            "event-block-evidence-owner",
            latest_evidence_observed_at=GENERATED_AT - timedelta(seconds=18000),
            domain_owner_present=False,
        ),
        item(
            "event-block-review",
            last_information_refresh_at=GENERATED_AT - timedelta(seconds=10800),
            manual_review_requested=True,
        ),
    )

    assert report.sweep_status == "block"
    assert report.queue_item_count == d("5.000000")
    assert report.block_count == d("2.000000")
    assert report.watch_count == d("2.000000")
    assert report.pass_count == d("1.000000")
    assert report.information_refresh_needed_count == d("2.000000")
    assert report.stale_evidence_count == d("1.000000")
    assert report.settlement_window_count == d("1.000000")
    assert report.missing_domain_owner_count == d("1.000000")
    assert report.review_required_count == d("4.000000")
    assert report.pending_review_count == d("1.000000")
    assert len(report.derived_validation_digest) == 64
    assert report.reason_codes == (
        "freshness_sweep_block",
        "information_refresh_needed_present",
        "stale_evidence_present",
        "settlement_window_present",
        "domain_owner_missing_present",
        "review_required_present",
        "pending_review_present",
    )
    assert tuple(row.queue_item_id for row in report.rows) == (
        "event-block-evidence-owner",
        "event-block-review",
        "event-watch-refresh",
        "event-watch-settlement",
        "event-pass",
    )

    evidence_owner = report.rows[0]
    stale_review = report.rows[1]
    refresh = report.rows[2]
    settlement = report.rows[3]
    passing = report.rows[4]

    assert evidence_owner.sweep_status == "block"
    assert evidence_owner.reason_codes == (
        "evidence_block_stale",
        "domain_owner_missing",
        "review_required",
    )
    assert evidence_owner.evidence_age_seconds == d("18000.000000")
    assert stale_review.reason_codes == (
        "information_refresh_block_stale",
        "manual_review_pending",
        "review_required",
    )
    assert refresh.sweep_status == "watch"
    assert refresh.reason_codes == (
        "information_refresh_watch_stale",
        "review_required",
    )
    assert settlement.reason_codes == ("settlement_watch_window", "review_required")
    assert settlement.settlement_seconds_remaining == d("7200.000000")
    assert passing.sweep_status == "pass"
    assert passing.reason_codes == ("freshness_sweep_pass",)
    assert passing.review_required is False
    assert passing.paper_only is True
    assert passing.report_only is True
    assert passing.readonly is True


def test_empty_queue_blocks_without_division_or_float_leakage() -> None:
    report = build_report()

    assert report.sweep_status == "block"
    assert report.queue_item_count == d("0.000000")
    assert report.review_required_count == d("0.000000")
    assert report.reason_codes == ("no_queue_events_to_sweep",)
    assert report.rows == ()


def test_threshold_boundaries_are_deterministic() -> None:
    report = build_report(
        item(
            "event-info-watch-boundary",
            last_information_refresh_at=GENERATED_AT - timedelta(seconds=1800),
        ),
        item(
            "event-info-block-boundary",
            last_information_refresh_at=GENERATED_AT - timedelta(seconds=7200),
        ),
        item(
            "event-evidence-watch-boundary",
            latest_evidence_observed_at=GENERATED_AT - timedelta(seconds=3600),
        ),
        item(
            "event-evidence-block-boundary",
            latest_evidence_observed_at=GENERATED_AT - timedelta(seconds=14400),
        ),
        item(
            "event-settlement-watch-boundary",
            settlement_at=GENERATED_AT + timedelta(seconds=86400),
        ),
        item(
            "event-settlement-block-boundary",
            settlement_at=GENERATED_AT + timedelta(seconds=1800),
        ),
    )

    rows = {row.queue_item_id: row for row in report.rows}
    assert rows["event-info-watch-boundary"].sweep_status == "watch"
    assert rows["event-info-block-boundary"].sweep_status == "block"
    assert rows["event-evidence-watch-boundary"].sweep_status == "watch"
    assert rows["event-evidence-block-boundary"].sweep_status == "block"
    assert rows["event-settlement-watch-boundary"].sweep_status == "watch"
    assert rows["event-settlement-block-boundary"].sweep_status == "block"


def test_dataclasses_are_frozen_and_public_numeric_fields_use_decimal() -> None:
    freshness_module = module()

    assert freshness_module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_EVENT_FRESHNESS_SWEEP_CONFIG_VERSION",
        "ResearchMarketEventFreshnessSweepConfig",
        "ResearchMarketEventFreshnessSweepInput",
        "ResearchMarketEventFreshnessSweepReport",
        "ResearchMarketEventFreshnessSweepRow",
        "build_research_market_event_freshness_sweep_report",
        "research_market_event_freshness_sweep_report_payload",
    )
    for exported_name in freshness_module.__all__:
        value = getattr(freshness_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(item("event-pass"))

    for field in fields(report):
        if field.name.endswith("_count"):
            assert type(getattr(report, field.name)) is Decimal
    for row in report.rows:
        for field in fields(row):
            if field.name.endswith("_seconds"):
                value = getattr(row, field.name)
                assert value is None or type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].sweep_status = "block"  # type: ignore[misc]


def test_report_exposes_stable_derived_validation_digest() -> None:
    freshness_module = module()
    report = build_report(item("event-pass"))
    rebuilt = build_report(item("event-pass"))

    assert report.derived_validation_digest == rebuilt.derived_validation_digest
    assert report.derived_validation_digest != "0" * 64

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        freshness_module.ResearchMarketEventFreshnessSweepReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            queue_item_count=report.queue_item_count,
            block_count=report.block_count,
            watch_count=report.watch_count,
            pass_count=report.pass_count,
            information_refresh_needed_count=report.information_refresh_needed_count,
            stale_evidence_count=report.stale_evidence_count,
            settlement_window_count=report.settlement_window_count,
            missing_domain_owner_count=report.missing_domain_owner_count,
            review_required_count=report.review_required_count,
            pending_review_count=report.pending_review_count,
            sweep_status=report.sweep_status,
            reason_codes=report.reason_codes,
            rows=report.rows,
            derived_validation_digest="0" * 64,
        )


def test_utc_aware_datetimes_are_required_and_future_inputs_are_rejected() -> None:
    freshness_module = module()

    report = freshness_module.build_research_market_event_freshness_sweep_report(
        (
            item(
                "event-pass",
                last_information_refresh_at=datetime(2026, 7, 8, 11, 50, tzinfo=timezone.utc),
                latest_evidence_observed_at=datetime(2026, 7, 8, 11, 40, tzinfo=timezone.utc),
                settlement_at=datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc),
            ),
        ),
        config=config(),
        generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].last_information_refresh_at == datetime(
        2026,
        7,
        8,
        11,
        50,
        tzinfo=UTC,
    )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        freshness_module.build_research_market_event_freshness_sweep_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="last_information_refresh_at must be timezone-aware"):
        item(
            "event-naive",
            last_information_refresh_at=datetime(2026, 7, 8, 11, 0),
        )
    with pytest.raises(ValueError, match="settlement_at must not be after max horizon"):
        build_report(
            item(
                "event-far-settlement",
                settlement_at=GENERATED_AT + timedelta(days=370),
            ),
        )
    with pytest.raises(ValueError, match="latest_evidence_observed_at must not be after generated_at"):
        build_report(
            item(
                "event-future-evidence",
                latest_evidence_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )


def test_rejects_non_decimal_values_duplicate_ids_and_false_hard_flags() -> None:
    freshness_module = module()

    with pytest.raises(ValueError, match="information_refresh_watch_after_seconds must be a Decimal"):
        freshness_module.ResearchMarketEventFreshnessSweepConfig(
            information_refresh_watch_after_seconds=1800,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="domain_owner_present must be a bool"):
        item("event-bad-owner", domain_owner_present=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only must be True"):
        freshness_module.ResearchMarketEventFreshnessSweepConfig(paper_only=False)
    with pytest.raises(ValueError, match="duplicate queue_item_id"):
        build_report(item("event-dup"), item("event-dup"))


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "raw-candidate-123",
        "event-market-123",
        "event-source-123",
        "https://example.invalid/item",
        "event-url-123",
        "event-dsn-123",
        "event-table-123",
        "event-token-123",
        "event-text-123",
    ),
)
def test_rejects_unsafe_public_text_surfaces(unsafe_value: str) -> None:
    freshness_module = module()

    with pytest.raises(ValueError, match="unsafe public surface"):
        freshness_module.ResearchMarketEventFreshnessSweepInput(
            queue_item_id=unsafe_value,
            last_information_refresh_at=GENERATED_AT,
            latest_evidence_observed_at=GENERATED_AT,
            settlement_at=GENERATED_AT + timedelta(days=2),
            domain_owner_present=True,
        )


def test_json_ready_payload_has_no_floats_or_sensitive_raw_surfaces() -> None:
    freshness_module = module()
    report = build_report(item("event-pass"))

    payload = freshness_module.research_market_event_freshness_sweep_report_payload(report)

    json.dumps(payload, sort_keys=True)
    assert payload["queue_item_count"] == "1.000000"
    assert payload["rows"][0]["information_refresh_age_seconds"] == "600.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert_no_float(payload)
    assert_no_sensitive_public_surface(payload)


def test_public_payload_rejects_tampered_unsafe_surface_values() -> None:
    freshness_module = module()
    report = build_report(item("event-pass"))

    object.__setattr__(report.rows[0], "queue_item_id", "event-token")

    with pytest.raises(ValueError, match="unsafe public surface"):
        freshness_module.research_market_event_freshness_sweep_report_payload(report)


def test_module_omits_runtime_write_and_financial_action_surfaces() -> None:
    source = module().__loader__.get_source(module().__name__)
    assert source is not None
    lowered = source.lower()

    for forbidden in (
        "requests.",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "mysql",
        "sqlalchemy",
        ".execute(",
        ".commit(",
        "recommendation",
        "trading advice",
        "place_order",
        "cancel_order",
    ):
        assert forbidden not in lowered


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def assert_no_sensitive_public_surface(value: Any) -> None:
    fragments = (
        "raw",
        "candidate",
        "market",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "text",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = str(key).lower()
            assert not any(fragment in lowered_key for fragment in fragments)
            assert_no_sensitive_public_surface(item)
    if isinstance(value, list):
        for item in value:
            assert_no_sensitive_public_surface(item)
    if isinstance(value, str):
        lowered_value = value.lower()
        assert not any(fragment in lowered_value for fragment in fragments)
