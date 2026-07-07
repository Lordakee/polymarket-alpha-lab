from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 15, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_source_collection_load_balancer_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def decimal_arg(value: object) -> object:
    if type(value) is str:
        return d(value)
    return value


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "queue_watch_age_seconds": d("3600.000000"),
        "queue_blocked_age_seconds": d("10800.000000"),
        "close_urgency_seconds": d("3600.000000"),
        "specialist_load_watch_ratio": d("0.750000"),
        "min_category_expertise_score": d("0.700000"),
    }
    values.update(overrides)
    return module.TeamSpecialistSourceCollectionLoadBalancerV2Config(**values)


def queue_item(
    collection_id: str,
    source_family: str,
    *,
    queued_seconds_ago: int,
    closes_in_seconds: int,
    source_family_gap_score: str,
    contradiction_severity_score: str,
):
    module = api()
    return module.TeamSpecialistSourceCollectionQueueItemV2(
        collection_id=collection_id,
        team_id="macro_rates",
        category_id="finance.macro.rates",
        source_family=source_family,
        queued_at=GENERATED_AT - timedelta(seconds=queued_seconds_ago),
        closes_at=GENERATED_AT + timedelta(seconds=closes_in_seconds),
        source_family_gap_score=d(source_family_gap_score),
        contradiction_severity_score=d(contradiction_severity_score),
    )


def specialist(
    specialist_id: str,
    source_families: tuple[str, ...],
    *,
    current_assignment_count: str,
    max_assignment_count: str,
    category_expertise_score: str,
):
    module = api()
    return module.TeamSpecialistSourceCollectionSpecialistLoadV2(
        specialist_id=specialist_id,
        team_id="macro_rates",
        category_id="finance.macro.rates",
        source_families=source_families,
        current_assignment_count=decimal_arg(current_assignment_count),
        max_assignment_count=decimal_arg(max_assignment_count),
        category_expertise_score=decimal_arg(category_expertise_score),
    )


def build_report(*items: object, specialists: tuple[object, ...] | None = None):
    module = api()
    return module.build_team_specialist_source_collection_load_balancer_v2(
        items,
        specialists=specialists
        if specialists is not None
        else (
            specialist(
                "macro_collector_a",
                ("official", "news"),
                current_assignment_count="1",
                max_assignment_count="4",
                category_expertise_score="0.900000",
            ),
            specialist(
                "macro_collector_b",
                ("official",),
                current_assignment_count="3",
                max_assignment_count="4",
                category_expertise_score="0.950000",
            ),
            specialist(
                "macro_collector_c",
                ("altdata",),
                current_assignment_count="0",
                max_assignment_count="2",
                category_expertise_score="0.650000",
            ),
        ),
        config=config(),
        generated_at=GENERATED_AT,
    )


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if type(value) is dict:
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_float_values(item)
    if type(value) in (list, tuple):
        for item in value:
            assert_no_float_values(item)


