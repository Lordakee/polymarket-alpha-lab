from __future__ import annotations

import ast
import hashlib
import importlib
import json
import re
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "research-strategy-source-memory-claim-floor-report-v0"
ZERO = Decimal("0.000000")


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_source_memory_claim_floor_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    research = module()
    values = {
        "config_version": CONFIG_VERSION,
        "claim_floor_score": d("0.600000"),
        "watch_margin": d("0.050000"),
    }
    values.update(overrides)
    return research.ResearchStrategySourceMemoryClaimFloorConfig(**values)


def claim(
    candidate_ref: str,
    *,
    market_ref: str = "raw-market-alpha",
    source_locator: str = "https://example.test/raw/source?token=do-not-leak",
    claim_text: str = "raw source claim text must stay private",
    memory_score: Decimal = d("0.900000"),
    claim_support_score: Decimal = d("0.800000"),
    source_independence_score: Decimal = d("0.700000"),
    source_recency_score: Decimal = d("0.750000"),
    contradiction_score: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    research = module()
    return research.ResearchStrategySourceMemoryClaimFloorClaim(
        candidate_ref=candidate_ref,
        market_ref=market_ref,
        source_locator=source_locator,
        claim_text=claim_text,
        memory_score=memory_score,
        claim_support_score=claim_support_score,
        source_independence_score=source_independence_score,
        source_recency_score=source_recency_score,
        contradiction_score=contradiction_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*claims, cfg=None, generated_at: datetime = GENERATED_AT):
    research = module()
    return research.build_research_strategy_source_memory_claim_floor_report(
        claims,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_builds_claim_floor_report_with_only_pass_watch_block_states() -> None:
    report = build_report(
        claim("candidate-pass"),
        claim(
            "candidate-watch",
            memory_score=d("0.620000"),
            claim_support_score=d("0.800000"),
            source_independence_score=d("0.700000"),
            source_recency_score=d("0.700000"),
            contradiction_score=d("0.200000"),
        ),
        claim(
            "candidate-block",
            memory_score=d("0.400000"),
            claim_support_score=d("0.650000"),
            source_independence_score=d("0.700000"),
            source_recency_score=d("0.700000"),
            contradiction_score=d("0.150000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.claim_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.status == "block"
    assert set(report.reason_codes) <= {
        "claim_floor_pass",
        "claim_floor_watch",
        "claim_floor_block",
        "claim_floor_watch_margin",
        "memory_score_below_floor",
    }
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    block_row, watch_row, pass_row = report.rows
    assert block_row.claim_floor_score == d("0.400000")
    assert block_row.floor_delta == d("-0.200000")
    assert block_row.reason_codes == (
        "claim_floor_block",
        "memory_score_below_floor",
    )
    assert watch_row.claim_floor_score == d("0.620000")
    assert watch_row.floor_delta == d("0.020000")
    assert watch_row.reason_codes == (
        "claim_floor_watch",
        "claim_floor_watch_margin",
    )
    assert pass_row.claim_floor_score == d("0.700000")
    assert pass_row.floor_delta == d("0.100000")
    assert pass_row.reason_codes == ("claim_floor_pass",)


def test_public_payload_is_deterministic_digest_validated_and_sanitized() -> None:
    research = module()
    report = build_report(
        claim(
            "candidate-alpha-sensitive",
            market_ref="market-slug-sensitive",
            source_locator="https://example.test/source/path?token=private",
            claim_text="raw text about the source memory claim",
        ),
    )

    payload = research.research_strategy_source_memory_claim_floor_report_payload(report)
    same_payload = research.research_strategy_source_memory_claim_floor_report_payload(
        build_report(
            claim(
                "candidate-alpha-sensitive",
                market_ref="market-slug-sensitive",
                source_locator="https://example.test/source/path?token=private",
                claim_text="raw text about the source memory claim",
            ),
        ),
    )
    assert payload == same_payload

    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8",
        ),
    ).hexdigest()
    assert payload["derived_validation_digest"] == expected_digest
    research.validate_research_strategy_source_memory_claim_floor_public_payload(payload)

    encoded = json.dumps(payload, sort_keys=True)
    for raw_fragment in (
        "candidate-alpha-sensitive",
        "market-slug-sensitive",
        "https://example.test",
        "token",
        "private",
        "raw text about the source memory claim",
    ):
        assert raw_fragment not in encoded
    assert len(payload["rows"][0]["claim_ref_digest"]) == 64
    assert len(payload["rows"][0]["market_ref_digest"]) == 64
    assert len(payload["rows"][0]["source_ref_digest"]) == 64
    assert not _contains_float_or_int(payload)


def test_digest_validation_rejects_tampering_flag_downgrades_and_unsafe_payload() -> None:
    research = module()
    payload = research.research_strategy_source_memory_claim_floor_report_payload(
        build_report(claim("candidate-alpha")),
    )

    tampered = dict(payload)
    tampered["status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research.research_strategy_source_memory_claim_floor_report_payload(tampered)

    downgraded = dict(payload)
    downgraded["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        research.research_strategy_source_memory_claim_floor_report_payload(downgraded)

    unsafe_key = dict(payload)
    unsafe_key["wallet_ref"] = "blocked"
    with pytest.raises(ValueError, match="unsafe"):
        research.research_strategy_source_memory_claim_floor_report_payload(unsafe_key)

    unsafe_value = dict(payload)
    unsafe_value["public_note"] = "contains token material"
    with pytest.raises(ValueError, match="unsafe"):
        research.research_strategy_source_memory_claim_floor_report_payload(unsafe_value)


def test_frozen_dataclasses_decimal_only_and_validation_guards() -> None:
    research = module()
    report = build_report(claim("candidate-alpha"))

    assert is_dataclass(research.ResearchStrategySourceMemoryClaimFloorConfig)
    assert is_dataclass(research.ResearchStrategySourceMemoryClaimFloorClaim)
    assert is_dataclass(research.ResearchStrategySourceMemoryClaimFloorRow)
    assert is_dataclass(research.ResearchStrategySourceMemoryClaimFloorReport)
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].claim_floor_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        claim("candidate-alpha", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="memory_score"):
        claim("candidate-alpha", memory_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="claim_support_score"):
        claim("candidate-alpha", claim_support_score=d("1.000001"))
    with pytest.raises(ValueError, match="watch_margin"):
        config(watch_margin=d("-0.000001"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(claim("candidate-alpha"), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")

    for item in (report, *report.rows):
        for field_name, value in item.__dict__.items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field_name
            assert type(value) is not float, field_name


def test_static_module_surface_is_readonly_report_only_and_decimal_only() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_strategy_source_memory_claim_floor_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests.",
        "urllib",
        "sqlite",
        "psycopg",
        "subprocess",
        "socket",
        "open(",
        "db",
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "live trading",
        "sizing",
        "recommendation",
        "private_key",
        "api_key",
        "secret",
        "token",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
    assert not re.search(r"\b(requests|urllib|sqlite|psycopg|socket)\b", lowered)


def _contains_float_or_int(value: object) -> bool:
    if isinstance(value, float) or type(value) is int:
        return True
    if isinstance(value, dict):
        return any(_contains_float_or_int(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float_or_int(item) for item in value)
    return False
