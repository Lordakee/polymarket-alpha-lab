from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_candidate_source_freshness_margin_score_v2"


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "candidate_id": "candidate-source-freshness-margin-v2",
        "source_count": d("4"),
        "fresh_source_count": d("3"),
        "stale_source_count": d("1"),
        "official_source_count": d("2"),
        "maximum_source_age_seconds": d("900"),
        "freshness_target_seconds": d("600"),
        "base_margin_bps": d("240.000000"),
        "minimum_actionable_score": d("150.000000"),
        "reason_codes": ("research_sources_present",),
    }
    values.update(overrides)
    return module.StrategyCandidateSourceFreshnessMarginScoreV2Input(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_strategy_candidate_source_freshness_margin_score_v2(
        score_input() if subject is None else subject,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_source_freshness_margin_score_applies_stale_penalty_and_official_boost() -> None:
    result = score()

    assert result.source_freshness_margin_ratio == d("0.750000")
    assert result.raw_source_margin_bps == d("180.000000")
    assert result.stale_source_penalty_bps == d("35.000000")
    assert result.official_source_boost_bps == d("40.000000")
    assert result.paper_score_bps == d("185.000000")
    assert result.score_status == "candidate"
    assert result.score_decision == "paper_candidate"
    assert result.reason_codes == (
        "research_sources_present",
        "strategy_candidate_source_freshness_margin_score_v2",
        "score_candidate",
        "fresh_source_majority",
        "stale_source_penalty_applied",
        "official_source_boost_applied",
        "minimum_actionable_score_met",
    )
    assert type(result.paper_score_bps) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64


def test_stale_source_penalties_can_block_old_low_freshness_sources() -> None:
    result = score(
        score_input(
            source_count=d("4"),
            fresh_source_count=d("1"),
            stale_source_count=d("3"),
            official_source_count=d("0"),
            maximum_source_age_seconds=d("2400"),
            freshness_target_seconds=d("600"),
            base_margin_bps=d("200.000000"),
            minimum_actionable_score=d("50.000000"),
            reason_codes=(),
        ),
    )

    assert result.source_freshness_margin_ratio == d("0.250000")
    assert result.raw_source_margin_bps == d("50.000000")
    assert result.stale_source_penalty_bps == d("135.000000")
    assert result.official_source_boost_bps == d("0.000000")
    assert result.paper_score_bps == d("-85.000000")
    assert result.score_status == "blocked"
    assert result.score_decision == "reject"
    assert "score_below_zero" in result.reason_codes


def test_official_source_boost_can_lift_watch_score_to_candidate() -> None:
    without_official = score(
        score_input(
            source_count=d("4"),
            fresh_source_count=d("2"),
            stale_source_count=d("2"),
            official_source_count=d("0"),
            maximum_source_age_seconds=d("600"),
            freshness_target_seconds=d("600"),
            base_margin_bps=d("220.000000"),
            minimum_actionable_score=d("100.000000"),
            reason_codes=(),
        ),
    )
    with_official = score(
        score_input(
            source_count=d("4"),
            fresh_source_count=d("2"),
            stale_source_count=d("2"),
            official_source_count=d("3"),
            maximum_source_age_seconds=d("600"),
            freshness_target_seconds=d("600"),
            base_margin_bps=d("220.000000"),
            minimum_actionable_score=d("100.000000"),
            reason_codes=(),
        ),
    )

    assert without_official.paper_score_bps == d("60.000000")
    assert without_official.score_status == "watch"
    assert with_official.official_source_boost_bps == d("60.000000")
    assert with_official.paper_score_bps == d("120.000000")
    assert with_official.score_status == "candidate"


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    result = score()
    payload = result.payload

    assert payload == module.strategy_candidate_source_freshness_margin_score_v2_payload(
        result,
    )
    assert payload["paper_score_bps"] == "185.000000"
    assert payload["source_count"] == "4"
    assert payload["source_freshness_margin_ratio"] == "0.750000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_source_freshness_margin_score_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.StrategyCandidateSourceFreshnessMarginScoreV2Input.__dataclass_params__.frozen
    assert module.StrategyCandidateSourceFreshnessMarginScoreV2Result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.candidate_id = "other-candidate"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.score_status = "candidate"  # type: ignore[misc]

    for instance in (subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        score_input(source_count=4)
    with pytest.raises(ValueError, match="candidate_id must be a canonical"):
        score_input(candidate_id=" candidate-source-freshness-margin-v2")
    with pytest.raises(ValueError, match="source counts must classify every source"):
        score_input(fresh_source_count=d("2"), stale_source_count=d("1"))
    with pytest.raises(ValueError, match="official_source_count must not exceed source_count"):
        score_input(official_source_count=d("5"))
    with pytest.raises(ValueError, match="freshness_target_seconds must be positive"):
        score_input(freshness_target_seconds=d("0"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["research_sources_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())

    rebuilt = module.StrategyCandidateSourceFreshnessMarginScoreV2Result(
        **public_field_values(result),
    )
    assert rebuilt == result


def test_rejects_digest_tampering_and_unsafe_public_payload_keys_and_values() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.StrategyCandidateSourceFreshnessMarginScoreV2Result(
            **{
                **public_field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )

    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            score_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_source_freshness_margin_score_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_source_freshness_margin_score_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/strategy_candidate_source_freshness_margin_score_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    unsafe_surface_terms = (
        "live",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "wallet",
        " auth",
        "order",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_surface_terms:
        assert term not in lowered

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
    assert module.__all__ == (
        "SCORE_STATUSES",
        "SCORE_DECISIONS",
        "StrategyCandidateSourceFreshnessMarginScoreV2Input",
        "StrategyCandidateSourceFreshnessMarginScoreV2Result",
        "estimate_strategy_candidate_source_freshness_margin_score_v2",
        "strategy_candidate_source_freshness_margin_score_v2_payload",
        "reject_strategy_candidate_source_freshness_margin_score_v2_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "strategy_candidate_source_freshness_margin_score_v2" not in getattr(
        root,
        "__all__",
        (),
    )
