from __future__ import annotations

import ast
import copy
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_fee_drag_sensitivity_report import (
    DEFAULT_RESEARCH_MARKET_FEE_DRAG_SENSITIVITY_CONFIG_VERSION,
    FEE_DRAG_SENSITIVITY_STATUSES,
    ResearchMarketFeeDragSensitivityConfig,
    ResearchMarketFeeDragSensitivityInput,
    ResearchMarketFeeDragSensitivityReasonCodeCount,
    ResearchMarketFeeDragSensitivityReport,
    ResearchMarketFeeDragSensitivityRow,
    build_research_market_fee_drag_sensitivity_report,
    research_market_fee_drag_sensitivity_report_payload,
    validate_research_market_fee_drag_sensitivity_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_market_fee_drag_sensitivity_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate_digest(raw_candidate_id: str) -> str:
    return hashlib.sha256(raw_candidate_id.encode("utf-8")).hexdigest()


def config(**overrides: object) -> ResearchMarketFeeDragSensitivityConfig:
    values: dict[str, object] = {
        "config_version": DEFAULT_RESEARCH_MARKET_FEE_DRAG_SENSITIVITY_CONFIG_VERSION,
        "base_manual_edge_rate": d("0.020000"),
        "watch_minimum_edge_needed_rate": d("0.060000"),
        "block_minimum_edge_needed_rate": d("0.100000"),
    }
    values.update(overrides)
    return ResearchMarketFeeDragSensitivityConfig(**values)


def input_row(
    raw_candidate_id: str = "fee-drag-case-pass",
    *,
    fee_rate: Decimal = d("0.005000"),
    spread_rate: Decimal = d("0.005000"),
    slippage_rate: Decimal = d("0.005000"),
    settlement_friction_rate: Decimal = d("0.002000"),
    confidence_haircut_rate: Decimal = d("0.003000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketFeeDragSensitivityInput:
    return ResearchMarketFeeDragSensitivityInput(
        raw_candidate_id=raw_candidate_id,
        fee_rate=fee_rate,
        spread_rate=spread_rate,
        slippage_rate=slippage_rate,
        settlement_friction_rate=settlement_friction_rate,
        confidence_haircut_rate=confidence_haircut_rate,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchMarketFeeDragSensitivityInput,
    cfg: ResearchMarketFeeDragSensitivityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketFeeDragSensitivityReport:
    return build_research_market_fee_drag_sensitivity_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def test_builds_fee_drag_sensitivity_rows_counts_and_minimum_edge_needed() -> None:
    built = report(
        input_row(
            "fee-drag-case-watch",
            fee_rate=d("0.015000"),
            spread_rate=d("0.015000"),
            slippage_rate=d("0.010000"),
            settlement_friction_rate=d("0.005000"),
            confidence_haircut_rate=d("0.010000"),
        ),
        input_row(
            "fee-drag-case-block",
            fee_rate=d("0.030000"),
            spread_rate=d("0.025000"),
            slippage_rate=d("0.020000"),
            settlement_friction_rate=d("0.015000"),
            confidence_haircut_rate=d("0.020000"),
            upstream_reason_codes=("analyst_review_needed",),
        ),
        input_row("fee-drag-case-pass", upstream_reason_codes=("manual_research_only",)),
    )

    assert FEE_DRAG_SENSITIVITY_STATUSES == ("pass", "watch", "block")
    assert type(built) is ResearchMarketFeeDragSensitivityReport
    assert built.generated_at == GENERATED_AT
    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.base_manual_edge_rate == d("0.020000")
    assert built.max_minimum_edge_needed_rate == d("0.130000")
    assert built.average_minimum_edge_needed_rate == d("0.081667")
    assert built.status == "block"
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    block_row, watch_row, pass_row = built.rows
    assert [(row.manual_research_status, row.minimum_edge_needed_rate) for row in built.rows] == [
        ("block", d("0.130000")),
        ("watch", d("0.075000")),
        ("pass", d("0.040000")),
    ]
    assert tuple(row.candidate_digest for row in built.rows) == (
        candidate_digest("fee-drag-case-block"),
        candidate_digest("fee-drag-case-watch"),
        candidate_digest("fee-drag-case-pass"),
    )
    assert type(block_row) is ResearchMarketFeeDragSensitivityRow
    assert block_row.total_friction_rate == d("0.110000")
    assert block_row.reason_codes == (
        "fee_drag_confidence_haircut_component",
        "fee_drag_fee_component",
        "fee_drag_minimum_edge_block",
        "fee_drag_settlement_friction_component",
        "fee_drag_slippage_component",
        "fee_drag_spread_component",
        "fee_drag_status_block",
        "input_analyst_review_needed",
    )
    assert watch_row.total_friction_rate == d("0.055000")
    assert "fee_drag_minimum_edge_watch" in watch_row.reason_codes
    assert pass_row.total_friction_rate == d("0.020000")
    assert pass_row.reason_codes == (
        "fee_drag_confidence_haircut_component",
        "fee_drag_fee_component",
        "fee_drag_settlement_friction_component",
        "fee_drag_slippage_component",
        "fee_drag_spread_component",
        "fee_drag_status_pass",
        "input_manual_research_only",
    )

    counts_by_code = {item.reason_code: item.count for item in built.reason_code_counts}
    assert counts_by_code["fee_drag_fee_component"] == d("3.000000")
    assert counts_by_code["fee_drag_status_block"] == d("1.000000")
    assert built.reason_code_counts == tuple(
        sorted(built.reason_code_counts, key=lambda item: (-item.count, item.reason_code)),
    )
    assert built.reason_codes == tuple(sorted(built.reason_codes))


def test_payload_is_deterministic_decimal_string_serialized_and_digest_validated() -> None:
    first = research_market_fee_drag_sensitivity_report_payload(
        report(
            input_row("fee-drag-case-z", upstream_reason_codes=("zeta", "alpha")),
            input_row("fee-drag-case-a", upstream_reason_codes=("alpha", "zeta")),
        ),
    )
    second = research_market_fee_drag_sensitivity_report_payload(
        report(
            input_row("fee-drag-case-a", upstream_reason_codes=("zeta", "alpha")),
            input_row("fee-drag-case-z", upstream_reason_codes=("alpha", "zeta")),
        ),
    )

    assert first == second
    assert json.dumps(first, sort_keys=True)
    assert not any(isinstance(value, float) for value in walk_values(first))
    assert not any(isinstance(value, Decimal) for value in walk_values(first))
    assert first["row_count"] == "2.000000"
    assert first["rows"][0]["fee_rate"] == "0.005000"
    assert first["rows"][0]["minimum_edge_needed_rate"] == "0.040000"
    assert first["paper_only"] is True
    assert first["report_only"] is True
    assert first["readonly"] is True

    digest_payload = dict(first)
    provided_digest = digest_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert provided_digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert validate_research_market_fee_drag_sensitivity_report_payload(first) == first

    tampered = dict(first)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_market_fee_drag_sensitivity_report_payload(tampered)


def test_public_payload_excludes_raw_candidates_market_text_urls_and_live_surfaces() -> None:
    raw_reference = (
        "candidate-777 market_id=123 market_slug=will-this-resolve "
        "question=https://example.test/source?token=secret dsn=postgres "
        "table_name=orders wallet=abc trade=manual live_surface "
        "sizing=recommendation"
    )
    built = report((input_row(raw_reference),)[0])
    payload = research_market_fee_drag_sensitivity_report_payload(built)
    rendered = repr(payload).lower()

    for forbidden in (
        "candidate-777",
        "market_id",
        "market_slug",
        "will-this-resolve",
        "question=",
        "https://example.test",
        "token=secret",
        "dsn=postgres",
        "table_name",
        "orders",
        "wallet=abc",
        "trade=manual",
        "live_surface",
        "sizing=",
        "recommendation",
        "raw_candidate_id",
    ):
        assert forbidden not in rendered

    unsafe_report = replace(built)
    object.__setattr__(unsafe_report, "reason_codes", ("fee_drag_status_pass", "wallet"))
    object.__setattr__(unsafe_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_market_fee_drag_sensitivity_report_payload(unsafe_report)

    for unsafe_reason_code in ("sizing_surface", "recommendation_surface"):
        with pytest.raises(ValueError, match="unsafe public payload"):
            input_row(upstream_reason_codes=(unsafe_reason_code,))


def test_validation_rejects_non_decimal_values_bad_datetimes_flags_and_inconsistent_rows() -> None:
    with pytest.raises(ValueError, match="fee_rate"):
        input_row(fee_rate=0.01)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="spread_rate"):
        input_row(spread_rate=_DecimalSubclass("0.005000"))

    with pytest.raises(ValueError, match="base_manual_edge_rate"):
        config(base_manual_edge_rate=d("-0.010000"))

    with pytest.raises(ValueError, match="block_minimum_edge_needed_rate"):
        config(block_minimum_edge_needed_rate=d("0.050000"))

    with pytest.raises(ValueError, match="UTC-aware"):
        report(input_row(), generated_at=datetime(2026, 7, 8, 16, 0))

    with pytest.raises(ValueError, match="datetime"):
        report(input_row(), generated_at=_DatetimeSubclass(2026, 7, 8, tzinfo=UTC))

    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        report(input_row(readonly=False))

    built = report(input_row())
    unsafe_report = replace(built)
    object.__setattr__(unsafe_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        research_market_fee_drag_sensitivity_report_payload(unsafe_report)

    inconsistent_row = replace(
        built.rows[0],
        minimum_edge_needed_rate=d("0.999000"),
    )
    with pytest.raises(ValueError, match="minimum_edge_needed_rate"):
        ResearchMarketFeeDragSensitivityReport(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_RESEARCH_MARKET_FEE_DRAG_SENSITIVITY_CONFIG_VERSION,
            status="pass",
            input_count=d("1.000000"),
            row_count=d("1.000000"),
            pass_count=d("1.000000"),
            watch_count=d("0.000000"),
            block_count=d("0.000000"),
            base_manual_edge_rate=d("0.020000"),
            max_minimum_edge_needed_rate=d("0.999000"),
            average_minimum_edge_needed_rate=d("0.999000"),
            reason_codes=inconsistent_row.reason_codes,
            reason_code_counts=(),
            rows=(inconsistent_row,),
        )


def test_payload_validation_rejects_nested_hard_flag_tampering() -> None:
    payload = research_market_fee_drag_sensitivity_report_payload(report(input_row()))
    tampered = copy.deepcopy(payload)
    tampered["rows"][0]["paper_only"] = False
    digest_payload = dict(tampered)
    digest_payload.pop("derived_validation_digest")
    tampered["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            digest_payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()

    with pytest.raises(ValueError, match="paper_only"):
        validate_research_market_fee_drag_sensitivity_report_payload(tampered)


def test_public_objects_are_frozen_dataclasses_with_decimal_only_numeric_fields() -> None:
    built = report(input_row())

    for item in (config(), input_row(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]

    public_classes = (
        ResearchMarketFeeDragSensitivityConfig,
        ResearchMarketFeeDragSensitivityInput,
        ResearchMarketFeeDragSensitivityRow,
        ResearchMarketFeeDragSensitivityReasonCodeCount,
        ResearchMarketFeeDragSensitivityReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        assert all(
            field.type not in (int, float)
            for field in fields(klass)
            if field.name not in {"paper_only", "report_only", "readonly"}
        )


def test_empty_report_is_report_only_readonly_and_has_valid_digest() -> None:
    built = report()
    payload = research_market_fee_drag_sensitivity_report_payload(built)

    assert built.input_count == d("0.000000")
    assert built.row_count == d("0.000000")
    assert built.status == "block"
    assert built.reason_codes == ("fee_drag_sensitivity_report_empty",)
    assert built.reason_code_counts == ()
    assert built.rows == ()
    assert payload["generated_at"] == "2026-07-08T16:00:00+00:00"
    assert validate_research_market_fee_drag_sensitivity_report_payload(payload) == payload


def test_module_has_no_auth_io_or_market_action_surface() -> None:
    module_path = Path(__file__).resolve().parents[1] / MODULE_PATH
    tree = ast.parse(module_path.read_text())
    source = module_path.read_text().lower()

    for token in (
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "private_key",
        "api_key",
        "requests",
        "httpx",
        "urllib",
        "urlopen",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlite",
        "redis",
        "os.environ",
        "getenv",
        "open(",
        "read_text",
        "write_text",
        "path(",
        "connect(",
        "execute(",
        "sizing",
        "recommend",
    ):
        assert token not in source

    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
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
