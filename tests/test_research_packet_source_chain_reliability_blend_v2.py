from __future__ import annotations

import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal

import pytest

from polymarket_alpha_lab import research_packet_source_chain_reliability_blend_v2 as blend


GENERATED_AT = blend.datetime(2026, 1, 1, 12, 0, tzinfo=blend.UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def source(**overrides: object) -> blend.ResearchPacketSourceChainReliabilityBlendV2Source:
    values = {
        "packet_id": "packet-alpha",
        "team_id": "politics",
        "source_id": "src-a",
        "source_family": "official",
        "reliability_score": d("0.800000"),
        "chain_weight": d("1.000000"),
        "contradiction_count": d("0.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return blend.ResearchPacketSourceChainReliabilityBlendV2Source(**values)


def report(*sources: object, **config_overrides: object):
    config = blend.ResearchPacketSourceChainReliabilityBlendV2Config(
        **config_overrides,
    )
    return blend.build_research_packet_source_chain_reliability_blend_v2_report(
        sources,
        config=config,
        generated_at=GENERATED_AT,
    )


def assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float value leaked: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_blends_source_reliability_with_weighted_base_score() -> None:
    packet = report(
        source(source_id="src-a", source_family="official", reliability_score=d("0.800000"), chain_weight=d("2.000000")),
        source(source_id="src-b", source_family="expert", reliability_score=d("0.600000"), chain_weight=d("1.000000")),
    )

    row = packet.rows[0]

    assert row.base_reliability_score == d("0.733333")
    assert row.independent_source_boost == d("0.030000")
    assert row.contradiction_penalty == d("0.000000")
    assert row.blended_reliability_score == d("0.763333")
    assert row.reliability_status == "ready"
    assert row.reason_codes == (
        "source_chain_reliability_blend_v2_independent_sources_boosted",
    )


def test_contradiction_penalties_reduce_blended_score_and_status() -> None:
    packet = report(
        source(source_id="src-a", reliability_score=d("0.700000"), contradiction_count=d("2.000000")),
    )

    row = packet.rows[0]

    assert row.base_reliability_score == d("0.700000")
    assert row.contradiction_penalty == d("0.160000")
    assert row.independent_source_boost == d("0.000000")
    assert row.blended_reliability_score == d("0.540000")
    assert row.reliability_status == "blocked"
    assert row.reason_codes == (
        "source_chain_reliability_blend_v2_contradiction_penalty",
        "source_chain_reliability_blend_v2_below_minimum_reliability",
    )


def test_independent_source_families_boost_reliability() -> None:
    same_family = report(
        source(source_id="src-a", source_family="official", reliability_score=d("0.700000")),
        source(source_id="src-b", source_family="official", reliability_score=d("0.700000")),
    )
    independent_family = report(
        source(source_id="src-a", source_family="official", reliability_score=d("0.700000")),
        source(source_id="src-b", source_family="expert", reliability_score=d("0.700000")),
    )

    assert same_family.rows[0].independent_source_boost == d("0.000000")
    assert independent_family.rows[0].independent_source_boost == d("0.030000")
    assert independent_family.rows[0].blended_reliability_score > same_family.rows[0].blended_reliability_score


def test_payload_serializes_decimals_as_strings_and_keeps_digest() -> None:
    packet = report(
        source(source_id="src-a"),
        source(source_id="src-b", source_family="expert", reliability_score=d("0.600000")),
    )

    payload = blend.research_packet_source_chain_reliability_blend_v2_payload(packet)

    assert payload["packet_count"] == "1.000000"
    assert payload["average_blended_reliability"] == "0.730000"
    assert payload["rows"][0]["base_reliability_score"] == "0.700000"
    assert payload["rows"][0]["derived_validation_digest"] == packet.rows[0].derived_validation_digest
    assert payload["derived_validation_digest"] == packet.derived_validation_digest
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)


def test_dataclasses_are_frozen_and_public_numerics_are_decimal_only() -> None:
    packet = report(source())

    assert is_dataclass(packet)
    assert is_dataclass(packet.rows[0])

    with pytest.raises(FrozenInstanceError):
        packet.paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        packet.rows[0].blended_reliability_score = d("0.1")  # type: ignore[misc]
    with pytest.raises(ValueError, match="reliability_score"):
        source(reliability_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="chain_weight"):
        source(chain_weight=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_count"):
        source(contradiction_count=d("1.500000"))


def test_hard_flags_cannot_be_downgraded() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        blend.ResearchPacketSourceChainReliabilityBlendV2Config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        source(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(source()), readonly=False)
    with pytest.raises(ValueError, match="readonly"):
        blend.research_packet_source_chain_reliability_blend_v2_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )


def test_derived_validation_digest_rejects_tampering() -> None:
    packet = report(source())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(packet, average_blended_reliability=d("0.999999"))

    payload = blend.research_packet_source_chain_reliability_blend_v2_payload(packet)
    tampered_value = dict(payload)
    tampered_value["average_blended_reliability"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        blend.research_packet_source_chain_reliability_blend_v2_payload(tampered_value)

    tampered_digest = dict(payload)
    tampered_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        blend.research_packet_source_chain_reliability_blend_v2_payload(tampered_digest)


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        source(source_id="source-wallet")
    with pytest.raises(ValueError, match="unsafe"):
        blend.research_packet_source_chain_reliability_blend_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_reference": "paper",
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        blend.research_packet_source_chain_reliability_blend_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "note": "execute trade",
            },
        )


def test_public_surface_has_no_unsafe_operational_terms() -> None:
    unsafe_terms = {
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

    public_names = set(blend.__all__)
    for exported_name in blend.__all__:
        exported = getattr(blend, exported_name)
        if is_dataclass(exported):
            public_names.update(field.name for field in fields(exported))
        if inspect.isfunction(exported):
            public_names.update(inspect.signature(exported).parameters)

    assert public_names
    for public_name in public_names:
        normalized = public_name.lower()
        assert not any(term in normalized for term in unsafe_terms), public_name

    packet_payload = blend.research_packet_source_chain_reliability_blend_v2_payload(
        report(source()),
    )
    flattened_values = json.dumps(packet_payload, sort_keys=True).lower()
    for term in unsafe_terms:
        assert term not in flattened_values
