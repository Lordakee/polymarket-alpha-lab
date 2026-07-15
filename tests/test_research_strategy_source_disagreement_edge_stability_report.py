from __future__ import annotations

import ast
from hashlib import sha256
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_source_disagreement_edge_stability_report import (
    DEFAULT_RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_STATUSES,
    ResearchStrategySourceDisagreementEdgeStabilityConfig,
    ResearchStrategySourceDisagreementEdgeStabilityInput,
    ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount,
    ResearchStrategySourceDisagreementEdgeStabilityReport,
    ResearchStrategySourceDisagreementEdgeStabilityRow,
    build_research_strategy_source_disagreement_edge_stability_report,
    research_strategy_source_disagreement_edge_stability_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategySourceDisagreementEdgeStabilityConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_REPORT_CONFIG_VERSION
        ),
        "max_authority_conflict_pass_pressure": d("0.200000"),
        "max_authority_conflict_watch_pressure": d("0.450000"),
        "min_source_freshness_pass_score": d("0.750000"),
        "min_source_freshness_watch_score": d("0.500000"),
        "min_corroboration_pass_score": d("0.700000"),
        "min_corroboration_watch_score": d("0.450000"),
        "min_edge_persistence_pass_score": d("0.700000"),
        "min_edge_persistence_watch_score": d("0.400000"),
        "max_edge_drift_pass_probability": d("0.050000"),
        "max_edge_drift_watch_probability": d("0.150000"),
        "max_market_cost_pass_pressure": d("0.300000"),
        "max_market_cost_watch_pressure": d("0.650000"),
        "composite_pass_floor": d("0.700000"),
        "composite_watch_floor": d("0.450000"),
        "authority_conflict_weight": d("1.000000"),
        "freshness_weight": d("1.000000"),
        "corroboration_weight": d("1.000000"),
        "edge_persistence_weight": d("1.000000"),
        "market_cost_weight": d("1.000000"),
    }
    values.update(overrides)
    return ResearchStrategySourceDisagreementEdgeStabilityConfig(**values)


def report_input(
    **overrides: object,
) -> ResearchStrategySourceDisagreementEdgeStabilityInput:
    values = {
        "candidate_id": "candidate_alpha_raw_id",
        "market_id": "market_alpha_raw_id",
        "market_slug": "alpha-market-slug",
        "market_question": "Will alpha resolve yes?",
        "source_url": "https://source.example/private-alpha?token=SECRET",
        "source_text": "private alpha source text",
        "observed_at": datetime(2026, 7, 8, 11, 40, tzinfo=UTC),
        "source_disagreement_probability": d("0.100000"),
        "source_authority_weight": d("0.800000"),
        "source_freshness_score": d("0.900000"),
        "independent_corroboration_score": d("0.850000"),
        "current_edge_probability": d("0.060000"),
        "prior_edge_probability": d("0.055000"),
        "edge_persistence_score": d("0.920000"),
        "market_cost_pressure_score": d("0.120000"),
    }
    values.update(overrides)
    return ResearchStrategySourceDisagreementEdgeStabilityInput(**values)


