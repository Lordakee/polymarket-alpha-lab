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


MODULE_NAME = "polymarket_alpha_lab.research_source_authority_consensus_quorum_report"
GENERATED_AT = datetime(2026, 7, 8, 13, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_primary_source_count": d("1.000000"),
        "min_total_source_count": d("3.000000"),
        "min_independent_source_count": d("2.000000"),
        "freshness_watch_age_seconds": d("3600.000000"),
        "freshness_block_age_seconds": d("7200.000000"),
        "contradiction_watch_pressure": d("0.300000"),
        "contradiction_block_pressure": d("0.600000"),
        "coverage_gap_watch_score": d("0.250000"),
        "coverage_gap_block_score": d("0.500000"),
        "pass_consensus_score": d("0.750000"),
        "watch_consensus_score": d("0.450000"),
        "tier_mix_weight": d("0.250000"),
        "freshness_weight": d("0.200000"),
        "independence_weight": d("0.250000"),
        "contradiction_weight": d("0.150000"),
        "coverage_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityConsensusQuorumConfig(**values)


def quorum_item(
    quorum_bucket: str,
    *,
    primary_source_count: Decimal = d("1.000000"),
    secondary_source_count: Decimal = d("2.000000"),
    independent_source_count: Decimal = d("3.000000"),
    max_source_age_seconds: Decimal = d("900.000000"),
    contradiction_pressure_score: Decimal = d("0.050000"),
    coverage_gap_score: Decimal = d("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceAuthorityConsensusQuorumInput(
        quorum_bucket=quorum_bucket,
        primary_source_count=primary_source_count,
        secondary_source_count=secondary_source_count,
        independent_source_count=independent_source_count,
        max_source_age_seconds=max_source_age_seconds,
        contradiction_pressure_score=contradiction_pressure_score,
        coverage_gap_score=coverage_gap_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_authority_consensus_quorum_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_quorum_scores_tier_freshness_independence_coverage_into_pass_watch_block_rows() -> None:
    module = api()
    report = build_report(
        quorum_item("official_consensus"),
        quorum_item(
            "community_crosscheck",
            primary_source_count=d("1.000000"),
            secondary_source_count=d("1.000000"),
            independent_source_count=d("1.000000"),
            max_source_age_seconds=d("4800.000000"),
            contradiction_pressure_score=d("0.350000"),
            coverage_gap_score=d("0.300000"),
        ),
        quorum_item(
            "disputed_gap",
            primary_source_count=d("0.000000"),
            secondary_source_count=d("1.000000"),
            independent_source_count=d("0.000000"),
            max_source_age_seconds=d("8000.000000"),
            contradiction_pressure_score=d("0.700000"),
            coverage_gap_score=d("0.650000"),
        ),
    )

    assert type(report) is module.ResearchSourceAuthorityConsensusQuorumReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.quorum_item_count == d("3.000000")
    assert report.pass_quorum_item_count == d("1.000000")
    assert report.watch_quorum_item_count == d("1.000000")
    assert report.block_quorum_item_count == d("1.000000")
    assert report.weak_source_tier_mix_count == d("2.000000")
    assert report.stale_source_count == d("2.000000")
    assert report.thin_independence_count == d("2.000000")
    assert report.contradiction_pressure_count == d("2.000000")
    assert report.coverage_gap_count == d("2.000000")
    assert report.lowest_consensus_score == d("0.139167")
    assert report.highest_quorum_risk_score == d("0.860833")
    assert report.oldest_source_age_seconds == d("8000.000000")
    assert report.highest_contradiction_pressure_score == d("0.700000")
    assert report.highest_coverage_gap_score == d("0.650000")
    assert tuple(row.quorum_bucket for row in report.rows) == (
        "disputed_gap",
        "community_crosscheck",
        "official_consensus",
    )
    assert report.reason_codes == (
        "research_source_authority_consensus_quorum_weak_tier_mix_block",
        "research_source_authority_consensus_quorum_stale_sources_block",
        "research_source_authority_consensus_quorum_low_independence_block",
        "research_source_authority_consensus_quorum_contradiction_pressure_block",
        "research_source_authority_consensus_quorum_coverage_gap_block",
        "research_source_authority_consensus_quorum_low_score_block",
        "research_source_authority_consensus_quorum_weak_tier_mix_watch",
        "research_source_authority_consensus_quorum_stale_sources_watch",
        "research_source_authority_consensus_quorum_low_independence_watch",
        "research_source_authority_consensus_quorum_contradiction_pressure_watch",
        "research_source_authority_consensus_quorum_coverage_gap_watch",
        "research_source_authority_consensus_quorum_low_score_watch",
    )
    assert (
        "research_source_authority_consensus_quorum_clear",
        d("1.000000"),
    ) in tuple((row.reason_code, row.count) for row in report.reason_code_counts)

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.total_source_count == d("1.000000")
    assert blocked.source_tier_mix_score == d("0.166667")
    assert blocked.freshness_score == d("0.000000")
    assert blocked.independence_score == d("0.000000")
    assert blocked.contradiction_support_score == d("0.300000")
    assert blocked.coverage_score == d("0.350000")
    assert blocked.consensus_score == d("0.139167")
    assert blocked.quorum_risk_score == d("0.860833")
    assert blocked.reason_codes == (
        "research_source_authority_consensus_quorum_weak_tier_mix_block",
        "research_source_authority_consensus_quorum_stale_sources_block",
        "research_source_authority_consensus_quorum_low_independence_block",
        "research_source_authority_consensus_quorum_contradiction_pressure_block",
        "research_source_authority_consensus_quorum_coverage_gap_block",
        "research_source_authority_consensus_quorum_low_score_block",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.source_tier_mix_score == d("0.833334")
    assert watched.freshness_score == d("0.666667")
    assert watched.independence_score == d("0.500000")
    assert watched.consensus_score == d("0.669167")
    assert watched.quorum_risk_score == d("0.330833")

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.consensus_score == d("0.992500")
    assert passed.quorum_risk_score == d("0.007500")
    assert passed.reason_codes == ("research_source_authority_consensus_quorum_clear",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_contradiction_pressure_penalizes_consensus_score_and_can_block_row() -> None:
    low_pressure = build_report(
        quorum_item("low_pressure", contradiction_pressure_score=d("0.100000")),
    ).rows[0]
    high_pressure = build_report(
        quorum_item("high_pressure", contradiction_pressure_score=d("0.700000")),
    ).rows[0]

    assert low_pressure.consensus_score == d("0.985000")
    assert low_pressure.status == "pass"
    assert high_pressure.consensus_score == d("0.895000")
    assert high_pressure.quorum_risk_score == d("0.105000")
    assert high_pressure.status == "block"
    assert high_pressure.consensus_score < low_pressure.consensus_score
    assert high_pressure.reason_codes == (
        "research_source_authority_consensus_quorum_contradiction_pressure_block",
    )


def test_public_payload_digest_is_deterministic_json_ready_and_tamper_checked() -> None:
    module = api()
    report_a = build_report(
        quorum_item("official_consensus"),
        quorum_item(
            "disputed_gap",
            primary_source_count=d("0.000000"),
            secondary_source_count=d("1.000000"),
            independent_source_count=d("0.000000"),
            max_source_age_seconds=d("8000.000000"),
            contradiction_pressure_score=d("0.700000"),
            coverage_gap_score=d("0.650000"),
        ),
    )
    report_b = build_report(
        quorum_item(
            "disputed_gap",
            primary_source_count=d("0.000000"),
            secondary_source_count=d("1.000000"),
            independent_source_count=d("0.000000"),
            max_source_age_seconds=d("8000.000000"),
            contradiction_pressure_score=d("0.700000"),
            coverage_gap_score=d("0.650000"),
        ),
        quorum_item("official_consensus"),
    )

    payload_a = module.research_source_authority_consensus_quorum_report_payload(report_a)
    payload_b = module.research_source_authority_consensus_quorum_report_payload(report_b)
    digest_a = module.research_source_authority_consensus_quorum_report_digest(report_a)
    digest_b = module.research_source_authority_consensus_quorum_report_digest(report_b)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-08T13:00:00+00:00"
    assert payload_a["quorum_item_count"] == "2.000000"
    assert payload_a["rows"][0]["quorum_risk_score"] == "0.860833"
    json.dumps(payload_a, sort_keys=True, allow_nan=False)
    assert_no_public_numeric_values(payload_a)
    assert_payload_has_no_leaked_values(payload_a)
    module.validate_research_source_authority_consensus_quorum_report_digest(report_a)
    module.validate_research_source_authority_consensus_quorum_public_payload(payload_a)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)
    tampered = dict(payload_a)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_authority_consensus_quorum_public_payload(tampered)


def test_public_payload_validator_rejects_recomputed_unsafe_report_flags() -> None:
    module = api()
    report = build_report(quorum_item("official_consensus"))
    payload = module.research_source_authority_consensus_quorum_report_payload(report)

    top_level_tampered = {**payload, "report_only": False}
    top_level_tampered["derived_validation_digest"] = canonical_digest(top_level_tampered)
    with pytest.raises(ValueError, match="report_only"):
        module.validate_research_source_authority_consensus_quorum_public_payload(
            top_level_tampered,
        )

    nested_tampered = {
        **payload,
        "rows": [{**payload["rows"][0], "readonly": False}],
    }
    nested_tampered["derived_validation_digest"] = canonical_digest(nested_tampered)
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_source_authority_consensus_quorum_public_payload(
            nested_tampered,
        )


def test_public_payload_prevents_identifier_url_secret_and_trading_leaks() -> None:
    module = api()
    report = build_report(quorum_item("official_consensus"))
    payload = module.research_source_authority_consensus_quorum_report_payload(report)
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
        for cls in (type(quorum_item("official_consensus")), type(report), type(report.rows[0]))
        for field in fields(cls)
    }

    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload)

    for unsafe_value in (
        "candidate-123",
        "candidate_123",
        "raw_candidate_123",
        "market_123",
        "market_slug",
        "postgresql://example.invalid/source",
        "sqlite://example.invalid/source",
        "https://example.invalid/source",
        "api_key=abc123",
        "private_key=abc123",
        "bearer abc123",
        "source_text",
        "users_table",
        "table_users",
        "public.table",
        "wallet_token",
        "live_order_surface",
    ):
        with pytest.raises(ValueError, match="unsafe text"):
            quorum_item(unsafe_value)

    for unsafe_payload in (
        {"candidate_id": "safe"},
        {"safe": "https://example.invalid/source"},
        {"safe": "postgresql://example.invalid/source"},
        {"safe": "api_key=abc123"},
        {"safe": "private_key=abc123"},
        {"safe": "bearer abc123"},
        {"safe": "users_table"},
        {"safe": "wallet token"},
        {"safe": "live order trade recommendation"},
        {"table_name": "public_summary"},
    ):
        with pytest.raises(ValueError, match="public payload"):
            module.validate_research_source_authority_consensus_quorum_public_payload(
                {
                    **payload,
                    **unsafe_payload,
                    "derived_validation_digest": payload["derived_validation_digest"],
                },
            )


def test_custom_config_validation_flags_and_frozen_dataclasses() -> None:
    module = api()
    loose_config = config(
        min_total_source_count=d("2.000000"),
        min_independent_source_count=d("1.000000"),
        freshness_watch_age_seconds=d("6000.000000"),
        freshness_block_age_seconds=d("9000.000000"),
        contradiction_watch_pressure=d("0.500000"),
        contradiction_block_pressure=d("0.800000"),
        coverage_gap_watch_score=d("0.400000"),
        coverage_gap_block_score=d("0.700000"),
        pass_consensus_score=d("0.650000"),
        watch_consensus_score=d("0.300000"),
    )
    report = build_report(
        quorum_item(
            "community_crosscheck",
            primary_source_count=d("1.000000"),
            secondary_source_count=d("1.000000"),
            independent_source_count=d("1.000000"),
            max_source_age_seconds=d("4800.000000"),
            contradiction_pressure_score=d("0.350000"),
            coverage_gap_score=d("0.300000"),
        ),
        cfg=loose_config,
    )

    assert report.status == "pass"
    assert report.rows[0].status == "pass"
    assert report.rows[0].reason_codes == ("research_source_authority_consensus_quorum_clear",)

    with pytest.raises(ValueError, match="tier_mix_weight"):
        config(tier_mix_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="min_total_source_count"):
        config(min_total_source_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="weights must sum"):
        config(coverage_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_consensus_score"):
        config(pass_consensus_score=d("0.300000"))
    with pytest.raises(ValueError, match="freshness_watch_age_seconds"):
        config(freshness_watch_age_seconds=d("7200.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        quorum_item("official_consensus", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        quorum_item("official_consensus", readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_authority_consensus_quorum_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 13, 0),
        )

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_AUTHORITY_CONSENSUS_QUORUM_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_AUTHORITY_CONSENSUS_QUORUM_STATUSES",
        "ResearchSourceAuthorityConsensusQuorumConfig",
        "ResearchSourceAuthorityConsensusQuorumInput",
        "ResearchSourceAuthorityConsensusQuorumReasonCodeCount",
        "ResearchSourceAuthorityConsensusQuorumReport",
        "ResearchSourceAuthorityConsensusQuorumRow",
        "build_research_source_authority_consensus_quorum_report",
        "research_source_authority_consensus_quorum_report_digest",
        "research_source_authority_consensus_quorum_report_payload",
        "validate_research_source_authority_consensus_quorum_public_payload",
        "validate_research_source_authority_consensus_quorum_report_digest",
    )
    assert is_dataclass(config())
    assert is_dataclass(quorum_item("official_consensus"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().coverage_weight = d("0.100000")
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
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
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
        "postgresql://",
        "mysql://",
        "sqlite://",
        "jdbc:",
        "candidate-",
        "candidate_",
        "raw_candidate",
        "candidate_id",
        "market-",
        "market_",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "api_key",
        "private_key",
        "bearer ",
        "_table",
        "table_",
        ".table",
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
