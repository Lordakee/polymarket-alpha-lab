from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_research_handoff import (
    TeamResearchHandoffConfig,
    TeamResearchHandoffItem,
    build_team_research_handoff_summary,
    format_team_research_handoff_summary,
    team_research_handoff_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 10, 30, tzinfo=UTC)
UPDATED_AT = datetime(2026, 7, 2, 9, 45, tzinfo=UTC)


def item(
    *,
    source_team_id: str = "macro_rates",
    target_team_id: str = "crypto_btc",
    handoff_status: str = "watch",
    updated_at: datetime = UPDATED_AT,
    missing_evidence: tuple[str, ...] = ("fresh_clob_depth_snapshot",),
    stale_sources: tuple[str, ...] = ("gamma_market_metadata",),
    blockers: tuple[str, ...] = (),
    next_research_actions: tuple[str, ...] = ("refresh_public_market_depth",),
    public_notes: str = "Need fresh source confirmation before specialist synthesis.",
    sensitive_fields: dict[str, object] | None = None,
    reason_codes: tuple[str, ...] = ("handoff_watch_missing_evidence",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> TeamResearchHandoffItem:
    return TeamResearchHandoffItem(
        source_team_id=source_team_id,
        target_team_id=target_team_id,
        handoff_status=handoff_status,
        updated_at=updated_at,
        missing_evidence=missing_evidence,
        stale_sources=stale_sources,
        blockers=blockers,
        next_research_actions=next_research_actions,
        public_notes=public_notes,
        sensitive_fields=sensitive_fields
        if sensitive_fields is not None
        else {
            "operator_email": "analyst@example.com",
            "private_note": "do not share",
        },
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_builds_immutable_handoff_summary_with_research_only_next_actions() -> None:
    summary = build_team_research_handoff_summary(
        (
            item(
                source_team_id="macro_rates",
                target_team_id="crypto_btc",
                handoff_status="ready",
                missing_evidence=(),
                stale_sources=(),
                reason_codes=("handoff_ready",),
            ),
            item(
                source_team_id="sports_soccer",
                target_team_id="risk_review",
                handoff_status="blocked",
                blockers=("lineup_source_unavailable",),
                next_research_actions=("collect_public_lineup_report",),
                reason_codes=("handoff_blocked_blockers_present",),
            ),
            item(
                source_team_id="politics",
                target_team_id="calibration",
                handoff_status="watch",
            ),
        ),
        config=TeamResearchHandoffConfig(),
        generated_at=GENERATED_AT,
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.handoff_status == "blocked"
    assert summary.handoff_count == Decimal("3")
    assert summary.ready_count == Decimal("1")
    assert summary.watch_count == Decimal("1")
    assert summary.blocked_count == Decimal("1")
    assert summary.missing_evidence_count == Decimal("2")
    assert summary.stale_source_count == Decimal("2")
    assert summary.blocker_count == Decimal("1")
    for count_value in (
        summary.handoff_count,
        summary.ready_count,
        summary.watch_count,
        summary.blocked_count,
        summary.missing_evidence_count,
        summary.stale_source_count,
        summary.blocker_count,
    ):
        assert type(count_value) is Decimal
    assert summary.recommended_next_step == "resolve_blocked_research_handoffs"
    assert summary.reason_codes == ("team_research_handoff_blocked",)
    assert summary.derived_validation.startswith("sha256:")
    assert all(row.derived_validation.startswith("sha256:") for row in summary.items)
    assert tuple((row.source_team_id, row.target_team_id) for row in summary.items) == (
        ("macro_rates", "crypto_btc"),
        ("politics", "calibration"),
        ("sports_soccer", "risk_review"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    with pytest.raises(FrozenInstanceError):
        summary.handoff_status = "ready"
    with pytest.raises(ValueError, match="derived_validation"):
        replace(summary, generated_at=GENERATED_AT + timedelta(minutes=1))
    with pytest.raises(ValueError, match="derived_validation"):
        replace(summary.items[0], public_notes="Changed after validation.")


def test_payload_redacts_sensitive_fields_and_blocks_trade_instructions() -> None:
    summary = build_team_research_handoff_summary(
        (
            item(
                source_team_id="macro_rates",
                target_team_id="crypto_btc",
                sensitive_fields={
                    "dsn": "postgresql://user:secret@localhost/db",
                    "wallet": "0xdeadbeef",
                    "private_key": "secret-key",
                    "nested": {"operator_token": "token-value"},
                },
            ),
        ),
        config=TeamResearchHandoffConfig(),
        generated_at=GENERATED_AT,
    )

    payload = team_research_handoff_payload(summary)
    rendered_payload = repr(payload)

    assert "<redacted>" in rendered_payload
    assert "postgresql://user:secret@localhost/db" not in rendered_payload
    assert "0xdeadbeef" not in rendered_payload
    assert "secret-key" not in rendered_payload
    assert "token-value" not in rendered_payload
    assert "wallet" not in rendered_payload
    assert "private_key" not in rendered_payload
    assert "operator_token" not in rendered_payload
    assert payload["items"][0]["sensitive_fields"] == {
        "redacted_field_1": "<redacted>",
        "redacted_field_2": "<redacted>",
        "redacted_field_3": "<redacted>",
        "redacted_field_4": {"redacted_field_1": "<redacted>"},
    }
    assert payload["derived_validation"] == summary.derived_validation
    assert payload["items"][0]["derived_validation"] == summary.items[0].derived_validation
    assert payload["handoff_count"] == "1"
    assert payload["watch_count"] == "1"
    serialized_summary = repr(summary).lower()
    assert "postgresql://user:secret@localhost/db" not in serialized_summary
    assert "0xdeadbeef" not in serialized_summary
    assert "secret-key" not in serialized_summary
    assert "token-value" not in serialized_summary
    assert "wallet" not in serialized_summary
    assert "private_key" not in serialized_summary
    assert "operator_token" not in serialized_summary

    with pytest.raises(ValueError, match="trade or investment instruction"):
        item(next_research_actions=("place order after source refresh",))

    redacted_public_payload = team_research_handoff_payload(
        item(public_notes="database_url=postgresql://user:secret@localhost/db"),
    )
    assert redacted_public_payload["public_notes"] == "<redacted>"
    assert "postgresql://" not in repr(redacted_public_payload)
    assert "secret" not in repr(redacted_public_payload)


def test_rejects_public_payloads_without_validation_or_with_unsafe_surface() -> None:
    with pytest.raises(ValueError, match="derived_validation"):
        team_research_handoff_payload(
            {
                "handoff_status": "watch",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )

    summary = build_team_research_handoff_summary(
        (item(),),
        config=TeamResearchHandoffConfig(),
        generated_at=GENERATED_AT,
    )
    payload = team_research_handoff_payload(summary)

    tampered_payload = dict(payload)
    tampered_payload["handoff_count"] = "99"
    with pytest.raises(ValueError, match="derived_validation"):
        team_research_handoff_payload(tampered_payload)

    unsafe_payload = dict(payload)
    unsafe_payload["wallet"] = "<redacted>"
    with pytest.raises(ValueError, match="unsafe"):
        team_research_handoff_payload(unsafe_payload)

    int_payload = dict(payload)
    int_payload["handoff_count"] = 1
    with pytest.raises(ValueError, match="Decimal-derived"):
        team_research_handoff_payload(int_payload)


def test_formatting_is_deterministic_and_uses_utc_timestamps() -> None:
    offset_time = datetime(2026, 7, 2, 5, 45, tzinfo=timezone(timedelta(hours=-4)))
    summary = build_team_research_handoff_summary(
        (
            item(
                source_team_id="politics",
                target_team_id="calibration",
                updated_at=offset_time,
                missing_evidence=("pollster_methodology_update",),
                stale_sources=("polling_average_snapshot",),
                next_research_actions=("refresh_public_polling_methodology",),
                public_notes="Poll methodology update pending.",
            ),
            item(
                source_team_id="crypto_btc",
                target_team_id="macro_rates",
                handoff_status="ready",
                missing_evidence=(),
                stale_sources=(),
                next_research_actions=("review_public_cross_asset_context",),
                public_notes="Public context ready for macro review.",
                reason_codes=("handoff_ready",),
            ),
        ),
        config=TeamResearchHandoffConfig(),
        generated_at=datetime(2026, 7, 2, 6, 30, tzinfo=timezone(timedelta(hours=-4))),
    )

    rendered = format_team_research_handoff_summary(summary)

    assert rendered == (
        "team-research-handoff: generated_at=2026-07-02T10:30:00+00:00 "
        "status=watch handoff_count=2 ready=1 watch=1 blocked=0 "
        "missing_evidence=1 stale_sources=1 blockers=0 "
        "next_step=review_watch_research_handoffs "
        "items=crypto_btc>macro_rates:ready:2026-07-02T09:45:00+00:00:"
        "missing=none:stale=none:blockers=none:"
        "actions=review_public_cross_asset_context:reasons=handoff_ready:"
        f"validation={summary.items[0].derived_validation}|"
        "politics>calibration:watch:2026-07-02T09:45:00+00:00:"
        "missing=pollster_methodology_update:stale=polling_average_snapshot:"
        "blockers=none:actions=refresh_public_polling_methodology:"
        "reasons=handoff_watch_missing_evidence:"
        f"validation={summary.items[1].derived_validation} "
        "reason_codes=team_research_handoff_watch "
        f"derived_validation={summary.derived_validation} "
        "paper_only=True report_only=True readonly=True\n"
    )


def test_rejects_naive_datetimes_false_flags_and_bad_status_consistency() -> None:
    with pytest.raises(ValueError, match="updated_at must be timezone-aware"):
        item(updated_at=datetime(2026, 7, 2, 9, 45))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_team_research_handoff_summary(
            (item(),),
            config=TeamResearchHandoffConfig(),
            generated_at=datetime(2026, 7, 2, 10, 30),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(item(), paper_only=False)
    with pytest.raises(ValueError, match="blockers require blocked handoff_status"):
        item(blockers=("source_access_blocked",), handoff_status="watch")
    with pytest.raises(ValueError, match="blocked handoffs require blockers"):
        item(handoff_status="blocked", blockers=())
