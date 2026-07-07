from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
import re
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return import_module(
        "polymarket_alpha_lab.research_packet_source_freshness_authority_join_v2",
    )


def _packet_input(
    *,
    packet_id: str = "packet-alpha",
    event_slug: str = "event-alpha",
    category: str = "macro",
    newest_source_age_seconds: Decimal = d("900"),
    oldest_source_age_seconds: Decimal = d("1800"),
    authority_score: Decimal = d("0.900000"),
    proxy_dependency_ratio: Decimal = d("0.100000"),
    conflicting_source_count: Decimal = d("0"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    api = _api()
    return api.ResearchPacketSourceFreshnessAuthorityInput(
        packet_id=packet_id,
        event_slug=event_slug,
        category=category,
        newest_source_age_seconds=newest_source_age_seconds,
        oldest_source_age_seconds=oldest_source_age_seconds,
        authority_score=authority_score,
        proxy_dependency_ratio=proxy_dependency_ratio,
        conflicting_source_count=conflicting_source_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(packet_inputs: tuple[Any, ...] | list[Any], **config_overrides: object) -> Any:
    api = _api()
    config = api.ResearchPacketSourceFreshnessAuthorityJoinV2Config(**config_overrides)
    return api.build_research_packet_source_freshness_authority_join_v2_report(
        packet_inputs,
        generated_at=GENERATED_AT,
        config=config,
    )


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


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_public_numbers_are_decimal(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_public_numbers_are_decimal(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_public_numbers_are_decimal(getattr(value, field.name))


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


def test_joined_freshness_authority_score_passes_fresh_authoritative_packets() -> None:
    report = _report(
        (
            _packet_input(
                newest_source_age_seconds=d("900"),
                oldest_source_age_seconds=d("1800"),
                authority_score=d("0.900000"),
                proxy_dependency_ratio=d("0.100000"),
            ),
        ),
    )

    assert report.report_status == "pass"
    assert report.packet_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.stale_source_count == ZERO
    assert report.low_authority_count == ZERO
    assert report.proxy_dependent_count == ZERO
    assert report.conflict_count == ZERO
    assert report.min_quality_score == d("0.922188")
    assert tuple((item.reason_code, item.count) for item in report.reason_code_counts) == (
        ("freshness_authority_pass", d("1.000000")),
    )

    row = report.rows[0]
    assert row.packet_id == "packet-alpha"
    assert row.event_slug == "event-alpha"
    assert row.category == "macro"
    assert row.freshness_authority_score == d("0.922188")
    assert row.status == "pass"
    assert row.reason_codes == ("freshness_authority_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_report_sorts_rows_and_rolls_up_watch_and_block_reasons() -> None:
    report = _report(
        (
            _packet_input(
                packet_id="packet-c",
                event_slug="event-c",
                category="sports",
                newest_source_age_seconds=d("1200"),
                oldest_source_age_seconds=d("2000"),
                authority_score=d("0.950000"),
                proxy_dependency_ratio=d("0.000000"),
                conflicting_source_count=d("1"),
            ),
            _packet_input(packet_id="packet-a", event_slug="event-a", category="macro"),
            _packet_input(
                packet_id="packet-b",
                event_slug="event-b",
                category="politics",
                newest_source_age_seconds=d("120000"),
                oldest_source_age_seconds=d("180000"),
                authority_score=d("0.400000"),
                proxy_dependency_ratio=d("0.900000"),
                conflicting_source_count=d("2"),
            ),
        ),
    )

    assert tuple(row.packet_id for row in report.rows) == (
        "packet-a",
        "packet-b",
        "packet-c",
    )
    assert tuple(row.status for row in report.rows) == ("pass", "block", "watch")
    assert report.report_status == "block"
    assert report.packet_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.low_authority_count == d("1.000000")
    assert report.proxy_dependent_count == d("1.000000")
    assert report.conflict_count == d("3.000000")
    assert report.min_quality_score == ZERO

    blocked_row = report.rows[1]
    assert blocked_row.freshness_authority_score == ZERO
    assert blocked_row.reason_codes == (
        "stale_source",
        "low_authority",
        "proxy_dependent",
        "conflicting_sources",
        "quality_below_minimum",
    )
    watched_row = report.rows[2]
    assert watched_row.freshness_authority_score == d("0.865741")
    assert watched_row.reason_codes == ("conflicting_sources",)

    assert tuple((item.reason_code, item.count) for item in report.reason_code_counts) == (
        ("stale_source", d("1.000000")),
        ("low_authority", d("1.000000")),
        ("proxy_dependent", d("1.000000")),
        ("conflicting_sources", d("2.000000")),
        ("quality_below_minimum", d("1.000000")),
        ("freshness_authority_pass", d("1.000000")),
    )


def test_newest_source_age_affects_freshness_authority_score() -> None:
    report = _report(
        (
            _packet_input(
                packet_id="packet-a-fresh",
                event_slug="event-fresh",
                newest_source_age_seconds=d("0"),
                oldest_source_age_seconds=d("43200"),
            ),
            _packet_input(
                packet_id="packet-b-aging",
                event_slug="event-aging",
                newest_source_age_seconds=d("43200"),
                oldest_source_age_seconds=d("43200"),
            ),
        ),
        min_quality_score=d("0.600000"),
    )

    fresh, aging = report.rows
    assert fresh.freshness_authority_score == d("0.805000")
    assert aging.freshness_authority_score == d("0.680000")
    assert aging.freshness_authority_score < fresh.freshness_authority_score
    assert fresh.reason_codes == ("freshness_authority_pass",)
    assert aging.reason_codes == ("freshness_authority_pass",)


def test_empty_input_returns_empty_status_and_zero_decimal_rollups() -> None:
    report = _report(())

    assert report.report_status == "empty"
    assert report.rows == ()
    assert report.reason_code_counts == ()
    assert report.packet_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.stale_source_count == ZERO
    assert report.low_authority_count == ZERO
    assert report.proxy_dependent_count == ZERO
    assert report.conflict_count == ZERO
    assert report.min_quality_score == ZERO

    payload = report.payload
    assert payload["report_status"] == "empty"
    assert payload["packet_count"] == "0.000000"
    assert payload["min_quality_score"] == "0.000000"
    json.dumps(payload, sort_keys=True)


def test_payload_serializes_decimal_strings_and_rejects_digest_tampering() -> None:
    api = _api()
    report = _report((_packet_input(),))

    _assert_public_numbers_are_decimal(report)
    payload = api.research_packet_source_freshness_authority_join_v2_payload(report)
    assert payload == report.payload
    _assert_json_ready(payload)
    _assert_no_decimal_objects(payload)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["packet_count"] == "1.000000"
    assert payload["min_quality_score"] == "0.922188"
    assert payload["rows"][0]["freshness_authority_score"] == "0.922188"
    assert payload["derived_validation_digest"] == report.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["packet_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.research_packet_source_freshness_authority_join_v2_payload(tampered_payload)


def test_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    api = _api()
    packet_input = _packet_input()
    report = _report((packet_input,))

    with pytest.raises(FrozenInstanceError):
        packet_input.authority_score = d("0.800000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        _packet_input(authority_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="proxy_dependency_ratio must be a Decimal"):
        _packet_input(proxy_dependency_ratio=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        _packet_input(authority_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="oldest_source_age_seconds"):
        _packet_input(
            newest_source_age_seconds=d("2000"),
            oldest_source_age_seconds=d("1000"),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_research_packet_source_freshness_authority_join_v2_report(
            [packet_input],
            generated_at=datetime(2026, 7, 7, 12, 0),
        )
    with pytest.raises(TypeError):

        class BadInput(api.ResearchPacketSourceFreshnessAuthorityInput):
            pass


def test_hard_flags_safe_payload_and_public_exports_are_enforced() -> None:
    api = _api()

    assert api.__all__ == (
        "DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_AUTHORITY_JOIN_V2_CONFIG_VERSION",
        "ResearchPacketSourceFreshnessAuthorityJoinV2Config",
        "ResearchPacketSourceFreshnessAuthorityInput",
        "ResearchPacketSourceFreshnessAuthorityJoinV2Row",
        "ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount",
        "ResearchPacketSourceFreshnessAuthorityJoinV2Report",
        "build_research_packet_source_freshness_authority_join_v2_report",
        "research_packet_source_freshness_authority_join_v2_payload",
    )

    with pytest.raises(ValueError, match="paper_only"):
        api.ResearchPacketSourceFreshnessAuthorityJoinV2Config(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _packet_input(readonly=False)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="unsafe public"):
        _packet_input(packet_id="live-packet")

    payload = _report((_packet_input(),)).payload
    unsafe_payload = dict(payload)
    unsafe_payload["wallet_reference"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public"):
        api.research_packet_source_freshness_authority_join_v2_payload(unsafe_payload)
    unsafe_payload = dict(payload)
    unsafe_payload["auth_reference"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public"):
        api.research_packet_source_freshness_authority_join_v2_payload(unsafe_payload)

    unsafe_terms = (
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
    )
    public_names = set(api.__all__)
    for dataclass_type in (
        api.ResearchPacketSourceFreshnessAuthorityJoinV2Config,
        api.ResearchPacketSourceFreshnessAuthorityInput,
        api.ResearchPacketSourceFreshnessAuthorityJoinV2Row,
        api.ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount,
        api.ResearchPacketSourceFreshnessAuthorityJoinV2Report,
    ):
        public_names.update(field.name for field in fields(dataclass_type))
    public_names.update(_walk_strings(payload))
    for name in public_names:
        tokens = tuple(token for token in re.split(r"[^a-z0-9]+", name.lower()) if token)
        assert all(term not in tokens for term in unsafe_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "session",
        "client",
        "submit",
        "execute",
    ):
        assert not hasattr(api, forbidden_name)

    source_path = Path(api.__file__)
    assert source_path.name == "research_packet_source_freshness_authority_join_v2.py"
    source_text = source_path.read_text(encoding="utf-8")
    assert "requests" not in source_text
    assert "sqlite3" not in source_text
    assert "sqlalchemy" not in source_text
    assert "web3" not in source_text
