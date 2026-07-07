from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_counterevidence_freshness_authority_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "max_source_age_seconds": d("3600.000000"),
        "min_counterevidence_quorum_ratio": d("0.666667"),
        "min_authority_score": d("0.700000"),
        "pass_readiness_score": d("0.800000"),
    }
    values.update(overrides)
    return module.ResearchPacketCounterevidenceFreshnessAuthorityV2Config(**values)


def packet(packet_id: str, **overrides: object):
    module = api()
    values = {
        "packet_id": packet_id,
        "event_slug": "fed-rate-cut-2026",
        "category": "macro",
        "counterevidence_quorum_ratio": d("0.900000"),
        "source_age_seconds": d("900.000000"),
        "authority_score": d("0.900000"),
        "contradiction_count": d("0"),
        "official_source_count": d("2"),
    }
    values.update(overrides)
    return module.ResearchPacketCounterevidenceFreshnessAuthorityV2Input(**values)


def report(*rows: object, cfg=None):
    module = api()
    return module.build_research_packet_counterevidence_freshness_authority_v2_report(
        rows,
        config=cfg or config(),
    )


def assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) is dict:
        for child in value.values():
            assert_no_public_numeric_scalars(child)
        return
    if type(value) is list:
        for child in value:
            assert_no_public_numeric_scalars(child)
        return
    assert type(value) not in (int, float, Decimal)


def test_empty_report_is_readonly_report_only_with_zero_decimal_rollups() -> None:
    module = api()
    empty = report()

    assert type(empty) is module.ResearchPacketCounterevidenceFreshnessAuthorityV2Report
    assert is_dataclass(empty)
    assert empty.report_status == "empty"
    assert empty.packet_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.stale_source_count == d("0")
    assert empty.low_authority_count == d("0")
    assert empty.low_quorum_count == d("0")
    assert empty.contradiction_count == d("0")
    assert empty.min_readiness_score == d("0.000000")
    assert empty.reason_code_counts == ()
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True
    assert len(empty.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in empty.derived_validation_digest)

    payload = module.research_packet_counterevidence_freshness_authority_v2_payload(empty)
    assert payload["report_status"] == "empty"
    assert payload["packet_count"] == "0"
    assert payload["min_readiness_score"] == "0.000000"
    assert payload["reason_code_counts"] == {}
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_scalars(payload)
    json.dumps(payload, sort_keys=True)


