from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_settlement_fee_uncertainty_ladder_report"
)
GENERATED_AT = datetime(2026, 7, 8, 15, 30, tzinfo=UTC)


def _api() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} must exist")
        raise


def _observation(raw_candidate_id: str, **overrides: Any) -> object:
    api = _api()
    values = {
        "raw_candidate_id": raw_candidate_id,
        "observed_at": GENERATED_AT,
        "fee_assumption": Decimal("0.002000"),
        "quoted_spread": Decimal("0.004000"),
        "slippage_buffer": Decimal("0.001000"),
        "settlement_friction": Decimal("0.001000"),
        "liquidity_depth": Decimal("0.900000"),
        "confidence_haircut": Decimal("0.002000"),
        "sensitive_context": (
            "candidate-id market-id market-slug market question "
            "https://example.invalid/source raw text postgres://host/db "
            "orders_table token abc wallet order trade live sizing"
        ),
    }
    values.update(overrides)
    return api.ResearchMarketSettlementFeeUncertaintyLadderObservation(**values)


def _report(observations: tuple[object, ...], *, config: object | None = None) -> object:
    api = _api()
    return api.build_research_market_settlement_fee_uncertainty_ladder_report(
        observations,
        generated_at=GENERATED_AT,
        config=config,
    )


def test_ladder_combines_fee_spread_slippage_settlement_depth_and_confidence() -> None:
    api = _api()
    config = api.ResearchMarketSettlementFeeUncertaintyLadderConfig(
        liquidity_depth_penalty_rate=Decimal("0.050000"),
        pass_threshold=Decimal("0.020000"),
        block_threshold=Decimal("0.070000"),
    )

    report = _report(
        (
            _observation("raw-pass"),
            _observation(
                "raw-watch",
                fee_assumption=Decimal("0.010000"),
                quoted_spread=Decimal("0.020000"),
                slippage_buffer=Decimal("0.005000"),
                settlement_friction=Decimal("0.004000"),
                liquidity_depth=Decimal("0.750000"),
                confidence_haircut=Decimal("0.006000"),
            ),
            _observation(
                "raw-block",
                fee_assumption=Decimal("0.025000"),
                quoted_spread=Decimal("0.060000"),
                slippage_buffer=Decimal("0.015000"),
                settlement_friction=Decimal("0.012000"),
                liquidity_depth=Decimal("0.200000"),
                confidence_haircut=Decimal("0.020000"),
            ),
        ),
        config=config,
    )

    assert type(report) is api.ResearchMarketSettlementFeeUncertaintyLadderReport
    assert report.sample_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.average_settlement_fee_uncertainty_score == Decimal("0.067500")
    assert report.max_settlement_fee_uncertainty_score == Decimal("0.142000")
    assert report.status == "block"
    assert set(row.status for row in report.rows) == {"pass", "watch", "block"}
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    first, second, third = report.rows
    assert first.ladder_rank == Decimal("1.000000")
    assert first.status == "block"
    assert first.fee_assumption_cost == Decimal("0.025000")
    assert first.spread_cost == Decimal("0.030000")
    assert first.slippage_buffer_cost == Decimal("0.015000")
    assert first.settlement_friction_cost == Decimal("0.012000")
    assert first.liquidity_depth_score == Decimal("0.200000")
    assert first.liquidity_depth_cost == Decimal("0.040000")
    assert first.confidence_haircut_cost == Decimal("0.020000")
    assert first.settlement_fee_uncertainty_score == Decimal("0.142000")
    assert first.reason_codes == (
        "fee_assumption_component",
        "spread_component",
        "slippage_buffer_component",
        "settlement_friction_component",
        "liquidity_depth_component",
        "confidence_haircut_component",
        "settlement_fee_uncertainty_block",
    )
    assert second.status == "watch"
    assert second.settlement_fee_uncertainty_score == Decimal("0.047500")
    assert third.status == "pass"
    assert third.settlement_fee_uncertainty_score == Decimal("0.013000")


