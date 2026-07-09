from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_claim_review_memory_score_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "memory_hit_rate_weight": d("0.300000"),
        "correction_rate_weight": d("0.200000"),
        "memory_freshness_weight": d("0.200000"),
        "reviewer_alignment_weight": d("0.200000"),
        "unresolved_resolution_weight": d("0.100000"),
        "memory_age_watch_seconds": d("1209600.000000"),
        "memory_age_block_seconds": d("2592000.000000"),
        "memory_hit_rate_watch_below": d("0.600000"),
        "memory_hit_rate_block_below": d("0.300000"),
        "correction_rate_watch_below": d("0.600000"),
        "correction_rate_block_below": d("0.300000"),
        "reviewer_alignment_watch_below": d("0.750000"),
        "reviewer_alignment_block_below": d("0.500000"),
        "unresolved_pressure_watch_ratio": d("0.250000"),
        "unresolved_pressure_block_ratio": d("0.500000"),
        "stale_memory_watch_ratio": d("0.250000"),
        "stale_memory_block_ratio": d("0.500000"),
        "memory_score_watch_threshold": d("0.700000"),
        "memory_score_block_threshold": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainClaimReviewMemoryScoreConfig(**values)


def review_input(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "domain_key": "politics",
        "team_key": "policy_team",
        "claim_review_reference": (
            "candidate-123 market_id market_slug question text "
            "https://example.invalid/path?token=secret"
        ),
        "reviewed_at": GENERATED_AT - timedelta(hours=2),
        "memory_observed_at": GENERATED_AT - timedelta(days=1),
        "claim_review_count": d("10.000000"),
        "memory_hit_count": d("9.000000"),
        "corrected_claim_review_count": d("8.000000"),
        "unresolved_claim_review_count": d("0.000000"),
        "stale_memory_count": d("0.000000"),
        "reviewer_alignment_score": d("0.900000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchTeamDomainClaimReviewMemoryScoreInput(**values)


def build_report(*items: object, cfg: object | None = None, generated_at=GENERATED_AT):
    module = api()
    return module.build_research_team_domain_claim_review_memory_score_report(
        items,
        generated_at=generated_at,
        config=cfg or config(),
    )


def test_empty_input_blocks_with_report_only_digest_and_decimal_payload() -> None:
    built = build_report()

    assert is_dataclass(built)
    assert built.generated_at == GENERATED_AT
    assert built.report_status == "block"
    assert built.input_count == d("0.000000")
    assert built.row_count == d("0.000000")
    assert built.pass_count == d("0.000000")
    assert built.watch_count == d("0.000000")
    assert built.block_count == d("0.000000")
    assert built.average_memory_score == d("0.000000")
    assert built.rows == ()
    assert built.reason_codes == ("domain_claim_review_memory_score_empty",)
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    payload = api().research_team_domain_claim_review_memory_score_public_payload(built)
    assert payload == built.public_payload
    assert payload["input_count"] == "0.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert api().research_team_domain_claim_review_memory_score_report_digest(built) == (
        payload["derived_validation_digest"]
    )
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert not any(type(value) is float for value in _walk_payload_values(payload))


def test_claim_review_memory_scores_pass_watch_block_rows_deterministically() -> None:
    built = build_report(
        review_input(
            domain_key="sports",
            team_key="tennis_team",
            claim_review_reference="sports-memory-review",
            memory_observed_at=GENERATED_AT - timedelta(days=16),
            memory_hit_count=d("5.000000"),
            corrected_claim_review_count=d("6.000000"),
            unresolved_claim_review_count=d("3.000000"),
            stale_memory_count=d("3.000000"),
            reviewer_alignment_score=d("0.700000"),
        ),
        review_input(
            domain_key="crypto",
            team_key="chain_team",
            claim_review_reference="crypto-memory-review",
            memory_observed_at=GENERATED_AT - timedelta(days=35),
            memory_hit_count=d("2.000000"),
            corrected_claim_review_count=d("2.000000"),
            unresolved_claim_review_count=d("6.000000"),
            stale_memory_count=d("6.000000"),
            reviewer_alignment_score=d("0.300000"),
        ),
        review_input(
            domain_key="politics",
            team_key="policy_team",
            claim_review_reference="politics-memory-review",
        ),
    )

    assert built.report_status == "block"
    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.average_memory_score == d("0.558889")
    assert built.min_memory_score == d("0.200000")
    assert built.max_unresolved_pressure == d("0.600000")
    assert built.oldest_memory_age_seconds == d("3024000.000000")

    crypto_row, sports_row, politics_row = built.rows
    assert tuple(row.memory_rank for row in built.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert (crypto_row.domain_key, sports_row.domain_key, politics_row.domain_key) == (
        "crypto",
        "sports",
        "politics",
    )

    assert crypto_row.memory_status == "block"
    assert crypto_row.memory_age_seconds == d("3024000.000000")
    assert crypto_row.memory_freshness_score == d("0.000000")
    assert crypto_row.memory_hit_rate == d("0.200000")
    assert crypto_row.correction_rate == d("0.200000")
    assert crypto_row.unresolved_pressure == d("0.600000")
    assert crypto_row.stale_memory_pressure == d("0.600000")
    assert crypto_row.memory_score == d("0.200000")
    assert crypto_row.reason_codes == (
        "memory_age_block",
        "memory_hit_rate_block",
        "correction_rate_block",
        "reviewer_alignment_block",
        "unresolved_pressure_block",
        "stale_memory_pressure_block",
        "memory_score_block",
    )

    assert sports_row.memory_status == "watch"
    assert sports_row.memory_age_seconds == d("1382400.000000")
    assert sports_row.memory_freshness_score == d("0.466667")
    assert sports_row.memory_score == d("0.573333")
    assert sports_row.reason_codes == (
        "memory_age_watch",
        "memory_hit_rate_watch",
        "reviewer_alignment_watch",
        "unresolved_pressure_watch",
        "stale_memory_pressure_watch",
        "memory_score_watch",
    )

    assert politics_row.memory_status == "pass"
    assert politics_row.memory_score == d("0.903333")
    assert politics_row.reason_codes == ("domain_claim_review_memory_score_pass",)
    assert all(len(row.claim_review_digest) == 64 for row in built.rows)
    assert all(set(row.claim_review_digest) <= set("0123456789abcdef") for row in built.rows)


def test_payload_digest_validation_rejects_tampering_and_sensitive_public_surfaces() -> None:
    built = build_report(
        review_input(
            claim_review_reference=(
                "candidate-999 market_id market_slug question text "
                "https://example.invalid/path?token=secret dsn://warehouse/table "
                "wallet order trade live sizing recommendation"
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    payload = built.public_payload
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    api().validate_research_team_domain_claim_review_memory_score_public_payload(payload)
    for forbidden in (
        "candidate-999",
        "market_id",
        "market_slug",
        "question text",
        "https://example.invalid",
        "token=secret",
        "dsn://warehouse",
        "table",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in serialized

    tampered = dict(payload)
    tampered["rows"] = [dict(payload["rows"][0], memory_score="0.999999")]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api().research_team_domain_claim_review_memory_score_public_payload(tampered)

    leaked = dict(payload)
    leaked["source_url"] = "https://example.invalid/path"
    leaked["derived_validation_digest"] = canonical_digest(leaked)
    with pytest.raises(ValueError, match="unsafe public"):
        api().research_team_domain_claim_review_memory_score_public_payload(leaked)

    bad_report_status = dict(payload)
    bad_report_status["report_status"] = "paused"
    bad_report_status["derived_validation_digest"] = canonical_digest(bad_report_status)
    with pytest.raises(ValueError, match="report_status"):
        api().research_team_domain_claim_review_memory_score_public_payload(
            bad_report_status,
        )

    bad_row_status = json.loads(json.dumps(payload))
    bad_row_status["rows"][0]["memory_status"] = "paused"
    bad_row_status["derived_validation_digest"] = canonical_digest(bad_row_status)
    with pytest.raises(ValueError, match="memory_status"):
        api().research_team_domain_claim_review_memory_score_public_payload(
            bad_row_status,
        )

    extra_field = dict(payload)
    extra_field["extra_safe_key"] = "safe_value"
    extra_field["derived_validation_digest"] = canonical_digest(extra_field)
    with pytest.raises(ValueError, match="public payload keys"):
        api().research_team_domain_claim_review_memory_score_public_payload(extra_field)


def test_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    module = api()
    built = build_report(review_input())

    with pytest.raises(FrozenInstanceError):
        built.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].memory_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        review_input(memory_hit_count=9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_hit_count"):
        review_input(memory_hit_count=d("11.000000"))
    with pytest.raises(ValueError, match="reviewed_at"):
        build_report(review_input(reviewed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="memory_observed_at"):
        build_report(review_input(memory_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="weights must sum to 1"):
        config(unresolved_resolution_weight=d("0.200000"))
    with pytest.raises(ValueError, match="memory_score_block_threshold"):
        config(
            memory_score_watch_threshold=d("0.300000"),
            memory_score_block_threshold=d("0.400000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchTeamDomainClaimReviewMemoryScoreConfig(paper_only=False)
    with pytest.raises(ValueError, match="memory_status"):
        replace(built.rows[0], memory_status="bad")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)

    for item in (
        config(),
        review_input(),
        built,
        built.rows[0],
        built.reason_code_counts[0],
    ):
        assert is_dataclass(item)
        for field in fields(item):
            value = getattr(item, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_rate")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
                or field.name.endswith("_pressure")
                or field.name.endswith("_score")
                or field.name.endswith("_weight")
                or field.name.endswith("_threshold")
                or field.name.endswith("_rank")
                or field.name.endswith("_below")
            ):
                if value is not None:
                    assert type(value) is Decimal


def test_module_scope_has_no_io_network_or_trading_surface_exports() -> None:
    module = api()
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_domain_claim_review_memory_score_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()

    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "psycopg",
        "sqlalchemy",
        "sqlite",
        "open(",
        "connect(",
    ):
        assert forbidden not in source

    unsafe_export_fragments = (
        "wallet",
        "order",
        "trade",
        "trading",
        "live",
        "sizing",
        "recommendation",
        "auth",
        "token",
        "dsn",
        "table",
    )
    assert all(
        not any(fragment in exported.lower() for fragment in unsafe_export_fragments)
        for exported in module.__all__
    )
    assert set(module.PUBLIC_STATUSES) == {"pass", "watch", "block"}


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
