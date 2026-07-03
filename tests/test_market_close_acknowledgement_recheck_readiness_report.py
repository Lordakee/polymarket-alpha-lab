from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


MODULE = "polymarket_alpha_lab.market_close_acknowledgement_recheck_readiness_report"
GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE)


def d(value: str) -> Decimal:
    return Decimal(value)


def close_ack(
    condition_id: str,
    *,
    close_time: datetime | None = datetime(2026, 7, 2, 11, 0, tzinfo=UTC),
    close_evidence_observed_at: datetime | None = datetime(2026, 7, 2, 11, 5, tzinfo=UTC),
    acknowledgement_observed_at: datetime | None = datetime(2026, 7, 2, 11, 7, tzinfo=UTC),
    rechecked_at: datetime | None = datetime(2026, 7, 2, 11, 45, tzinfo=UTC),
    outcome_source: str = "acknowledgement",
):
    module = api()
    return module.MarketCloseAcknowledgementRecheckInput(
        condition_id=condition_id,
        close_time=close_time,
        close_evidence_observed_at=close_evidence_observed_at,
        acknowledgement_observed_at=acknowledgement_observed_at,
        rechecked_at=rechecked_at,
        outcome_source=outcome_source,
    )


def report(*rows):
    module = api()
    return module.build_market_close_acknowledgement_recheck_readiness_report(
        rows,
        config=module.MarketCloseAcknowledgementRecheckReadinessConfig(
            max_recheck_age_seconds=d("3600"),
            max_close_evidence_age_seconds=d("7200"),
        ),
        generated_at=GENERATED_AT,
    )


def test_report_rolls_up_ready_missing_stale_and_non_acknowledged_sources() -> None:
    readiness = report(
        close_ack("missing-close", close_time=None),
        close_ack(
            "stale-close",
            close_time=GENERATED_AT - timedelta(hours=3),
            close_evidence_observed_at=GENERATED_AT - timedelta(hours=3),
        ),
        close_ack(
            "missing-ack",
            acknowledgement_observed_at=None,
            outcome_source="resolver",
        ),
        close_ack(
            "stale-recheck",
            rechecked_at=GENERATED_AT - timedelta(hours=2),
        ),
        close_ack("ready-market"),
    )

    assert is_dataclass(readiness)
    assert readiness.generated_at == GENERATED_AT
    assert readiness.config_version == "market-close-ack-recheck-readiness-v0"
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True
    assert readiness.market_count == d("5")
    assert readiness.ready_count == d("1")
    assert readiness.watch_count == d("2")
    assert readiness.blocked_count == d("2")
    assert readiness.readiness_ratio == d("0.200000")
    assert readiness.status == "blocked"
    assert readiness.reason_codes == (
        "missing_close_evidence",
        "missing_acknowledgement",
        "stale_recheck",
        "stale_close_evidence",
        "outcome_source_not_acknowledgement",
    )

    assert tuple(row.condition_id for row in readiness.rows) == (
        "missing-close",
        "missing-ack",
        "stale-recheck",
        "stale-close",
        "ready-market",
    )
    assert tuple(row.readiness_status for row in readiness.rows) == (
        "blocked",
        "blocked",
        "watch",
        "watch",
        "ready",
    )
    missing_close = readiness.rows[0]
    assert missing_close.close_time_known is False
    assert missing_close.close_age_seconds is None
    assert missing_close.reason_codes == ("missing_close_evidence",)

    missing_ack = readiness.rows[1]
    assert missing_ack.acknowledgement_present is False
    assert missing_ack.outcome_source_acknowledged is False
    assert missing_ack.reason_codes == (
        "missing_acknowledgement",
        "outcome_source_not_acknowledgement",
    )

    stale_recheck = readiness.rows[2]
    assert stale_recheck.recheck_age_seconds == d("7200.000000")
    assert stale_recheck.recheck_fresh is False
    assert stale_recheck.reason_codes == ("stale_recheck",)

    stale_close = readiness.rows[3]
    assert stale_close.close_age_seconds == d("10800.000000")
    assert stale_close.close_evidence_fresh is False
    assert stale_close.reason_codes == ("stale_close_evidence",)

    ready = readiness.rows[4]
    assert ready.readiness_status == "ready"
    assert ready.reason_codes == ("market_close_ack_recheck_ready",)


