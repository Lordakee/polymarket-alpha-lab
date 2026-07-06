from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 15, 0, tzinfo=UTC)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_dispute_resolution_source_route_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> object:
    module = api()
    values = {
        "config_version": "research-packet-dispute-resolution-source-route-v2",
        "min_official_source_count": d("1"),
        "min_independent_source_count": d("2"),
        "min_source_route_score": d("0.700000"),
        "official_source_route_boost": d("0.150000"),
        "ambiguous_route_penalty": d("0.250000"),
        "missing_official_route_penalty": d("0.300000"),
    }
    values.update(overrides)
    return module.ResearchPacketDisputeResolutionSourceRouteConfig(**values)


def source(**overrides: object) -> object:
    module = api()
    values = {
        "packet_id": "packet-alpha",
        "resolution_reference": "resolution-ref-alpha",
        "source_id": "source-alpha",
        "source_route_type": "official",
        "source_available": True,
        "checked_at": GENERATED_AT - timedelta(minutes=5),
        "route_confidence_score": d("0.800000"),
        "ambiguous_resolution_route": False,
        "public_summary": "Official source resolves the event.",
    }
    values.update(overrides)
    return module.ResearchPacketDisputeResolutionSourceRouteSource(**values)


def report(*rows: object, cfg: object | None = None) -> object:
    module = api()
    return module.build_research_packet_dispute_resolution_source_route_v2(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_no_runtime_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numeric_values(item)
    else:
        assert type(value) not in (Decimal, float, int)


def test_dispute_resolution_source_routing_scores_all_statuses() -> None:
    digest_report = report(
        source(
            packet_id="packet-clear",
            resolution_reference="resolution-clear",
            source_id="source-clear-official",
            source_route_type="official",
            route_confidence_score=d("0.750000"),
        ),
        source(
            packet_id="packet-clear",
            resolution_reference="resolution-clear",
            source_id="source-clear-independent",
            source_route_type="independent",
            route_confidence_score=d("0.650000"),
        ),
        source(
            packet_id="packet-review",
            resolution_reference="resolution-review",
            source_id="source-review-official",
            source_route_type="official",
            route_confidence_score=d("0.800000"),
            ambiguous_resolution_route=True,
            public_summary="Official source uses ambiguous resolution language.",
        ),
        source(
            packet_id="packet-review",
            resolution_reference="resolution-review",
            source_id="source-review-independent",
            source_route_type="independent",
            route_confidence_score=d("0.700000"),
        ),
        source(
            packet_id="packet-gap",
            resolution_reference="resolution-gap",
            source_id="source-gap-independent",
            source_route_type="independent",
            route_confidence_score=d("0.600000"),
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.source_count == d("5")
    assert digest_report.route_row_count == d("3")
    assert digest_report.pass_count == d("1")
    assert digest_report.review_count == d("1")
    assert digest_report.blocked_count == d("1")
    assert digest_report.average_source_route_score == d("0.600000")
    assert digest_report.max_ambiguous_route_penalty == d("0.250000")
    assert digest_report.report_status == "blocked"
    assert digest_report.reason_codes == (
        "dispute_resolution_source_route_blocked",
        "dispute_resolution_source_route_review",
        "ambiguous_route_penalty_applied",
        "missing_official_route_penalty_applied",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    rows_by_packet = {row.packet_id: row for row in digest_report.rows}
    clear = rows_by_packet["packet-clear"]
    assert clear.selected_source_route == "official_resolution_route"
    assert clear.source_route_status == "pass"
    assert clear.average_route_confidence_score == d("0.700000")
    assert clear.official_route_boost == d("0.150000")
    assert clear.source_route_score == d("0.850000")
    assert clear.reason_codes == (
        "official_route_boost_applied",
        "independent_route_support",
        "resolution_source_route_clear",
    )

    review = rows_by_packet["packet-review"]
    assert review.selected_source_route == "official_resolution_route"
    assert review.source_route_status == "review"
    assert review.ambiguous_route_count == d("1")
    assert review.ambiguous_route_penalty == d("0.250000")
    assert review.source_route_score == d("0.650000")
    assert review.reason_codes == (
        "official_route_boost_applied",
        "independent_route_support",
        "ambiguous_route_penalty_applied",
        "resolution_source_route_review",
    )

    gap = rows_by_packet["packet-gap"]
    assert gap.selected_source_route == "source_gap_route"
    assert gap.source_route_status == "blocked"
    assert gap.missing_official_route_penalty == d("0.300000")
    assert gap.source_route_score == d("0.300000")
    assert gap.reason_codes == (
        "missing_official_route_penalty_applied",
        "resolution_source_route_blocked",
    )


def test_official_route_boosts_can_clear_threshold() -> None:
    digest_report = report(
        source(route_confidence_score=d("0.600000")),
        cfg=config(min_source_route_score=d("0.700000")),
    )

    row = digest_report.rows[0]
    assert row.average_route_confidence_score == d("0.600000")
    assert row.official_route_boost == d("0.150000")
    assert row.source_route_score == d("0.750000")
    assert row.source_route_status == "pass"
    assert row.reason_codes == (
        "official_route_boost_applied",
        "resolution_source_route_clear",
    )


def test_ambiguous_route_penalties_can_force_review() -> None:
    digest_report = report(
        source(
            route_confidence_score=d("0.900000"),
            ambiguous_resolution_route=True,
        ),
        cfg=config(min_source_route_score=d("0.700000")),
    )

    row = digest_report.rows[0]
    assert row.average_route_confidence_score == d("0.900000")
    assert row.official_route_boost == d("0.150000")
    assert row.ambiguous_route_penalty == d("0.250000")
    assert row.source_route_score == d("0.800000")
    assert row.source_route_status == "review"
    assert row.reason_codes == (
        "official_route_boost_applied",
        "ambiguous_route_penalty_applied",
        "resolution_source_route_review",
    )


def test_payload_serializes_decimal_values_as_strings_and_preserves_flags() -> None:
    module = api()
    digest_report = report(source())

    payload = module.research_packet_dispute_resolution_source_route_v2_payload(
        digest_report,
    )
    payload_text = repr(payload)

    assert payload["generated_at"] == "2026-07-06T15:00:00+00:00"
    assert payload["source_count"] == "1"
    assert payload["average_source_route_score"] == "0.950000"
    assert payload["rows"][0]["source_route_score"] == "0.950000"
    assert payload["rows"][0]["derived_validation_digest"] == (
        digest_report.rows[0].derived_validation_digest
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "Decimal(" not in payload_text
    assert "datetime" not in payload_text.lower()
    assert_no_runtime_numeric_values(payload)


def test_dataclasses_are_frozen_and_require_decimal_public_numbers() -> None:
    module = api()
    digest_report = report(source())

    with pytest.raises(FrozenInstanceError):
        digest_report.rows[0].source_route_status = "review"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        digest_report.source_count = d("2")  # type: ignore[misc]

    with pytest.raises(ValueError, match="route_confidence_score must be a Decimal"):
        source(route_confidence_score=0.8)

    with pytest.raises(ValueError, match="min_official_source_count must be a Decimal"):
        config(min_official_source_count=1)

    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="source must be readonly"):
        source(readonly=False)

    assert {field.name for field in fields(module.ResearchPacketDisputeResolutionSourceRouteRow)}
    assert {field.name for field in fields(module.ResearchPacketDisputeResolutionSourceRouteReport)}


def test_derived_validation_digest_rejects_tampering() -> None:
    digest_report = report(source())

    assert len(digest_report.derived_validation_digest) == 64
    assert len(digest_report.rows[0].derived_validation_digest) == 64

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(digest_report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(digest_report.rows[0], derived_validation_digest="0" * 64)


def test_unsafe_payload_keys_values_and_flag_downgrades_are_rejected() -> None:
    module = api()
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

    with pytest.raises(ValueError, match="payload must be readonly"):
        module.research_packet_dispute_resolution_source_route_v2_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.research_packet_dispute_resolution_source_route_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "score": 0.1,
            },
        )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_packet_dispute_resolution_source_route_v2_payload(
                {"paper_only": True, "report_only": True, "readonly": True, term: "x"},
            )
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_packet_dispute_resolution_source_route_v2_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    "note": f"contains {term} term",
                },
            )


def test_public_module_surface_excludes_execution_side_effects() -> None:
    module = api()
    source_path = Path(
        "src/polymarket_alpha_lab/research_packet_dispute_resolution_source_route_v2.py",
    )
    source_text = source_path.read_text(encoding="utf-8")
    lowered = source_text.lower()

    assert module.__all__ == (
        "ResearchPacketDisputeResolutionSourceRouteConfig",
        "ResearchPacketDisputeResolutionSourceRouteSource",
        "ResearchPacketDisputeResolutionSourceRouteRow",
        "ResearchPacketDisputeResolutionSourceRouteReport",
        "build_research_packet_dispute_resolution_source_route_v2",
        "research_packet_dispute_resolution_source_route_v2_payload",
    )
    public_names = {name.lower() for name in module.__all__}
    public_fields = {
        field.name.lower()
        for cls_name in module.__all__
        if cls_name.startswith("ResearchPacket")
        for field in fields(getattr(module, cls_name))
    }
    for forbidden in (
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
        assert all(forbidden not in name for name in public_names)
        assert all(forbidden not in name for name in public_fields)

    for forbidden_fragment in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "subprocess",
        "open(",
        "write(",
        "delete(",
    ):
        assert forbidden_fragment not in lowered

    tree = ast.parse(source_text)
    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Import):
            assert all(
                alias.name.split(".")[0] not in forbidden_import_roots
                for alias in node.names
            )
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
