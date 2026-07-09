from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_probability_gap_explainability_decay_report import (
    DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_STATUSES,
    ResearchStrategyProbabilityGapExplainabilityDecayConfig,
    ResearchStrategyProbabilityGapExplainabilityDecayInput,
    ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount,
    ResearchStrategyProbabilityGapExplainabilityDecayReport,
    ResearchStrategyProbabilityGapExplainabilityDecayRow,
    build_research_strategy_probability_gap_explainability_decay_report,
    research_strategy_probability_gap_explainability_decay_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_probability_gap_explainability_decay_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 17, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyProbabilityGapExplainabilityDecayConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_REPORT_CONFIG_VERSION
        ),
        "pass_min_explainability_score": d("0.750000"),
        "watch_min_explainability_score": d("0.550000"),
        "max_pass_evidence_age_seconds": d("21600.000000"),
        "max_watch_evidence_age_seconds": d("86400.000000"),
        "max_pass_cost_probability_drag": d("0.030000"),
        "max_watch_cost_probability_drag": d("0.080000"),
        "min_pass_liquidity_quality_score": d("0.750000"),
        "min_watch_liquidity_quality_score": d("0.500000"),
        "min_pass_adjusted_source_confidence_score": d("0.700000"),
        "min_watch_adjusted_source_confidence_score": d("0.500000"),
        "max_pass_resolution_ambiguity_score": d("0.200000"),
        "max_watch_resolution_ambiguity_score": d("0.450000"),
        "evidence_freshness_weight": d("0.250000"),
        "cost_stability_weight": d("0.200000"),
        "liquidity_quality_weight": d("0.200000"),
        "source_confidence_weight": d("0.200000"),
        "resolution_clarity_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchStrategyProbabilityGapExplainabilityDecayConfig(**values)


def gap_input(**overrides: object) -> ResearchStrategyProbabilityGapExplainabilityDecayInput:
    values = {
        "candidate_ref": "candidate-alpha-raw",
        "surface_ref": "market-alpha-slug?token=hidden&wallet=private",
        "observed_at": OBSERVED_AT,
        "model_probability": d("0.620000"),
        "public_probability": d("0.540000"),
        "evidence_age_seconds": d("7200.000000"),
        "cost_probability_drag": d("0.010000"),
        "liquidity_quality_score": d("0.900000"),
        "source_confidence_score": d("0.900000"),
        "source_confidence_decay_score": d("0.050000"),
        "resolution_ambiguity_score": d("0.100000"),
        "reason_codes": ("evidence_packet_ready",),
    }
    values.update(overrides)
    return ResearchStrategyProbabilityGapExplainabilityDecayInput(**values)


