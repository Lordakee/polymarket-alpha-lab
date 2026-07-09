from __future__ import annotations

import ast
import hashlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NaiveTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab."
        "research_market_probability_liquidity_decay_floor_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def case(**overrides: object) -> Any:
    module = api()
    values = {
        "case_digest": digest("case-pass"),
        "research_probability": d("0.650000"),
        "market_probability": d("0.550000"),
        "depth_score": d("0.900000"),
        "liquidity_score": d("0.850000"),
        "freshness_score": d("0.950000"),
        "fee_probability_drag": d("0.010000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchMarketProbabilityLiquidityDecayFloorInput(**values)


def report(rows: list[object] | tuple[object, ...]) -> Any:
    module = api()
    return module.build_research_market_probability_liquidity_decay_floor_report(
        rows,
        generated_at=GENERATED_AT,
    )


def test_decay_floor_scores_sorts_and_uses_only_pass_watch_block_statuses() -> None:
    module = api()
    passed = case()
    watched = case(
        case_digest=digest("case-watch"),
        research_probability=d("0.590000"),
        market_probability=d("0.550000"),
        depth_score=d("0.700000"),
        liquidity_score=d("0.700000"),
        freshness_score=d("0.650000"),
        fee_probability_drag=d("0.015000"),
    )
    blocked = case(
        case_digest=digest("case-block"),
        research_probability=d("0.570000"),
        market_probability=d("0.560000"),
        depth_score=d("0.300000"),
        liquidity_score=d("0.350000"),
        freshness_score=d("0.450000"),
        fee_probability_drag=d("0.020000"),
    )

    decay_report = report([passed, watched, blocked])
    repeated_report = report([blocked, passed, watched])

    assert type(decay_report) is module.ResearchMarketProbabilityLiquidityDecayFloorReport
    assert is_dataclass(decay_report)
    assert decay_report.generated_at == GENERATED_AT
    assert decay_report.config_version == (
        module.DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_DECAY_FLOOR_CONFIG_VERSION
    )
    assert decay_report.report_status == "block"
    assert decay_report.case_count == d("3.000000")
    assert decay_report.pass_count == d("1.000000")
    assert decay_report.watch_count == d("1.000000")
    assert decay_report.block_count == d("1.000000")
    assert decay_report.average_gross_probability_edge == d("0.050000")
    assert decay_report.average_floor_probability_edge == d("0.025333")
    assert decay_report.min_floor_probability_edge == d("-0.016333")
    assert decay_report.average_liquidity_decay_score == d("0.350000")
    assert decay_report.max_liquidity_decay_score == d("0.633333")
    assert [row.case_digest for row in decay_report.rows] == [
        digest("case-block"),
        digest("case-watch"),
        digest("case-pass"),
    ]

    blocked_row, watched_row, passed_row = decay_report.rows
    assert blocked_row.status == "block"
    assert blocked_row.gross_probability_edge == d("0.010000")
    assert blocked_row.liquidity_decay_score == d("0.633333")
    assert blocked_row.floor_probability_edge == d("-0.016333")
    assert blocked_row.reason_codes == (
        "liquidity_decay_floor_block",
        "floor_edge_block",
        "liquidity_decay_block",
        "fee_drag_watch",
    )

    assert watched_row.status == "watch"
    assert watched_row.gross_probability_edge == d("0.040000")
    assert watched_row.liquidity_decay_score == d("0.316667")
    assert watched_row.floor_probability_edge == d("0.012333")
    assert watched_row.reason_codes == (
        "liquidity_decay_floor_watch",
        "floor_edge_watch",
        "fee_drag_watch",
    )

    assert passed_row.status == "pass"
    assert passed_row.gross_probability_edge == d("0.100000")
    assert passed_row.liquidity_decay_score == d("0.100000")
    assert passed_row.floor_probability_edge == d("0.080000")
    assert passed_row.reason_codes == ("liquidity_decay_floor_pass",)

    assert decay_report.reason_code_counts[0].reason_code == "liquidity_decay_floor_block"
    assert (
        decay_report.derived_validation_digest
        == repeated_report.derived_validation_digest
    )
    assert len(decay_report.derived_validation_digest) == 64
    assert set(decay_report.derived_validation_digest) <= set("0123456789abcdef")
    assert decay_report.paper_only is True
    assert decay_report.report_only is True
    assert decay_report.readonly is True
    assert set(module.STATUSES) == {"pass", "watch", "block"}


def test_empty_input_is_report_only_and_public_payload_is_tamper_evident() -> None:
    module = api()
    empty_report = report([])

    assert empty_report.report_status == "pass"
    assert empty_report.case_count == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.reason_code_counts == ()
    assert empty_report.average_gross_probability_edge == d("0.000000")
    assert empty_report.average_floor_probability_edge == d("0.000000")
    assert empty_report.min_floor_probability_edge == d("0.000000")
    assert empty_report.average_liquidity_decay_score == d("0.000000")
    assert empty_report.max_liquidity_decay_score == d("0.000000")

    payload = module.research_market_probability_liquidity_decay_floor_report_payload(
        empty_report,
    )
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["report_status"] == "pass"
    assert payload["case_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == empty_report.derived_validation_digest
    assert not _contains_float(payload)
    _assert_public_payload_safe(payload)

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["report_status"] = "block"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]

    tampered = dict(payload)
    tampered["report_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_probability_liquidity_decay_floor_report_payload(
            tampered,
        )


def test_custom_config_drives_floor_and_decay_reason_validation() -> None:
    module = api()
    custom_config = module.ResearchMarketProbabilityLiquidityDecayFloorConfig(
        watch_floor_probability_edge=d("0.005000"),
        block_floor_probability_edge=d("-0.010000"),
        watch_liquidity_decay_score=d("0.500000"),
        block_liquidity_decay_score=d("0.750000"),
        watch_fee_probability_drag=d("0.020000"),
    )

    custom_report = (
        module.build_research_market_probability_liquidity_decay_floor_report(
            [
                case(
                    case_digest=digest("custom-config-pass"),
                    research_probability=d("0.590000"),
                    market_probability=d("0.550000"),
                    depth_score=d("0.700000"),
                    liquidity_score=d("0.700000"),
                    freshness_score=d("0.650000"),
                    fee_probability_drag=d("0.015000"),
                ),
            ],
            generated_at=GENERATED_AT,
            config=custom_config,
        )
    )

    assert custom_report.report_status == "pass"
    assert custom_report.rows[0].floor_probability_edge == d("0.012333")
    assert custom_report.rows[0].reason_codes == ("liquidity_decay_floor_pass",)
    assert custom_report.reason_code_counts[0].reason_code == "liquidity_decay_floor_pass"
    module.research_market_probability_liquidity_decay_floor_report_payload(
        custom_report,
    )


def test_payload_keeps_private_references_outside_public_surface() -> None:
    module = api()
    raw_private_reference = (
        "raw candidate reference private item identifier source reference "
        "secret credential execution venue"
    )
    decay_report = report(
        [
            case(
                case_digest=digest(raw_private_reference),
                research_probability=d("0.720000"),
                market_probability=d("0.610000"),
            ),
        ],
    )

    payload = module.research_market_probability_liquidity_decay_floor_report_payload(
        decay_report,
    )
    rendered_payload = json.dumps(payload, sort_keys=True)

    assert payload["rows"][0]["case_digest"] == digest(raw_private_reference)
    assert raw_private_reference not in rendered_payload
    for fragment in (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "https://example.invalid/a",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    ):
        assert fragment not in rendered_payload.lower()
    _assert_public_payload_safe(payload)


def test_validation_is_strict_frozen_decimal_only_and_flag_locked() -> None:
    module = api()
    base_case = case()
    decay_report = report([base_case])

    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_DECAY_FLOOR_CONFIG_VERSION",
        "ResearchMarketProbabilityLiquidityDecayFloorConfig",
        "ResearchMarketProbabilityLiquidityDecayFloorInput",
        "ResearchMarketProbabilityLiquidityDecayFloorRow",
        "ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount",
        "ResearchMarketProbabilityLiquidityDecayFloorReport",
        "build_research_market_probability_liquidity_decay_floor_report",
        "research_market_probability_liquidity_decay_floor_report_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    with pytest.raises(FrozenInstanceError):
        base_case.case_digest = digest("mutated")  # type: ignore[misc]
    with pytest.raises(ValueError, match="case_digest"):
        case(case_digest="not-a-digest")
    with pytest.raises(ValueError, match="research_probability"):
        case(research_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_probability"):
        case(market_probability=d("1.500000"))
    with pytest.raises(ValueError, match="depth_score"):
        case(depth_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="fee_probability_drag"):
        case(fee_probability_drag=d("-0.001000"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_probability_liquidity_decay_floor_report(
            [base_case],
            generated_at=_DateTimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_research_market_probability_liquidity_decay_floor_report(
            [base_case],
            generated_at=datetime(2026, 7, 9),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_research_market_probability_liquidity_decay_floor_report(
            [base_case],
            generated_at=datetime(2026, 7, 9, tzinfo=_NaiveTz()),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(base_case, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(decay_report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(decay_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="rows"):
        replace(decay_report, rows=())

    for value in _walk_public_values(decay_report):
        if isinstance(value, Decimal):
            assert type(value) is Decimal
        if type(value) is int or isinstance(value, float):
            raise AssertionError(f"public numeric value is not Decimal: {value!r}")


def test_rejects_duplicate_cases_bad_reason_codes_and_unsafe_public_payload() -> None:
    module = api()
    base = case()
    with pytest.raises(ValueError, match="unique"):
        report([base, base])

    blocked_row = report(
        [
            case(
                case_digest=digest("blocked"),
                research_probability=d("0.570000"),
                market_probability=d("0.560000"),
                depth_score=d("0.300000"),
                liquidity_score=d("0.350000"),
                freshness_score=d("0.450000"),
                fee_probability_drag=d("0.020000"),
            ),
        ],
    ).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            blocked_row,
            reason_codes=("liquidity_decay_floor_block", "floor_edge_block"),
        )

    payload = module.research_market_probability_liquidity_decay_floor_report_payload(
        report([base]),
    )
    with pytest.raises(ValueError, match="readonly"):
        module.research_market_probability_liquidity_decay_floor_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_probability_liquidity_decay_floor_report_payload(
            {**payload, "candidate_id": "abc"},
        )
    for unsafe_payload in (
        _payload_with_fresh_digest(
            module,
            payload,
            url="https://example.invalid/a",
        ),
        _payload_with_fresh_digest(module, payload, source="text leak"),
        _payload_with_fresh_digest(module, payload, database="analytics"),
        _payload_with_fresh_digest(module, payload, api_key="secret"),
        _payload_with_fresh_digest(module, payload, credential="private"),
        _payload_with_fresh_digest(module, payload, execution="surface"),
    ):
        with pytest.raises(ValueError, match="unsafe"):
            module.research_market_probability_liquidity_decay_floor_report_payload(
                unsafe_payload,
            )
    with pytest.raises(ValueError, match="numeric|Decimal"):
        module.research_market_probability_liquidity_decay_floor_report_payload(
            {**payload, "case_count": 1},
        )


def test_public_payload_rejects_resigned_schema_drift() -> None:
    module = api()
    payload = module.research_market_probability_liquidity_decay_floor_report_payload(
        report([case()]),
    )

    with pytest.raises(ValueError, match="schema"):
        module.research_market_probability_liquidity_decay_floor_report_payload(
            _payload_with_fresh_digest(
                module,
                payload,
                schema_extension="not-canonical",
            ),
        )

    row_drift = dict(payload)
    row_items = [dict(payload["rows"][0])]
    row_items[0]["schema_extension"] = "not-canonical"
    row_drift["rows"] = row_items
    with pytest.raises(ValueError, match="schema"):
        module.research_market_probability_liquidity_decay_floor_report_payload(
            _payload_with_fresh_digest(module, row_drift),
        )

    count_drift = dict(payload)
    count_items = [dict(payload["reason_code_counts"][0])]
    count_items[0]["schema_extension"] = "not-canonical"
    count_drift["reason_code_counts"] = count_items
    with pytest.raises(ValueError, match="schema"):
        module.research_market_probability_liquidity_decay_floor_report_payload(
            _payload_with_fresh_digest(module, count_drift),
        )

    with pytest.raises(ValueError, match="schema"):
        module.research_market_probability_liquidity_decay_floor_report_payload(
            _payload_with_fresh_digest(module, payload, report_status="clear"),
        )
    with pytest.raises(ValueError, match="Decimal"):
        module.research_market_probability_liquidity_decay_floor_report_payload(
            _payload_with_fresh_digest(module, payload, case_count="not-a-decimal"),
        )


def test_source_file_has_no_io_side_effect_or_live_private_surface() -> None:
    module = api()
    source = inspect.getsource(module)
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_probability_liquidity_decay_floor_report.py"
    )
    tree = ast.parse(source_path.read_text())
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.partition(".")[0])

    assert not {
        "asyncio",
        "http",
        "os",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    } & imports
    lowered = source.lower()
    for forbidden in (
        "auth",
        "database_url",
        "api_key",
        "credential",
        "dsn",
        "execute",
        "execute_trade",
        "execution",
        "live trading",
        "market_id",
        "market_slug",
        "order",
        "place_order",
        "position_size",
        "raw_candidate",
        "raw_market",
        "recommendation",
        "sizing",
        "source_text",
        "source_url",
        "secret",
        "table_name",
        "token",
        "trade",
        "wallet",
    ):
        assert forbidden not in lowered


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False


def _assert_public_payload_safe(value: object) -> None:
    banned_payload_fragments = (
        "api_key",
        "candidate_id",
        "credential",
        "database",
        "execute",
        "execution",
        "market_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "url",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommendation",
        "secret",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(fragment in lowered for fragment in banned_payload_fragments)
            _assert_public_payload_safe(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_public_payload_safe(item)
    if isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in banned_payload_fragments)


def _payload_with_fresh_digest(
    module: Any,
    payload: object,
    **overrides: object,
) -> dict[str, object]:
    refreshed = dict(payload)  # type: ignore[arg-type]
    refreshed.update(overrides)
    payload_without_digest = dict(refreshed)
    payload_without_digest.pop("derived_validation_digest", None)
    refreshed["derived_validation_digest"] = module._digest_for_value(
        payload_without_digest,
    )
    return refreshed


def _walk_public_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            values.extend(_walk_public_values(getattr(value, field.name)))
    elif isinstance(value, tuple):
        for item in value:
            values.extend(_walk_public_values(item))
    return tuple(values)
