from __future__ import annotations

import ast
import copy
import importlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_packet_domain_source_map_v2 import (
    DEFAULT_RESEARCH_PACKET_DOMAIN_SOURCE_MAP_V2_CONFIG_VERSION,
    DomainSourceFamilyScoreV2,
    ResearchPacketDomainSourceMapV2Config,
    ResearchPacketDomainSourceMapV2InputRow,
    ResearchPacketDomainSourceMapV2Report,
    build_research_packet_domain_source_map_v2,
    research_packet_domain_source_map_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _family(
    source_family: str,
    anchor: str,
    *,
    reliability: Decimal = d("0.950000"),
    latency: Decimal = d("300.000000"),
    independence: Decimal = d("0.900000"),
    contradiction: Decimal = d("0.050000"),
) -> DomainSourceFamilyScoreV2:
    return DomainSourceFamilyScoreV2(
        source_family=source_family,
        official_source_anchor=anchor,
        historical_reliability_score=reliability,
        median_latency_seconds=latency,
        independence_score=independence,
        contradiction_risk_score=contradiction,
    )


def _input_row(
    event_domain: str = "politics.us.election",
    *,
    preferred: tuple[DomainSourceFamilyScoreV2, ...] | None = None,
    backup: tuple[DomainSourceFamilyScoreV2, ...] | None = None,
) -> ResearchPacketDomainSourceMapV2InputRow:
    if preferred is None:
        preferred = (_family("election_calendar", "public-election-calendar"),)
    if backup is None:
        backup = (
            _family(
                "wire_reference",
                "public-wire-summary",
                reliability=d("0.800000"),
                latency=d("1200.000000"),
                independence=d("0.700000"),
                contradiction=d("0.150000"),
            ),
        )
    return ResearchPacketDomainSourceMapV2InputRow(
        event_domain=event_domain,
        preferred_source_families=preferred,
        backup_source_families=backup,
    )


def _report() -> ResearchPacketDomainSourceMapV2Report:
    return build_research_packet_domain_source_map_v2(
        (
            _input_row(
                "finance.crypto.btc",
                preferred=(
                    _family(
                        "exchange_reference",
                        "public-reference-index",
                        reliability=d("0.980000"),
                        latency=d("60.000000"),
                        independence=d("0.850000"),
                        contradiction=d("0.020000"),
                    ),
                ),
            ),
            _input_row(),
        ),
        config=ResearchPacketDomainSourceMapV2Config(),
        generated_at=GENERATED_AT,
    )


def _all_leaf_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        leaves: list[object] = []
        for item in value.values():
            leaves.extend(_all_leaf_values(item))
        return tuple(leaves)
    if isinstance(value, list):
        leaves = []
        for item in value:
            leaves.extend(_all_leaf_values(item))
        return tuple(leaves)
    return (value,)


def test_builds_decimal_only_domain_source_map_payload_with_digest() -> None:
    report = _report()

    assert isinstance(report, ResearchPacketDomainSourceMapV2Report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_RESEARCH_PACKET_DOMAIN_SOURCE_MAP_V2_CONFIG_VERSION
    )
    assert report.row_count == d("2")
    assert report.preferred_source_family_count == d("2")
    assert report.backup_source_family_count == d("2")
    assert report.average_historical_reliability_score == d("0.965000")
    assert report.maximum_median_latency_seconds == d("300.000000")
    assert report.average_independence_score == d("0.875000")
    assert report.maximum_contradiction_risk_score == d("0.050000")
    assert report.mapping_status == "ready"
    assert report.reason_codes == ("domain_source_map_ready",)
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.event_domain for row in report.rows) == (
        "finance.crypto.btc",
        "politics.us.election",
    )
    btc_row = report.rows[0]
    assert btc_row.official_source_anchors == (
        "public-reference-index",
        "public-wire-summary",
    )
    assert btc_row.historical_reliability_score == d("0.980000")
    assert btc_row.median_latency_seconds == d("60.000000")
    assert btc_row.independence_score == d("0.850000")
    assert btc_row.contradiction_risk_score == d("0.020000")
    assert btc_row.contradiction_risk_band == "low"

    payload = research_packet_domain_source_map_v2_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["row_count"] == "2"
    assert payload["average_historical_reliability_score"] == "0.965000"
    assert payload["maximum_median_latency_seconds"] == "300.000000"
    assert payload["rows"][0]["preferred_source_families"][0][
        "historical_reliability_score"
    ] == "0.980000"
    assert payload["rows"][0]["backup_source_families"][0][
        "median_latency_seconds"
    ] == "1200.000000"
    assert not any(isinstance(value, Decimal) for value in _all_leaf_values(payload))


