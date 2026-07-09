from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_team_playbook_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "validated_lesson_pass_count": d("5.000000"),
        "validated_lesson_watch_count": d("3.000000"),
        "feedback_pass_age_seconds": d("604800.000000"),
        "feedback_watch_age_seconds": d("1209600.000000"),
        "calibration_note_pass_count": d("3.000000"),
        "calibration_note_watch_count": d("1.000000"),
        "unresolved_caveat_watch_count": d("1.000000"),
        "unresolved_caveat_block_count": d("3.000000"),
        "triage_readiness_pass_score": d("0.800000"),
        "triage_readiness_watch_score": d("0.550000"),
    }
    values.update(overrides)
    return module.ResearchDomainTeamPlaybookMemoryQualityConfig(**values)


def memory(**overrides: object) -> Any:
    module = api()
    values = {
        "domain_team_label": "macro_rates",
        "specialist_team_label": "rates_research",
        "validated_lesson_count": d("6.000000"),
        "latest_feedback_at": GENERATED_AT - timedelta(days=2),
        "calibration_note_count": d("3.000000"),
        "unresolved_caveat_count": d("0.000000"),
        "observed_at": GENERATED_AT - timedelta(hours=1),
    }
    values.update(overrides)
    return module.ResearchDomainTeamPlaybookMemoryQualityInput(**values)


