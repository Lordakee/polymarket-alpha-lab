from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab import research_packet_official_source_hierarchy_score_v2 as module


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def source(
    source_id: str,
    *,
    packet_id: str = "packet-hierarchy-pass",
    event_id: str = "event-election-result",
    source_role: str = "official_primary",
    source_family: str = "election-board",
    source_title: str = "Official result bulletin",
    observed_delta: timedelta = timedelta(seconds=60),
    supports_resolution_rule: bool = True,
    contradicts_resolution: bool = False,
) -> module.ResearchPacketOfficialSourceHierarchyInput:
    return module.ResearchPacketOfficialSourceHierarchyInput(
        packet_id=packet_id,
        event_id=event_id,
        source_id=source_id,
        source_role=source_role,
        source_family=source_family,
        source_title=source_title,
        observed_at=GENERATED_AT - observed_delta,
        supports_resolution_rule=supports_resolution_rule,
        contradicts_resolution=contradicts_resolution,
    )


def config(**overrides: object) -> module.ResearchPacketOfficialSourceHierarchyScoreConfig:
    values: dict[str, object] = {
        "max_source_age_seconds": d("3600.000000"),
        "minimum_independent_confirmation_count": d("2"),
        "pass_score_threshold": d("0.850000"),
        "block_score_threshold": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchPacketOfficialSourceHierarchyScoreConfig(**values)


def clean_sources(packet_id: str = "packet-hierarchy-pass") -> tuple[object, ...]:
    return (
        source(
            "source-official-primary",
            packet_id=packet_id,
            source_role="official_primary",
            source_family="election-board",
            source_title="Official result bulletin",
            observed_delta=timedelta(seconds=60),
        ),
        source(
            "source-secondary",
            packet_id=packet_id,
            source_role="secondary",
            source_family="court-record",
            source_title="Court record summary",
            observed_delta=timedelta(seconds=120),
        ),
        source(
            "source-confirmation-a",
            packet_id=packet_id,
            source_role="independent_confirmation",
            source_family="research-archive-a",
            source_title="Independent confirmation A",
            observed_delta=timedelta(seconds=180),
            supports_resolution_rule=False,
        ),
        source(
            "source-confirmation-b",
            packet_id=packet_id,
            source_role="independent_confirmation",
            source_family="research-archive-b",
            source_title="Independent confirmation B",
            observed_delta=timedelta(seconds=240),
            supports_resolution_rule=False,
        ),
    )


def build_report(
    rows: tuple[object, ...],
    *,
    generated_at: datetime = GENERATED_AT,
) -> module.ResearchPacketOfficialSourceHierarchyScoreReport:
    return module.build_research_packet_official_source_hierarchy_score_v2_report(
        rows,
        config=config(),
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


def test_clean_hierarchy_scores_pass_and_payload_digest_is_deterministic() -> None:
    report = build_report(clean_sources())
    reversed_report = build_report(tuple(reversed(clean_sources())))

    assert report.status == "pass"
    assert report.packet_count == d("1")
    assert report.source_count == d("4")
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.average_hierarchy_score == d("1.000000")
    assert report.reason_codes == ("official_source_hierarchy_score_pass",)
    assert report.derived_validation_digest == reversed_report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)

    row = report.rows[0]
    assert row.packet_id == "packet-hierarchy-pass"
    assert row.score_band == "pass"
    assert row.official_primary_source_count == d("1")
    assert row.secondary_source_count == d("1")
    assert row.independent_confirmation_count == d("2")
    assert row.fresh_source_count == d("4")
    assert row.stale_source_count == d("0")
    assert row.contradictory_source_count == d("0")
    assert row.resolution_rule_aligned_source_count == d("1")
    assert row.official_primary_score == d("1.000000")
    assert row.secondary_source_score == d("1.000000")
    assert row.independent_confirmation_score == d("1.000000")
    assert row.freshness_score == d("1.000000")
    assert row.contradiction_score == d("1.000000")
    assert row.resolution_rule_alignment_score == d("1.000000")
    assert row.hierarchy_score == d("1.000000")
    assert row.reason_codes == ("official_source_hierarchy_score_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True

    payload = module.research_packet_official_source_hierarchy_score_v2_payload(report)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["packet_count"] == "1"
    assert payload["source_count"] == "4"
    assert payload["average_hierarchy_score"] == "1.000000"
    assert payload["rows"][0]["hierarchy_score"] == "1.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int(payload)


def test_missing_secondary_thin_confirmation_stale_and_contradictory_sources_roll_up() -> None:
    rows = (
        source(
            "missing-primary-secondary",
            packet_id="packet-missing-primary",
            source_role="secondary",
            source_family="court-record",
        ),
        source(
            "missing-primary-confirmation",
            packet_id="packet-missing-primary",
            source_role="independent_confirmation",
            source_family="research-archive",
            supports_resolution_rule=False,
        ),
        source(
            "stale-contradictory-primary",
            packet_id="packet-stale-contradictory",
            source_role="official_primary",
            source_family="election-board",
            observed_delta=timedelta(seconds=7201),
            contradicts_resolution=True,
        ),
        source(
            "stale-contradictory-secondary",
            packet_id="packet-stale-contradictory",
            source_role="secondary",
            source_family="court-record",
            observed_delta=timedelta(seconds=120),
        ),
        source(
            "watch-primary",
            packet_id="packet-watch",
            source_role="official_primary",
            source_family="election-board",
        ),
        source(
            "watch-confirmation",
            packet_id="packet-watch",
            source_role="independent_confirmation",
            source_family="research-archive",
            supports_resolution_rule=False,
        ),
    )

    report = build_report(rows)

    assert report.status == "blocked"
    assert report.packet_count == d("3")
    assert report.source_count == d("6")
    assert report.pass_count == d("0")
    assert report.watch_count == d("1")
    assert report.blocked_count == d("2")
    assert report.missing_official_primary_source_count == d("1")
    assert report.missing_secondary_source_count == d("1")
    assert report.thin_independent_confirmation_count == d("3")
    assert report.stale_source_count == d("1")
    assert report.contradictory_source_count == d("1")
    assert report.missing_resolution_rule_alignment_count == d("1")
    assert report.reason_codes == (
        "official_source_hierarchy_score_blocked",
        "missing_official_primary_source",
        "missing_secondary_source",
        "thin_independent_confirmations",
        "stale_hierarchy_source",
        "contradictory_hierarchy_source",
        "missing_resolution_rule_alignment",
    )

    rows_by_packet = {row.packet_id: row for row in report.rows}
    assert tuple(rows_by_packet) == (
        "packet-missing-primary",
        "packet-stale-contradictory",
        "packet-watch",
    )

    missing_primary = rows_by_packet["packet-missing-primary"]
    assert missing_primary.score_band == "blocked"
    assert missing_primary.hierarchy_score == d("0.500000")
    assert missing_primary.reason_codes == (
        "official_source_hierarchy_score_blocked",
        "missing_official_primary_source",
        "thin_independent_confirmations",
        "missing_resolution_rule_alignment",
    )

    stale_contradictory = rows_by_packet["packet-stale-contradictory"]
    assert stale_contradictory.score_band == "blocked"
    assert stale_contradictory.stale_source_count == d("1")
    assert stale_contradictory.contradictory_source_count == d("1")
    assert stale_contradictory.freshness_score == d("0.500000")
    assert stale_contradictory.contradiction_score == d("0.500000")
    assert stale_contradictory.reason_codes == (
        "official_source_hierarchy_score_blocked",
        "thin_independent_confirmations",
        "stale_hierarchy_source",
        "contradictory_hierarchy_source",
    )

    watch = rows_by_packet["packet-watch"]
    assert watch.score_band == "watch"
    assert watch.hierarchy_score == d("0.750000")
    assert watch.reason_codes == (
        "official_source_hierarchy_score_watch",
        "missing_secondary_source",
        "thin_independent_confirmations",
    )


def test_frozen_dataclasses_and_digest_validation_reject_tampering() -> None:
    report = build_report(clean_sources())

    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.research_packet_official_source_hierarchy_score_v2_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["average_hierarchy_score"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_official_source_hierarchy_score_v2_payload(tampered_payload)

    missing_digest_payload = dict(payload)
    missing_digest_payload.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_official_source_hierarchy_score_v2_payload(
            missing_digest_payload,
        )


def test_inputs_require_decimals_exact_datetime_flags_uniqueness_and_safe_text() -> None:
    with pytest.raises(ValueError, match="max_source_age_seconds must be a Decimal"):
        config(max_source_age_seconds=3600)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="supports_resolution_rule must be a bool"):
        source("bad-bool", supports_resolution_rule=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="source_role"):
        source("bad-role", source_role="blog")

    naive_source = source(
        "naive-source",
        observed_delta=timedelta(seconds=60),
    )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_packet_official_source_hierarchy_score_v2_report(
            (naive_source,),
            config=config(),
            generated_at=datetime(2026, 7, 7, 12, 0),
        )

    future_source = source("future-source", observed_delta=timedelta(seconds=-1))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report((future_source,))

    duplicate = source("duplicate-source")
    with pytest.raises(ValueError, match="unique by packet_id and source_id"):
        build_report((duplicate, duplicate))

    with pytest.raises(ValueError, match="unsafe public value"):
        source("unsafe-source", source_title="official wa" "llet page")


def test_payload_rejects_unsafe_public_keys_values_and_non_report_types() -> None:
    payload = module.research_packet_official_source_hierarchy_score_v2_payload(
        build_report(clean_sources()),
    )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wa" "llet_reference"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public key"):
        module.research_packet_official_source_hierarchy_score_v2_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [
        dict(payload["rows"][0], source_family="paper-" "tra" "de")
    ]
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_packet_official_source_hierarchy_score_v2_payload(
            unsafe_value_payload,
        )

    with pytest.raises(ValueError, match="report must be"):
        module.research_packet_official_source_hierarchy_score_v2_payload(object())


def test_module_scope_is_pure_in_memory_report_only() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/research_packet_official_source_hierarchy_score_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()
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

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported = tuple(alias.name for alias in node.names)
            assert "requests" not in imported
            assert "socket" not in imported
