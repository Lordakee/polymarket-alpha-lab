from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 30, tzinfo=UTC)
MEMORY_REFRESHED_AT = datetime(2026, 7, 8, 6, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_specialist_coverage_map_report.py",
)
EXPECTED_DOMAINS = (
    "politics",
    "crypto",
    "equities",
    "commodities",
    "football",
    "basketball",
    "other",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_coverage_map_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    return api().ResearchTeamSpecialistCoverageMapConfig(**overrides)


def specialist(
    domain_label: str = "politics",
    *,
    specialist_team_label: str = "team_politics",
    observed_at: datetime = OBSERVED_AT,
    memory_refreshed_at: datetime = MEMORY_REFRESHED_AT,
    active_specialist_count: Decimal = d("2"),
    backup_specialist_count: Decimal = d("1"),
    assigned_packet_count: Decimal = d("4"),
    calibration_error_score: Decimal = d("0.050000"),
    coverage_confidence_score: Decimal = d("0.900000"),
    **overrides: object,
):
    values = {
        "domain_label": domain_label,
        "specialist_team_label": specialist_team_label,
        "observed_at": observed_at,
        "memory_refreshed_at": memory_refreshed_at,
        "active_specialist_count": active_specialist_count,
        "backup_specialist_count": backup_specialist_count,
        "assigned_packet_count": assigned_packet_count,
        "calibration_error_score": calibration_error_score,
        "coverage_confidence_score": coverage_confidence_score,
    }
    values.update(overrides)
    return api().ResearchTeamSpecialistCoverageMapInput(**values)


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    return api().build_research_team_specialist_coverage_map_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_coverage_map_rolls_up_required_domains_and_validates_digest() -> None:
    items = (
        specialist("politics", specialist_team_label="team_politics"),
        specialist(
            "crypto",
            specialist_team_label="team_crypto",
            active_specialist_count=d("1"),
            assigned_packet_count=d("10"),
            memory_refreshed_at=GENERATED_AT - timedelta(hours=48),
            calibration_error_score=d("0.150000"),
            coverage_confidence_score=d("0.650000"),
        ),
        specialist(
            "commodities",
            specialist_team_label="team_commodities",
            active_specialist_count=d("0"),
            backup_specialist_count=d("0"),
            assigned_packet_count=d("18"),
            memory_refreshed_at=GENERATED_AT - timedelta(hours=96),
            calibration_error_score=d("0.300000"),
            coverage_confidence_score=d("0.400000"),
        ),
        specialist("football", specialist_team_label="team_football"),
    )

    summary = build_report(
        *items,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    reversed_summary = build_report(*reversed(items))

    assert api().COVERAGE_MAP_STATUSES == ("pass", "watch", "block")
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == "research-team-specialist-coverage-map-report-v0"
    assert summary.status == "block"
    assert summary.paper_queue_action == "paper_specialist_coverage_map_block"
    assert summary.domain_count == d("7.000000")
    assert summary.covered_domain_count == d("4.000000")
    assert summary.missing_domain_count == d("3.000000")
    assert summary.pass_count == d("2.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("4.000000")
    assert summary.coverage_gap_domain_count == d("5.000000")
    assert summary.stale_memory_domain_count == d("2.000000")
    assert summary.overloaded_domain_count == d("2.000000")
    assert summary.weak_calibration_domain_count == d("2.000000")
    assert summary.max_memory_age_hours == d("96.000000")
    assert summary.max_assigned_packet_count == d("18.000000")
    assert summary.max_calibration_error_score == d("0.300000")
    assert summary.min_coverage_confidence_score == d("0.000000")
    assert len(summary.derived_validation_digest) == 64
    int(summary.derived_validation_digest, 16)

    assert tuple(row.domain_label for row in summary.rows) == EXPECTED_DOMAINS
    by_domain = {row.domain_label: row for row in summary.rows}
    assert by_domain["politics"].coverage_status == "pass"
    assert by_domain["politics"].reason_codes == ("specialist_coverage_clear",)
    assert by_domain["crypto"].coverage_status == "watch"
    assert by_domain["crypto"].memory_age_hours == d("48.000000")
    assert by_domain["crypto"].reason_codes == (
        "specialist_coverage_depth_watch",
        "specialist_coverage_memory_stale_watch",
        "specialist_coverage_overload_watch",
        "specialist_coverage_calibration_watch",
        "specialist_coverage_confidence_watch",
    )
    assert by_domain["commodities"].coverage_status == "block"
    assert by_domain["commodities"].reason_codes == (
        "specialist_coverage_depth_block",
        "specialist_coverage_memory_stale_block",
        "specialist_coverage_overload_block",
        "specialist_coverage_calibration_block",
        "specialist_coverage_confidence_block",
    )
    assert by_domain["equities"].coverage_status == "block"
    assert by_domain["equities"].specialist_team_label == "unassigned"
    assert by_domain["equities"].reason_codes == ("specialist_coverage_missing_block",)
    assert summary.reason_codes == (
        "specialist_coverage_report_block",
        "specialist_coverage_missing_block",
        "specialist_coverage_depth_block",
        "specialist_coverage_memory_stale_block",
        "specialist_coverage_overload_block",
        "specialist_coverage_calibration_block",
        "specialist_coverage_confidence_block",
        "specialist_coverage_depth_watch",
        "specialist_coverage_memory_stale_watch",
        "specialist_coverage_overload_watch",
        "specialist_coverage_calibration_watch",
        "specialist_coverage_confidence_watch",
    )

    payload = api().research_team_specialist_coverage_map_report_payload(summary)
    reversed_payload = api().research_team_specialist_coverage_map_report_payload(
        reversed_summary,
    )
    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert api().research_team_specialist_coverage_map_report_digest(summary) == (
        payload["derived_validation_digest"]
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["domain_count"] == "7.000000"
    assert payload["rows"][0]["domain_label"] == "politics"
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_empty_coverage_map_blocks_all_required_domains() -> None:
    summary = build_report()

    assert summary.status == "block"
    assert summary.paper_queue_action == "paper_specialist_coverage_map_block"
    assert summary.domain_count == d("7.000000")
    assert summary.covered_domain_count == d("0.000000")
    assert summary.missing_domain_count == d("7.000000")
    assert summary.pass_count == d("0.000000")
    assert summary.watch_count == d("0.000000")
    assert summary.block_count == d("7.000000")
    assert tuple(row.domain_label for row in summary.rows) == EXPECTED_DOMAINS
    assert all(row.coverage_status == "block" for row in summary.rows)
    assert all(
        row.reason_codes == ("specialist_coverage_missing_block",)
        for row in summary.rows
    )
    assert summary.reason_codes == (
        "specialist_coverage_report_block",
        "specialist_coverage_missing_block",
    )
    assert summary.reason_code_counts == (
        api().ResearchTeamSpecialistCoverageMapReasonCodeCount(
            reason_code="specialist_coverage_missing_block",
            count=d("7.000000"),
            domain_ratio=d("1.000000"),
        ),
    )


def test_coverage_map_is_report_only_public_safe_and_decimal_strict() -> None:
    module = api()
    cfg = config()
    signal = specialist("basketball", specialist_team_label="team_basketball")
    summary = build_report(signal, cfg=cfg)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIST_COVERAGE_MAP_REPORT_CONFIG_VERSION",
        "COVERAGE_MAP_STATUSES",
        "COVERAGE_MAP_DOMAINS",
        "ResearchTeamSpecialistCoverageMapConfig",
        "ResearchTeamSpecialistCoverageMapInput",
        "ResearchTeamSpecialistCoverageMapReasonCodeCount",
        "ResearchTeamSpecialistCoverageMapReport",
        "ResearchTeamSpecialistCoverageMapRow",
        "build_research_team_specialist_coverage_map_report",
        "research_team_specialist_coverage_map_report_digest",
        "research_team_specialist_coverage_map_report_payload",
    )
    assert module.COVERAGE_MAP_DOMAINS == EXPECTED_DOMAINS
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        summary.rows[0].coverage_status = "watch"  # type: ignore[misc]

    for value in (cfg, signal, summary, *summary.rows, *summary.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_score", "_ratio", "_hours", "_seconds")):
                assert type(item) is Decimal

    with pytest.raises(ValueError, match="active_specialist_count must be a Decimal"):
        specialist(active_specialist_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="calibration_error_score must be a Decimal"):
        specialist(calibration_error_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="coverage_confidence_score must be a Decimal"):
        specialist(coverage_confidence_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        specialist(observed_at=datetime(2026, 7, 8, 11, 30))
    with pytest.raises(ValueError, match="memory_refreshed_at must be a datetime"):
        specialist(memory_refreshed_at=_DateTimeSubclass(2026, 7, 8, 10, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        build_report(specialist(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="future"):
        build_report(specialist(memory_refreshed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="domain_label"):
        specialist("soccer")
    with pytest.raises(ValueError, match="specialist_team_label"):
        specialist(specialist_team_label="market_slug")
    with pytest.raises(ValueError, match="unique"):
        build_report(
            specialist("politics", specialist_team_label="team_politics_a"),
            specialist("politics", specialist_team_label="team_politics_b"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        specialist(paper_only=False)
    with pytest.raises(ValueError, match="max_watch_assigned_packet_count"):
        config(
            max_pass_assigned_packet_count=d("12.000000"),
            max_watch_assigned_packet_count=d("8.000000"),
        )
    with pytest.raises(ValueError, match="min_watch_coverage_confidence_score"):
        config(
            min_pass_coverage_confidence_score=d("0.400000"),
            min_watch_coverage_confidence_score=d("0.600000"),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, pass_count=d("7.000000"))


def test_public_payload_rejects_raw_identifiers_tampering_and_unsafe_surfaces() -> None:
    module = api()
    summary = build_report(specialist("politics", specialist_team_label="team_politics"))
    payload = module.research_team_specialist_coverage_map_report_payload(summary)
    payload_text = repr(payload).lower()

    forbidden = (
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
        assert token_value not in payload_text

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_coverage_map_report_payload(tampered)

    for unsafe_key, unsafe_value in (
        ("candidate_id", "opaque"),
        ("market_slug", "will-fed-cut-rates"),
        ("question", "Will this resolve yes?"),
        ("source_url", "https://example.test/item"),
        ("dsn", "postgres://example"),
        ("wallet", "0xabc"),
        ("order_ticket", "abc"),
        ("sizing", "100"),
        ("recommendation", "buy"),
        ("auth_header", "paper"),
        ("execution_endpoint", "paper"),
        ("live_trading_surface", "paper"),
        ("network_request", "paper"),
    ):
        leaked = dict(payload)
        leaked[unsafe_key] = unsafe_value
        leaked["derived_validation_digest"] = canonical_digest(leaked)
        with pytest.raises(ValueError, match="unsafe"):
            module.research_team_specialist_coverage_map_report_payload(leaked)

    numeric = dict(payload)
    numeric["domain_count"] = 7
    numeric["derived_validation_digest"] = canonical_digest(numeric)
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_specialist_coverage_map_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    downgraded["derived_validation_digest"] = canonical_digest(downgraded)
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_specialist_coverage_map_report_payload(downgraded)

    object.__setattr__(summary.rows[0], "active_specialist_count", d("99.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_coverage_map_report_payload(summary)


def test_public_payload_requires_exact_schema_even_when_resigned() -> None:
    module = api()
    summary = build_report(specialist("politics", specialist_team_label="team_politics"))
    payload = module.research_team_specialist_coverage_map_report_payload(summary)

    def extra_report_field(value: dict[str, Any]) -> None:
        value["public_note"] = "coverage"

    def missing_report_field(value: dict[str, Any]) -> None:
        value.pop("status")

    def extra_row_field(value: dict[str, Any]) -> None:
        value["rows"][0]["public_note"] = "coverage"

    def missing_row_field(value: dict[str, Any]) -> None:
        value["rows"][0].pop("coverage_status")

    def extra_reason_count_field(value: dict[str, Any]) -> None:
        value["reason_code_counts"][0]["public_note"] = "coverage"

    for mutate in (
        extra_report_field,
        missing_report_field,
        extra_row_field,
        missing_row_field,
        extra_reason_count_field,
    ):
        changed = json.loads(json.dumps(payload))
        mutate(changed)
        changed["derived_validation_digest"] = canonical_digest(changed)
        with pytest.raises(ValueError, match="schema"):
            module.research_team_specialist_coverage_map_report_payload(changed)


def test_public_payload_revalidates_nested_flags_and_report_semantics() -> None:
    module = api()
    summary = build_report(specialist("politics", specialist_team_label="team_politics"))
    payload = module.research_team_specialist_coverage_map_report_payload(summary)

    downgraded = json.loads(json.dumps(payload))
    downgraded["rows"][0]["readonly"] = False
    downgraded["derived_validation_digest"] = canonical_digest(downgraded)
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_specialist_coverage_map_report_payload(downgraded)

    inconsistent = json.loads(json.dumps(payload))
    inconsistent["status"] = "pass"
    inconsistent["paper_queue_action"] = "paper_specialist_coverage_map_monitor"
    inconsistent["reason_codes"] = ["specialist_coverage_report_pass"]
    inconsistent["derived_validation_digest"] = canonical_digest(inconsistent)
    with pytest.raises(ValueError, match="status must match rows"):
        module.research_team_specialist_coverage_map_report_payload(inconsistent)


def test_module_is_report_only_without_external_write_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
        "write_text",
        "write_bytes",
        "float",
        "__import__",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float


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
