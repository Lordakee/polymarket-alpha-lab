from __future__ import annotations

import ast
import dataclasses
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
BASE_EVIDENCE_AT = GENERATED_AT - timedelta(hours=1)
BASE_DEADLINE_AT = GENERATED_AT + timedelta(hours=3)
RAW_EVENT_REFERENCE = "candidate-alpha-market-slug-question-source-url-token"


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_event_resolution_evidence_latency_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    module = api()
    values = {
        "evidence_latency_watch_seconds": d("3600.000000"),
        "evidence_latency_block_seconds": d("10800.000000"),
        "deadline_watch_seconds": d("7200.000000"),
        "deadline_block_seconds": d("1800.000000"),
        "minimum_evidence_trust_score": d("0.700000"),
        "minimum_evidence_strength_score": d("0.700000"),
        "revision_watch_threshold": d("0.300000"),
        "revision_block_threshold": d("0.700000"),
        "decay_watch_threshold": d("0.300000"),
        "decay_block_threshold": d("0.700000"),
        "latency_weight": d("0.400000"),
        "trust_gap_weight": d("0.200000"),
        "strength_gap_weight": d("0.200000"),
        "revision_weight": d("0.100000"),
        "deadline_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchEventResolutionEvidenceLatencyDecayConfig(**values)


def _input(
    event_reference: str = RAW_EVENT_REFERENCE,
    *,
    evidence_observed_at: datetime = BASE_EVIDENCE_AT,
    resolution_deadline_at: datetime | None = BASE_DEADLINE_AT,
    evidence_trust_score: Decimal = d("0.800000"),
    evidence_strength_score: Decimal = d("0.850000"),
    evidence_revision_risk: Decimal = d("0.200000"),
    reason_codes: tuple[str, ...] = ("verified_packet",),
):
    module = api()
    return module.ResearchEventResolutionEvidenceLatencyDecayInput(
        event_reference=event_reference,
        evidence_observed_at=evidence_observed_at,
        resolution_deadline_at=resolution_deadline_at,
        evidence_trust_score=evidence_trust_score,
        evidence_strength_score=evidence_strength_score,
        evidence_revision_risk=evidence_revision_risk,
        reason_codes=reason_codes,
    )


def _build_report(*events, config=None):
    module = api()
    return module.build_research_event_resolution_evidence_latency_decay_report(
        events,
        generated_at=GENERATED_AT,
        config=_config() if config is None else config,
    )


def _scenario_report():
    return _build_report(
        _input(
            "event-blocked",
            evidence_observed_at=GENERATED_AT - timedelta(hours=4),
            resolution_deadline_at=GENERATED_AT + timedelta(minutes=20),
            evidence_trust_score=d("0.400000"),
            evidence_strength_score=d("0.500000"),
            evidence_revision_risk=d("0.800000"),
            reason_codes=(),
        ),
        _input(
            "event-watch",
            evidence_observed_at=GENERATED_AT - timedelta(hours=1),
            resolution_deadline_at=GENERATED_AT + timedelta(hours=3),
            evidence_trust_score=d("0.800000"),
            evidence_strength_score=d("0.850000"),
            evidence_revision_risk=d("0.200000"),
            reason_codes=("reviewed",),
        ),
        _input(
            "event-pass",
            evidence_observed_at=GENERATED_AT - timedelta(minutes=10),
            resolution_deadline_at=GENERATED_AT + timedelta(days=1),
            evidence_trust_score=d("0.950000"),
            evidence_strength_score=d("0.950000"),
            evidence_revision_risk=d("0.050000"),
            reason_codes=("complete",),
        ),
    )


def test_report_scores_latency_trust_strength_revision_and_deadline_decay() -> None:
    report = _scenario_report()

    assert dataclasses.is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.reason_codes == (
        "evidence_latency_stale",
        "evidence_trust_gap",
        "evidence_strength_gap",
        "evidence_revision_risk",
        "resolution_deadline_pressure",
        "evidence_latency_decay_elevated",
    )
    assert report.event_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.stale_count == d("2")
    assert report.trust_gap_count == d("1")
    assert report.strength_gap_count == d("1")
    assert report.revision_risk_count == d("1")
    assert report.deadline_pressure_count == d("1")
    assert report.max_evidence_age_seconds == d("14400.000000")
    assert report.average_evidence_latency_decay_score == d("0.356852")
    assert report.highest_evidence_latency_decay_score == d("0.800000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    rows = {row.event_digest: row for row in report.rows}
    blocked = rows[hashlib.sha256(b"event-blocked").hexdigest()]
    assert blocked.status == "block"
    assert blocked.evidence_age_seconds == d("14400.000000")
    assert blocked.deadline_proximity_seconds == d("1200.000000")
    assert blocked.latency_pressure_score == d("1.000000")
    assert blocked.trust_gap_score == d("0.600000")
    assert blocked.strength_gap_score == d("0.500000")
    assert blocked.deadline_pressure_score == d("1.000000")
    assert blocked.evidence_latency_decay_score == d("0.800000")
    assert blocked.reason_codes == (
        "evidence_latency_stale",
        "evidence_trust_gap",
        "evidence_strength_gap",
        "evidence_revision_risk",
        "resolution_deadline_pressure",
        "evidence_latency_decay_elevated",
    )

    watch = rows[hashlib.sha256(b"event-watch").hexdigest()]
    assert watch.status == "watch"
    assert watch.evidence_age_seconds == d("3600.000000")
    assert watch.deadline_proximity_seconds == d("10800.000000")
    assert watch.latency_pressure_score == d("0.333333")
    assert watch.evidence_latency_decay_score == d("0.223333")
    assert watch.reason_codes == ("evidence_latency_stale", "reviewed")

    passed = rows[hashlib.sha256(b"event-pass").hexdigest()]
    assert passed.status == "pass"
    assert passed.evidence_age_seconds == d("600.000000")
    assert passed.deadline_proximity_seconds == d("86400.000000")
    assert passed.evidence_latency_decay_score == d("0.047222")
    assert passed.reason_codes == ("complete", "evidence_latency_clear")


def test_empty_report_payload_uses_decimal_strings_and_validates_digest() -> None:
    module = api()

    report = _build_report()
    payload = module.research_event_resolution_evidence_latency_decay_payload(report)
    digest = module.research_event_resolution_evidence_latency_decay_digest(report)

    assert report.status == "pass"
    assert report.reason_codes == ("evidence_latency_empty",)
    assert report.event_count == d("0")
    assert report.rows == ()
    assert report.average_evidence_latency_decay_score == d("0.000000")
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["event_count"] == "0"
    assert payload["average_evidence_latency_decay_score"] == "0.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest == digest
    assert len(digest) == 64
    int(digest, 16)
    assert _float_paths(payload) == ()
    assert _int_paths(payload) == ()
    json.dumps(payload, sort_keys=True)
    module.validate_research_event_resolution_evidence_latency_decay_digest(report)

    tampered_payload = dict(payload)
    tampered_payload["event_count"] = "1"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_resolution_evidence_latency_decay_payload(tampered_payload)


def test_input_order_does_not_change_rows_digest_or_expose_raw_reference() -> None:
    module = api()
    first_event = _input(
        RAW_EVENT_REFERENCE,
        evidence_observed_at=GENERATED_AT - timedelta(minutes=30),
    )
    second_event = _input(
        "plain-private-reference",
        evidence_observed_at=GENERATED_AT - timedelta(hours=4),
        resolution_deadline_at=GENERATED_AT + timedelta(minutes=10),
        evidence_trust_score=d("0.500000"),
        evidence_strength_score=d("0.500000"),
        evidence_revision_risk=d("0.750000"),
        reason_codes=(),
    )

    first = module.build_research_event_resolution_evidence_latency_decay_report(
        (first_event, second_event),
        generated_at=GENERATED_AT,
        config=_config(),
    )
    second = module.build_research_event_resolution_evidence_latency_decay_report(
        (second_event, first_event),
        generated_at=GENERATED_AT,
        config=_config(),
    )
    payload = module.research_event_resolution_evidence_latency_decay_payload(first)
    encoded = json.dumps(payload, sort_keys=True)

    assert first == second
    assert first.derived_validation_digest == second.derived_validation_digest
    assert [row.event_digest for row in first.rows] == sorted(
        (row.event_digest for row in first.rows),
        key=lambda event_digest: (
            first.rows[
                tuple(row.event_digest for row in first.rows).index(event_digest)
            ].status,
            event_digest,
        ),
    )
    assert RAW_EVENT_REFERENCE not in encoded
    assert hashlib.sha256(RAW_EVENT_REFERENCE.encode("utf-8")).hexdigest() in encoded
    assert not _unsafe_public_fragments(payload)


def test_validation_enforces_frozen_flags_decimal_datetimes_status_and_tamper() -> None:
    module = api()

    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    report = _scenario_report()

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="evidence_latency_watch_seconds must be a Decimal"):
        module.ResearchEventResolutionEvidenceLatencyDecayConfig(
            evidence_latency_watch_seconds=3600,
        )
    with pytest.raises(ValueError, match="evidence_trust_score must be a Decimal"):
        _input(evidence_trust_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="evidence_observed_at must be timezone-aware"):
        _input(evidence_observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="resolution_deadline_at must be timezone-aware"):
        _input(
            resolution_deadline_at=datetime(
                2026,
                7,
                9,
                12,
                0,
                tzinfo=NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="evidence_observed_at must be <= generated_at"):
        _build_report(
            _input(evidence_observed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="event_reference values must be unique"):
        _build_report(_input("same-reference"), _input("same-reference"))
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="reason_code contains unsafe text"):
        _input(reason_codes=("market_slug",))


def test_public_dataclasses_exports_and_static_module_surface_are_report_only() -> None:
    module = api()

    assert module.RESEARCH_EVENT_RESOLUTION_EVIDENCE_LATENCY_DECAY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_LATENCY_DECAY_REPORT_CONFIG_VERSION",
        "RESEARCH_EVENT_RESOLUTION_EVIDENCE_LATENCY_DECAY_STATUSES",
        "ResearchEventResolutionEvidenceLatencyDecayConfig",
        "ResearchEventResolutionEvidenceLatencyDecayInput",
        "ResearchEventResolutionEvidenceLatencyDecayReport",
        "ResearchEventResolutionEvidenceLatencyDecayRow",
        "build_research_event_resolution_evidence_latency_decay_report",
        "research_event_resolution_evidence_latency_decay_digest",
        "research_event_resolution_evidence_latency_decay_payload",
        "validate_research_event_resolution_evidence_latency_decay_digest",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert dataclasses.is_dataclass(value)

    for cls in (
        module.ResearchEventResolutionEvidenceLatencyDecayConfig,
        module.ResearchEventResolutionEvidenceLatencyDecayInput,
        module.ResearchEventResolutionEvidenceLatencyDecayReport,
        module.ResearchEventResolutionEvidenceLatencyDecayRow,
    ):
        for field in fields(cls):
            assert field.name not in {
                "candidate_id",
                "market_id",
                "market_slug",
                "question",
                "url",
                "text",
                "dsn",
                "table_name",
                "token",
                "wallet",
                "order",
                "trade",
            }

    source = Path(
        "src/polymarket_alpha_lab/"
        "research_event_resolution_evidence_latency_decay_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "broker",
        "private_key",
        "credential",
        "submit",
        "cancel",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

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


def _int_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if type(value) is int:
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_int_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_int_paths(nested, child))
        return tuple(paths)
    return ()


def _unsafe_public_fragments(value: object) -> tuple[str, ...]:
    fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "source url",
        "source_url",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = key.lower()
            findings.extend(fragment for fragment in fragments if fragment in normalized_key)
            findings.extend(_unsafe_public_fragments(item))
    elif isinstance(value, list):
        for item in value:
            findings.extend(_unsafe_public_fragments(item))
    elif type(value) is str:
        normalized_value = value.lower()
        findings.extend(fragment for fragment in fragments if fragment in normalized_value)
    return tuple(findings)
