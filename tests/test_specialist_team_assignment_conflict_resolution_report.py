from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 12, 9, 30, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 12, 9, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_assignment_conflict_resolution_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    return api().SpecialistTeamAssignmentConflictResolutionConfig(**overrides)


def route(
    candidate_key: str,
    team_label: str,
    *,
    primary_route_confidence: Decimal = d("0.910000"),
    advisory_route_confidence: Decimal = d("0.250000"),
    domain_overlap_count: Decimal = d("3.000000"),
    memory_policy_status: str = "pass",
    source_quorum_status: str = "pass",
    observed_at: datetime = OBSERVED_AT,
):
    return api().SpecialistTeamAssignmentRouteCandidate(
        candidate_key=candidate_key,
        team_label=team_label,
        primary_route_confidence=primary_route_confidence,
        advisory_route_confidence=advisory_route_confidence,
        domain_overlap_count=domain_overlap_count,
        memory_policy_status=memory_policy_status,
        source_quorum_status=source_quorum_status,
        observed_at=observed_at,
    )


def build_report(*routes, cfg=None, generated_at: datetime = GENERATED_AT):
    return api().build_specialist_team_assignment_conflict_resolution_report(
        routes,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_assignment_conflict_resolution_selects_primary_and_advisors() -> None:
    candidate_alpha = (
        route("candidate-alpha-sensitive-key", "team_macro"),
        route(
            "candidate-alpha-sensitive-key",
            "team_crypto",
            primary_route_confidence=d("0.850000"),
            advisory_route_confidence=d("0.780000"),
            domain_overlap_count=d("2.000000"),
        ),
        route(
            "candidate-alpha-sensitive-key",
            "team_politics",
            primary_route_confidence=d("0.760000"),
            advisory_route_confidence=d("0.650000"),
            domain_overlap_count=d("1.000000"),
        ),
    )
    candidate_beta = (
        route(
            "candidate-beta-sensitive-key",
            "team_energy",
            primary_route_confidence=d("0.780000"),
            advisory_route_confidence=d("0.640000"),
            domain_overlap_count=d("1.000000"),
        ),
        route(
            "candidate-beta-sensitive-key",
            "team_macro",
            primary_route_confidence=d("0.740000"),
            advisory_route_confidence=d("0.600000"),
            domain_overlap_count=d("1.000000"),
        ),
    )
    candidate_gamma = (
        route(
            "candidate-gamma-sensitive-key",
            "team_weather",
            primary_route_confidence=d("0.620000"),
            advisory_route_confidence=d("0.550000"),
            domain_overlap_count=d("0.000000"),
            memory_policy_status="watch",
        ),
    )
    candidate_delta = (
        route(
            "candidate-delta-sensitive-key",
            "team_sports",
            primary_route_confidence=d("0.930000"),
            advisory_route_confidence=d("0.200000"),
            source_quorum_status="blocked",
        ),
    )

    report = build_report(
        *candidate_alpha,
        *candidate_beta,
        *candidate_gamma,
        *candidate_delta,
    )
    reversed_report = build_report(
        *reversed((*candidate_alpha, *candidate_beta, *candidate_gamma, *candidate_delta)),
    )

    assert api().ASSIGNMENT_CONFLICT_RESOLUTION_STATUSES == ("pass", "watch", "blocked")
    assert report.assignment_count == d("4.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("2.000000")
    assert report.blocked_count == d("1.000000")
    assert report.manual_review_count == d("3.000000")
    assert report.status == "blocked"
    assert report.manual_next_step == "paper_assignment_conflict_block_review"
    assert report.max_primary_route_confidence == d("0.930000")
    assert report.min_primary_route_confidence == d("0.620000")
    assert report.max_domain_overlap_count == d("3.000000")

    blocked, watched_conflict, watched_low, passed = report.rows
    assert tuple(row.assignment_rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
        d("4.000000"),
    )
    assert blocked.assignment_status == "blocked"
    assert blocked.selected_primary_team == "team_sports"
    assert blocked.advisory_teams == ()
    assert blocked.reason_codes == ("assignment_source_quorum_blocked",)
    assert blocked.manual_next_step == "paper_assignment_source_quorum_review"

    assert watched_conflict.assignment_status == "watch"
    assert watched_conflict.selected_primary_team == "team_energy"
    assert watched_conflict.advisory_teams == ("team_macro",)
    assert watched_conflict.reason_codes == (
        "assignment_primary_confidence_watch",
        "assignment_primary_margin_conflict_watch",
    )
    assert watched_conflict.manual_next_step == "paper_assignment_conflict_review"

    assert watched_low.assignment_status == "watch"
    assert watched_low.selected_primary_team == "team_weather"
    assert watched_low.advisory_teams == ()
    assert watched_low.reason_codes == (
        "assignment_primary_confidence_watch",
        "assignment_memory_policy_watch",
    )

    assert passed.assignment_status == "pass"
    assert passed.selected_primary_team == "team_macro"
    assert passed.advisory_teams == ("team_crypto", "team_politics")
    assert passed.reason_codes == ("assignment_conflict_clear",)
    assert passed.manual_next_step == "paper_assignment_monitor"

    payload = api().specialist_team_assignment_conflict_resolution_report_payload(report)
    reversed_payload = api().specialist_team_assignment_conflict_resolution_report_payload(
        reversed_report,
    )
    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["rows"][0]["primary_route_confidence"] == "0.930000"
    assert payload["rows"][1]["advisory_teams"] == ["team_macro"]
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_assignment_conflict_resolution_is_report_only_and_decimal_strict() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_SPECIALIST_TEAM_ASSIGNMENT_CONFLICT_RESOLUTION_CONFIG_VERSION",
        "ASSIGNMENT_CONFLICT_RESOLUTION_STATUSES",
        "SpecialistTeamAssignmentConflictResolutionConfig",
        "SpecialistTeamAssignmentConflictResolutionReport",
        "SpecialistTeamAssignmentConflictResolutionRow",
        "SpecialistTeamAssignmentRouteCandidate",
        "build_specialist_team_assignment_conflict_resolution_report",
        "specialist_team_assignment_conflict_resolution_report_digest",
        "specialist_team_assignment_conflict_resolution_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    empty = build_report()
    assert empty.status == "pass"
    assert empty.assignment_count == d("0.000000")
    assert empty.reason_codes == ("assignment_conflict_no_candidates",)
    assert empty.manual_next_step == "paper_assignment_monitor"
    assert empty.rows == ()

    populated = build_report(route("candidate-public-safe-key", "team_macro"))
    for value in (config(), route("candidate-other-safe-key", "team_energy"), populated, *populated.rows):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_confidence", "_rank")):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.rows[0].assignment_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="primary_route_confidence must be a Decimal"):
        route("candidate-key", "team_macro", primary_route_confidence=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        route("candidate-key", "team_macro", observed_at=datetime(2026, 7, 12, 9, 0))
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            route("candidate-key", "team_macro"),
            generated_at=datetime(
                2026,
                7,
                12,
                9,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="duplicate team"):
        build_report(
            route("candidate-key", "team_macro"),
            route("candidate-key", "team_macro", advisory_route_confidence=d("0.700000")),
        )
    with pytest.raises(ValueError, match="memory_policy_status"):
        route("candidate-key", "team_macro", memory_policy_status="open")
    with pytest.raises(ValueError, match="source_quorum_status"):
        route("candidate-key", "team_macro", source_quorum_status="open")
    with pytest.raises(ValueError, match="min_pass_primary_route_confidence"):
        config(
            min_pass_primary_route_confidence=d("0.700000"),
            min_watch_primary_route_confidence=d("0.800000"),
        )

    payload = module.specialist_team_assignment_conflict_resolution_report_payload(
        populated,
    )
    public = repr(payload).lower()
    forbidden = (
        "candidate-public-safe-key",
        "candidate-other-safe-key",
        "candidate",
        "market",
        "slug",
        "question",
        "https://",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "sizing",
        "live",
    )
    for token_value in forbidden:
        assert token_value not in public


def test_assignment_conflict_resolution_rejects_payload_leaks_and_schema_extensions() -> None:
    module = api()
    report = build_report(
        route(
            "candidate-sensitive-key",
            "team_macro",
            source_quorum_status="watch",
        ),
    )
    payload = module.specialist_team_assignment_conflict_resolution_report_payload(report)

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.specialist_team_assignment_conflict_resolution_report_payload(tampered)

    int_numeric = dict(payload)
    int_numeric["assignment_count"] = 1
    int_numeric["derived_validation_digest"] = canonical_digest(int_numeric)
    with pytest.raises(ValueError, match="Decimal"):
        module.specialist_team_assignment_conflict_resolution_report_payload(int_numeric)

    unsafe_extra = dict(payload)
    unsafe_extra["wallet"] = "0xabc"
    unsafe_extra["derived_validation_digest"] = canonical_digest(unsafe_extra)
    with pytest.raises(ValueError, match="unsafe"):
        module.specialist_team_assignment_conflict_resolution_report_payload(unsafe_extra)

    unexpected_extra = dict(payload)
    unexpected_extra["review_note"] = "internal note"
    unexpected_extra["derived_validation_digest"] = canonical_digest(unexpected_extra)
    with pytest.raises(ValueError, match="unexpected public payload field"):
        module.specialist_team_assignment_conflict_resolution_report_payload(
            unexpected_extra,
        )

    leaked_candidate_ref = dict(payload)
    leaked_candidate_ref["rows"] = [
        dict(payload["rows"][0], assignment_ref="candidate-sensitive-key"),
    ]
    leaked_candidate_ref["derived_validation_digest"] = canonical_digest(
        leaked_candidate_ref,
    )
    with pytest.raises(ValueError, match="assignment_ref"):
        module.specialist_team_assignment_conflict_resolution_report_payload(
            leaked_candidate_ref,
        )


def _float_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) is float:
        return (path or "<root>",)
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            found.extend(_float_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(found)
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(found)
    return ()
