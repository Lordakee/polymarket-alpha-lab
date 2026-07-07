from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import importlib.util
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_packet_source_freshness_staleness_gate_v2"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, f"{MODULE_NAME} should exist"
    return importlib.import_module(MODULE_NAME)


def packet(
    packet_id: str,
    *,
    event_slug: str = "fomc-july-cut",
    category: str = "macro",
    newest_age_seconds: int = 300,
    oldest_age_seconds: int = 1200,
    official_source_count: Decimal = d("1"),
    independent_source_family_count: Decimal = d("2"),
    required_freshness_seconds: Decimal = d("1800.000000"),
) -> Any:
    gate = module()
    return gate.ResearchPacketSourceFreshnessStalenessGateV2Input(
        packet_id=packet_id,
        event_slug=event_slug,
        category=category,
        newest_source_at=GENERATED_AT - timedelta(seconds=newest_age_seconds),
        oldest_source_at=GENERATED_AT - timedelta(seconds=oldest_age_seconds),
        official_source_count=official_source_count,
        independent_source_family_count=independent_source_family_count,
        required_freshness_seconds=required_freshness_seconds,
    )


def build_report(*rows: Any, config: Any | None = None) -> Any:
    gate = module()
    return gate.build_research_packet_source_freshness_staleness_gate_v2(
        rows,
        generated_at=GENERATED_AT,
        config=config or gate.ResearchPacketSourceFreshnessStalenessGateV2Config(),
    )


def assert_no_public_numeric_scalars(value: object) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if isinstance(value, (int, float, Decimal)):
        raise AssertionError(f"public payload contains numeric scalar: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numeric_scalars(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_public_numeric_scalars(item)
        return
    raise AssertionError(f"unexpected public payload value: {value!r}")


def test_builds_ordered_report_with_pass_watch_and_block_rollups() -> None:
    gate = module()
    config = gate.ResearchPacketSourceFreshnessStalenessGateV2Config(
        min_official_source_count=d("1"),
        min_independent_source_family_count=d("2"),
    )

    report = build_report(
        packet("watch-packet", oldest_age_seconds=2400),
        packet("pass-packet"),
        packet(
            "block-packet",
            event_slug="baseball-final",
            category="sports",
            newest_age_seconds=2500,
            oldest_age_seconds=4200,
            official_source_count=d("0"),
            independent_source_family_count=d("1"),
        ),
        config=config,
    )

    assert tuple(row.packet_id for row in report.rows) == (
        "pass-packet",
        "watch-packet",
        "block-packet",
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert report.packet_count == d("3")
    assert report.pass_packet_count == d("1")
    assert report.watch_packet_count == d("1")
    assert report.block_packet_count == d("1")
    assert report.stale_packet_count == d("2")
    assert report.official_source_gap_count == d("1")
    assert report.source_family_gap_count == d("1")
    assert report.max_oldest_source_age_seconds == d("4200.000000")
    assert report.report_status == "block"
    assert report.reason_code_counts["source_freshness_pass"] == d("1")
    assert report.reason_code_counts["stale_source_gap"] == d("2")
    assert report.reason_code_counts["newest_source_stale"] == d("1")
    assert report.reason_code_counts["official_source_gap"] == d("1")
    assert report.reason_code_counts["source_family_gap"] == d("1")

    block_row = report.rows[2]
    assert block_row.newest_source_age_seconds == d("2500.000000")
    assert block_row.oldest_source_age_seconds == d("4200.000000")
    assert block_row.stale_source_gap == d("2400.000000")
    assert block_row.reason_codes == (
        "newest_source_stale",
        "stale_source_gap",
        "official_source_gap",
        "source_family_gap",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_input_returns_empty_status_and_zero_decimal_rollups() -> None:
    report = build_report()

    assert report.report_status == "empty"
    assert report.rows == ()
    assert report.reason_code_counts == {}
    assert report.packet_count == d("0")
    assert report.pass_packet_count == d("0")
    assert report.watch_packet_count == d("0")
    assert report.block_packet_count == d("0")
    assert report.stale_packet_count == d("0")
    assert report.official_source_gap_count == d("0")
    assert report.source_family_gap_count == d("0")
    assert report.max_oldest_source_age_seconds == d("0.000000")


def test_public_payload_is_decimal_only_safe_and_digest_validated() -> None:
    gate = module()
    report = build_report(packet("packet-alpha"))

    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)

    payload = gate.research_packet_source_freshness_staleness_gate_v2_public_payload(
        report,
    )

    assert payload["packet_count"] == "1"
    assert payload["max_oldest_source_age_seconds"] == "1200.000000"
    assert payload["reason_code_counts"] == {"source_freshness_pass": "1"}
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_scalars(payload)
    assert gate.validate_research_packet_source_freshness_staleness_gate_v2_public_payload(
        payload,
    )

    tampered = dict(payload)
    tampered["report_status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        gate.research_packet_source_freshness_staleness_gate_v2_public_payload(tampered)

    numeric_payload = dict(payload)
    numeric_payload["packet_count"] = 1
    with pytest.raises(ValueError, match="Decimal strings"):
        gate.research_packet_source_freshness_staleness_gate_v2_public_payload(
            numeric_payload,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["wallet_field"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        gate.research_packet_source_freshness_staleness_gate_v2_public_payload(
            unsafe_payload,
        )


def test_decimal_only_inputs_flags_and_datetime_invariants_are_enforced() -> None:
    gate = module()

    with pytest.raises(ValueError, match="Decimal"):
        packet("bad-official-count", official_source_count=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        gate.ResearchPacketSourceFreshnessStalenessGateV2Config(
            min_official_source_count=1,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="oldest_source_at"):
        gate.ResearchPacketSourceFreshnessStalenessGateV2Input(
            packet_id="bad-time-sequence",
            event_slug="fomc-july-cut",
            category="macro",
            newest_source_at=GENERATED_AT - timedelta(seconds=600),
            oldest_source_at=GENERATED_AT - timedelta(seconds=300),
            official_source_count=d("1"),
            independent_source_family_count=d("2"),
            required_freshness_seconds=d("1800.000000"),
        )

    with pytest.raises(ValueError, match="must not be after generated_at"):
        build_report(
            gate.ResearchPacketSourceFreshnessStalenessGateV2Input(
                packet_id="future-packet",
                event_slug="fomc-july-cut",
                category="macro",
                newest_source_at=GENERATED_AT + timedelta(seconds=1),
                oldest_source_at=GENERATED_AT - timedelta(seconds=300),
                official_source_count=d("1"),
                independent_source_family_count=d("2"),
                required_freshness_seconds=d("1800.000000"),
            ),
        )

    with pytest.raises(ValueError, match="paper_only"):
        replace(packet("bad-flag"), paper_only=False)


def test_dataclasses_are_frozen() -> None:
    gate = module()
    config = gate.ResearchPacketSourceFreshnessStalenessGateV2Config()
    input_row = packet("frozen-input")
    report = build_report(input_row)
    output_row = report.rows[0]

    for value in (config, input_row, output_row, report):
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
