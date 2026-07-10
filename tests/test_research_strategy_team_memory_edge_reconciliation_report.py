from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_team_memory_edge_reconciliation_report.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_team_memory_edge_reconciliation_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def item(**overrides: object) -> Any:
    module = api()
    values = {
        "analyst_row_label": "alpha_memory_edge",
        "memory_signal_label": "calibrated_research_memory",
        "observed_at": datetime(2026, 7, 8, 11, 45, tzinfo=UTC),
        "probability_edge_estimate": d("0.080000"),
        "calibration_freshness_score": d("0.900000"),
        "prior_outcome_learning_score": d("0.800000"),
        "evidence_confidence_score": d("0.880000"),
        "cost_pressure_score": d("0.120000"),
    }
    values.update(overrides)
    return module.ResearchStrategyTeamMemoryEdgeReconciliationInput(**values)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_TEAM_MEMORY_EDGE_RECONCILIATION_CONFIG_VERSION
        ),
        "probability_edge_pass_floor": d("0.050000"),
        "probability_edge_watch_floor": d("0.015000"),
        "calibration_freshness_pass_floor": d("0.800000"),
        "calibration_freshness_watch_floor": d("0.500000"),
        "prior_outcome_learning_pass_floor": d("0.750000"),
        "prior_outcome_learning_watch_floor": d("0.500000"),
        "evidence_confidence_pass_floor": d("0.800000"),
        "evidence_confidence_watch_floor": d("0.550000"),
        "cost_pressure_pass_ceiling": d("0.250000"),
        "cost_pressure_watch_ceiling": d("0.600000"),
        "reconciliation_score_pass_floor": d("0.750000"),
        "reconciliation_score_watch_floor": d("0.500000"),
        "probability_edge_weight": d("0.250000"),
        "calibration_freshness_weight": d("0.200000"),
        "prior_outcome_learning_weight": d("0.200000"),
        "evidence_confidence_weight": d("0.250000"),
        "cost_pressure_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchStrategyTeamMemoryEdgeReconciliationConfig(**values)


