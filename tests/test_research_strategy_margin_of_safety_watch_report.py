from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_strategy_margin_of_safety_watch_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_margin_of_safety_watch_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 55, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "research-strategy-margin-of-safety-watch-report-v1",
        "pass_adjusted_margin_floor": d("0.050000"),
        "watch_adjusted_margin_floor": d("0.020000"),
        "pass_cost_drag_ceiling": d("0.030000"),
        "watch_cost_drag_ceiling": d("0.080000"),
        "pass_confidence_haircut_ceiling": d("0.050000"),
        "watch_confidence_haircut_ceiling": d("0.150000"),
        "pass_liquidity_uncertainty_ceiling": d("0.100000"),
        "watch_liquidity_uncertainty_ceiling": d("0.250000"),
        "pass_evidence_strength_floor": d("0.700000"),
        "watch_evidence_strength_floor": d("0.450000"),
        "pass_resolution_ambiguity_ceiling": d("0.100000"),
        "watch_resolution_ambiguity_ceiling": d("0.250000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchStrategyMarginOfSafetyWatchConfig(**values)


def margin_input(
    *,
    candidate_id: str = "cand-private-alpha",
    market_id: str = "market-private-alpha",
    market_slug: str = "alpha-private-slug",
    market_question: str = "Will alpha private outcome happen?",
    source_url: str = "https://example.invalid/private-alpha",
    source_text: str = "private source text must not become public",
    observed_at: datetime = OBSERVED_AT,
    model_edge_probability: Decimal = d("0.180000"),
    cost_drag_probability: Decimal = d("0.020000"),
    confidence_haircut_probability: Decimal = d("0.020000"),
    liquidity_uncertainty_probability: Decimal = d("0.030000"),
    evidence_strength_score: Decimal = d("0.900000"),
    resolution_ambiguity_score: Decimal = d("0.020000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyMarginOfSafetyWatchInput(
        candidate_id=candidate_id,
        market_id=market_id,
        market_slug=market_slug,
        market_question=market_question,
        source_url=source_url,
        source_text=source_text,
        observed_at=observed_at,
        model_edge_probability=model_edge_probability,
        cost_drag_probability=cost_drag_probability,
        confidence_haircut_probability=confidence_haircut_probability,
        liquidity_uncertainty_probability=liquidity_uncertainty_probability,
        evidence_strength_score=evidence_strength_score,
        resolution_ambiguity_score=resolution_ambiguity_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*inputs: object, generated_at: datetime = GENERATED_AT, config: object | None = None):
    module = api()
    return module.build_research_strategy_margin_of_safety_watch_report(
        inputs,
        generated_at=generated_at,
        config=config or cfg(),
    )


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_public_number_payload(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_public_number_payload(item_value)


def assert_no_forbidden_public_surface(value: Any) -> None:
    forbidden_fragments = (
        "candidate",
        "market",
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
        "buy",
        "sell",
        "sizing",
        "recommend",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_fragments:
                assert fragment not in lowered, key
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        assert "://" not in lowered
        for fragment in forbidden_fragments:
            assert fragment not in lowered, value


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"rows", "reason_codes", "reason_code_counts"}:
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "score",
                "probability",
                "floor",
                "ceiling",
                "ratio",
            )
        ):
            assert type(getattr(value, field.name)) is Decimal, field.name


def test_empty_input_returns_block_report_only_decimal_digest() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == (
        "research-strategy-margin-of-safety-watch-report-v1"
    )
    assert empty_report.status == "block"
    assert empty_report.reason_codes == ("margin_of_safety_report_empty",)
    assert empty_report.input_count == d("0")
    assert empty_report.pass_count == d("0")
    assert empty_report.watch_count == d("0")
    assert empty_report.block_count == d("0")
    assert empty_report.mean_model_edge_probability == d("0.000000")
    assert empty_report.mean_total_uncertainty_probability == d("0.000000")
    assert empty_report.mean_adjusted_margin_of_safety_probability == d("0.000000")
    assert empty_report.min_evidence_strength_score == d("0.000000")
    assert empty_report.max_resolution_ambiguity_score == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_fields(empty_report)

    payload = module.research_strategy_margin_of_safety_watch_report_payload(empty_report)
    digest_value = module.research_strategy_margin_of_safety_watch_report_digest(
        empty_report,
    )
    json.dumps(payload, sort_keys=True)
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert payload["status"] == "block"
    assert payload["input_count"] == "0.000000"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64


def test_report_scores_margin_safety_drags_evidence_and_resolution_ambiguity() -> None:
    passed = margin_input(
        candidate_id="cand-pass",
        market_id="market-pass",
        market_slug="private-pass-slug",
        observed_at=GENERATED_AT - timedelta(minutes=6),
        model_edge_probability=d("0.180000"),
        cost_drag_probability=d("0.020000"),
        confidence_haircut_probability=d("0.020000"),
        liquidity_uncertainty_probability=d("0.030000"),
        evidence_strength_score=d("0.900000"),
        resolution_ambiguity_score=d("0.020000"),
    )
    watched = margin_input(
        candidate_id="cand-watch",
        market_id="market-watch",
        market_slug="private-watch-slug",
        observed_at=GENERATED_AT - timedelta(minutes=5),
        model_edge_probability=d("0.180000"),
        cost_drag_probability=d("0.040000"),
        confidence_haircut_probability=d("0.050000"),
        liquidity_uncertainty_probability=d("0.030000"),
        evidence_strength_score=d("0.600000"),
        resolution_ambiguity_score=d("0.030000"),
    )
    blocked = margin_input(
        candidate_id="cand-block",
        market_id="market-block",
        market_slug="private-block-slug",
        observed_at=GENERATED_AT - timedelta(minutes=4),
        model_edge_probability=d("0.120000"),
        cost_drag_probability=d("0.090000"),
        confidence_haircut_probability=d("0.160000"),
        liquidity_uncertainty_probability=d("0.300000"),
        evidence_strength_score=d("0.300000"),
        resolution_ambiguity_score=d("0.300000"),
    )

    built = report(passed, watched, blocked)

    assert built.status == "block"
    assert built.input_count == d("3")
    assert built.pass_count == d("1")
    assert built.watch_count == d("1")
    assert built.block_count == d("1")
    assert built.mean_model_edge_probability == d("0.160000")
    assert built.mean_total_uncertainty_probability == d("0.363333")
    assert built.mean_adjusted_margin_of_safety_probability == d("-0.203333")
    assert built.min_evidence_strength_score == d("0.300000")
    assert built.max_resolution_ambiguity_score == d("0.300000")
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")

    blocked_row, watched_row, passed_row = built.rows
    assert blocked_row.total_uncertainty_probability == d("0.850000")
    assert blocked_row.adjusted_margin_of_safety_probability == d("-0.730000")
    assert blocked_row.reason_codes == (
        "adjusted_margin_block",
        "cost_drag_block",
        "confidence_haircut_block",
        "liquidity_uncertainty_block",
        "evidence_strength_block",
        "resolution_ambiguity_block",
    )
    assert watched_row.total_uncertainty_probability == d("0.150000")
    assert watched_row.adjusted_margin_of_safety_probability == d("0.030000")
    assert watched_row.reason_codes == (
        "adjusted_margin_watch",
        "cost_drag_watch",
        "evidence_strength_watch",
    )
    assert passed_row.status == "pass"
    assert passed_row.reason_codes == ("margin_of_safety_pass",)


def test_payload_is_sanitized_deterministic_decimal_string_and_digest_checked() -> None:
    module = api()
    inputs = (
        margin_input(
            candidate_id="cand-private-beta",
            market_id="market-private-beta",
            market_slug="private-beta-slug",
            market_question="Will beta private outcome happen?",
            source_url="https://example.invalid/private-beta",
            source_text="private beta source text",
            model_edge_probability=d("0.180000"),
        ),
        margin_input(
            candidate_id="cand-private-gamma",
            market_id="market-private-gamma",
            market_slug="private-gamma-slug",
            market_question="Will gamma private outcome happen?",
            source_url="https://example.invalid/private-gamma",
            source_text="private gamma source text",
            model_edge_probability=d("0.170000"),
            evidence_strength_score=d("0.600000"),
        ),
    )
    first = report(*inputs)
    second = report(*reversed(inputs))

    payload = first.payload
    encoded = json.dumps(payload, sort_keys=True)
    assert "cand-private" not in encoded
    assert "market-private" not in encoded
    assert "private-beta-slug" not in encoded
    assert "Will beta" not in encoded
    assert "https://" not in encoded
    assert "source text" not in encoded
    assert payload["rows"][0]["row_number"] == "1.000000"
    assert payload["rows"][0]["model_edge_probability"] == "0.170000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_strategy_margin_of_safety_watch_report_digest(first) == (
        first.derived_validation_digest
    )
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert_decimal_public_fields(first)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_strategy_margin_of_safety_watch_public_payload(
            tampered,
        )


