from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_fee_probability_memory_ladder_report"
)
GENERATED_AT = datetime(2026, 7, 9, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_FEE_PROBABILITY_MEMORY_LADDER_REPORT_CONFIG_VERSION
        ),
        "minimum_pass_probability_gap": d("0.080000"),
        "minimum_watch_probability_gap": d("0.030000"),
        "maximum_pass_fee_ratio": d("0.010000"),
        "maximum_watch_fee_ratio": d("0.030000"),
        "minimum_pass_memory_confidence": d("0.800000"),
        "minimum_watch_memory_confidence": d("0.500000"),
        "probability_gap_weight": d("0.400000"),
        "fee_efficiency_weight": d("0.300000"),
        "memory_confidence_weight": d("0.300000"),
    }
    values.update(overrides)
    return module.ResearchMarketFeeProbabilityMemoryLadderConfig(**values)


def ladder_input(
    private_ref: str = "private-alpha",
    *,
    observed_at: datetime = GENERATED_AT,
    research_probability: Decimal = d("0.660000"),
    venue_probability: Decimal = d("0.560000"),
    fee_ratio: Decimal = d("0.005000"),
    memory_confidence: Decimal = d("0.900000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketFeeProbabilityMemoryLadderInput(
        private_ref=private_ref,
        observed_at=observed_at,
        research_probability=research_probability,
        venue_probability=venue_probability,
        fee_ratio=fee_ratio,
        memory_confidence=memory_confidence,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_market_fee_probability_memory_ladder_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in payload_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in payload_values(child))
    return (value,)


def test_builds_deterministic_public_payload_and_validates_digest() -> None:
    module = api()
    raw_private_ref = (
        "raw-candidate-42/market-99/https://example.test/source"
        "?token=secret&dsn=hidden&table=markets"
    )
    first = report(
        ladder_input("pass-private"),
        ladder_input(
            raw_private_ref,
            research_probability=d("0.540000"),
            venue_probability=d("0.530000"),
            fee_ratio=d("0.050000"),
            memory_confidence=d("0.200000"),
            reason_codes=("manual_review",),
        ),
        ladder_input(
            "watch-private",
            observed_at=datetime(2026, 7, 9, 11, 0, tzinfo=timezone(timedelta(hours=-4))),
            research_probability=d("0.620000"),
            venue_probability=d("0.570000"),
            fee_ratio=d("0.020000"),
            memory_confidence=d("0.650000"),
        ),
    )
    second = report(
        ladder_input(
            "watch-private",
            observed_at=datetime(2026, 7, 9, 15, 0, tzinfo=UTC),
            research_probability=d("0.620000"),
            venue_probability=d("0.570000"),
            fee_ratio=d("0.020000"),
            memory_confidence=d("0.650000"),
        ),
        ladder_input(
            raw_private_ref,
            research_probability=d("0.540000"),
            venue_probability=d("0.530000"),
            fee_ratio=d("0.050000"),
            memory_confidence=d("0.200000"),
            reason_codes=("manual_review",),
        ),
        ladder_input("pass-private"),
    )

    assert module.MARKET_FEE_PROBABILITY_MEMORY_LADDER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert type(first) is module.ResearchMarketFeeProbabilityMemoryLadderReport
    assert first.generated_at == GENERATED_AT
    assert first.status == "block"
    assert first.input_count == d("3.000000")
    assert first.row_count == d("3.000000")
    assert first.pass_count == d("1.000000")
    assert first.watch_count == d("1.000000")
    assert first.block_count == d("1.000000")
    assert first.low_probability_gap_count == d("2.000000")
    assert first.high_fee_count == d("2.000000")
    assert first.low_memory_confidence_count == d("2.000000")
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert {row.status for row in first.rows} <= {"pass", "watch", "block"}
    assert first.rows[0].reason_codes == (
        "input_manual_review",
        "ladder_fee_ratio_block",
        "ladder_memory_confidence_block",
        "ladder_probability_gap_block",
        "ladder_status_block",
    )
    assert first.average_ladder_score == d("0.486667")
    assert first.min_probability_gap == d("0.010000")
    assert first.max_fee_ratio == d("0.050000")
    assert first.min_memory_confidence == d("0.200000")
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True

    first_payload = module.research_market_fee_probability_memory_ladder_report_payload(first)
    second_payload = second.public_payload
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True)
    assert first_payload["generated_at"] == "2026-07-09T15:00:00+00:00"
    assert first_payload["rows"][0]["status"] == "block"
    assert first_payload["rows"][0]["fee_ratio"] == "0.050000"
    assert first_payload["rows"][0]["memory_confidence"] == "0.200000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in payload_values(first_payload))
    assert not any(
        isinstance(value, (float, int)) and not isinstance(value, bool)
        for value in payload_values(first_payload)
    )

    digest_payload = dict(first_payload)
    provided_digest = digest_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert provided_digest == expected_digest
    assert (
        module.validate_research_market_fee_probability_memory_ladder_report_payload(
            first_payload,
        )
        == first_payload
    )

    rendered = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "raw-candidate-42",
        "market-99",
        "https://example.test",
        "source?token",
        "secret",
        "dsn=hidden",
        "table=markets",
        "private_ref",
        "candidate_id",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "table_name",
        "token",
    ):
        assert forbidden not in rendered


