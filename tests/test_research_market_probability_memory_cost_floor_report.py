from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_probability_memory_cost_floor_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_market_probability_memory_cost_floor_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 15, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 14, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, "memory cost floor report module is missing"
    return importlib.import_module(MODULE_NAME)


def _public_name() -> str:
    return "research_market_probability_memory_cost_floor_report"


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_PROBABILITY_MEMORY_COST_FLOOR_REPORT_CONFIG_VERSION
        ),
        "pass_min_memory_score": d("0.800000"),
        "watch_min_memory_score": d("0.600000"),
        "max_pass_probability_gap": d("0.050000"),
        "max_watch_probability_gap": d("0.120000"),
        "max_pass_cost_floor_gap": d("0.000000"),
        "max_watch_cost_floor_gap": d("0.050000"),
        "watch_stale_evidence_hours": d("24.000000"),
        "block_stale_evidence_hours": d("72.000000"),
    }
    values.update(overrides)
    return module.ResearchMarketProbabilityMemoryCostFloorConfig(**values)


def _input(module: Any, private_ref: str = "private-case-alpha", **overrides: object) -> Any:
    values = {
        "private_ref": private_ref,
        "observed_probability": d("0.540000"),
        "memory_probability": d("0.530000"),
        "memory_score": d("0.900000"),
        "cost_floor_probability": d("0.480000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": (),
    }
    values.update(overrides)
    return module.ResearchMarketProbabilityMemoryCostFloorInput(**values)


def _build(module: Any, rows: tuple[Any, ...], **overrides: object) -> Any:
    values = {
        "items": rows,
        "generated_at": GENERATED_AT,
        "config": _config(module),
    }
    values.update(overrides)
    return getattr(module, f"build_{_public_name()}")(**values)


def _payload(module: Any, value: Any) -> dict[str, Any]:
    return getattr(module, f"{_public_name()}_public_payload")(value)


def _digest(module: Any, value: Any) -> str:
    return getattr(module, f"{_public_name()}_digest")(value)


def _validate(module: Any, value: Any) -> dict[str, Any]:
    return getattr(module, f"validate_{_public_name()}_public_payload")(value)


def _walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(_walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(_walk_values(item))
        return tuple(nested)
    return (value,)


def _unsigned_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_builds_pass_watch_and_block_rows_with_private_refs_redacted() -> None:
    module = _module()
    report = _build(
        module,
        (
            _input(
                module,
                "candidate-alpha/market-slug?source_url=https://hidden.example/a&token=secret",
                observed_probability=d("0.540000"),
                memory_probability=d("0.530000"),
                memory_score=d("0.900000"),
                cost_floor_probability=d("0.480000"),
            ),
            _input(
                module,
                "watch-market/private-source raw table text dsn://hidden",
                observed_probability=d("0.420000"),
                memory_probability=d("0.500000"),
                memory_score=d("0.700000"),
                cost_floor_probability=d("0.450000"),
                observed_at=GENERATED_AT - timedelta(hours=30),
            ),
            _input(
                module,
                "block-market/source-url?wallet=private",
                observed_probability=d("0.300000"),
                memory_probability=d("0.500000"),
                memory_score=d("0.400000"),
                cost_floor_probability=d("0.450000"),
                observed_at=GENERATED_AT - timedelta(hours=100),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchMarketProbabilityMemoryCostFloorReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.status == "block"
    assert report.case_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_probability_gap == d("0.096667")
    assert report.max_cost_floor_gap == d("0.150000")
    assert report.max_observed_age_hours == d("100.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert blocked.case_digest.startswith("sha256:")
    assert blocked.probability_gap == d("0.200000")
    assert blocked.cost_floor_gap == d("0.150000")
    assert blocked.observed_age_hours == d("100.000000")
    assert blocked.reason_codes == (
        "memory_cost_floor_block",
        "probability_gap_block",
        "memory_score_block",
        "cost_floor_gap_block",
        "stale_evidence_block",
    )

    watched = report.rows[1]
    assert watched.reason_codes == (
        "memory_cost_floor_watch",
        "probability_gap_watch",
        "memory_score_watch",
        "cost_floor_gap_watch",
        "stale_evidence_watch",
    )

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.reason_codes == ("memory_cost_floor_pass",)

    payload = _payload(module, report)
    encoded_payload = json.dumps(payload, sort_keys=True).lower()
    assert payload["rows"][0]["case_digest"].startswith("sha256:")
    for forbidden in (
        "candidate-alpha",
        "market-slug",
        "source_url",
        "https://hidden.example",
        "token=secret",
        "private-source",
        "raw table text",
        "dsn://hidden",
        "wallet=private",
    ):
        assert forbidden not in encoded_payload


def test_public_payload_digest_is_deterministic_decimal_stringed_and_validated() -> None:
    module = _module()
    first = _build(
        module,
        (
            _input(module, "raw-b", memory_score=d("0.700000")),
            _input(module, "raw-a", memory_score=d("0.900000")),
        ),
    )
    second = _build(
        module,
        (
            _input(module, "raw-a", memory_score=d("0.900000")),
            _input(module, "raw-b", memory_score=d("0.700000")),
        ),
    )

    first_payload = _payload(module, first)
    second_payload = _payload(module, second)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.derived_validation_digest == _digest(module, first)
    assert first_payload["derived_validation_digest"] == _unsigned_digest(first_payload)
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert first_payload["case_count"] == "2.000000"
    assert first_payload["rows"][0]["memory_score"] == "0.700000"
    assert first_payload["rows"][0]["observed_at"] == "2026-07-09T14:30:00+00:00"
    assert not any(
        type(value) in (Decimal, int, float) for value in _walk_values(first_payload)
    )

    tampered_digest = dict(first_payload)
    tampered_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        _validate(module, tampered_digest)

    tampered_score = json.loads(json.dumps(first_payload))
    tampered_score["rows"][0]["memory_score"] = "0.010000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        _validate(module, tampered_score)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_public_payload_rejects_raw_private_fields_values_and_flag_downgrades() -> None:
    module = _module()
    report = _build(module, (_input(module),))
    payload = _payload(module, report)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        _validate(module, missing_digest)

    bad_flag = json.loads(json.dumps(payload))
    bad_flag["rows"][0]["readonly"] = False
    bad_flag["derived_validation_digest"] = _unsigned_digest(bad_flag)
    with pytest.raises(ValueError, match="readonly"):
        _validate(module, bad_flag)

    for unsafe_payload in (
        {"candidate_id": "private-alpha"},
        {"market": "raw market name"},
        {"source_url": "https://hidden.example/raw"},
        {"raw_text": "verbatim private body"},
        {"dsn": "postgres://private"},
        {"table": "private_rows"},
        {"token": "secret"},
    ):
        unsafe_payload.update(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
            },
        )
        with pytest.raises(ValueError, match="unsafe"):
            _validate(module, unsafe_payload)


def test_dataclasses_are_frozen_decimal_only_and_status_limited() -> None:
    module = _module()

    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type) and exported_name.startswith("ResearchMarket"):
            assert is_dataclass(exported)

    report = _build(module, (_input(module),))
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="observed_probability"):
        _input(module, observed_probability=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_probability"):
        _input(module, memory_probability=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 9, 14, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="private_ref"):
        _input(module, private_ref=_StringSubclass("subclassed"))
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)

    for public_type in (
        module.ResearchMarketProbabilityMemoryCostFloorConfig,
        module.ResearchMarketProbabilityMemoryCostFloorInput,
        module.ResearchMarketProbabilityMemoryCostFloorReasonCodeCount,
        module.ResearchMarketProbabilityMemoryCostFloorRow,
        module.ResearchMarketProbabilityMemoryCostFloorReport,
    ):
        assert all(
            field.default is True
            for field in fields(public_type)
            if field.name in {"paper_only", "report_only", "readonly"}
        )

    for value in (report, *report.rows, *report.reason_code_counts):
        for field in fields(value):
            item = getattr(value, field.name)
            if isinstance(item, Decimal):
                assert type(item) is Decimal


def test_report_only_scope_has_no_forbidden_runtime_surface_terms() -> None:
    module = _module()
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "db",
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "live trading",
        "sizing",
        "recommendation",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "execute(",
        "commit(",
        "rollback(",
        "send(",
        "submit(",
        '"blocked"',
        '"ready"',
    ):
        assert forbidden not in lowered

    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_PROBABILITY_MEMORY_COST_FLOOR_REPORT_CONFIG_VERSION",
        "ResearchMarketProbabilityMemoryCostFloorConfig",
        "ResearchMarketProbabilityMemoryCostFloorInput",
        "ResearchMarketProbabilityMemoryCostFloorReasonCodeCount",
        "ResearchMarketProbabilityMemoryCostFloorRow",
        "ResearchMarketProbabilityMemoryCostFloorReport",
        "build_research_market_probability_memory_cost_floor_report",
        "research_market_probability_memory_cost_floor_report_public_payload",
        "research_market_probability_memory_cost_floor_report_digest",
        "validate_research_market_probability_memory_cost_floor_report_public_payload",
    )
