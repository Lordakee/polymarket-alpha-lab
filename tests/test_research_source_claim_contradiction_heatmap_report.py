from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_claim_contradiction_heatmap_report"
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(**overrides: object) -> Any:
    module = api()
    values = {
        "candidate_id": "cand-alpha",
        "market_id": "mkt-alpha",
        "market_slug": "will-fed-cut-july",
        "market_question": "Will the central bank change rates in July?",
        "claim_family": "macro_policy",
        "source_family": "official_release",
        "authority_tier": "primary",
        "freshness_bucket": "current",
        "contradiction_pressure": d("0.050000"),
        "reviewer_verified": True,
        "raw_source_locator": "https://example.test/feed?token=secret",
        "raw_source_excerpt": "Internal evidence text that must stay private.",
    }
    values.update(overrides)
    return module.ResearchSourceClaimContradictionEvidence(**values)


def report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_claim_contradiction_heatmap_report(
        items,
        config=cfg or module.ResearchSourceClaimContradictionHeatmapConfig(),
        generated_at=GENERATED_AT,
    )


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def with_recomputed_digest(payload: dict[str, Any]) -> dict[str, Any]:
    values = dict(payload)
    values.pop("validation_digest", None)
    encoded = json.dumps(
        values,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return {
        **payload,
        "validation_digest": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
    }


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool:
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)


