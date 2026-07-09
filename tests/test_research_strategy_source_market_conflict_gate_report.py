from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_strategy_source_market_conflict_gate_report as api
from polymarket_alpha_lab.research_strategy_source_market_conflict_gate_report import (
    DEFAULT_RESEARCH_STRATEGY_SOURCE_MARKET_CONFLICT_GATE_REPORT_CONFIG_VERSION,
    ResearchStrategySourceMarketConflictGateConfig,
    ResearchStrategySourceMarketConflictGateInputRow,
    ResearchStrategySourceMarketConflictGateReport,
    ResearchStrategySourceMarketConflictPublicPayloadItem,
    build_research_strategy_source_market_conflict_gate_report,
    research_strategy_source_market_conflict_gate_report_payload,
)


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _NaiveTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _input_row(
    review_label: str,
    *,
    source_probability: Decimal = d("0.720000"),
    market_implied_probability: Decimal = d("0.700000"),
    evidence_authority_score: Decimal = d("0.900000"),
    evidence_freshness_score: Decimal = d("0.900000"),
    market_move_score: Decimal = d("0.100000"),
    liquidity_quality_score: Decimal = d("0.900000"),
    cost_drag_score: Decimal = d("0.100000"),
    specialist_memory_confidence: Decimal = d("0.900000"),
    observed_at: datetime = NOW,
) -> ResearchStrategySourceMarketConflictGateInputRow:
    return ResearchStrategySourceMarketConflictGateInputRow(
        review_label=review_label,
        source_probability=source_probability,
        market_implied_probability=market_implied_probability,
        evidence_authority_score=evidence_authority_score,
        evidence_freshness_score=evidence_freshness_score,
        market_move_score=market_move_score,
        liquidity_quality_score=liquidity_quality_score,
        cost_drag_score=cost_drag_score,
        specialist_memory_confidence=specialist_memory_confidence,
        observed_at=observed_at,
    )


def _config(**overrides: object) -> ResearchStrategySourceMarketConflictGateConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_SOURCE_MARKET_CONFLICT_GATE_REPORT_CONFIG_VERSION
        ),
        "watch_conflict_score": d("0.350000"),
        "block_conflict_score": d("0.650000"),
        "watch_probability_gap": d("0.120000"),
        "block_probability_gap": d("0.250000"),
        "max_evidence_age_seconds": d("7200.000000"),
        "market_move_watch_threshold": d("0.250000"),
        "market_move_block_threshold": d("0.550000"),
        "liquidity_quality_floor": d("0.400000"),
        "cost_drag_watch_threshold": d("0.120000"),
        "cost_drag_block_threshold": d("0.250000"),
        "memory_confidence_floor": d("0.550000"),
    }
    values.update(overrides)
    return ResearchStrategySourceMarketConflictGateConfig(**values)


def _sample_rows() -> tuple[ResearchStrategySourceMarketConflictGateInputRow, ...]:
    return (
        _input_row(
            "conflict_block",
            source_probability=d("0.820000"),
            market_implied_probability=d("0.430000"),
            evidence_authority_score=d("0.950000"),
            evidence_freshness_score=d("0.900000"),
            market_move_score=d("0.700000"),
            liquidity_quality_score=d("0.850000"),
            cost_drag_score=d("0.300000"),
            specialist_memory_confidence=d("0.920000"),
        ),
        _input_row(
            "conflict_watch",
            source_probability=d("0.620000"),
            market_implied_probability=d("0.440000"),
            evidence_authority_score=d("0.850000"),
            evidence_freshness_score=d("0.750000"),
            market_move_score=d("0.300000"),
            liquidity_quality_score=d("0.700000"),
            cost_drag_score=d("0.150000"),
            specialist_memory_confidence=d("0.720000"),
        ),
        _input_row(
            "conflict_pass",
            source_probability=d("0.540000"),
            market_implied_probability=d("0.500000"),
            evidence_authority_score=d("0.800000"),
            evidence_freshness_score=d("0.900000"),
            market_move_score=d("0.100000"),
            liquidity_quality_score=d("0.900000"),
            cost_drag_score=d("0.040000"),
            specialist_memory_confidence=d("0.850000"),
        ),
    )


def _build_report(
    rows: tuple[ResearchStrategySourceMarketConflictGateInputRow, ...],
    *,
    public_payload: tuple[ResearchStrategySourceMarketConflictPublicPayloadItem, ...] = (),
) -> ResearchStrategySourceMarketConflictGateReport:
    return build_research_strategy_source_market_conflict_gate_report(
        rows,
        generated_at=NOW,
        config=_config(),
        public_payload=public_payload,
    )


