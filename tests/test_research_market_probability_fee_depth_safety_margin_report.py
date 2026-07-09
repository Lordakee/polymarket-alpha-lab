from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
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
    "research_market_probability_fee_depth_safety_margin_report"
)
GENERATED_AT = datetime(2026, 7, 9, 10, 0, tzinfo=UTC)
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
            module.DEFAULT_RESEARCH_MARKET_PROBABILITY_FEE_DEPTH_SAFETY_MARGIN_REPORT_CONFIG_VERSION
        ),
        "minimum_pass_probability_edge": d("0.080000"),
        "minimum_watch_probability_edge": d("0.030000"),
        "maximum_pass_fee_ratio": d("0.010000"),
        "maximum_watch_fee_ratio": d("0.030000"),
        "minimum_pass_available_depth": d("1000.000000"),
        "minimum_watch_available_depth": d("250.000000"),
        "minimum_pass_safety_margin_score": d("0.750000"),
        "minimum_watch_safety_margin_score": d("0.450000"),
        "probability_edge_weight": d("0.400000"),
        "fee_efficiency_weight": d("0.250000"),
        "depth_resilience_weight": d("0.350000"),
    }
    values.update(overrides)
    return module.ResearchMarketProbabilityFeeDepthSafetyMarginConfig(**values)


