from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_information_recency_decay_report"
GENERATED_AT = datetime(2026, 7, 8, 9, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(**overrides: object) -> Any:
    module = api()
    values = {
        "research_key": "policy_calendar",
        "evidence_family": "official",
        "evidence_age_minutes": d("20.000000"),
        "authority_score": d("0.900000"),
        "corroboration_count": d("3"),
        "contradiction_pressure": d("0.050000"),
        "minutes_until_deadline": d("240.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceInformationRecencyEvidence(**values)


def report(*items: object, **overrides: object) -> Any:
    module = api()
    return module.build_research_source_information_recency_decay_report(
        items,
        generated_at=overrides.pop("generated_at", GENERATED_AT),
        **overrides,
    )


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        children: list[object] = []
        for child in value.values():
            children.extend(walk(child))
        return tuple(children)
    if isinstance(value, list):
        children = []
        for child in value:
            children.extend(walk(child))
        return tuple(children)
    return (value,)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_report_scores_source_evidence_decay_before_strategy_review() -> None:
    result = report(
        evidence(),
        evidence(
            research_key="injury_signal",
            evidence_family="secondary",
            evidence_age_minutes=d("120.000000"),
            authority_score=d("0.700000"),
            corroboration_count=d("2"),
            contradiction_pressure=d("0.300000"),
            minutes_until_deadline=d("50.000000"),
        ),
        evidence(
            research_key="litigation_window",
            evidence_family="filing",
            evidence_age_minutes=d("210.000000"),
            authority_score=d("0.400000"),
            corroboration_count=d("1"),
            contradiction_pressure=d("0.700000"),
            minutes_until_deadline=d("20.000000"),
        ),
    )

    assert result.report_status == "block"
    assert result.evidence_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.min_decay_score == d("0.273333")
    assert result.max_staleness_pressure == d("1.000000")
    assert result.reason_codes == (
        "evidence_age_block",
        "evidence_age_stale",
        "authority_weight_weak",
        "corroboration_gap",
        "contradiction_pressure_block",
        "contradiction_pressure_watch",
        "deadline_proximity_block",
        "deadline_proximity_watch",
        "source_information_recency_decay_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)

    assert tuple(row.research_key for row in result.rows) == (
        "litigation_window",
        "injury_signal",
        "policy_calendar",
    )
    assert tuple(row.decay_status for row in result.rows) == ("block", "watch", "pass")

    blocked = result.rows[0]
    assert blocked.age_decay_score == d("0.000000")
    assert blocked.corroboration_score == d("0.333333")
    assert blocked.contradiction_score == d("0.300000")
    assert blocked.deadline_proximity_score == d("0.333333")
    assert blocked.evidence_decay_score == d("0.273333")
    assert blocked.staleness_pressure == d("1.000000")
    assert blocked.reason_codes == (
        "evidence_age_block",
        "authority_weight_weak",
        "corroboration_gap",
        "contradiction_pressure_block",
        "deadline_proximity_block",
    )
    assert_digest(blocked.validation_digest)

    watched = result.rows[1]
    assert watched.age_decay_score == d("0.333333")
    assert watched.corroboration_score == d("0.666667")
    assert watched.contradiction_score == d("0.700000")
    assert watched.deadline_proximity_score == d("0.833333")
    assert watched.evidence_decay_score == d("0.646667")
    assert watched.reason_codes == (
        "evidence_age_stale",
        "corroboration_gap",
        "contradiction_pressure_watch",
        "deadline_proximity_watch",
    )

    passed = result.rows[2]
    assert passed.age_decay_score == d("0.888889")
    assert passed.evidence_decay_score == d("0.947778")
    assert passed.reason_codes == ("source_information_recency_decay_pass",)
    assert blocked.evidence_decay_score < watched.evidence_decay_score < passed.evidence_decay_score


def test_payload_is_deterministic_json_safe_and_digest_validated() -> None:
    module = api()
    result = report(evidence())

    payload = result.payload
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload == module.research_source_information_recency_decay_report_payload(result)
    assert payload["generated_at"] == "2026-07-08T09:30:00+00:00"
    assert payload["evidence_count"] == "1"
    assert payload["rows"][0]["evidence_decay_score"] == "0.947778"
    assert payload["rows"][0]["validation_digest"] == result.rows[0].validation_digest
    assert payload["validation_digest"] == result.validation_digest
    assert module.research_source_information_recency_decay_report_payload(payload) == payload
    assert not any(type(value) is Decimal for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))
    assert not any(type(value) is float for value in walk(payload))

    with pytest.raises(ValueError, match="validation_digest must match"):
        module.research_source_information_recency_decay_report_payload(
            {**payload, "report_status": "watch"},
        )
    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "://",
    ):
        assert forbidden not in encoded.lower()

    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result.rows[0], validation_digest="0" * 64)
    with pytest.raises(ValueError, match="evidence_decay_score must match"):
        replace(result.rows[0], evidence_decay_score=d("0.100000"))
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)


