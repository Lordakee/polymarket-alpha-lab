from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab."
        "strategy_recommendation_source_contradiction_stoplight_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    values: dict[str, object] = {
        "red_contradiction_count": d("2.000000"),
        "red_contradiction_severity_score": d("0.750000"),
        "watch_contradiction_severity_score": d("0.250000"),
        "min_independent_confirmations": d("2.000000"),
        "max_source_age_seconds": d("3600.000000"),
        "watch_resolution_rule_ambiguity_score": d("0.250000"),
        "red_resolution_rule_ambiguity_score": d("0.750000"),
        "min_green_cost_adjusted_edge_margin": d("0.030000"),
        "min_watch_cost_adjusted_edge_margin": d("0.000000"),
    }
    values.update(overrides)
    return api().StrategyRecommendationSourceContradictionStoplightV2Config(**values)


def source(
    source_id: str,
    *,
    source_role: str = "independent",
    supports_recommendation: bool = True,
    age_seconds: int = 300,
    source_family: str | None = None,
    independence_group: str | None = None,
    contradiction_severity_score: Decimal = d("0.000000"),
    resolution_rule_ambiguity_score: Decimal = d("0.050000"),
    observed_at: datetime | None = None,
) -> Any:
    return api().StrategyRecommendationSourceContradictionEvidence(
        source_id=source_id,
        source_family=source_family or f"{source_id}-family",
        source_role=source_role,
        independence_group=independence_group or source_id,
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=age_seconds),
        supports_recommendation=supports_recommendation,
        contradiction_severity_score=contradiction_severity_score,
        resolution_rule_ambiguity_score=resolution_rule_ambiguity_score,
    )


def candidate(
    recommendation_id: str,
    *,
    market_slug: str | None = None,
    cost_adjusted_edge_margin: Decimal = d("0.060000"),
    sources: tuple[Any, ...] | None = None,
) -> Any:
    return api().StrategyRecommendationSourceContradictionCandidate(
        recommendation_id=recommendation_id,
        market_slug=market_slug or f"{recommendation_id}-market",
        side="yes",
        cost_adjusted_edge_margin=cost_adjusted_edge_margin,
        sources=(
            source("independent-a", independence_group="group-a"),
            source("independent-b", independence_group="group-b"),
        )
        if sources is None
        else sources,
    )


def report(rows: tuple[Any, ...], **overrides: object) -> Any:
    return api().build_strategy_recommendation_source_contradiction_stoplight_v2(
        rows,
        config=config(**overrides),
        generated_at=GENERATED_AT,
    )


def test_builds_red_watch_green_stoplights_from_source_contradiction_inputs() -> None:
    built = report(
        (
            candidate(
                "green-recommendation",
                market_slug="z-green-market",
                sources=(
                    source("green-independent-a", independence_group="green-a"),
                    source("green-independent-b", independence_group="green-b"),
                    source("green-official", source_role="official"),
                ),
            ),
            candidate(
                "red-recommendation",
                market_slug="a-red-market",
                cost_adjusted_edge_margin=d("0.050000"),
                sources=(
                    source(
                        "official-conflict",
                        source_role="official",
                        supports_recommendation=False,
                        contradiction_severity_score=d("0.900000"),
                        resolution_rule_ambiguity_score=d("0.800000"),
                        independence_group="official",
                    ),
                    source("red-independent-a", independence_group="red-a"),
                    source("red-independent-b", independence_group="red-b"),
                ),
            ),
            candidate(
                "watch-recommendation",
                market_slug="m-watch-market",
                cost_adjusted_edge_margin=d("0.015000"),
                sources=(
                    source(
                        "watch-independent-a",
                        age_seconds=7200,
                        independence_group="watch-a",
                        resolution_rule_ambiguity_score=d("0.400000"),
                    ),
                    source(
                        "watch-supporting",
                        source_role="supporting",
                        age_seconds=1800,
                        resolution_rule_ambiguity_score=d("0.300000"),
                    ),
                ),
            ),
        ),
    )

    assert built.stoplight_status == "red"
    assert built.recommendation_count == d("3.000000")
    assert built.green_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.red_count == d("1.000000")
    assert built.source_count == d("8.000000")
    assert built.contradiction_count == d("1.000000")
    assert built.official_source_conflict_count == d("1.000000")
    assert built.independent_confirmation_count == d("5.000000")
    assert built.stale_recommendation_count == d("1.000000")
    assert built.ambiguous_resolution_rule_count == d("2.000000")
    assert built.max_contradiction_severity_score == d("0.900000")
    assert built.min_cost_adjusted_edge_margin == d("0.015000")
    assert built.reason_codes == (
        "source_contradiction_present",
        "source_contradiction_severity_red",
        "official_source_conflict",
        "independent_confirmation_gap",
        "source_recency_stale",
        "resolution_rule_ambiguity_red",
        "resolution_rule_ambiguity_watch",
        "cost_adjusted_edge_margin_watch",
    )

    assert tuple(row.recommendation_id for row in built.rows) == (
        "red-recommendation",
        "watch-recommendation",
        "green-recommendation",
    )
    red, watched, green = built.rows
    assert red.stoplight_status == "red"
    assert red.contradiction_count == d("1.000000")
    assert red.official_source_conflict_count == d("1.000000")
    assert red.independent_confirmation_count == d("2.000000")
    assert red.max_contradiction_severity_score == d("0.900000")
    assert red.max_resolution_rule_ambiguity_score == d("0.800000")
    assert red.reason_codes == (
        "source_contradiction_present",
        "source_contradiction_severity_red",
        "official_source_conflict",
        "resolution_rule_ambiguity_red",
    )

    assert watched.stoplight_status == "watch"
    assert watched.independent_confirmation_count == d("1.000000")
    assert watched.newest_source_age_seconds == d("1800.000000")
    assert watched.max_source_age_seconds == d("7200.000000")
    assert watched.cost_adjusted_edge_margin == d("0.015000")
    assert watched.reason_codes == (
        "independent_confirmation_gap",
        "source_recency_stale",
        "resolution_rule_ambiguity_watch",
        "cost_adjusted_edge_margin_watch",
    )

    assert green.stoplight_status == "green"
    assert green.reason_codes == ("source_contradiction_stoplight_green",)
    assert len(built.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in built.derived_validation_digest)