def test_empty_report_blocks_without_private_surface() -> None:
    module = api()
    built = report()

    assert built.status == "block"
    assert built.input_count == ZERO
    assert built.row_count == ZERO
    assert built.rows == ()
    assert built.average_ladder_score == ZERO
    assert built.min_probability_gap == ZERO
    assert built.max_fee_ratio == ZERO
    assert built.min_memory_confidence == ZERO
    assert built.reason_codes == ("ladder_no_inputs",)
    assert built.reason_code_counts == (
        module.ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount(
            reason_code="ladder_no_inputs",
            count=ONE,
        ),
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_validation_rejects_bad_types_flags_statuses_and_digest_tampering() -> None:
    module = api()

    with pytest.raises(ValueError, match="minimum_pass_probability_gap"):
        config(minimum_pass_probability_gap=DecimalSubclass("0.080000"))
    with pytest.raises(ValueError, match="maximum_watch_fee_ratio"):
        config(maximum_watch_fee_ratio=0.03)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="minimum_pass_probability_gap"):
        config(minimum_pass_probability_gap=d("0.010000"))
    with pytest.raises(ValueError, match="maximum_pass_fee_ratio"):
        config(maximum_pass_fee_ratio=d("0.040000"))
    with pytest.raises(ValueError, match="minimum_pass_memory_confidence"):
        config(minimum_pass_memory_confidence=d("0.400000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(probability_gap_weight=d("0.410000"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_fee_probability_memory_ladder_report(
            (ladder_input(),),
            config=config(),
            generated_at=datetime(2026, 7, 9, 15, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_fee_probability_memory_ladder_report(
            (ladder_input(),),
            config=config(),
            generated_at=DatetimeSubclass(2026, 7, 9, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        ladder_input(observed_at=datetime(2026, 7, 9, 15, 0))
    with pytest.raises(ValueError, match="research_probability"):
        ladder_input(research_probability=d("NaN"))
    with pytest.raises(ValueError, match="venue_probability"):
        ladder_input(venue_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fee_ratio"):
        ladder_input(fee_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="memory_confidence"):
        ladder_input(memory_confidence=-d("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        ladder_input(reason_codes=("token_seen",))
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report(ladder_input(readonly=False))

    built = report(ladder_input())
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="ladder_score"):
        replace(built.rows[0], ladder_score=ZERO)
    with pytest.raises(ValueError, match="status"):
        replace(built, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)

    payload = built.public_payload
    tampered = dict(payload)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_fee_probability_memory_ladder_report_payload(
            tampered,
        )
    with pytest.raises(ValueError, match="report"):
        module.research_market_fee_probability_memory_ladder_report_payload(object())


def test_row_validation_uses_non_default_config_weights() -> None:
    cfg = config(
        probability_gap_weight=d("0.200000"),
        fee_efficiency_weight=d("0.500000"),
        memory_confidence_weight=d("0.300000"),
    )
    built = report(
        ladder_input(
            research_probability=d("0.650000"),
            venue_probability=d("0.550000"),
            fee_ratio=d("0.020000"),
            memory_confidence=d("0.650000"),
        ),
        cfg=cfg,
    )

    row = built.rows[0]
    assert row.probability_gap_score == d("1.000000")
    assert row.fee_efficiency_score == d("0.500000")
    assert row.memory_confidence_score == d("0.500000")
    assert row.ladder_score == d("0.600000")
    assert row.probability_gap_weight == d("0.200000")
    assert row.fee_efficiency_weight == d("0.500000")
    assert row.memory_confidence_weight == d("0.300000")

    with pytest.raises(ValueError, match="ladder_score"):
        replace(
            row,
            probability_gap_weight=d("0.400000"),
            fee_efficiency_weight=d("0.300000"),
            memory_confidence_weight=d("0.300000"),
        )


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    built = report(ladder_input())

    for item in (config(), ladder_input(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)
        assert item.__dataclass_params__.frozen is True
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].ladder_score = ZERO  # type: ignore[misc]

    public_classes = (
        module.ResearchMarketFeeProbabilityMemoryLadderConfig,
        module.ResearchMarketFeeProbabilityMemoryLadderInput,
        module.ResearchMarketFeeProbabilityMemoryLadderRow,
        module.ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount,
        module.ResearchMarketFeeProbabilityMemoryLadderReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        for field in fields(klass):
            if field.name in {
                "paper_only",
                "report_only",
                "readonly",
                "private_ref",
                "config_version",
                "public_row_ref",
                "status",
                "reason_code",
                "reason_codes",
                "reason_code_counts",
                "rows",
                "derived_validation_digest",
                "observed_at",
                "generated_at",
            }:
                continue
            assert field.type in (Decimal, "Decimal")


def test_public_dataclasses_reject_subclassing() -> None:
    module = api()
    for klass in (
        module.ResearchMarketFeeProbabilityMemoryLadderConfig,
        module.ResearchMarketFeeProbabilityMemoryLadderInput,
        module.ResearchMarketFeeProbabilityMemoryLadderRow,
        module.ResearchMarketFeeProbabilityMemoryLadderReasonCodeCount,
        module.ResearchMarketFeeProbabilityMemoryLadderReport,
    ):
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"{klass.__name__}Subclass", (klass,), {})


def test_owned_module_has_no_durable_live_or_decision_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_fee_probability_memory_ladder_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "read_text",
        "write_text",
        "connect(",
        "execute(",
        "database",
        "network",
        "wallet",
        "auth",
        "private_key",
        "api_key",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "position",
        "sizing",
        "execution",
    ):
        assert forbidden not in source

    forbidden_calls = {
        "open",
        "connect",
        "execute",
        "request",
        "create_order",
        "submit_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
