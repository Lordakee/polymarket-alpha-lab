from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_claim_authority_recheck_queue_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_claim_authority_recheck_queue_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(
    index: int,
    *,
    claim_bucket: str = "alpha-pass",
    authority_bucket: str | None = None,
    claim_observed_at: datetime | None = None,
    authority_last_checked_at: datetime | None = None,
    source_authority_score: Decimal = d("0.950000"),
    source_confidence_score: Decimal = d("0.950000"),
    conflict_score: Decimal = d("0.000000"),
    corroborating_authority_count: Decimal = d("2.000000"),
    required_authority_count: Decimal = d("2.000000"),
    resolution_deadline_at: datetime | None = None,
    reason_codes: tuple[str, ...] = (),
) -> Any:
    module = api()
    return module.ResearchSourceClaimAuthorityRecheckQueueInput(
        claim_bucket=claim_bucket,
        authority_bucket=authority_bucket or f"authority-{index:03d}",
        private_candidate_reference=(
            f"raw_candidate_id=CAND-{index:03d}; token=secret-{index}"
        ),
        private_market_reference=(
            f"market_id=0xMARKET{index:03d}; market_slug=will-alpha-{index}; "
            f"market_question=Will Alpha resolve {index}?"
        ),
        private_source_reference=(
            "https://authority.example.test/private?"
            f"dsn=postgres://user:pass@host/db&table=authority_table_{index}; "
            f"wallet=0xabc; order={index}; trade={index}; live feed; source text"
        ),
        claim_observed_at=claim_observed_at
        if claim_observed_at is not None
        else GENERATED_AT - timedelta(hours=1),
        authority_last_checked_at=authority_last_checked_at
        if authority_last_checked_at is not None
        else GENERATED_AT - timedelta(minutes=20),
        source_authority_score=source_authority_score,
        source_confidence_score=source_confidence_score,
        conflict_score=conflict_score,
        corroborating_authority_count=corroborating_authority_count,
        required_authority_count=required_authority_count,
        resolution_deadline_at=resolution_deadline_at,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[Any, ...],
    *,
    config: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_source_claim_authority_recheck_queue_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def test_prioritizes_claim_authority_rechecks_without_public_private_surfaces() -> None:
    module = api()
    recheck_report = report(
        (
            candidate(
                1,
                claim_bucket="alpha-pass",
                authority_bucket="authority-pass",
            ),
            candidate(
                2,
                claim_bucket="beta-watch",
                authority_bucket="authority-watch",
                authority_last_checked_at=GENERATED_AT - timedelta(hours=12),
                source_authority_score=d("0.600000"),
                source_confidence_score=d("0.800000"),
                conflict_score=d("0.400000"),
                corroborating_authority_count=d("1.000000"),
                required_authority_count=d("3.000000"),
                resolution_deadline_at=GENERATED_AT + timedelta(hours=24),
                reason_codes=("manual_recheck_window",),
            ),
            candidate(
                3,
                claim_bucket="gamma-block",
                authority_bucket="authority-block",
                authority_last_checked_at=GENERATED_AT - timedelta(days=4),
                source_authority_score=d("0.250000"),
                source_confidence_score=d("0.300000"),
                conflict_score=d("0.800000"),
                corroborating_authority_count=d("0.000000"),
                required_authority_count=d("3.000000"),
                resolution_deadline_at=GENERATED_AT - timedelta(minutes=1),
                reason_codes=("primary_claim_stale",),
            ),
        ),
    )

    assert recheck_report.status == "block"
    assert recheck_report.row_count == d("3.000000")
    assert recheck_report.stale_authority_count == d("2.000000")
    assert recheck_report.authority_gap_count == d("2.000000")
    assert recheck_report.conflict_count == d("2.000000")
    assert recheck_report.source_confidence_gap_count == d("1.000000")
    assert recheck_report.corroboration_gap_count == d("2.000000")
    assert recheck_report.deadline_proximity_count == d("2.000000")
    assert recheck_report.pass_count == d("1.000000")
    assert recheck_report.watch_count == d("1.000000")
    assert recheck_report.block_count == d("1.000000")
    assert recheck_report.average_recheck_priority_score == d("0.444163")
    assert recheck_report.max_recheck_priority_score == d("0.875000")

    block_row, watch_row, pass_row = recheck_report.rows
    assert type(block_row) is module.ResearchSourceClaimAuthorityRecheckQueueRow
    assert block_row.claim_bucket == "gamma-block"
    assert block_row.status == "block"
    assert block_row.claim_age_seconds == d("3600.000000")
    assert block_row.authority_age_seconds == d("345600.000000")
    assert block_row.authority_freshness_score == d("1.000000")
    assert block_row.authority_gap_score == d("0.750000")
    assert block_row.source_confidence_gap_score == d("0.700000")
    assert block_row.authority_corroboration_gap_score == d("1.000000")
    assert block_row.deadline_proximity_score == d("1.000000")
    assert block_row.recheck_priority_score == d("0.875000")
    assert block_row.reason_codes == (
        "authority_corroboration_block",
        "authority_freshness_block",
        "authority_gap_block",
        "claim_authority_recheck_queue_block",
        "claim_conflict_block",
        "deadline_proximity_block",
        "input_primary_claim_stale",
        "source_confidence_block",
    )

    assert watch_row.claim_bucket == "beta-watch"
    assert watch_row.status == "watch"
    assert watch_row.authority_age_seconds == d("43200.000000")
    assert watch_row.authority_freshness_score == d("0.478261")
    assert watch_row.authority_gap_score == d("0.400000")
    assert watch_row.source_confidence_gap_score == d("0.200000")
    assert watch_row.authority_corroboration_gap_score == d("0.666667")
    assert watch_row.deadline_proximity_score == d("0.500000")
    assert watch_row.recheck_priority_score == d("0.440821")
    assert "input_manual_recheck_window" in watch_row.reason_codes

    assert pass_row.claim_bucket == "alpha-pass"
    assert pass_row.status == "pass"
    assert pass_row.recheck_priority_score == d("0.016667")
    assert pass_row.reason_codes == (
        "authority_corroboration_clear",
        "authority_freshness_clear",
        "authority_gap_clear",
        "claim_authority_recheck_queue_pass",
        "claim_conflict_clear",
        "deadline_proximity_clear",
        "source_confidence_clear",
    )

    payload = module.research_source_claim_authority_recheck_queue_report_payload(
        recheck_report,
    )
    encoded = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "raw_candidate_id",
        "cand-001",
        "market_id",
        "market_slug",
        "market_question",
        "will alpha resolve",
        "https://authority.example.test",
        "dsn=postgres",
        "authority_table",
        "token=secret",
        "wallet=0xabc",
        "order=1",
        "trade=1",
        "live feed",
        "source text",
        "private_candidate_reference",
        "private_market_reference",
        "private_source_reference",
    ):
        assert forbidden not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))


