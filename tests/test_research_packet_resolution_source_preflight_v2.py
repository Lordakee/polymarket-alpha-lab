from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_resolution_source_preflight_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "min_official_anchor_count": d("2"),
        "min_independent_source_family_count": d("2"),
        "max_official_anchor_age_seconds": d("3600"),
        "min_rule_text_trace_count": d("1"),
        "min_settlement_evidence_count": d("1"),
    }
    values.update(overrides)
    return module.ResearchPacketResolutionSourcePreflightConfig(**values)


def anchor(
    source_id: str,
    *,
    source_family: str,
    observed_at: datetime = GENERATED_AT,
    is_official_resolution_source: bool = True,
    has_rule_text_trace: bool = True,
    has_settlement_evidence: bool = False,
):
    module = api()
    return module.ResearchPacketResolutionSourceAnchor(
        source_id=source_id,
        source_family=source_family,
        observed_at=observed_at,
        is_official_resolution_source=is_official_resolution_source,
        has_rule_text_trace=has_rule_text_trace,
        has_settlement_evidence=has_settlement_evidence,
    )


def packet(
    anchors,
    *,
    contradiction_reviewed: bool = True,
    contradiction_reviewed_at: datetime | None = GENERATED_AT,
):
    module = api()
    return module.ResearchPacketResolutionSourceEventPacket(
        packet_id="packet_final_result",
        event_slug="event_final_result",
        rule_text_reference="rule_text_primary",
        contradiction_reviewed=contradiction_reviewed,
        contradiction_reviewed_at=contradiction_reviewed_at,
        anchors=anchors,
    )


