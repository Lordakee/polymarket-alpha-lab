from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from polymarket_alpha_lab.specialist_team_routing_taxonomy_readiness_report import (
    DEFAULT_SPECIALIST_TEAM_ROUTING_TAXONOMY_READINESS_CONFIG_VERSION,
    MEDIUM_SCALE_SPECIALIST_TEAM_CATEGORIES,
    SPECIALIST_TEAM_ROUTING_TAXONOMY_READINESS_STATUSES,
    SpecialistTeamRoutingTaxonomyReadinessConfig,
    SpecialistTeamRoutingTaxonomyReadinessInput,
    SpecialistTeamRoutingTaxonomyReadinessReport,
    SpecialistTeamRoutingTaxonomyReadinessRow,
    build_specialist_team_routing_taxonomy_readiness_report,
    specialist_team_routing_taxonomy_readiness_report_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_routing_taxonomy_readiness_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _AlwaysEqualString(str):
    __hash__ = str.__hash__

    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False


_DEFAULT_PRIMARY_TEAM_ID = object()


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def rehash(payload: dict[str, Any]) -> dict[str, Any]:
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def assignment(
    category_id: str,
    *,
    primary_team_id: str | None | object = _DEFAULT_PRIMARY_TEAM_ID,
    advisory_team_ids: tuple[str, ...] = ("general_research",),
    unrouted_block_reason: str | None = None,
) -> SpecialistTeamRoutingTaxonomyReadinessInput:
    actual_primary_team_id = (
        category_id if primary_team_id is _DEFAULT_PRIMARY_TEAM_ID else primary_team_id
    )
    return SpecialistTeamRoutingTaxonomyReadinessInput(
        category_id=category_id,
        primary_team_id=actual_primary_team_id,  # type: ignore[arg-type]
        advisory_team_ids=advisory_team_ids,
        unrouted_block_reason=unrouted_block_reason,
    )


def complete_assignments(
    *,
    overrides: dict[str, SpecialistTeamRoutingTaxonomyReadinessInput] | None = None,
) -> tuple[SpecialistTeamRoutingTaxonomyReadinessInput, ...]:
    values = {
        category_id: assignment(category_id)
        for category_id in MEDIUM_SCALE_SPECIALIST_TEAM_CATEGORIES
    }
    if overrides is not None:
        values.update(overrides)
    return tuple(values[category_id] for category_id in MEDIUM_SCALE_SPECIALIST_TEAM_CATEGORIES)


def build_report(
    inputs: tuple[SpecialistTeamRoutingTaxonomyReadinessInput, ...] | None = None,
) -> SpecialistTeamRoutingTaxonomyReadinessReport:
    return build_specialist_team_routing_taxonomy_readiness_report(
        complete_assignments() if inputs is None else inputs,
        config=SpecialistTeamRoutingTaxonomyReadinessConfig(),
    )


def assert_no_float_int_or_live_surface(value: Any) -> None:
    forbidden = (
        "live",
        "auth",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
        "database",
        "table",
        "dsn",
        "url",
        "http://",
        "https://",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            lowered_key = key.casefold()
            assert not any(term in lowered_key for term in forbidden), lowered_key
            assert_no_float_int_or_live_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_int_or_live_surface(item)
        return
    if isinstance(value, float):
        raise AssertionError(f"unexpected float {value!r}")
    if type(value) is int:
        raise AssertionError(f"unexpected int {value!r}")
    if type(value) is str:
        lowered = value.casefold()
        assert not any(term in lowered for term in forbidden), lowered


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def test_complete_taxonomy_passes_for_all_medium_scale_specialist_categories() -> None:
    report = build_report()
    payload = specialist_team_routing_taxonomy_readiness_report_payload(report)

    assert report.config_version == (
        DEFAULT_SPECIALIST_TEAM_ROUTING_TAXONOMY_READINESS_CONFIG_VERSION
    )
    assert MEDIUM_SCALE_SPECIALIST_TEAM_CATEGORIES == (
        "politics",
        "crypto_btc",
        "crypto_eth",
        "macro_rates",
        "equity_indices",
        "gold",
        "oil",
        "soccer",
        "basketball",
        "other_sports",
    )
    assert SPECIALIST_TEAM_ROUTING_TAXONOMY_READINESS_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "pass"
    assert report.category_count == d("10.000000")
    assert report.pass_count == d("10.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.ready_ratio == d("1.000000")
    assert report.reason_codes == ("routing_taxonomy_ready",)
    assert tuple(row.category_id for row in report.rows) == (
        MEDIUM_SCALE_SPECIALIST_TEAM_CATEGORIES
    )
    assert {row.status for row in report.rows} == {"pass"}
    assert payload["category_count"] == "10.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_int_or_live_surface(payload)
    json.dumps(payload, sort_keys=True)


def test_builds_readonly_research_assignments_for_medium_scale_domain_teams() -> None:
    report = build_report(
        complete_assignments(
            overrides={
                "crypto_btc": assignment(
                    "crypto_btc",
                    advisory_team_ids=("macro_rates", "equity_indices"),
                ),
                "soccer": assignment("soccer", advisory_team_ids=()),
                "basketball": assignment(
                    "basketball",
                    primary_team_id=None,
                    advisory_team_ids=("sports_soccer",),
                    unrouted_block_reason="needs_team_memory_backfill",
                ),
            },
        ),
    )

    assert report.assignment_count == d("10.000000")
    assert report.memory_ready_count == d("9.000000")
    assert report.calibration_ready_count == d("9.000000")
    assert report.research_assignment_action == "prepare_readonly_research_assignments"

    by_category = {
        assignment.category_id: assignment for assignment in report.research_assignments
    }
    assert by_category["politics"].research_team_id == "politics"
    assert by_category["politics"].assignment_kind == "team_readiness_confirm"
    assert by_category["politics"].memory_readiness == "ready"
    assert by_category["politics"].calibration_readiness == "ready"
    assert by_category["politics"].research_assignment == (
        "confirm_politics_team_memory_and_calibration_readiness"
    )

    assert by_category["crypto_btc"].research_team_id == "crypto_btc"
    assert by_category["crypto_btc"].advisory_team_ids == (
        "macro_rates",
        "equity_indices",
    )
    assert by_category["crypto_btc"].assignment_kind == "team_readiness_confirm"

    assert by_category["soccer"].research_team_id == "sports_soccer"
    assert by_category["soccer"].assignment_kind == "calibration_backfill"
    assert by_category["soccer"].memory_readiness == "ready"
    assert by_category["soccer"].calibration_readiness == "needs_backfill"
    assert by_category["soccer"].research_assignment == (
        "backfill_sports_soccer_calibration_advisory_coverage"
    )

    assert by_category["basketball"].research_team_id is None
    assert by_category["basketball"].assignment_kind == "memory_backfill"
    assert by_category["basketball"].memory_readiness == "needs_backfill"
    assert by_category["basketball"].calibration_readiness == "ready"
    assert by_category["basketball"].research_assignment == (
        "backfill_sports_basketball_primary_team_memory"
    )

    payload = report.payload
    assert payload["research_assignment_action"] == (
        "prepare_readonly_research_assignments"
    )
    assert payload["research_assignments"][0]["research_assignment"] == (
        "confirm_politics_team_memory_and_calibration_readiness"
    )
    assert_no_float_int_or_live_surface(payload)


def test_missing_primary_advisory_and_unrouted_reason_are_reported_per_category() -> None:
    report = build_report(
        complete_assignments(
            overrides={
                "crypto_eth": assignment("crypto_eth", primary_team_id=None),
                "oil": assignment("oil", advisory_team_ids=()),
                "other_sports": assignment(
                    "other_sports",
                    primary_team_id=None,
                    advisory_team_ids=(),
                    unrouted_block_reason="needs_specialist_owner",
                ),
            },
        ),
    )

    assert report.status == "block"
    assert report.pass_count == d("7.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("2.000000")
    assert report.ready_ratio == d("0.700000")
    assert report.reason_codes == (
        "routing_taxonomy_has_watch_categories",
        "routing_taxonomy_has_block_categories",
    )

    by_category = {row.category_id: row for row in report.rows}
    assert by_category["crypto_eth"].status == "block"
    assert by_category["crypto_eth"].primary_team_ready is False
    assert by_category["crypto_eth"].advisory_teams_ready is True
    assert by_category["crypto_eth"].unrouted_block_reason_ready is False
    assert by_category["crypto_eth"].reason_codes == (
        "primary_team_missing",
        "unrouted_block_reason_missing",
    )

    assert by_category["oil"].status == "watch"
    assert by_category["oil"].primary_team_ready is True
    assert by_category["oil"].advisory_teams_ready is False
    assert by_category["oil"].reason_codes == ("advisory_teams_missing",)

    assert by_category["other_sports"].status == "block"
    assert by_category["other_sports"].primary_team_ready is False
    assert by_category["other_sports"].advisory_teams_ready is False
    assert by_category["other_sports"].unrouted_block_reason_ready is True
    assert by_category["other_sports"].reason_codes == (
        "primary_team_missing",
        "advisory_teams_missing",
        "unrouted_block_reason_present",
    )
    assert_no_float_int_or_live_surface(report.payload)


def test_missing_category_is_blocked_without_persistence_or_live_surface() -> None:
    inputs = tuple(
        item for item in complete_assignments() if item.category_id != "gold"
    )

    report = build_report(inputs)

    assert report.status == "block"
    assert report.category_count == d("10.000000")
    assert report.observed_category_count == d("9.000000")
    assert report.missing_category_count == d("1.000000")

    gold = {row.category_id: row for row in report.rows}["gold"]
    assert gold.status == "block"
    assert gold.primary_team_id is None
    assert gold.advisory_team_ids == ()
    assert gold.unrouted_block_reason is None
    assert gold.reason_codes == (
        "taxonomy_category_missing",
        "primary_team_missing",
        "advisory_teams_missing",
        "unrouted_block_reason_missing",
    )
    assert_no_float_int_or_live_surface(report.payload)


def test_dataclasses_are_frozen_exact_decimal_only_and_strictly_validated() -> None:
    cfg = SpecialistTeamRoutingTaxonomyReadinessConfig()
    input_value = assignment("politics")
    row = build_report().rows[0]
    report = build_report()

    for value in (cfg, input_value, row, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        assert_public_numeric_values_are_decimal(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="category_count must be exactly Decimal"):
        replace(report, category_count=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="category_count must be exactly Decimal"):
        replace(report, category_count=_DecimalSubclass("10"))
    with pytest.raises(ValueError, match="category_id"):
        assignment("crypto")
    with pytest.raises(ValueError, match="primary_team_id"):
        assignment("politics", primary_team_id="general")
    with pytest.raises(ValueError, match="advisory_team_ids"):
        assignment("politics", advisory_team_ids=("politics",))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(cfg, paper_only=False)


def test_public_payload_rejects_flag_downgrades_digest_tampering_and_unsafe_terms() -> None:
    report = build_report()
    payload = dict(report.payload)

    payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        specialist_team_routing_taxonomy_readiness_report_payload(payload)

    payload = dict(report.payload)
    payload["status"] = "watch"
    with pytest.raises(ValueError, match="digest"):
        specialist_team_routing_taxonomy_readiness_report_payload(payload)

    payload = dict(report.payload)
    payload["category_count"] = 10
    with pytest.raises(ValueError, match="Decimal-derived"):
        specialist_team_routing_taxonomy_readiness_report_payload(payload)

    payload = dict(report.payload)
    payload["note"] = "live order routing"
    with pytest.raises(ValueError, match="unsafe public value"):
        specialist_team_routing_taxonomy_readiness_report_payload(payload)


def test_dict_payload_materializes_exact_report_and_rejects_rehashed_derived_tampering() -> None:
    report = build_report()
    payload = json.loads(json.dumps(report.payload))

    assert specialist_team_routing_taxonomy_readiness_report_payload(payload) == payload

    mutations: tuple[tuple[tuple[str | int, ...], object], ...] = (
        (("status",), "watch"),
        (("pass_count",), "9.000000"),
        (("reason_codes",), ["routing_taxonomy_has_watch_categories"]),
        (("rows", 0, "status"), "watch"),
        (("rows", 0, "reason_codes"), ["advisory_teams_missing"]),
        (
            ("research_assignments", 0, "research_assignment"),
            "confirm_politics_team_memory_readiness",
        ),
    )
    for path, replacement in mutations:
        tampered = json.loads(json.dumps(payload))
        target: Any = tampered
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = replacement
        rehash(tampered)
        with pytest.raises(ValueError):
            specialist_team_routing_taxonomy_readiness_report_payload(tampered)

    extra_field = json.loads(json.dumps(payload))
    extra_field["note"] = "readonly_taxonomy_snapshot"
    rehash(extra_field)
    with pytest.raises(ValueError):
        specialist_team_routing_taxonomy_readiness_report_payload(extra_field)


def test_mapping_proxy_payload_preserves_plain_mapping_behavior() -> None:
    payload = json.loads(json.dumps(build_report().payload))

    assert specialist_team_routing_taxonomy_readiness_report_payload(
        MappingProxyType(payload),
    ) == payload


def test_mapping_payload_rejects_string_subclass_with_custom_equality() -> None:
    payload = json.loads(json.dumps(build_report().payload))
    payload["config_version"] = _AlwaysEqualString("unsupported_version")
    rehash(payload)

    with pytest.raises(ValueError, match="exact string"):
        specialist_team_routing_taxonomy_readiness_report_payload(payload)


def test_object_payload_canonicalizes_exact_decimal_quantum_and_digest() -> None:
    report = build_report()
    canonical_digest_value = report.derived_validation_digest
    object.__setattr__(report, "category_count", Decimal("10"))
    object.__setattr__(report, "ready_ratio", Decimal("1"))
    object.__setattr__(report.rows[0], "readiness_score", Decimal("1"))

    payload = specialist_team_routing_taxonomy_readiness_report_payload(report)

    assert payload["category_count"] == "10.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["rows"][0]["readiness_score"] == "1.000000"
    assert payload["derived_validation_digest"] == canonical_digest_value

    alternate_payload = json.loads(json.dumps(payload))
    alternate_payload["category_count"] = "10"
    alternate_payload["ready_ratio"] = "1"
    alternate_payload["rows"][0]["readiness_score"] = "1"
    rehash(alternate_payload)
    assert alternate_payload["derived_validation_digest"] != canonical_digest_value
    object.__setattr__(
        report,
        "derived_validation_digest",
        alternate_payload["derived_validation_digest"],
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        specialist_team_routing_taxonomy_readiness_report_payload(report)


@pytest.mark.parametrize(
    ("path", "replacement"),
    (
        (("category_count",), "10"),
        (("ready_ratio",), "1"),
        (("rows", 0, "readiness_score"), "1"),
    ),
)
def test_dict_payload_rejects_rehashed_noncanonical_decimal_quantum(
    path: tuple[str | int, ...],
    replacement: str,
) -> None:
    payload = json.loads(json.dumps(build_report().payload))
    original_digest = payload["derived_validation_digest"]
    target: Any = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    rehash(payload)
    assert payload["derived_validation_digest"] != original_digest

    with pytest.raises(ValueError, match="canonical"):
        specialist_team_routing_taxonomy_readiness_report_payload(payload)


def test_rows_retain_explicit_category_observation_evidence() -> None:
    inputs = tuple(
        item for item in complete_assignments() if item.category_id != "gold"
    )

    report = build_report(inputs)
    by_category = {row.category_id: row for row in report.rows}

    assert by_category["politics"].category_observed is True
    assert by_category["gold"].category_observed is False
    assert report.payload["rows"][0]["category_observed"] is True
    assert report.payload["rows"][5]["category_observed"] is False


def test_rehashed_payload_cannot_self_declare_observed_category_missing() -> None:
    payload = json.loads(json.dumps(build_report().payload))
    payload["rows"][0]["reason_codes"] = ["taxonomy_category_missing"]
    payload["observed_category_count"] = "9.000000"
    payload["missing_category_count"] = "1.000000"
    rehash(payload)

    with pytest.raises(ValueError, match="category_observed|reason_codes"):
        specialist_team_routing_taxonomy_readiness_report_payload(payload)


def test_object_payload_revalidates_nested_rows_after_digest_is_recomputed() -> None:
    report = build_report()
    tampered_payload = json.loads(json.dumps(report.payload))
    tampered_payload["rows"][0]["reason_codes"] = ["advisory_teams_missing"]
    object.__setattr__(report.rows[0], "reason_codes", ("advisory_teams_missing",))
    object.__setattr__(report, "derived_validation_digest", canonical_digest(tampered_payload))

    with pytest.raises(ValueError, match="reason_codes"):
        specialist_team_routing_taxonomy_readiness_report_payload(report)


def test_object_payload_rejects_noncanonical_rows_container() -> None:
    report = build_report()
    object.__setattr__(report, "rows", list(report.rows))

    with pytest.raises(ValueError, match="rows must be a tuple"):
        specialist_team_routing_taxonomy_readiness_report_payload(report)


def test_object_payload_rejects_report_count_decimal_subclass() -> None:
    report = build_report()
    object.__setattr__(
        report,
        "category_count",
        _DecimalSubclass("10.000000"),
    )

    with pytest.raises(ValueError, match="category_count must be exactly Decimal"):
        specialist_team_routing_taxonomy_readiness_report_payload(report)


def test_module_is_report_only_and_external_io_free() -> None:
    report = build_report()
    assert report == build_report()
    assert report.payload == build_report().payload

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_names: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module.split(".")[0])
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    assert imported_names.isdisjoint(
        {
            "httpx",
            "requests",
            "socket",
            "urllib",
            "psycopg",
            "psycopg2",
            "supabase",
            "sqlalchemy",
        },
    )
    assert call_names.isdisjoint({"open", "connect", "request", "post", "put", "delete"})
    assert_no_float_int_or_live_surface(report.payload)