def test_public_payload_validation_rejects_non_schema_status_and_extra_fields() -> None:
    module = api()
    built = report(margin_input())

    invalid_status = dict(built.payload)
    invalid_status["status"] = "hold"
    invalid_status["derived_validation_digest"] = module._public_payload_digest(  # noqa: SLF001
        invalid_status,
    )
    with pytest.raises(ValueError, match="status"):
        module.validate_research_strategy_margin_of_safety_watch_public_payload(
            invalid_status,
        )

    extra_report_field = dict(built.payload)
    extra_report_field["diagnostic_summary"] = "pass"
    extra_report_field["derived_validation_digest"] = module._public_payload_digest(  # noqa: SLF001
        extra_report_field,
    )
    with pytest.raises(ValueError, match="unexpected public payload field"):
        module.validate_research_strategy_margin_of_safety_watch_public_payload(
            extra_report_field,
        )

    extra_row_field = dict(built.payload)
    extra_row_field["rows"] = [dict(extra_row_field["rows"][0])]
    extra_row_field["rows"][0]["diagnostic_summary"] = "pass"
    extra_row_field["rows"][0]["derived_validation_digest"] = (
        module._public_payload_digest(extra_row_field["rows"][0])  # noqa: SLF001
    )
    extra_row_field["derived_validation_digest"] = module._public_payload_digest(  # noqa: SLF001
        extra_row_field,
    )
    with pytest.raises(ValueError, match="unexpected public payload field"):
        module.validate_research_strategy_margin_of_safety_watch_public_payload(
            extra_row_field,
        )


def test_dataclasses_are_frozen_and_enforce_decimal_flags_and_public_safety() -> None:
    module = api()
    built = report(margin_input())

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchStrategyMarginOfSafetyWatchConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        margin_input(readonly=False)

    with pytest.raises(ValueError, match="Decimal"):
        margin_input(model_edge_probability=0.18)  # type: ignore[arg-type]

    unsafe = dict(built.payload)
    unsafe["live_order_surface"] = "blocked"
    unsafe["derived_validation_digest"] = module._public_payload_digest(unsafe)  # noqa: SLF001
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_margin_of_safety_watch_report_payload(unsafe)
