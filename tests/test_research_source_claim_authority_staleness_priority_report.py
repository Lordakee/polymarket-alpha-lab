from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_claim_authority_staleness_priority_report"
)


def _module() -> Any:
    return importlib.import_module(MODULE_NAME)


def _now() -> datetime:
    return datetime(2026, 7, 9, 12, 0, 0, tzinfo=timezone.utc)


def _signal(
    *,
    suffix: str,
    observed_age: timedelta = timedelta(minutes=5),
    authority_score: Decimal = Decimal("0.900000"),
    claim_priority_score: Decimal = Decimal("0.100000"),
) -> Any:
    m = _module()
    return m.ResearchSourceClaimAuthorityStalenessPrioritySignal(
        candidate_id=f"candidate-{suffix}",
        market_id=f"market-{suffix}",
        market_slug=f"will-event-{suffix}-resolve",
        market_question=f"Will event {suffix} resolve by the deadline?",
        source_url=f"https://example.invalid/private/{suffix}?token=secret-token",
        source_text=f"raw source text for {suffix}",
        source_observed_at=_now() - observed_age,
        authority_score=authority_score,
        claim_priority_score=claim_priority_score,
        corroborating_source_count=Decimal("2.000000"),
        contradiction_count=Decimal("0.000000"),
    )


def _assert_decimal_only_dataclass_values(value: Any) -> None:
    if is_dataclass(value):
        for field in fields(value):
            _assert_decimal_only_dataclass_values(getattr(value, field.name))
        return
    if isinstance(value, tuple):
        for item in value:
            _assert_decimal_only_dataclass_values(item)
        return
    assert type(value) not in (float, int), repr(value)


def _payload_scalars(value: Any) -> list[Any]:
    if isinstance(value, dict):
        scalars: list[Any] = []
        for key, item in value.items():
            scalars.append(key)
            scalars.extend(_payload_scalars(item))
        return scalars
    if isinstance(value, (list, tuple)):
        scalars = []
        for item in value:
            scalars.extend(_payload_scalars(item))
        return scalars
    return [value]


