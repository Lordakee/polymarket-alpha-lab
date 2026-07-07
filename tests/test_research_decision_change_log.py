from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_decision_change_log"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
REF_A = "candidate_ref_" + ("a" * 64)
REF_B = "candidate_ref_" + ("b" * 64)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def change_record(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "redacted_candidate_ref": REF_A,
        "score_before": d("0.720000"),
        "score_after": d("0.730000"),
        "team_review_before_state": "pass",
        "team_review_after_state": "pass",
        "evidence_quality_before": d("0.840000"),
        "evidence_quality_after": d("0.830000"),
    }
    values.update(overrides)
    return module.ResearchDecisionChangeLogRecord(**values)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": module.DEFAULT_RESEARCH_DECISION_CHANGE_LOG_CONFIG_VERSION,
        "watch_abs_score_delta": d("0.050000"),
        "block_abs_score_delta": d("0.200000"),
        "watch_abs_evidence_quality_delta": d("0.100000"),
        "block_abs_evidence_quality_delta": d("0.250000"),
    }
    values.update(overrides)
    return module.ResearchDecisionChangeLogConfig(**values)


def report(*records: object, cfg: object | None = None):
    return api().build_research_decision_change_log(
        records,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_public_payload_shape(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if "status" in key or "state" in key:
                assert child in {"pass", "watch", "block"} or isinstance(child, list)
            assert_public_payload_shape(child)
    elif isinstance(value, list):
        for child in value:
            assert_public_payload_shape(child)
    else:
        assert type(value) not in (Decimal, datetime, float, int)


def test_stable_score_review_and_evidence_changes_pass() -> None:
    module = api()
    change_log = report(change_record())

    assert module.CHANGE_STATUSES == ("pass", "watch", "block")
    assert type(change_log) is module.ResearchDecisionChangeLogReport
    assert change_log.generated_at == GENERATED_AT
    assert change_log.status == "pass"
    assert change_log.candidate_count == d("1.000000")
    assert change_log.pass_count == d("1.000000")
    assert change_log.watch_count == d("0.000000")
    assert change_log.block_count == d("0.000000")
    assert change_log.reason_codes == ("research_decision_change_stable",)

    row = change_log.rows[0]
    assert row.redacted_candidate_ref == REF_A
    assert row.score_delta == d("0.010000")
    assert row.abs_score_delta == d("0.010000")
    assert row.evidence_quality_delta == d("-0.010000")
    assert row.abs_evidence_quality_delta == d("0.010000")
    assert row.status == "pass"
    assert row.reason_codes == ("research_decision_change_stable",)

    payload = module.research_decision_change_log_payload(change_log)
    json.dumps(payload, sort_keys=True)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["score_delta"] == "0.010000"
    assert "market_id" not in payload["rows"][0]
    assert "source_text" not in payload["rows"][0]
    assert_public_payload_shape(payload)


def test_material_score_and_evidence_quality_changes_watch() -> None:
    change_log = report(
        change_record(
            score_after=d("0.790000"),
            evidence_quality_after=d("0.710000"),
        ),
    )

    assert change_log.status == "watch"
    assert change_log.watch_count == d("1.000000")
    row = change_log.rows[0]
    assert row.status == "watch"
    assert row.score_delta == d("0.070000")
    assert row.evidence_quality_delta == d("-0.130000")
    assert row.reason_codes == (
        "score_delta_watch",
        "evidence_quality_delta_watch",
    )


def test_abnormal_score_review_or_evidence_changes_block() -> None:
    change_log = report(
        change_record(
            score_after=d("0.480000"),
            team_review_after_state="block",
            evidence_quality_after=d("0.520000"),
        ),
    )

    assert change_log.status == "block"
    assert change_log.block_count == d("1.000000")
    row = change_log.rows[0]
    assert row.status == "block"
    assert row.abs_score_delta == d("0.240000")
    assert row.evidence_quality_delta == d("-0.320000")
    assert row.reason_codes == (
        "score_delta_block",
        "team_review_state_block",
        "evidence_quality_delta_block",
    )


def test_decimal_exact_types_and_frozen_dataclasses_are_required() -> None:
    module = api()
    record = change_record()
    change_log = report(record)

    assert is_dataclass(record)
    assert is_dataclass(change_log)
    assert module.ResearchDecisionChangeLogRecord.__dataclass_params__.frozen
    assert module.ResearchDecisionChangeLogReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        record.score_after = d("0.740000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        change_log.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="score_before must be a Decimal"):
        change_record(score_before=1)
    with pytest.raises(ValueError, match="score_after must be a Decimal"):
        change_record(score_after=1.0)
    with pytest.raises(ValueError, match="evidence_quality_after must be a Decimal"):
        change_record(evidence_quality_after=DecimalSubclass("0.830000"))
    with pytest.raises(ValueError, match="watch_abs_score_delta must be a Decimal"):
        config(watch_abs_score_delta=DecimalSubclass("0.050000"))
    with pytest.raises(ValueError, match="team_review_after_state must be pass, watch, or block"):
        change_record(team_review_after_state="blocked")
    with pytest.raises(ValueError, match="records must contain"):
        report(object())


def test_public_payload_rejects_leaks_status_aliases_and_numeric_values() -> None:
    module = api()
    valid_payload = module.research_decision_change_log_payload(report(change_record()))
    assert module.validate_research_decision_change_log_public_payload(valid_payload)

    unsafe_payloads = (
        ({"raw_candidate_id": "abc"}, "raw candidate"),
        ({"candidate_id": "abc"}, "raw candidate"),
        ({"redacted_candidate_ref": "candidate_ref_not-a-digest"}, "raw candidate"),
        ({"market_id": "m-1"}, "market"),
        ({"market_slug": "will-x-happen"}, "market"),
        ({"question": "Will X happen?"}, "market"),
        ({"source_ref": "source-ref-1"}, "source"),
        ({"source_url": "https://example.test/item"}, "source"),
        ({"source_text": "raw event text"}, "source"),
        ({"safe_key": "https://example.test/item"}, "source"),
        ({"dsn": "postgres://user@host/db"}, "source"),
        ({"table": "orders"}, "unsafe"),
        ({"safe_key": "api_token=secret"}, "unsafe"),
        ({"safe_key": "wallet auth"}, "unsafe"),
        ({"safe_key": "order trade"}, "unsafe"),
        ({"safe_key": "position sizing"}, "unsafe"),
        ({"safe_key": "buy sell recommendation"}, "unsafe"),
        ({"status": "blocked"}, "status"),
        ({"state": "ready"}, "status"),
        ({"candidate_count": 1}, "decimal strings"),
        ({"candidate_count": 1.0}, "decimal strings"),
    )
    for payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_research_decision_change_log_public_payload(payload)


def test_hard_flags_are_required_on_all_public_models() -> None:
    module = api()
    change_log = report(change_record())

    assert change_log.paper_only is True
    assert change_log.report_only is True
    assert change_log.readonly is True
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        change_record(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(change_log, readonly=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.research_decision_change_log_payload(replace(change_log, readonly=False))


def test_payload_output_is_deterministic_and_digest_checked() -> None:
    module = api()
    first = report(
        change_record(redacted_candidate_ref=REF_B, score_after=d("0.790000")),
        change_record(redacted_candidate_ref=REF_A, score_after=d("0.480000")),
    )
    second = report(
        change_record(redacted_candidate_ref=REF_A, score_after=d("0.480000")),
        change_record(redacted_candidate_ref=REF_B, score_after=d("0.790000")),
    )

    assert first == second
    assert first.rows[0].redacted_candidate_ref == REF_A
    assert first.rows[1].redacted_candidate_ref == REF_B
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_decision_change_log_payload(first) == (
        module.research_decision_change_log_payload(second)
    )
    assert list(module.research_decision_change_log_payload(first)) == [
        "generated_at",
        "config_version",
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_abs_score_delta",
        "max_abs_evidence_quality_delta",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ]

    rebuilt = module.ResearchDecisionChangeLogReport(**public_field_values(first))
    assert rebuilt == first

    object.__setattr__(first, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_decision_change_log_payload(first)


def test_module_surface_stays_pure_report_only_and_unwired() -> None:
    module = api()
    source = Path("src/polymarket_alpha_lab/research_decision_change_log.py").read_text(
        encoding="utf-8",
    )

    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

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
    assert module.__all__ == (
        "CHANGE_STATUSES",
        "DEFAULT_RESEARCH_DECISION_CHANGE_LOG_CONFIG_VERSION",
        "ResearchDecisionChangeLogConfig",
        "ResearchDecisionChangeLogRecord",
        "ResearchDecisionChangeLogRow",
        "ResearchDecisionChangeLogReasonCodeCount",
        "ResearchDecisionChangeLogReport",
        "build_research_decision_change_log",
        "research_decision_change_log_payload",
        "validate_research_decision_change_log_public_payload",
    )
