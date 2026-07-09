import ast
import copy
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report_module():
    return import_module(
        "polymarket_alpha_lab."
        "research_event_authority_source_memory_floor_report",
    )


def observation(
    *,
    candidate_reference: str = (
        "Will the raw candidate resolve from "
        "https://candidate.example/private?token=secret"
    ),
    market_reference: str = "prod_events_table:market_123",
    authority_reference: str = "https://authority.example/doc?token=secret",
    authority_family: str = "official-disclosure",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    memory_score: Decimal = d("0.820000"),
    confidence_score: Decimal = d("0.910000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = report_module()
    return module.ResearchEventAuthoritySourceMemoryObservation(
        candidate_reference=candidate_reference,
        market_reference=market_reference,
        authority_reference=authority_reference,
        authority_family=authority_family,
        observed_at=observed_at,
        memory_score=memory_score,
        confidence_score=confidence_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**overrides):
    module = report_module()
    values = {
        "config_version": "authority-source-memory-floor-v0",
        "min_authority_count": d("2"),
        "min_authority_family_count": d("2"),
        "pass_memory_floor": d("0.700000"),
        "watch_memory_floor": d("0.400000"),
        "min_confidence_floor": d("0.500000"),
        "stale_age_seconds": d("86400"),
    }
    values.update(overrides)
    return module.ResearchEventAuthoritySourceMemoryFloorConfig(**values)


def build_report(*observations, report_config=None, generated_at=GENERATED_AT):
    module = report_module()
    return module.build_research_event_authority_source_memory_floor_report(
        observations,
        config=report_config or config(),
        generated_at=generated_at,
    )


def public_payload(report):
    module = report_module()
    return module.research_event_authority_source_memory_floor_public_payload(report)


def digest_payload(payload):
    unsigned_payload = copy.deepcopy(payload)
    digest = unsigned_payload.pop("payload_sha256")
    canonical = json.dumps(
        unsigned_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return digest, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def resign_payload(payload):
    resigned_payload = copy.deepcopy(payload)
    resigned_payload["payload_sha256"] = ""
    resigned_payload["payload_sha256"] = digest_payload(resigned_payload)[1]
    return resigned_payload


def walk_json_strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_json_strings(item)
    elif isinstance(value, str):
        yield value


def field_values(instance):
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_builds_deterministic_report_only_payload_with_valid_digest():
    raw_candidate = "Candidate raw text https://candidate.example/path?token=secret"
    raw_market = "postgres://prod_dsn/events_table/market_123"
    raw_authority_a = "https://source.example/a?token=abc"
    raw_authority_b = "https://source.example/b?token=def"

    first = observation(
        candidate_reference=raw_candidate,
        market_reference=raw_market,
        authority_reference=raw_authority_a,
        authority_family="official-disclosure",
        memory_score=d("0.820000"),
        confidence_score=d("0.910000"),
    )
    second = observation(
        candidate_reference=raw_candidate,
        market_reference=raw_market,
        authority_reference=raw_authority_b,
        authority_family="regulatory-filing",
        memory_score=d("0.760000"),
        confidence_score=d("0.880000"),
    )

    report = build_report(first, second)
    reversed_report = build_report(second, first)

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.status == "pass"
    assert report.event_count == d("1.000000")
    assert report.authority_observation_count == d("2.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.reason_codes == ("all_events_pass_memory_floor",)
    assert len(report.rows) == 1

    row = report.rows[0]
    assert row.status == "pass"
    assert row.event_key != raw_candidate
    assert len(row.event_key) == 64
    assert row.authority_count == d("2.000000")
    assert row.authority_family_count == d("2.000000")
    assert row.memory_floor_score == d("0.760000")
    assert row.average_memory_score == d("0.790000")
    assert row.confidence_floor_score == d("0.880000")
    assert row.reason_codes == ("event_memory_floor_pass",)

    payload = public_payload(report)
    assert payload == public_payload(reversed_report)
    assert payload["payload_sha256"] == report.payload_sha256
    actual_digest, expected_digest = digest_payload(payload)
    assert actual_digest == expected_digest
    assert report_module().validate_research_event_authority_source_memory_floor_payload(
        payload,
    )

    serialized_payload = json.dumps(payload, sort_keys=True)
    for raw_value in (
        raw_candidate,
        raw_market,
        raw_authority_a,
        raw_authority_b,
        "candidate.example",
        "prod_dsn",
        "events_table",
        "token=secret",
        "token=abc",
        "token=def",
    ):
        assert raw_value not in serialized_payload


def test_statuses_are_only_pass_watch_or_block():
    pass_report = build_report(
        observation(authority_reference="authority-a", authority_family="official"),
        observation(authority_reference="authority-b", authority_family="filing"),
    )
    assert pass_report.status == "pass"

    watch_report = build_report(
        observation(
            authority_reference="authority-a",
            authority_family="official",
            memory_score=d("0.620000"),
        ),
        observation(
            authority_reference="authority-b",
            authority_family="filing",
            memory_score=d("0.600000"),
        ),
    )
    assert watch_report.status == "watch"
    assert watch_report.rows[0].status == "watch"
    assert watch_report.rows[0].reason_codes == ("memory_floor_below_pass",)

    block_report = build_report(
        observation(memory_score=d("0.300000")),
    )
    assert block_report.status == "block"
    assert block_report.rows[0].status == "block"
    assert "insufficient_authority_count" in block_report.rows[0].reason_codes

    empty_report = build_report()
    assert empty_report.status == "block"
    assert empty_report.reason_codes == ("no_event_observations",)

    for report in (pass_report, watch_report, block_report, empty_report):
        statuses = {report.status, *(row.status for row in report.rows)}
        assert statuses <= {"pass", "watch", "block"}


def test_constructors_are_frozen_decimal_only_and_validate_consistency():
    module = report_module()
    eastern = timezone(timedelta(hours=-4))
    observed = _DatetimeSubclass(2026, 7, 9, 11, 45, tzinfo=UTC)

    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=observed)
    with pytest.raises(ValueError, match="memory_score"):
        observation(memory_score=_DecimalSubclass("0.8"))
    with pytest.raises(ValueError, match="memory_score"):
        observation(memory_score=d("1.000001"))
    with pytest.raises(ValueError, match="confidence_score"):
        observation(confidence_score=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="min_authority_count"):
        config(min_authority_count=2)
    with pytest.raises(ValueError, match="generated_at"):
        build_report(generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))

    report = build_report(
        observation(
            authority_reference="authority-a",
            authority_family="official",
            observed_at=datetime(2026, 7, 9, 7, 45, tzinfo=eastern),
        ),
        observation(authority_reference="authority-b", authority_family="filing"),
    )
    assert report.generated_at == GENERATED_AT
    assert report.rows[0].newest_age_seconds == d("900.000000")

    rebuilt_row = module.ResearchEventAuthoritySourceMemoryFloorRow(
        **field_values(report.rows[0]),
    )
    rebuilt_report = module.ResearchEventAuthoritySourceMemoryFloorReport(
        **field_values(report),
    )
    assert rebuilt_row == report.rows[0]
    assert rebuilt_report == report

    with pytest.raises(ValueError, match="payload_sha256"):
        replace(report, payload_sha256="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")
    with pytest.raises(ValueError, match="event_count"):
        replace(report, event_count=d("2.000000"))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"


def test_payload_validation_rejects_tampering_and_public_sensitive_surfaces():
    report = build_report(
        observation(authority_reference="authority-a", authority_family="official"),
        observation(authority_reference="authority-b", authority_family="filing"),
    )
    module = report_module()
    payload = public_payload(report)

    tampered_status = copy.deepcopy(payload)
    tampered_status["rows"][0]["status"] = "watch"
    with pytest.raises(ValueError, match="payload_sha256"):
        module.validate_research_event_authority_source_memory_floor_payload(
            tampered_status,
        )

    tampered_raw = copy.deepcopy(payload)
    tampered_raw["rows"][0]["candidate_url"] = "https://candidate.example/raw"
    tampered_raw = resign_payload(tampered_raw)
    with pytest.raises(ValueError, match="public payload"):
        module.validate_research_event_authority_source_memory_floor_payload(
            tampered_raw,
        )

    tampered_numeric = copy.deepcopy(payload)
    tampered_numeric["event_count"] = 1
    tampered_numeric = resign_payload(tampered_numeric)
    with pytest.raises(ValueError, match="public payload numeric values"):
        module.validate_research_event_authority_source_memory_floor_payload(
            tampered_numeric,
        )

    for public_key, public_value in (
        ("wallet_address", "0xabc123"),
        ("order_id", "order-123"),
        ("trade_size", "100"),
        ("position_sizing", "100"),
        ("recommendation", "buy"),
        ("question", "Will a raw event resolve?"),
        ("market_slug", "raw-market-slug"),
    ):
        tampered_surface = copy.deepcopy(payload)
        tampered_surface[public_key] = public_value
        tampered_surface = resign_payload(tampered_surface)
        with pytest.raises(ValueError, match="public payload"):
            module.validate_research_event_authority_source_memory_floor_payload(
                tampered_surface,
            )


def test_module_has_no_live_imports_and_payload_keys_do_not_expose_raw_surfaces():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_authority_source_memory_floor_report.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_modules: list[str] = []
    call_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
            elif isinstance(node.func, ast.Name):
                call_names.append(node.func.id)

    assert set(imported_modules) <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

    forbidden_import_fragments = (
        "api",
        "client",
        "database",
        "exchange",
        "http",
        "network",
        "private",
        "request",
        "session",
        "socket",
        "sql",
        "urllib",
        "wallet",
    )
    for module_name in imported_modules:
        normalized = "".join(
            character for character in module_name.lower() if character.isalnum()
        )
        for fragment in forbidden_import_fragments:
            assert fragment not in normalized
    assert "total_seconds" not in call_names

    report = build_report(
        observation(authority_reference="authority-a", authority_family="official"),
        observation(authority_reference="authority-b", authority_family="filing"),
    )
    payload = public_payload(report)
    forbidden_public_fragments = (
        "candidate",
        "market",
        "source_url",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommend",
        "question",
        "slug",
    )
    for value in walk_json_strings(payload):
        normalized = value.lower()
        for fragment in forbidden_public_fragments:
            assert fragment not in normalized
