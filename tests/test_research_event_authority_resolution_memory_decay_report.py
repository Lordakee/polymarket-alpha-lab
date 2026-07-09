from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_event_authority_resolution_memory_decay_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_authority_resolution_memory_decay_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "authority_reliability_watch_below": d("0.700000"),
        "authority_reliability_block_below": d("0.400000"),
        "resolution_age_watch_seconds": d("3600.000000"),
        "resolution_age_block_seconds": d("10800.000000"),
        "memory_age_watch_seconds": d("7200.000000"),
        "memory_age_block_seconds": d("21600.000000"),
        "parser_confidence_watch_below": d("0.800000"),
        "parser_confidence_block_below": d("0.500000"),
        "evidence_quorum_watch_count": d("2.000000"),
        "conflict_watch_threshold": d("0.300000"),
        "conflict_block_threshold": d("0.600000"),
    }
    values.update(overrides)
    return module.ResearchEventAuthorityResolutionMemoryDecayConfig(**values)


def event(
    seed: str,
    *,
    parsed_at: datetime | None = None,
    authority_reliability_score: Decimal = d("0.900000"),
    resolution_age_seconds: Decimal = d("900.000000"),
    memory_age_seconds: Decimal = d("1800.000000"),
    parser_confidence_score: Decimal = d("0.950000"),
    evidence_count: Decimal = d("3.000000"),
    conflict_score: Decimal = d("0.050000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchEventAuthorityResolutionMemoryDecayInput(
        event_digest=digest(f"{seed}-event"),
        authority_digest=digest(f"{seed}-authority"),
        parsed_at=parsed_at or (GENERATED_AT - timedelta(minutes=20)),
        authority_reliability_score=authority_reliability_score,
        resolution_age_seconds=resolution_age_seconds,
        memory_age_seconds=memory_age_seconds,
        parser_confidence_score=parser_confidence_score,
        evidence_count=evidence_count,
        conflict_score=conflict_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_event_authority_resolution_memory_decay_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_builds_report_only_memory_decay_report_with_pass_watch_block_rows() -> None:
    module = api()
    result = build_report(
        event("pass"),
        event(
            "watch",
            authority_reliability_score=d("0.650000"),
            resolution_age_seconds=d("7200.000000"),
            memory_age_seconds=d("10000.000000"),
            parser_confidence_score=d("0.750000"),
            evidence_count=d("1.000000"),
            conflict_score=d("0.350000"),
        ),
        event(
            "block",
            parsed_at=(GENERATED_AT - timedelta(hours=2)).astimezone(
                timezone(timedelta(hours=-4)),
            ),
            authority_reliability_score=d("0.350000"),
            resolution_age_seconds=d("12000.000000"),
            memory_age_seconds=d("25000.000000"),
            parser_confidence_score=d("0.450000"),
            evidence_count=d("0.000000"),
            conflict_score=d("0.700000"),
        ),
    )

    assert type(result) is module.ResearchEventAuthorityResolutionMemoryDecayReport
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        module.DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_DECAY_REPORT_CONFIG_VERSION
    )
    assert module.RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_DECAY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert result.status == "block"
    assert result.event_count == d("3.000000")
    assert result.pass_event_count == d("1.000000")
    assert result.watch_event_count == d("1.000000")
    assert result.block_event_count == d("1.000000")
    assert result.weak_authority_count == d("2.000000")
    assert result.stale_resolution_count == d("2.000000")
    assert result.decayed_memory_count == d("2.000000")
    assert result.low_parser_confidence_count == d("2.000000")
    assert result.thin_evidence_quorum_count == d("2.000000")
    assert result.conflict_pressure_count == d("2.000000")
    assert result.highest_authority_resolution_memory_decay_score == d("0.816667")
    assert result.oldest_resolution_age_seconds == d("12000.000000")
    assert result.oldest_memory_age_seconds == d("25000.000000")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64

    assert tuple((row.status, row.event_digest) for row in result.rows) == (
        ("block", digest("block-event")),
        ("watch", digest("watch-event")),
        ("pass", digest("pass-event")),
    )

    blocked, watched, passed = result.rows
    assert blocked.parsed_at == GENERATED_AT - timedelta(hours=2)
    assert blocked.observation_age_seconds == d("7200.000000")
    assert blocked.authority_reliability_band == "weak"
    assert blocked.resolution_freshness_band == "expired"
    assert blocked.memory_decay_band == "expired"
    assert blocked.parser_confidence_band == "low"
    assert blocked.evidence_quorum_band == "missing"
    assert blocked.conflict_band == "conflicted"
    assert blocked.authority_resolution_memory_decay_score == d("0.816667")
    assert blocked.reason_codes == (
        "authority_reliability_block",
        "resolution_age_block",
        "memory_age_block",
        "parser_confidence_block",
        "evidence_quorum_block",
        "conflict_pressure_block",
    )

    assert watched.status == "watch"
    assert watched.authority_reliability_band == "thin"
    assert watched.resolution_freshness_band == "stale"
    assert watched.memory_decay_band == "stale"
    assert watched.parser_confidence_band == "thin"
    assert watched.evidence_quorum_band == "thin"
    assert watched.conflict_band == "elevated"
    assert watched.authority_resolution_memory_decay_score == d("0.429938")
    assert watched.reason_codes == (
        "authority_reliability_watch",
        "resolution_age_watch",
        "memory_age_watch",
        "parser_confidence_watch",
        "evidence_quorum_watch",
        "conflict_pressure_watch",
    )

    assert passed.status == "pass"
    assert passed.authority_reliability_band == "trusted"
    assert passed.resolution_freshness_band == "fresh"
    assert passed.memory_decay_band == "fresh"
    assert passed.parser_confidence_band == "strong"
    assert passed.evidence_quorum_band == "covered"
    assert passed.conflict_band == "clear"
    assert passed.authority_resolution_memory_decay_score == d("0.061111")
    assert passed.reason_codes == ("event_authority_resolution_memory_decay_clear",)


def test_empty_report_payload_is_deterministic_decimal_safe_and_digest_validated() -> None:
    module = api()
    result = build_report()

    assert result.status == "pass"
    assert result.event_count == d("0.000000")
    assert result.reason_codes == (
        "research_event_authority_resolution_memory_decay_empty",
    )
    assert result.rows == ()
    assert result.highest_authority_resolution_memory_decay_score == d("0.000000")
    assert (
        result.derived_validation_digest
        == module.research_event_authority_resolution_memory_decay_report_digest(result)
    )
    module.validate_research_event_authority_resolution_memory_decay_report_digest(
        result,
    )

    payload = result.payload
    assert payload == module.research_event_authority_resolution_memory_decay_report_payload(
        result,
    )
    assert payload["event_count"] == "0.000000"
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert_no_numeric_objects(payload)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    assert_payload_has_no_leaked_values(payload)
    for forbidden in unsafe_public_field_names() | {"http://", "https://", "://"}:
        assert forbidden not in encoded.lower()

    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        unsigned_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert hashlib.sha256(canonical.encode()).hexdigest() == payload[
        "derived_validation_digest"
    ]


def test_payload_order_is_stable_and_rejects_public_leakage_or_digest_tampering() -> None:
    module = api()
    block = event(
        "block",
        authority_reliability_score=d("0.350000"),
        resolution_age_seconds=d("12000.000000"),
        memory_age_seconds=d("25000.000000"),
        parser_confidence_score=d("0.450000"),
        evidence_count=d("0.000000"),
        conflict_score=d("0.700000"),
    )
    passed = event("pass")
    report_a = build_report(passed, block)
    report_b = build_report(block, passed)
    payload_a = module.research_event_authority_resolution_memory_decay_report_payload(
        report_a,
    )
    payload_b = module.research_event_authority_resolution_memory_decay_report_payload(
        report_b,
    )

    assert payload_a == payload_b
    assert payload_a["derived_validation_digest"] == payload_b[
        "derived_validation_digest"
    ]
    assert payload_a["rows"][0]["authority_resolution_memory_decay_score"] == "0.816667"
    payload_text = json.dumps(payload_a, sort_keys=True)
    assert "block-event" not in payload_text
    assert "pass-event" not in payload_text

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)
    with pytest.raises(FrozenInstanceError):
        report_a.rows[0].status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_event_authority_resolution_memory_decay_report_payload(
            {**payload_a, "raw_candidate_id": "hidden"},
        )
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_event_authority_resolution_memory_decay_report_payload(
            {**payload_a, "source_url": "https://example.invalid/private"},
        )
    with pytest.raises(ValueError, match="numeric values"):
        module.research_event_authority_resolution_memory_decay_report_payload(
            {**payload_a, "event_count": 2},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.research_event_authority_resolution_memory_decay_report_payload(
            {**payload_a, "readonly": False},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_authority_resolution_memory_decay_report_payload(
            {**payload_a, "event_count": "9.000000"},
        )


def test_validation_requires_digest_inputs_decimal_inputs_flags_and_safe_statuses() -> None:
    module = api()

    with pytest.raises(ValueError, match="sha-256"):
        module.ResearchEventAuthorityResolutionMemoryDecayInput(
            event_digest=_join_parts("raw-", "candidate", "-id"),
            authority_digest=digest("authority"),
            parsed_at=GENERATED_AT,
            authority_reliability_score=d("0.900000"),
            resolution_age_seconds=d("900.000000"),
            memory_age_seconds=d("1800.000000"),
            parser_confidence_score=d("0.950000"),
            evidence_count=d("3.000000"),
            conflict_score=d("0.050000"),
        )
    with pytest.raises(ValueError, match="authority_reliability_score must be a Decimal"):
        event("bad-decimal", authority_reliability_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_reliability_score must be a Decimal"):
        event(
            "bad-subclass",
            authority_reliability_score=_DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="six decimal places"):
        event("bad-scale", evidence_count=d("3.0"))
    with pytest.raises(ValueError, match="integer Decimal"):
        event("bad-count", evidence_count=d("1.500000"))
    with pytest.raises(ValueError, match="between zero and one"):
        event("bad-ratio-range", conflict_score=d("1.000001"))
    with pytest.raises(ValueError, match="parsed_at must be timezone-aware"):
        event("bad-time", parsed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="parsed_at must not be after generated_at"):
        build_report(event("bad-future", parsed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        event("bad-paper", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        event("bad-report", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        event("bad-readonly", readonly=False)
    with pytest.raises(ValueError, match="authority_reliability_block_below"):
        config(authority_reliability_block_below=d("0.800000"))
    with pytest.raises(ValueError, match="resolution_age_block_seconds"):
        config(resolution_age_block_seconds=d("3600.000000"))
    with pytest.raises(ValueError, match="parser_confidence_block_below"):
        config(parser_confidence_block_below=d("0.900000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_authority_resolution_memory_decay_report(
            (),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="config must be"):
        module.build_research_event_authority_resolution_memory_decay_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    duplicate = event("duplicate")
    with pytest.raises(ValueError, match="unique"):
        build_report(duplicate, duplicate)

    result = build_report(event("valid"))
    with pytest.raises(ValueError, match="status"):
        replace(result, status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status="blocked")
    with pytest.raises(ValueError, match="authority_resolution_memory_decay_score"):
        replace(result.rows[0], authority_resolution_memory_decay_score=d("0.999999"))


def test_exports_frozen_dataclasses_and_contains_no_execution_surfaces() -> None:
    module = api()
    result = build_report(event("valid"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_DECAY_REPORT_CONFIG_VERSION",
        "RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_DECAY_STATUSES",
        "ResearchEventAuthorityResolutionMemoryDecayConfig",
        "ResearchEventAuthorityResolutionMemoryDecayInput",
        "ResearchEventAuthorityResolutionMemoryDecayReport",
        "ResearchEventAuthorityResolutionMemoryDecayRow",
        "build_research_event_authority_resolution_memory_decay_report",
        "research_event_authority_resolution_memory_decay_report_digest",
        "research_event_authority_resolution_memory_decay_report_payload",
        "validate_research_event_authority_resolution_memory_decay_public_payload",
        "validate_research_event_authority_resolution_memory_decay_report_digest",
    )
    assert is_dataclass(config())
    assert is_dataclass(event("valid"))
    assert is_dataclass(result)
    assert is_dataclass(result.rows[0])
    assert config().__dataclass_params__.frozen is True
    assert event("valid").__dataclass_params__.frozen is True
    assert result.__dataclass_params__.frozen is True
    assert result.rows[0].__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().resolution_age_watch_seconds = d("1.000000")

    public_fields = {
        field.name
        for cls in (type(result), type(result.rows[0]), type(event("valid")))
        for field in fields(cls)
    }
    assert unsafe_public_field_names().isdisjoint(public_fields)
    for public_field in public_fields:
        assert not contains_forbidden_public_surface(public_field)

    source_text = MODULE_PATH.read_text()
    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    called_names: set[str] = set()
    assigned_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            called_names.add(getattr(node.func, "attr", getattr(node.func, "id", "")))
        if isinstance(node, ast.Name):
            assigned_names.add(node.id)

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
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not called_names.intersection(
        {
            "connect",
            "execute",
            "executemany",
            "open",
            "request",
            "post",
            "put",
            "patch",
            "delete",
            "commit",
            "rollback",
            "place_order",
            "submit_order",
            "cancel_order",
            "size_position",
            "recommend",
        },
    )
    assert not assigned_names.intersection(
        {
            "live_trading",
            "wallet",
            "login",
            "credential",
            "order_client",
            "network_client",
            "database",
            "persistence",
            "position_size",
            "recommendation",
        },
    )
    for forbidden in (
        "candidate",
        "market",
        _join_parts("sour", "ce"),
        _join_parts("ur", "l"),
        _join_parts("te", "xt"),
        "dsn",
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("siz", "ing"),
        _join_parts("recomm", "endation"),
    ):
        assert forbidden not in source_text.lower()


def assert_no_numeric_objects(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_objects(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_numeric_objects(item)
    else:
        assert type(value) not in (Decimal, int, float)


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "candidate-",
        "candidate_id",
        "market-",
        "market_id",
        "market_slug",
        "market_question",
        _join_parts("que", "stion"),
        _join_parts("sour", "ce_", "te", "xt"),
        _join_parts("sour", "ce_", "ur", "l"),
        "dsn",
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)


def unsafe_public_field_names() -> set[str]:
    return {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        _join_parts("sour", "ce_", "ur", "l"),
        _join_parts("sour", "ce_", "te", "xt"),
        "dsn",
        _join_parts("ta", "ble", "_name"),
        _join_parts("to", "ken"),
    }


def contains_forbidden_public_surface(value: str) -> bool:
    lowered = value.lower()
    if any(
        phrase in lowered
        for phrase in (
            _join_parts("candidate", "_", "id"),
            _join_parts("market", "_", "id"),
            _join_parts("market", "_", "slug"),
            _join_parts("sour", "ce", "_", "ur", "l"),
            _join_parts("sour", "ce", "_", "te", "xt"),
            _join_parts("ta", "ble", "_name"),
        )
    ):
        return True
    tokens = tuple(token for token in lowered.replace("_", " ").split() if token)
    forbidden_tokens = frozenset(
        (
            "candidate",
            "market",
            _join_parts("que", "stion"),
            "url",
            "text",
            "dsn",
            _join_parts("ta", "ble"),
            _join_parts("to", "ken"),
        ),
    )
    return any(token in forbidden_tokens for token in tokens)