def test_report_scores_orders_and_rolls_up_pass_watch_block_readiness() -> None:
    mixed = report(
        packet("packet-pass"),
        packet(
            "packet-watch",
            source_age_seconds=d("5400.000000"),
            counterevidence_quorum_ratio=d("0.700000"),
            authority_score=d("0.750000"),
        ),
        packet(
            "packet-block",
            event_slug="court-ruling-2026",
            category="politics",
            counterevidence_quorum_ratio=d("0.500000"),
            source_age_seconds=d("600.000000"),
            authority_score=d("0.600000"),
            contradiction_count=d("2"),
            official_source_count=d("0"),
        ),
    )

    assert tuple(row.packet_id for row in mixed.rows) == (
        "packet-block",
        "packet-watch",
        "packet-pass",
    )
    assert tuple(row.status for row in mixed.rows) == ("block", "watch", "pass")
    assert tuple(row.readiness_score for row in mixed.rows) == (
        d("0.330000"),
        d("0.505000"),
        d("0.855000"),
    )
    assert tuple(row.freshness_score for row in mixed.rows) == (
        d("0.833333"),
        d("0.000000"),
        d("0.750000"),
    )
    assert mixed.rows[0].reason_codes == (
        "counterevidence_quorum_below_floor",
        "authority_score_below_floor",
        "source_contradiction_present",
        "official_source_missing",
        "readiness_score_below_pass",
        "counterevidence_freshness_authority_block",
    )
    assert mixed.rows[1].reason_codes == (
        "source_age_stale",
        "readiness_score_below_pass",
        "counterevidence_freshness_authority_watch",
    )
    assert mixed.rows[2].reason_codes == (
        "counterevidence_freshness_authority_pass",
    )

    assert mixed.report_status == "block"
    assert mixed.packet_count == d("3")
    assert mixed.pass_count == d("1")
    assert mixed.watch_count == d("1")
    assert mixed.block_count == d("1")
    assert mixed.stale_source_count == d("1")
    assert mixed.low_authority_count == d("1")
    assert mixed.low_quorum_count == d("1")
    assert mixed.contradiction_count == d("2")
    assert mixed.min_readiness_score == d("0.330000")
    assert mixed.reason_code_counts == (
        ("counterevidence_quorum_below_floor", d("1")),
        ("source_age_stale", d("1")),
        ("authority_score_below_floor", d("1")),
        ("source_contradiction_present", d("1")),
        ("official_source_missing", d("1")),
        ("readiness_score_below_pass", d("2")),
        ("counterevidence_freshness_authority_pass", d("1")),
        ("counterevidence_freshness_authority_watch", d("1")),
        ("counterevidence_freshness_authority_block", d("1")),
    )

    payload = api().research_packet_counterevidence_freshness_authority_v2_payload(mixed)
    assert payload["report_status"] == "block"
    assert payload["contradiction_count"] == "2"
    assert payload["reason_code_counts"]["readiness_score_below_pass"] == "2"
    assert payload["rows"][0]["readiness_score"] == "0.330000"
    assert payload["rows"][2]["status"] == "pass"
    assert payload["rows"][2]["derived_validation_digest"] == (
        mixed.rows[2].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == mixed.derived_validation_digest
    assert_no_public_numeric_scalars(payload)
    json.dumps(payload, sort_keys=True)


def test_frozen_dataclasses_decimal_only_and_digest_tamper_evident() -> None:
    module = api()
    built = report(packet("packet-ready"))

    for klass in (
        module.ResearchPacketCounterevidenceFreshnessAuthorityV2Config,
        module.ResearchPacketCounterevidenceFreshnessAuthorityV2Input,
        module.ResearchPacketCounterevidenceFreshnessAuthorityV2Row,
        module.ResearchPacketCounterevidenceFreshnessAuthorityV2Report,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        built.report_status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].status = "block"  # type: ignore[misc]

    with pytest.raises(ValueError, match="counterevidence_quorum_ratio"):
        packet("packet-decimal-subclass", counterevidence_quorum_ratio=_DecimalSubclass("0.9"))
    with pytest.raises(ValueError, match="source_age_seconds"):
        packet("packet-int-age", source_age_seconds=900)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="official_source_count"):
        packet("packet-fractional-official", official_source_count=d("1.5"))
    with pytest.raises(ValueError, match="packet_id"):
        packet(" packet-space ")
    with pytest.raises(ValueError, match="unsafe"):
        packet("wallet")
    with pytest.raises(ValueError, match="duplicate packet_id"):
        report(packet("packet-dup"), packet("packet-dup"))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built.rows[0], readiness_score=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, pass_count=d("0"))


def test_public_payload_validation_rejects_numerics_tampering_and_unsafe_surface() -> None:
    module = api()
    built = report(packet("packet-ready"))
    payload = module.research_packet_counterevidence_freshness_authority_v2_payload(built)

    module.validate_research_packet_counterevidence_freshness_authority_v2_public_payload(
        payload,
    )

    with pytest.raises(ValueError, match="Decimal-derived string"):
        module.validate_research_packet_counterevidence_freshness_authority_v2_public_payload(
            {**payload, "min_readiness_score": Decimal("0.855000")},
        )
    with pytest.raises(ValueError, match="float"):
        module.validate_research_packet_counterevidence_freshness_authority_v2_public_payload(
            {**payload, "min_readiness_score": 0.855},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_research_packet_counterevidence_freshness_authority_v2_public_payload(
            {**payload, "wallet": "paper"},
        )

    tampered = {**payload, "report_status": "pass" if payload["report_status"] != "pass" else "watch"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_counterevidence_freshness_authority_v2_payload(tampered)


def test_module_scope_is_readonly_report_only_and_external_io_free() -> None:
    module = api()

    public_surface = " ".join(module.__all__).lower()
    for forbidden in ("wallet", "private_key", "broker", "trade"):
        assert forbidden not in public_surface

    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    for forbidden in (
        "requests",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "submit_" + "order",
        "place_" + "order",
    ):
        assert forbidden not in source
