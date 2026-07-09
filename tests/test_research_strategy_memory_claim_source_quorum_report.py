from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_memory_claim_source_quorum_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "research-strategy-memory-claim-source-quorum-report-test",
        "minimum_source_count": d("3.000000"),
        "minimum_independent_source_count": d("2.000000"),
        "minimum_support_ratio": d("0.800000"),
        "minimum_confidence_score": d("0.700000"),
        "watch_confidence_floor": d("0.500000"),
        "maximum_contradiction_ratio": d("0.250000"),
    }
    values.update(overrides)
    return module.ResearchStrategyMemoryClaimSourceQuorumReportConfig(**values)


def claim(**overrides: object) -> Any:
    module = api()
    values = {
        "raw_candidate": "candidate-private-alpha",
        "raw_market": "market-private-alpha",
        "raw_claim": "claim text private alpha",
        "raw_source_refs": (
            "https://example.invalid/alpha?secret_token=alpha",
            "warehouse://private_dsn/private_table_alpha",
            "source text excerpt alpha",
        ),
        "source_family_refs": ("primary", "research", "archive"),
        "observed_at": OBSERVED_AT,
        "source_count": d("3.000000"),
        "independent_source_count": d("3.000000"),
        "contradicting_source_count": d("0.000000"),
        "confidence_score": d("0.900000"),
    }
    values.update(overrides)
    return module.ResearchStrategyMemoryClaimSourceQuorumClaim(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_strategy_memory_claim_source_quorum_report(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def assert_no_float_or_int(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)
        return
    assert type(value) not in (float, int)


def test_source_quorum_statuses_and_decimal_report_rollups() -> None:
    report = build_report(
        claim(raw_candidate="candidate-pass"),
        claim(
            raw_candidate="candidate-watch",
            raw_claim="claim text private watch",
            raw_source_refs=(
                "https://example.invalid/watch?secret_token=watch",
                "source text excerpt watch",
            ),
            source_family_refs=("primary", "research"),
            source_count=d("2.000000"),
            independent_source_count=d("2.000000"),
            confidence_score=d("0.650000"),
        ),
        claim(
            raw_candidate="candidate-block",
            raw_claim="claim text private block",
            raw_source_refs=(
                "https://example.invalid/block?secret_token=block",
                "warehouse://private_dsn/private_table_block",
                "source text excerpt block",
            ),
            source_family_refs=("primary", "research", "archive"),
            source_count=d("3.000000"),
            independent_source_count=d("1.000000"),
            contradicting_source_count=d("1.000000"),
            confidence_score=d("0.300000"),
        ),
    )

    rows = {row.status: row for row in report.rows}
    assert rows["pass"].source_quorum_score == d("0.975000")
    assert rows["pass"].support_ratio == d("1.000000")
    assert rows["pass"].reason_codes == ("source_quorum_pass",)

    assert rows["watch"].source_quorum_score == d("0.779167")
    assert rows["watch"].support_ratio == d("1.000000")
    assert rows["watch"].reason_codes == (
        "source_quorum_watch",
        "thin_source_count",
        "low_confidence_score",
    )

    assert rows["block"].source_quorum_score == d("0.429167")
    assert rows["block"].support_ratio == d("0.666667")
    assert rows["block"].reason_codes == (
        "source_quorum_block",
        "thin_independent_sources",
        "high_contradiction_ratio",
        "low_confidence_score",
    )

    assert report.status == "block"
    assert report.claim_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_source_quorum_score == d("0.727778")

    for item in (cfg(), *report.rows, report):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if field.name.endswith(("_count", "_ratio", "_score")):
                assert type(value) is Decimal


def test_public_payload_is_canonical_deterministic_and_redacted() -> None:
    module = api()
    alpha = claim(raw_candidate="candidate-alpha-secret")
    beta = claim(
        raw_candidate="candidate-beta-secret",
        raw_market="market-beta-secret",
        raw_claim="claim text private beta",
        raw_source_refs=(
            "https://example.invalid/beta?secret_token=beta",
            "warehouse://private_dsn/private_table_beta",
            "source text excerpt beta",
        ),
    )

    payload = module.research_strategy_memory_claim_source_quorum_report_payload(
        build_report(beta, alpha),
    )
    reordered_payload = module.research_strategy_memory_claim_source_quorum_report_payload(
        build_report(alpha, beta),
    )

    assert payload == reordered_payload
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["claim_count"] == "2.000000"
    assert payload["rows"][0]["source_quorum_score"] == "0.975000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    material = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    expected_digest = sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert payload["derived_validation_digest"] == expected_digest
    assert module.validate_research_strategy_memory_claim_source_quorum_report_payload(
        payload,
    )
    assert_no_float_or_int(payload)
    json.dumps(payload, sort_keys=True)

    public_json = json.dumps(payload, sort_keys=True)
    for raw_value in (
        "candidate-alpha-secret",
        "candidate-beta-secret",
        "market-beta-secret",
        "claim text private beta",
        "https://example.invalid/beta?secret_token=beta",
        "warehouse://private_dsn/private_table_beta",
        "source text excerpt beta",
    ):
        assert raw_value not in public_json

    assert set(payload["rows"][0]) == {
        "claim_digest",
        "source_bundle_digest",
        "observed_at",
        "source_count",
        "independent_source_count",
        "contradicting_source_count",
        "support_ratio",
        "confidence_score",
        "source_quorum_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    }


def test_dataclasses_are_frozen_final_and_decimal_only() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_MEMORY_CLAIM_SOURCE_QUORUM_REPORT_VERSION",
        "ResearchStrategyMemoryClaimSourceQuorumReportConfig",
        "ResearchStrategyMemoryClaimSourceQuorumClaim",
        "ResearchStrategyMemoryClaimSourceQuorumRow",
        "ResearchStrategyMemoryClaimSourceQuorumReport",
        "build_research_strategy_memory_claim_source_quorum_report",
        "research_strategy_memory_claim_source_quorum_report_payload",
        "validate_research_strategy_memory_claim_source_quorum_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(claim())
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.ResearchStrategyMemoryClaimSourceQuorumReportConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeClaim(module.ResearchStrategyMemoryClaimSourceQuorumClaim):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.ResearchStrategyMemoryClaimSourceQuorumRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.ResearchStrategyMemoryClaimSourceQuorumReport):
            pass

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        claim(source_count=DecimalSubclass("3.000000"))
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        claim(source_count=3)


def test_hard_flags_statuses_and_digest_tampering_are_rejected() -> None:
    module = api()
    with pytest.raises(ValueError, match="paper_only must be True"):
        claim(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)

    report = build_report(claim())
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report.rows[0], status="ready")
    with pytest.raises(ValueError, match="claim_count"):
        replace(report, claim_count=d("2.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.research_strategy_memory_claim_source_quorum_report_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["claim_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_strategy_memory_claim_source_quorum_report_payload(
            tampered_payload,
        )

    raw_key_payload = dict(payload)
    raw_key_payload["raw_candidate"] = "candidate-private-alpha"
    with pytest.raises(ValueError, match="unexpected public payload key"):
        module.validate_research_strategy_memory_claim_source_quorum_report_payload(
            raw_key_payload,
        )


def test_module_omits_runtime_surfaces_and_unsafe_public_names() -> None:
    module = api()
    public_names = set(module.__all__) | {
        name for name in dir(module) if not name.startswith("_")
    }
    forbidden_fragments = (
        "requests",
        "urllib",
        "http.client",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "subprocess",
        "Path(",
        "open(",
        ".write(",
        ".read(",
        "db",
        "".join(("net", "work")),
        "".join(("wall", "et")),
        "".join(("au", "th")),
        "".join(("or", "der")),
        "live trading",
        "".join(("siz", "ing")),
        "".join(("recommend", "ation")),
    )

    for public_name in public_names:
        lower_name = public_name.lower()
        for fragment in forbidden_fragments:
            assert fragment.lower() not in lower_name

    source = inspect.getsource(module).lower()
    for fragment in forbidden_fragments:
        assert fragment.lower() not in source
