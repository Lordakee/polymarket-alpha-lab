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


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_domain_memory_reuse_rank_v2.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_domain_memory_reuse_rank_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def context(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "context_id": "macro_rates_cpi_context",
        "domain_id": "macro",
        "category_id": "rates",
        "event_archetype": "cpi_surprise",
        "required_source_families": (
            "official_release",
            "market_price",
            "expert_analysis",
        ),
    }
    values.update(overrides)
    return module.TeamSpecialistDomainMemoryReuseContextV2(**values)


def memory_item(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "team_id": "team_alpha",
        "specialist_id": "macro_calibration_lead",
        "memory_id": "macro_cpi_memory",
        "domain_ids": ("macro",),
        "category_ids": ("rates",),
        "event_archetypes": ("cpi_surprise", "fed_meeting"),
        "source_family_ids": (
            "official_release",
            "market_price",
            "expert_analysis",
        ),
        "outcome_calibration_score": d("0.920000"),
        "memory_age_days": d("5.000000"),
        "contradiction_count": d("0"),
        "resolved_postmortem_usefulness_score": d("0.900000"),
    }
    values.update(overrides)
    return module.TeamSpecialistDomainMemoryReuseItemV2(**values)


def build_report(*items: object, **overrides: object) -> Any:
    module = api()
    reuse_context = overrides.pop("reuse_context", context())
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            memory_item(),
            memory_item(
                team_id="team_beta",
                specialist_id="macro_source_lead",
                memory_id="rates_release_recheck_memory",
                category_ids=("inflation", "rates"),
                source_family_ids=("official_release", "market_price"),
                outcome_calibration_score=d("0.700000"),
                memory_age_days=d("30.000000"),
                contradiction_count=d("1"),
                resolved_postmortem_usefulness_score=d("0.650000"),
            ),
            memory_item(
                team_id="team_gamma",
                specialist_id="sports_rotation_lead",
                memory_id="basketball_injury_memory",
                domain_ids=("sports",),
                category_ids=("basketball",),
                event_archetypes=("injury_status_change",),
                source_family_ids=("official_release",),
                outcome_calibration_score=d("0.400000"),
                memory_age_days=d("120.000000"),
                contradiction_count=d("5"),
                resolved_postmortem_usefulness_score=d("0.200000"),
            ),
        )
    return module.build_team_specialist_domain_memory_reuse_rank_v2_report(
        reuse_context=reuse_context,
        memory_items=items,
        generated_at=generated_at,
        config=config,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_builds_ranked_domain_category_reuse_report_and_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.reuse_status == "reuse"
    assert report.context_id == "macro_rates_cpi_context"
    assert report.domain_id == "macro"
    assert report.category_id == "rates"
    assert report.memory_count == d("3")
    assert report.reuse_count == d("1")
    assert report.watch_count == d("1")
    assert report.skip_count == d("1")
    assert report.average_reuse_score == d("0.623241")
    assert report.top_reuse_score == d("0.953889")
    assert report.reason_codes == (
        "team_specialist_domain_memory_reuse_rank_reuse_rows",
        "team_specialist_domain_memory_reuse_rank_watch_rows",
        "team_specialist_domain_memory_reuse_rank_skip_rows",
    )

    rows = report.rows
    assert tuple(row.memory_id for row in rows) == (
        "macro_cpi_memory",
        "rates_release_recheck_memory",
        "basketball_injury_memory",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.reuse_status for row in rows) == ("reuse", "watch", "skip")
    assert tuple(row.reuse_score for row in rows) == (
        d("0.953889"),
        d("0.735833"),
        d("0.180000"),
    )

    top = rows[0]
    assert top.domain_match_score == d("1.000000")
    assert top.category_match_score == d("1.000000")
    assert top.outcome_calibration_score == d("0.920000")
    assert top.recency_score == d("0.944444")
    assert top.source_overlap_score == d("1.000000")
    assert top.event_archetype_match_score == d("1.000000")
    assert top.contradiction_history_score == d("1.000000")
    assert top.resolved_postmortem_usefulness_score == d("0.900000")
    assert top.reason_codes == (
        "team_specialist_domain_memory_reuse_domain_match",
        "team_specialist_domain_memory_reuse_category_match",
        "team_specialist_domain_memory_reuse_outcome_calibration_strong",
        "team_specialist_domain_memory_reuse_recent",
        "team_specialist_domain_memory_reuse_source_overlap_complete",
        "team_specialist_domain_memory_reuse_event_archetype_match",
        "team_specialist_domain_memory_reuse_contradiction_history_clean",
        "team_specialist_domain_memory_reuse_resolved_postmortem_useful",
        "team_specialist_domain_memory_reuse_reuse",
    )

    skipped = rows[2]
    assert skipped.domain_match_score == d("0.000000")
    assert skipped.category_match_score == d("0.000000")
    assert skipped.recency_score == d("0.000000")
    assert skipped.event_archetype_match_score == d("0.000000")
    assert skipped.contradiction_history_score == d("0.000000")
    assert skipped.reason_codes == (
        "team_specialist_domain_memory_reuse_domain_gap",
        "team_specialist_domain_memory_reuse_category_gap",
        "team_specialist_domain_memory_reuse_outcome_calibration_weak",
        "team_specialist_domain_memory_reuse_stale",
        "team_specialist_domain_memory_reuse_source_overlap_gap",
        "team_specialist_domain_memory_reuse_event_archetype_gap",
        "team_specialist_domain_memory_reuse_contradiction_history_present",
        "team_specialist_domain_memory_reuse_resolved_postmortem_gap",
        "team_specialist_domain_memory_reuse_skip",
    )

    payload = report.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["memory_count"] == "3"
    assert payload["average_reuse_score"] == "0.623241"
    assert payload["rows"][0]["reuse_score"] == "0.953889"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_rank_is_deterministic_skip_report() -> None:
    report = build_report(use_default_items=False)

    assert report.reuse_status == "skip"
    assert report.memory_count == d("0")
    assert report.reuse_count == d("0")
    assert report.watch_count == d("0")
    assert report.skip_count == d("0")
    assert report.average_reuse_score == d("0.000000")
    assert report.top_reuse_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "team_specialist_domain_memory_reuse_rank_empty",
    )
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_input_order_does_not_change_rank_order_payload_or_digest() -> None:
    first = memory_item()
    second = memory_item(
        team_id="team_beta",
        specialist_id="macro_source_lead",
        memory_id="rates_release_recheck_memory",
        source_family_ids=("official_release", "market_price"),
        outcome_calibration_score=d("0.700000"),
        memory_age_days=d("30.000000"),
        contradiction_count=d("1"),
        resolved_postmortem_usefulness_score=d("0.650000"),
    )

    left = build_report(first, second)
    right = build_report(second, first)

    assert tuple((row.memory_id, row.rank) for row in left.rows) == (
        ("macro_cpi_memory", d("1")),
        ("rates_release_recheck_memory", d("2")),
    )
    assert left.payload == right.payload
    assert left.derived_validation_digest == right.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistDomainMemoryReuseRankV2Config()
    reuse_context = context()
    sample = memory_item()
    report = build_report(sample, reuse_context=reuse_context)
    row = report.rows[0]

    decimal_fields = {
        "outcome_calibration_weight",
        "recency_weight",
        "source_overlap_weight",
        "event_archetype_match_weight",
        "contradiction_history_weight",
        "resolved_postmortem_usefulness_weight",
        "max_memory_age_days",
        "max_contradiction_count",
        "reuse_score_floor",
        "watch_score_floor",
        "outcome_calibration_score",
        "memory_age_days",
        "contradiction_count",
        "resolved_postmortem_usefulness_score",
        "rank",
        "domain_match_score",
        "category_match_score",
        "recency_score",
        "source_overlap_score",
        "event_archetype_match_score",
        "contradiction_history_score",
        "required_source_family_count",
        "matched_source_family_count",
        "reuse_score",
        "memory_count",
        "reuse_count",
        "watch_count",
        "skip_count",
        "average_reuse_score",
        "top_reuse_score",
    }

    for item in (config, reuse_context, sample, row, report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in decimal_fields:
                assert type(getattr(item, field.name)) is Decimal
            assert type(getattr(item, field.name)) is not float
            assert type(getattr(item, field.name)) is not int

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.TeamSpecialistDomainMemoryReuseRankV2Config):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeContext(module.TeamSpecialistDomainMemoryReuseContextV2):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeItem(module.TeamSpecialistDomainMemoryReuseItemV2):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.TeamSpecialistDomainMemoryReuseRankV2Row):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.TeamSpecialistDomainMemoryReuseRankV2Report):
            pass


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "outcome_calibration_score",
            _DecimalSubclass("0.900000"),
            "outcome_calibration_score must be exactly Decimal",
        ),
        (
            "resolved_postmortem_usefulness_score",
            d("1.000001"),
            "resolved_postmortem_usefulness_score must be <= 1.000000",
        ),
        (
            "memory_age_days",
            d("-1.000000"),
            "memory_age_days must be >= 0.000000",
        ),
        (
            "memory_age_days",
            d("5.0000004"),
            "memory_age_days must use six decimal places or fewer",
        ),
        (
            "contradiction_count",
            d("1.5"),
            "contradiction_count must be an integral Decimal",
        ),
        (
            "contradiction_count",
            Decimal("NaN"),
            "contradiction_count must be finite",
        ),
    ),
)
def test_memory_item_validation_rejects_bad_decimal_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        memory_item(**{field_name: bad_value})


