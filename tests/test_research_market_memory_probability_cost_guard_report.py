from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
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
    "research_market_memory_probability_cost_guard_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_market_memory_probability_cost_guard_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_MEMORY_PROBABILITY_COST_GUARD_REPORT_CONFIG_VERSION
        ),
        "watch_probability_gap_ratio": d("0.080000"),
        "block_probability_gap_ratio": d("0.200000"),
        "watch_cost_ratio": d("0.030000"),
        "block_cost_ratio": d("0.080000"),
        "watch_memory_decay_ratio": d("0.200000"),
        "block_memory_decay_ratio": d("0.400000"),
        "probability_gap_weight": d("0.400000"),
        "cost_weight": d("0.300000"),
        "memory_decay_weight": d("0.300000"),
    }
    values.update(overrides)
    return module.ResearchMarketMemoryProbabilityCostGuardConfig(**values)


def observation(
    record_ref: str = "alpha-record",
    sample_ref: str = "sample-001",
    *,
    observed_at: datetime | None = None,
    memory_probability: Decimal = d("0.510000"),
    current_probability: Decimal = d("0.530000"),
    cost_ratio: Decimal = d("0.010000"),
    memory_decay_ratio: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketMemoryProbabilityCostGuardObservation(
        record_ref=record_ref,
        sample_ref=sample_ref,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=5),
        memory_probability=memory_probability,
        current_probability=current_probability,
        cost_ratio=cost_ratio,
        memory_decay_ratio=memory_decay_ratio,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def public_item(key: str = "mode", value: str = "paper") -> Any:
    module = api()
    return module.ResearchMarketMemoryProbabilityCostGuardPublicPayloadItem(
        key=key,
        value=value,
    )


def report(
    *observations: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
    public_payload: tuple[object, ...] = (),
) -> Any:
    module = api()
    return module.build_research_market_memory_probability_cost_guard_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
        public_payload=public_payload,
    )


def payload_without_digest(payload: dict[str, object]) -> dict[str, object]:
    trimmed = dict(payload)
    trimmed.pop("derived_validation_digest", None)
    return trimmed


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(
            item for nested in value.values() for item in walk_payload_values(nested)
        )
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk_payload_values(nested))
    return (value,)


def assert_no_decimal_objects(value: object) -> None:
    assert not isinstance(value, Decimal)
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_decimal_objects(nested)
    if isinstance(value, list):
        for nested in value:
            assert_no_decimal_objects(nested)


