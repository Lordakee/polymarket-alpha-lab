from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_news_monitoring_need_router.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_news_monitoring_need_router",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def unsafe(*parts: str) -> str:
    return "".join(parts)


def domain(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "domain_key": "macro_policy_calendar",
        "domain_label": "Macro policy calendar",
        "observed_at": GENERATED_AT - timedelta(minutes=30),
        "catalyst_cadence_score": d("0.200000"),
        "source_age_seconds": d("900.000000"),
        "evidence_conflict_score": d("0.100000"),
        "resolution_horizon_seconds": d("604800.000000"),
        "team_coverage_score": d("0.900000"),
        "reason_codes": (),
    }
    values.update(overrides)
    return module.ResearchEventNewsMonitoringNeedDomain(**values)


def report(domains: object | None = None):
    module = api()
    return module.build_research_event_news_monitoring_need_router_report(
        domains
        if domains is not None
        else (
            domain(),
            domain(
                domain_key="sports_roster_window",
                domain_label="Sports roster window",
                catalyst_cadence_score=d("0.650000"),
                source_age_seconds=d("7200.000000"),
                evidence_conflict_score=d("0.300000"),
                resolution_horizon_seconds=d("43200.000000"),
                team_coverage_score=d("0.550000"),
            ),
            domain(
                domain_key="governance_vote_close",
                domain_label="Governance vote close",
                catalyst_cadence_score=d("0.900000"),
                source_age_seconds=d("18000.000000"),
                evidence_conflict_score=d("0.850000"),
                resolution_horizon_seconds=d("1800.000000"),
                team_coverage_score=d("0.200000"),
            ),
        ),
        generated_at=GENERATED_AT,
    )