def report(
    *rows: ResearchStrategySourceDisagreementEdgeStabilityInput,
    cfg: ResearchStrategySourceDisagreementEdgeStabilityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategySourceDisagreementEdgeStabilityReport:
    return build_research_strategy_source_disagreement_edge_stability_report(
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


def resign_payload(payload: dict[str, Any]) -> None:
    unsigned = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    payload["derived_validation_digest"] = sha256(encoded).hexdigest()


def test_report_scores_disagreement_edge_stability_and_cost_pressure() -> None:
    summary = report(
        report_input(
            candidate_id="candidate_alpha_raw_id",
            market_id="market_alpha_raw_id",
            market_slug="alpha-market-slug",
            source_disagreement_probability=d("0.100000"),
            source_authority_weight=d("0.800000"),
            source_freshness_score=d("0.900000"),
            independent_corroboration_score=d("0.850000"),
            current_edge_probability=d("0.060000"),
            prior_edge_probability=d("0.055000"),
            edge_persistence_score=d("0.920000"),
            market_cost_pressure_score=d("0.120000"),
        ),
        report_input(
            candidate_id="candidate_beta_raw_id",
            market_id="market_beta_raw_id",
            market_slug="beta-market-slug",
            source_disagreement_probability=d("0.400000"),
            source_authority_weight=d("0.800000"),
            source_freshness_score=d("0.650000"),
            independent_corroboration_score=d("0.600000"),
            current_edge_probability=d("0.050000"),
            prior_edge_probability=d("0.000000"),
            edge_persistence_score=d("0.720000"),
            market_cost_pressure_score=d("0.500000"),
        ),
        report_input(
            candidate_id="candidate_gamma_raw_id",
            market_id="market_gamma_raw_id",
            market_slug="gamma-market-slug",
            source_disagreement_probability=d("0.700000"),
            source_authority_weight=d("0.900000"),
            source_freshness_score=d("0.300000"),
            independent_corroboration_score=d("0.200000"),
            current_edge_probability=d("0.350000"),
            prior_edge_probability=d("0.050000"),
            edge_persistence_score=d("0.350000"),
            market_cost_pressure_score=d("0.800000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategySourceDisagreementEdgeStabilityReport
    assert summary.generated_at == GENERATED_AT
    assert summary.source_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_authority_weighted_conflict_pressure == d("0.343333")
    assert summary.mean_edge_stability_score == d("0.545000")
    assert summary.mean_market_cost_pressure_score == d("0.473333")
    assert summary.mean_disagreement_edge_stability_score == d("0.579000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "source_disagreement_edge_stability_report_block",
        "authority_conflict_pressure_review",
        "source_freshness_review",
        "corroboration_review",
        "edge_persistence_review",
        "edge_drift_review",
        "market_cost_pressure_review",
        "composite_stability_review",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64

    blocked, watched, passed = summary.rows
    assert isinstance(blocked, ResearchStrategySourceDisagreementEdgeStabilityRow)
    assert blocked.authority_weighted_conflict_pressure == d("0.630000")
    assert blocked.edge_drift_probability == d("0.300000")
    assert blocked.edge_stability_score == d("0.050000")
    assert blocked.disagreement_edge_stability_score == d("0.224000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "authority_conflict_pressure_block",
        "source_freshness_block",
        "corroboration_block",
        "edge_persistence_block",
        "edge_drift_block",
        "market_cost_pressure_block",
        "composite_stability_block",
    )

    assert watched.status == "watch"
    assert watched.authority_weighted_conflict_pressure == d("0.320000")
    assert watched.edge_drift_probability == d("0.050000")
    assert watched.edge_stability_score == d("0.670000")
    assert watched.disagreement_edge_stability_score == d("0.620000")
    assert watched.reason_codes == (
        "authority_conflict_pressure_watch",
        "source_freshness_watch",
        "corroboration_watch",
        "edge_persistence_watch",
        "market_cost_pressure_watch",
        "composite_stability_watch",
    )

    assert passed.status == "pass"
    assert passed.authority_weighted_conflict_pressure == d("0.080000")
    assert passed.edge_stability_score == d("0.915000")
    assert passed.disagreement_edge_stability_score == d("0.893000")
    assert passed.reason_codes == ("source_disagreement_edge_stability_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts[
        "market_cost_pressure_watch"
    ] == ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount(
        reason_code="market_cost_pressure_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_boundary_thresholds_classify_pass_watch_and_block() -> None:
    summary = report(
        report_input(
            candidate_id="candidate_pass_boundary",
            market_id="market_pass_boundary",
            source_disagreement_probability=d("0.250000"),
            source_authority_weight=d("0.800000"),
            source_freshness_score=d("0.750000"),
            independent_corroboration_score=d("0.700000"),
            current_edge_probability=d("0.100000"),
            prior_edge_probability=d("0.050000"),
            edge_persistence_score=d("0.750000"),
            market_cost_pressure_score=d("0.300000"),
        ),
        report_input(
            candidate_id="candidate_watch_boundary",
            market_id="market_watch_boundary",
            source_disagreement_probability=d("0.500000"),
            source_authority_weight=d("0.900000"),
            source_freshness_score=d("0.500000"),
            independent_corroboration_score=d("0.450000"),
            current_edge_probability=d("0.200000"),
            prior_edge_probability=d("0.050000"),
            edge_persistence_score=d("0.550000"),
            market_cost_pressure_score=d("0.650000"),
        ),
        report_input(
            candidate_id="candidate_block_boundary",
            market_id="market_block_boundary",
            source_disagreement_probability=d("0.450001"),
            source_authority_weight=d("1.000000"),
            source_freshness_score=d("0.499999"),
            independent_corroboration_score=d("0.449999"),
            current_edge_probability=d("0.200001"),
            prior_edge_probability=d("0.050000"),
            edge_persistence_score=d("0.550000"),
            market_cost_pressure_score=d("0.650001"),
        ),
    )

    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")
    blocked, watched, passed = summary.rows
    assert passed.reason_codes == ("source_disagreement_edge_stability_pass",)
    assert watched.disagreement_edge_stability_score == d("0.450000")
    assert watched.reason_codes == (
        "authority_conflict_pressure_watch",
        "source_freshness_watch",
        "corroboration_watch",
        "edge_persistence_watch",
        "edge_drift_watch",
        "market_cost_pressure_watch",
        "composite_stability_watch",
    )
    assert blocked.reason_codes == (
        "authority_conflict_pressure_block",
        "source_freshness_block",
        "corroboration_block",
        "edge_persistence_watch",
        "edge_drift_block",
        "market_cost_pressure_block",
        "composite_stability_block",
    )


def test_public_payload_is_deterministic_digest_guarded_and_leak_free() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_source_disagreement_edge_stability_report_payload(
        report(report_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_source_disagreement_edge_stability_report_payload(
        report(report_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["source_row_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["authority_weighted_conflict_pressure"] == "0.080000"
    assert first_payload["rows"][0]["edge_stability_score"] == "0.915000"
    assert first_payload["rows"][0]["disagreement_edge_stability_score"] == "0.893000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
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
        "alpha-market-slug",
        "will alpha resolve yes",
        "https://source.example/private-alpha",
        "private alpha source text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "trading",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in payload_text

    tampered_payload = research_strategy_source_disagreement_edge_stability_report_payload(
        report(report_input()),
    )
    tampered_payload["rows"][0]["edge_stability_score"] = "0.111111"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_source_disagreement_edge_stability_report_payload(
            tampered_payload,
        )

    tampered_report = report(report_input())
    object.__setattr__(tampered_report.rows[0], "source_freshness_score", d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest|mean"):
        research_strategy_source_disagreement_edge_stability_report_payload(tampered_report)

    unsafe_payload = dict(first_payload)
    unsafe_payload["rows"] = [
        {
            **first_payload["rows"][0],
            "candidate_id": "candidate_alpha_raw_id",
        },
    ]
    with pytest.raises(ValueError, match="unsafe|unexpected|derived_validation_digest"):
        research_strategy_source_disagreement_edge_stability_report_payload(unsafe_payload)


def test_resigned_payload_cannot_disable_nested_hard_flags() -> None:
    payload = research_strategy_source_disagreement_edge_stability_report_payload(
        report(report_input()),
    )
    payload["rows"][0]["readonly"] = False
    resign_payload(payload["rows"][0])
    resign_payload(payload)

    with pytest.raises(ValueError, match="readonly"):
        research_strategy_source_disagreement_edge_stability_report_payload(payload)


def test_resigned_payload_rejects_unexpected_public_fields() -> None:
    payload = research_strategy_source_disagreement_edge_stability_report_payload(
        report(report_input()),
    )
    payload["rows"][0]["opaque_note"] = "alpha"
    resign_payload(payload["rows"][0])
    resign_payload(payload)

    with pytest.raises(ValueError, match="unexpected"):
        research_strategy_source_disagreement_edge_stability_report_payload(payload)


def test_custom_config_validation_and_hard_flags() -> None:
    strict = config(
        max_authority_conflict_pass_pressure=d("0.050000"),
        composite_pass_floor=d("0.950000"),
        composite_watch_floor=d("0.600000"),
    )
    summary = report(report_input(), cfg=strict)

    assert summary.status == "watch"
    assert summary.rows[0].reason_codes == (
        "authority_conflict_pressure_watch",
        "composite_stability_watch",
    )

    with pytest.raises(ValueError, match="config_version"):
        config(config_version="unsupported-config")
    with pytest.raises(ValueError, match="max_authority_conflict_pass_pressure"):
        config(
            max_authority_conflict_pass_pressure=d("0.500000"),
            max_authority_conflict_watch_pressure=d("0.400000"),
        )
    with pytest.raises(ValueError, match="min_source_freshness_pass_score"):
        config(
            min_source_freshness_pass_score=d("0.400000"),
            min_source_freshness_watch_score=d("0.500000"),
        )
    with pytest.raises(ValueError, match="composite_pass_floor"):
        config(composite_pass_floor=d("0.400000"), composite_watch_floor=d("0.500000"))
    with pytest.raises(ValueError, match="weight"):
        config(
            authority_conflict_weight=d("0.000000"),
            freshness_weight=d("0.000000"),
            corroboration_weight=d("0.000000"),
            edge_persistence_weight=d("0.000000"),
            market_cost_weight=d("0.000000"),
        )
    with pytest.raises(ValueError, match="source_disagreement_probability"):
        report_input(source_disagreement_probability=0.1)
    with pytest.raises(ValueError, match="source_authority_weight"):
        report_input(source_authority_weight=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="current_edge_probability"):
        report_input(current_edge_probability=d("1.200000"))
    with pytest.raises(ValueError, match="observed_at"):
        report_input(observed_at=datetime(2026, 7, 8, 11, 40))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            report_input(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(report_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            report_input(candidate_id="same_candidate", market_id="market_a"),
            report_input(candidate_id="same_candidate", market_id="market_b"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_external_surfaces() -> None:
    summary = report(report_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_STATUSES == (
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
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            source_freshness_score=d("0.100000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            source_row_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )

    for value in (
        config(),
        report_input(),
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
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "count",
                    "floor",
                    "pressure",
                    "probability",
                    "ratio",
                    "score",
                    "weight",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_source_disagreement_edge_stability_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_SOURCE_DISAGREEMENT_EDGE_STABILITY_STATUSES",
        "ResearchStrategySourceDisagreementEdgeStabilityConfig",
        "ResearchStrategySourceDisagreementEdgeStabilityInput",
        "ResearchStrategySourceDisagreementEdgeStabilityReasonCodeCount",
        "ResearchStrategySourceDisagreementEdgeStabilityRow",
        "ResearchStrategySourceDisagreementEdgeStabilityReport",
        "build_research_strategy_source_disagreement_edge_stability_report",
        "research_strategy_source_disagreement_edge_stability_report_payload",
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

    forbidden_source_terms = (
        "reco" + "mmendation",
        "siz" + "ing",
        "b" + "uy",
        "se" + "ll",
        "wal" + "let",
        "or" + "der",
        "li" + "ve",
        "trad" + "ing",
        "data" + "base",
        "net" + "work",
        "request",
        "socket",
        "subprocess",
        "open(",
    )
    assert all(term not in source.lower() for term in forbidden_source_terms)

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