def test_conflict_gate_blocks_watches_passes_and_sorts_deterministically() -> None:
    report = _build_report(tuple(reversed(_sample_rows())))

    assert report == ResearchStrategySourceMarketConflictGateReport(
        generated_at=NOW,
        config_version=(
            DEFAULT_RESEARCH_STRATEGY_SOURCE_MARKET_CONFLICT_GATE_REPORT_CONFIG_VERSION
        ),
        gate_status="block",
        input_count=d("3.000000"),
        pass_count=d("1.000000"),
        watch_count=d("1.000000"),
        block_count=d("1.000000"),
        average_probability_gap=d("0.203333"),
        max_probability_gap=d("0.390000"),
        average_conflict_score=d("0.343767"),
        max_conflict_score=d("0.658100"),
        average_cost_drag_score=d("0.163333"),
        max_cost_drag_score=d("0.300000"),
        rows=report.rows,
        reason_codes=(
            "probability_gap_watch",
            "probability_gap_block",
            "conflict_score_block",
            "market_move_watch",
            "market_move_block",
            "cost_drag_watch",
            "cost_drag_block",
            "source_market_conflict_pass",
        ),
        public_payload=(),
        derived_validation_digest=report.derived_validation_digest,
    )
    assert tuple(row.review_label for row in report.rows) == (
        "conflict_block",
        "conflict_watch",
        "conflict_pass",
    )

    block_row = report.rows[0]
    assert block_row.gate_status == "block"
    assert block_row.probability_gap == d("0.390000")
    assert block_row.conflict_score == d("0.658100")
    assert block_row.manual_review_required is True
    assert block_row.reason_codes == (
        "probability_gap_block",
        "conflict_score_block",
        "market_move_block",
        "cost_drag_block",
    )

    watch_row = report.rows[1]
    assert watch_row.gate_status == "watch"
    assert watch_row.probability_gap == d("0.180000")
    assert watch_row.conflict_score == d("0.283200")
    assert watch_row.manual_review_required is True
    assert watch_row.reason_codes == (
        "probability_gap_watch",
        "market_move_watch",
        "cost_drag_watch",
    )

    pass_row = report.rows[2]
    assert pass_row.gate_status == "pass"
    assert pass_row.probability_gap == d("0.040000")
    assert pass_row.conflict_score == d("0.090000")
    assert pass_row.manual_review_required is False
    assert pass_row.reason_codes == ("source_market_conflict_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_json_ready_tamper_evident_and_excludes_private_surfaces() -> None:
    public_payload = (
        ResearchStrategySourceMarketConflictPublicPayloadItem(
            "review_scope",
            "manual conflict review queue",
        ),
    )
    report = _build_report(_sample_rows(), public_payload=public_payload)
    reversed_report = _build_report(tuple(reversed(_sample_rows())), public_payload=public_payload)

    payload = research_strategy_source_market_conflict_gate_report_payload(report)
    reversed_payload = research_strategy_source_market_conflict_gate_report_payload(
        reversed_report,
    )
    encoded_payload = json.dumps(payload, sort_keys=True)

    assert payload == reversed_payload
    assert payload == report.payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["input_count"] == "3.000000"
    assert payload["average_probability_gap"] == "0.203333"
    assert payload["max_conflict_score"] == "0.658100"
    assert payload["rows"][0]["review_label"] == "conflict_block"
    assert payload["rows"][0]["manual_review_required"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert set(report.derived_validation_digest) <= set("0123456789abcdef")
    assert "candidate" not in encoded_payload.lower()
    assert "market_slug" not in encoded_payload.lower()
    assert "question" not in encoded_payload.lower()
    assert "token" not in encoded_payload.lower()
    assert "wallet" not in encoded_payload.lower()
    assert "order" not in encoded_payload.lower()
    assert "trade" not in encoded_payload.lower()
    assert "recommend" not in encoded_payload.lower()
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchStrategySourceMarketConflictPublicPayloadItem(
                    "review_scope",
                    "changed queue",
                ),
            ),
        )

    with pytest.raises(ValueError, match="readonly"):
        research_strategy_source_market_conflict_gate_report_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_source_market_conflict_gate_report_payload(
            {**payload, "market_id": "abc"},
        )

    with pytest.raises(ValueError, match="numeric"):
        research_strategy_source_market_conflict_gate_report_payload(
            {**payload, "input_count": 3},
        )