def test_report_dataclasses_are_frozen_hard_flagged_and_decimal_only() -> None:
    m = _module()
    config = m.ResearchSourceClaimAuthorityStalenessPriorityConfig()
    signal = _signal(suffix="pass")
    report = m.build_research_source_claim_authority_staleness_priority_report(
        [signal],
        as_of=_now(),
        config=config,
    )

    dataclass_values = [config, signal, report, *report.rows, *report.status_counts]
    for value in dataclass_values:
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        _assert_decimal_only_dataclass_values(value)

    with pytest.raises(FrozenInstanceError):
        config.readonly = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        signal.authority_score = Decimal("0.100000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "block"  # type: ignore[misc]


def test_statuses_are_only_pass_watch_block_and_decimals_are_required() -> None:
    m = _module()
    signals = [
        _signal(suffix="pass"),
        _signal(
            suffix="watch",
            observed_age=timedelta(days=2),
            authority_score=Decimal("0.500000"),
        ),
        _signal(
            suffix="block",
            observed_age=timedelta(days=8),
            authority_score=Decimal("0.200000"),
            claim_priority_score=Decimal("0.950000"),
        ),
    ]

    report = m.build_research_source_claim_authority_staleness_priority_report(
        signals,
        as_of=_now(),
    )

    assert m.ALLOWED_STATUSES == ("pass", "watch", "block")
    row_statuses = {row.status for row in report.rows}
    assert row_statuses == {"pass", "watch", "block"}
    assert report.status == "block"

    with pytest.raises(ValueError, match="authority_score"):
        m.ResearchSourceClaimAuthorityStalenessPrioritySignal(
            candidate_id="candidate-float",
            market_id="market-float",
            market_slug="will-float-resolve",
            market_question="Will this float resolve?",
            source_url="https://example.invalid/float",
            source_text="float score",
            source_observed_at=_now(),
            authority_score=0.5,
            claim_priority_score=Decimal("0.100000"),
            corroborating_source_count=Decimal("1.000000"),
            contradiction_count=Decimal("0.000000"),
        )

    with pytest.raises(ValueError, match="status"):
        m.ResearchSourceClaimAuthorityStalenessPriorityRow(
            claim_key="sha256:" + "0" * 64,
            source_observed_at=_now(),
            source_age_seconds=Decimal("0.000000"),
            authority_score=Decimal("0.900000"),
            claim_priority_score=Decimal("0.100000"),
            corroborating_source_count=Decimal("1.000000"),
            contradiction_count=Decimal("0.000000"),
            status="review",
            reason_codes=("within_thresholds",),
        )


def test_public_payload_is_deterministic_immutable_and_digest_validates() -> None:
    m = _module()
    signals = [
        _signal(suffix="b", observed_age=timedelta(days=8), authority_score=Decimal("0.200000")),
        _signal(suffix="a"),
        _signal(suffix="c", observed_age=timedelta(days=2), authority_score=Decimal("0.500000")),
    ]
    report = m.build_research_source_claim_authority_staleness_priority_report(
        signals,
        as_of=_now(),
    )
    reversed_report = m.build_research_source_claim_authority_staleness_priority_report(
        list(reversed(signals)),
        as_of=_now(),
    )

    payload = m.research_source_claim_authority_staleness_priority_public_payload(report)
    reversed_payload = m.research_source_claim_authority_staleness_priority_public_payload(
        reversed_report,
    )

    assert m.research_source_claim_authority_staleness_priority_payload_json(report) == (
        m.research_source_claim_authority_staleness_priority_payload_json(reversed_report)
    )
    assert payload == reversed_payload
    assert m.validate_research_source_claim_authority_staleness_priority_payload(payload)
    assert payload["validation_digest"].startswith("sha256:")
    assert len(payload["validation_digest"]) == len("sha256:") + 64

    with pytest.raises(TypeError):
        payload["status"] = "pass"
    with pytest.raises(TypeError):
        payload["rows"].append({"status": "pass"})

    for scalar in _payload_scalars(payload):
        assert type(scalar) not in (float, int), repr(scalar)

    parsed = json.loads(
        m.research_source_claim_authority_staleness_priority_payload_json(report),
    )
    assert parsed["validation_digest"] == payload["validation_digest"]


def test_public_payload_does_not_leak_raw_identifiers_or_sensitive_surfaces() -> None:
    m = _module()
    signal = m.ResearchSourceClaimAuthorityStalenessPrioritySignal(
        candidate_id="raw-candidate-id-123",
        market_id="raw-market-id-456",
        market_slug="raw-market-slug-should-not-leak",
        market_question="Will the raw market question leak?",
        source_url="https://private.example.invalid/report?token=secret-token",
        source_text=(
            "raw quoted source text with postgres://user:pass@host/db, "
            "alpha_private_table, wallet, order, trade, sizing, recommendation"
        ),
        source_observed_at=_now() - timedelta(days=9),
        authority_score=Decimal("0.100000"),
        claim_priority_score=Decimal("0.950000"),
        corroborating_source_count=Decimal("3.000000"),
        contradiction_count=Decimal("1.000000"),
    )
    report = m.build_research_source_claim_authority_staleness_priority_report(
        [signal],
        as_of=_now(),
    )
    payload_json = m.research_source_claim_authority_staleness_priority_payload_json(report)

    forbidden_raw_fragments = (
        signal.candidate_id,
        signal.market_id,
        signal.market_slug,
        signal.market_question,
        signal.source_url,
        signal.source_text,
        "secret-token",
        "postgres://",
        "alpha_private_table",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )
    for raw_fragment in forbidden_raw_fragments:
        assert raw_fragment not in payload_json

    payload = m.research_source_claim_authority_staleness_priority_public_payload(report)
    forbidden_public_keys = {
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
    }
    assert forbidden_public_keys.isdisjoint(
        {key for key in _payload_scalars(payload) if isinstance(key, str)}
    )


def test_module_has_no_live_persistence_execution_or_advice_surfaces() -> None:
    m = _module()
    source = Path(m.__file__).read_text(encoding="utf-8")
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "sqlalchemy",
        "sqlite3",
        "web3",
        "ccxt",
    )
    for fragment in forbidden_import_fragments:
        assert fragment not in source

    forbidden_public_surface_fragments = (
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )
    for name in m.__all__:
        lowered = name.lower()
        for fragment in forbidden_public_surface_fragments:
            assert fragment not in lowered