def test_config_build_and_payload_validation_reject_bad_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="reuse rank weights must sum to 1.000000"):
        module.TeamSpecialistDomainMemoryReuseRankV2Config(
            resolved_postmortem_usefulness_weight=d("0.100000"),
        )
    with pytest.raises(ValueError, match="watch_score_floor must not exceed reuse_score_floor"):
        module.TeamSpecialistDomainMemoryReuseRankV2Config(
            watch_score_floor=d("0.800000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistDomainMemoryReuseRankV2Config(paper_only=False)
    with pytest.raises(ValueError, match="required_source_families must not be empty"):
        context(required_source_families=())
    with pytest.raises(ValueError, match="memory_items must be a list or tuple"):
        module.build_team_specialist_domain_memory_reuse_rank_v2_report(
            reuse_context=context(),
            memory_items=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="memory_items must contain TeamSpecialistDomainMemoryReuseItemV2 values",
    ):
        module.build_team_specialist_domain_memory_reuse_rank_v2_report(
            reuse_context=context(),
            memory_items=[object()],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="memory_items must have unique public keys"):
        module.build_team_specialist_domain_memory_reuse_rank_v2_report(
            reuse_context=context(),
            memory_items=(memory_item(), memory_item()),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_domain_memory_reuse_rank_v2_report(
            reuse_context=context(),
            memory_items=(memory_item(),),
            generated_at=datetime(2026, 7, 7),
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        memory_item(readonly=False)
    with pytest.raises(ValueError, match="report must be"):
        module.team_specialist_domain_memory_reuse_rank_v2_payload(object())


def test_digest_tampering_and_row_consistency_are_rejected() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="average_reuse_score must match rows"):
        replace(report, average_reuse_score=d("0.500000"))
    with pytest.raises(ValueError, match="rows must be sorted by reuse score and rank"):
        replace(report, rows=(report.rows[1], report.rows[0], report.rows[2]))
    with pytest.raises(ValueError, match="derived_validation_digest must match row fields"):
        replace(report.rows[0], reuse_score=d("0.900000"))


def test_rejects_unsafe_public_keys_values_and_surface() -> None:
    module = api()

    for unsafe_value in (
        "live_team",
        "auth_team",
        "wallet_team",
        "order_team",
        "network_team",
        "database_team",
        "persist_team",
        "signing_team",
        "mutation_team",
        "buy_team",
        "sell_team",
        "trade_team",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            memory_item(team_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_public_surface_is_readonly_report_only_and_has_no_unsafe_runtime_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)

    module = api()
    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_DOMAIN_MEMORY_REUSE_RANK_V2_CONFIG_VERSION",
        "TeamSpecialistDomainMemoryReuseContextV2",
        "TeamSpecialistDomainMemoryReuseItemV2",
        "TeamSpecialistDomainMemoryReuseRankV2Config",
        "TeamSpecialistDomainMemoryReuseRankV2Report",
        "TeamSpecialistDomainMemoryReuseRankV2Row",
        "build_team_specialist_domain_memory_reuse_rank_v2_report",
        "team_specialist_domain_memory_reuse_rank_v2_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "team_specialist_domain_memory_reuse_rank_v2" not in getattr(
        root,
        "__all__",
        (),
    )
