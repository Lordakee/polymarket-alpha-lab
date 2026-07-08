from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_domain_regulation_signal_memory_quality_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
HANDOFF_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_regulation_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_DOMAIN_REGULATION_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION
        ),
        "fresh_agency_max_age_seconds": d("7200.000000"),
        "fresh_court_max_age_seconds": d("21600.000000"),
        "fresh_rulemaking_max_age_seconds": d("43200.000000"),
        "fresh_enforcement_max_age_seconds": d("43200.000000"),
        "fresh_effective_date_max_age_seconds": d("86400.000000"),
        "pass_memory_score": d("0.800000"),
        "watch_memory_score": d("0.550000"),
        "block_conflict_count": d("2.000000"),
        "watch_conflict_count": d("1.000000"),
    }
    values.update(overrides)
    return module.ResearchDomainRegulationSignalMemoryQualityConfig(**values)


def memory_input(**overrides: object):
    module = api()
    values = {
        "jurisdiction_label": "us_federal",
        "regulatory_area": "digital_asset_policy",
        "memory_scope": "agency_court_rulemaking_enforcement_effective_date",
        "agency_memorized_at": HANDOFF_AT - timedelta(minutes=45),
        "court_memorized_at": HANDOFF_AT - timedelta(hours=2),
        "rulemaking_memorized_at": HANDOFF_AT - timedelta(hours=4),
        "enforcement_memorized_at": HANDOFF_AT - timedelta(hours=5),
        "effective_date_memorized_at": HANDOFF_AT - timedelta(hours=8),
        "agency_memory_score": d("0.940000"),
        "court_memory_score": d("0.900000"),
        "rulemaking_memory_score": d("0.880000"),
        "enforcement_memory_score": d("0.860000"),
        "effective_date_memory_score": d("0.920000"),
        "agency_conflict_count": d("0.000000"),
        "court_conflict_count": d("0.000000"),
        "rulemaking_conflict_count": d("0.000000"),
        "enforcement_conflict_count": d("0.000000"),
        "effective_date_conflict_count": d("0.000000"),
    }
    values.update(overrides)
    return module.ResearchDomainRegulationSignalMemoryQualityInputRow(**values)


