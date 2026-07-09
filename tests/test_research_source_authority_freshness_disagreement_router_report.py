from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_authority_freshness_disagreement_router_report"
)
GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "authority_watch_floor": d("0.700000"),
        "authority_block_floor": d("0.500000"),
        "freshness_watch_lag_seconds": d("1800.000000"),
        "freshness_block_lag_seconds": d("3600.000000"),
        "corroboration_watch_breadth": d("2.000000"),
        "corroboration_block_breadth": d("0.000000"),
        "extraction_confidence_watch_floor": d("0.800000"),
        "extraction_confidence_block_floor": d("0.600000"),
        "conflict_watch_pressure": d("0.300000"),
        "conflict_block_pressure": d("0.600000"),
        "authority_weight": d("0.200000"),
        "freshness_weight": d("0.200000"),
        "corroboration_weight": d("0.200000"),
        "extraction_weight": d("0.200000"),
        "conflict_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityFreshnessDisagreementRouterConfig(**values)


def disagreement_item(
    disagreement_bucket: str,
    *,
    authority_tier: str = "official",
    freshness_lag_seconds: Decimal = d("600.000000"),
    corroboration_breadth_count: Decimal = d("3.000000"),
    extraction_confidence_score: Decimal = d("0.950000"),
    conflict_pressure_score: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceAuthorityFreshnessDisagreementRouterInput(
        disagreement_bucket=disagreement_bucket,
        authority_tier=authority_tier,
        freshness_lag_seconds=freshness_lag_seconds,
        corroboration_breadth_count=corroboration_breadth_count,
        extraction_confidence_score=extraction_confidence_score,
        conflict_pressure_score=conflict_pressure_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_authority_freshness_disagreement_router_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_routes_disagreements_by_authority_freshness_breadth_confidence_and_pressure() -> None:
    module = api()
    report = build_report(
        disagreement_item("official_clear"),
        disagreement_item(
            "secondary_aging_crosscheck",
            authority_tier="secondary",
            freshness_lag_seconds=d("2400.000000"),
            corroboration_breadth_count=d("1.000000"),
            extraction_confidence_score=d("0.750000"),
            conflict_pressure_score=d("0.400000"),
        ),
        disagreement_item(
            "tertiary_conflict_gap",
            authority_tier="tertiary",
            freshness_lag_seconds=d("4200.000000"),
            corroboration_breadth_count=d("0.000000"),
            extraction_confidence_score=d("0.500000"),
            conflict_pressure_score=d("0.700000"),
        ),
    )

    assert type(report) is module.ResearchSourceAuthorityFreshnessDisagreementRouterReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.disagreement_count == d("3.000000")
    assert report.pass_disagreement_count == d("1.000000")
    assert report.watch_disagreement_count == d("1.000000")
    assert report.block_disagreement_count == d("1.000000")
    assert report.low_authority_count == d("2.000000")
    assert report.stale_freshness_count == d("2.000000")
    assert report.thin_corroboration_count == d("2.000000")
    assert report.low_extraction_confidence_count == d("2.000000")
    assert report.conflict_pressure_count == d("2.000000")
    assert report.highest_router_pressure_score == d("0.760000")
    assert report.lowest_authority_tier_score == d("0.400000")
    assert report.oldest_freshness_lag_seconds == d("4200.000000")
    assert report.lowest_corroboration_breadth_count == d("0.000000")
    assert report.lowest_extraction_confidence_score == d("0.500000")
    assert report.highest_conflict_pressure_score == d("0.700000")
    assert tuple(row.disagreement_bucket for row in report.rows) == (
        "tertiary_conflict_gap",
        "secondary_aging_crosscheck",
        "official_clear",
    )
    assert report.reason_codes == (
        "research_source_authority_freshness_disagreement_router_low_authority_block",
        "research_source_authority_freshness_disagreement_router_stale_freshness_block",
        "research_source_authority_freshness_disagreement_router_thin_corroboration_block",
        "research_source_authority_freshness_disagreement_router_low_extraction_confidence_block",
        "research_source_authority_freshness_disagreement_router_conflict_pressure_block",
        "research_source_authority_freshness_disagreement_router_low_authority_watch",
        "research_source_authority_freshness_disagreement_router_stale_freshness_watch",
        "research_source_authority_freshness_disagreement_router_thin_corroboration_watch",
        "research_source_authority_freshness_disagreement_router_low_extraction_confidence_watch",
        "research_source_authority_freshness_disagreement_router_conflict_pressure_watch",
    )
    assert (
        "research_source_authority_freshness_disagreement_router_clear",
        d("1.000000"),
    ) in tuple((row.reason_code, row.count) for row in report.reason_code_counts)

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.authority_tier_score == d("0.400000")
    assert blocked.authority_band == "low"
    assert blocked.freshness_band == "stale"
    assert blocked.corroboration_breadth_score == d("0.000000")
    assert blocked.router_pressure_score == d("0.760000")
    assert blocked.reason_codes == (
        "research_source_authority_freshness_disagreement_router_low_authority_block",
        "research_source_authority_freshness_disagreement_router_stale_freshness_block",
        "research_source_authority_freshness_disagreement_router_thin_corroboration_block",
        "research_source_authority_freshness_disagreement_router_low_extraction_confidence_block",
        "research_source_authority_freshness_disagreement_router_conflict_pressure_block",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.authority_tier_score == d("0.650000")
    assert watched.authority_band == "medium"
    assert watched.freshness_band == "aging"
    assert watched.corroboration_breadth_score == d("0.500000")
    assert watched.router_pressure_score == d("0.433333")

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.authority_tier_score == d("1.000000")
    assert passed.authority_band == "high"
    assert passed.freshness_band == "fresh"
    assert passed.router_pressure_score == d("0.063333")
    assert passed.reason_codes == (
        "research_source_authority_freshness_disagreement_router_clear",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_threshold_edges_route_authority_and_freshness_deterministically() -> None:
    module = api()
    pass_report = build_report(disagreement_item("fresh_official"))
    watch_report = build_report(
        disagreement_item(
            "secondary_at_watch",
            authority_tier="secondary",
            freshness_lag_seconds=d("1800.000001"),
        ),
    )
    block_report = build_report(
        disagreement_item(
            "tertiary_at_block",
            authority_tier="tertiary",
            freshness_lag_seconds=d("3600.000000"),
        ),
    )

    assert module.RESEARCH_SOURCE_AUTHORITY_FRESHNESS_DISAGREEMENT_ROUTER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert pass_report.status == "pass"
    assert pass_report.rows[0].status == "pass"
    assert watch_report.status == "watch"
    assert watch_report.rows[0].status == "watch"
    assert watch_report.rows[0].freshness_band == "aging"
    assert block_report.status == "block"
    assert block_report.rows[0].status == "block"
    assert block_report.rows[0].freshness_band == "stale"


def test_public_payload_digest_is_deterministic_json_ready_and_tamper_checked() -> None:
    module = api()
    report_a = build_report(
        disagreement_item("official_clear"),
        disagreement_item(
            "tertiary_conflict_gap",
            authority_tier="tertiary",
            freshness_lag_seconds=d("4200.000000"),
            corroboration_breadth_count=d("0.000000"),
            extraction_confidence_score=d("0.500000"),
            conflict_pressure_score=d("0.700000"),
        ),
    )
    report_b = build_report(
        disagreement_item(
            "tertiary_conflict_gap",
            authority_tier="tertiary",
            freshness_lag_seconds=d("4200.000000"),
            corroboration_breadth_count=d("0.000000"),
            extraction_confidence_score=d("0.500000"),
            conflict_pressure_score=d("0.700000"),
        ),
        disagreement_item("official_clear"),
    )

    payload_a = module.research_source_authority_freshness_disagreement_router_report_payload(
        report_a,
    )
    payload_b = module.research_source_authority_freshness_disagreement_router_report_payload(
        report_b,
    )
    digest_a = module.research_source_authority_freshness_disagreement_router_report_digest(
        report_a,
    )
    digest_b = module.research_source_authority_freshness_disagreement_router_report_digest(
        report_b,
    )

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-08T14:00:00+00:00"
    assert payload_a["disagreement_count"] == "2.000000"
    assert payload_a["rows"][0]["router_pressure_score"] == "0.760000"
    json.dumps(payload_a, sort_keys=True, allow_nan=False)
    assert_no_public_numeric_values(payload_a)
    assert_payload_has_no_leaked_values(payload_a)
    module.validate_research_source_authority_freshness_disagreement_router_report_digest(
        report_a,
    )
    module.validate_research_source_authority_freshness_disagreement_router_public_payload(
        payload_a,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)
    tampered = dict(payload_a)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_authority_freshness_disagreement_router_public_payload(
            tampered,
        )


def test_public_payload_prevents_identifier_source_secret_and_trading_leaks() -> None:
    module = api()
    report = build_report(disagreement_item("official_clear"))
    payload = module.research_source_authority_freshness_disagreement_router_report_payload(
        report,
    )
    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
        "recommendation",
    }
    keys = {
        field.name
        for cls in (
            type(disagreement_item("official_clear")),
            type(report),
            type(report.rows[0]),
        )
        for field in fields(cls)
    }

    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload)

    for unsafe_value in (
        "candidate-123",
        "market_slug",
        "https://example.invalid/source",
        "source_text",
        "wallet_token",
        "live_order_surface",
    ):
        with pytest.raises(ValueError, match="unsafe text"):
            disagreement_item(unsafe_value)

    for unsafe_payload in (
        {"candidate_id": "safe"},
        {"safe": "https://example.invalid/source"},
        {"safe": "wallet token"},
        {"safe": "live order trade recommendation"},
        {"table_name": "public_summary"},
    ):
        with pytest.raises(ValueError, match="public payload"):
            module.validate_research_source_authority_freshness_disagreement_router_public_payload(
                {
                    **payload,
                    **unsafe_payload,
                    "derived_validation_digest": payload["derived_validation_digest"],
                },
            )


def test_custom_config_validation_flags_and_frozen_dataclasses() -> None:
    module = api()
    loose_config = config(
        authority_watch_floor=d("0.600000"),
        authority_block_floor=d("0.300000"),
        freshness_watch_lag_seconds=d("3000.000000"),
        freshness_block_lag_seconds=d("5000.000000"),
        corroboration_watch_breadth=d("1.000000"),
        extraction_confidence_watch_floor=d("0.700000"),
        extraction_confidence_block_floor=d("0.400000"),
        conflict_watch_pressure=d("0.500000"),
        conflict_block_pressure=d("0.800000"),
    )
    report = build_report(
        disagreement_item(
            "secondary_aging_crosscheck",
            authority_tier="secondary",
            freshness_lag_seconds=d("2400.000000"),
            corroboration_breadth_count=d("1.000000"),
            extraction_confidence_score=d("0.750000"),
            conflict_pressure_score=d("0.400000"),
        ),
        cfg=loose_config,
    )

    assert report.status == "pass"
    assert report.rows[0].status == "pass"
    assert report.rows[0].reason_codes == (
        "research_source_authority_freshness_disagreement_router_clear",
    )

    with pytest.raises(ValueError, match="authority_weight"):
        config(authority_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="freshness_watch_lag_seconds"):
        config(freshness_watch_lag_seconds=1800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="weights must sum"):
        config(conflict_weight=d("0.100000"))
    with pytest.raises(ValueError, match="authority_block_floor"):
        config(authority_block_floor=d("0.800000"))
    with pytest.raises(ValueError, match="freshness_watch_lag_seconds"):
        config(freshness_watch_lag_seconds=d("3600.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="authority_tier"):
        build_report(disagreement_item("unknown_tier", authority_tier="local_blog"))
    with pytest.raises(ValueError, match="conflict_pressure_score"):
        disagreement_item("official_clear", conflict_pressure_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="corroboration_breadth_count"):
        disagreement_item("official_clear", corroboration_breadth_count=d("1.500000"))
    with pytest.raises(ValueError, match="disagreement_bucket contains unsafe text"):
        disagreement_item("market-question")
    with pytest.raises(ValueError, match="report_only"):
        disagreement_item("official_clear", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        disagreement_item("official_clear", readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_authority_freshness_disagreement_router_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 14, 0),
        )

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_AUTHORITY_FRESHNESS_DISAGREEMENT_ROUTER_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_AUTHORITY_FRESHNESS_DISAGREEMENT_ROUTER_STATUSES",
        "ResearchSourceAuthorityFreshnessDisagreementRouterConfig",
        "ResearchSourceAuthorityFreshnessDisagreementRouterInput",
        "ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount",
        "ResearchSourceAuthorityFreshnessDisagreementRouterReport",
        "ResearchSourceAuthorityFreshnessDisagreementRouterRow",
        "build_research_source_authority_freshness_disagreement_router_report",
        "research_source_authority_freshness_disagreement_router_report_digest",
        "research_source_authority_freshness_disagreement_router_report_payload",
        "validate_research_source_authority_freshness_disagreement_router_public_payload",
        "validate_research_source_authority_freshness_disagreement_router_report_digest",
    )
    assert is_dataclass(config())
    assert is_dataclass(disagreement_item("official_clear"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().conflict_weight = d("0.100000")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="block")


def test_module_scope_is_pure_report_only_without_external_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
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
                "submit_order",
                "place_order",
                "recommend",
                "size_position",
            }

    forbidden_import_fragments = (
        "auth",
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "wallet",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)
    else:
        assert type(value) is not float
        assert type(value) is not int


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate-",
        "candidate_id",
        "market-",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "token",
        "wallet",
        "order",
        "trade",
        "live_surface",
        "recommendation",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