def market_input(
    private_ref: str = "private-alpha",
    *,
    observed_at: datetime = GENERATED_AT,
    research_probability: Decimal = d("0.660000"),
    venue_probability: Decimal = d("0.560000"),
    fee_ratio: Decimal = d("0.005000"),
    available_depth: Decimal = d("1500.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketProbabilityFeeDepthSafetyMarginInput(
        private_ref=private_ref,
        observed_at=observed_at,
        research_probability=research_probability,
        venue_probability=venue_probability,
        fee_ratio=fee_ratio,
        available_depth=available_depth,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_market_probability_fee_depth_safety_margin_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_payload_values(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk_payload_values(nested))
    return (value,)


def test_scores_probability_fee_depth_safety_margin_pass_watch_and_block_rows() -> None:
    module = api()
    built = report(
        market_input(
            "block-private",
            research_probability=d("0.550000"),
            venue_probability=d("0.530000"),
            fee_ratio=d("0.040000"),
            available_depth=d("100.000000"),
            reason_codes=("manual_check",),
        ),
        market_input(
            "watch-private",
            research_probability=d("0.620000"),
            venue_probability=d("0.570000"),
            fee_ratio=d("0.020000"),
            available_depth=d("625.000000"),
        ),
        market_input("pass-private"),
    )

    assert type(built) is module.ResearchMarketProbabilityFeeDepthSafetyMarginReport
    assert module.PROBABILITY_FEE_DEPTH_SAFETY_MARGIN_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert built.generated_at == GENERATED_AT
    assert built.status == "block"
    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.low_probability_edge_count == d("2.000000")
    assert built.high_fee_count == d("2.000000")
    assert built.thin_depth_count == d("2.000000")
    assert built.average_safety_margin_score == d("0.486667")
    assert built.min_probability_edge == d("0.020000")
    assert built.max_fee_ratio == d("0.040000")
    assert built.min_available_depth == d("100.000000")

    block_row, watch_row, pass_row = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert block_row.probability_edge == d("0.020000")
    assert block_row.safety_margin_score == ZERO
    assert block_row.reason_codes == (
        "input_manual_check",
        "safety_margin_available_depth_block",
        "safety_margin_fee_ratio_block",
        "safety_margin_probability_edge_block",
        "safety_margin_status_block",
    )
    assert watch_row.probability_edge == d("0.050000")
    assert watch_row.probability_edge_score == d("0.400000")
    assert watch_row.fee_efficiency_score == d("0.500000")
    assert watch_row.depth_resilience_score == d("0.500000")
    assert watch_row.safety_margin_score == d("0.460000")
    assert watch_row.status == "watch"
    assert pass_row.probability_edge == d("0.100000")
    assert pass_row.safety_margin_score == ONE
    assert pass_row.reason_codes == (
        "safety_margin_available_depth_pass",
        "safety_margin_fee_ratio_pass",
        "safety_margin_probability_edge_pass",
        "safety_margin_status_pass",
    )


def test_empty_report_blocks_without_live_or_recommendation_surface() -> None:
    module = api()
    built = report()

    assert built.status == "block"
    assert built.input_count == ZERO
    assert built.row_count == ZERO
    assert built.rows == ()
    assert built.average_safety_margin_score == ZERO
    assert built.reason_codes == ("safety_margin_no_inputs",)
    assert built.reason_code_counts == (
        module.ResearchMarketProbabilityFeeDepthSafetyMarginReasonCodeCount(
            reason_code="safety_margin_no_inputs",
            count=ONE,
        ),
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_public_payload_is_deterministic_digest_validated_and_public_safe() -> None:
    module = api()
    first = report(
        market_input(
            "raw-candidate-id-123/market-id-99/will-this-question-resolve/"
            "https://example.test/source?token=secret&wallet=abc&order=1",
            reason_codes=("zeta", "alpha"),
        ),
        market_input("alpha-private", fee_ratio=d("0.020000")),
    )
    second = report(
        market_input("alpha-private", fee_ratio=d("0.020000")),
        market_input(
            "raw-candidate-id-123/market-id-99/will-this-question-resolve/"
            "https://example.test/source?token=secret&wallet=abc&order=1",
            reason_codes=("alpha", "zeta"),
        ),
    )

    first_payload = module.research_market_probability_fee_depth_safety_margin_report_payload(
        first,
    )
    second_payload = second.public_payload
    digest_payload = dict(first_payload)
    provided_digest = digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert provided_digest == hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["rows"][0]["fee_ratio"] == "0.020000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))
    assert not any(
        isinstance(value, (float, int)) and not isinstance(value, bool)
        for value in walk_payload_values(first_payload)
    )
    assert (
        module.validate_research_market_probability_fee_depth_safety_margin_report_payload(
            first_payload,
        )
        == first_payload
    )

    rendered = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "raw-candidate-id-123",
        "market-id-99",
        "will-this-question-resolve",
        "https://example.test",
        "source?token",
        "secret",
        "wallet",
        "order",
        "private_ref",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "trade",
        "live",
        "recommend",
        "position",
        "sizing",
        "execution",
    ):
        assert forbidden not in rendered

    tampered = dict(first_payload)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_probability_fee_depth_safety_margin_report_payload(
            tampered,
        )

    invalid_status_payload = json.loads(json.dumps(first_payload))
    invalid_status_payload["rows"][0]["status"] = "blocked"
    invalid_status_digest_payload = dict(invalid_status_payload)
    invalid_status_digest_payload.pop("derived_validation_digest")
    invalid_status_payload["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            invalid_status_digest_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    with pytest.raises(ValueError, match="status"):
        module.validate_research_market_probability_fee_depth_safety_margin_report_payload(
            invalid_status_payload,
        )

    unsafe_report = replace(first)
    object.__setattr__(
        unsafe_report,
        "reason_codes",
        ("safety_margin_status_pass", "token_seen"),
    )
    object.__setattr__(unsafe_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_market_probability_fee_depth_safety_margin_report_payload(
            unsafe_report,
        )


def test_validation_rejects_bad_boundaries_types_flags_and_inconsistent_objects() -> None:
    module = api()
    custom = config(
        minimum_pass_probability_edge=d("0.100000"),
        minimum_watch_probability_edge=d("0.040000"),
    )
    custom_report = report(
        market_input(
            "custom-pass",
            research_probability=d("0.700000"),
            venue_probability=d("0.600000"),
        ),
        cfg=custom,
    )

    assert custom_report.status == "pass"
    assert custom_report.rows[0].probability_edge_score == ONE
    with pytest.raises(ValueError, match="minimum_pass_probability_edge"):
        config(minimum_pass_probability_edge=DecimalSubclass("0.080000"))
    with pytest.raises(ValueError, match="maximum_watch_fee_ratio"):
        config(maximum_watch_fee_ratio=0.03)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="minimum_pass_probability_edge"):
        config(minimum_pass_probability_edge=d("0.020000"))
    with pytest.raises(ValueError, match="maximum_pass_fee_ratio"):
        config(maximum_pass_fee_ratio=d("0.040000"))
    with pytest.raises(ValueError, match="minimum_pass_available_depth"):
        config(minimum_pass_available_depth=d("100.000000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(probability_edge_weight=d("0.410000"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_probability_fee_depth_safety_margin_report(
            (market_input(),),
            config=config(),
            generated_at=datetime(2026, 7, 9, 10, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_probability_fee_depth_safety_margin_report(
            (market_input(),),
            config=config(),
            generated_at=DatetimeSubclass(2026, 7, 9, 10, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        market_input(observed_at=datetime(2026, 7, 9, 10, 0))
    with pytest.raises(ValueError, match="research_probability"):
        market_input(research_probability=d("NaN"))
    with pytest.raises(ValueError, match="venue_probability"):
        market_input(venue_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fee_ratio"):
        market_input(fee_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="available_depth"):
        market_input(available_depth=-d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        market_input(reason_codes=("token_seen",))
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report(market_input(readonly=False))

    built = report(market_input())
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="safety_margin_score"):
        replace(built.rows[0], safety_margin_score=ZERO)
    with pytest.raises(ValueError, match="status"):
        replace(built, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_probability_fee_depth_safety_margin_report_payload(object())


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    built = report(market_input())

    for item in (config(), market_input(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].safety_margin_score = ZERO  # type: ignore[misc]

    public_classes = (
        module.ResearchMarketProbabilityFeeDepthSafetyMarginConfig,
        module.ResearchMarketProbabilityFeeDepthSafetyMarginInput,
        module.ResearchMarketProbabilityFeeDepthSafetyMarginRow,
        module.ResearchMarketProbabilityFeeDepthSafetyMarginReasonCodeCount,
        module.ResearchMarketProbabilityFeeDepthSafetyMarginReport,
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


def test_owned_module_has_no_storage_network_wallet_or_decision_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_probability_fee_depth_safety_margin_report.py"
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
        "wallet",
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
