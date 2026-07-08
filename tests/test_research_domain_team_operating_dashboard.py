from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_team_operating_dashboard",
    )


def observation(
    domain: str = "politics",
    *,
    workload_count: Decimal = Decimal("4.000000"),
    active_research_count: Decimal = Decimal("2.000000"),
    memory_covered_count: Decimal = Decimal("8.000000"),
    memory_total_count: Decimal = Decimal("10.000000"),
    pending_review_count: Decimal = Decimal("0.000000"),
    stale_memory_count: Decimal = Decimal("0.000000"),
    blocked_review_count: Decimal = Decimal("0.000000"),
    evidence_gap_count: Decimal = Decimal("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchDomainTeamOperatingObservation(
        domain=domain,
        workload_count=workload_count,
        active_research_count=active_research_count,
        memory_covered_count=memory_covered_count,
        memory_total_count=memory_total_count,
        pending_review_count=pending_review_count,
        stale_memory_count=stale_memory_count,
        blocked_review_count=blocked_review_count,
        evidence_gap_count=evidence_gap_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report_from(observations: tuple[Any, ...]) -> Any:
    module = api()
    return module.build_research_domain_team_operating_dashboard(
        observations,
        config=module.ResearchDomainTeamOperatingDashboardConfig(),
        generated_at=GENERATED_AT,
    )


def assert_no_public_float_or_int(value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        pytest.fail(f"public numeric payload must not contain float/int: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_float_or_int(item)


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def test_builds_pass_watch_block_dashboard_payload_safely() -> None:
    module = api()
    report = report_from(
        (
            observation("soccer"),
            observation("crypto", pending_review_count=Decimal("1.000000")),
            observation("basketball"),
            observation(
                "macro",
                memory_covered_count=Decimal("4.000000"),
                blocked_review_count=Decimal("1.000000"),
                pending_review_count=Decimal("2.000000"),
                evidence_gap_count=Decimal("1.000000"),
            ),
            observation("gold"),
            observation("politics"),
        ),
    )

    assert report.public_status == "block"
    assert report.domain_count == Decimal("6.000000")
    assert report.pass_count == Decimal("4.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.total_workload_count == Decimal("24.000000")
    assert report.total_pending_review_count == Decimal("3.000000")
    assert report.average_memory_coverage_ratio == Decimal("0.733333")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    rows_by_domain = {row.domain: row for row in report.rows}
    assert rows_by_domain["politics"].public_status == "pass"
    assert rows_by_domain["crypto"].public_status == "watch"
    assert rows_by_domain["macro"].public_status == "block"
    assert rows_by_domain["macro"].reason_codes == (
        "domain_workload_pass",
        "domain_memory_coverage_block",
        "domain_pending_review_watch",
        "domain_blocked_review_present",
        "domain_evidence_gap_present",
    )

    payload = module.research_domain_team_operating_dashboard_payload(report)
    assert_no_public_float_or_int(payload)
    assert payload["public_status"] == "block"
    assert payload["domain_count"] == "6.000000"
    assert [row["domain"] for row in payload["rows"]] == [
        "basketball",
        "crypto",
        "gold",
        "macro",
        "politics",
        "soccer",
    ]
    assert {
        value
        for value in walk_values(payload)
        if isinstance(value, str) and value in {"pass", "watch", "block"}
    } == {"pass", "watch", "block"}
    assert all(
        status in {"pass", "watch", "block"}
        for status in [payload["public_status"]]
        + [row["public_status"] for row in payload["rows"]]
    )


def test_dataclasses_are_frozen_and_public_counts_are_decimal_only() -> None:
    module = api()

    for cls_name in (
        "ResearchDomainTeamOperatingDashboardConfig",
        "ResearchDomainTeamOperatingObservation",
        "ResearchDomainTeamOperatingDashboardRow",
        "ResearchDomainTeamOperatingDashboardReport",
    ):
        cls = getattr(module, cls_name)
        assert is_dataclass(cls)
        assert getattr(cls, "__dataclass_params__").frozen is True

    numeric_field_names = {
        field.name
        for cls_name in (
            "ResearchDomainTeamOperatingObservation",
            "ResearchDomainTeamOperatingDashboardRow",
            "ResearchDomainTeamOperatingDashboardReport",
        )
        for field in fields(getattr(module, cls_name))
        if field.name.endswith("_count") or field.name.endswith("_ratio")
    }
    assert numeric_field_names

    with pytest.raises(ValueError, match="workload_count must be a Decimal"):
        observation(workload_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_total_count must be a Decimal"):
        observation(memory_total_count=_DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_research_domain_team_operating_dashboard(
            (observation(),),
            config=module.ResearchDomainTeamOperatingDashboardConfig(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )

    row = report_from((observation(),)).rows[0]
    with pytest.raises(FrozenInstanceError):
        row.public_status = "watch"  # type: ignore[misc]


def test_public_payload_rejects_sensitive_keys_and_values() -> None:
    module = api()
    payload = module.research_domain_team_operating_dashboard_payload(
        report_from((observation(),)),
    )

    with pytest.raises(ValueError, match="unsafe public"):
        module.research_domain_team_operating_dashboard_payload(
            {**payload, "market_slug": "will-election-market-close"},
        )

    leaked_value = json.loads(json.dumps(payload))
    leaked_value["rows"][0]["reason_codes"] = ["buy_recommendation_from_source_url"]
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_domain_team_operating_dashboard_payload(leaked_value)

    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)


def test_payload_is_deterministic_for_input_order_and_timezone() -> None:
    module = api()
    observations = (
        observation("politics"),
        observation("crypto", pending_review_count=Decimal("1.000000")),
        observation("macro", blocked_review_count=Decimal("1.000000")),
    )
    shifted_generated_at = datetime(
        2026,
        7,
        8,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    first = module.research_domain_team_operating_dashboard_payload(
        module.build_research_domain_team_operating_dashboard(
            observations,
            config=module.ResearchDomainTeamOperatingDashboardConfig(),
            generated_at=GENERATED_AT,
        ),
    )
    second = module.research_domain_team_operating_dashboard_payload(
        module.build_research_domain_team_operating_dashboard(
            tuple(reversed(observations)),
            config=module.ResearchDomainTeamOperatingDashboardConfig(),
            generated_at=shifted_generated_at,
        ),
    )

    assert first == second
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
        second,
        sort_keys=True,
        separators=(",", ":"),
    )


def test_digest_matches_public_report_summary() -> None:
    module = api()
    report = report_from(
        (
            observation("politics"),
            observation("crypto", pending_review_count=Decimal("1.000000")),
            observation("macro", blocked_review_count=Decimal("1.000000")),
        ),
    )

    payload = module.research_domain_team_operating_dashboard_payload(report)
    digest = module.research_domain_team_operating_dashboard_digest(report)

    assert_no_public_float_or_int(digest)
    assert "rows" not in digest
    assert digest["generated_at"] == payload["generated_at"]
    assert digest["config_version"] == payload["config_version"]
    assert digest["public_status"] == payload["public_status"]
    assert digest["domain_count"] == payload["domain_count"]
    assert digest["pass_count"] == payload["pass_count"]
    assert digest["watch_count"] == payload["watch_count"]
    assert digest["block_count"] == payload["block_count"]
    assert digest["total_workload_count"] == payload["total_workload_count"]
    assert digest["total_pending_review_count"] == payload["total_pending_review_count"]
    assert digest["average_memory_coverage_ratio"] == payload[
        "average_memory_coverage_ratio"
    ]
    assert digest["reason_codes"] == payload["reason_codes"]
    assert digest["report_validation_digest"] == payload["validation_digest"]
    assert len(digest["digest_validation_digest"]) == 64
