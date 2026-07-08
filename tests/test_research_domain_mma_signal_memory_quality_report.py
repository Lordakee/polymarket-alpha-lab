from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_domain_mma_signal_memory_quality_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_domain_mma_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "mma-signal-memory-quality-test",
        "stale_fighter_after_seconds": d("604800.000000"),
        "stale_injury_after_seconds": d("172800.000000"),
        "stale_weight_cut_after_seconds": d("259200.000000"),
        "stale_camp_after_seconds": d("1209600.000000"),
        "stale_matchup_context_after_seconds": d("604800.000000"),
        "conflict_block_threshold_count": d("1"),
        "stale_memory_penalty": d("0.250000"),
        "conflict_penalty": d("0.400000"),
        "min_pass_quality_score": d("0.700000"),
        "min_watch_quality_score": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchDomainMmaSignalMemoryQualityConfig(**values)


def memory(**overrides: object):
    module = api()
    values = {
        "memory_label": "mma-memory-fighter-a",
        "team_label": "mma-research-team",
        "event_label": "mma-event-a",
        "input_family": "fighter",
        "memory_present": True,
        "observed_at": GENERATED_AT - timedelta(hours=12),
        "evidence_count": d("3"),
        "conflicting_evidence_count": d("0"),
        "confidence_score": d("0.820000"),
        "redaction_confirmed": True,
    }
    values.update(overrides)
    return module.ResearchDomainMmaSignalMemoryInput(**values)


def build_report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_domain_mma_signal_memory_quality_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def test_mma_memory_quality_identifies_stale_conflicting_and_missing_inputs() -> None:
    module = api()
    report = build_report(
        memory(memory_label="mma-memory-fighter-ready", input_family="fighter"),
        memory(
            memory_label="mma-memory-injury-stale",
            input_family="injury",
            observed_at=GENERATED_AT - timedelta(days=4),
            confidence_score=d("0.760000"),
        ),
        memory(
            memory_label="mma-memory-camp-conflict",
            input_family="camp",
            conflicting_evidence_count=d("1"),
            confidence_score=d("0.880000"),
        ),
        memory(
            memory_label="mma-memory-weight-cut-missing",
            input_family="weight_cut",
            memory_present=False,
            observed_at=None,
            evidence_count=d("0"),
            confidence_score=d("0.000000"),
        ),
        memory(
            memory_label="mma-memory-matchup-ready",
            input_family="matchup_context",
            observed_at=GENERATED_AT - timedelta(hours=6),
            confidence_score=d("0.900000"),
        ),
    )

    assert type(report) is module.ResearchDomainMmaSignalMemoryQualityReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "mma-signal-memory-quality-test"
    assert report.status == "block"
    assert report.input_count == d("5")
    assert report.row_count == d("5")
    assert report.pass_count == d("2")
    assert report.watch_count == d("1")
    assert report.block_count == d("2")
    assert report.stale_count == d("1")
    assert report.conflict_count == d("1")
    assert report.missing_count == d("1")
    assert report.average_quality_score == d("0.542000")
    assert report.reason_codes == (
        "missing_mma_memory_present",
        "stale_mma_memory_present",
        "conflicting_mma_memory_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.row_status for row in report.rows) == (
        "block",
        "block",
        "watch",
        "pass",
        "pass",
    )
    assert tuple(row.input_family for row in report.rows) == (
        "camp",
        "weight_cut",
        "injury",
        "fighter",
        "matchup_context",
    )
    assert report.rows[0] == module.ResearchDomainMmaSignalMemoryQualityRow(
        memory_label="mma-memory-camp-conflict",
        team_label="mma-research-team",
        event_label="mma-event-a",
        input_family="camp",
        row_status="block",
        memory_present=True,
        memory_age_seconds=d("43200.000000"),
        freshness_limit_seconds=d("1209600.000000"),
        evidence_count=d("3"),
        conflicting_evidence_count=d("1"),
        confidence_score=d("0.880000"),
        stale_memory_penalty=d("0.000000"),
        conflict_penalty=d("0.400000"),
        quality_score=d("0.480000"),
        reason_codes=("conflicting_mma_memory",),
    )
    assert report.rows[1].quality_score == d("0.000000")
    assert report.rows[1].reason_codes == ("missing_mma_memory",)
    assert report.rows[2].memory_age_seconds == d("345600.000000")
    assert report.rows[2].freshness_limit_seconds == d("172800.000000")
    assert report.rows[2].quality_score == d("0.510000")
    assert report.rows[2].reason_codes == ("stale_mma_memory",)


def test_empty_mma_memory_report_blocks_review_without_public_raw_surfaces() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.input_count == d("0")
    assert report.row_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.average_quality_score == d("0.000000")
    assert report.reason_codes == ("no_mma_memory_inputs_supplied",)
    assert report.rows == ()

    payload_text = repr(report.payload).lower()
    for forbidden in _FORBIDDEN_PUBLIC_FRAGMENTS:
        assert forbidden not in payload_text