def build_report(*rows: Any, config: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_strategy_team_memory_edge_reconciliation_report(
        rows,
        config=config or cfg(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item_value in value.values():
            values.extend(walk_values(item_value))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item_value in value:
            values.extend(walk_values(item_value))
        return tuple(values)
    return (value,)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def strip_digest_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: strip_digest_fields(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [strip_digest_fields(item) for item in value]
    return value


def payload_digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        strip_digest_fields(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def resign_payload_tree(value: Any) -> Any:
    if isinstance(value, dict):
        for item in value.values():
            resign_payload_tree(item)
        if "derived_validation_digest" in value:
            value["derived_validation_digest"] = payload_digest(value)
    elif isinstance(value, list):
        for item in value:
            resign_payload_tree(item)
    return value


def test_reconciliation_scores_pass_watch_and_block_rows() -> None:
    report = build_report(
        item(
            analyst_row_label="alpha_memory_edge",
            probability_edge_estimate=d("0.080000"),
            calibration_freshness_score=d("0.900000"),
            prior_outcome_learning_score=d("0.800000"),
            evidence_confidence_score=d("0.880000"),
            cost_pressure_score=d("0.120000"),
        ),
        item(
            analyst_row_label="beta_memory_edge",
            probability_edge_estimate=d("-0.030000"),
            calibration_freshness_score=d("0.700000"),
            prior_outcome_learning_score=d("0.650000"),
            evidence_confidence_score=d("0.720000"),
            cost_pressure_score=d("0.400000"),
        ),
        item(
            analyst_row_label="gamma_memory_edge",
            probability_edge_estimate=d("0.005000"),
            calibration_freshness_score=d("0.300000"),
            prior_outcome_learning_score=d("0.400000"),
            evidence_confidence_score=d("0.450000"),
            cost_pressure_score=d("0.750000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-strategy-team-memory-edge-reconciliation-v0"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_absolute_probability_edge == d("0.038333")
    assert report.average_cost_pressure_score == d("0.423333")
    assert report.average_reconciliation_score == d("0.620167")
    assert report.min_reconciliation_score == d("0.302500")
    assert report.status == "block"
    assert report.reason_codes == (
        "team_memory_edge_reconciliation_report_block",
        "probability_edge_review",
        "calibration_freshness_review",
        "prior_outcome_learning_review",
        "evidence_confidence_review",
        "cost_pressure_review",
        "reconciliation_score_review",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.analyst_row_label for row in report.rows) == (
        "gamma_memory_edge",
        "beta_memory_edge",
        "alpha_memory_edge",
    )

    blocked = report.rows[0]
    assert blocked.absolute_probability_edge == d("0.005000")
    assert blocked.probability_edge_score == d("0.100000")
    assert blocked.cost_quality_score == d("0.250000")
    assert blocked.reconciliation_score == d("0.302500")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "probability_edge_gap",
        "calibration_freshness_gap",
        "prior_outcome_learning_gap",
        "evidence_confidence_gap",
        "cost_pressure_gap",
        "reconciliation_score_gap",
    )

    watched = report.rows[1]
    assert watched.absolute_probability_edge == d("0.030000")
    assert watched.probability_edge_score == d("0.600000")
    assert watched.cost_quality_score == d("0.600000")
    assert watched.reconciliation_score == d("0.660000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "probability_edge_gap",
        "calibration_freshness_gap",
        "prior_outcome_learning_gap",
        "evidence_confidence_gap",
        "cost_pressure_gap",
        "reconciliation_score_gap",
    )

    passed = report.rows[2]
    assert passed.reconciliation_score == d("0.898000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("team_memory_edge_reconciliation_pass",)

    counts = {row.reason_code: row for row in report.reason_code_counts}
    assert counts["probability_edge_gap"].count == d("2.000000")
    assert counts["probability_edge_gap"].input_ratio == d("0.666667")


def test_payload_is_deterministic_decimal_stringed_and_digest_validated() -> None:
    first = build_report(
        item(analyst_row_label="beta_memory_edge", probability_edge_estimate=d("-0.030000")),
        item(analyst_row_label="alpha_memory_edge"),
    )
    second = build_report(
        item(analyst_row_label="alpha_memory_edge"),
        item(analyst_row_label="beta_memory_edge", probability_edge_estimate=d("-0.030000")),
    )

    module = api()
    first_payload = module.research_strategy_team_memory_edge_reconciliation_report_payload(first)
    second_payload = module.research_strategy_team_memory_edge_reconciliation_report_payload(second)

    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["input_count"] == "2.000000"
    assert first_payload["rows"][0]["probability_edge_estimate"] == "-0.030000"
    assert first_payload["rows"][0]["absolute_probability_edge"] == "0.030000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert first_payload["derived_validation_digest"] == payload_digest(first_payload)
    assert first_payload["config"]["derived_validation_digest"] == payload_digest(
        first_payload["config"],
    )
    assert all(
        row["derived_validation_digest"] == payload_digest(row)
        for row in first_payload["rows"]
    )
    assert all(
        row["derived_validation_digest"] == payload_digest(row)
        for row in first_payload["reason_code_counts"]
    )
    assert module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
        first_payload,
    )
    json.dumps(first_payload, sort_keys=True)
    assert not any(type(value) in (int, float, Decimal) for value in walk_values(first_payload))

    tampered = json.loads(json.dumps(first_payload, sort_keys=True))
    tampered["rows"][0]["reconciliation_score"] = "0.123456"
    with pytest.raises(ValueError, match="derived_validation_digest payload mismatch"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(tampered)


def test_manual_review_rank_follows_stable_row_order() -> None:
    module = api()
    report = build_report(
        item(
            analyst_row_label="pass_memory_edge",
            probability_edge_estimate=d("0.080000"),
        ),
        item(
            analyst_row_label="block_memory_edge",
            probability_edge_estimate=d("0.005000"),
            calibration_freshness_score=d("0.300000"),
            prior_outcome_learning_score=d("0.400000"),
            evidence_confidence_score=d("0.450000"),
            cost_pressure_score=d("0.750000"),
        ),
        item(
            analyst_row_label="watch_memory_edge",
            probability_edge_estimate=d("0.030000"),
            calibration_freshness_score=d("0.700000"),
            prior_outcome_learning_score=d("0.650000"),
            evidence_confidence_score=d("0.720000"),
            cost_pressure_score=d("0.400000"),
        ),
    )
    payload = module.research_strategy_team_memory_edge_reconciliation_report_payload(
        report,
    )

    assert tuple(getattr(row, "manual_review_rank", None) for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.get("manual_review_rank") for row in payload["rows"]) == (
        "1.000000",
        "2.000000",
        "3.000000",
    )


def test_stable_sort_uses_public_label_tie_breakers() -> None:
    report = build_report(
        item(
            analyst_row_label="zeta_memory_edge",
            memory_signal_label="beta_signal",
        ),
        item(
            analyst_row_label="alpha_memory_edge",
            memory_signal_label="zeta_signal",
        ),
        item(
            analyst_row_label="alpha_memory_edge",
            memory_signal_label="alpha_signal",
        ),
    )

    assert tuple(
        (row.analyst_row_label, row.memory_signal_label, row.manual_review_rank)
        for row in report.rows
    ) == (
        ("alpha_memory_edge", "alpha_signal", d("1.000000")),
        ("alpha_memory_edge", "zeta_signal", d("2.000000")),
        ("zeta_memory_edge", "beta_signal", d("3.000000")),
    )


def test_public_validator_rejects_resigned_manual_review_rank_forgeries() -> None:
    module = api()
    payload = module.research_strategy_team_memory_edge_reconciliation_report_payload(
        build_report(
            item(analyst_row_label="alpha_memory_edge"),
            item(
                analyst_row_label="beta_memory_edge",
                probability_edge_estimate=d("-0.030000"),
            ),
        ),
    )

    forged_rank = json.loads(json.dumps(payload))
    forged_rank["rows"][0]["manual_review_rank"] = "2.000000"
    resign_payload_tree(forged_rank)
    with pytest.raises(
        ValueError,
        match="manual_review_rank must match stable row sequence",
    ):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            forged_rank,
        )

    forged_order = json.loads(json.dumps(payload))
    forged_order["rows"].reverse()
    for index, row in enumerate(forged_order["rows"], start=1):
        row["manual_review_rank"] = f"{index}.000000"
    resign_payload_tree(forged_order)
    with pytest.raises(ValueError, match="rows must use stable sort"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            forged_order,
        )


def test_decimal_validation_checks_raw_bounds_non_finite_and_signed_zero() -> None:
    module = api()

    for non_finite in (d("NaN"), d("Infinity"), d("-Infinity")):
        with pytest.raises(ValueError, match="probability_edge_estimate must be finite"):
            item(probability_edge_estimate=non_finite)
        with pytest.raises(ValueError, match="calibration_freshness_score must be finite"):
            item(calibration_freshness_score=non_finite)
        with pytest.raises(ValueError, match="probability_edge_weight must be finite"):
            cfg(probability_edge_weight=non_finite)
        with pytest.raises(ValueError, match="count must be finite"):
            module.ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount(
                reason_code="team_memory_edge_reconciliation_pass",
                count=non_finite,
                input_ratio=d("1.000000"),
            )

    with pytest.raises(
        ValueError,
        match="calibration_freshness_score must be between 0.000000 and 1.000000",
    ):
        item(calibration_freshness_score=d("-0.0000004"))
    with pytest.raises(
        ValueError,
        match="probability_edge_pass_floor must be between 0.000000 and 1.000000",
    ):
        cfg(probability_edge_pass_floor=d("1.0000004"))
    with pytest.raises(
        ValueError,
        match="probability_edge_estimate must be between -1.000000 and 1.000000",
    ):
        item(probability_edge_estimate=d("1.0000004"))

    with pytest.raises(ValueError, match="probability_edge_weight.*signed zero"):
        cfg(probability_edge_weight=d("-0.000000"))
    with pytest.raises(ValueError, match="probability_edge_estimate.*signed zero"):
        item(probability_edge_estimate=d("-0.0000004"))
    with pytest.raises(ValueError, match="count.*signed zero"):
        module.ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount(
            reason_code="team_memory_edge_reconciliation_pass",
            count=d("-0.000000"),
            input_ratio=d("1.000000"),
        )


@pytest.mark.parametrize(
    "non_positive_pass_floor",
    (d("0.000000"), d("-0.000001")),
)
def test_config_rejects_non_positive_probability_edge_pass_floor(
    non_positive_pass_floor: Decimal,
) -> None:
    with pytest.raises(ValueError, match="probability_edge_pass_floor"):
        cfg(
            probability_edge_pass_floor=non_positive_pass_floor,
            probability_edge_watch_floor=d("0.000000"),
        )


def test_public_payload_uses_exact_nested_schemas_and_canonical_types() -> None:
    module = api()
    payload = module.research_strategy_team_memory_edge_reconciliation_report_payload(
        build_report(item()),
    )

    assert frozenset(payload) == frozenset(
        {
            "generated_at",
            "config_version",
            "config",
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_absolute_probability_edge",
            "average_cost_pressure_score",
            "average_reconciliation_score",
            "min_reconciliation_score",
            "status",
            "reason_codes",
            "reason_code_counts",
            "rows",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        },
    )
    assert frozenset(payload["config"]) == frozenset(
        {
            "config_version",
            "probability_edge_pass_floor",
            "probability_edge_watch_floor",
            "calibration_freshness_pass_floor",
            "calibration_freshness_watch_floor",
            "prior_outcome_learning_pass_floor",
            "prior_outcome_learning_watch_floor",
            "evidence_confidence_pass_floor",
            "evidence_confidence_watch_floor",
            "cost_pressure_pass_ceiling",
            "cost_pressure_watch_ceiling",
            "reconciliation_score_pass_floor",
            "reconciliation_score_watch_floor",
            "probability_edge_weight",
            "calibration_freshness_weight",
            "prior_outcome_learning_weight",
            "evidence_confidence_weight",
            "cost_pressure_weight",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        },
    )
    assert frozenset(payload["rows"][0]) == frozenset(
        {
            "analyst_row_label",
            "memory_signal_label",
            "manual_review_rank",
            "observed_at",
            "probability_edge_estimate",
            "absolute_probability_edge",
            "probability_edge_score",
            "calibration_freshness_score",
            "prior_outcome_learning_score",
            "evidence_confidence_score",
            "cost_pressure_score",
            "cost_quality_score",
            "reconciliation_score",
            "status",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        },
    )
    assert frozenset(payload["reason_code_counts"][0]) == frozenset(
        {
            "reason_code",
            "count",
            "input_ratio",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        },
    )

    forged_root = json.loads(json.dumps(payload))
    forged_root["extra"] = "public"
    resign_payload_tree(forged_root)
    with pytest.raises(ValueError, match="report payload.*exact schema"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            forged_root,
        )

    forged_row = json.loads(json.dumps(payload))
    forged_row["rows"][0]["extra"] = "public"
    resign_payload_tree(forged_row)
    with pytest.raises(ValueError, match="row payload.*exact schema"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            forged_row,
        )

    forged_reason_count = json.loads(json.dumps(payload))
    forged_reason_count["reason_code_counts"][0]["extra"] = "public"
    resign_payload_tree(forged_reason_count)
    with pytest.raises(ValueError, match="reason code count payload.*exact schema"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            forged_reason_count,
        )

    forged_config = json.loads(json.dumps(payload))
    forged_config["config"]["extra"] = "public"
    resign_payload_tree(forged_config)
    with pytest.raises(ValueError, match="config payload.*exact schema"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            forged_config,
        )

    noncanonical_count = json.loads(json.dumps(payload))
    noncanonical_count["input_count"] = "1"
    resign_payload_tree(noncanonical_count)
    with pytest.raises(ValueError, match="input_count.*canonical Decimal string"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            noncanonical_count,
        )

    noncanonical_timestamp = json.loads(json.dumps(payload))
    noncanonical_timestamp["generated_at"] = "2026-07-08T08:00:00-04:00"
    resign_payload_tree(noncanonical_timestamp)
    with pytest.raises(ValueError, match="generated_at.*canonical UTC"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            noncanonical_timestamp,
        )


def test_public_validator_rejects_resigned_derived_row_forgeries() -> None:
    module = api()
    payload = module.research_strategy_team_memory_edge_reconciliation_report_payload(
        build_report(item()),
    )

    forged_fields = (
        ("absolute_probability_edge", "0.123456"),
        ("probability_edge_score", "0.123456"),
        ("cost_quality_score", "0.123456"),
        ("reconciliation_score", "0.123456"),
    )
    for field_name, forged_value in forged_fields:
        forged = json.loads(json.dumps(payload))
        forged["rows"][0][field_name] = forged_value
        if field_name == "reconciliation_score":
            forged["average_reconciliation_score"] = forged_value
            forged["min_reconciliation_score"] = forged_value
        resign_payload_tree(forged)
        with pytest.raises(ValueError, match=field_name):
            module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
                forged,
            )

    forged_policy = json.loads(json.dumps(payload))
    forged_policy["rows"][0]["status"] = "watch"
    forged_policy["rows"][0]["reason_codes"] = ["probability_edge_gap"]
    forged_policy["pass_count"] = "0.000000"
    forged_policy["watch_count"] = "1.000000"
    forged_policy["status"] = "watch"
    forged_policy["reason_codes"] = [
        "team_memory_edge_reconciliation_report_watch",
        "probability_edge_review",
    ]
    forged_policy["reason_code_counts"][0]["reason_code"] = "probability_edge_gap"
    resign_payload_tree(forged_policy)
    with pytest.raises(ValueError, match="status|reason_codes"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            forged_policy,
        )


def test_public_validator_rejects_resigned_report_count_reason_and_score_forgeries() -> None:
    module = api()
    payload = module.research_strategy_team_memory_edge_reconciliation_report_payload(
        build_report(item()),
    )

    forged_values = (
        ("input_count", "2.000000", "input_count"),
        ("pass_count", "0.000000", "pass_count"),
        ("watch_count", "1.000000", "watch_count"),
        ("block_count", "1.000000", "block_count"),
        (
            "average_absolute_probability_edge",
            "0.123456",
            "average_absolute_probability_edge",
        ),
        ("average_cost_pressure_score", "0.123456", "average_cost_pressure_score"),
        ("average_reconciliation_score", "0.123456", "average_reconciliation_score"),
        ("min_reconciliation_score", "0.123456", "min_reconciliation_score"),
    )
    for field_name, forged_value, error_match in forged_values:
        forged = json.loads(json.dumps(payload))
        forged[field_name] = forged_value
        resign_payload_tree(forged)
        with pytest.raises(ValueError, match=error_match):
            module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
                forged,
            )

    forged_reason_counts = json.loads(json.dumps(payload))
    forged_reason_counts["reason_code_counts"][0]["count"] = "2.000000"
    resign_payload_tree(forged_reason_counts)
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            forged_reason_counts,
        )

    forged_reason_ratio = json.loads(json.dumps(payload))
    forged_reason_ratio["reason_code_counts"][0]["input_ratio"] = "0.500000"
    resign_payload_tree(forged_reason_ratio)
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            forged_reason_ratio,
        )

    forged_signed_zero = json.loads(json.dumps(payload))
    forged_signed_zero["watch_count"] = "-0.000000"
    resign_payload_tree(forged_signed_zero)
    with pytest.raises(ValueError, match="watch_count.*signed zero"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            forged_signed_zero,
        )


def test_custom_config_is_signed_into_payload_and_revalidated() -> None:
    module = api()
    strict = cfg(
        probability_edge_pass_floor=d("0.090000"),
        probability_edge_watch_floor=d("0.020000"),
        reconciliation_score_pass_floor=d("0.900000"),
        reconciliation_score_watch_floor=d("0.650000"),
    )
    payload = module.research_strategy_team_memory_edge_reconciliation_report_payload(
        build_report(item(), config=strict),
    )

    assert payload["config"]["probability_edge_pass_floor"] == "0.090000"
    assert payload["rows"][0]["status"] == "watch"
    assert module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
        payload,
    )

    forged_config = json.loads(json.dumps(payload))
    forged_config["config"]["probability_edge_pass_floor"] = "0.050000"
    resign_payload_tree(forged_config)
    with pytest.raises(ValueError, match="probability_edge_score|status|reason_codes"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            forged_config,
        )


def test_public_validator_rejects_fully_resigned_zero_probability_edge_pass_floor() -> None:
    module = api()
    custom = cfg(
        probability_edge_pass_floor=d("0.090000"),
        probability_edge_watch_floor=d("0.020000"),
    )
    payload = module.research_strategy_team_memory_edge_reconciliation_report_payload(
        build_report(item(), config=custom),
    )
    forged_config = json.loads(json.dumps(payload))
    forged_config["config"]["probability_edge_pass_floor"] = "0.000000"
    forged_config["config"]["probability_edge_watch_floor"] = "0.000000"
    resign_payload_tree(forged_config)

    with pytest.raises(ValueError, match="probability_edge_pass_floor"):
        module.validate_research_strategy_team_memory_edge_reconciliation_report_payload(
            forged_config,
        )


def test_public_payload_blocks_private_surface_terms_and_source_values() -> None:
    payload = api().research_strategy_team_memory_edge_reconciliation_report_payload(
        build_report(item()),
    )
    payload_text = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "live",
        "auth",
        "private-alpha-raw-value",
    ):
        assert forbidden not in payload_text

    with pytest.raises(ValueError, match="unsafe public value"):
        item(analyst_row_label=f"alpha_{hidden_word('63616e6469646174655f6964')}")

    with pytest.raises(ValueError, match="unsafe public value"):
        item(memory_signal_label=f"edge_{hidden_word('736f757263655f75726c')}")


@pytest.mark.parametrize(
    ("field_name", "private_reference"),
    (
        ("analyst_row_label", "private-alpha-raw-value"),
        ("analyst_row_label", "internal-record-001"),
        ("memory_signal_label", "memory-secret-reference"),
    ),
)
def test_private_reference_labels_are_rejected(
    field_name: str,
    private_reference: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public value"):
        item(**{field_name: private_reference})


def test_custom_config_validation_and_thresholds_are_enforced() -> None:
    module = api()

    strict = cfg(
        probability_edge_pass_floor=d("0.090000"),
        probability_edge_watch_floor=d("0.020000"),
        reconciliation_score_pass_floor=d("0.900000"),
        reconciliation_score_watch_floor=d("0.650000"),
    )
    report = build_report(item(), config=strict)

    assert report.status == "watch"
    assert report.rows[0].status == "watch"
    assert report.rows[0].reason_codes == (
        "probability_edge_gap",
        "reconciliation_score_gap",
    )

    with pytest.raises(ValueError, match="probability_edge_pass_floor"):
        cfg(probability_edge_pass_floor=d("0.010000"))

    with pytest.raises(ValueError, match="cost_pressure_watch_ceiling"):
        cfg(cost_pressure_pass_ceiling=d("0.700000"))

    with pytest.raises(ValueError, match="component weights must sum"):
        cfg(cost_pressure_weight=d("0.200000"))

    with pytest.raises(ValueError, match="probability_edge_weight must be a Decimal"):
        cfg(probability_edge_weight=0.25)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="config must be"):
        module.build_research_strategy_team_memory_edge_reconciliation_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_public_dataclasses_are_non_subclassable() -> None:
    module = api()

    for base in (
        module.ResearchStrategyTeamMemoryEdgeReconciliationConfig,
        module.ResearchStrategyTeamMemoryEdgeReconciliationInput,
        module.ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount,
        module.ResearchStrategyTeamMemoryEdgeReconciliationRow,
        module.ResearchStrategyTeamMemoryEdgeReconciliationReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Derived{base.__name__}", (base,), {})


def test_frozen_dataclasses_invariants_and_side_effect_free_source() -> None:
    module = api()
    sample_config = cfg()
    sample_input = item()
    report = build_report(item())
    reason_count = report.reason_code_counts[0]

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_TEAM_MEMORY_EDGE_RECONCILIATION_CONFIG_VERSION",
        "RESEARCH_STRATEGY_TEAM_MEMORY_EDGE_RECONCILIATION_STATUSES",
        "ResearchStrategyTeamMemoryEdgeReconciliationConfig",
        "ResearchStrategyTeamMemoryEdgeReconciliationInput",
        "ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount",
        "ResearchStrategyTeamMemoryEdgeReconciliationRow",
        "ResearchStrategyTeamMemoryEdgeReconciliationReport",
        "build_research_strategy_team_memory_edge_reconciliation_report",
        "research_strategy_team_memory_edge_reconciliation_report_payload",
        "validate_research_strategy_team_memory_edge_reconciliation_report_payload",
    )
    assert module.RESEARCH_STRATEGY_TEAM_MEMORY_EDGE_RECONCILIATION_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert all(
        is_dataclass(getattr(module, name))
        for name in module.__all__
        if name.startswith("Research")
    )

    expected_fields = {
        module.ResearchStrategyTeamMemoryEdgeReconciliationConfig: {
            "config_version",
            "probability_edge_pass_floor",
            "probability_edge_watch_floor",
            "calibration_freshness_pass_floor",
            "calibration_freshness_watch_floor",
            "prior_outcome_learning_pass_floor",
            "prior_outcome_learning_watch_floor",
            "evidence_confidence_pass_floor",
            "evidence_confidence_watch_floor",
            "cost_pressure_pass_ceiling",
            "cost_pressure_watch_ceiling",
            "reconciliation_score_pass_floor",
            "reconciliation_score_watch_floor",
            "probability_edge_weight",
            "calibration_freshness_weight",
            "prior_outcome_learning_weight",
            "evidence_confidence_weight",
            "cost_pressure_weight",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        },
        module.ResearchStrategyTeamMemoryEdgeReconciliationInput: {
            "analyst_row_label",
            "memory_signal_label",
            "observed_at",
            "probability_edge_estimate",
            "calibration_freshness_score",
            "prior_outcome_learning_score",
            "evidence_confidence_score",
            "cost_pressure_score",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        },
        module.ResearchStrategyTeamMemoryEdgeReconciliationReasonCodeCount: {
            "reason_code",
            "count",
            "input_ratio",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        },
        module.ResearchStrategyTeamMemoryEdgeReconciliationRow: {
            "analyst_row_label",
            "memory_signal_label",
            "manual_review_rank",
            "observed_at",
            "probability_edge_estimate",
            "absolute_probability_edge",
            "probability_edge_score",
            "calibration_freshness_score",
            "prior_outcome_learning_score",
            "evidence_confidence_score",
            "cost_pressure_score",
            "cost_quality_score",
            "reconciliation_score",
            "status",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        },
        module.ResearchStrategyTeamMemoryEdgeReconciliationReport: {
            "generated_at",
            "config_version",
            "config",
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_absolute_probability_edge",
            "average_cost_pressure_score",
            "average_reconciliation_score",
            "min_reconciliation_score",
            "status",
            "reason_codes",
            "reason_code_counts",
            "rows",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        },
    }
    for value in (sample_config, sample_input, reason_count, report.rows[0], report):
        assert {field.name for field in fields(value)} == expected_fields[type(value)]
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    with pytest.raises(ValueError, match="derived_validation_digest payload mismatch"):
        replace(sample_config, probability_edge_pass_floor=d("0.060000"))

    with pytest.raises(ValueError, match="derived_validation_digest payload mismatch"):
        replace(sample_input, evidence_confidence_score=d("0.870000"))

    with pytest.raises(ValueError, match="derived_validation_digest payload mismatch"):
        replace(report.rows[0], reconciliation_score=d("0.123456"))

    with pytest.raises(ValueError, match="status must match rows"):
        replace(report, status="block")

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(item(observed_at=GENERATED_AT + timedelta(seconds=1)))

    source_text = MODULE_PATH.read_text(encoding="utf-8")
    source = source_text.lower()
    for forbidden in (
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        "read_text",
        "write_text",
        "wallet",
        "order",
        "trade",
        "sizing",
        "auth",
        "token",
        "dsn",
        "recommendation",
    ):
        assert forbidden not in source

    tree = ast.parse(source_text)
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = {
        "api",
        "auth",
        "broker",
        "client",
        "database",
        "db",
        "http",
        "network",
        "order",
        "persist",
        "request",
        "socket",
        "sql",
        "store",
        "wallet",
        "web3",
    }
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "insert",
        "open",
        "order",
        "persist",
        "read_bytes",
        "read_text",
        "recommendation",
        "rollback",
        "sell",
        "send",
        "sizing",
        "trade",
        "write",
        "write_bytes",
        "write_text",
    }
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