def test_payload_rejects_digest_tampering_and_unsafe_public_surface() -> None:
    payload = research_packet_domain_source_map_v2_payload(_report())

    tampered_metric = copy.deepcopy(payload)
    tampered_metric["rows"][0]["contradiction_risk_score"] = "0.990000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_packet_domain_source_map_v2_payload(tampered_metric)

    tampered_digest = copy.deepcopy(payload)
    tampered_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_packet_domain_source_map_v2_payload(tampered_digest)

    unsafe_key = copy.deepcopy(payload)
    unsafe_key["network_path"] = "public-reference"
    with pytest.raises(ValueError, match="unsafe public"):
        research_packet_domain_source_map_v2_payload(unsafe_key)

    unsafe_value = copy.deepcopy(payload)
    unsafe_value["rows"][0]["event_domain"] = "live politics"
    with pytest.raises(ValueError, match="unsafe public"):
        research_packet_domain_source_map_v2_payload(unsafe_value)

    flag_downgrade = copy.deepcopy(payload)
    flag_downgrade["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_packet_domain_source_map_v2_payload(flag_downgrade)


def test_validates_decimal_only_strings_flags_and_frozen_dataclasses() -> None:
    with pytest.raises(ValueError, match="minimum_reliability_score"):
        ResearchPacketDomainSourceMapV2Config(minimum_reliability_score=1)
    with pytest.raises(ValueError, match="source_family"):
        _family(_StringSubclass("official_reference"), "public-anchor")
    with pytest.raises(ValueError, match="historical_reliability_score"):
        _family(
            "official_reference",
            "public-anchor",
            reliability=_DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="preferred_source_families"):
        ResearchPacketDomainSourceMapV2InputRow(
            event_domain="politics.us.election",
            preferred_source_families=(),
            backup_source_families=(),
        )
    with pytest.raises(ValueError, match="unique"):
        ResearchPacketDomainSourceMapV2InputRow(
            event_domain="politics.us.election",
            preferred_source_families=(
                _family("official_reference", "public-anchor-one"),
            ),
            backup_source_families=(
                _family("official_reference", "public-anchor-two"),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_family("official_reference", "public-anchor"), paper_only=False)

    report = _report()
    with pytest.raises(FrozenInstanceError):
        report.rows[0].event_domain = "politics.other"


def test_rejects_inconsistent_rows_and_reports() -> None:
    source_family = _family(
        "official_reference",
        "public-anchor",
        reliability=d("0.900000"),
        latency=d("900.000000"),
        independence=d("0.800000"),
        contradiction=d("0.250000"),
    )

    with pytest.raises(ValueError, match="historical_reliability_score"):
        replace(
            _input_row(preferred=(source_family,)).to_report_row(),
            historical_reliability_score=d("0.910000"),
        )

    report = _report()
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, mapping_status="watch")


def test_scope_excludes_io_and_sensitive_surface() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_packet_domain_source_map_v2",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    lowered_source = source.lower()
    for token in (
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
    ):
        assert token not in lowered_source

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "send",
            }

    forbidden_import_fragments = (
        "db",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