def test_dataclasses_are_frozen_reject_subclassing_and_use_decimal_metrics() -> None:
    report = _build_report(_sample_rows())

    with pytest.raises(FrozenInstanceError):
        report.rows[0].gate_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchStrategySourceMarketConflictGateConfig):
            pass

    for value in _walk_public_values(report):
        if isinstance(value, Decimal):
            assert type(value) is Decimal
        if type(value) is int or isinstance(value, float):
            raise AssertionError(f"public numeric value is not Decimal: {value!r}")


def test_rejects_unsafe_fields_bad_decimals_times_duplicates_and_flags() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchStrategySourceMarketConflictGateConfig(paper_only=False)
    with pytest.raises(ValueError, match="block_conflict_score"):
        ResearchStrategySourceMarketConflictGateConfig(
            watch_conflict_score=d("0.650000"),
            block_conflict_score=d("0.650000"),
        )
    with pytest.raises(ValueError, match="max_evidence_age_seconds"):
        ResearchStrategySourceMarketConflictGateConfig(max_evidence_age_seconds=7200)
    with pytest.raises(ValueError, match="source_probability"):
        _input_row("bad_probability", source_probability=1)
    with pytest.raises(ValueError, match="market_move_score"):
        _input_row("bad_subclass", market_move_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="review_label"):
        _input_row(_join_parts("candidate", "_", "id"))
    with pytest.raises(ValueError, match="review_label"):
        _input_row(_join_parts("mar", "ket", "_", "slug"))
    with pytest.raises(ValueError, match="review_label"):
        _input_row(_join_parts("que", "stion"))
    with pytest.raises(ValueError, match="timezone-aware"):
        _input_row("naive_time", observed_at=datetime(2026, 7, 8))
    with pytest.raises(ValueError, match="timezone-aware"):
        _input_row(
            "naive_like_tzinfo",
            observed_at=datetime(2026, 7, 8, tzinfo=_NaiveTz()),
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(_input_row("not_readonly"), readonly=False)
    with pytest.raises(ValueError, match="future"):
        build_research_strategy_source_market_conflict_gate_report(
            (_input_row("future_input", observed_at=NOW + timedelta(seconds=1)),),
            generated_at=NOW,
            config=_config(),
        )
    with pytest.raises(ValueError, match="duplicate"):
        build_research_strategy_source_market_conflict_gate_report(
            (_input_row("duplicate"), _input_row("duplicate")),
            generated_at=NOW,
            config=_config(),
        )


def test_public_payload_rejects_raw_identifiers_urls_dsn_tables_and_live_surfaces() -> None:
    unsafe_values = (
        ("candidate_id", "public summary"),
        ("candidate-id", "public summary"),
        (_join_parts("mar", "ket", "_", "id"), "public summary"),
        (_join_parts("mar", "ket", "-", "id"), "public summary"),
        (_join_parts("source", "-", "url"), "public summary"),
        ("safe_key", "https://example.test/path"),
        ("safe_key", "postgres://user:pass@localhost/db"),
        ("safe_key", _join_parts("source", " ", "text", " excerpt")),
        ("safe_key", _join_parts("data", "base", " ", "url", " alias")),
        ("safe_key", "table_name=private_rows"),
        ("safe_key", _join_parts("table", " ", "name", " alias")),
        ("safe_key", _join_parts("api", "-", "key", " alias")),
        ("safe_key", _join_parts("auth", "-", "header")),
        ("safe_key", _join_parts("auth", "_", "key")),
        ("safe_key", _join_parts("author", "ization", " header")),
        ("safe_key", _join_parts("private", "-", "key", " alias")),
        ("safe_key", _join_parts("re", "commendation score")),
        ("safe_key", _join_parts("execut", "ion surface")),
        ("safe_key", "token=secret"),
        ("safe_key", "wallet 0xabc"),
        ("safe_key", "order submission"),
        ("safe_key", "live trade surface"),
    )

    for key, value in unsafe_values:
        with pytest.raises(ValueError):
            ResearchStrategySourceMarketConflictPublicPayloadItem(key, value)


def test_module_is_pure_report_only_and_does_not_import_io_or_live_surfaces() -> None:
    source = inspect.getsource(api)
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.partition(".")[0])

    assert not {
        "asyncio",
        "os",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    } & imports
    lowered = source.lower()
    for forbidden in (
        "sizing",
        "position_size",
        "execute_trade",
        "place_order",
        "wallet",
        "private_key",
        "database_url",
        "dsn",
    ):
        assert forbidden not in lowered


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError(f"payload contains Decimal object: {value!r}")
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"payload contains non-string numeric value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
    elif isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)


def _walk_public_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            values.extend(_walk_public_values(getattr(value, field.name)))
    elif isinstance(value, tuple):
        for item in value:
            values.extend(_walk_public_values(item))
    return tuple(values)
