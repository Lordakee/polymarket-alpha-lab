import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal, localcontext

import pytest

from polymarket_alpha_lab.research_market_depth_fee_memory_confidence_ladder_report import (
    DEFAULT_RESEARCH_MARKET_DEPTH_FEE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION,
    ResearchMarketDepthFeeMemoryConfidenceLadderConfig,
    ResearchMarketDepthFeeMemoryConfidenceLadderObservation,
    ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount,
    ResearchMarketDepthFeeMemoryConfidenceLadderReport,
    ResearchMarketDepthFeeMemoryConfidenceLadderRow,
    build_research_market_depth_fee_memory_confidence_ladder_report,
    research_market_depth_fee_memory_confidence_ladder_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


def test_builds_deterministic_sanitized_payload_with_digest_validation() -> None:
    report = build_research_market_depth_fee_memory_confidence_ladder_report(
        (
            _observation(
                case_id="case-pass",
                observed_at=datetime(2026, 7, 9, 8, 30, tzinfo=timezone(timedelta(hours=-4))),
                depth_score=Decimal("0.950000"),
                fee_bps=Decimal("0.750000"),
                memory_confidence=Decimal("0.900000"),
            ),
            _observation(
                case_id="case-block",
                observed_at=datetime(2026, 7, 9, 12, 10, tzinfo=UTC),
                depth_score=Decimal("0.050000"),
                fee_bps=Decimal("12.000000"),
                memory_confidence=Decimal("0.100000"),
            ),
            _observation(
                case_id="case-watch",
                observed_at=datetime(2026, 7, 9, 12, 5, tzinfo=UTC),
                depth_score=Decimal("0.400000"),
                fee_bps=Decimal("4.000000"),
                memory_confidence=Decimal("0.550000"),
            ),
        ),
        config=ResearchMarketDepthFeeMemoryConfidenceLadderConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.report_status == "block"
    assert report.case_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert [row.case_id for row in report.rows] == [
        "case-block",
        "case-watch",
        "case-pass",
    ]
    assert {row.status for row in report.rows} <= {"pass", "watch", "block"}
    assert report.reason_codes == ("depth_fee_memory_ladder_block",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = research_market_depth_fee_memory_confidence_ladder_report_payload(report)
    assert payload == research_market_depth_fee_memory_confidence_ladder_report_payload(report)
    json.dumps(payload, sort_keys=True)
    _assert_no_float_or_decimal_payload(payload)
    _assert_no_raw_payload_keys(payload)
    assert "https://polymarket.example/raw?token=secret" not in json.dumps(
        payload,
        sort_keys=True,
    )
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"][0]["observed_at"] == "2026-07-09T12:10:00+00:00"
    assert payload["rows"][0]["fee_bps"] == "12.000000"
    assert payload["rows"][0]["status"] == "block"

    expected_digest = _digest_from_payload(payload)
    assert payload["derived_payload_digest"] == expected_digest


def test_empty_report_remains_report_only_and_uses_watch_status() -> None:
    report = build_research_market_depth_fee_memory_confidence_ladder_report(
        (),
        config=ResearchMarketDepthFeeMemoryConfidenceLadderConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.report_status == "watch"
    assert report.case_count == Decimal("0.000000")
    assert report.pass_count == Decimal("0.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.highest_cost_pressure == Decimal("0.000000")
    assert report.average_cost_pressure == Decimal("0.000000")
    assert report.average_fee_bps == Decimal("0.000000")
    assert report.average_memory_confidence == Decimal("0.000000")
    assert report.reason_codes == ("depth_fee_memory_ladder_no_inputs",)
    assert report.reason_code_counts == (
        ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount(
            reason_code="depth_fee_memory_ladder_no_inputs",
            count=Decimal("1.000000"),
        ),
    )
    assert report.rows == ()


def test_payload_rejects_tampered_digest_or_nested_public_values() -> None:
    report = build_research_market_depth_fee_memory_confidence_ladder_report(
        (_observation(),),
        config=ResearchMarketDepthFeeMemoryConfidenceLadderConfig(),
        generated_at=GENERATED_AT,
    )
    research_market_depth_fee_memory_confidence_ladder_report_payload(report)

    object.__setattr__(report.rows[0], "cost_pressure", Decimal("0.123456"))
    with pytest.raises(ValueError, match="derived_payload_digest"):
        research_market_depth_fee_memory_confidence_ladder_report_payload(report)
    object.__setattr__(report.rows[0], "cost_pressure", Decimal("0.000000"))

    object.__setattr__(report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        research_market_depth_fee_memory_confidence_ladder_report_payload(report)

    fresh_report = build_research_market_depth_fee_memory_confidence_ladder_report(
        (_observation(),),
        config=ResearchMarketDepthFeeMemoryConfidenceLadderConfig(),
        generated_at=GENERATED_AT,
    )
    tampered_payload = research_market_depth_fee_memory_confidence_ladder_report_payload(
        fresh_report,
    )
    tampered_payload["rows"][0]["case_id"] = "wallet-private"
    tampered_payload["derived_payload_digest"] = _digest_from_payload(tampered_payload)
    object.__setattr__(fresh_report.rows[0], "case_id", "wallet-private")
    object.__setattr__(
        fresh_report,
        "derived_payload_digest",
        tampered_payload["derived_payload_digest"],
    )
    with pytest.raises(ValueError, match="case_id"):
        research_market_depth_fee_memory_confidence_ladder_report_payload(fresh_report)

    numeric_report = build_research_market_depth_fee_memory_confidence_ladder_report(
        (_observation(),),
        config=ResearchMarketDepthFeeMemoryConfidenceLadderConfig(),
        generated_at=GENERATED_AT,
    )
    numeric_payload = research_market_depth_fee_memory_confidence_ladder_report_payload(
        numeric_report,
    )
    numeric_payload["case_count"] = 1
    numeric_payload["derived_payload_digest"] = _digest_from_payload(numeric_payload)
    object.__setattr__(numeric_report, "case_count", 1)
    object.__setattr__(
        numeric_report,
        "derived_payload_digest",
        numeric_payload["derived_payload_digest"],
    )
    with pytest.raises(ValueError, match="case_count"):
        research_market_depth_fee_memory_confidence_ladder_report_payload(numeric_report)


def test_public_constructors_reject_floats_raw_identifiers_and_invalid_statuses() -> None:
    with pytest.raises(ValueError, match="depth_score"):
        _observation(depth_score=0.5)
    with pytest.raises(ValueError, match="case_id"):
        _observation(case_id="https://polymarket.example/raw?token=secret")
    for unsafe_case_id in (
        "candidate-alpha",
        "market-123",
        "event-slug-alpha",
        "question-will-this-resolve",
        "source-url-alpha",
        "source-text-alpha",
        "dsn-alpha",
        "table-alpha",
        "token-alpha",
        "wallet-alpha",
        "order-alpha",
        "trade-alpha",
        "auth-alpha",
        "live-alpha",
        "sizing-alpha",
        "recommendation-alpha",
        "execution-alpha",
    ):
        with pytest.raises(ValueError, match="case_id"):
            _observation(case_id=unsafe_case_id)
    with pytest.raises(ValueError, match="status"):
        ResearchMarketDepthFeeMemoryConfidenceLadderRow(
            case_id="case-pass",
            observed_at=GENERATED_AT,
            depth_score=Decimal("1.000000"),
            fee_bps=Decimal("0.000000"),
            fee_pressure=Decimal("0.000000"),
            memory_confidence=Decimal("1.000000"),
            confidence_gap=Decimal("0.000000"),
            cost_pressure=Decimal("0.000000"),
            status="blocked",
            reason_codes=("depth_fee_memory_pass",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        ResearchMarketDepthFeeMemoryConfidenceLadderConfig(paper_only=False)
    with pytest.raises(ValueError, match="config_version"):
        ResearchMarketDepthFeeMemoryConfidenceLadderConfig(
            config_version=DEFAULT_RESEARCH_MARKET_DEPTH_FEE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION
            + "-v2",
        )


def test_public_dataclasses_are_frozen_and_decimal_only() -> None:
    report = build_research_market_depth_fee_memory_confidence_ladder_report(
        (_observation(),),
        config=ResearchMarketDepthFeeMemoryConfidenceLadderConfig(),
        generated_at=GENERATED_AT,
    )
    values = (
        ResearchMarketDepthFeeMemoryConfidenceLadderConfig(),
        _observation(),
        *report.rows,
        *report.reason_code_counts,
        report,
    )

    for value in values:
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False
        for field in fields(value):
            public_value = getattr(value, field.name)
            if isinstance(public_value, Decimal):
                assert type(public_value) is Decimal
            assert not isinstance(public_value, float)


def test_payload_digest_is_independent_of_external_decimal_context() -> None:
    config = ResearchMarketDepthFeeMemoryConfidenceLadderConfig(
        watch_fee_bps=Decimal("1.000000"),
        block_fee_bps=Decimal("3.000000"),
    )
    observations = (
        _observation(
            case_id="case-alpha",
            depth_score=Decimal("0.333333"),
            fee_bps=Decimal("1.000000"),
            memory_confidence=Decimal("0.666667"),
        ),
        _observation(
            case_id="case-beta",
            depth_score=Decimal("0.777777"),
            fee_bps=Decimal("2.000000"),
            memory_confidence=Decimal("0.444444"),
        ),
    )

    with localcontext() as context:
        context.prec = 4
        low_precision_payload = research_market_depth_fee_memory_confidence_ladder_report_payload(
            build_research_market_depth_fee_memory_confidence_ladder_report(
                observations,
                config=config,
                generated_at=GENERATED_AT,
            ),
        )
    with localcontext() as context:
        context.prec = 64
        high_precision_payload = research_market_depth_fee_memory_confidence_ladder_report_payload(
            build_research_market_depth_fee_memory_confidence_ladder_report(
                observations,
                config=config,
                generated_at=GENERATED_AT,
            ),
        )

    assert low_precision_payload == high_precision_payload
    assert low_precision_payload["derived_payload_digest"] == _digest_from_payload(
        low_precision_payload,
    )


def test_public_dataclasses_reject_subclassing_and_subclass_instantiation() -> None:
    public_types = (
        ResearchMarketDepthFeeMemoryConfidenceLadderConfig,
        ResearchMarketDepthFeeMemoryConfidenceLadderObservation,
        ResearchMarketDepthFeeMemoryConfidenceLadderRow,
        ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount,
        ResearchMarketDepthFeeMemoryConfidenceLadderReport,
    )
    for public_type in public_types:
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})


def test_module_scope_excludes_disallowed_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_market_depth_fee_memory_confidence_ladder_report",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    lowered_source = source.lower()
    forbidden_literals = (
        "db",
        "network",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "live trading",
        "sizing",
        "recommendation",
        "execution",
    )
    assert not any(token in lowered_source for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "sqlite",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "pathlib",
        "os",
        "subprocess",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _observation(
    **overrides: object,
) -> ResearchMarketDepthFeeMemoryConfidenceLadderObservation:
    values = {
        "case_id": "case-pass",
        "observed_at": GENERATED_AT,
        "depth_score": Decimal("1.000000"),
        "fee_bps": Decimal("0.000000"),
        "memory_confidence": Decimal("1.000000"),
    }
    values.update(overrides)
    return ResearchMarketDepthFeeMemoryConfidenceLadderObservation(**values)


def _digest_from_payload(payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_payload_digest")
    return hashlib.sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _assert_no_float_or_decimal_payload(value: object) -> None:
    if isinstance(value, (float, Decimal)):
        pytest.fail("public payload must not contain float or Decimal numerics")
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_float_or_decimal_payload(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_float_or_decimal_payload(child)


def _assert_no_raw_payload_keys(value: object) -> None:
    raw_keys = {
        "auth",
        "candidate",
        "candidate_id",
        "execution",
        "live",
        "market",
        "market_id",
        "market_slug",
        "order",
        "question",
        "recommendation",
        "sizing",
        "slug",
        "source",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "trade",
        "wallet",
    }
    if isinstance(value, dict):
        assert raw_keys.isdisjoint(value)
        for child in value.values():
            _assert_no_raw_payload_keys(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_raw_payload_keys(child)
