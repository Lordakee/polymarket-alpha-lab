from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_fee_depth_resolution_margin_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_FEE_DEPTH_RESOLUTION_MARGIN_REPORT_CONFIG_VERSION
        ),
        "maximum_pass_fee_drag_ratio": d("0.010000"),
        "maximum_watch_fee_drag_ratio": d("0.030000"),
        "minimum_pass_available_depth": d("1000.000000"),
        "minimum_watch_available_depth": d("250.000000"),
        "minimum_pass_resolution_margin_ratio": d("0.100000"),
        "minimum_watch_resolution_margin_ratio": d("0.030000"),
        "minimum_pass_margin_score": d("0.750000"),
        "minimum_watch_margin_score": d("0.450000"),
        "fee_drag_weight": d("0.300000"),
        "available_depth_weight": d("0.350000"),
        "resolution_margin_weight": d("0.350000"),
    }
    values.update(overrides)
    return module.ResearchMarketFeeDepthResolutionMarginConfig(**values)


def margin_input(
    private_signal_ref: str = "private-alpha",
    *,
    observed_at: datetime = GENERATED_AT,
    fee_drag_ratio: Decimal = d("0.005000"),
    available_depth: Decimal = d("1500.000000"),
    resolution_margin_ratio: Decimal = d("0.120000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketFeeDepthResolutionMarginInput(
        private_signal_ref=private_signal_ref,
        observed_at=observed_at,
        fee_drag_ratio=fee_drag_ratio,
        available_depth=available_depth,
        resolution_margin_ratio=resolution_margin_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_market_fee_depth_resolution_margin_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_blocks_without_sensitive_public_identifiers() -> None:
    module = api()
    built = report()

    assert module.FEE_DEPTH_RESOLUTION_MARGIN_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "FEE_DEPTH_RESOLUTION_MARGIN_STATUSES",
        "DEFAULT_RESEARCH_MARKET_FEE_DEPTH_RESOLUTION_MARGIN_REPORT_CONFIG_VERSION",
        "ResearchMarketFeeDepthResolutionMarginConfig",
        "ResearchMarketFeeDepthResolutionMarginInput",
        "ResearchMarketFeeDepthResolutionMarginReasonCodeCount",
        "ResearchMarketFeeDepthResolutionMarginReport",
        "ResearchMarketFeeDepthResolutionMarginRow",
        "build_research_market_fee_depth_resolution_margin_report",
        "research_market_fee_depth_resolution_margin_report_payload",
        "validate_research_market_fee_depth_resolution_margin_report_payload",
    )
    assert built.generated_at == GENERATED_AT
    assert built.status == "block"
    assert built.input_count == ZERO
    assert built.row_count == ZERO
    assert built.pass_count == ZERO
    assert built.watch_count == ZERO
    assert built.block_count == ZERO
    assert built.average_margin_score == ZERO
    assert built.reason_codes == ("margin_no_inputs",)
    assert built.reason_code_counts == (
        module.ResearchMarketFeeDepthResolutionMarginReasonCodeCount(
            reason_code="margin_no_inputs",
            count=ONE,
        ),
    )
    assert built.rows == ()
    assert len(built.derived_validation_digest) == 64
    int(built.derived_validation_digest, 16)
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_scores_fee_depth_resolution_margin_rows_and_rollups() -> None:
    built = report(
        margin_input(
            "block-private",
            fee_drag_ratio=d("0.040000"),
            available_depth=d("100.000000"),
            resolution_margin_ratio=d("0.010000"),
            reason_codes=("manual_check",),
        ),
        margin_input(
            "watch-private",
            fee_drag_ratio=d("0.020000"),
            available_depth=d("625.000000"),
            resolution_margin_ratio=d("0.065000"),
        ),
        margin_input("pass-private"),
    )

    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.status == "block"
    assert built.high_fee_drag_count == d("2.000000")
    assert built.thin_depth_count == d("2.000000")
    assert built.low_resolution_margin_count == d("2.000000")
    assert built.average_margin_score == d("0.500000")
    assert built.min_available_depth == d("100.000000")
    assert built.max_fee_drag_ratio == d("0.040000")
    assert built.min_resolution_margin_ratio == d("0.010000")

    block_row, watch_row, pass_row = built.rows
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert block_row.margin_score == ZERO
    assert block_row.reason_codes == (
        "input_manual_check",
        "margin_available_depth_block",
        "margin_fee_drag_block",
        "margin_resolution_margin_block",
        "margin_status_block",
    )
    assert watch_row.fee_drag_score == d("0.500000")
    assert watch_row.available_depth_score == d("0.500000")
    assert watch_row.resolution_margin_score == d("0.500000")
    assert watch_row.margin_score == d("0.500000")
    assert pass_row.margin_score == ONE
    assert pass_row.reason_codes == (
        "margin_available_depth_pass",
        "margin_fee_drag_pass",
        "margin_resolution_margin_pass",
        "margin_status_pass",
    )


def test_resolution_margin_boundaries_are_inclusive() -> None:
    boundary = report(
        margin_input("pass-boundary", resolution_margin_ratio=d("0.100000")),
        margin_input("watch-boundary", resolution_margin_ratio=d("0.030000")),
        margin_input("block-boundary", resolution_margin_ratio=d("0.029999")),
    )

    assert tuple(row.status for row in boundary.rows) == ("block", "watch", "pass")
    block_row, watch_row, pass_row = boundary.rows
    assert "margin_resolution_margin_block" in block_row.reason_codes
    assert "margin_resolution_margin_watch" in watch_row.reason_codes
    assert "margin_resolution_margin_pass" in pass_row.reason_codes


def test_public_payload_is_deterministic_decimal_string_serialized_and_digest_validated() -> None:
    module = api()
    first = report(
        margin_input("zulu-private", reason_codes=("zeta", "alpha")),
        margin_input("alpha-private"),
    )
    second = report(
        margin_input("alpha-private"),
        margin_input("zulu-private", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_fee_depth_resolution_margin_report_payload(
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
    assert first_payload["rows"][0]["fee_drag_ratio"] == "0.005000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))
    assert not any(
        isinstance(value, (float, int)) and not isinstance(value, bool)
        for value in walk_payload_values(first_payload)
    )
    assert module.validate_research_market_fee_depth_resolution_margin_report_payload(
        first_payload,
    ) == first_payload

    tampered = dict(first_payload)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_fee_depth_resolution_margin_report_payload(
            tampered,
        )


def test_public_payload_excludes_private_refs_sensitive_text_and_decision_surfaces() -> None:
    module = api()
    built = report(
        margin_input(
            "raw-candidate-id-123/market-id-99/will-this-question-resolve/"
            "https://example.test/source?token=secret&wallet=abc",
        ),
    )
    payload = module.research_market_fee_depth_resolution_margin_report_payload(built)
    rendered = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "raw-candidate-id-123",
        "market-id-99",
        "will-this-question-resolve",
        "https://example.test",
        "source?token",
        "secret",
        "wallet",
        "private_signal_ref",
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
        "recommend",
        "position",
        "sizing",
        "execution",
    ):
        assert forbidden not in rendered

    unsafe_report = replace(built)
    object.__setattr__(unsafe_report, "reason_codes", ("margin_status_pass", "token_seen"))
    object.__setattr__(unsafe_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_market_fee_depth_resolution_margin_report_payload(
            unsafe_report,
        )


def test_rejects_bad_numeric_datetime_flag_status_digest_and_custom_config() -> None:
    module = api()

    with pytest.raises(ValueError, match="maximum_pass_fee_drag_ratio"):
        config(maximum_pass_fee_drag_ratio=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="maximum_watch_fee_drag_ratio"):
        config(maximum_watch_fee_drag_ratio=0.03)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="maximum_pass_fee_drag_ratio"):
        config(maximum_pass_fee_drag_ratio=d("0.040000"))
    with pytest.raises(ValueError, match="minimum_pass_available_depth"):
        config(minimum_pass_available_depth=d("100.000000"))
    with pytest.raises(ValueError, match="minimum_pass_resolution_margin_ratio"):
        config(minimum_pass_resolution_margin_ratio=d("0.010000"))
    with pytest.raises(ValueError, match="minimum_pass_margin_score"):
        config(minimum_pass_margin_score=d("0.100000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(fee_drag_weight=d("0.400000"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_fee_depth_resolution_margin_report(
            (margin_input(),),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_fee_depth_resolution_margin_report(
            (margin_input(),),
            config=config(),
            generated_at=DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        margin_input(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="fee_drag_ratio"):
        margin_input(fee_drag_ratio=d("NaN"))
    with pytest.raises(ValueError, match="available_depth"):
        margin_input(available_depth=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="available_depth"):
        margin_input(available_depth=-d("1.000000"))
    with pytest.raises(ValueError, match="resolution_margin_ratio"):
        margin_input(resolution_margin_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="resolution_margin_ratio"):
        margin_input(resolution_margin_ratio=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        margin_input(reason_codes=("token_seen",))
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report(margin_input(readonly=False))

    built = report(margin_input())
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="margin_score"):
        replace(built.rows[0], margin_score=d("1.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(built, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_fee_depth_resolution_margin_report_payload(object())

    unsafe_payload = dict(
        module.research_market_fee_depth_resolution_margin_report_payload(built),
    )
    unsafe_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_market_fee_depth_resolution_margin_report_payload(
            unsafe_payload,
        )

    custom_weight_report = report(
        margin_input(
            "custom-weight-row",
            fee_drag_ratio=d("0.020000"),
            available_depth=d("625.000000"),
            resolution_margin_ratio=d("0.065000"),
        ),
        cfg=config(
            fee_drag_weight=d("0.200000"),
            available_depth_weight=d("0.500000"),
            resolution_margin_weight=d("0.300000"),
        ),
    )
    assert custom_weight_report.rows[0].margin_score == d("0.500000")


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    built = report(margin_input())

    for item in (config(), margin_input(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].margin_score = ZERO  # type: ignore[misc]

    public_classes = (
        module.ResearchMarketFeeDepthResolutionMarginConfig,
        module.ResearchMarketFeeDepthResolutionMarginInput,
        module.ResearchMarketFeeDepthResolutionMarginRow,
        module.ResearchMarketFeeDepthResolutionMarginReasonCodeCount,
        module.ResearchMarketFeeDepthResolutionMarginReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        for field in fields(klass):
            if field.name in {
                "paper_only",
                "report_only",
                "readonly",
                "private_signal_ref",
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


def test_owned_module_has_no_storage_network_or_decision_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_fee_depth_resolution_margin_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
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
        assert forbidden not in text

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


def walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
