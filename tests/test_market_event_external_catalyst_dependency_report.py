from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import inspect
import json
from typing import Any

import pytest

import polymarket_alpha_lab.market_event_external_catalyst_dependency_report as api
from polymarket_alpha_lab.market_event_external_catalyst_dependency_report import (
    MARKET_EVENT_EXTERNAL_CATALYST_DEPENDENCY_STATUSES,
    MarketEventExternalCatalystDependencyInput,
    MarketEventExternalCatalystDependencyReport,
    build_market_event_external_catalyst_dependency_report,
    market_event_external_catalyst_dependency_public_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def catalyst_input(
    **overrides: object,
) -> MarketEventExternalCatalystDependencyInput:
    values = {
        "external_catalyst_count": d("2.000000"),
        "confirmed_catalyst_count": d("2.000000"),
        "unconfirmed_catalyst_count": d("0.000000"),
        "next_catalyst_hours": d("72.000000"),
        "market_close_hours": d("168.000000"),
    }
    values.update(overrides)
    return MarketEventExternalCatalystDependencyInput(**values)


def report(**overrides: object) -> MarketEventExternalCatalystDependencyReport:
    return build_market_event_external_catalyst_dependency_report(
        catalyst_input(**overrides),
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def test_builds_ready_report_when_external_catalysts_are_confirmed_and_scheduled() -> None:
    summary = report()

    assert is_dataclass(summary)
    assert type(summary) is MarketEventExternalCatalystDependencyReport
    assert summary.external_catalyst_count == d("2.000000")
    assert summary.confirmed_catalyst_count == d("2.000000")
    assert summary.unconfirmed_catalyst_count == d("0.000000")
    assert summary.next_catalyst_hours == d("72.000000")
    assert summary.market_close_hours == d("168.000000")
    assert summary.catalyst_dependency_status == "ready"
    assert summary.reason_codes == (
        "market_event_external_catalyst_dependency_ready",
    )
    assert summary.manual_next_step == "document_external_catalyst_dependency_review"
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.payload_digest) == 64


def test_blocks_when_market_depends_on_unconfirmed_external_catalysts() -> None:
    summary = report(
        external_catalyst_count=d("3.000000"),
        confirmed_catalyst_count=d("1.000000"),
        unconfirmed_catalyst_count=d("2.000000"),
    )

    assert summary.catalyst_dependency_status == "blocked"
    assert summary.reason_codes == (
        "external_catalysts_unconfirmed_blocker",
    )
    assert summary.manual_next_step == "escalate_manual_catalyst_confirmation"


def test_attention_when_next_catalyst_occurs_after_market_close() -> None:
    summary = report(
        next_catalyst_hours=d("240.000000"),
        market_close_hours=d("168.000000"),
    )

    assert summary.catalyst_dependency_status == "attention"
    assert summary.reason_codes == (
        "next_catalyst_after_market_close_attention",
    )
    assert summary.manual_next_step == "review_market_close_before_catalyst"


def test_attention_when_no_external_catalyst_is_identified() -> None:
    summary = report(
        external_catalyst_count=d("0.000000"),
        confirmed_catalyst_count=d("0.000000"),
        unconfirmed_catalyst_count=d("0.000000"),
        next_catalyst_hours=d("0.000000"),
    )

    assert summary.catalyst_dependency_status == "attention"
    assert summary.reason_codes == (
        "external_catalyst_not_identified_attention",
    )
    assert summary.manual_next_step == "identify_public_external_catalyst"


def test_public_payload_and_digest_are_canonical_decimal_only_and_public_safe() -> None:
    summary = report()
    payload = summary.public_payload

    assert payload == market_event_external_catalyst_dependency_public_payload(summary)
    assert payload["external_catalyst_count"] == "2.000000"
    assert payload["confirmed_catalyst_count"] == "2.000000"
    assert payload["unconfirmed_catalyst_count"] == "0.000000"
    assert payload["next_catalyst_hours"] == "72.000000"
    assert payload["market_close_hours"] == "168.000000"
    assert payload["catalyst_dependency_status"] == "ready"
    assert payload["reason_codes"] == [
        "market_event_external_catalyst_dependency_ready",
    ]
    assert payload["manual_next_step"] == (
        "document_external_catalyst_dependency_review"
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == summary.payload_digest
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(payload)
    )

    digest_input = dict(payload)
    digest_input.pop("payload_digest")
    expected_digest = sha256(
        json.dumps(
            digest_input,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert payload["payload_digest"] == expected_digest

    payload_text = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "auth",
        "wallet",
        "key",
        "sign",
        "auto",
        "live",
        "trade",
        "buy",
        "sell",
        "execute",
        "execution",
        "jsonl",
        "persist",
        "crawl",
        "scrape",
    ):
        assert forbidden not in payload_text


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    summary = report()

    with pytest.raises(FrozenInstanceError):
        summary.catalyst_dependency_status = "attention"  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        catalyst_input(external_catalyst_count=2)

    with pytest.raises(ValueError, match="integer-valued Decimal"):
        catalyst_input(confirmed_catalyst_count=d("1.500000"))

    with pytest.raises(ValueError, match="confirmed_catalyst_count"):
        catalyst_input(
            external_catalyst_count=d("1.000000"),
            confirmed_catalyst_count=d("2.000000"),
        )

    with pytest.raises(ValueError, match="catalyst counts"):
        catalyst_input(
            external_catalyst_count=d("2.000000"),
            confirmed_catalyst_count=d("1.000000"),
            unconfirmed_catalyst_count=d("0.000000"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        replace(catalyst_input(), paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)

    with pytest.raises(ValueError, match="payload_digest"):
        replace(summary, catalyst_dependency_status="attention")


def test_no_io_or_actionable_surface_is_exposed() -> None:
    assert MARKET_EVENT_EXTERNAL_CATALYST_DEPENDENCY_STATUSES == (
        "ready",
        "attention",
        "blocked",
    )

    unsafe_terms = (
        "auth",
        "wallet",
        "key",
        "sign",
        "auto",
        "live",
        "trade",
        "buy",
        "sell",
        "execute",
        "execution",
        "jsonl",
        "persist",
        "crawl",
        "scrape",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        MarketEventExternalCatalystDependencyInput,
        MarketEventExternalCatalystDependencyReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    tree = ast.parse(inspect.getsource(api))
    imported_modules = {
        node.module.split(".")[0]
        if isinstance(node, ast.ImportFrom)
        else alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in (
            node.names
            if isinstance(node, ast.Import)
            else [ast.alias(node.module or "")]
        )
    }
    assert imported_modules.isdisjoint(
        {
            "builtins",
            "os",
            "pathlib",
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "supabase",
            "web3",
            "ccxt",
            "subprocess",
        },
    )