def assert_no_float_or_int_values(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_heatmap_aggregates_claim_family_pressure_deterministically() -> None:
    inputs = (
        evidence(
            candidate_id="cand-pass-a",
            market_id="mkt-pass",
            market_slug="macro-pass",
            claim_family="macro_policy",
            source_family="official_release",
            authority_tier="primary",
            freshness_bucket="current",
            contradiction_pressure=d("0.050000"),
            reviewer_verified=True,
        ),
        evidence(
            candidate_id="cand-pass-b",
            market_id="mkt-pass",
            market_slug="macro-pass",
            claim_family="macro_policy",
            source_family="wire_summary",
            authority_tier="secondary",
            freshness_bucket="current",
            contradiction_pressure=d("0.100000"),
            reviewer_verified=True,
        ),
        evidence(
            candidate_id="cand-watch-a",
            market_id="mkt-watch",
            market_slug="earnings-watch",
            claim_family="earnings_guidance",
            source_family="filing",
            authority_tier="primary",
            freshness_bucket="recent",
            contradiction_pressure=d("0.400000"),
            reviewer_verified=True,
        ),
        evidence(
            candidate_id="cand-watch-b",
            market_id="mkt-watch",
            market_slug="earnings-watch",
            claim_family="earnings_guidance",
            source_family="analyst_note",
            authority_tier="secondary",
            freshness_bucket="stale",
            contradiction_pressure=d("0.200000"),
            reviewer_verified=False,
        ),
        evidence(
            candidate_id="cand-block-a",
            market_id="mkt-block",
            market_slug="election-block",
            market_question="Will a private market question leak?",
            claim_family="election_integrity",
            source_family="official_release",
            authority_tier="primary",
            freshness_bucket="recent",
            contradiction_pressure=d("0.800000"),
            reviewer_verified=False,
        ),
        evidence(
            candidate_id="cand-block-b",
            market_id="mkt-block",
            market_slug="election-block",
            claim_family="election_integrity",
            source_family="local_report",
            authority_tier="secondary",
            freshness_bucket="stale",
            contradiction_pressure=d("0.650000"),
            reviewer_verified=False,
        ),
        evidence(
            candidate_id="cand-block-c",
            market_id="mkt-block",
            market_slug="election-block",
            claim_family="election_integrity",
            source_family="community_summary",
            authority_tier="tertiary",
            freshness_bucket="current",
            contradiction_pressure=d("0.450000"),
            reviewer_verified=True,
        ),
    )
    result = report(*inputs)

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-source-claim-contradiction-heatmap-v1"
    assert result.evidence_count == d("7")
    assert result.claim_family_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.status == "block"
    assert result.reason_codes == (
        "contradiction_pressure_block",
        "contradiction_pressure_watch",
        "cross_source_family_pressure",
        "high_authority_contradiction",
        "reviewer_verification_gap_watch",
        "stale_evidence_contradiction",
        "claim_family_pressure_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.claim_family for row in result.claim_family_rows) == (
        "election_integrity",
        "earnings_guidance",
        "macro_policy",
    )

    blocked = result.claim_family_rows[0]
    assert blocked.evidence_count == d("3")
    assert blocked.source_family_count == d("3")
    assert blocked.authority_tier_count == d("3")
    assert blocked.freshness_bucket_count == d("3")
    assert blocked.reviewer_verified_count == d("1")
    assert blocked.reviewer_verification_ratio == d("0.333333")
    assert blocked.average_contradiction_pressure == d("0.633333")
    assert blocked.max_contradiction_pressure == d("0.800000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "contradiction_pressure_block",
        "cross_source_family_pressure",
        "high_authority_contradiction",
        "stale_evidence_contradiction",
    )
    assert_digest(blocked.validation_digest)

    watched = result.claim_family_rows[1]
    assert watched.average_contradiction_pressure == d("0.300000")
    assert watched.reviewer_verification_ratio == d("0.500000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "contradiction_pressure_watch",
        "cross_source_family_pressure",
        "high_authority_contradiction",
        "reviewer_verification_gap_watch",
        "stale_evidence_contradiction",
    )

    passed = result.claim_family_rows[2]
    assert passed.average_contradiction_pressure == d("0.075000")
    assert passed.reviewer_verification_ratio == d("1.000000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("claim_family_pressure_pass",)

    assert result.source_family_rollups[0].source_family == "official_release"
    assert result.source_family_rollups[0].evidence_count == d("2")
    assert result.source_family_rollups[0].max_contradiction_pressure == d("0.800000")
    assert result.authority_tier_rollups[0].authority_tier == "primary"
    assert result.authority_tier_rollups[0].evidence_count == d("3")
    assert result.freshness_bucket_rollups[0].freshness_bucket == "stale"
    assert result.freshness_bucket_rollups[0].average_contradiction_pressure == d("0.425000")
    assert result.reviewer_verification_rollups[0].reviewer_verification_bucket == "unverified"
    assert result.reviewer_verification_rollups[0].evidence_count == d("3")

    same_result = report(*reversed(inputs))
    assert same_result.validation_digest == result.validation_digest


def test_empty_report_is_report_only_blocked_and_digest_validated() -> None:
    result = report()

    assert result.evidence_count == d("0")
    assert result.claim_family_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.status == "block"
    assert result.reason_codes == (
        "research_source_claim_contradiction_heatmap_empty",
    )
    assert result.claim_family_rows == ()
    assert result.source_family_rollups == ()
    assert result.authority_tier_rollups == ()
    assert result.freshness_bucket_rollups == ()
    assert result.reviewer_verification_rollups == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)


def test_public_payload_is_json_ready_and_hides_raw_surfaces() -> None:
    module = api()
    item = evidence(
        candidate_id="cand-secret-alpha",
        market_id="mkt-secret-alpha",
        market_slug="secret-market-slug",
        market_question="Will the hidden market resolve yes?",
        raw_source_locator="https://example.test/private/path?token=secret",
        raw_source_excerpt="Full private source text should never be public.",
    )
    result = report(item)

    payload = module.research_source_claim_contradiction_heatmap_report_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["evidence_count"] == "1"
    assert payload["claim_family_rows"][0]["claim_family"] == "macro_policy"
    assert payload["claim_family_rows"][0]["validation_digest"] == (
        result.claim_family_rows[0].validation_digest
    )
    assert "candidate_id" not in encoded
    assert "cand-secret-alpha" not in encoded
    assert "market_id" not in encoded
    assert "market_slug" not in encoded
    assert "secret-market-slug" not in encoded
    assert "market_question" not in encoded
    assert "hidden market resolve" not in encoded
    assert "raw_source_locator" not in encoded
    assert "raw_source_excerpt" not in encoded
    assert "token=secret" not in encoded
    assert "private source text" not in encoded
    assert_no_float_or_int_values(payload)
    assert module.research_source_claim_contradiction_heatmap_report_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly"):
        module.research_source_claim_contradiction_heatmap_report_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.research_source_claim_contradiction_heatmap_report_payload(
            {**payload, "wallet": {"address": "0x0"}},
        )

    with pytest.raises(ValueError, match="numeric"):
        module.research_source_claim_contradiction_heatmap_report_payload(
            {**payload, "evidence_count": 1},
        )

    with pytest.raises(ValueError, match="numeric"):
        module.research_source_claim_contradiction_heatmap_report_payload(
            {**payload, "block_count": 1.0},
        )


def test_public_payload_rejects_tampered_statuses_digests_and_extra_fields() -> None:
    module = api()
    payload = module.research_source_claim_contradiction_heatmap_report_payload(
        report(evidence()),
    )

    with pytest.raises(ValueError, match="status"):
        module.research_source_claim_contradiction_heatmap_report_payload(
            {**payload, "status": "blocked"},
        )

    tampered_rows = [dict(payload["claim_family_rows"][0], status="blocked")]
    with pytest.raises(ValueError, match="status"):
        module.research_source_claim_contradiction_heatmap_report_payload(
            {**payload, "claim_family_rows": tampered_rows},
        )

    with pytest.raises(ValueError, match="validation_digest"):
        module.research_source_claim_contradiction_heatmap_report_payload(
            {**payload, "validation_digest": "0" * 64},
        )

    with pytest.raises(ValueError, match="unexpected public payload field"):
        module.research_source_claim_contradiction_heatmap_report_payload(
            {**payload, "notes": "nonpublic-alias"},
        )


def test_public_payload_rejects_recomputed_digest_semantic_tampering() -> None:
    module = api()
    payload = module.research_source_claim_contradiction_heatmap_report_payload(
        report(evidence()),
    )

    tampered_summary = with_recomputed_digest(
        {
            **payload,
            "average_contradiction_pressure": "0.900000",
        },
    )
    with pytest.raises(ValueError, match="average_contradiction_pressure"):
        module.research_source_claim_contradiction_heatmap_report_payload(
            tampered_summary,
        )

    tampered_row = with_recomputed_digest(
        {
            **payload["claim_family_rows"][0],
            "reviewer_verified_count": "0",
        },
    )
    tampered_rows_payload = with_recomputed_digest(
        {
            **payload,
            "claim_family_rows": [tampered_row],
        },
    )
    with pytest.raises(ValueError, match="reviewer counts"):
        module.research_source_claim_contradiction_heatmap_report_payload(
            tampered_rows_payload,
        )

    tampered_rollup = with_recomputed_digest(
        {
            **payload["source_family_rollups"][0],
            "reviewer_verified_count": "0",
        },
    )
    tampered_rollup_payload = with_recomputed_digest(
        {
            **payload,
            "source_family_rollups": [tampered_rollup],
        },
    )
    with pytest.raises(ValueError, match="reviewer_verification_ratio"):
        module.research_source_claim_contradiction_heatmap_report_payload(
            tampered_rollup_payload,
        )

    tampered_rollup_average = with_recomputed_digest(
        {
            **payload["source_family_rollups"][0],
            "average_contradiction_pressure": "0.040000",
        },
    )
    tampered_rollup_average_payload = with_recomputed_digest(
        {
            **payload,
            "source_family_rollups": [tampered_rollup_average],
        },
    )
    with pytest.raises(
        ValueError,
        match="source_family_rollups average_contradiction_pressure",
    ):
        module.research_source_claim_contradiction_heatmap_report_payload(
            tampered_rollup_average_payload,
        )

    missing_rollup_payload = with_recomputed_digest(
        {
            **payload,
            "source_family_rollups": [],
        },
    )
    with pytest.raises(ValueError, match="source_family_rollups"):
        module.research_source_claim_contradiction_heatmap_report_payload(
            missing_rollup_payload,
        )


def test_inputs_config_datetimes_and_tampering_are_rejected() -> None:
    module = api()

    with pytest.raises(ValueError, match="config_version must be supported"):
        module.ResearchSourceClaimContradictionHeatmapConfig(
            config_version="unsupported-config-version",
        )
    with pytest.raises(ValueError, match="contradiction_pressure must be a Decimal"):
        evidence(contradiction_pressure=0.5)
    with pytest.raises(ValueError, match="contradiction_pressure must be between 0 and 1"):
        evidence(contradiction_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="reviewer_verified must be a bool"):
        evidence(reviewer_verified=1)
    with pytest.raises(ValueError, match="paper_only must be True"):
        evidence(paper_only=False)
    with pytest.raises(ValueError, match="watch threshold must not exceed block threshold"):
        module.ResearchSourceClaimContradictionHeatmapConfig(
            contradiction_pressure_watch_threshold=d("0.800000"),
            contradiction_pressure_block_threshold=d("0.600000"),
        )
    with pytest.raises(ValueError, match="verification block floor must not exceed"):
        module.ResearchSourceClaimContradictionHeatmapConfig(
            reviewer_verification_block_floor=d("0.700000"),
            reviewer_verification_watch_floor=d("0.500000"),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_claim_contradiction_heatmap_report(
            (evidence(),),
            config=module.ResearchSourceClaimContradictionHeatmapConfig(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_claim_contradiction_heatmap_report(
            (evidence(),),
            config=module.ResearchSourceClaimContradictionHeatmapConfig(),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    result = report(evidence())
    row = result.claim_family_rows[0]
    with pytest.raises(FrozenInstanceError):
        row.status = "block"
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="block")
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="block_count must match"):
        replace(result, block_count=d("1"))
    with pytest.raises(ValueError, match="claim_family_rows must be sorted"):
        replace(
            result,
            claim_family_rows=(
                heatmap_row("zeta_claim", d("0.050000")),
                heatmap_row("alpha_claim", d("0.050000")),
            ),
        )
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)


def heatmap_row(claim_family: str, pressure: Decimal) -> Any:
    return report(
        evidence(
            candidate_id=f"cand-{claim_family}",
            claim_family=claim_family,
            contradiction_pressure=pressure,
        ),
    ).claim_family_rows[0]


def test_module_is_pure_report_only_and_contains_no_io_surfaces() -> None:
    path = Path(
        "src/polymarket_alpha_lab/"
        "research_source_claim_contradiction_heatmap_report.py",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))

    banned_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    banned_calls = {
        "connect",
        "delete",
        "execute",
        "insert",
        "login",
        "open",
        "post",
        "request",
        "send",
        "submit",
        "update",
        "urlopen",
        "write",
    }
    banned_attributes = banned_calls | {"commit", "replace", "rollback", "session"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes
