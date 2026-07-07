from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_domain_expert_review_queue import (
    DOMAINS,
    ResearchDomainExpertReviewQueueConfig,
    ResearchDomainExpertReviewQueueInput,
    build_research_domain_expert_review_queue,
    research_domain_expert_review_queue_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def domain_input(
    *,
    packet_id: str,
    market_id: str,
    domain: str,
    question: str,
    evidence_gap_codes: tuple[str, ...] = (),
    latest_evidence_at: datetime | None = GENERATED_AT - timedelta(minutes=10),
    conflict_strength: Decimal = d("0.000000"),
) -> ResearchDomainExpertReviewQueueInput:
    return ResearchDomainExpertReviewQueueInput(
        packet_id=packet_id,
        market_id=market_id,
        domain=domain,
        question=question,
        evidence_gap_codes=evidence_gap_codes,
        latest_evidence_at=latest_evidence_at,
        conflict_strength=conflict_strength,
    )


def test_builds_pass_watch_block_expert_review_queue() -> None:
    report = build_research_domain_expert_review_queue(
        (
            domain_input(
                packet_id="packet-politics",
                market_id="market-politics",
                domain="politics",
                question="Will the certified election margin exceed the threshold?",
            ),
            domain_input(
                packet_id="packet-btc",
                market_id="market-btc",
                domain="btc",
                question="Will BTC settle above the reference level?",
                evidence_gap_codes=("missing_onchain_source",),
                latest_evidence_at=GENERATED_AT - timedelta(hours=2),
                conflict_strength=d("0.200000"),
            ),
            domain_input(
                packet_id="packet-soccer",
                market_id="market-soccer",
                domain="soccer",
                question="Will the home team qualify after the second leg?",
                evidence_gap_codes=(
                    "missing_official_source",
                    "missing_lineup_report",
                    "missing_injury_report",
                ),
                latest_evidence_at=None,
                conflict_strength=d("0.850000"),
            ),
        ),
        config=ResearchDomainExpertReviewQueueConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.status == "block"
    assert report.candidate_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.domain_count == d("3")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.review_status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.priority_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert report.rows[0].domain == "soccer"
    assert report.rows[0].evidence_gap_count == d("3")
    assert report.rows[0].evidence_age_seconds is None
    assert report.rows[0].recency_status == "missing"
    assert report.rows[0].conflict_status == "high"
    assert "evidence_missing" in report.rows[0].review_reason_codes
    assert "source_conflict_block" in report.rows[0].review_reason_codes
    assert report.rows[1].review_status == "watch"
    assert report.rows[1].recency_status == "stale"
    assert report.rows[2].review_status == "pass"
    assert report.rows[2].recency_status == "current"


def test_all_supported_domains_can_be_reported_as_pass() -> None:
    report = build_research_domain_expert_review_queue(
        tuple(
            domain_input(
                packet_id=f"packet-{domain}",
                market_id=f"market-{domain}",
                domain=domain,
                question=f"Will the {domain} reference event resolve as stated?",
            )
            for domain in DOMAINS
        ),
        config=ResearchDomainExpertReviewQueueConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.status == "pass"
    assert report.candidate_count == d("6")
    assert report.pass_count == d("6")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.domain_count == d("6")
    assert tuple(row.domain for row in report.rows) == DOMAINS


def test_payload_is_public_safe_and_has_no_float_values() -> None:
    report = build_research_domain_expert_review_queue(
        (
            domain_input(
                packet_id="packet-gold",
                market_id="market-gold",
                domain="gold",
                question="Will the gold reference fixing exceed the threshold?",
            ),
        ),
        config=ResearchDomainExpertReviewQueueConfig(),
        generated_at=GENERATED_AT,
    )

    payload = research_domain_expert_review_queue_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["conflict_strength"] == "0.000000"
    assert _has_no_float_values(payload)
    assert _has_no_unsafe_public_terms(payload)


def test_dataclasses_are_frozen_and_require_exact_public_types() -> None:
    config = ResearchDomainExpertReviewQueueConfig()
    row_input = domain_input(
        packet_id="packet-basketball",
        market_id="market-basketball",
        domain="basketball",
        question="Will the away team win the listed basketball game?",
    )

    assert is_dataclass(config)
    assert is_dataclass(row_input)
    with pytest.raises(FrozenInstanceError):
        row_input.domain = "soccer"  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        ResearchDomainExpertReviewQueueInput(
            packet_id="packet-btc",
            market_id="market-btc",
            domain="btc",
            question="Will BTC settle above the reference level?",
            evidence_gap_codes=(),
            latest_evidence_at=GENERATED_AT,
            conflict_strength=0.5,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="known domain"):
        domain_input(
            packet_id="packet-unknown",
            market_id="market-unknown",
            domain="tennis",
            question="Will the listed event resolve?",
        )


def test_public_payload_rejects_unsafe_keys_and_values() -> None:
    with pytest.raises(ValueError, match="unsafe public key"):
        research_domain_expert_review_queue_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_hint": "redacted",
            },
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        domain_input(
            packet_id="packet-unsafe",
            market_id="market-unsafe",
            domain="politics",
            question="Should a user buy this outcome?",
        )


def test_report_rejects_network_or_execution_surfaces() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/research_domain_expert_review_queue.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    imported_roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )

    assert imported_roots.isdisjoint(
        {
            "asyncio",
            "httpx",
            "pathlib",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "urllib",
        },
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "print", "__import__"}
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)


def _has_no_float_values(value: Any) -> bool:
    if isinstance(value, float):
        return False
    if isinstance(value, dict):
        return all(_has_no_float_values(item) for item in value.values())
    if isinstance(value, list):
        return all(_has_no_float_values(item) for item in value)
    return True


def _has_no_unsafe_public_terms(value: Any) -> bool:
    unsafe_terms = ("auth", "wallet", "order", "database", "network", "buy", "sell", "trade")
    if isinstance(value, str):
        lowered = value.lower()
        return all(term not in lowered for term in unsafe_terms)
    if isinstance(value, dict):
        return all(
            _has_no_unsafe_public_terms(str(key)) and _has_no_unsafe_public_terms(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return all(_has_no_unsafe_public_terms(item) for item in value)
    return True
