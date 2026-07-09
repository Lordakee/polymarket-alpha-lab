from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_team_domain_playbook_adherence_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def item(team_label: str, domain_label: str, **overrides: object):
    module = api()
    values = {
        "team_label": team_label,
        "domain_label": domain_label,
        "playbook_step_count": d("10"),
        "followed_playbook_step_count": d("10"),
        "required_source_count": d("5"),
        "cited_required_source_count": d("5"),
        "required_calibration_note_count": d("2"),
        "calibration_note_count": d("2"),
        "stale_memory_override_count": d("1"),
        "documented_stale_memory_override_count": d("1"),
        "exception_count": d("1"),
        "documented_exception_count": d("1"),
        "review_started_at": GENERATED_AT - timedelta(seconds=3600),
        "review_completed_at": GENERATED_AT,
        "redaction_confirmed": True,
    }
    values.update(overrides)
    return module.ResearchTeamDomainPlaybookAdherenceInput(**values)


def report(*items: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_playbook_adherence_report(
        items,
        config=cfg or module.ResearchTeamDomainPlaybookAdherenceConfig(),
        generated_at=generated_at,
    )


def test_playbook_adherence_scores_required_sources_notes_latency_and_exceptions() -> None:
    module = api()
    blocked = item(
        "macro-research",
        "policy-calendar",
        playbook_step_count=d("10"),
        followed_playbook_step_count=d("6"),
        required_source_count=d("5"),
        cited_required_source_count=d("3"),
        required_calibration_note_count=d("2"),
        calibration_note_count=d("0"),
        stale_memory_override_count=d("2"),
        documented_stale_memory_override_count=d("1"),
        exception_count=d("2"),
        documented_exception_count=d("1"),
        review_started_at=GENERATED_AT - timedelta(seconds=18000),
    )
    watched = item(
        "sports-research",
        "injury-news",
        playbook_step_count=d("10"),
        followed_playbook_step_count=d("8"),
        required_source_count=d("5"),
        cited_required_source_count=d("4"),
        required_calibration_note_count=d("2"),
        calibration_note_count=d("1"),
        stale_memory_override_count=d("0"),
        documented_stale_memory_override_count=d("0"),
        exception_count=d("0"),
        documented_exception_count=d("0"),
        review_started_at=GENERATED_AT - timedelta(seconds=10800),
    )
    passing = item("rates-research", "central-bank")

    adherence = report(passing, blocked, watched)
    rebuilt = report(watched, passing, blocked)
    changed = report(
        passing,
        watched,
        item(
            "macro-research",
            "policy-calendar",
            playbook_step_count=d("10"),
            followed_playbook_step_count=d("6"),
            required_source_count=d("5"),
            cited_required_source_count=d("3"),
            required_calibration_note_count=d("2"),
            calibration_note_count=d("1"),
            stale_memory_override_count=d("2"),
            documented_stale_memory_override_count=d("1"),
            exception_count=d("2"),
            documented_exception_count=d("1"),
            review_started_at=GENERATED_AT - timedelta(seconds=18000),
        ),
    )

    assert type(adherence) is module.ResearchTeamDomainPlaybookAdherenceReport
    assert is_dataclass(adherence)
    assert adherence.status == "block"
    assert adherence.input_count == d("3")
    assert adherence.pass_count == d("1")
    assert adherence.watch_count == d("1")
    assert adherence.block_count == d("1")
    assert adherence.average_playbook_step_adherence_ratio == d("0.800000")
    assert adherence.average_required_source_coverage_ratio == d("0.800000")
    assert adherence.average_calibration_note_ratio == d("0.500000")
    assert adherence.average_stale_override_documentation_ratio == d("0.833333")
    assert adherence.average_exception_documentation_ratio == d("0.833333")
    assert adherence.average_review_latency_seconds == d("10800.000000")
    assert adherence.average_playbook_adherence_score == d("0.735000")
    assert adherence.reason_codes == (
        "playbook_steps_incomplete",
        "playbook_steps_watch",
        "required_source_coverage_gap",
        "required_source_coverage_watch",
        "calibration_note_gap",
        "calibration_note_watch",
        "stale_memory_override_missing_documentation",
        "review_latency_sla_breach",
        "review_latency_watch",
        "exception_documentation_gap",
        "domain_playbook_adherence_block",
        "domain_playbook_adherence_watch",
    )
    assert adherence.paper_only is True
    assert adherence.report_only is True
    assert adherence.readonly is True

    assert tuple(row.row_status for row in adherence.rows) == ("block", "watch", "pass")
    assert adherence.rows[0] == module.ResearchTeamDomainPlaybookAdherenceRow(
        team_label="macro-research",
        domain_label="policy-calendar",
        playbook_step_count=d("10"),
        followed_playbook_step_count=d("6"),
        playbook_step_adherence_ratio=d("0.600000"),
        required_source_count=d("5"),
        cited_required_source_count=d("3"),
        required_source_coverage_ratio=d("0.600000"),
        required_calibration_note_count=d("2"),
        calibration_note_count=d("0"),
        calibration_note_ratio=d("0.000000"),
        stale_memory_override_count=d("2"),
        documented_stale_memory_override_count=d("1"),
        stale_override_documentation_ratio=d("0.500000"),
        exception_count=d("2"),
        documented_exception_count=d("1"),
        exception_documentation_ratio=d("0.500000"),
        review_latency_seconds=d("18000.000000"),
        review_latency_score=d("0.000000"),
        playbook_adherence_score=d("0.420000"),
        row_status="block",
        reason_codes=(
            "playbook_steps_incomplete",
            "required_source_coverage_gap",
            "calibration_note_gap",
            "stale_memory_override_missing_documentation",
            "review_latency_sla_breach",
            "exception_documentation_gap",
            "domain_playbook_adherence_block",
        ),
    )

    payload = module.research_team_domain_playbook_adherence_report_payload(adherence)
    assert payload == adherence.payload
    assert payload["rows"][0]["playbook_adherence_score"] == "0.420000"
    assert payload["rows"][0]["review_latency_seconds"] == "18000.000000"
    assert payload["derived_validation_digest"] == adherence.derived_validation_digest
    assert len(adherence.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in adherence.derived_validation_digest)
    assert adherence.derived_validation_digest == rebuilt.derived_validation_digest
    assert adherence.derived_validation_digest != changed.derived_validation_digest
    _assert_no_floats(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_input_blocks_without_raw_public_identifiers() -> None:
    module = api()
    adherence = report()

    assert adherence.status == "block"
    assert adherence.input_count == d("0")
    assert adherence.row_count == d("0")
    assert adherence.pass_count == d("0")
    assert adherence.watch_count == d("0")
    assert adherence.block_count == d("0")
    assert adherence.average_playbook_adherence_score == d("0.000000")
    assert adherence.reason_codes == ("no_domain_playbook_adherence_inputs",)
    assert adherence.rows == ()

    payload_text = repr(adherence.payload).lower()
    for forbidden in (
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
        "trade",
        "live",
    ):
        assert forbidden not in payload_text


def test_adherence_report_is_frozen_decimal_only_public_safe_and_readonly() -> None:
    module = api()
    adherence = report(item("rates-research", "central-bank"))

    assert module.DOMAIN_PLAYBOOK_ADHERENCE_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_ADHERENCE_REPORT_CONFIG_VERSION",
        "DOMAIN_PLAYBOOK_ADHERENCE_STATUSES",
        "DOMAIN_PLAYBOOK_ADHERENCE_REASON_CODES",
        "ResearchTeamDomainPlaybookAdherenceConfig",
        "ResearchTeamDomainPlaybookAdherenceInput",
        "ResearchTeamDomainPlaybookAdherenceReport",
        "ResearchTeamDomainPlaybookAdherenceRow",
        "build_research_team_domain_playbook_adherence_report",
        "research_team_domain_playbook_adherence_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        adherence.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="playbook_step_count must be a Decimal"):
        item("rates-research", "central-bank", playbook_step_count=10)
    with pytest.raises(ValueError, match="playbook_step_count must be a whole Decimal"):
        item("rates-research", "central-bank", playbook_step_count=d("10.500000"))
    with pytest.raises(ValueError, match="source_coverage_weight must be a Decimal"):
        module.ResearchTeamDomainPlaybookAdherenceConfig(
            source_coverage_weight=_DecimalSubclass("0.200000"),
        )
    with pytest.raises(ValueError, match="review_started_at"):
        item(
            "rates-research",
            "central-bank",
            review_started_at=datetime(2026, 7, 8, 11, 0),
        )
    with pytest.raises(ValueError, match="review_completed_at"):
        item(
            "rates-research",
            "central-bank",
            review_completed_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="team_label"):
        item(_StringSubclass("rates-research"), "central-bank")
    with pytest.raises(ValueError, match="public-safe"):
        item("wallet", "central-bank")
    with pytest.raises(ValueError, match="redaction_confirmed"):
        item("rates-research", "central-bank", redaction_confirmed=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(
            item(
                "rates-research",
                "central-bank",
                review_completed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(module.ResearchTeamDomainPlaybookAdherenceConfig(), paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(adherence, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="followed_playbook_step_count"):
        replace(
            adherence.rows[0],
            followed_playbook_step_count=d("11"),
            playbook_step_adherence_ratio=d("1.000000"),
        )
    assert (
        report(
            item("rates-research", "central-bank"),
            generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
        ).generated_at
        == GENERATED_AT
    )

    _assert_public_numeric_values_are_decimal(adherence)
    _assert_no_floats(adherence.payload)


def test_payload_dict_entrypoint_rejects_self_digesting_schema_drift() -> None:
    module = api()
    base_payload = report(item("rates-research", "central-bank")).payload

    top_level_drift = json.loads(json.dumps(base_payload, sort_keys=True))
    top_level_drift["unexpected_public_field"] = "public-summary"
    top_level_drift["derived_validation_digest"] = module._derived_digest(top_level_drift)
    with pytest.raises(ValueError, match="payload schema"):
        module.research_team_domain_playbook_adherence_report_payload(top_level_drift)

    row_level_drift = json.loads(json.dumps(base_payload, sort_keys=True))
    row_level_drift["rows"][0]["unexpected_public_field"] = "public-summary"
    row_level_drift["derived_validation_digest"] = module._derived_digest(row_level_drift)
    with pytest.raises(ValueError, match="payload schema"):
        module.research_team_domain_playbook_adherence_report_payload(row_level_drift)


def test_module_scope_has_no_external_or_decision_action_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_team_domain_playbook_adherence_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "candidate_id",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
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
        "order",
        "trade",
        "live",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
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


def _assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _assert_public_numeric_values_are_decimal(value: Any) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field_name in value.__dataclass_fields__:
            _assert_public_numeric_values_are_decimal(getattr(value, field_name))
    if isinstance(value, dict):
        for item in value.values():
            _assert_public_numeric_values_are_decimal(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_public_numeric_values_are_decimal(item)
