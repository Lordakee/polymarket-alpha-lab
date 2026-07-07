from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_liquidity_regime_shift_score"
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "candidate_decision_liquidity_regime_shift_score.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


class StringSubclass(str):
    pass


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing liquidity regime shift score module: {MODULE_NAME}")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_LIQUIDITY_REGIME_SHIFT_SCORE_CONFIG_VERSION
        ),
        "max_pass_shift_score": d("0.250000"),
        "max_watch_shift_score": d("0.600000"),
        "max_pass_depth_drop_score": d("0.200000"),
        "max_watch_depth_drop_score": d("0.500000"),
        "max_pass_spread_widening_score": d("0.200000"),
        "max_watch_spread_widening_score": d("0.600000"),
        "max_pass_volume_decay_score": d("0.250000"),
        "max_watch_volume_decay_score": d("0.600000"),
        "max_pass_stale_quote_minutes": d("2.000000"),
        "max_watch_stale_quote_minutes": d("20.000000"),
        "max_stale_quote_minutes_for_score": d("30.000000"),
        "depth_drop_weight": d("0.300000"),
        "spread_widening_weight": d("0.250000"),
        "volume_decay_weight": d("0.200000"),
        "stale_quote_weight": d("0.150000"),
        "regime_confidence_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.CandidateDecisionLiquidityRegimeShiftScoreConfig(**values)


def candidate(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "redacted_candidate_ref": "candidate_ref_alpha",
        "current_depth_score": d("0.920000"),
        "historical_depth_score": d("0.900000"),
        "spread_widening_score": d("0.050000"),
        "volume_decay_score": d("0.050000"),
        "stale_quote_minutes": d("1.000000"),
        "regime_confidence_score": d("0.900000"),
    }
    values.update(overrides)
    return module.CandidateDecisionLiquidityRegimeShiftInput(**values)


