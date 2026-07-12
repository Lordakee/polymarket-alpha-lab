from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.market_candidate_information_gap_report as api
from polymarket_alpha_lab.market_candidate_information_gap_report import (
    DEFAULT_MARKET_CANDIDATE_INFORMATION_GAP_REPORT_CONFIG_VERSION,
    INFORMATION_GAP_BANDS,
    MarketCandidateInformationGapConfig,
    MarketCandidateInformationGapInput,
    MarketCandidateInformationGapReport,
    build_market_candidate_information_gap_report,
    market_candidate_information_gap_digest,
    market_candidate_information_gap_public_payload,
)


GENERATED_AT = datetime(2026, 7, 12, 8, 30, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_candidate_information_gap_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketCandidateInformationGapConfig:
    values = {
        "config_version": DEFAULT_MARKET_CANDIDATE_INFORMATION_GAP_REPORT_CONFIG_VERSION,
        "attention_score_threshold": d("0.250000"),
        "blocker_score_threshold": d("0.600000"),
        "freshness_attention_seconds": d("3600.000000"),
        "freshness_blocker_seconds": d("21600.000000"),
        "independent_source_attention_threshold": ONE,
        "independent_source_blocker_threshold": d("3.000000"),
    }
    values.update(overrides)
    return MarketCandidateInformationGapConfig(**values)


def candidate(**overrides: object) -> MarketCandidateInformationGapInput:
    values = {
        "candidate_key": "market-alpha",
        "official_source_missing": False,
        "independent_source_gap_count": ZERO,
        "freshness_gap_seconds": ZERO,
        "resolution_rule_gap": False,
        "cost_model_gap": False,
        "team_memory_gap": False,
        "operator_redaction_gap": False,
        "manual_review_required": False,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return MarketCandidateInformationGapInput(**values)


def report(
    candidate_input: MarketCandidateInformationGapInput,
    *,
    cfg: MarketCandidateInformationGapConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketCandidateInformationGapReport:
    return build_market_candidate_information_gap_report(
        candidate_input,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_gap_band_vocabulary_is_exact() -> None:
    assert INFORMATION_GAP_BANDS == ("ready", "attention", "blocker")


def test_ready_candidate_has_zero_gap_score_public_payload_and_stable_digest() -> None:
    readiness = report(candidate())

    assert is_dataclass(readiness)
    assert readiness.generated_at == GENERATED_AT
    assert readiness.config_version == (
        DEFAULT_MARKET_CANDIDATE_INFORMATION_GAP_REPORT_CONFIG_VERSION
    )
    assert readiness.information_gap_score == ZERO
    assert readiness.gap_band == "ready"
    assert readiness.blocked_reason_codes == ()
    assert readiness.attention_reason_codes == ()
    assert readiness.ready_ratio == ONE
    assert readiness.reason_codes == ("market_candidate_information_gap_ready",)
    assert readiness.public_payload == market_candidate_information_gap_public_payload(
        readiness,
    )
    assert readiness.digest == market_candidate_information_gap_digest(readiness)

    payload = readiness.public_payload
    assert payload["information_gap_score"] == "0.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)
    assert readiness.digest == market_candidate_information_gap_digest(readiness)


def test_attention_gaps_score_reasons_and_ready_ratio_are_deterministic() -> None:
    readiness = report(
        candidate(
            independent_source_gap_count=ONE,
            freshness_gap_seconds=d("7200.000000"),
            team_memory_gap=True,
        ),
    )

    assert readiness.gap_band == "attention"
    assert readiness.information_gap_score == d("0.375000")
    assert readiness.ready_ratio == d("0.625000")
    assert readiness.blocked_reason_codes == ()
    assert readiness.attention_reason_codes == (
        "independent_source_gap_attention",
        "freshness_gap_attention",
        "team_memory_gap_attention",
    )
    assert readiness.reason_codes == (
        "market_candidate_information_gap_attention",
        "independent_source_gap_attention",
        "freshness_gap_attention",
        "team_memory_gap_attention",
    )


def test_blocker_gaps_override_attention_and_manual_review_blocks() -> None:
    readiness = report(
        candidate(
            official_source_missing=True,
            independent_source_gap_count=d("4.000000"),
            freshness_gap_seconds=d("43200.000000"),
            resolution_rule_gap=True,
            cost_model_gap=True,
            team_memory_gap=True,
            operator_redaction_gap=True,
            manual_review_required=True,
        ),
    )

    assert readiness.gap_band == "blocker"
    assert readiness.information_gap_score == ONE
    assert readiness.ready_ratio == ZERO
    assert readiness.blocked_reason_codes == (
        "official_source_missing_blocker",
        "independent_source_gap_blocker",
        "freshness_gap_blocker",
        "resolution_rule_gap_blocker",
        "operator_redaction_gap_blocker",
        "manual_review_required_blocker",
    )
    assert readiness.attention_reason_codes == (
        "cost_model_gap_attention",
        "team_memory_gap_attention",
    )
    assert readiness.reason_codes == (
        "market_candidate_information_gap_blocker",
        "official_source_missing_blocker",
        "independent_source_gap_blocker",
        "freshness_gap_blocker",
        "resolution_rule_gap_blocker",
        "operator_redaction_gap_blocker",
        "manual_review_required_blocker",
        "cost_model_gap_attention",
        "team_memory_gap_attention",
    )


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    readiness = report(candidate())

    with pytest.raises(FrozenInstanceError):
        readiness.gap_band = "blocker"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(MarketCandidateInformationGapInput):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        MarketCandidateInformationGapConfig(paper_only=False)

    with pytest.raises(ValueError, match="independent_source_gap_count must be a Decimal"):
        candidate(independent_source_gap_count=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="independent_source_gap_count must be an integer"):
        candidate(independent_source_gap_count=d("1.500000"))

    with pytest.raises(ValueError, match="freshness_gap_seconds must be nonnegative"):
        candidate(freshness_gap_seconds=d("-1.000000"))

    with pytest.raises(ValueError, match="manual_review_required must be a bool"):
        candidate(manual_review_required=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="readonly"):
        candidate(readonly=False)

    with pytest.raises(ValueError, match="blocked_reason_codes must match gap inputs"):
        MarketCandidateInformationGapReport(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_MARKET_CANDIDATE_INFORMATION_GAP_REPORT_CONFIG_VERSION,
            attention_score_threshold=d("0.250000"),
            blocker_score_threshold=d("0.600000"),
            candidate_key="market-alpha",
            official_source_missing=True,
            independent_source_gap_count=ZERO,
            freshness_gap_seconds=ZERO,
            freshness_attention_seconds=d("3600.000000"),
            freshness_blocker_seconds=d("21600.000000"),
            independent_source_attention_threshold=ONE,
            independent_source_blocker_threshold=d("3.000000"),
            resolution_rule_gap=False,
            cost_model_gap=False,
            team_memory_gap=False,
            operator_redaction_gap=False,
            manual_review_required=False,
            information_gap_score=d("0.500000"),
            gap_band="blocker",
            blocked_reason_codes=(),
            attention_reason_codes=(),
            reason_codes=("market_candidate_information_gap_blocker",),
            ready_ratio=d("0.500000"),
        )


def test_config_validates_threshold_ordering() -> None:
    with pytest.raises(ValueError, match="blocker_score_threshold"):
        config(
            attention_score_threshold=d("0.700000"),
            blocker_score_threshold=d("0.600000"),
        )

    with pytest.raises(ValueError, match="freshness_blocker_seconds"):
        config(
            freshness_attention_seconds=d("7200.000000"),
            freshness_blocker_seconds=d("3600.000000"),
        )

    with pytest.raises(ValueError, match="independent_source_blocker_threshold"):
        config(
            independent_source_attention_threshold=d("3.000000"),
            independent_source_blocker_threshold=d("2.000000"),
        )


def test_report_validation_preserves_custom_threshold_context() -> None:
    readiness = report(
        candidate(
            independent_source_gap_count=ONE,
            freshness_gap_seconds=d("7200.000000"),
        ),
        cfg=config(
            freshness_attention_seconds=d("10800.000000"),
            freshness_blocker_seconds=d("21600.000000"),
            independent_source_attention_threshold=d("2.000000"),
            independent_source_blocker_threshold=d("5.000000"),
        ),
    )

    assert readiness.gap_band == "ready"
    assert readiness.information_gap_score == ZERO
    assert readiness.attention_reason_codes == ()
    assert readiness.reason_codes == ("market_candidate_information_gap_ready",)


def test_custom_score_threshold_context_allows_attention_only_blocker_band() -> None:
    readiness = report(
        candidate(
            independent_source_gap_count=ONE,
            freshness_gap_seconds=d("7200.000000"),
            cost_model_gap=True,
            team_memory_gap=True,
        ),
        cfg=config(blocker_score_threshold=d("0.500000")),
    )

    assert readiness.gap_band == "blocker"
    assert readiness.information_gap_score == d("0.500000")
    assert readiness.blocked_reason_codes == ()
    assert readiness.attention_reason_codes == (
        "independent_source_gap_attention",
        "freshness_gap_attention",
        "cost_model_gap_attention",
        "team_memory_gap_attention",
    )


def test_public_api_excludes_live_trading_auth_wallet_database_and_network_surfaces() -> None:
    forbidden_fragments = (
        "auth",
        "wallet",
        "order",
        "trade",
        "broker",
        "position",
        "database",
        "db",
        "network",
        "http",
        "socket",
        "request",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        MarketCandidateInformationGapConfig,
        MarketCandidateInformationGapInput,
        MarketCandidateInformationGapReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

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
    ):
        assert not hasattr(api, forbidden_name)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "web3",
            "ccxt",
        },
    )