def assert_decimal_only_public_numbers(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only_public_numbers(getattr(value, field.name))
        return
    if isinstance(value, tuple):
        for nested in value:
            assert_decimal_only_public_numbers(nested)
        return
    if isinstance(value, bool) or value is None:
        return
    assert not isinstance(value, (int, float))
    if isinstance(value, Decimal):
        assert type(value) is Decimal


def test_builds_pass_watch_block_rows_with_decimal_only_guard_math() -> None:
    module = api()
    built = report(
        observation("pass-record", "sample-pass"),
        observation(
            "watch-record",
            "sample-watch",
            memory_probability=d("0.400000"),
            current_probability=d("0.500000"),
            cost_ratio=d("0.040000"),
            memory_decay_ratio=d("0.300000"),
        ),
        observation(
            "block-record",
            "sample-block",
            memory_probability=d("0.300000"),
            current_probability=d("0.550000"),
            cost_ratio=d("0.090000"),
            memory_decay_ratio=d("0.500000"),
        ),
        public_payload=(public_item("mode", "paper"), public_item("phase", "alpha")),
    )

    assert type(built) is module.ResearchMarketMemoryProbabilityCostGuardReport
    assert is_dataclass(built)
    assert module.STATUSES == ("pass", "watch", "block")
    assert built.generated_at == GENERATED_AT
    assert built.generated_at.tzinfo is UTC
    assert built.status == "block"
    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.max_probability_gap_ratio == d("0.250000")
    assert built.max_cost_ratio == d("0.090000")
    assert built.max_memory_decay_ratio == d("0.500000")
    assert built.average_guard_pressure == d("0.575833")
    assert built.max_guard_pressure == ONE
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    blocked, watched, passed = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert blocked.probability_gap_ratio == d("0.250000")
    assert blocked.guard_pressure == ONE
    assert blocked.reason_codes == (
        "memory_probability_cost_guard_block",
        "memory_probability_cost_guard_cost_ratio_block",
        "memory_probability_cost_guard_memory_decay_block",
        "memory_probability_cost_guard_probability_gap_block",
    )
    assert watched.probability_gap_ratio == d("0.100000")
    assert watched.guard_pressure == d("0.575000")
    assert watched.reason_codes == (
        "memory_probability_cost_guard_cost_ratio_watch",
        "memory_probability_cost_guard_memory_decay_watch",
        "memory_probability_cost_guard_probability_gap_watch",
        "memory_probability_cost_guard_watch",
    )
    assert passed.guard_pressure == d("0.152500")
    assert passed.reason_codes == ("memory_probability_cost_guard_pass",)
    assert all(row.paper_only and row.report_only and row.readonly for row in built.rows)
    assert built.public_payload == (public_item("mode", "paper"), public_item("phase", "alpha"))
    assert_decimal_only_public_numbers(built)


def test_empty_inputs_block_with_report_only_no_inputs_reason() -> None:
    module = api()
    built = report()

    assert built.status == "block"
    assert built.input_count == ZERO
    assert built.row_count == ZERO
    assert built.pass_count == ZERO
    assert built.watch_count == ZERO
    assert built.block_count == ZERO
    assert built.average_guard_pressure == ZERO
    assert built.max_guard_pressure == ZERO
    assert built.rows == ()
    assert built.reason_codes == ("memory_probability_cost_guard_no_inputs",)
    assert built.reason_code_counts == (
        module.ResearchMarketMemoryProbabilityCostGuardReasonCodeCount(
            reason_code="memory_probability_cost_guard_no_inputs",
            count=ONE,
        ),
    )


def test_payload_is_deterministic_and_validated_by_sha256_digest() -> None:
    built = report(
        observation("alpha-record", "sample-alpha"),
        observation(
            "beta-record",
            "sample-beta",
            memory_probability=d("0.420000"),
            current_probability=d("0.520000"),
            cost_ratio=d("0.040000"),
            memory_decay_ratio=d("0.300000"),
        ),
        public_payload=(public_item("mode", "paper"),),
    )

    payload = built.payload
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    encoded_again = json.dumps(
        built.payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert encoded == encoded_again
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["input_count"] == "2.000000"
    assert payload["rows"][0]["observation_count"] == "1.000000"
    assert payload["derived_validation_digest"] == built.derived_validation_digest
    assert len(built.derived_validation_digest) == 64
    assert all(char in "0123456789abcdef" for char in built.derived_validation_digest)
    assert_no_decimal_objects(payload)

    expected_digest = hashlib.sha256(
        json.dumps(
            payload_without_digest(payload),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert expected_digest == built.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, public_payload=(public_item("phase", "changed"),))


def test_validation_enforces_frozen_flags_decimal_ratios_and_utc_time() -> None:
    built = report(observation())

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].guard_pressure = ZERO  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(api().ResearchMarketMemoryProbabilityCostGuardReport):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)
    with pytest.raises(ValueError, match="Decimal"):
        observation(cost_ratio=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(memory_probability=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="between zero and one"):
        observation(current_probability=d("1.000001"))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 9, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 9))
    with pytest.raises(ValueError, match="after generated_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate"):
        report(observation("dup-record", "dup-sample"), observation("dup-record", "dup-sample"))
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")


def test_public_payload_hides_raw_refs_and_rejects_sensitive_public_items() -> None:
    module = api()
    raw_ref = "Will event resolve from https://private.example/path?secret=value"
    raw_sample = "sample-private-001"
    built = report(
        observation(raw_ref, raw_sample),
        observation(
            raw_ref,
            "sample-private-002",
            cost_ratio=d("0.040000"),
        ),
    )
    payload = built.payload
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)

    assert raw_ref not in encoded
    assert raw_sample not in encoded
    assert hashlib.sha256(raw_ref.encode("utf-8")).hexdigest() in encoded

    blocked_fragments = (
        "candi" + "date",
        "sou" + "rce",
        "u" + "rl",
        "te" + "xt",
        "d" + "sn",
        "ta" + "ble",
        "tok" + "en",
    )
    for fragment in blocked_fragments:
        assert fragment not in encoded.lower()

    with pytest.raises(ValueError, match="public payload"):
        module.ResearchMarketMemoryProbabilityCostGuardPublicPayloadItem(
            "sou" + "rce_" + "u" + "rl",
            "paper",
        )
    with pytest.raises(ValueError, match="public payload"):
        module.ResearchMarketMemoryProbabilityCostGuardPublicPayloadItem(
            "mode",
            "https://private.example/path?" + "tok" + "en=value",
        )


def test_module_excludes_external_side_effect_and_decision_capabilities() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    blocked_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "web3",
    }
    assert not (imported_roots & blocked_imports)
    assert ".get(" not in source
    assert ".post(" not in source
    assert ".execute(" not in source
    assert "subprocess" not in source