def report(*items: object, cfg: object | None = None, generated_at=GENERATED_AT) -> Any:
    module = api()
    return module.build_candidate_decision_liquidity_regime_shift_score(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_sha256(value: str) -> None:
    assert type(value) is str
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_float_values(item)
    if isinstance(value, list | tuple):
        for item in value:
            assert_no_float_values(item)


def assert_public_payload_has_no_forbidden_language(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "question",
        "source_ref",
        "source_url",
        "url",
        "dsn",
        "table_name",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "position",
        "sizing",
        "ready",
        "blocked",
        "matched",
        "supported",
    )
    for fragment in forbidden_fragments:
        assert fragment not in rendered


def test_stable_liquidity_regime_passes_with_report_only_payload() -> None:
    module = api()
    result = report(candidate())

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "candidate-decision-liquidity-regime-shift-score-v0"
    assert result.candidate_count == d("1")
    assert result.pass_count == d("1")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.max_shift_score == d("0.032000")
    assert result.max_depth_drop_score == ZERO
    assert result.max_stale_quote_minutes == d("1.000000")
    assert result.status == "pass"
    assert result.reason_codes == ("liquidity_regime_shift_pass",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_sha256(result.report_sha256)
    assert_sha256(result.derived_validation_digest)

    row = result.rows[0]
    assert row.redacted_candidate_ref == "candidate_ref_alpha"
    assert row.depth_drop_score == ZERO
    assert row.stale_quote_component_score == d("0.033333")
    assert row.confidence_adjusted_shift_component_score == d("0.045000")
    assert row.shift_score == d("0.032000")
    assert row.status == "pass"
    assert row.reason_codes == ("liquidity_regime_shift_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert_sha256(row.row_sha256)
    assert_sha256(row.derived_validation_digest)

    payload = module.candidate_decision_liquidity_regime_shift_score_payload(result)
    assert payload == result.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["block_count"] == "0.000000"
    assert payload["rows"][0]["shift_score"] == "0.032000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    assert_public_payload_has_no_forbidden_language(payload)


def test_severe_liquidity_shift_blocks_candidate_priority() -> None:
    result = report(
        candidate(
            redacted_candidate_ref="candidate_ref_severe",
            current_depth_score=d("0.200000"),
            historical_depth_score=d("0.900000"),
            spread_widening_score=d("0.850000"),
            volume_decay_score=d("0.800000"),
            stale_quote_minutes=d("45.000000"),
            regime_confidence_score=d("0.950000"),
        ),
    )

    assert result.status == "block"
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == d("1")
    assert result.reason_codes == (
        "depth_regime_shift_block",
        "spread_regime_shift_block",
        "volume_regime_shift_block",
        "stale_quote_block",
        "shift_score_block",
    )

    row = result.rows[0]
    assert row.depth_drop_score == d("0.700000")
    assert row.stale_quote_component_score == d("1.000000")
    assert row.confidence_adjusted_shift_component_score == d("0.950000")
    assert row.shift_score == d("0.827500")
    assert row.status == "block"
    assert row.reason_codes == result.reason_codes


def test_moderate_liquidity_shift_watches_candidate_priority() -> None:
    result = report(
        candidate(
            redacted_candidate_ref="candidate_ref_moderate",
            current_depth_score=d("0.600000"),
            historical_depth_score=d("0.900000"),
            spread_widening_score=d("0.350000"),
            volume_decay_score=d("0.300000"),
            stale_quote_minutes=d("8.000000"),
            regime_confidence_score=d("0.800000"),
        ),
    )

    assert result.status == "watch"
    assert result.pass_count == ZERO
    assert result.watch_count == d("1")
    assert result.block_count == ZERO
    assert result.reason_codes == (
        "depth_regime_shift_watch",
        "spread_regime_shift_watch",
        "volume_regime_shift_watch",
        "stale_quote_watch",
        "shift_score_watch",
    )
    assert result.rows[0].shift_score == d("0.305500")
    assert result.rows[0].status == "watch"


def test_exact_decimal_validation_rejects_int_float_subclasses_and_bad_config() -> None:
    module = api()

    with pytest.raises(ValueError, match="current_depth_score must be a Decimal"):
        candidate(current_depth_score=0.92)
    with pytest.raises(ValueError, match="stale_quote_minutes must be a Decimal"):
        candidate(stale_quote_minutes=1)
    with pytest.raises(ValueError, match="exact Decimal"):
        candidate(historical_depth_score=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="redacted_candidate_ref must be a str"):
        candidate(redacted_candidate_ref=StringSubclass("candidate_ref_subclass"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(candidate(), generated_at=DatetimeSubclass(2026, 7, 7, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(candidate(), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="depth_drop_weight must be a Decimal"):
        config(depth_drop_weight=1)
    with pytest.raises(ValueError, match="weights must sum to 1"):
        config(depth_drop_weight=d("0.350000"))
    with pytest.raises(ValueError, match="config"):
        module.build_candidate_decision_liquidity_regime_shift_score(
            [candidate()],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="CandidateDecisionLiquidityRegimeShiftInput"):
        module.build_candidate_decision_liquidity_regime_shift_score(
            [object()],
            config=config(),
            generated_at=GENERATED_AT,
        )


def test_leak_rejection_blocks_raw_references_and_public_payload_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        candidate(redacted_candidate_ref="candidate-secret-token-alpha")
    with pytest.raises(ValueError, match="unsafe public payload"):
        candidate(redacted_candidate_ref="candidate_ref_wallet")
    with pytest.raises(ValueError, match="reason_codes"):
        module.CandidateDecisionLiquidityRegimeShiftRow(
            **{
                **report(candidate()).rows[0].__dict__,
                "reason_codes": ("buy_signal",),
            },
        )

    payload = module.candidate_decision_liquidity_regime_shift_score_payload(
        report(candidate(redacted_candidate_ref="candidate_ref_public")),
    )
    unsafe_payloads = (
        {"candidate_id": "candidate-123"},
        {"market_id": "market-123"},
        {"market_slug": "raw-market-slug"},
        {"market_question": "Will this resolve?"},
        {"source_url": "https://example.test/source"},
        {"source_ref": "research-note"},
        {"dsn": "postgresql://example.test/db"},
        {"table_name": "candidate_scores"},
        {"review_note": "token"},
        {"review_note": "auth"},
        {"review_note": "wallet"},
        {"review_note": "order"},
        {"review_note": "trade"},
        {"review_note": "buy"},
        {"review_note": "sell"},
        {"review_note": "recommendation"},
        {"review_note": "position sizing"},
        {"status": "blocked"},
        {"status": "ready"},
        {"status": "matched"},
        {"status": "supported"},
    )
    for extra_payload in unsafe_payloads:
        with pytest.raises(ValueError, match="unsafe public payload"):
            module.validate_candidate_decision_liquidity_regime_shift_public_payload(
                {**payload, **extra_payload},
            )


def test_dataclasses_are_frozen_and_hard_flagged() -> None:
    module = api()
    cfg = config()
    item = candidate()
    result = report(item, cfg=cfg)
    row = result.rows[0]

    for klass in (
        module.CandidateDecisionLiquidityRegimeShiftScoreConfig,
        module.CandidateDecisionLiquidityRegimeShiftInput,
        module.CandidateDecisionLiquidityRegimeShiftRow,
        module.CandidateDecisionLiquidityRegimeShiftReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        item.current_depth_score = d("0.1")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]

    for instance in (cfg, item, row, result):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for field in fields(instance):
            value = getattr(instance, field.name)
            if field.name in {
                "paper_only",
                "report_only",
                "readonly",
                "payload",
                "report_sha256",
                "row_sha256",
                "derived_validation_digest",
            }:
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(cfg, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_deterministic_payload_sorting_and_digest_values() -> None:
    module = api()
    severe = candidate(
        redacted_candidate_ref="candidate_ref_severe",
        current_depth_score=d("0.200000"),
        historical_depth_score=d("0.900000"),
        spread_widening_score=d("0.850000"),
        volume_decay_score=d("0.800000"),
        stale_quote_minutes=d("45.000000"),
        regime_confidence_score=d("0.950000"),
    )
    stable = candidate(redacted_candidate_ref="candidate_ref_stable")
    moderate = candidate(
        redacted_candidate_ref="candidate_ref_moderate",
        current_depth_score=d("0.600000"),
        historical_depth_score=d("0.900000"),
        spread_widening_score=d("0.350000"),
        volume_decay_score=d("0.300000"),
        stale_quote_minutes=d("8.000000"),
        regime_confidence_score=d("0.800000"),
    )

    first = report(stable, severe, moderate)
    second = report(moderate, stable, severe)

    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert tuple(row.redacted_candidate_ref for row in first.rows) == (
        "candidate_ref_severe",
        "candidate_ref_moderate",
        "candidate_ref_stable",
    )
    assert first.payload == second.payload
    assert module.candidate_decision_liquidity_regime_shift_score_payload(first) == (
        first.payload
    )
    assert_no_float_values(first.payload)
    assert_public_payload_has_no_forbidden_language(first.payload)


def test_report_consistency_rejects_tampered_counts_order_and_digests() -> None:
    module = api()
    result = report(
        candidate(redacted_candidate_ref="candidate_ref_pass"),
        candidate(
            redacted_candidate_ref="candidate_ref_watch",
            current_depth_score=d("0.600000"),
            historical_depth_score=d("0.900000"),
            spread_widening_score=d("0.350000"),
            volume_decay_score=d("0.300000"),
            stale_quote_minutes=d("8.000000"),
            regime_confidence_score=d("0.800000"),
        ),
    )

    assert tuple(row.status for row in result.rows) == ("watch", "pass")

    with pytest.raises(ValueError, match="shift_score must match"):
        replace(result.rows[0], shift_score=d("0.123456"))
    with pytest.raises(ValueError, match="status must match"):
        replace(result.rows[0], status="pass")
    with pytest.raises(ValueError, match="row_sha256 must match"):
        replace(result.rows[0], row_sha256="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result.rows[0], derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(result, pass_count=d("2"))
    with pytest.raises(ValueError, match="status must match"):
        replace(result, status="pass")
    with pytest.raises(ValueError, match="rows must be deterministically sorted"):
        module.CandidateDecisionLiquidityRegimeShiftReport(
            **{
                **result.__dict__,
                "rows": tuple(reversed(result.rows)),
            },
        )
    with pytest.raises(ValueError, match="report_sha256 must match"):
        replace(result, report_sha256="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result, derived_validation_digest="0" * 64)


def test_source_has_no_io_network_persistence_float_literals_or_live_surfaces() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    banned_import_roots = {
        "asyncio",
        "csv",
        "http",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    assert not (set(imported_modules) & banned_import_roots)

    public_api_text = "\n".join(module.__all__).lower()
    for forbidden in (
        "ready",
        "blocked",
        "matched",
        "supported",
        "market_slug",
        "question",
        "url",
        "source_ref",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "position",
        "sizing",
    ):
        assert forbidden not in public_api_text
