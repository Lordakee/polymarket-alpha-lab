from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_information_source_gap_closure_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _coverage(
    domain_name: str = "macro_policy",
    team_name: str = "policy_research",
    source_family: str = "public_calendar",
    *,
    required_source_count: Decimal = d("3"),
    available_source_count: Decimal = d("3"),
    fresh_source_count: Decimal = d("3"),
    stale_source_count: Decimal = d("0"),
    oldest_source_age_hours: Decimal = d("12.000000"),
    closure_sla_hours: Decimal = d("24.000000"),
):
    module = api()
    return module.ResearchInformationSourceGapClosureInput(
        domain_name=domain_name,
        team_name=team_name,
        source_family=source_family,
        required_source_count=required_source_count,
        available_source_count=available_source_count,
        fresh_source_count=fresh_source_count,
        stale_source_count=stale_source_count,
        oldest_source_age_hours=oldest_source_age_hours,
        closure_sla_hours=closure_sla_hours,
    )


def _config(**overrides: object):
    module = api()
    return module.ResearchInformationSourceGapClosureConfig(**overrides)


def _build_report(*rows, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_information_source_gap_closure_report(
        rows,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_gap_closure_report_rolls_up_domains_actions_and_digest() -> None:
    module = api()
    pass_input = _coverage(
        "macro_policy",
        "policy_research",
        "public_calendar",
    )
    watch_input = _coverage(
        "weather_events",
        "event_research",
        "official_bulletins",
        required_source_count=d("4"),
        available_source_count=d("3"),
        fresh_source_count=d("3"),
        stale_source_count=d("1"),
        oldest_source_age_hours=d("80.000000"),
        closure_sla_hours=d("12.000000"),
    )
    block_input = _coverage(
        "company_actions",
        "equity_research",
        "issuer_filings",
        required_source_count=d("5"),
        available_source_count=d("2"),
        fresh_source_count=d("1"),
        stale_source_count=d("3"),
        oldest_source_age_hours=d("200.000000"),
        closure_sla_hours=d("6.000000"),
    )

    report = _build_report(pass_input, watch_input, block_input)
    permuted = _build_report(block_input, pass_input, watch_input)
    payload = module.research_information_source_gap_closure_report_to_payload(report)
    permuted_payload = module.research_information_source_gap_closure_report_to_payload(
        permuted,
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert set(row.status for row in report.rows) == {"pass", "watch", "block"}
    assert report.domain_team_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.missing_source_count == d("4")
    assert report.stale_source_count == d("4")
    assert report.average_coverage_ratio == d("0.716667")
    assert report.minimum_fresh_ratio == d("0.200000")
    assert report.reason_codes == (
        "research_information_source_gap_closure_block",
        "research_information_source_gap_closure_watch",
        "research_information_source_gap_closure_pass",
    )
    assert report.public_digest == module.research_information_source_gap_closure_digest(
        report,
    )
    assert len(report.public_digest) == 64
    int(report.public_digest, 16)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.closure_action for row in report.rows) == (
        "close_research_information_source_gap_before_workflow_use",
        "schedule_public_research_source_refresh",
        "maintain_research_information_source_coverage",
    )

    blocked = report.rows[0]
    assert blocked.domain_name == "company_actions"
    assert blocked.coverage_gap_count == d("3")
    assert blocked.freshness_gap_count == d("4")
    assert blocked.coverage_ratio == d("0.400000")
    assert blocked.fresh_ratio == d("0.200000")
    assert blocked.reason_codes == (
        "research_information_source_gap_closure_missing_sources_block",
        "research_information_source_gap_closure_stale_sources_block",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.coverage_gap_count == d("1")
    assert watched.freshness_gap_count == d("1")
    assert watched.reason_codes == (
        "research_information_source_gap_closure_missing_sources_watch",
        "research_information_source_gap_closure_stale_sources_watch",
    )

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.reason_codes == (
        "research_information_source_gap_closure_pass",
    )

    assert payload == permuted_payload
    assert payload["public_digest"] == report.public_digest
    assert payload["rows"][0]["coverage_ratio"] == "0.400000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_empty_gap_closure_report_is_pass_and_report_only() -> None:
    module = api()
    local_generated_at = datetime(
        2026,
        7,
        8,
        10,
        30,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    report = _build_report(generated_at=local_generated_at)
    payload = module.research_information_source_gap_closure_report_to_payload(report)

    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.reason_codes == (
        "research_information_source_gap_closure_no_inputs",
    )
    assert report.domain_team_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.missing_source_count == d("0")
    assert report.stale_source_count == d("0")
    assert report.average_coverage_ratio == d("0.000000")
    assert report.minimum_fresh_ratio == d("0.000000")
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-08T14:30:00+00:00"
    assert payload["status"] == "pass"
    assert payload["rows"] == []
    assert payload["public_digest"] == report.public_digest
    assert _float_paths(payload) == ()


def test_decimal_frozen_flags_and_consistency_are_validated() -> None:
    module = api()
    report = _build_report(_coverage())

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report, status="ready")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="required_source_count must be a Decimal"):
        _coverage(required_source_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="available_source_count must be finite"):
        _coverage(available_source_count=Decimal("NaN"))
    with pytest.raises(ValueError, match="fresh_source_count must be nonnegative"):
        _coverage(fresh_source_count=d("-1"))
    with pytest.raises(ValueError, match="stale_source_count must be integral"):
        _coverage(stale_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="watch_coverage_ratio must be between 0 and 1"):
        _config(watch_coverage_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="block_stale_age_hours"):
        _config(
            watch_stale_age_hours=d("200.000000"),
            block_stale_age_hours=d("100.000000"),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_information_source_gap_closure_report(
            (_coverage(),),
            config=_config(),
            generated_at=datetime(2026, 7, 8, 14, 30),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.ResearchInformationSourceGapClosureConfig(readonly=False)
    with pytest.raises(ValueError, match="public_digest"):
        replace(report, public_digest="0" * 64)
    with pytest.raises(ValueError, match="rows must be sorted"):
        unordered = _build_report(
            _coverage("z_domain", "z_team", "z_family"),
            _coverage("a_domain", "a_team", "a_family"),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_contract_rejects_sensitive_names_and_duplicate_groups() -> None:
    module = api()
    report = _build_report(_coverage())
    unsafe_values = (
        "raw_" + "source_" + "ref",
        "source_" + "url",
        "source_" + "text",
        "market_" + "id",
        "market_" + "slug",
        "question",
        "dsn",
        "to" + "ken",
        "wal" + "let",
        "ord" + "er",
        "trade",
        "buy",
        "sell",
        "au" + "th",
        "private_" + "key",
    )

    for unsafe_value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public value"):
            _coverage(unsafe_value, "policy_research", "public_calendar")
        with pytest.raises(ValueError, match="unsafe public value"):
            _coverage("macro_policy", unsafe_value, "public_calendar")
        with pytest.raises(ValueError, match="unsafe public value"):
            _coverage("macro_policy", "policy_research", unsafe_value)

    with pytest.raises(ValueError, match="duplicate domain/team/source family"):
        _build_report(_coverage(), _coverage())
    with pytest.raises(ValueError, match="report must be"):
        module.research_information_source_gap_closure_report_to_payload(object())
    with pytest.raises(ValueError, match="report must be"):
        module.research_information_source_gap_closure_digest(object())

    public_text = repr(module.research_information_source_gap_closure_report_to_payload(report))
    for unsafe_value in unsafe_values:
        assert unsafe_value not in public_text
    for row in report.rows:
        for field in fields(row):
            if field.name.endswith(("_count", "_hours", "_ratio")):
                assert type(getattr(row, field.name)) is Decimal


def test_public_api_has_no_external_or_private_execution_surfaces() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_INFORMATION_SOURCE_GAP_CLOSURE_CONFIG_VERSION",
        "ResearchInformationSourceGapClosureAction",
        "ResearchInformationSourceGapClosureConfig",
        "ResearchInformationSourceGapClosureInput",
        "ResearchInformationSourceGapClosureReport",
        "build_research_information_source_gap_closure_report",
        "research_information_source_gap_closure_digest",
        "research_information_source_gap_closure_report_to_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    public_field_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_names.add(getattr(node.func, "attr", getattr(node.func, "id", "")))
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float

    for dataclass_type in (
        module.ResearchInformationSourceGapClosureInput,
        module.ResearchInformationSourceGapClosureAction,
        module.ResearchInformationSourceGapClosureReport,
    ):
        public_field_names.update(field.name for field in fields(dataclass_type))

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    forbidden_calls = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "float",
        "__import__",
    }
    forbidden_public_field_fragments = (
        "raw_source_ref",
        "source_url",
        "source_text",
        "market_id",
        "market_slug",
        "question",
        "dsn",
        "token",
        "wallet",
        "order",
        "auth",
        "private_key",
    )

    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not (call_names & forbidden_calls)
    assert not any(
        fragment in field_name
        for field_name in public_field_names
        for fragment in forbidden_public_field_fragments
    )


def _float_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if isinstance(value, float):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    return ()