def report(
    *rows: ResearchStrategyProbabilityGapExplainabilityDecayInput,
    cfg: ResearchStrategyProbabilityGapExplainabilityDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyProbabilityGapExplainabilityDecayReport:
    return build_research_strategy_probability_gap_explainability_decay_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def refresh_payload_digest(payload: dict[str, object]) -> None:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    payload["derived_validation_digest"] = sha256(
        json.dumps(
            unsigned_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(
            (
                "_count",
                "_score",
                "_weight",
                "_ratio",
                "_probability",
                "_seconds",
                "_drag",
                "_gap",
            ),
        ):
            assert type(item) is Decimal


def test_scores_gap_explainability_decay_across_pass_watch_and_block() -> None:
    summary = report(
        gap_input(
            candidate_ref="candidate-pass-raw",
            surface_ref="market-pass-slug?token=hidden",
            model_probability=d("0.620000"),
            public_probability=d("0.540000"),
            evidence_age_seconds=d("7200.000000"),
            cost_probability_drag=d("0.010000"),
            liquidity_quality_score=d("0.900000"),
            source_confidence_score=d("0.900000"),
            source_confidence_decay_score=d("0.050000"),
            resolution_ambiguity_score=d("0.100000"),
            reason_codes=("evidence_packet_ready",),
        ),
        gap_input(
            candidate_ref="candidate-watch-raw",
            surface_ref="market-watch-slug",
            model_probability=d("0.610000"),
            public_probability=d("0.570000"),
            evidence_age_seconds=d("36000.000000"),
            cost_probability_drag=d("0.040000"),
            liquidity_quality_score=d("0.650000"),
            source_confidence_score=d("0.750000"),
            source_confidence_decay_score=d("0.200000"),
            resolution_ambiguity_score=d("0.350000"),
            reason_codes=("cost_update_observed", "liquidity_update_observed"),
        ),
        gap_input(
            candidate_ref="candidate-block-raw",
            surface_ref="market-block-slug",
            model_probability=d("0.400000"),
            public_probability=d("0.520000"),
            evidence_age_seconds=d("100000.000000"),
            cost_probability_drag=d("0.100000"),
            liquidity_quality_score=d("0.400000"),
            source_confidence_score=d("0.600000"),
            source_confidence_decay_score=d("0.400000"),
            resolution_ambiguity_score=d("0.600000"),
            reason_codes=("resolution_scope_review_requested",),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategyProbabilityGapExplainabilityDecayReport
    assert summary.generated_at == GENERATED_AT
    assert summary.config_version == (
        DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_REPORT_CONFIG_VERSION
    )
    assert summary.status == "block"
    assert summary.input_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_explainability_score == d("0.565167")
    assert summary.min_explainability_score == d("0.212000")
    assert summary.max_evidence_age_seconds == d("100000.000000")
    assert summary.max_cost_probability_drag == d("0.100000")
    assert summary.min_liquidity_quality_score == d("0.400000")
    assert summary.min_adjusted_source_confidence_score == d("0.360000")
    assert summary.max_resolution_ambiguity_score == d("0.600000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")

    blocked = summary.rows[0]
    assert type(blocked) is ResearchStrategyProbabilityGapExplainabilityDecayRow
    assert blocked.probability_gap == d("0.120000")
    assert blocked.gap_direction == "model_below_public"
    assert blocked.evidence_freshness_score == d("0.000000")
    assert blocked.cost_stability_score == d("0.000000")
    assert blocked.adjusted_source_confidence_score == d("0.360000")
    assert blocked.resolution_clarity_score == d("0.400000")
    assert blocked.explainability_score == d("0.212000")
    assert blocked.reason_codes == (
        "resolution_scope_review_requested",
        "evidence_age_block",
        "cost_drag_block",
        "liquidity_change_block",
        "source_confidence_decay_block",
        "resolution_ambiguity_block",
        "explainability_score_block",
    )

    watched = summary.rows[1]
    assert watched.probability_gap == d("0.040000")
    assert watched.gap_direction == "model_above_public"
    assert watched.evidence_freshness_score == d("0.583333")
    assert watched.cost_stability_score == d("0.500000")
    assert watched.adjusted_source_confidence_score == d("0.600000")
    assert watched.explainability_score == d("0.593333")
    assert watched.reason_codes == (
        "cost_update_observed",
        "liquidity_update_observed",
        "evidence_age_watch",
        "cost_drag_watch",
        "liquidity_change_watch",
        "source_confidence_decay_watch",
        "resolution_ambiguity_watch",
        "explainability_score_watch",
    )

    passed = summary.rows[2]
    assert passed.probability_gap == d("0.080000")
    assert passed.gap_direction == "model_above_public"
    assert passed.explainability_score == d("0.890167")
    assert passed.reason_codes == ("evidence_packet_ready", "gap_explainability_pass")

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["evidence_age_block"] == ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount(
        reason_code="evidence_age_block",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_empty_report_is_report_only_block() -> None:
    summary = report()

    assert summary.status == "block"
    assert summary.input_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_explainability_score == ZERO
    assert summary.min_explainability_score == ZERO
    assert summary.max_evidence_age_seconds == ZERO
    assert summary.max_cost_probability_drag == ZERO
    assert summary.min_liquidity_quality_score == ZERO
    assert summary.min_adjusted_source_confidence_score == ZERO
    assert summary.max_resolution_ambiguity_score == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == ("empty_input",)
    assert summary.reason_code_counts == (
        ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            input_ratio=d("1.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_is_deterministic_decimal_stringed_and_digest_guarded_without_raw_surfaces() -> None:
    first_payload = research_strategy_probability_gap_explainability_decay_report_payload(
        report(gap_input()),
    )
    second_payload = research_strategy_probability_gap_explainability_decay_report_payload(
        report(gap_input()),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert first_payload["input_count"] == "1.000000"
    assert first_payload["rows"][0]["gap_ref_digest"].startswith("sha256:")
    assert first_payload["rows"][0]["public_probability"] == "0.540000"
    assert first_payload["rows"][0]["explainability_score"] == "0.890167"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )

    payload_text = json.dumps(first_payload, sort_keys=True).casefold()
    for forbidden in (
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
        "candidate-alpha-raw",
        "market-alpha-slug",
        "hidden",
        "private",
    ):
        assert forbidden not in payload_text
        assert forbidden not in repr(asdict(report(gap_input()))).casefold()

    tampered = research_strategy_probability_gap_explainability_decay_report_payload(
        report(gap_input()),
    )
    tampered["rows"][0]["explainability_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_probability_gap_explainability_decay_report_payload(tampered)

    with pytest.raises(ValueError, match="unsafe public"):
        research_strategy_probability_gap_explainability_decay_report_payload(
            {
                "market_slug": "raw-market-alpha-slug",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )

    integer_payload = research_strategy_probability_gap_explainability_decay_report_payload(
        report(gap_input()),
    )
    integer_payload["input_count"] = 1
    stringified_integer_digest_payload = dict(integer_payload)
    stringified_integer_digest_payload["input_count"] = "1"
    refresh_payload_digest(stringified_integer_digest_payload)
    integer_payload["derived_validation_digest"] = stringified_integer_digest_payload[
        "derived_validation_digest"
    ]
    with pytest.raises(ValueError, match="Decimal-derived strings"):
        research_strategy_probability_gap_explainability_decay_report_payload(integer_payload)

    flagless_payload = research_strategy_probability_gap_explainability_decay_report_payload(
        report(gap_input()),
    )
    flagless_payload.pop("paper_only")
    flagless_payload.pop("report_only")
    flagless_payload.pop("readonly")
    refresh_payload_digest(flagless_payload)
    with pytest.raises(ValueError, match="paper_only"):
        research_strategy_probability_gap_explainability_decay_report_payload(flagless_payload)

    nested_flagless_payload = (
        research_strategy_probability_gap_explainability_decay_report_payload(
            report(gap_input()),
        )
    )
    nested_rows = [dict(row) for row in nested_flagless_payload["rows"]]  # type: ignore[index]
    nested_rows[0].pop("readonly")
    nested_flagless_payload["rows"] = nested_rows
    refresh_payload_digest(nested_flagless_payload)
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_probability_gap_explainability_decay_report_payload(
            nested_flagless_payload,
        )


def test_payload_rejects_execution_and_trading_surface_language() -> None:
    for unsafe_field in ("execution_surface", "trading_mode"):
        with pytest.raises(ValueError, match="unsafe public"):
            research_strategy_probability_gap_explainability_decay_report_payload(
                {
                    unsafe_field: "paper",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )


def test_validation_rejects_non_decimal_bad_times_flags_and_drift() -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="pass_min_explainability_score"):
        config(pass_min_explainability_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_explainability_score"):
        config(watch_min_explainability_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="pass_min_explainability_score"):
        config(pass_min_explainability_score=d("0.500000"))
    with pytest.raises(ValueError, match="max_pass_evidence_age_seconds"):
        config(max_pass_evidence_age_seconds=d("90000.000000"))
    with pytest.raises(ValueError, match="probability_gap weights"):
        config(evidence_freshness_weight=d("0.300000"))

    with pytest.raises(ValueError, match="candidate_ref"):
        gap_input(candidate_ref=_StringSubclass("candidate-alpha"))
    with pytest.raises(ValueError, match="surface_ref"):
        gap_input(surface_ref=" ")
    with pytest.raises(ValueError, match="model_probability"):
        gap_input(model_probability=0.62)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public_probability"):
        gap_input(public_probability=_DecimalSubclass("0.540000"))
    with pytest.raises(ValueError, match="evidence_age_seconds"):
        gap_input(evidence_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="source_confidence_decay_score"):
        gap_input(source_confidence_decay_score=d("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        gap_input(observed_at=_DateTimeSubclass(2026, 7, 8, 17, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(gap_input(observed_at=datetime(2026, 7, 8, 18, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="inputs"):
        build_research_strategy_probability_gap_explainability_decay_report(
            (object(),),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    summary = report(gap_input())
    with pytest.raises(ValueError, match="status"):
        replace(summary.rows[0], status="watch")
    with pytest.raises(ValueError, match="explainability_score"):
        replace(summary.rows[0], explainability_score=ZERO, validation_config=config())
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, derived_validation_digest="0" * 64)


def test_dataclasses_are_frozen_decimal_only_and_public_api_is_narrow() -> None:
    summary = report(gap_input())
    row = summary.rows[0]

    assert is_dataclass(ResearchStrategyProbabilityGapExplainabilityDecayConfig)
    assert is_dataclass(ResearchStrategyProbabilityGapExplainabilityDecayInput)
    assert is_dataclass(ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount)
    assert is_dataclass(ResearchStrategyProbabilityGapExplainabilityDecayRow)
    assert is_dataclass(ResearchStrategyProbabilityGapExplainabilityDecayReport)
    assert RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_STATUSES == (
        "pass",
        "watch",
        "block",
    )

    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary.reason_code_counts[0], readonly=False)

    assert_decimal_public_fields(gap_input())
    assert_decimal_public_fields(summary)
    assert_decimal_public_fields(row)
    assert_decimal_public_fields(summary.reason_code_counts[0])

    assert __import__(
        "polymarket_alpha_lab.research_strategy_probability_gap_explainability_decay_report",
        fromlist=["__all__"],
    ).__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_PROBABILITY_GAP_EXPLAINABILITY_DECAY_STATUSES",
        "ResearchStrategyProbabilityGapExplainabilityDecayConfig",
        "ResearchStrategyProbabilityGapExplainabilityDecayInput",
        "ResearchStrategyProbabilityGapExplainabilityDecayReasonCodeCount",
        "ResearchStrategyProbabilityGapExplainabilityDecayReport",
        "ResearchStrategyProbabilityGapExplainabilityDecayRow",
        "build_research_strategy_probability_gap_explainability_decay_report",
        "research_strategy_probability_gap_explainability_decay_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    assert not {name.split(".", maxsplit=1)[0] for name in imported_modules} & forbidden_import_roots
    assert not set(call_names) & forbidden_calls