def build_report(*items: object, cfg=None, generated_at=GENERATED_AT, handoff_at=HANDOFF_AT):
    module = api()
    return module.build_research_domain_regulation_signal_memory_quality_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
        handoff_at=handoff_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_regulation_signal_memory_quality_flags_missing_stale_and_conflicts() -> None:
    module = api()
    report = build_report(
        memory_input(
            jurisdiction_label="federal_block",
            agency_memorized_at=None,
            court_memorized_at=HANDOFF_AT - timedelta(days=2),
            rulemaking_memorized_at=None,
            enforcement_memorized_at=HANDOFF_AT - timedelta(days=3),
            effective_date_memorized_at=HANDOFF_AT - timedelta(days=5),
            agency_memory_score=d("0.420000"),
            court_memory_score=d("0.480000"),
            rulemaking_memory_score=d("0.500000"),
            enforcement_memory_score=d("0.440000"),
            effective_date_memory_score=d("0.460000"),
            court_conflict_count=d("2.000000"),
            enforcement_conflict_count=d("3.000000"),
        ),
        memory_input(
            jurisdiction_label="state_watch",
            agency_memorized_at=HANDOFF_AT - timedelta(hours=3),
            court_memorized_at=HANDOFF_AT - timedelta(hours=7),
            rulemaking_memorized_at=HANDOFF_AT - timedelta(hours=13),
            enforcement_memorized_at=HANDOFF_AT - timedelta(hours=2),
            effective_date_memorized_at=HANDOFF_AT - timedelta(hours=10),
            agency_memory_score=d("0.780000"),
            court_memory_score=d("0.740000"),
            rulemaking_memory_score=d("0.700000"),
            enforcement_memory_score=d("0.760000"),
            effective_date_memory_score=d("0.720000"),
            agency_conflict_count=d("1.000000"),
            rulemaking_conflict_count=d("1.000000"),
        ),
        memory_input(jurisdiction_label="federal_pass"),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchDomainRegulationSignalMemoryQualityReport
    assert report.generated_at == GENERATED_AT
    assert report.handoff_at == HANDOFF_AT
    assert (
        report.config_version
        == "research-domain-regulation-signal-memory-quality-report-v0"
    )
    assert report.report_status == "block"
    assert report.handoff_gate_label == (
        "block_report_only_regulation_signal_memory_forecast_handoff"
    )
    assert report.memory_set_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.stale_memory_set_count == d("2.000000")
    assert report.conflicting_memory_set_count == d("2.000000")
    assert report.missing_memory_set_count == d("1.000000")
    assert report.average_memory_score == d("0.700000")
    assert report.average_freshness_score == d("0.466667")
    assert report.average_conflict_score == d("0.500000")
    assert report.agency_missing_count == d("1.000000")
    assert report.court_stale_count == d("2.000000")
    assert report.rulemaking_missing_count == d("1.000000")
    assert report.enforcement_conflicting_count == d("1.000000")
    assert report.effective_date_stale_count == d("1.000000")
    assert report.max_effective_date_age_seconds == d("432000.000000")
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, watched, passed = report.rows
    assert tuple(row.public_status for row in report.rows) == ("block", "watch", "pass")
    assert blocked.jurisdiction_label == "federal_block"
    assert blocked.freshness_status == "block"
    assert blocked.conflict_status == "block"
    assert blocked.agency_age_seconds is None
    assert blocked.court_age_seconds == d("172800.000000")
    assert blocked.rulemaking_age_seconds is None
    assert blocked.enforcement_age_seconds == d("259200.000000")
    assert blocked.effective_date_age_seconds == d("432000.000000")
    assert blocked.composite_memory_score == d("0.460000")
    assert blocked.freshness_score == d("0.000000")
    assert blocked.conflict_score == d("0.000000")
    assert blocked.reason_codes == (
        "regulation_memory_quality_agency_missing",
        "regulation_memory_quality_conflict_block",
        "regulation_memory_quality_court_conflicting",
        "regulation_memory_quality_court_stale",
        "regulation_memory_quality_effective_date_stale",
        "regulation_memory_quality_enforcement_conflicting",
        "regulation_memory_quality_enforcement_stale",
        "regulation_memory_quality_memory_score_block",
        "regulation_memory_quality_rulemaking_missing",
    )

    assert watched.public_status == "watch"
    assert watched.freshness_status == "watch"
    assert watched.conflict_status == "watch"
    assert watched.composite_memory_score == d("0.740000")
    assert watched.freshness_score == d("0.400000")
    assert watched.conflict_score == d("0.500000")
    assert watched.reason_codes == (
        "regulation_memory_quality_agency_conflicting",
        "regulation_memory_quality_agency_stale",
        "regulation_memory_quality_conflict_watch",
        "regulation_memory_quality_court_stale",
        "regulation_memory_quality_memory_score_watch",
        "regulation_memory_quality_rulemaking_conflicting",
        "regulation_memory_quality_rulemaking_stale",
        "regulation_memory_quality_watch",
    )

    assert passed.public_status == "pass"
    assert passed.freshness_status == "pass"
    assert passed.conflict_status == "pass"
    assert passed.composite_memory_score == d("0.900000")
    assert passed.freshness_score == d("1.000000")
    assert passed.conflict_score == d("1.000000")
    assert passed.reason_codes == (
        "regulation_memory_quality_fresh",
        "regulation_memory_quality_no_conflict",
        "regulation_memory_quality_pass",
    )


def test_empty_inputs_return_block_report_only_digest() -> None:
    module = api()
    report = build_report()

    assert report.report_status == "block"
    assert report.memory_set_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("regulation_memory_quality_no_inputs",)
    assert report.reason_code_counts == (
        module.ResearchDomainRegulationSignalMemoryQualityReasonCodeCount(
            reason_code="regulation_memory_quality_no_inputs",
            count=d("1.000000"),
            memory_set_ratio=d("0.000000"),
        ),
    )
    assert report.derived_validation_digest == (
        module.research_domain_regulation_signal_memory_quality_report_digest(report)
    )
    for obj in (report, *report.reason_code_counts):
        assert obj.paper_only is True
        assert obj.report_only is True
        assert obj.readonly is True
        for field in fields(obj):
            value = getattr(obj, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_score", "_seconds", "_ratio")):
                assert type(value) is Decimal


def test_payload_is_deterministic_public_decimal_only_and_digest_validated() -> None:
    module = api()
    first = build_report(
        memory_input(
            jurisdiction_label="state_watch",
            agency_memorized_at=datetime(
                2026,
                7,
                8,
                4,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
            rulemaking_memorized_at=HANDOFF_AT - timedelta(hours=13),
            agency_memory_score=d("0.780000"),
            court_memory_score=d("0.740000"),
            rulemaking_memory_score=d("0.700000"),
            enforcement_memory_score=d("0.760000"),
            effective_date_memory_score=d("0.720000"),
            agency_conflict_count=d("1.000000"),
            rulemaking_conflict_count=d("1.000000"),
        ),
        memory_input(jurisdiction_label="federal_pass"),
        generated_at=datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-7))),
        handoff_at=datetime(2026, 7, 8, 7, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    second = build_report(
        memory_input(jurisdiction_label="federal_pass"),
        memory_input(
            jurisdiction_label="state_watch",
            agency_memorized_at=datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
            rulemaking_memorized_at=HANDOFF_AT - timedelta(hours=13),
            agency_memory_score=d("0.780000"),
            court_memory_score=d("0.740000"),
            rulemaking_memory_score=d("0.700000"),
            enforcement_memory_score=d("0.760000"),
            effective_date_memory_score=d("0.720000"),
            agency_conflict_count=d("1.000000"),
            rulemaking_conflict_count=d("1.000000"),
        ),
    )

    payload = module.research_domain_regulation_signal_memory_quality_report_payload(first)
    repeat_payload = module.research_domain_regulation_signal_memory_quality_report_payload(
        second,
    )
    unsigned_payload = dict(payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    expected_digest = sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()

    assert payload == repeat_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T15:00:00+00:00"
    assert payload["handoff_at"] == "2026-07-08T14:00:00+00:00"
    assert payload["memory_set_count"] == "2.000000"
    assert payload["rows"][0]["public_status"] == "watch"
    assert payload["rows"][0]["composite_memory_score"] == "0.740000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert digest == expected_digest
    assert_no_int_or_float_values(payload)
    json.dumps(payload, sort_keys=True)

    unsafe_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "database",
        "network",
        "auth",
        "live",
        "sizing",
        "recommendation",
    )
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload)
        for fragment in unsafe_fragments
    )
    payload_text = repr(payload).lower()
    assert not any(fragment in payload_text for fragment in unsafe_fragments)

    tampered = dict(payload)
    tampered["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_domain_regulation_signal_memory_quality_report_payload(tampered)

    unsafe = dict(payload)
    unsafe["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_domain_regulation_signal_memory_quality_report_payload(unsafe)

    numeric = dict(payload)
    numeric["memory_set_count"] = 2
    with pytest.raises(ValueError, match="numeric"):
        module.research_domain_regulation_signal_memory_quality_report_payload(numeric)


def test_validates_types_statuses_flags_labels_and_freezing() -> None:
    module = api()
    safe_input = memory_input()
    report = build_report(safe_input)
    row = report.rows[0]

    with pytest.raises(FrozenInstanceError):
        report.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.public_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        memory_input(agency_memory_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        memory_input(court_conflict_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="datetime"):
        memory_input(agency_memorized_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="datetime"):
        memory_input(
            court_memorized_at=_DatetimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="handoff_at"):
        build_report(safe_input, handoff_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(safe_input, generated_at=HANDOFF_AT - timedelta(seconds=1))
    with pytest.raises(ValueError, match="future"):
        build_report(memory_input(agency_memorized_at=HANDOFF_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        build_report(memory_input(), memory_input())
    with pytest.raises(ValueError, match="jurisdiction_label"):
        memory_input(jurisdiction_label=_StringSubclass("us_federal"))
    with pytest.raises(ValueError, match="regulatory_area"):
        memory_input(regulatory_area="digital asset policy")
    with pytest.raises(ValueError, match="paper_only"):
        memory_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        memory_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        memory_input(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_report(memory_input(), cfg=object())
    with pytest.raises(ValueError, match="status"):
        replace(row, public_status="review")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, pass_count=d("2.000000"))

    multi_row_report = build_report(
        memory_input(jurisdiction_label="alpha_pass"),
        memory_input(jurisdiction_label="beta_watch", agency_conflict_count=d("1.000000")),
    )
    with pytest.raises(ValueError, match="rows"):
        replace(multi_row_report, rows=tuple(reversed(multi_row_report.rows)))

    payload = module.research_domain_regulation_signal_memory_quality_report_payload(report)
    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_domain_regulation_signal_memory_quality_report_payload(downgraded)

    assert {report.report_status, *(item.public_status for item in report.rows)} <= {
        "pass",
        "watch",
        "block",
    }
    for obj in (report, *report.rows, *report.reason_code_counts):
        for field in fields(obj):
            if field.name.endswith("status"):
                assert getattr(obj, field.name) in {"pass", "watch", "block"}


def test_public_inputs_reject_private_and_actionable_surfaces() -> None:
    leak_values = (
        _join_parts("raw_", "candidate", "_17"),
        _join_parts("market", "_slug"),
        _join_parts("will", "_policy", "_pass", "_question"),
        _join_parts("https", "://example.test/path"),
        _join_parts("source", "_text"),
        _join_parts("dsn", "_analytics"),
        _join_parts("table", "_name"),
        _join_parts("to", "ken", "_abc"),
        _join_parts("wal", "let", "_field"),
        _join_parts("sub", "mit", "_order"),
        _join_parts("trade", "_surface"),
        _join_parts("size", "_edge"),
        _join_parts("rec", "ommend", "_yes"),
    )

    for value in leak_values:
        with pytest.raises(ValueError, match="public"):
            memory_input(memory_scope=value)


def test_module_is_pure_report_only_and_has_no_io_or_action_surface() -> None:
    module = api()
    module_source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(module_source)

    forbidden_import_roots = {
        "builtins",
        "io",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "sys",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "delete",
        "execute",
        "open",
        "post",
        "put",
        "read_text",
        "send",
        "submit",
        "write_text",
    }
    forbidden_terms = (
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("order"),
        _join_parts("trade"),
        _join_parts("trading"),
        _join_parts("position"),
        _join_parts("buy"),
        _join_parts("sell"),
        _join_parts("rec", "ommend"),
    )

    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_calls)
    assert not any(term in module_source.lower() for term in forbidden_terms)

    for cls_name in (
        "ResearchDomainRegulationSignalMemoryQualityConfig",
        "ResearchDomainRegulationSignalMemoryQualityInputRow",
        "ResearchDomainRegulationSignalMemoryQualityReasonCodeCount",
        "ResearchDomainRegulationSignalMemoryQualityReport",
        "ResearchDomainRegulationSignalMemoryQualityReportRow",
    ):
        cls = getattr(module, cls_name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
