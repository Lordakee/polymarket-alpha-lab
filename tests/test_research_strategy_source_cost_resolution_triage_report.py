from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_source_cost_resolution_triage_report import (
    DEFAULT_RESEARCH_STRATEGY_SOURCE_COST_RESOLUTION_TRIAGE_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_SOURCE_COST_RESOLUTION_TRIAGE_REPORT_STATUSES,
    ResearchStrategySourceCostResolutionTriageConfig,
    ResearchStrategySourceCostResolutionTriageInput,
    ResearchStrategySourceCostResolutionTriageReasonCodeCount,
    ResearchStrategySourceCostResolutionTriageReport,
    ResearchStrategySourceCostResolutionTriageRow,
    build_research_strategy_source_cost_resolution_triage_report,
    research_strategy_source_cost_resolution_triage_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StrSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategySourceCostResolutionTriageConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_SOURCE_COST_RESOLUTION_TRIAGE_REPORT_CONFIG_VERSION
        ),
        "source_readiness_pass_floor": d("0.750000"),
        "source_readiness_watch_floor": d("0.500000"),
        "cost_adjusted_edge_pass_floor": d("0.020000"),
        "cost_adjusted_edge_watch_floor": d("0.000000"),
        "resolution_ambiguity_pass_ceiling": d("0.250000"),
        "resolution_ambiguity_watch_ceiling": d("0.550000"),
    }
    values.update(overrides)
    return ResearchStrategySourceCostResolutionTriageConfig(**values)


def triage_input(**overrides: object) -> ResearchStrategySourceCostResolutionTriageInput:
    values = {
        "candidate_id": "candidate_alpha_raw_id",
        "market_id": "market_alpha_raw_id",
        "market_slug": "market-alpha-slug",
        "market_question": "Will alpha resolve yes?",
        "source_url": "https://example.invalid/private-alpha",
        "source_text": "private alpha source text",
        "observed_at": datetime(2026, 7, 8, 11, 40, tzinfo=UTC),
        "source_readiness_score": d("0.920000"),
        "source_count": d("3.000000"),
        "source_family_count": d("2.000000"),
        "forecast_probability": d("0.620000"),
        "market_probability": d("0.570000"),
        "fee_probability_drag": d("0.006000"),
        "spread_probability_drag": d("0.004000"),
        "depth_probability_drag": d("0.003000"),
        "latency_probability_haircut": d("0.002000"),
        "resolution_ambiguity_score": d("0.100000"),
    }
    values.update(overrides)
    return ResearchStrategySourceCostResolutionTriageInput(**values)