def test_payload_uses_decimal_strings_flags_digest_and_rejects_tampering() -> None:
    built = report((candidate("payload-recommendation"),))

    payload = api().strategy_recommendation_source_contradiction_stoplight_v2_payload(built)

    assert payload == built.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["recommendation_count"] == "1.000000"
    assert payload["rows"][0]["cost_adjusted_edge_margin"] == "0.060000"
    assert payload["rows"][0]["newest_source_age_seconds"] == "300.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == built.derived_validation_digest
    json.dumps(payload, sort_keys=True, allow_nan=False)
    assert_no_numeric_scalars(payload)

    tampered = dict(payload)
    tampered["green_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        api().strategy_recommendation_source_contradiction_stoplight_v2_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        api().strategy_recommendation_source_contradiction_stoplight_v2_payload(
            replace(built, derived_validation_digest="0" * 64),
        )


def test_empty_input_is_red_report_only_and_digest_validated() -> None:
    empty = report(())

    assert empty.stoplight_status == "red"
    assert empty.reason_codes == ("no_recommendations",)
    assert empty.recommendation_count == d("0.000000")
    assert empty.green_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.red_count == d("0.000000")
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    payload = api().strategy_recommendation_source_contradiction_stoplight_v2_payload(empty)
    assert payload["stoplight_status"] == "red"
    assert payload["reason_codes"] == ["no_recommendations"]


def test_validation_rejects_non_decimal_subclasses_bad_times_duplicates_and_false_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="red_contradiction_count"):
        config(red_contradiction_count=2)
    with pytest.raises(ValueError, match="cost_adjusted_edge_margin"):
        candidate("bad-edge", cost_adjusted_edge_margin=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="observed_at"):
        source(
            "datetime-subclass",
            observed_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source observed_at"):
        report((candidate("future", sources=(source("future", age_seconds=-1),)),))
    with pytest.raises(ValueError, match="recommendation_id"):
        report((candidate("duplicate"), candidate("duplicate")))
    with pytest.raises(ValueError, match="source_id"):
        report(
            (
                candidate(
                    "duplicate-source",
                    sources=(source("same"), source("same", independence_group="other")),
                ),
            ),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_recommendation_source_contradiction_stoplight_v2(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        report((replace(candidate("bad-flag"), paper_only=False),))
    with pytest.raises(ValueError, match="readonly"):
        report(
            (
                candidate(
                    "bad-source-flag",
                    sources=(replace(source("bad-source"), readonly=False),),
                ),
            ),
        )


def test_public_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    public_dataclasses = (
        module.StrategyRecommendationSourceContradictionStoplightV2Config,
        module.StrategyRecommendationSourceContradictionEvidence,
        module.StrategyRecommendationSourceContradictionCandidate,
        module.StrategyRecommendationSourceContradictionStoplightRow,
        module.StrategyRecommendationSourceContradictionStoplightReport,
    )
    for cls in public_dataclasses:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    built = report((candidate("frozen"),))
    with pytest.raises(FrozenInstanceError):
        built.stoplight_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].cost_adjusted_edge_margin = d("0.010000")  # type: ignore[misc]

    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in built.rows)
    assert_public_numbers_are_decimal(built)


def test_module_is_pure_phase1_report_only_with_no_external_runtime_surface() -> None:
    module = api()
    source_text = inspect.getsource(module)
    tree = ast.parse(source_text)

    forbidden_import_roots = {
        "builtins",
        "http",
        "io",
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
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "eval", "exec", "compile"}

    assert not any(
        hasattr(module, name)
        for name in (
            "client",
            "connect",
            "execute",
            "request",
            "session",
            "submit",
        )
    )
    assert module.__all__ == (
        "DEFAULT_STRATEGY_RECOMMENDATION_SOURCE_CONTRADICTION_STOPLIGHT_V2_CONFIG_VERSION",
        "StrategyRecommendationSourceContradictionStoplightV2Config",
        "StrategyRecommendationSourceContradictionEvidence",
        "StrategyRecommendationSourceContradictionCandidate",
        "StrategyRecommendationSourceContradictionStoplightRow",
        "StrategyRecommendationSourceContradictionStoplightReport",
        "build_strategy_recommendation_source_contradiction_stoplight_v2",
        "strategy_recommendation_source_contradiction_stoplight_v2_payload",
    )


def assert_no_numeric_scalars(value: object) -> None:
    if type(value) is bool:
        return
    if type(value) is int or isinstance(value, (float, Decimal)):
        raise AssertionError(f"payload contains a numeric scalar: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_numeric_scalars(child)
    if isinstance(value, list):
        for child in value:
            assert_no_numeric_scalars(child)


def assert_public_numbers_are_decimal(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            assert_public_numbers_are_decimal(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            assert_public_numbers_are_decimal(getattr(value, field.name))