def test_assigns_source_collection_by_priority_load_expertise_and_gaps() -> None:
    report = build_report(
        queue_item(
            "collect-beta",
            "altdata",
            queued_seconds_ago=600,
            closes_in_seconds=7200,
            source_family_gap_score="0.700000",
            contradiction_severity_score="0.100000",
        ),
        queue_item(
            "collect-alpha",
            "official",
            queued_seconds_ago=7200,
            closes_in_seconds=1800,
            source_family_gap_score="0.900000",
            contradiction_severity_score="0.800000",
        ),
    )

    assert report.report_status == "watch"
    assert report.queue_item_count == d("2")
    assert report.assigned_item_count == d("2")
    assert report.watch_item_count == d("2")
    assert report.blocked_item_count == d("0")
    assert report.specialist_count == d("3")
    assert report.reason_codes == (
        "queue_age_watch",
        "category_expertise_strong",
        "category_expertise_weak",
        "source_family_gap_present",
        "source_family_skill_matched",
        "close_urgency_present",
        "contradiction_severity_present",
        "source_collection_load_balancer_watch",
    )

    alpha, beta = report.assignment_rows
    assert alpha.collection_id == "collect-alpha"
    assert alpha.assignment_rank == d("1")
    assert alpha.assigned_specialist_id == "macro_collector_a"
    assert alpha.assignment_status == "watch"
    assert alpha.queue_age_seconds == d("7200.000000")
    assert alpha.queue_age_score == d("0.666667")
    assert alpha.specialist_load_ratio == d("0.250000")
    assert alpha.specialist_remaining_capacity_count == d("2")
    assert alpha.category_expertise_score == d("0.900000")
    assert alpha.source_family_gap_score == d("0.900000")
    assert alpha.close_urgency_score == d("0.500000")
    assert alpha.contradiction_severity_score == d("0.800000")
    assert alpha.assignment_score == d("0.841667")
    assert alpha.reason_codes == (
        "queue_age_watch",
        "category_expertise_strong",
        "source_family_gap_present",
        "source_family_skill_matched",
        "close_urgency_present",
        "contradiction_severity_present",
        "assignment_ranked",
    )

    assert beta.collection_id == "collect-beta"
    assert beta.assignment_rank == d("2")
    assert beta.assigned_specialist_id == "macro_collector_c"
    assert beta.assignment_status == "watch"
    assert beta.queue_age_score == d("0.055556")
    assert beta.specialist_load_ratio == d("0.000000")
    assert beta.category_expertise_score == d("0.650000")
    assert beta.source_family_gap_score == d("0.700000")
    assert beta.close_urgency_score == d("0.000000")
    assert beta.contradiction_severity_score == d("0.100000")
    assert beta.assignment_score == d("0.715972")
    assert beta.reason_codes == (
        "category_expertise_weak",
        "source_family_gap_present",
        "source_family_skill_matched",
        "contradiction_severity_present",
        "assignment_ranked",
    )


def test_assignment_is_input_order_deterministic_and_tamper_evident() -> None:
    alpha = queue_item(
        "collect-alpha",
        "official",
        queued_seconds_ago=7200,
        closes_in_seconds=1800,
        source_family_gap_score="0.900000",
        contradiction_severity_score="0.800000",
    )
    beta = queue_item(
        "collect-beta",
        "altdata",
        queued_seconds_ago=600,
        closes_in_seconds=7200,
        source_family_gap_score="0.700000",
        contradiction_severity_score="0.100000",
    )

    first = build_report(beta, alpha)
    second = build_report(alpha, beta)

    assert first.assignment_rows == second.assignment_rows
    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert all(len(row.derived_validation_digest) == 64 for row in first.assignment_rows)

    object.__setattr__(first.assignment_rows[0], "assignment_score", d("0.000001"))
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        api().team_specialist_source_collection_load_balancer_v2_payload(first)


def test_blocks_when_no_specialist_capacity_is_available() -> None:
    report = build_report(
        queue_item(
            "collect-alpha",
            "official",
            queued_seconds_ago=12000,
            closes_in_seconds=0,
            source_family_gap_score="1.000000",
            contradiction_severity_score="1.000000",
        ),
        specialists=(
            specialist(
                "macro_collector_full",
                ("official",),
                current_assignment_count="2",
                max_assignment_count="2",
                category_expertise_score="0.950000",
            ),
        ),
    )

    row = report.assignment_rows[0]
    assert report.report_status == "blocked"
    assert report.assigned_item_count == d("0")
    assert report.blocked_item_count == d("1")
    assert row.assignment_status == "blocked"
    assert row.assigned_specialist_id is None
    assert row.assignment_score == d("0.000000")
    assert row.reason_codes == (
        "queue_age_blocked",
        "specialist_load_blocked",
        "source_family_gap_present",
        "close_urgency_present",
        "contradiction_severity_present",
        "assignment_unfilled",
    )