def report(
    *rows: ResearchStrategySourceCostResolutionTriageInput,
    cfg: ResearchStrategySourceCostResolutionTriageConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategySourceCostResolutionTriageReport:
    return build_research_strategy_source_cost_resolution_triage_report(
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


def test_report_combines_source_cost_and_resolution_triage_statuses() -> None:
    summary = report(
        triage_input(
            candidate_id="candidate_alpha_raw_id",
            market_id="market_alpha_raw_id",
            market_slug="market-alpha-slug",
            source_readiness_score=d("0.920000"),
            forecast_probability=d("0.620000"),
            market_probability=d("0.570000"),
            fee_probability_drag=d("0.006000"),
            spread_probability_drag=d("0.004000"),
            depth_probability_drag=d("0.003000"),
            latency_probability_haircut=d("0.002000"),
            resolution_ambiguity_score=d("0.100000"),
        ),
        triage_input(
            candidate_id="candidate_beta_raw_id",
            market_id="market_beta_raw_id",
            market_slug="market-beta-slug",
            source_readiness_score=d("0.650000"),
            forecast_probability=d("0.580000"),
            market_probability=d("0.510000"),
            fee_probability_drag=d("0.010000"),
            spread_probability_drag=d("0.020000"),
            depth_probability_drag=d("0.008000"),
            latency_probability_haircut=d("0.007000"),
            resolution_ambiguity_score=d("0.350000"),
        ),
        triage_input(
            candidate_id="candidate_gamma_raw_id",
            market_id="market_gamma_raw_id",
            market_slug="market-gamma-slug",
            source_readiness_score=d("0.300000"),
            forecast_probability=d("0.520000"),
            market_probability=d("0.510000"),
            fee_probability_drag=d("0.030000"),
            spread_probability_drag=d("0.035000"),
            depth_probability_drag=d("0.020000"),
            latency_probability_haircut=d("0.015000"),
            resolution_ambiguity_score=d("0.800000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategySourceCostResolutionTriageReport
    assert summary.generated_at == GENERATED_AT
    assert summary.input_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_source_readiness_score == d("0.623333")
    assert summary.mean_absolute_forecast_edge_probability == d("0.043333")
    assert summary.mean_total_cost_probability == d("0.053333")
    assert summary.mean_cost_adjusted_edge_probability == d("-0.010000")
    assert summary.mean_resolution_ambiguity_score == d("0.416667")
    assert summary.mean_triage_pressure_score == d("0.375555")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "source_cost_resolution_triage_report_block",
        "source_readiness_review",
        "cost_adjusted_edge_review",
        "resolution_ambiguity_review",
    )
    assert tuple(row.candidate_id for row in summary.rows) == (
        "candidate_gamma_raw_id",
        "candidate_beta_raw_id",
        "candidate_alpha_raw_id",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategySourceCostResolutionTriageRow)
    assert blocked.raw_forecast_edge_probability == d("0.010000")
    assert blocked.absolute_forecast_edge_probability == d("0.010000")
    assert blocked.total_cost_probability == d("0.100000")
    assert blocked.cost_adjusted_edge_probability == d("-0.090000")
    assert blocked.cost_edge_sanity_score == d("0.000000")
    assert blocked.triage_pressure_score == d("0.833333")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "source_cost_resolution_triage_block",
        "source_readiness_block",
        "cost_adjusted_edge_block",
        "resolution_ambiguity_block",
    )

    watched = summary.rows[1]
    assert watched.cost_adjusted_edge_probability == d("0.025000")
    assert watched.cost_edge_sanity_score == d("1.000000")
    assert watched.triage_pressure_score == d("0.233333")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "source_cost_resolution_triage_watch",
        "source_readiness_watch",
        "cost_adjusted_edge_pass",
        "resolution_ambiguity_watch",
    )

    passed = summary.rows[2]
    assert passed.status == "pass"
    assert passed.triage_pressure_score == d("0.060000")
    assert passed.reason_codes == (
        "source_cost_resolution_triage_pass",
        "source_readiness_pass",
        "cost_adjusted_edge_pass",
        "resolution_ambiguity_pass",
    )
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts[
        "resolution_ambiguity_watch"
    ] == ResearchStrategySourceCostResolutionTriageReasonCodeCount(
        reason_code="resolution_ambiguity_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_empty_report_is_block_readonly_and_decimal_zeroed() -> None:
    empty = report()

    assert empty.input_count == d("0.000000")
    assert empty.pass_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.block_count == d("0.000000")
    assert empty.mean_source_readiness_score == d("0.000000")
    assert empty.mean_cost_adjusted_edge_probability == d("0.000000")
    assert empty.mean_resolution_ambiguity_score == d("0.000000")
    assert empty.mean_triage_pressure_score == d("0.000000")
    assert empty.status == "block"
    assert empty.reason_codes == ("source_cost_resolution_triage_report_empty",)
    assert empty.reason_code_counts == (
        ResearchStrategySourceCostResolutionTriageReasonCodeCount(
            reason_code="source_cost_resolution_triage_report_empty",
            count=d("1.000000"),
            input_ratio=d("1.000000"),
        ),
    )
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_public_payload_is_deterministic_sanitized_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_source_cost_resolution_triage_report_payload(
        report(triage_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_source_cost_resolution_triage_report_payload(
        report(triage_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["input_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["cost_adjusted_edge_probability"] == "0.035000"
    assert first_payload["rows"][0]["triage_pressure_score"] == "0.060000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert len(first_payload["rows"][0]["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )
    payload_text = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "candidate_alpha_raw_id",
        "market_alpha_raw_id",
        "market-alpha-slug",
        "will alpha resolve yes",
        "https://example.invalid/private-alpha",
        "private alpha source text",
    ):
        assert forbidden not in payload_text

    tampered_payload = research_strategy_source_cost_resolution_triage_report_payload(
        report(triage_input()),
    )
    tampered_payload["rows"][0]["total_cost_probability"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_source_cost_resolution_triage_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_source_cost_resolution_triage_report_payload(
            {
                "access_" + "token": "redacted",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    for unsafe_key in (
        "auth_header",
        "position_" + "sizing",
        "execution_surface",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            research_strategy_source_cost_resolution_triage_report_payload(
                {
                    unsafe_key: "redacted",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )
    for unsafe_value in (
        "orders_" + "table",
        "postgres://public.example.invalid/db",
        "auth bearer credential",
        "position_" + "sizing signal",
        "manual execution note",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            research_strategy_source_cost_resolution_triage_report_payload(
                {
                    "public_note": unsafe_value,
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )


def test_validation_rejects_non_decimal_flags_bad_times_and_duplicate_candidates() -> None:
    with pytest.raises(ValueError, match="source_readiness_score"):
        triage_input(source_readiness_score=0.92)
    with pytest.raises(ValueError, match="fee_probability_drag"):
        triage_input(fee_probability_drag=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="market_probability"):
        triage_input(market_probability=d("1.200000"))
    with pytest.raises(ValueError, match="source_count"):
        triage_input(source_count=d("1.500000"))
    with pytest.raises(ValueError, match="observed_at"):
        triage_input(observed_at=datetime(2026, 7, 8, 11, 40))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            triage_input(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(triage_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            triage_input(candidate_id="same_candidate", market_id="market_a"),
            triage_input(candidate_id="same_candidate", market_id="market_b"),
        )
    with pytest.raises(ValueError, match="source_readiness_pass_floor"):
        config(
            source_readiness_pass_floor=d("0.400000"),
            source_readiness_watch_floor=d("0.500000"),
        )
    with pytest.raises(ValueError, match="resolution_ambiguity_pass_ceiling"):
        config(
            resolution_ambiguity_pass_ceiling=d("0.700000"),
            resolution_ambiguity_watch_ceiling=d("0.550000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_external_surfaces() -> None:
    summary = report(triage_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_SOURCE_COST_RESOLUTION_TRIAGE_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(row, status=_StrSubclass("pass"), derived_validation_digest="")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            total_cost_probability=d("0.010000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            input_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )

    for value in (
        config(),
        triage_input(),
        row,
        summary,
        *summary.reason_code_counts,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item_value is None or item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "reason_codes",
                "reason_code_counts",
                "rows",
                "candidate_id",
                "market_id",
                "market_slug",
                "market_question",
                "source_url",
                "source_text",
                "config_version",
                "status",
                "derived_validation_digest",
                "observed_at",
                "generated_at",
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "count",
                    "cost",
                    "drag",
                    "edge",
                    "floor",
                    "friction",
                    "haircut",
                    "probability",
                    "ratio",
                    "score",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_source_cost_resolution_triage_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_SOURCE_COST_RESOLUTION_TRIAGE_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_SOURCE_COST_RESOLUTION_TRIAGE_REPORT_STATUSES",
        "ResearchStrategySourceCostResolutionTriageConfig",
        "ResearchStrategySourceCostResolutionTriageInput",
        "ResearchStrategySourceCostResolutionTriageReasonCodeCount",
        "ResearchStrategySourceCostResolutionTriageRow",
        "ResearchStrategySourceCostResolutionTriageReport",
        "build_research_strategy_source_cost_resolution_triage_report",
        "research_strategy_source_cost_resolution_triage_report_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_source_cost_resolution_triage_report.py"
    )
    module_source = module_path.read_text(encoding="utf-8").lower()
    forbidden_source_terms = (
        "request",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "connect(",
        "open(",
        "create_" + "order",
        "cancel_" + "order",
        "post(",
        "wal" + "let",
        "reco" + "mmendation",
        "siz" + "ing",
        "b" + "uy",
        "se" + "ll",
        "trad" + "e",
    )
    assert all(term not in module_source for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