def test_payload_uses_decimal_strings_iso_datetimes_and_no_float_surfaces() -> None:
    module = api()
    payload = module.market_close_acknowledgement_recheck_readiness_payload(
        report(close_ack("ready-market")),
    )

    payload_text = repr(payload).lower()
    assert "wallet" not in payload_text
    assert "order" not in payload_text
    assert "cancel" not in payload_text
    assert "sign" not in payload_text
    assert "advice" not in payload_text
    assert "recommend" not in payload_text
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "1"
    assert payload["readiness_ratio"] == "1.000000"
    assert payload["rows"][0]["close_time"] == "2026-07-02T11:00:00+00:00"
    assert payload["rows"][0]["recheck_age_seconds"] == "900.000000"
    assert not any(isinstance(value, float) for value in _walk_values(payload))


def test_empty_inputs_are_ready_with_empty_reason_code() -> None:
    readiness = report()

    assert readiness.market_count == d("0")
    assert readiness.ready_count == d("0")
    assert readiness.watch_count == d("0")
    assert readiness.blocked_count == d("0")
    assert readiness.readiness_ratio == d("0.000000")
    assert readiness.status == "ready"
    assert readiness.reason_codes == ("empty_market_close_ack_recheck_inputs",)
    assert readiness.rows == ()


def test_inputs_are_frozen_decimal_only_and_timezone_deterministic() -> None:
    module = api()
    eastern = timezone(timedelta(hours=-4))
    row = close_ack(
        "tz-market",
        close_time=datetime(2026, 7, 2, 7, 0, tzinfo=eastern),
        acknowledgement_observed_at=datetime(2026, 7, 2, 7, 7, tzinfo=eastern),
    )

    assert row.close_time == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert row.acknowledgement_observed_at == datetime(2026, 7, 2, 11, 7, tzinfo=UTC)
    with pytest.raises(FrozenInstanceError):
        row.condition_id = "other"  # type: ignore[misc]

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_market_close_acknowledgement_recheck_readiness_report(
            (close_ack("ready-market"),),
            config=module.MarketCloseAcknowledgementRecheckReadinessConfig(
                max_recheck_age_seconds=d("3600"),
                max_close_evidence_age_seconds=d("7200"),
            ),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )

    with pytest.raises(ValueError, match="max_recheck_age_seconds must be a Decimal"):
        module.MarketCloseAcknowledgementRecheckReadinessConfig(
            max_recheck_age_seconds=3600.0,
            max_close_evidence_age_seconds=d("7200"),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)


def test_readiness_row_rejects_acknowledgement_age_without_observation() -> None:
    row = report(close_ack("ready-market")).rows[0]

    with pytest.raises(ValueError, match="acknowledgement_age_seconds"):
        replace(
            row,
            acknowledgement_observed_at=None,
            acknowledgement_present=False,
            acknowledgement_age_seconds=d("100.000000"),
        )


def test_module_surface_is_pure_in_memory_report_only() -> None:
    module = api()
    public_names = {
        name
        for name in dir(module)
        if not name.startswith("_") and name not in {"annotations"}
    }
    forbidden_fragments = (
        "auth",
        "wallet",
        "broker",
        "submit",
        "cancel",
        "sign",
        "trade",
        "order",
        "database",
        "db",
        "network",
        "advice",
        "recommend",
    )

    assert not any(
        fragment in name.lower()
        for name in public_names
        for fragment in forbidden_fragments
    )
    assert module.MarketCloseAcknowledgementRecheckReadinessConfig().paper_only is True
    assert module.MarketCloseAcknowledgementRecheckReadinessConfig().report_only is True
    assert module.MarketCloseAcknowledgementRecheckReadinessConfig().readonly is True


def _walk_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_values(item)
    else:
        yield value