def report(
    event_packet,
    *,
    cfg=None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_packet_resolution_source_preflight_v2_report(
        event_packet,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float_or_int(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)


def redigest_payload(payload: dict[str, Any]) -> dict[str, Any]:
    redigested = dict(payload)
    canonical = json.dumps(
        {
            key: value
            for key, value in redigested.items()
            if key != "derived_validation_digest"
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    redigested["derived_validation_digest"] = hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return redigested


def clear_packet():
    return packet(
        (
            anchor(
                "official_final_result_a",
                source_family="official_result_family_a",
                observed_at=GENERATED_AT - timedelta(seconds=30),
                has_settlement_evidence=True,
            ),
            anchor(
                "official_final_result_b",
                source_family="official_result_family_b",
                observed_at=GENERATED_AT - timedelta(seconds=60),
            ),
        ),
    )


def test_clear_preflight_passes_and_payload_serializes_decimals_as_strings() -> None:
    module = api()
    preflight = report(clear_packet())

    assert is_dataclass(preflight)
    assert preflight.generated_at == GENERATED_AT
    assert preflight.official_anchor_count == d("2")
    assert preflight.independent_source_family_count == d("2")
    assert preflight.stale_official_anchor_count == d("0")
    assert preflight.rule_text_trace_count == d("2")
    assert preflight.settlement_evidence_count == d("1")
    assert preflight.contradiction_review_count == d("1")
    assert preflight.newest_official_anchor_age_seconds == d("30.000000")
    assert preflight.oldest_official_anchor_age_seconds == d("60.000000")
    assert preflight.status == "pass"
    assert preflight.reason_codes == ("resolution_source_preflight_clear",)
    assert preflight.paper_only is True
    assert preflight.report_only is True
    assert preflight.readonly is True
    assert len(preflight.derived_validation_digest) == 64

    assert tuple(row.source_id for row in preflight.anchor_rows) == (
        "official_final_result_a",
        "official_final_result_b",
    )
    assert preflight.anchor_rows[0].anchor_age_seconds == d("30.000000")
    assert preflight.anchor_rows[0].is_fresh is True

    payload = module.research_packet_resolution_source_preflight_v2_payload(preflight)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["official_anchor_count"] == "2"
    assert payload["newest_official_anchor_age_seconds"] == "30.000000"
    assert payload["anchor_rows"][0]["anchor_age_seconds"] == "30.000000"
    assert payload["derived_validation_digest"] == preflight.derived_validation_digest
    assert module.validate_research_packet_resolution_source_preflight_v2_payload(payload) == payload
    assert_no_float_or_int(payload)


def test_preflight_blocks_insufficient_stale_unreviewed_untraced_packet() -> None:
    blocked = report(
        packet(
            (
                anchor(
                    "official_stale_result",
                    source_family="official_result_family_a",
                    observed_at=GENERATED_AT - timedelta(seconds=7201),
                    has_rule_text_trace=False,
                    has_settlement_evidence=False,
                ),
            ),
            contradiction_reviewed=False,
            contradiction_reviewed_at=None,
        ),
    )

    assert blocked.official_anchor_count == d("1")
    assert blocked.independent_source_family_count == d("1")
    assert blocked.stale_official_anchor_count == d("1")
    assert blocked.rule_text_trace_count == d("0")
    assert blocked.settlement_evidence_count == d("0")
    assert blocked.contradiction_review_count == d("0")
    assert blocked.status == "blocked"
    assert blocked.reason_codes == (
        "insufficient_official_anchor_count",
        "insufficient_source_family_independence",
        "stale_official_resolution_source_anchor",
        "missing_contradiction_review",
        "missing_rule_text_traceability",
        "missing_settlement_evidence",
    )
    assert blocked.anchor_rows[0].is_fresh is False


def test_frozen_flags_digest_tamper_and_unsafe_public_payload_rejection() -> None:
    module = api()
    preflight = report(clear_packet())

    with pytest.raises(FrozenInstanceError):
        preflight.packet_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(preflight, paper_only=False)

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(preflight, derived_validation_digest="0" * 64)

    payload = module.research_packet_resolution_source_preflight_v2_payload(preflight)
    tampered_payload = dict(payload)
    tampered_payload["official_anchor_count"] = "3"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.validate_research_packet_resolution_source_preflight_v2_payload(
            tampered_payload,
        )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wa" "llet_reference"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.validate_research_packet_resolution_source_preflight_v2_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["event_slug"] = "paper-" "tra" "de"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.validate_research_packet_resolution_source_preflight_v2_payload(
            unsafe_value_payload,
        )

    for flag_name in ("paper_only", "report_only", "readonly"):
        flagless_payload = redigest_payload(
            {key: value for key, value in payload.items() if key != flag_name},
        )
        with pytest.raises(ValueError, match=f"{flag_name} must be True"):
            module.validate_research_packet_resolution_source_preflight_v2_payload(
                flagless_payload,
            )

        row_flagless_payload = dict(payload)
        row_flagless_payload["anchor_rows"] = [
            dict(row) for row in payload["anchor_rows"]
        ]
        row_flagless_payload["anchor_rows"][0].pop(flag_name)
        row_flagless_payload = redigest_payload(row_flagless_payload)
        with pytest.raises(
            ValueError,
            match=f"anchor_rows\\[0\\].{flag_name} must be True",
        ):
            module.validate_research_packet_resolution_source_preflight_v2_payload(
                row_flagless_payload,
            )

    with pytest.raises(ValueError, match="source_id has unsafe public value"):
        anchor(
            "wa" "llet_feed",
            source_family="official_result_family_a",
        )


def test_validates_decimal_datetime_uniqueness_and_packet_invariants() -> None:
    module = api()

    with pytest.raises(ValueError, match="min_official_anchor_count must be a Decimal"):
        config(min_official_anchor_count=2.0)

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        anchor(
            "official_naive_result",
            source_family="official_result_family_a",
            observed_at=datetime(2026, 7, 2, 12, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(
            clear_packet(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        report(
            packet(
                (
                    anchor(
                        "official_future_result",
                        source_family="official_result_family_a",
                        observed_at=GENERATED_AT + timedelta(seconds=1),
                    ),
                ),
            ),
        )

    with pytest.raises(ValueError, match="source_id values must be unique"):
        packet(
            (
                anchor("official_duplicate", source_family="official_result_family_a"),
                anchor("official_duplicate", source_family="official_result_family_b"),
            ),
        )

    with pytest.raises(ValueError, match="contradiction_reviewed_at is required"):
        packet(clear_packet().anchors, contradiction_reviewed=True, contradiction_reviewed_at=None)

    with pytest.raises(ValueError, match="config must be"):
        module.build_research_packet_resolution_source_preflight_v2_report(
            clear_packet(),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_module_scope_is_pure_in_memory_report_only() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_packet_resolution_source_preflight_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for token in (
        "li" "ve",
        "au" "th",
        "wa" "llet",
        "or" "der",
        "net" "work",
        "data" "base",
        "per" "sist",
        "sign" "ing",
        "muta" "tion",
        "bu" "y",
        "se" "ll",
        "tra" "de",
        "request",
        "socket",
        "urllib",
        "sqlite",
        "sqlalchemy",
        "open(",
        "write(",
        "read(",
    ):
        assert token not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported = tuple(alias.name for alias in node.names)
            assert "requests" not in imported
            assert "socket" not in imported
