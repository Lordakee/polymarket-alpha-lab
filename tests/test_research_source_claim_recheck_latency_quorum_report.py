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
    "research_source_claim_recheck_latency_quorum_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_claim_recheck_latency_quorum_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
DEFAULT_QUORUM_REACHED_AT = object()


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def ago(seconds: int) -> datetime:
    return GENERATED_AT - timedelta(seconds=seconds)


def candidate(
    index: int,
    *,
    claim_bucket: str = "alpha-pass",
    evidence_bucket: str | None = None,
    recheck_requested_at: datetime | None = None,
    quorum_reached_at: datetime | None | object = DEFAULT_QUORUM_REACHED_AT,
    supporting_recheck_count: Decimal = d("3.000000"),
    required_quorum_count: Decimal = d("3.000000"),
    conflicting_recheck_count: Decimal = d("0.000000"),
    reason_codes: tuple[str, ...] = (),
) -> Any:
    module = api()
    return module.ResearchSourceClaimRecheckLatencyQuorumInput(
        claim_bucket=claim_bucket,
        evidence_bucket=evidence_bucket or f"evidence-{index:03d}",
        private_candidate_reference=(
            f"raw_candidate_id=CAND-{index:03d}; token=secret-{index}"
        ),
        private_market_reference=(
            f"market_id=0xMARKET{index:03d}; market_slug=will-alpha-{index}; "
            f"question=Will Alpha resolve {index}?"
        ),
        private_source_reference=(
            "https://authority.example.test/private?"
            f"dsn=postgres://user:pass@host/db&table=source_table_{index}; "
            f"wallet=0xabc; order={index}; trade={index}; live feed; source text"
        ),
        recheck_requested_at=recheck_requested_at
        if recheck_requested_at is not None
        else ago(600),
        quorum_reached_at=ago(300)
        if quorum_reached_at is DEFAULT_QUORUM_REACHED_AT
        else quorum_reached_at,
        supporting_recheck_count=supporting_recheck_count,
        required_quorum_count=required_quorum_count,
        conflicting_recheck_count=conflicting_recheck_count,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[Any, ...],
    *,
    config: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_source_claim_recheck_latency_quorum_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_builds_claim_recheck_latency_quorum_report_without_private_surfaces() -> None:
    module = api()
    recheck_report = report(
        (
            candidate(1, claim_bucket="alpha-pass", evidence_bucket="official-pass"),
            candidate(
                2,
                claim_bucket="beta-watch",
                evidence_bucket="specialist-watch",
                recheck_requested_at=ago(1600),
                quorum_reached_at=ago(400),
                supporting_recheck_count=d("2.000000"),
                required_quorum_count=d("3.000000"),
                conflicting_recheck_count=d("1.000000"),
                reason_codes=("manual_recheck_window",),
            ),
            candidate(
                3,
                claim_bucket="gamma-block",
                evidence_bucket="aggregate-block",
                recheck_requested_at=ago(5000),
                quorum_reached_at=None,
                supporting_recheck_count=d("1.000000"),
                required_quorum_count=d("3.000000"),
                conflicting_recheck_count=d("3.000000"),
                reason_codes=("primary_claim_stale",),
            ),
        ),
    )

    assert recheck_report.status == "block"
    assert recheck_report.row_count == d("3.000000")
    assert recheck_report.delayed_recheck_count == d("2.000000")
    assert recheck_report.quorum_gap_count == d("2.000000")
    assert recheck_report.conflict_count == d("2.000000")
    assert recheck_report.pass_count == d("1.000000")
    assert recheck_report.watch_count == d("1.000000")
    assert recheck_report.block_count == d("1.000000")
    assert recheck_report.average_recheck_latency_seconds == d("2166.666667")
    assert recheck_report.average_quorum_ratio == d("0.666667")
    assert recheck_report.max_recheck_latency_quorum_score == d("0.805556")

    block_row, watch_row, pass_row = recheck_report.rows
    assert type(block_row) is module.ResearchSourceClaimRecheckLatencyQuorumRow
    assert block_row.claim_bucket == "gamma-block"
    assert block_row.status == "block"
    assert block_row.recheck_latency_seconds == d("5000.000000")
    assert block_row.quorum_ratio == d("0.333333")
    assert block_row.quorum_gap_score == d("0.666667")
    assert block_row.conflict_ratio == d("0.750000")
    assert block_row.recheck_latency_quorum_score == d("0.805556")
    assert "recheck_latency_block" in block_row.reason_codes
    assert "input_primary_claim_stale" in block_row.reason_codes

    assert watch_row.claim_bucket == "beta-watch"
    assert watch_row.status == "watch"
    assert watch_row.recheck_latency_seconds == d("1200.000000")
    assert watch_row.latency_pressure_score == d("0.333333")
    assert watch_row.quorum_ratio == d("0.666667")
    assert watch_row.conflict_ratio == d("0.333333")
    assert watch_row.recheck_latency_quorum_score == d("0.333333")
    assert "input_manual_recheck_window" in watch_row.reason_codes

    assert pass_row.claim_bucket == "alpha-pass"
    assert pass_row.status == "pass"
    assert pass_row.recheck_latency_seconds == d("300.000000")
    assert pass_row.recheck_latency_quorum_score == d("0.027778")
    assert pass_row.reason_codes == (
        "claim_recheck_latency_quorum_pass",
        "recheck_conflict_clear",
        "recheck_latency_clear",
        "recheck_quorum_clear",
    )

    payload = module.research_source_claim_recheck_latency_quorum_report_payload(
        recheck_report,
    )
    encoded = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "raw_candidate_id",
        "cand-001",
        "market_id",
        "market_slug",
        "question=will alpha",
        "https://authority.example.test",
        "dsn=postgres",
        "source_table",
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


def test_payload_is_deterministic_decimal_only_and_digest_validated() -> None:
    module = api()
    first = report(
        (
            candidate(2, claim_bucket="beta-watch", recheck_requested_at=ago(1600)),
            candidate(1, claim_bucket="alpha-pass"),
        ),
    )
    second = report(
        (
            candidate(1, claim_bucket="alpha-pass"),
            candidate(2, claim_bucket="beta-watch", recheck_requested_at=ago(1600)),
        ),
    )

    payload = module.research_source_claim_recheck_latency_quorum_report_payload(first)

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == module.research_source_claim_recheck_latency_quorum_report_payload(
        second,
    )
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["watch_count"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_claim_recheck_latency_quorum_report_payload(
            tampered_payload,
        )


def test_validation_rejects_bad_numerics_flags_statuses_and_dates() -> None:
    module = api()
    recheck_report = report((candidate(1),))

    with pytest.raises(ValueError, match="watch_recheck_latency_seconds"):
        module.ResearchSourceClaimRecheckLatencyQuorumConfig(
            watch_recheck_latency_seconds=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="block_recheck_latency_seconds"):
        module.ResearchSourceClaimRecheckLatencyQuorumConfig(
            block_recheck_latency_seconds=DecimalSubclass("3600.000000"),
        )
    with pytest.raises(ValueError, match="block_recheck_latency_seconds"):
        module.ResearchSourceClaimRecheckLatencyQuorumConfig(
            watch_recheck_latency_seconds=d("3600.000000"),
            block_recheck_latency_seconds=d("900.000000"),
        )
    with pytest.raises(ValueError, match="supporting_recheck_count"):
        candidate(1, supporting_recheck_count=d("-1.000000"))
    with pytest.raises(ValueError, match="required_quorum_count"):
        candidate(1, required_quorum_count=d("0.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(1), paper_only=False)
    with pytest.raises(ValueError, match="recheck_requested_at"):
        report((candidate(1, recheck_requested_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="quorum_reached_at"):
        report((candidate(1, quorum_reached_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_claim_recheck_latency_quorum_report(
            (),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="status"):
        replace(recheck_report.rows[0], status="blocked")


def test_public_dataclasses_are_frozen_and_payload_requires_hard_flags() -> None:
    module = api()
    recheck_report = report((candidate(1),))
    payload = module.research_source_claim_recheck_latency_quorum_report_payload(
        recheck_report,
    )

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_CLAIM_RECHECK_LATENCY_QUORUM_REPORT_CONFIG_VERSION",
        "ResearchSourceClaimRecheckLatencyQuorumConfig",
        "ResearchSourceClaimRecheckLatencyQuorumInput",
        "ResearchSourceClaimRecheckLatencyQuorumReport",
        "ResearchSourceClaimRecheckLatencyQuorumRow",
        "build_research_source_claim_recheck_latency_quorum_report",
        "research_source_claim_recheck_latency_quorum_report_payload",
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
        recheck_report.rows[0].recheck_latency_quorum_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="recheck_latency_quorum_score"):
        replace(recheck_report.rows[0], recheck_latency_quorum_score=d("0.750000"))

    bad_payload = dict(payload)
    bad_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_source_claim_recheck_latency_quorum_report_payload(bad_payload)

    unsafe_payload = dict(payload)
    unsafe_payload["market_slug"] = "unsafe"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_source_claim_recheck_latency_quorum_report_payload(
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
