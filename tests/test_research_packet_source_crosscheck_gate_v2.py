from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return import_module(
        "polymarket_alpha_lab.research_packet_source_crosscheck_gate_v2",
    )


def _config(**overrides: object) -> Any:
    api = _api()
    values = {
        "config_version": "source-crosscheck-gate-v2-test",
        "max_evidence_age_seconds": d("3600"),
        "min_independent_source_family_count": d("3"),
        "min_fresh_evidence_count": d("3"),
    }
    values.update(overrides)
    return api.ResearchPacketSourceCrosscheckGateV2Config(**values)


def _evidence(
    evidence_id: str,
    *,
    event_id: str = "event-alpha",
    source_family: str = "source-family-a",
    source_kind: str = "independent",
    evidence_outcome: str = "yes",
    observed_at: datetime | None = None,
    official_confirmation: bool = False,
    contradiction_reviewed: bool = False,
    resolution_source_traceable: bool = False,
) -> Any:
    api = _api()
    return api.ResearchPacketSourceCrosscheckEvidence(
        event_id=event_id,
        evidence_id=evidence_id,
        source_family=source_family,
        source_kind=source_kind,
        evidence_outcome=evidence_outcome,
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=60),
        official_confirmation=official_confirmation,
        contradiction_reviewed=contradiction_reviewed,
        resolution_source_traceable=resolution_source_traceable,
    )


def _report(rows: tuple[Any, ...] | list[Any], **overrides: object) -> Any:
    api = _api()
    return api.build_research_packet_source_crosscheck_gate_v2(
        rows,
        config=_config(**overrides),
        generated_at=GENERATED_AT,
    )


def _bypassed_row(row: object, **overrides: object) -> object:
    malformed = object.__new__(type(row))
    for field in fields(row):
        object.__setattr__(malformed, field.name, getattr(row, field.name))
    for key, value in overrides.items():
        object.__setattr__(malformed, key, value)
    return malformed