def test_payload_serializes_decimal_strings_and_revalidates_digest() -> None:
    module = api()
    report = build_report(
        queue_item(
            "collect-alpha",
            "official",
            queued_seconds_ago=7200,
            closes_in_seconds=1800,
            source_family_gap_score="0.900000",
            contradiction_severity_score="0.800000",
        ),
    )

    payload = module.team_specialist_source_collection_load_balancer_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T15:00:00+00:00"
    assert payload["queue_item_count"] == "1"
    assert payload["assignment_rows"][0]["assignment_rank"] == "1"
    assert payload["assignment_rows"][0]["assignment_score"] == "0.841667"
    assert payload["assignment_rows"][0]["paper_only"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)

    tampered = dict(payload)
    tampered["assigned_item_count"] = "0"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_source_collection_load_balancer_v2_payload(tampered)

    with pytest.raises(ValueError, match="Decimal"):
        module.team_specialist_source_collection_load_balancer_v2_payload(
            {"score": 1, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="float"):
        module.team_specialist_source_collection_load_balancer_v2_payload(
            {"score": 0.5, "paper_only": True, "report_only": True, "readonly": True},
        )


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    item = queue_item(
        "collect-alpha",
        "official",
        queued_seconds_ago=7200,
        closes_in_seconds=1800,
        source_family_gap_score="0.900000",
        contradiction_severity_score="0.800000",
    )
    person = specialist(
        "macro_collector_a",
        ("official",),
        current_assignment_count="1",
        max_assignment_count="4",
        category_expertise_score="0.900000",
    )
    report = build_report(item, specialists=(person,))

    for value in (config(), item, person, report.assignment_rows[0], report):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        assert_public_numeric_values_are_decimal(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="current_assignment_count"):
        specialist(
            "macro_collector_a",
            ("official",),
            current_assignment_count="1.5",
            max_assignment_count="4",
            category_expertise_score="0.900000",
        )
    with pytest.raises(ValueError, match="category_expertise_score"):
        specialist(
            "macro_collector_a",
            ("official",),
            current_assignment_count="1",
            max_assignment_count="4",
            category_expertise_score=_DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="queue_watch_age_seconds"):
        config(queue_watch_age_seconds=_DecimalSubclass("3600.000000"))

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt):  # type: ignore[no-untyped-def]
            return None

        def dst(self, dt):  # type: ignore[no-untyped-def]
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_source_collection_load_balancer_v2(
            (item,),
            specialists=(person,),
            config=config(),
            generated_at=datetime(2026, 7, 6, 15, 0, tzinfo=MissingOffsetTz()),
        )


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "li" "ve_surface",
        "au" "th_surface",
        "wal" "let_surface",
        "or" "der_surface",
        "net" "work_surface",
        "data" "base_surface",
        "per" "sist_surface",
        "sig" "ning_surface",
        "mu" "tation_surface",
        "b" "uy_surface",
        "se" "ll_surface",
        "tra" "de_surface",
    ),
)
def test_rejects_unsafe_public_keys_and_values(unsafe_value: str) -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public"):
        queue_item(
            unsafe_value,
            "official",
            queued_seconds_ago=7200,
            closes_in_seconds=1800,
            source_family_gap_score="0.900000",
            contradiction_severity_score="0.800000",
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.team_specialist_source_collection_load_balancer_v2_payload(
            {"note": unsafe_value, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.team_specialist_source_collection_load_balancer_v2_payload(
            {unsafe_value: "redacted", "paper_only": True, "report_only": True, "readonly": True},
        )


def test_module_scope_has_no_unsafe_surfaces() -> None:
    module = api()
    source_text = inspect.getsource(module)
    tree = ast.parse(source_text)

    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_SOURCE_COLLECTION_LOAD_BALANCER_V2_CONFIG_VERSION",
        "ASSIGNMENT_STATUSES",
        "REPORT_STATUSES",
        "TeamSpecialistSourceCollectionLoadBalancerV2Config",
        "TeamSpecialistSourceCollectionQueueItemV2",
        "TeamSpecialistSourceCollectionSpecialistLoadV2",
        "TeamSpecialistSourceCollectionAssignmentRowV2",
        "TeamSpecialistSourceCollectionLoadBalancerV2Report",
        "build_team_specialist_source_collection_load_balancer_v2",
        "team_specialist_source_collection_load_balancer_v2_payload",
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
        "polymarket_alpha_lab",
        "typing",
    }
    forbidden_source_terms = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "au" "th",
        "wal" "let",
        "or" "der",
        "net" "work",
        "data" "base",
        "per" "sist",
        "sig" "ning",
        "mu" "tation",
        "b" "uy",
        "se" "ll",
        "tra" "de",
        "tra" "ding",
        "broker",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
        "wri" "te_text",
        "wri" "te_bytes",
    )
    assert all(term not in source_text.lower() for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "send",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