def test_empty_report_blocks_with_decimal_zeroes() -> None:
    result = report()

    assert result.report_status == "block"
    assert result.evidence_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.min_decay_score is None
    assert result.max_staleness_pressure == d("0.000000")
    assert result.rows == ()
    assert result.reason_codes == ("source_information_recency_decay_empty",)
    assert_digest(result.validation_digest)


def test_validation_requires_exact_decimals_frozen_flags_and_safe_public_inputs() -> None:
    module = api()
    result = report(evidence())

    with pytest.raises(FrozenInstanceError):
        result.rows[0].decay_status = "block"  # type: ignore[misc]

    with pytest.raises(ValueError, match="evidence_age_minutes must be a Decimal"):
        evidence(evidence_age_minutes=20)
    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        evidence(authority_score=0.9)
    with pytest.raises(ValueError, match="authority_score must be a Decimal"):
        evidence(authority_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="evidence_age_minutes must be finite"):
        evidence(evidence_age_minutes=Decimal("NaN"))
    with pytest.raises(ValueError, match="authority_score must be between zero and one"):
        evidence(authority_score=d("1.000001"))
    with pytest.raises(ValueError, match="corroboration_count must be an integer"):
        evidence(corroboration_count=d("1.5"))
    with pytest.raises(ValueError, match="paper_only"):
        evidence(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(result.rows[0], decay_status="blocked")
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_source_information_recency_decay_report(
            (),
            generated_at=GENERATED_AT,
            config=object(),
        )


def test_payload_rejects_raw_private_and_live_surface_dicts() -> None:
    module = api()
    base = report(evidence()).payload

    with pytest.raises(ValueError, match="readonly"):
        module.research_source_information_recency_decay_report_payload(
            {**base, "readonly": False},
        )
    with pytest.raises(ValueError, match="numeric payload values must use Decimal"):
        module.research_source_information_recency_decay_report_payload(
            {**base, "evidence_count": 1},
        )
    with pytest.raises(ValueError, match="numeric payload values must use Decimal"):
        module.research_source_information_recency_decay_report_payload(
            {**base, "max_staleness_pressure": 1.0},
        )
    for unsafe_key, unsafe_value in (
        ("candidate_id", "abc"),
        ("event_market", "abc"),
        ("source_url", "abc"),
        ("source_text", "abc"),
        ("dsn", "abc"),
        ("table_name", "abc"),
        ("token", "abc"),
        ("wallet", "abc"),
        ("order_surface", "abc"),
        ("trade_surface", "abc"),
        ("live_surface", "abc"),
    ):
        with pytest.raises(ValueError, match="unsafe"):
            module.research_source_information_recency_decay_report_payload(
                {**base, unsafe_key: unsafe_value},
            )

    for unsafe_value in (
        "https://example.test/feed",
        "postgresql://example",
        "token-secret",
        "wallet-address",
        "live-trading",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            evidence(research_key=unsafe_value)


def test_module_scope_is_report_only_without_io_surfaces() -> None:
    module = api()
    path = Path("src/polymarket_alpha_lab/research_source_information_recency_decay_report.py")
    source = path.read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)

    banned_imports = {
        "asyncio",
        "http",
        "httpx",
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
    banned_attributes = banned_calls | {"commit", "rollback", "session"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    for public_name in module.__all__:
        lowered_name = public_name.lower()
        for forbidden in ("candidate", "market", "slug", "question", "url", "dsn"):
            assert forbidden not in lowered_name

    for cls in (
        module.ResearchSourceInformationRecencyDecayConfig,
        module.ResearchSourceInformationRecencyEvidence,
        module.ResearchSourceInformationRecencyDecayRow,
        module.ResearchSourceInformationRecencyDecayReport,
    ):
        for field in fields(cls):
            lowered_name = field.name.lower()
            for forbidden in (
                "candidate",
                "market",
                "slug",
                "question",
                "url",
                "text",
                "dsn",
                "table",
                "token",
                "wallet",
                "order",
                "trade",
                "live",
            ):
                assert forbidden not in lowered_name

    assert "requests." not in lowered
