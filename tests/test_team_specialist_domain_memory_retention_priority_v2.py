from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_domain_memory_retention_priority_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "team_id": "macro-team",
        "specialist_id": "rates-specialist",
        "domain_id": "fed-policy",
        "domain_age_days": d("45"),
        "forecast_error_bps": d("250.000000"),
        "source_decay_ratio": d("0.400000"),
        "event_recurrence_count_30d": d("3"),
        "open_market_exposure_usd": d("6000.000000"),
        "exposure_reference_usd": d("10000.000000"),
        "minimum_actionable_score": d("250.000000"),
        "reason_codes": ("manual_refresh_candidate",),
    }
    values.update(overrides)
    return module.TeamSpecialistDomainMemoryRetentionPriorityV2Input(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_team_specialist_domain_memory_retention_priority_v2(
        score_input() if subject is None else subject,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_priority_score_combines_refresh_pressure_inputs_deterministically() -> None:
    module = api()

    result = score()

    assert result == module.TeamSpecialistDomainMemoryRetentionPriorityV2Result(
        team_id="macro-team",
        specialist_id="rates-specialist",
        domain_id="fed-policy",
        domain_age_days=d("45"),
        forecast_error_bps=d("250.000000"),
        source_decay_ratio=d("0.400000"),
        event_recurrence_count_30d=d("3"),
        open_market_exposure_usd=d("6000.000000"),
        exposure_reference_usd=d("10000.000000"),
        domain_age_priority_bps=d("75.000000"),
        forecast_error_priority_bps=d("50.000000"),
        source_decay_priority_bps=d("40.000000"),
        event_recurrence_priority_bps=d("45.000000"),
        open_market_exposure_priority_bps=d("75.000000"),
        paper_score_bps=d("285.000000"),
        minimum_actionable_score=d("250.000000"),
        score_status="candidate",
        score_decision="paper_candidate",
        reason_codes=(
            "manual_refresh_candidate",
            "team_specialist_domain_memory_retention_priority_v2",
            "score_candidate",
            "domain_age_pressure_present",
            "forecast_error_present",
            "source_decay_present",
            "event_recurrence_present",
            "open_market_exposure_present",
            "minimum_actionable_score_met",
        ),
        derived_validation_digest=(
            "330dea50d89d43cdc55a62802545c318bab1a762c6ce092cdc63040b19191bd8"
        ),
    )
    assert type(result.paper_score_bps) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_priority_statuses_cover_watch_and_blocked_cases() -> None:
    watch = score(
        score_input(
            domain_age_days=d("10"),
            forecast_error_bps=d("25.000000"),
            source_decay_ratio=d("0.100000"),
            event_recurrence_count_30d=d("1"),
            open_market_exposure_usd=d("500.000000"),
            minimum_actionable_score=d("100.000000"),
            reason_codes=(),
        ),
    )

    assert watch.domain_age_priority_bps == d("16.666667")
    assert watch.forecast_error_priority_bps == d("5.000000")
    assert watch.source_decay_priority_bps == d("10.000000")
    assert watch.event_recurrence_priority_bps == d("15.000000")
    assert watch.open_market_exposure_priority_bps == d("6.250000")
    assert watch.paper_score_bps == d("52.916667")
    assert watch.score_status == "watch"
    assert watch.score_decision == "manual_review"
    assert "score_positive_below_minimum" in watch.reason_codes

    blocked = score(
        score_input(
            domain_age_days=d("0"),
            forecast_error_bps=d("0.000000"),
            source_decay_ratio=d("0.000000"),
            event_recurrence_count_30d=d("0"),
            open_market_exposure_usd=d("0.000000"),
            minimum_actionable_score=d("1.000000"),
            reason_codes=(),
        ),
    )

    assert blocked.paper_score_bps == d("0.000000")
    assert blocked.score_status == "blocked"
    assert blocked.score_decision == "reject"
    assert blocked.reason_codes == (
        "team_specialist_domain_memory_retention_priority_v2",
        "score_blocked",
        "score_below_zero",
    )


def test_caps_pressure_components_at_their_reference_levels() -> None:
    result = score(
        score_input(
            domain_age_days=d("120"),
            forecast_error_bps=d("900.000000"),
            source_decay_ratio=d("1.000000"),
            event_recurrence_count_30d=d("12"),
            open_market_exposure_usd=d("25000.000000"),
            exposure_reference_usd=d("10000.000000"),
            reason_codes=(),
        ),
    )

    assert result.domain_age_priority_bps == d("100.000000")
    assert result.forecast_error_priority_bps == d("100.000000")
    assert result.source_decay_priority_bps == d("100.000000")
    assert result.event_recurrence_priority_bps == d("75.000000")
    assert result.open_market_exposure_priority_bps == d("125.000000")
    assert result.paper_score_bps == d("500.000000")


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    result = score()
    payload = result.payload

    assert payload == module.team_specialist_domain_memory_retention_priority_v2_payload(
        result,
    )
    assert payload["paper_score_bps"] == "285.000000"
    assert payload["source_decay_ratio"] == "0.400000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_domain_memory_retention_priority_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.TeamSpecialistDomainMemoryRetentionPriorityV2Input.__dataclass_params__.frozen
    assert module.TeamSpecialistDomainMemoryRetentionPriorityV2Result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.team_id = "other-team"  # type: ignore[misc]
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

    with pytest.raises(ValueError, match="domain_age_days must be a Decimal"):
        score_input(domain_age_days=45)
    with pytest.raises(ValueError, match="team_id must be a canonical"):
        score_input(team_id=" macro-team")
    with pytest.raises(ValueError, match="source_decay_ratio must not exceed 1.000000"):
        score_input(source_decay_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="event_recurrence_count_30d must be integral"):
        score_input(event_recurrence_count_30d=d("3.500000"))
    with pytest.raises(ValueError, match="exposure_reference_usd must be positive"):
        score_input(exposure_reference_usd=d("0.000000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["manual_refresh_candidate"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())

    rebuilt = module.TeamSpecialistDomainMemoryRetentionPriorityV2Result(
        **public_field_values(result),
    )
    assert rebuilt == result


def test_rejects_digest_tampering_and_unsafe_public_payload_strings() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.TeamSpecialistDomainMemoryRetentionPriorityV2Result(
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
            module.reject_team_specialist_domain_memory_retention_priority_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_team_specialist_domain_memory_retention_priority_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/team_specialist_domain_memory_retention_priority_v2.py",
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
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "wallet",
        " auth",
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
        "TeamSpecialistDomainMemoryRetentionPriorityV2Input",
        "TeamSpecialistDomainMemoryRetentionPriorityV2Result",
        "estimate_team_specialist_domain_memory_retention_priority_v2",
        "team_specialist_domain_memory_retention_priority_v2_payload",
        "reject_team_specialist_domain_memory_retention_priority_v2_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "team_specialist_domain_memory_retention_priority_v2" not in getattr(
        root,
        "__all__",
        (),
    )