def test_payload_is_deterministic_public_safe_decimal_only_and_digest_validated() -> None:
    api = _api()

    left = _report(
        (
            _observation("raw-pass"),
            _observation(
                "raw-block",
                fee_assumption=Decimal("0.025000"),
                quoted_spread=Decimal("0.060000"),
                slippage_buffer=Decimal("0.015000"),
                settlement_friction=Decimal("0.012000"),
                liquidity_depth=Decimal("0.200000"),
                confidence_haircut=Decimal("0.020000"),
            ),
            _observation(
                "raw-watch",
                fee_assumption=Decimal("0.010000"),
                quoted_spread=Decimal("0.020000"),
                slippage_buffer=Decimal("0.005000"),
                settlement_friction=Decimal("0.004000"),
                liquidity_depth=Decimal("0.750000"),
                confidence_haircut=Decimal("0.006000"),
            ),
        ),
    )
    right = _report(
        (
            _observation(
                "raw-watch",
                fee_assumption=Decimal("0.010000"),
                quoted_spread=Decimal("0.020000"),
                slippage_buffer=Decimal("0.005000"),
                settlement_friction=Decimal("0.004000"),
                liquidity_depth=Decimal("0.750000"),
                confidence_haircut=Decimal("0.006000"),
            ),
            _observation("raw-pass"),
            _observation(
                "raw-block",
                fee_assumption=Decimal("0.025000"),
                quoted_spread=Decimal("0.060000"),
                slippage_buffer=Decimal("0.015000"),
                settlement_friction=Decimal("0.012000"),
                liquidity_depth=Decimal("0.200000"),
                confidence_haircut=Decimal("0.020000"),
            ),
        ),
    )

    left_payload = api.research_market_settlement_fee_uncertainty_ladder_report_payload(left)
    right_payload = api.research_market_settlement_fee_uncertainty_ladder_report_payload(right)

    assert left_payload == right_payload
    assert api.research_market_settlement_fee_uncertainty_ladder_digest(left) == (
        left.public_report_digest
    )
    assert left.public_report_digest == right.public_report_digest
    assert len(left.public_report_digest) == 64
    assert left_payload["sample_count"] == "3.000000"
    assert left_payload["rows"][0]["settlement_fee_uncertainty_score"] == "0.142000"
    assert left_payload["public_report_digest"] == left.public_report_digest
    payload_without_digest = dict(left_payload)
    payload_without_digest.pop("public_report_digest")
    expected_digest = sha256(
        json.dumps(
            payload_without_digest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert left.public_report_digest == expected_digest
    json.dumps(left_payload, sort_keys=True)
    _assert_no_decimal_objects(left_payload)
    _assert_no_float(left_payload)
    _assert_no_non_decimal_public_numbers(left)

    encoded = json.dumps(left_payload, sort_keys=True)
    for sensitive_fragment in (
        "raw-pass",
        "raw-watch",
        "raw-block",
        "candidate-id",
        "market-id",
        "market-slug",
        "market question",
        "https://example.invalid/source",
        "raw text",
        "postgres://host/db",
        "orders_table",
        "token abc",
        "wallet order trade live sizing",
    ):
        assert sensitive_fragment not in encoded
    for unsafe_key_fragment in (
        "candidate_id",
        "market_id",
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
        "position",
        "sizing",
    ):
        assert unsafe_key_fragment not in encoded.lower()

    with pytest.raises(ValueError, match="public_report_digest"):
        replace(left, public_report_digest="0" * 64)


def test_dataclasses_are_frozen_final_and_require_hard_flags() -> None:
    api = _api()
    report = _report((_observation("raw-pass"),))

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(api.ResearchMarketSettlementFeeUncertaintyLadderConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        api.ResearchMarketSettlementFeeUncertaintyLadderConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _observation("raw-bad", report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_output_schema_has_no_trade_or_market_surfaces() -> None:
    api = _api()
    forbidden_fragments = (
        "candidate_id",
        "market_id",
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
        "position",
        "sizing",
    )

    for cls in (
        api.ResearchMarketSettlementFeeUncertaintyLadderConfig,
        api.ResearchMarketSettlementFeeUncertaintyLadderRow,
        api.ResearchMarketSettlementFeeUncertaintyLadderReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    payload = api.research_market_settlement_fee_uncertainty_ladder_report_payload(
        _report((_observation("raw-pass"),)),
    )
    _assert_no_unsafe_payload_strings(payload, forbidden_fragments)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)


def test_decimal_only_numeric_inputs_are_required() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        _observation("raw-bad", fee_assumption=0.01)

    with pytest.raises(ValueError, match="Decimal"):
        _observation("raw-bad", liquidity_depth=1)


def test_count_like_decimals_must_be_whole() -> None:
    api = _api()
    row = _report((_observation("raw-pass"),)).rows[0]

    with pytest.raises(ValueError, match="ladder_rank must be a whole Decimal"):
        replace(row, ladder_rank=Decimal("1.500000"))

    with pytest.raises(ValueError, match="count must be a whole Decimal"):
        api.ResearchMarketSettlementFeeUncertaintyLadderReasonCodeCount(
            reason_code="settlement_fee_uncertainty_pass",
            count=Decimal("1.500000"),
        )


def test_reason_codes_reject_duplicates_and_must_match_components() -> None:
    row = _report(
        (
            _observation(
                "raw-zero",
                fee_assumption=Decimal("0.000000"),
                quoted_spread=Decimal("0.000000"),
                slippage_buffer=Decimal("0.000000"),
                settlement_friction=Decimal("0.000000"),
                liquidity_depth=Decimal("1.000000"),
                confidence_haircut=Decimal("0.000000"),
            ),
        ),
    ).rows[0]

    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(row, reason_codes=row.reason_codes + row.reason_codes)

    with pytest.raises(ValueError, match="reason_codes must match cost components"):
        replace(
            row,
            reason_codes=(
                "fee_assumption_component",
                "settlement_fee_uncertainty_pass",
            ),
        )


def test_payload_revalidates_report_and_nested_public_dataclasses() -> None:
    api = _api()

    nested_flag_report = _report((_observation("raw-pass"),))
    object.__setattr__(nested_flag_report.rows[0], "readonly", False)
    object.__setattr__(
        nested_flag_report,
        "public_report_digest",
        api._expected_public_report_digest(nested_flag_report),
    )
    with pytest.raises(ValueError, match="readonly"):
        api.research_market_settlement_fee_uncertainty_ladder_report_payload(
            nested_flag_report,
        )

    nested_drift_report = _report((_observation("raw-pass"),))
    object.__setattr__(
        nested_drift_report.rows[0],
        "fee_assumption_cost",
        Decimal("0.500000"),
    )
    object.__setattr__(
        nested_drift_report,
        "public_report_digest",
        api._expected_public_report_digest(nested_drift_report),
    )
    with pytest.raises(ValueError, match="cost components"):
        api.research_market_settlement_fee_uncertainty_ladder_report_payload(
            nested_drift_report,
        )

    report_flag_drift = _report((_observation("raw-pass"),))
    object.__setattr__(report_flag_drift, "paper_only", False)
    object.__setattr__(
        report_flag_drift,
        "public_report_digest",
        api._expected_public_report_digest(report_flag_drift),
    )
    with pytest.raises(ValueError, match="paper_only"):
        api.research_market_settlement_fee_uncertainty_ladder_report_payload(
            report_flag_drift,
        )

    version_drift = _report((_observation("raw-pass"),))
    object.__setattr__(version_drift, "config_version", "unsupported-version")
    object.__setattr__(
        version_drift,
        "public_report_digest",
        api._expected_public_report_digest(version_drift),
    )
    with pytest.raises(ValueError, match="config_version"):
        api.research_market_settlement_fee_uncertainty_ladder_report_payload(
            version_drift,
        )


def test_duplicate_observation_identifiers_are_rejected() -> None:
    with pytest.raises(ValueError, match="raw_candidate_id values must be unique"):
        _report(
            (
                _observation("raw-duplicate"),
                _observation(
                    "raw-duplicate",
                    fee_assumption=Decimal("0.003000"),
                ),
            ),
        )


def test_payload_rejects_future_rows_and_noncanonical_ladder_order() -> None:
    api = _api()

    future_row_report = _report((_observation("raw-pass"),))
    object.__setattr__(
        future_row_report.rows[0],
        "observed_at",
        GENERATED_AT + timedelta(seconds=1),
    )
    object.__setattr__(
        future_row_report,
        "public_report_digest",
        api._expected_public_report_digest(future_row_report),
    )
    with pytest.raises(ValueError, match="observed_at"):
        api.research_market_settlement_fee_uncertainty_ladder_report_payload(
            future_row_report,
        )

    ladder_report = _report(
        (
            _observation("raw-pass"),
            _observation(
                "raw-block",
                fee_assumption=Decimal("0.025000"),
                quoted_spread=Decimal("0.060000"),
                slippage_buffer=Decimal("0.015000"),
                settlement_friction=Decimal("0.012000"),
                liquidity_depth=Decimal("0.200000"),
                confidence_haircut=Decimal("0.020000"),
            ),
        ),
    )
    block_row, pass_row = ladder_report.rows
    object.__setattr__(
        ladder_report,
        "rows",
        (
            replace(pass_row, ladder_rank=Decimal("1.000000")),
            replace(block_row, ladder_rank=Decimal("2.000000")),
        ),
    )
    object.__setattr__(
        ladder_report,
        "public_report_digest",
        api._expected_public_report_digest(ladder_report),
    )
    with pytest.raises(ValueError, match="canonical ladder order"):
        api.research_market_settlement_fee_uncertainty_ladder_report_payload(
            ladder_report,
        )


def test_public_payload_schema_is_exact_and_module_has_no_side_effect_surfaces() -> None:
    api = _api()
    payload = api.research_market_settlement_fee_uncertainty_ladder_report_payload(
        _report((_observation("raw-pass"),)),
    )

    assert set(payload) == {
        "generated_at",
        "config_version",
        "sample_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_settlement_fee_uncertainty_score",
        "max_settlement_fee_uncertainty_score",
        "status",
        "reason_code_counts",
        "reason_codes",
        "rows",
        "public_report_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(payload["reason_code_counts"][0]) == {
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(payload["rows"][0]) == {
        "ladder_rank",
        "observed_at",
        "fee_assumption_cost",
        "spread_cost",
        "slippage_buffer_cost",
        "settlement_friction_cost",
        "liquidity_depth_score",
        "liquidity_depth_cost",
        "confidence_haircut_cost",
        "settlement_fee_uncertainty_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    }

    source = Path(api.__file__).read_text(encoding="utf-8")
    forbidden_runtime_fragments = (
        "import requests",
        "import httpx",
        "import socket",
        "import sqlite3",
        "import sqlalchemy",
        "import psycopg",
        "import supabase",
        "from requests",
        "from httpx",
        "from socket",
        "from sqlite3",
        "from sqlalchemy",
        "from psycopg",
        "from supabase",
        "open(",
        ".write_text(",
        ".write_bytes(",
        "wallet_client",
        "place_order",
        "submit_order",
        "execute_trade",
        "recommendation:",
        "position_size",
    )
    assert not any(fragment in source for fragment in forbidden_runtime_fragments)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_float(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError("payload contains a float")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_float(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))


def _assert_no_unsafe_payload_strings(
    value: object,
    forbidden_fragments: tuple[str, ...],
) -> None:
    if type(value) is str:
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(fragment in lowered_key for fragment in forbidden_fragments)
            _assert_no_unsafe_payload_strings(item, forbidden_fragments)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_unsafe_payload_strings(item, forbidden_fragments)