def _with_recomputed_report_digest(payload: dict[str, Any]) -> dict[str, Any]:
    without_digest = dict(payload)
    without_digest.pop("derived_validation_digest")
    payload["derived_validation_digest"] = sha256(
        json.dumps(
            without_digest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    return payload


def _assert_json_ready(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            assert type(key) is str
            _assert_json_ready(nested)
        return
    if isinstance(value, list):
        for nested in value:
            _assert_json_ready(nested)
        return
    assert value is None or type(value) in (str, bool)


def _walk_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        strings: list[str] = []
        for key, nested in value.items():
            strings.append(key)
            strings.extend(_walk_strings(nested))
        return tuple(strings)
    if isinstance(value, list):
        strings = []
        for nested in value:
            strings.extend(_walk_strings(nested))
        return tuple(strings)
    if type(value) is str:
        return (value,)
    return ()


def test_passes_when_evidence_has_required_independent_source_crosschecks() -> None:
    api = _api()
    report = _report(
        (
            _evidence(
                "official-confirmation",
                source_family="official-source-family",
                source_kind="official",
                official_confirmation=True,
                observed_at=datetime(
                    2026,
                    7,
                    6,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
            _evidence(
                "contradiction-review",
                source_family="review-source-family",
                source_kind="review",
                contradiction_reviewed=True,
                observed_at=GENERATED_AT - timedelta(seconds=120),
            ),
            _evidence(
                "resolution-trace",
                source_family="resolution-source-family",
                source_kind="resolution",
                resolution_source_traceable=True,
                observed_at=GENERATED_AT - timedelta(seconds=180),
            ),
        ),
    )

    assert type(report) is api.ResearchPacketSourceCrosscheckGateV2Report
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.gate_status == "pass"
    assert report.recommended_next_step == "promote_to_strategy_review"
    assert report.event_count == d("1.000000")
    assert report.pass_event_count == d("1.000000")
    assert report.blocked_event_count == d("0.000000")
    assert report.evidence_count == d("3.000000")
    assert report.fresh_evidence_count == d("3.000000")
    assert report.stale_evidence_count == d("0.000000")
    assert report.reason_codes == ("source_crosscheck_gate_passed",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.event_rows[0]
    assert row.event_id == "event-alpha"
    assert row.gate_status == "pass"
    assert row.eligible_for_strategy_review is True
    assert row.evidence_count == d("3.000000")
    assert row.fresh_evidence_count == d("3.000000")
    assert row.independent_source_family_count == d("3.000000")
    assert row.official_confirmation_count == d("1.000000")
    assert row.contradiction_review_count == d("1.000000")
    assert row.resolution_source_trace_count == d("1.000000")
    assert row.contradicting_outcome_count == d("0.000000")
    assert row.latest_evidence_age_seconds == d("60.000000")
    assert row.oldest_evidence_age_seconds == d("180.000000")
    assert row.reason_codes == ("source_crosscheck_gate_passed",)
    assert len(row.derived_validation_digest) == 64
    assert len(report.derived_validation_digest) == 64


def test_blocks_events_missing_required_crosschecks_with_deterministic_reasons() -> None:
    report = _report(
        (
            _evidence(
                "stale-proxy-only",
                source_family="proxy-source-family",
                source_kind="independent",
                observed_at=GENERATED_AT - timedelta(seconds=3601),
            ),
        ),
    )

    assert report.gate_status == "blocked"
    assert report.recommended_next_step == "block_strategy_review_pending_source_crosscheck"
    assert report.event_count == d("1.000000")
    assert report.blocked_event_count == d("1.000000")
    assert report.fresh_evidence_count == d("0.000000")
    assert report.stale_evidence_count == d("1.000000")
    assert report.reason_codes == (
        "insufficient_independent_source_families",
        "missing_official_confirmation",
        "insufficient_fresh_recency_coverage",
        "missing_contradiction_review",
        "missing_resolution_source_traceability",
    )
    row = report.event_rows[0]
    assert row.gate_status == "blocked"
    assert row.eligible_for_strategy_review is False
    assert row.independent_source_family_count == d("1.000000")
    assert row.official_confirmation_count == d("0.000000")
    assert row.contradiction_review_count == d("0.000000")
    assert row.resolution_source_trace_count == d("0.000000")
    assert row.reason_codes == report.reason_codes


def test_blocks_contradictory_event_outcomes_even_after_review() -> None:
    report = _report(
        (
            _evidence(
                "official-yes",
                source_family="official-source-family",
                source_kind="official",
                official_confirmation=True,
                contradiction_reviewed=True,
            ),
            _evidence(
                "review-yes",
                source_family="review-source-family",
                source_kind="review",
                contradiction_reviewed=True,
            ),
            _evidence(
                "resolution-no",
                source_family="resolution-source-family",
                source_kind="resolution",
                evidence_outcome="no",
                resolution_source_traceable=True,
                contradiction_reviewed=True,
            ),
        ),
    )

    assert report.gate_status == "blocked"
    assert report.reason_codes == ("unresolved_evidence_contradiction",)
    row = report.event_rows[0]
    assert row.gate_status == "blocked"
    assert row.contradicting_outcome_count == d("1.000000")
    assert row.reason_codes == ("unresolved_evidence_contradiction",)


def test_empty_evidence_blocks_report_without_event_rows() -> None:
    report = _report(())

    assert report.gate_status == "blocked"
    assert report.event_count == d("0.000000")
    assert report.evidence_count == d("0.000000")
    assert report.event_rows == ()
    assert report.reason_codes == ("no_event_evidence",)
    assert report.recommended_next_step == "block_strategy_review_pending_source_crosscheck"


def test_rejects_wrong_inputs_future_rows_false_flags_and_unsafe_public_surface() -> None:
    api = _api()
    evidence = _evidence("official-confirmation", official_confirmation=True)

    with pytest.raises(ValueError, match="evidence_rows must be a list or tuple"):
        api.build_research_packet_source_crosscheck_gate_v2(
            (row for row in (evidence,)),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="evidence_rows items must be"):
        api.build_research_packet_source_crosscheck_gate_v2(
            [object()],
            config=_config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_research_packet_source_crosscheck_gate_v2(
            [evidence],
            config=_config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _evidence("naive-time", observed_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="evidence observed_at must not be in the future"):
        _report((_evidence("future-row", observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="evidence row readonly must be True"):
        _report((_bypassed_row(evidence, readonly=False),))

    with pytest.raises(ValueError, match="event_id contains unsafe detail"):
        _evidence("unsafe-event", event_id="live-event-alpha")

    payload = api.research_packet_source_crosscheck_gate_v2_payload(_report((evidence,)))
    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wallet_key"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public field"):
        api.research_packet_source_crosscheck_gate_v2_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["review_note"] = "requires signing"
    with pytest.raises(ValueError, match="unsafe public value"):
        api.research_packet_source_crosscheck_gate_v2_payload(unsafe_value_payload)


def test_dataclasses_are_frozen_decimal_only_and_digest_tamper_is_rejected() -> None:
    api = _api()
    config = _config()
    evidence = _evidence("official-confirmation")
    report = _report(
        (
            _evidence("official-confirmation", official_confirmation=True),
            _evidence(
                "contradiction-review",
                source_family="review-source-family",
                contradiction_reviewed=True,
            ),
            _evidence(
                "resolution-trace",
                source_family="resolution-source-family",
                resolution_source_traceable=True,
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        evidence.evidence_id = "other"  # type: ignore[misc]

    with pytest.raises(ValueError, match="max_evidence_age_seconds must be a Decimal"):
        api.ResearchPacketSourceCrosscheckGateV2Config(
            max_evidence_age_seconds=3600,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="min_fresh_evidence_count must be a Decimal"):
        api.ResearchPacketSourceCrosscheckGateV2Config(
            min_fresh_evidence_count=_DecimalSubclass("2"),
        )
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        _evidence(
            "datetime-subclass",
            observed_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )

    malformed_report = _bypassed_row(report, derived_validation_digest="bad")
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        api.research_packet_source_crosscheck_gate_v2_payload(malformed_report)

    payload = api.research_packet_source_crosscheck_gate_v2_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["evidence_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        api.research_packet_source_crosscheck_gate_v2_payload(tampered_payload)


def test_public_payload_rejects_recomputed_report_digest_with_stale_row_digest() -> None:
    api = _api()
    payload = api.research_packet_source_crosscheck_gate_v2_payload(
        _report(
            (
                _evidence("official-confirmation", official_confirmation=True),
                _evidence(
                    "contradiction-review",
                    source_family="review-source-family",
                    contradiction_reviewed=True,
                ),
                _evidence(
                    "resolution-trace",
                    source_family="resolution-source-family",
                    resolution_source_traceable=True,
                ),
            ),
        ),
    )
    payload["event_rows"][0]["oldest_evidence_age_seconds"] = "181.000000"

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        api.research_packet_source_crosscheck_gate_v2_payload(
            _with_recomputed_report_digest(payload),
        )


def test_public_payload_rejects_recomputed_report_digest_with_bad_rollups() -> None:
    api = _api()
    payload = api.research_packet_source_crosscheck_gate_v2_payload(
        _report(
            (
                _evidence("official-confirmation", official_confirmation=True),
                _evidence(
                    "contradiction-review",
                    source_family="review-source-family",
                    contradiction_reviewed=True,
                ),
                _evidence(
                    "resolution-trace",
                    source_family="resolution-source-family",
                    resolution_source_traceable=True,
                ),
            ),
        ),
    )
    payload["event_count"] = "2.000000"

    with pytest.raises(ValueError, match="event_count must match event_rows"):
        api.research_packet_source_crosscheck_gate_v2_payload(
            _with_recomputed_report_digest(payload),
        )


def test_public_payload_is_json_ready_and_public_surface_is_safe() -> None:
    api = _api()
    report = _report(
        (
            _evidence(
                "official-confirmation",
                source_family="official-source-family",
                source_kind="official",
                official_confirmation=True,
            ),
            _evidence(
                "contradiction-review",
                source_family="review-source-family",
                source_kind="review",
                contradiction_reviewed=True,
            ),
            _evidence(
                "resolution-trace",
                source_family="resolution-source-family",
                source_kind="resolution",
                resolution_source_traceable=True,
            ),
        ),
    )

    payload = api.research_packet_source_crosscheck_gate_v2_payload(report)
    _assert_json_ready(payload)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["evidence_count"] == "3.000000"
    assert payload["event_rows"][0]["independent_source_family_count"] == "3.000000"
    assert payload["event_rows"][0]["latest_evidence_age_seconds"] == "60.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    assert api.__all__ == (
        "DEFAULT_RESEARCH_PACKET_SOURCE_CROSSCHECK_GATE_V2_CONFIG_VERSION",
        "ResearchPacketSourceCrosscheckGateV2Config",
        "ResearchPacketSourceCrosscheckEvidence",
        "ResearchPacketSourceCrosscheckEventRow",
        "ResearchPacketSourceCrosscheckGateV2Report",
        "build_research_packet_source_crosscheck_gate_v2",
        "research_packet_source_crosscheck_gate_v2_payload",
    )

    forbidden = {
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    }
    public_names = set(api.__all__)
    for dataclass_type in (
        api.ResearchPacketSourceCrosscheckGateV2Config,
        api.ResearchPacketSourceCrosscheckEvidence,
        api.ResearchPacketSourceCrosscheckEventRow,
        api.ResearchPacketSourceCrosscheckGateV2Report,
    ):
        public_names.update(field.name for field in fields(dataclass_type))
    public_names.update(_walk_strings(payload))

    for name in public_names:
        lowered = name.lower()
        assert all(token not in lowered for token in forbidden)