def build_report(*rows: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_domain_team_playbook_memory_quality_report(
        rows,
        config=config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_decimal_only_numerics(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only_numerics(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_decimal_only_numerics(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_decimal_only_numerics(item)


def test_report_scores_playbook_memory_quality_without_raw_payload_leakage() -> None:
    module = api()

    report = build_report(
        memory(
            domain_team_label="macro_rates",
            specialist_team_label="rates_research",
            validated_lesson_count=d("6.000000"),
            latest_feedback_at=GENERATED_AT - timedelta(days=2),
            calibration_note_count=d("3.000000"),
            unresolved_caveat_count=d("0.000000"),
        ),
        memory(
            domain_team_label="crypto_btc",
            specialist_team_label="crypto_research",
            validated_lesson_count=d("3.000000"),
            latest_feedback_at=GENERATED_AT - timedelta(days=9),
            calibration_note_count=d("1.000000"),
            unresolved_caveat_count=d("1.000000"),
        ),
        memory(
            domain_team_label="election_polling",
            specialist_team_label="politics_research",
            validated_lesson_count=d("1.000000"),
            latest_feedback_at=GENERATED_AT - timedelta(days=20),
            calibration_note_count=d("0.000000"),
            unresolved_caveat_count=d("4.000000"),
        ),
    )

    assert type(report) is module.ResearchDomainTeamPlaybookMemoryQualityReport
    assert report.report_status == "block"
    assert report.domain_team_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.total_validated_lesson_count == d("10.000000")
    assert report.total_calibration_note_count == d("4.000000")
    assert report.total_unresolved_caveat_count == d("5.000000")
    assert report.max_feedback_age_seconds == d("1728000.000000")
    assert report.min_triage_readiness_score == d("0.200000")
    assert report.reason_codes == (
        "playbook_memory_validated_lessons_block",
        "playbook_memory_recent_feedback_block",
        "playbook_memory_calibration_notes_block",
        "playbook_memory_unresolved_caveats_block",
        "playbook_memory_validated_lessons_watch",
        "playbook_memory_recent_feedback_watch",
        "playbook_memory_calibration_notes_watch",
        "playbook_memory_unresolved_caveats_watch",
    )

    assert tuple((row.status, row.domain_team_label) for row in report.rows) == (
        ("block", "election_polling"),
        ("watch", "crypto_btc"),
        ("pass", "macro_rates"),
    )

    blocked = report.rows[0]
    assert blocked.feedback_age_seconds == d("1728000.000000")
    assert blocked.triage_readiness_score == d("0.200000")
    assert blocked.reason_codes == (
        "playbook_memory_validated_lessons_block",
        "playbook_memory_recent_feedback_block",
        "playbook_memory_calibration_notes_block",
        "playbook_memory_unresolved_caveats_block",
    )

    watched = report.rows[1]
    assert watched.feedback_age_seconds == d("777600.000000")
    assert watched.triage_readiness_score == d("0.700000")
    assert watched.reason_codes == (
        "playbook_memory_validated_lessons_watch",
        "playbook_memory_recent_feedback_watch",
        "playbook_memory_calibration_notes_watch",
        "playbook_memory_unresolved_caveats_watch",
    )

    passed = report.rows[2]
    assert passed.reason_codes == ("playbook_memory_quality_clear",)
    assert passed.triage_readiness_score == d("1.000000")

    payload = module.research_domain_team_playbook_memory_quality_report_payload(report)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["rows"][0]["triage_readiness_score"] == "0.200000"
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    assert_no_float_values(payload)

    public_text = repr(payload)
    for raw_fragment in (
        "candidate-raw-001",
        "market-id",
        "market_slug",
        "question",
        "https://",
        "postgres://",
        "private-token",
        "wallet",
        "order",
        "trade",
        "recommendation",
    ):
        assert raw_fragment not in public_text.lower()


def test_empty_and_clear_reports_are_digest_backed_with_exact_statuses() -> None:
    module = api()

    empty = build_report()
    assert empty.report_status == "block"
    assert empty.reason_codes == ("playbook_memory_quality_empty",)
    assert empty.rows == ()
    assert empty.domain_team_count == d("0.000000")
    assert empty.min_triage_readiness_score == d("0.000000")

    clear = build_report(memory(domain_team_label="energy_power"))
    assert clear.report_status == "pass"
    assert clear.reason_codes == ("playbook_memory_quality_clear",)
    assert clear.rows[0].status == "pass"
    assert clear.rows[0].reason_codes == ("playbook_memory_quality_clear",)
    assert clear.derived_validation_digest != empty.derived_validation_digest

    payload = module.research_domain_team_playbook_memory_quality_report_payload(clear)
    assert module.research_domain_team_playbook_memory_quality_report_payload(payload) == payload

    tampered = dict(payload)
    tampered["domain_team_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_domain_team_playbook_memory_quality_report_payload(tampered)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    sample_config = config()
    sample_input = memory()
    sample_report = build_report(sample_input)
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_input, sample_row, sample_report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_decimal_only_numerics(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchDomainTeamPlaybookMemoryQualityConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        memory(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(memory(readonly=False))


def test_validates_inputs_config_time_order_and_public_payload_safety() -> None:
    module = api()
    good = memory()

    with pytest.raises(ValueError, match="Decimal"):
        config(validated_lesson_pass_count=5)
    with pytest.raises(ValueError, match="Decimal"):
        config(triage_readiness_pass_score=_DecimalSubclass("0.8"))
    with pytest.raises(ValueError, match="timezone-aware"):
        memory(observed_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            good,
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        build_report(memory(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="latest_feedback_at"):
        memory(
            latest_feedback_at=GENERATED_AT,
            observed_at=GENERATED_AT - timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="unique"):
        build_report(good, memory(domain_team_label=good.domain_team_label))
    with pytest.raises(ValueError, match="input rows"):
        module.build_research_domain_team_playbook_memory_quality_report(
            (object(),),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="public label"):
        memory(domain_team_label="market_slug_raw")

    payload = module.research_domain_team_playbook_memory_quality_report_payload(
        build_report(good),
    )
    unsafe = dict(payload)
    unsafe["source_url"] = "https://example.invalid/raw-text"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_domain_team_playbook_memory_quality_report_payload(unsafe)


def test_module_scope_is_pure_report_only_without_live_or_persistence_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "recommendation",
        "sizing",
        "requests",
        "httpx",
        "psycopg",
        "sqlalchemy",
        "sqlite",
        "socket",
        "subprocess",
        "web3",
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
                "delete",
            }

    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in (
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
    )
