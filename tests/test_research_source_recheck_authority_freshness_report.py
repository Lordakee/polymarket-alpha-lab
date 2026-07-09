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


MODULE_NAME = "polymarket_alpha_lab.research_source_recheck_authority_freshness_report"
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


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
        "recheck_freshness_watch_age_seconds": d("3600.000000"),
        "recheck_freshness_block_age_seconds": d("7200.000000"),
        "authority_corroboration_watch_count": d("2.000000"),
        "authority_corroboration_block_count": d("0.000000"),
        "retrieval_confidence_watch_floor": d("0.800000"),
        "retrieval_confidence_block_floor": d("0.600000"),
        "contradiction_watch_pressure": d("0.300000"),
        "contradiction_block_pressure": d("0.600000"),
        "authority_weight": d("0.250000"),
        "freshness_weight": d("0.250000"),
        "corroboration_weight": d("0.200000"),
        "retrieval_weight": d("0.150000"),
        "contradiction_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchSourceRecheckAuthorityFreshnessConfig(**values)


def recheck_item(
    source_bucket: str,
    *,
    source_authority_score: Decimal = d("0.900000"),
    latest_recheck_age_seconds: Decimal = d("900.000000"),
    authoritative_corroboration_count: Decimal = d("3.000000"),
    retrieval_confidence_score: Decimal = d("0.950000"),
    contradiction_pressure_score: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceRecheckAuthorityFreshnessInput(
        source_bucket=source_bucket,
        source_authority_score=source_authority_score,
        latest_recheck_age_seconds=latest_recheck_age_seconds,
        authoritative_corroboration_count=authoritative_corroboration_count,
        retrieval_confidence_score=retrieval_confidence_score,
        contradiction_pressure_score=contradiction_pressure_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_recheck_authority_freshness_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_recheck_authority_freshness_scores_pass_watch_and_block_rows() -> None:
    module = api()
    report = build_report(
        recheck_item("official_fresh"),
        recheck_item(
            "regional_stale_review",
            source_authority_score=d("0.650000"),
            latest_recheck_age_seconds=d("5400.000000"),
            authoritative_corroboration_count=d("1.000000"),
            retrieval_confidence_score=d("0.750000"),
            contradiction_pressure_score=d("0.400000"),
        ),
        recheck_item(
            "official_late_gap",
            source_authority_score=d("0.400000"),
            latest_recheck_age_seconds=d("8000.000000"),
            authoritative_corroboration_count=d("0.000000"),
            retrieval_confidence_score=d("0.500000"),
            contradiction_pressure_score=d("0.700000"),
        ),
    )

    assert type(report) is module.ResearchSourceRecheckAuthorityFreshnessReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.recheck_bucket_count == d("3.000000")
    assert report.pass_recheck_bucket_count == d("1.000000")
    assert report.watch_recheck_bucket_count == d("1.000000")
    assert report.block_recheck_bucket_count == d("1.000000")
    assert report.low_authority_count == d("2.000000")
    assert report.stale_recheck_count == d("2.000000")
    assert report.thin_authority_corroboration_count == d("2.000000")
    assert report.low_retrieval_confidence_count == d("2.000000")
    assert report.contradiction_pressure_count == d("2.000000")
    assert report.highest_authority_freshness_risk_score == d("0.780000")
    assert report.oldest_recheck_age_seconds == d("8000.000000")
    assert report.lowest_source_authority_score == d("0.400000")
    assert report.lowest_authoritative_corroboration_count == d("0.000000")
    assert report.lowest_retrieval_confidence_score == d("0.500000")
    assert report.highest_contradiction_pressure_score == d("0.700000")
    assert tuple(row.source_bucket for row in report.rows) == (
        "official_late_gap",
        "regional_stale_review",
        "official_fresh",
    )
    assert report.reason_codes == (
        "research_source_recheck_authority_freshness_low_authority_block",
        "research_source_recheck_authority_freshness_stale_recheck_block",
        "research_source_recheck_authority_freshness_thin_authority_corroboration_block",
        "research_source_recheck_authority_freshness_low_retrieval_confidence_block",
        "research_source_recheck_authority_freshness_contradiction_pressure_block",
        "research_source_recheck_authority_freshness_low_authority_watch",
        "research_source_recheck_authority_freshness_stale_recheck_watch",
        "research_source_recheck_authority_freshness_thin_authority_corroboration_watch",
        "research_source_recheck_authority_freshness_low_retrieval_confidence_watch",
        "research_source_recheck_authority_freshness_contradiction_pressure_watch",
    )
    assert (
        "research_source_recheck_authority_freshness_clear",
        d("1.000000"),
    ) in tuple((item.reason_code, item.count) for item in report.reason_code_counts)

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.authority_band == "low"
    assert blocked.freshness_band == "stale"
    assert blocked.authority_corroboration_score == d("0.000000")
    assert blocked.authority_freshness_risk_score == d("0.780000")
    assert blocked.reason_codes == (
        "research_source_recheck_authority_freshness_low_authority_block",
        "research_source_recheck_authority_freshness_stale_recheck_block",
        "research_source_recheck_authority_freshness_thin_authority_corroboration_block",
        "research_source_recheck_authority_freshness_low_retrieval_confidence_block",
        "research_source_recheck_authority_freshness_contradiction_pressure_block",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.authority_band == "medium"
    assert watched.freshness_band == "aging"
    assert watched.authority_corroboration_score == d("0.500000")
    assert watched.authority_freshness_risk_score == d("0.472500")
    assert watched.reason_codes == (
        "research_source_recheck_authority_freshness_low_authority_watch",
        "research_source_recheck_authority_freshness_stale_recheck_watch",
        "research_source_recheck_authority_freshness_thin_authority_corroboration_watch",
        "research_source_recheck_authority_freshness_low_retrieval_confidence_watch",
        "research_source_recheck_authority_freshness_contradiction_pressure_watch",
    )

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.authority_band == "high"
    assert passed.freshness_band == "fresh"
    assert passed.authority_freshness_risk_score == d("0.078750")
    assert passed.reason_codes == ("research_source_recheck_authority_freshness_clear",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_report_is_pass_status_with_empty_reason_and_decimal_payload() -> None:
    module = api()
    report = build_report()

    assert report.status == "pass"
    assert report.reason_codes == ("research_source_recheck_authority_freshness_empty",)
    assert report.recheck_bucket_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == (
        module.ResearchSourceRecheckAuthorityFreshnessReasonCodeCount(
            reason_code="research_source_recheck_authority_freshness_empty",
            count=d("1.000000"),
        ),
    )

    payload = module.research_source_recheck_authority_freshness_report_payload(report)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["recheck_bucket_count"] == "0.000000"
    assert payload["status"] == "pass"
    assert payload["rows"] == []
    assert_no_public_numeric_values(payload)
    json.dumps(payload, sort_keys=True, allow_nan=False)


def test_public_payload_digest_is_deterministic_and_tamper_checked() -> None:
    module = api()
    report_a = build_report(
        recheck_item("official_fresh"),
        recheck_item(
            "official_late_gap",
            source_authority_score=d("0.400000"),
            latest_recheck_age_seconds=d("8000.000000"),
            authoritative_corroboration_count=d("0.000000"),
            retrieval_confidence_score=d("0.500000"),
            contradiction_pressure_score=d("0.700000"),
        ),
    )
    report_b = build_report(
        recheck_item(
            "official_late_gap",
            source_authority_score=d("0.400000"),
            latest_recheck_age_seconds=d("8000.000000"),
            authoritative_corroboration_count=d("0.000000"),
            retrieval_confidence_score=d("0.500000"),
            contradiction_pressure_score=d("0.700000"),
        ),
        recheck_item("official_fresh"),
    )

    payload_a = module.research_source_recheck_authority_freshness_report_payload(report_a)
    payload_b = module.research_source_recheck_authority_freshness_report_payload(report_b)
    digest_a = module.research_source_recheck_authority_freshness_report_digest(report_a)
    digest_b = module.research_source_recheck_authority_freshness_report_digest(report_b)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["rows"][0]["authority_freshness_risk_score"] == "0.780000"
    assert_payload_has_no_leaked_values(payload_a)
    module.validate_research_source_recheck_authority_freshness_report_digest(report_a)
    module.validate_research_source_recheck_authority_freshness_public_payload(payload_a)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)
    tampered = dict(payload_a)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_recheck_authority_freshness_public_payload(tampered)


def test_public_payload_prevents_identifier_url_secret_and_trading_leaks() -> None:
    module = api()
    report = build_report(recheck_item("official_fresh"))
    payload = module.research_source_recheck_authority_freshness_report_payload(report)
    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "slug",
        "question",
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
        for cls in (type(recheck_item("official_fresh")), type(report), type(report.rows[0]))
        for field in fields(cls)
    }

    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload)

    for unsafe_value in (
        "candidate-123",
        "market_slug",
        "will-this-question-resolve",
        "https://example.invalid/source",
        "source_text",
        "wallet_token",
        "live_order_surface",
    ):
        with pytest.raises(ValueError, match="unsafe text"):
            recheck_item(unsafe_value)

    for unsafe_payload in (
        {"candidate_id": "safe"},
        {"slug": "safe"},
        {"safe": "https://example.invalid/source"},
        {"safe": "wallet token"},
        {"safe": "live order trade recommendation"},
        {"table_name": "public_summary"},
    ):
        with pytest.raises(ValueError, match="public payload"):
            module.validate_research_source_recheck_authority_freshness_public_payload(
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
        recheck_freshness_watch_age_seconds=d("6000.000000"),
        recheck_freshness_block_age_seconds=d("9000.000000"),
        retrieval_confidence_watch_floor=d("0.700000"),
        retrieval_confidence_block_floor=d("0.400000"),
        contradiction_watch_pressure=d("0.500000"),
        contradiction_block_pressure=d("0.800000"),
    )
    report = build_report(
        recheck_item(
            "regional_stale_review",
            source_authority_score=d("0.650000"),
            latest_recheck_age_seconds=d("5400.000000"),
            authoritative_corroboration_count=d("2.000000"),
            retrieval_confidence_score=d("0.750000"),
            contradiction_pressure_score=d("0.400000"),
        ),
        cfg=loose_config,
    )

    assert report.status == "pass"
    assert report.rows[0].status == "pass"
    assert report.rows[0].reason_codes == (
        "research_source_recheck_authority_freshness_clear",
    )

    with pytest.raises(ValueError, match="authority_weight"):
        config(authority_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="authority_corroboration_watch_count"):
        config(authority_corroboration_watch_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="weights must sum"):
        config(contradiction_weight=d("0.100000"))
    with pytest.raises(ValueError, match="authority_watch_floor"):
        config(authority_watch_floor=d("0.400000"))
    with pytest.raises(ValueError, match="recheck_freshness_watch_age_seconds"):
        config(recheck_freshness_watch_age_seconds=d("7200.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        recheck_item("official_fresh", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        recheck_item("official_fresh", readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_recheck_authority_freshness_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="authoritative_corroboration_count"):
        recheck_item(
            "invalid_fractional_count",
            authoritative_corroboration_count=d("1.500000"),
        )

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_RECHECK_AUTHORITY_FRESHNESS_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_RECHECK_AUTHORITY_FRESHNESS_STATUSES",
        "ResearchSourceRecheckAuthorityFreshnessConfig",
        "ResearchSourceRecheckAuthorityFreshnessInput",
        "ResearchSourceRecheckAuthorityFreshnessReasonCodeCount",
        "ResearchSourceRecheckAuthorityFreshnessReport",
        "ResearchSourceRecheckAuthorityFreshnessRow",
        "build_research_source_recheck_authority_freshness_report",
        "research_source_recheck_authority_freshness_report_digest",
        "research_source_recheck_authority_freshness_report_payload",
        "validate_research_source_recheck_authority_freshness_public_payload",
        "validate_research_source_recheck_authority_freshness_report_digest",
    )
    assert is_dataclass(config())
    assert is_dataclass(recheck_item("official_fresh"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().authority_weight = d("0.200000")
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
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
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
