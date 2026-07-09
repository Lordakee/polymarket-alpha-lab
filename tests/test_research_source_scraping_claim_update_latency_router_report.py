from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_scraping_claim_update_latency_router_report"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def ago(seconds: int) -> datetime:
    return GENERATED_AT - timedelta(seconds=seconds)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "extraction_latency_watch_seconds": d("120.000000"),
        "extraction_latency_block_seconds": d("600.000000"),
        "update_age_watch_seconds": d("3600.000000"),
        "update_age_block_seconds": d("14400.000000"),
        "authority_confidence_watch_floor": d("0.750000"),
        "authority_confidence_block_floor": d("0.500000"),
        "corroboration_breadth_watch_floor": d("2.000000"),
        "corroboration_breadth_block_floor": d("0.000000"),
        "contradiction_pressure_watch": d("0.300000"),
        "contradiction_pressure_block": d("0.700000"),
        "extraction_latency_weight": d("0.200000"),
        "update_freshness_weight": d("0.200000"),
        "authority_confidence_weight": d("0.200000"),
        "corroboration_breadth_weight": d("0.200000"),
        "contradiction_pressure_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchSourceScrapingClaimUpdateLatencyRouterConfig(**values)


def scraped_update(
    claim_update_bucket: str,
    *,
    scraped_at: datetime = ago(130),
    extracted_at: datetime = ago(120),
    claim_updated_at: datetime = ago(900),
    authority_confidence_score: Decimal = d("0.950000"),
    corroboration_breadth_count: Decimal = d("4.000000"),
    contradiction_pressure_score: Decimal = d("0.050000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceScrapingClaimUpdate(
        claim_update_bucket=claim_update_bucket,
        scraped_at=scraped_at,
        extracted_at=extracted_at,
        claim_updated_at=claim_updated_at,
        authority_confidence_score=authority_confidence_score,
        corroboration_breadth_count=corroboration_breadth_count,
        contradiction_pressure_score=contradiction_pressure_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*updates: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_source_scraping_claim_update_latency_router_report(
        updates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def assert_no_public_float_or_int(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_float_or_int(item)


def test_routes_sanitized_updates_by_latency_freshness_authority_breadth_and_pressure() -> None:
    report = build_report(
        scraped_update("official-clear"),
        scraped_update(
            "aging-crosscheck",
            scraped_at=ago(4200),
            extracted_at=ago(4020),
            claim_updated_at=ago(7200),
            authority_confidence_score=d("0.650000"),
            corroboration_breadth_count=d("1.000000"),
            contradiction_pressure_score=d("0.400000"),
        ),
        scraped_update(
            "stale-conflict",
            scraped_at=ago(3000),
            extracted_at=ago(2100),
            claim_updated_at=ago(20000),
            authority_confidence_score=d("0.400000"),
            corroboration_breadth_count=d("0.000000"),
            contradiction_pressure_score=d("0.850000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.update_count == d("3.000000")
    assert report.pass_update_count == d("1.000000")
    assert report.watch_update_count == d("1.000000")
    assert report.block_update_count == d("1.000000")
    assert report.max_extraction_latency_seconds == d("900.000000")
    assert report.oldest_update_age_seconds == d("20000.000000")
    assert report.lowest_authority_confidence_score == d("0.400000")
    assert report.lowest_corroboration_breadth_count == d("0.000000")
    assert report.highest_contradiction_pressure_score == d("0.850000")
    assert report.highest_router_pressure_score == d("0.890000")
    assert report.status == "block"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.claim_update_bucket for row in report.rows) == (
        "stale-conflict",
        "aging-crosscheck",
        "official-clear",
    )

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.extraction_latency_seconds == d("900.000000")
    assert blocked.update_age_seconds == d("20000.000000")
    assert blocked.corroboration_breadth_score == d("0.000000")
    assert blocked.router_pressure_score == d("0.890000")
    assert blocked.reason_codes == (
        "scraping_claim_update_latency_router_extraction_latency_block",
        "scraping_claim_update_latency_router_stale_update_block",
        "scraping_claim_update_latency_router_authority_confidence_block",
        "scraping_claim_update_latency_router_corroboration_breadth_block",
        "scraping_claim_update_latency_router_contradiction_pressure_block",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.extraction_latency_seconds == d("180.000000")
    assert watched.update_age_seconds == d("7200.000000")
    assert watched.corroboration_breadth_score == d("0.500000")
    assert watched.router_pressure_score == d("0.410000")
    assert watched.reason_codes == (
        "scraping_claim_update_latency_router_extraction_latency_watch",
        "scraping_claim_update_latency_router_stale_update_watch",
        "scraping_claim_update_latency_router_authority_confidence_watch",
        "scraping_claim_update_latency_router_corroboration_breadth_watch",
        "scraping_claim_update_latency_router_contradiction_pressure_watch",
    )

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.extraction_latency_seconds == d("10.000000")
    assert passed.update_age_seconds == d("900.000000")
    assert passed.router_pressure_score == d("0.055833")
    assert passed.reason_codes == ("scraping_claim_update_latency_router_pass",)


def test_stale_update_penalty_routes_to_block_even_when_extraction_is_fast() -> None:
    report = build_report(
        scraped_update(
            "stale-only",
            scraped_at=ago(20),
            extracted_at=ago(10),
            claim_updated_at=ago(18000),
            authority_confidence_score=d("0.950000"),
            corroboration_breadth_count=d("5.000000"),
            contradiction_pressure_score=d("0.050000"),
        ),
    )

    row = report.rows[0]
    assert report.status == "block"
    assert row.status == "block"
    assert row.extraction_latency_seconds == d("10.000000")
    assert row.update_age_seconds == d("18000.000000")
    assert row.reason_codes == (
        "scraping_claim_update_latency_router_stale_update_block",
    )


def test_public_payload_digest_is_deterministic_json_ready_and_validated() -> None:
    module = api()
    updates = (
        scraped_update("official-clear"),
        scraped_update(
            "stale-conflict",
            scraped_at=ago(3000),
            extracted_at=ago(2100),
            claim_updated_at=ago(20000),
            authority_confidence_score=d("0.400000"),
            corroboration_breadth_count=d("0.000000"),
            contradiction_pressure_score=d("0.850000"),
        ),
    )
    report_a = build_report(
        *updates,
        generated_at=datetime(2026, 7, 9, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    report_b = build_report(*tuple(reversed(updates)))

    payload_a = module.research_source_scraping_claim_update_latency_router_public_payload(
        report_a,
    )
    payload_b = module.research_source_scraping_claim_update_latency_router_public_payload(
        report_b,
    )

    assert payload_a == payload_b
    assert payload_a["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload_a["update_count"] == "2.000000"
    assert payload_a["rows"][0]["claim_update_bucket"] == "stale-conflict"
    assert payload_a["derived_validation_digest"] == report_a.derived_validation_digest
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert_no_public_float_or_int(payload_a)
    module.validate_research_source_scraping_claim_update_latency_router_digest(report_a)
    module.validate_research_source_scraping_claim_update_latency_router_public_payload(
        payload_a,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)

    tampered = dict(payload_a)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_scraping_claim_update_latency_router_public_payload(
            tampered,
        )


def test_public_payload_and_inputs_reject_sensitive_identifier_surfaces() -> None:
    module = api()
    for unsafe_bucket in (
        "candidate-alpha",
        "market-alpha",
        "slug-alpha",
        "question-alpha",
        "raw-alpha",
        "https-alpha",
        "url-alpha",
        "text-alpha",
        "dsn-alpha",
        "table-alpha",
        "token-alpha",
        "wallet-alpha",
        "order-alpha",
        "trade-alpha",
        "live-alpha",
    ):
        with pytest.raises(ValueError, match="claim_update_bucket has unsafe public value"):
            scraped_update(unsafe_bucket)

    payload = module.research_source_scraping_claim_update_latency_router_public_payload(
        build_report(scraped_update("official-clear")),
    )
    payload_text = repr(payload).lower()
    for forbidden in (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "postgres://",
        "dsn",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_trading",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in payload_text

    tampered = dict(payload)
    tampered["source_url"] = "https://example.invalid/private"
    tampered["derived_validation_digest"] = canonical_digest(tampered)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.validate_research_source_scraping_claim_update_latency_router_public_payload(
            tampered,
        )


def test_frozen_dataclasses_decimal_only_datetime_exactness_and_hard_flags() -> None:
    module = api()
    report = build_report(scraped_update("official-clear"))

    for klass in (
        module.ResearchSourceScrapingClaimUpdateLatencyRouterConfig,
        module.ResearchSourceScrapingClaimUpdate,
        module.ResearchSourceScrapingClaimUpdateLatencyRouterRow,
        module.ResearchSourceScrapingClaimUpdateLatencyRouterReasonCodeCount,
        module.ResearchSourceScrapingClaimUpdateLatencyRouterReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]

    decimal_fields = {
        "extraction_latency_seconds",
        "update_age_seconds",
        "authority_confidence_score",
        "corroboration_breadth_count",
        "corroboration_breadth_score",
        "contradiction_pressure_score",
        "router_pressure_score",
    }
    for row_field in fields(report.rows[0]):
        if row_field.name in decimal_fields:
            assert type(getattr(report.rows[0], row_field.name)) is Decimal

    with pytest.raises(ValueError, match="authority_confidence_score must be a Decimal"):
        scraped_update("bad-authority", authority_confidence_score=1)
    with pytest.raises(ValueError, match="contradiction_pressure_score must be a Decimal"):
        scraped_update(
            "bad-contradiction",
            contradiction_pressure_score=_DecimalSubclass("0.100000"),
        )
    with pytest.raises(ValueError, match="scraped_at must be a datetime"):
        scraped_update(
            "bad-time",
            scraped_at=_DatetimeSubclass(2026, 7, 9, 11, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="extracted_at must be timezone-aware"):
        scraped_update(
            "bad-offset",
            extracted_at=datetime(2026, 7, 9, 11, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="config must be readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="update must be paper_only"):
        scraped_update("bad-flag", paper_only=False)


def test_custom_config_validation_and_thresholds_are_deterministic() -> None:
    custom = config(
        extraction_latency_watch_seconds=d("30.000000"),
        extraction_latency_block_seconds=d("60.000000"),
        update_age_watch_seconds=d("120.000000"),
        update_age_block_seconds=d("600.000000"),
        authority_confidence_watch_floor=d("0.900000"),
        authority_confidence_block_floor=d("0.700000"),
        corroboration_breadth_watch_floor=d("3.000000"),
        corroboration_breadth_block_floor=d("1.000000"),
        contradiction_pressure_watch=d("0.100000"),
        contradiction_pressure_block=d("0.300000"),
    )
    report = build_report(
        scraped_update(
            "custom-watch",
            scraped_at=ago(225),
            extracted_at=ago(180),
            claim_updated_at=ago(180),
            authority_confidence_score=d("0.850000"),
            corroboration_breadth_count=d("2.000000"),
            contradiction_pressure_score=d("0.200000"),
        ),
        cfg=custom,
    )

    assert report.status == "watch"
    assert report.rows[0].status == "watch"
    assert report.rows[0].reason_codes == (
        "scraping_claim_update_latency_router_extraction_latency_watch",
        "scraping_claim_update_latency_router_stale_update_watch",
        "scraping_claim_update_latency_router_authority_confidence_watch",
        "scraping_claim_update_latency_router_corroboration_breadth_watch",
        "scraping_claim_update_latency_router_contradiction_pressure_watch",
    )

    with pytest.raises(ValueError, match="extraction_latency_block_seconds"):
        config(extraction_latency_block_seconds=d("120.000000"))
    with pytest.raises(ValueError, match="authority_confidence_block_floor"):
        config(authority_confidence_block_floor=d("0.800000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(contradiction_pressure_weight=d("0.100000"))
    with pytest.raises(ValueError, match="update_age_watch_seconds must be a Decimal"):
        config(update_age_watch_seconds=120)


def test_module_scope_has_no_runtime_io_or_trading_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/"
        "research_source_scraping_claim_update_latency_router_report.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlite",
        "supabase",
        "web3",
    )
    forbidden_runtime_names = (
        "signing",
        "private_key",
        "api_key",
        "authenticate",
        "submit",
        "cancel",
        "replace_order",
        "create_order",
        "execute",
        "connect",
        "commit",
        "rollback",
        "cursor",
        "open",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", maxsplit=1)[0] not in forbidden_modules
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", maxsplit=1)[0] not in forbidden_modules
        if isinstance(node, ast.Name):
            assert node.id.lower() not in forbidden_runtime_names
        if isinstance(node, ast.Attribute):
            assert node.attr.lower() not in forbidden_runtime_names
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id != "float"
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr.lower() not in forbidden_runtime_names
