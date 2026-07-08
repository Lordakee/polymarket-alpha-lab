from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_error_taxonomy_backlog_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    module = api()
    return module.ResearchTeamSpecialistErrorTaxonomyBacklogConfig(**overrides)


def item(
    specialist_label: str,
    error_category_label: str,
    *,
    unresolved_error_category_count: Decimal = ZERO,
    stale_calibration_feedback_count: Decimal = ZERO,
    impacted_domain_count: Decimal = d("1.000000"),
    available_reviewer_capacity_count: Decimal = d("3.000000"),
    memory_writeback_lag_seconds: Decimal = d("3600.000000"),
    manual_escalation_urgency_score: Decimal = d("0.100000"),
    observed_at: datetime = OBSERVED_AT,
):
    module = api()
    return module.ResearchTeamSpecialistErrorTaxonomyBacklogInput(
        specialist_label=specialist_label,
        error_category_label=error_category_label,
        unresolved_error_category_count=unresolved_error_category_count,
        stale_calibration_feedback_count=stale_calibration_feedback_count,
        impacted_domain_count=impacted_domain_count,
        available_reviewer_capacity_count=available_reviewer_capacity_count,
        memory_writeback_lag_seconds=memory_writeback_lag_seconds,
        manual_escalation_urgency_score=manual_escalation_urgency_score,
        observed_at=observed_at,
    )


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_specialist_error_taxonomy_backlog_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_specialist_error_taxonomy_backlog_scores_rows_and_digest() -> None:
    rows = (
        item("sports_rules", "settlement_ambiguity"),
        item(
            "macro_policy",
            "ambiguous_resolution_rule",
            unresolved_error_category_count=d("2.000000"),
            stale_calibration_feedback_count=d("1.000000"),
            impacted_domain_count=d("2.000000"),
            available_reviewer_capacity_count=d("1.000000"),
            memory_writeback_lag_seconds=d("172800.000000"),
            manual_escalation_urgency_score=d("0.700000"),
        ),
        item(
            "crypto_protocols",
            "oracle_dependency_gap",
            unresolved_error_category_count=d("5.000000"),
            stale_calibration_feedback_count=d("4.000000"),
            impacted_domain_count=d("5.000000"),
            available_reviewer_capacity_count=ZERO,
            memory_writeback_lag_seconds=d("900000.000000"),
            manual_escalation_urgency_score=d("0.950000"),
        ),
    )

    report = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert api().SPECIALIST_ERROR_TAXONOMY_BACKLOG_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "block"
    assert report.manual_escalation_urgency == "paper_manual_escalation_block"
    assert report.input_count == d("3.000000")
    assert report.backlog_item_count == d("2.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.backlog_ratio == d("0.666667")
    assert report.total_unresolved_error_category_count == d("7.000000")
    assert report.total_stale_calibration_feedback_count == d("5.000000")
    assert report.total_impacted_domain_count == d("8.000000")
    assert report.total_available_reviewer_capacity_count == d("4.000000")
    assert report.min_available_reviewer_capacity_count == ZERO
    assert report.max_memory_writeback_lag_seconds == d("900000.000000")
    assert report.max_manual_escalation_urgency_score == d("0.950000")
    assert report.max_backlog_pressure_score == d("1.000000")

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.backlog_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert blocked.specialist_label == "crypto_protocols"
    assert blocked.backlog_pressure_score == d("1.000000")
    assert blocked.reviewer_capacity_gap_count == d("2.000000")
    assert blocked.reviewer_capacity_gap_ratio == d("1.000000")
    assert blocked.reason_codes == (
        "specialist_error_taxonomy_unresolved_categories_block",
        "specialist_error_taxonomy_stale_calibration_feedback_block",
        "specialist_error_taxonomy_impacted_domain_count_block",
        "specialist_error_taxonomy_reviewer_capacity_block",
        "specialist_error_taxonomy_memory_writeback_lag_block",
        "specialist_error_taxonomy_manual_escalation_urgency_block",
    )
    assert watched.reason_codes == (
        "specialist_error_taxonomy_unresolved_categories_watch",
        "specialist_error_taxonomy_stale_calibration_feedback_watch",
        "specialist_error_taxonomy_impacted_domain_count_watch",
        "specialist_error_taxonomy_reviewer_capacity_watch",
        "specialist_error_taxonomy_memory_writeback_lag_watch",
        "specialist_error_taxonomy_manual_escalation_urgency_watch",
    )
    assert passed.reason_codes == ("specialist_error_taxonomy_backlog_clear",)
    assert (
        api().ResearchTeamSpecialistErrorTaxonomyBacklogReasonCodeCount(
            reason_code="specialist_error_taxonomy_manual_escalation_urgency_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
        in report.reason_code_counts
    )

    payload = api().research_team_specialist_error_taxonomy_backlog_report_payload(report)
    reversed_payload = (
        api().research_team_specialist_error_taxonomy_backlog_report_payload(
            reversed_report,
        )
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["backlog_pressure_score"] == "1.000000"
    assert payload["rows"][0]["available_reviewer_capacity_count"] == "0.000000"
    assert _float_paths(payload) == ()
    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "candidate-raw-123",
        "market-raw-123",
        "http://private.example",
        "postgresql://private",
        "orders_table",
        "private_token_value",
    ):
        assert forbidden not in encoded


def test_specialist_error_taxonomy_backlog_is_public_safe_report_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIST_ERROR_TAXONOMY_BACKLOG_REPORT_CONFIG_VERSION",
        "SPECIALIST_ERROR_TAXONOMY_BACKLOG_STATUSES",
        "ResearchTeamSpecialistErrorTaxonomyBacklogConfig",
        "ResearchTeamSpecialistErrorTaxonomyBacklogInput",
        "ResearchTeamSpecialistErrorTaxonomyBacklogReasonCodeCount",
        "ResearchTeamSpecialistErrorTaxonomyBacklogReport",
        "ResearchTeamSpecialistErrorTaxonomyBacklogRow",
        "build_research_team_specialist_error_taxonomy_backlog_report",
        "research_team_specialist_error_taxonomy_backlog_report_digest",
        "research_team_specialist_error_taxonomy_backlog_report_payload",
    )

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    empty = build_report()
    assert empty.status == "pass"
    assert empty.manual_escalation_urgency == "paper_manual_escalation_monitor"
    assert empty.reason_codes == ("specialist_error_taxonomy_backlog_empty",)
    assert empty.input_count == ZERO
    assert empty.backlog_item_count == ZERO
    assert empty.reason_code_counts == ()
    assert empty.rows == ()

    populated = build_report(item("sports_tennis", "late_injury_label"))
    for value in (
        populated,
        *populated.rows,
        *populated.reason_code_counts,
        config(),
        item("macro_rates", "policy_calendar_miss"),
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field_value is None:
                continue
            if field.name.endswith(("_count", "_ratio", "_score", "_seconds", "_rank")):
                assert type(field_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="unresolved_error_category_count must be a Decimal"):
        item(
            "macro",
            "policy",
            unresolved_error_category_count=1.0,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        item(
            "macro",
            "policy",
            observed_at=datetime(2026, 7, 8, 10, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            item("macro_rates", "policy_calendar_miss"),
            generated_at=datetime(
                2026,
                7,
                8,
                12,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="specialist error category labels must be unique"):
        build_report(
            item("macro_rates", "policy_calendar_miss"),
            item("macro_rates", "policy_calendar_miss"),
        )
    with pytest.raises(ValueError, match="manual_escalation_urgency_score"):
        item(
            "macro_rates",
            "policy_calendar_miss",
            manual_escalation_urgency_score=d("1.100000"),
        )
    with pytest.raises(ValueError, match="public aggregate label"):
        item("macro_http_ref", "policy_calendar_miss")
    with pytest.raises(ValueError, match="unsafe"):
        item("macro_rates", "candidate_raw_ref")
    with pytest.raises(ValueError, match="max_watch_unresolved_error_category_count"):
        config(
            max_pass_unresolved_error_category_count=d("5.000000"),
            max_watch_unresolved_error_category_count=d("3.000000"),
        )

    payload = module.research_team_specialist_error_taxonomy_backlog_report_payload(
        populated,
    )
    assert module.research_team_specialist_error_taxonomy_backlog_report_digest(
        populated,
    ) == payload["derived_validation_digest"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_specialist_error_taxonomy_backlog_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "candidate_id": "candidate-raw-123",
            },
        )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
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