def test_payload_serializes_decimal_strings_and_validates_sha256_digest() -> None:
    module = api()
    first = build_report(
        memory(
            memory_label="mma-memory-injury-stale",
            input_family="injury",
            observed_at=datetime(
                2026,
                7,
                4,
                1,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
            confidence_score=d("0.760000"),
        ),
        memory(memory_label="mma-memory-fighter-ready", input_family="fighter"),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = build_report(
        memory(memory_label="mma-memory-fighter-ready", input_family="fighter"),
        memory(
            memory_label="mma-memory-injury-stale",
            input_family="injury",
            observed_at=datetime(2026, 7, 4, 8, 0, tzinfo=UTC),
            confidence_score=d("0.760000"),
        ),
    )

    payload = module.research_domain_mma_signal_memory_quality_report_payload(first)
    repeat_payload = module.research_domain_mma_signal_memory_quality_report_payload(
        second,
    )
    unsigned_payload = dict(payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    expected_digest = sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()

    assert payload == first.payload
    assert payload == repeat_payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["input_count"] == "2"
    assert payload["rows"][0]["quality_score"] == "0.510000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert digest == expected_digest
    assert len(first.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in digest)
    assert_no_float_values(payload)
    assert_payload_has_no_forbidden_public_surface(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    tampered = dict(payload)
    tampered["pass_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_domain_mma_signal_memory_quality_report_payload(tampered)

    unsafe = dict(payload)
    unsafe["market_id"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_domain_mma_signal_memory_quality_report_payload(unsafe)

    numeric = dict(payload)
    numeric["input_count"] = 2
    with pytest.raises(ValueError, match="numeric|Decimal"):
        module.research_domain_mma_signal_memory_quality_report_payload(numeric)


def test_dataclasses_are_frozen_decimal_only_public_safe_and_readonly() -> None:
    module = api()
    sample_config = config()
    sample_memory = memory()
    sample_report = build_report(sample_memory)
    sample_row = sample_report.rows[0]

    assert module.MMA_SIGNAL_MEMORY_QUALITY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_DOMAIN_MMA_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION",
        "MMA_SIGNAL_MEMORY_QUALITY_STATUSES",
        "MMA_SIGNAL_MEMORY_QUALITY_REASON_CODES",
        "ResearchDomainMmaSignalMemoryInput",
        "ResearchDomainMmaSignalMemoryQualityConfig",
        "ResearchDomainMmaSignalMemoryQualityReport",
        "ResearchDomainMmaSignalMemoryQualityRow",
        "build_research_domain_mma_signal_memory_quality_report",
        "research_domain_mma_signal_memory_quality_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    for item in (sample_config, sample_memory, sample_row, sample_report):
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="evidence_count must be a Decimal"):
        memory(evidence_count=3)
    with pytest.raises(ValueError, match="evidence_count must be a whole Decimal"):
        memory(evidence_count=d("3.500000"))
    with pytest.raises(ValueError, match="confidence_score must be a Decimal"):
        memory(confidence_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="observed_at"):
        memory(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        memory(observed_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="team_label"):
        memory(team_label=_StringSubclass("mma-research-team"))
    with pytest.raises(ValueError, match="unsafe public"):
        memory(memory_label="market_slug")
    with pytest.raises(ValueError, match="redaction_confirmed"):
        memory(redaction_confirmed=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_report(memory(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        build_report(memory(), memory())
    with pytest.raises(ValueError, match="input_family"):
        memory(input_family="weather")
    with pytest.raises(ValueError, match="paper_only"):
        replace(sample_config, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        memory(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(memory(readonly=False))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(sample_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="row_status"):
        replace(sample_row, row_status="blocked")

    assert (
        build_report(
            memory(),
            generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
        ).generated_at
        == GENERATED_AT
    )


def test_module_scope_has_no_external_or_decision_action_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
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
        "wallet",
        "account",
        "private_key",
        "api_key",
        "secret",
        "clob",
        "submit",
        "cancel",
        "signing",
        "trading",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
        "live",
        "sizing",
        "recommend",
        "order",
        "trade",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
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
        "typing",
    }


_FORBIDDEN_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table_name",
    "private_token",
    "wallet",
    "auth",
    "order",
    "recommend",
    "sizing",
    "trade",
    "slug",
    "url",
    "token",
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
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_payload_has_no_forbidden_public_surface(value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in _FORBIDDEN_PUBLIC_FRAGMENTS)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(fragment in lowered_key for fragment in _FORBIDDEN_PUBLIC_FRAGMENTS)
            assert_payload_has_no_forbidden_public_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_payload_has_no_forbidden_public_surface(item)