def test_digest_is_deterministic_and_validated_for_report_and_payload() -> None:
    module = api()
    first = report(
        (
            candidate(
                2,
                claim_bucket="beta-watch",
                authority_last_checked_at=GENERATED_AT - timedelta(hours=8),
                conflict_score=d("0.400000"),
            ),
            candidate(1, claim_bucket="alpha-pass"),
        ),
    )
    second = report(
        (
            candidate(1, claim_bucket="alpha-pass"),
            candidate(
                2,
                claim_bucket="beta-watch",
                authority_last_checked_at=GENERATED_AT - timedelta(hours=8),
                conflict_score=d("0.400000"),
            ),
        ),
    )

    payload = module.research_source_claim_authority_recheck_queue_report_payload(first)
    unsigned_payload = dict(payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_claim_authority_recheck_queue_report_payload(
            tampered_payload,
        )


def test_dict_payload_requires_exact_schema_and_revalidates_derived_fields() -> None:
    module = api()
    payload = module.research_source_claim_authority_recheck_queue_report_payload(
        report((candidate(1),)),
    )

    extra_field_payload = dict(payload)
    extra_field_payload["safe_extension"] = "unexpected"
    extra_field_payload = _with_recomputed_digest(extra_field_payload)
    with pytest.raises(ValueError, match="schema"):
        module.research_source_claim_authority_recheck_queue_report_payload(
            extra_field_payload,
        )

    inconsistent_summary_payload = dict(payload)
    inconsistent_summary_payload["stale_authority_count"] = "1.000000"
    inconsistent_summary_payload = _with_recomputed_digest(
        inconsistent_summary_payload,
    )
    with pytest.raises(ValueError, match="stale_authority_count"):
        module.research_source_claim_authority_recheck_queue_report_payload(
            inconsistent_summary_payload,
        )

    invalid_nested_digest_payload = dict(payload)
    rows = [dict(row) for row in payload["rows"]]
    rows[0]["derived_validation_digest"] = "0" * 64
    invalid_nested_digest_payload["rows"] = rows
    invalid_nested_digest_payload = _with_recomputed_digest(
        invalid_nested_digest_payload,
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_claim_authority_recheck_queue_report_payload(
            invalid_nested_digest_payload,
        )

    inconsistent_nested_row_payload = dict(payload)
    rows = [dict(row) for row in payload["rows"]]
    rows[0]["status"] = "watch"
    rows[0] = _with_recomputed_digest(rows[0])
    inconsistent_nested_row_payload["rows"] = rows
    inconsistent_nested_row_payload = _with_recomputed_digest(
        inconsistent_nested_row_payload,
    )
    with pytest.raises(ValueError, match="reason_codes"):
        module.research_source_claim_authority_recheck_queue_report_payload(
            inconsistent_nested_row_payload,
        )


def test_validation_rejects_bad_numerics_flags_statuses_and_future_dates() -> None:
    module = api()
    with pytest.raises(ValueError, match="fresh_authority_age_seconds"):
        module.ResearchSourceClaimAuthorityRecheckQueueConfig(
            fresh_authority_age_seconds=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="watch_priority_score"):
        module.ResearchSourceClaimAuthorityRecheckQueueConfig(
            watch_priority_score=DecimalSubclass("0.250000"),
        )
    with pytest.raises(ValueError, match="block_priority_score"):
        module.ResearchSourceClaimAuthorityRecheckQueueConfig(
            watch_priority_score=d("0.700000"),
            block_priority_score=d("0.500000"),
        )
    with pytest.raises(ValueError, match="source_authority_score"):
        candidate(1, source_authority_score=d("1.100000"))
    with pytest.raises(ValueError, match="corroborating_authority_count"):
        candidate(
            1,
            corroborating_authority_count=d("3.000000"),
            required_authority_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(1), paper_only=False)
    with pytest.raises(ValueError, match="claim_observed_at"):
        report(
            (
                candidate(
                    1,
                    claim_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="authority_last_checked_at"):
        report(
            (
                candidate(
                    1,
                    authority_last_checked_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_claim_authority_recheck_queue_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="status"):
        replace(report((candidate(1),)).rows[0], status="blocked")


def test_public_dataclasses_are_frozen_and_payload_requires_hard_flags() -> None:
    module = api()
    recheck_report = report((candidate(1),))
    payload = module.research_source_claim_authority_recheck_queue_report_payload(
        recheck_report,
    )

    assert recheck_report.paper_only is True
    assert recheck_report.report_only is True
    assert recheck_report.readonly is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    with pytest.raises(FrozenInstanceError):
        recheck_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        recheck_report.rows[0].recheck_priority_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="recheck_priority_score"):
        replace(recheck_report.rows[0], recheck_priority_score=d("0.750000"))

    bad_payload = dict(payload)
    bad_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_source_claim_authority_recheck_queue_report_payload(bad_payload)

    unsafe_payload = dict(payload)
    unsafe_payload["market_slug"] = "unsafe"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_source_claim_authority_recheck_queue_report_payload(
            unsafe_payload,
        )


def test_owned_module_has_no_db_network_or_execution_imports_or_calls() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_imports = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "sqlalchemy",
    )
    forbidden_calls = (
        "open(",
        "connect(",
        "request(",
        "post(",
        "get(",
        "send(",
        "submit(",
        "cancel(",
        "replace_order(",
    )

    assert all(term not in lowered for term in forbidden_imports)
    assert all(term not in lowered for term in forbidden_calls)


def test_public_api_is_exactly_the_report_only_surface() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_RECHECK_QUEUE_REPORT_CONFIG_VERSION",
        "ResearchSourceClaimAuthorityRecheckQueueConfig",
        "ResearchSourceClaimAuthorityRecheckQueueInput",
        "ResearchSourceClaimAuthorityRecheckQueueReport",
        "ResearchSourceClaimAuthorityRecheckQueueRow",
        "build_research_source_claim_authority_recheck_queue_report",
        "research_source_claim_authority_recheck_queue_report_payload",
    )


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


def _with_recomputed_digest(payload: dict[str, Any]) -> dict[str, Any]:
    recomputed = dict(payload)
    unsigned_payload = dict(recomputed)
    unsigned_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    recomputed["derived_validation_digest"] = hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return recomputed