def assert_public_numbers_are_strings(value: Any) -> None:
    if type(value) in (float, int, Decimal, datetime):
        raise AssertionError(f"unexpected raw public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numbers_are_strings(item)
    if isinstance(value, list):
        for item in value:
            assert_public_numbers_are_strings(item)


def test_routes_event_domains_to_monitoring_intensity_from_news_need_dimensions() -> None:
    result = report()
    rows_by_key = {row.domain_key: row for row in result.routes}

    pass_row = rows_by_key["macro_policy_calendar"]
    watch_row = rows_by_key["sports_roster_window"]
    block_row = rows_by_key["governance_vote_close"]

    assert pass_row.route_status == "pass"
    assert pass_row.monitoring_intensity == "routine_review"
    assert pass_row.monitoring_need_score == d("17.000000")
    assert pass_row.reason_codes == (
        "event_news_monitoring_need_router_routine_review",
    )

    assert watch_row.route_status == "watch"
    assert watch_row.monitoring_intensity == "heightened_review"
    assert watch_row.monitoring_need_score == d("54.500000")
    assert watch_row.reason_codes == (
        "elevated_catalyst_cadence",
        "aging_source_window",
        "near_resolution_window",
        "limited_team_coverage",
    )

    assert block_row.route_status == "block"
    assert block_row.monitoring_intensity == "continuous_review"
    assert block_row.monitoring_need_score == d("88.000000")
    assert block_row.reason_codes == (
        "rapid_catalyst_cadence",
        "stale_source_window",
        "severe_evidence_conflict",
        "imminent_resolution_window",
        "thin_team_coverage",
    )

    assert tuple(row.route_status for row in result.routes) == ("block", "watch", "pass")
    assert result.status == "block"
    assert result.domain_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.max_monitoring_need_score == d("88.000000")
    assert result.mean_monitoring_need_score == d("53.166667")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_status_values_are_exactly_pass_watch_block() -> None:
    module = api()
    result = report()
    payload = module.research_event_news_monitoring_need_router_payload(result)

    statuses = {payload["status"]}
    statuses.update(row["route_status"] for row in payload["routes"])

    assert statuses == {"pass", "watch", "block"}
    assert set(module.MONITORING_STATUSES) == {"pass", "watch", "block"}
    assert "blocked" not in module.MONITORING_STATUSES
    with pytest.raises(ValueError, match="route_status"):
        replace(result.routes[0], route_status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(result, status="blocked")


def test_payload_is_deterministic_digest_checked_and_public_safe() -> None:
    module = api()
    first = report()
    second = report(tuple(reversed(first.input_domains)))

    payload = module.research_event_news_monitoring_need_router_payload(first)
    reversed_payload = module.research_event_news_monitoring_need_router_payload(second)

    assert payload == reversed_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["domain_count"] == "3.000000"
    assert payload["routes"][0]["monitoring_need_score"] == "88.000000"
    assert payload["routes"][0]["observed_at"] == "2026-07-08T11:30:00+00:00"
    assert len(payload["derived_validation_digest"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["derived_validation_digest"])
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_public_numbers_are_strings(payload)
    assert module.validate_research_event_news_monitoring_need_router_public_payload(
        payload,
    )

    tampered_payload = dict(payload)
    tampered_payload["domain_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_news_monitoring_need_router_payload(tampered_payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_news_monitoring_need_router_public_payload(
            missing_digest,
        )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload[unsafe("market", "_slug")] = "redacted"
    with pytest.raises(ValueError, match="public"):
        module.research_event_news_monitoring_need_router_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["operator_note"] = unsafe("https", "://example.test/raw")
    with pytest.raises(ValueError, match="public"):
        module.research_event_news_monitoring_need_router_payload(unsafe_value_payload)

    encoded = json.dumps(payload, sort_keys=True).lower()
    forbidden_public_fragments = (
        unsafe("source", "_url"),
        unsafe("source", "_text"),
        unsafe("raw", "_source"),
        unsafe("market", "_id"),
        unsafe("market", "_slug"),
        "slug",
        unsafe("ques", "tion"),
        unsafe("https", "://"),
        unsafe("http", "://"),
        unsafe("wal", "let"),
        unsafe("au", "th"),
        unsafe("ord", "er"),
        unsafe("tra", "de"),
        unsafe("li", "ve"),
        unsafe("reco", "mmend"),
    )
    assert not any(fragment in encoded for fragment in forbidden_public_fragments)


def test_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    module = api()
    result = report()

    for klass in (
        module.ResearchEventNewsMonitoringNeedRouterConfig,
        module.ResearchEventNewsMonitoringNeedDomain,
        module.ResearchEventNewsMonitoringNeedRoute,
        module.ResearchEventNewsMonitoringNeedReasonCodeCount,
        module.ResearchEventNewsMonitoringNeedReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        result.routes[0].route_status = "pass"  # type: ignore[misc]

    for public_record in (
        module.ResearchEventNewsMonitoringNeedRouterConfig(),
        domain(),
        result.routes[0],
        result.reason_code_counts[0],
        result,
    ):
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal

    with pytest.raises(TypeError):
        class DerivedDomain(module.ResearchEventNewsMonitoringNeedDomain):
            pass

    with pytest.raises(ValueError, match="config_version"):
        module.ResearchEventNewsMonitoringNeedRouterConfig(
            config_version=_StringSubclass(
                module.RESEARCH_EVENT_NEWS_MONITORING_NEED_ROUTER_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="observed_at"):
        domain(observed_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="catalyst_cadence_score"):
        domain(catalyst_cadence_score=1)
    with pytest.raises(ValueError, match="source_age_seconds"):
        domain(source_age_seconds=_DecimalSubclass("900.000000"))
    with pytest.raises(ValueError, match="evidence_conflict_score"):
        domain(evidence_conflict_score=d("1.000001"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_event_news_monitoring_need_router_report(
            (domain(),),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(domain(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(result.routes[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)


def test_empty_report_is_pass_report_only_and_digest_stable() -> None:
    module = api()
    result = module.build_research_event_news_monitoring_need_router_report(
        (),
        generated_at=GENERATED_AT,
    )
    payload = module.research_event_news_monitoring_need_router_payload(result)

    assert result.status == "pass"
    assert result.reason_codes == ("no_event_domains",)
    assert result.domain_count == d("0.000000")
    assert result.routes == ()
    assert result.reason_code_counts == ()
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert module.validate_research_event_news_monitoring_need_router_public_payload(
        payload,
    )


def test_module_scope_has_no_external_or_execution_surface() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lowered_source = source.lower()

    forbidden_source_fragments = (
        unsafe("source", "_url"),
        unsafe("source", "_text"),
        unsafe("raw", "_source"),
        unsafe("market", "_id"),
        unsafe("market", "_slug"),
        "slug",
        unsafe("ques", "tion"),
        unsafe("https", "://"),
        unsafe("http", "://"),
        unsafe("data", "base"),
        unsafe("net", "work"),
        unsafe("wal", "let"),
        unsafe("au", "th"),
        unsafe("ord", "er"),
        unsafe("tra", "de"),
        unsafe("li", "ve"),
        unsafe("exec", "ution"),
        unsafe("reco", "mmend"),
    )
    assert not any(fragment in lowered_source for fragment in forbidden_source_fragments)
    assert not hasattr(module, "client")
    assert not hasattr(module, "session")

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "asyncio",
        "http",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
