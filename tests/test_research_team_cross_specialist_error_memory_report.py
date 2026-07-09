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


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_cross_specialist_error_memory_report",
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
    return module.ResearchTeamCrossSpecialistErrorMemoryConfig(**overrides)


def item(
    primary_specialist_label: str,
    comparison_specialist_label: str,
    error_pattern_label: str,
    *,
    team_label: str = "research_alpha",
    shared_error_count: Decimal = ZERO,
    unresolved_repeat_count: Decimal = ZERO,
    cross_specialist_overlap_ratio: Decimal = d("0.100000"),
    specialist_agreement_gap_score: Decimal = d("0.100000"),
    memory_age_seconds: Decimal = d("3600.000000"),
    corrective_playbook_coverage_ratio: Decimal = d("0.900000"),
    observed_at: datetime = OBSERVED_AT,
):
    module = api()
    return module.ResearchTeamCrossSpecialistErrorMemoryInput(
        team_label=team_label,
        primary_specialist_label=primary_specialist_label,
        comparison_specialist_label=comparison_specialist_label,
        error_pattern_label=error_pattern_label,
        shared_error_count=shared_error_count,
        unresolved_repeat_count=unresolved_repeat_count,
        cross_specialist_overlap_ratio=cross_specialist_overlap_ratio,
        specialist_agreement_gap_score=specialist_agreement_gap_score,
        memory_age_seconds=memory_age_seconds,
        corrective_playbook_coverage_ratio=corrective_playbook_coverage_ratio,
        observed_at=observed_at,
    )


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_cross_specialist_error_memory_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_cross_specialist_error_memory_scores_rows_and_digest() -> None:
    rows = (
        item("sports_rules", "macro_policy", "late_rule_update"),
        item(
            "macro_policy",
            "crypto_protocols",
            "resolution_evidence_lag",
            shared_error_count=d("2.000000"),
            unresolved_repeat_count=d("1.000000"),
            cross_specialist_overlap_ratio=d("0.400000"),
            specialist_agreement_gap_score=d("0.450000"),
            memory_age_seconds=d("172800.000000"),
            corrective_playbook_coverage_ratio=d("0.700000"),
        ),
        item(
            "crypto_protocols",
            "sports_rules",
            "ambiguous_resolution_rule",
            shared_error_count=d("5.000000"),
            unresolved_repeat_count=d("3.000000"),
            cross_specialist_overlap_ratio=d("0.800000"),
            specialist_agreement_gap_score=d("0.900000"),
            memory_age_seconds=d("900000.000000"),
            corrective_playbook_coverage_ratio=d("0.200000"),
        ),
    )

    report = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert api().CROSS_SPECIALIST_ERROR_MEMORY_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "block"
    assert report.paper_review_urgency == "paper_cross_specialist_memory_block"
    assert report.input_count == d("3.000000")
    assert report.active_memory_count == d("2.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.active_memory_ratio == d("0.666667")
    assert report.total_shared_error_count == d("7.000000")
    assert report.total_unresolved_repeat_count == d("4.000000")
    assert report.average_cross_specialist_overlap_ratio == d("0.433333")
    assert report.average_specialist_agreement_gap_score == d("0.483333")
    assert report.min_corrective_playbook_coverage_ratio == d("0.200000")
    assert report.max_memory_age_seconds == d("900000.000000")
    assert report.max_error_memory_pressure_score == d("1.000000")

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.memory_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert blocked.primary_specialist_label == "crypto_protocols"
    assert blocked.error_memory_pressure_score == d("1.000000")
    assert blocked.reason_codes == (
        "cross_specialist_shared_error_count_block",
        "cross_specialist_unresolved_repeat_count_block",
        "cross_specialist_overlap_ratio_block",
        "cross_specialist_agreement_gap_block",
        "cross_specialist_memory_age_block",
        "cross_specialist_playbook_coverage_block",
    )
    assert watched.reason_codes == (
        "cross_specialist_shared_error_count_watch",
        "cross_specialist_unresolved_repeat_count_watch",
        "cross_specialist_overlap_ratio_watch",
        "cross_specialist_agreement_gap_watch",
        "cross_specialist_memory_age_watch",
        "cross_specialist_playbook_coverage_watch",
    )
    assert passed.reason_codes == ("cross_specialist_error_memory_clear",)
    assert (
        api().ResearchTeamCrossSpecialistErrorMemoryReasonCodeCount(
            reason_code="cross_specialist_playbook_coverage_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
        in report.reason_code_counts
    )

    payload = api().research_team_cross_specialist_error_memory_report_payload(report)
    reversed_payload = (
        api().research_team_cross_specialist_error_memory_report_payload(
            reversed_report,
        )
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"][0]["error_memory_pressure_score"] == "1.000000"
    assert payload["rows"][0]["corrective_playbook_coverage_ratio"] == "0.200000"
    assert _float_paths(payload) == ()
    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "candidate-raw-123",
        "market-raw-123",
        "event-slug",
        "Will this resolve",
        "http://private.example",
        "postgresql://private",
        "orders_table",
        "private_token_value",
        "wallet_abc",
    ):
        assert forbidden not in encoded


def test_cross_specialist_error_memory_is_public_safe_report_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_CROSS_SPECIALIST_ERROR_MEMORY_REPORT_CONFIG_VERSION",
        "CROSS_SPECIALIST_ERROR_MEMORY_REPORT_STATUSES",
        "ResearchTeamCrossSpecialistErrorMemoryConfig",
        "ResearchTeamCrossSpecialistErrorMemoryInput",
        "ResearchTeamCrossSpecialistErrorMemoryReasonCodeCount",
        "ResearchTeamCrossSpecialistErrorMemoryReport",
        "ResearchTeamCrossSpecialistErrorMemoryRow",
        "build_research_team_cross_specialist_error_memory_report",
        "research_team_cross_specialist_error_memory_report_digest",
        "research_team_cross_specialist_error_memory_report_payload",
    )

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    empty = build_report()
    assert empty.status == "pass"
    assert empty.paper_review_urgency == "paper_cross_specialist_memory_monitor"
    assert empty.reason_codes == ("cross_specialist_error_memory_empty",)
    assert empty.input_count == ZERO
    assert empty.active_memory_count == ZERO
    assert empty.reason_code_counts == ()
    assert empty.rows == ()

    populated = build_report(item("sports_tennis", "macro_rates", "late_update"))
    for value in (
        populated,
        *populated.rows,
        *populated.reason_code_counts,
        config(),
        item("macro_rates", "sports_tennis", "policy_calendar_miss"),
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
    with pytest.raises(ValueError, match="shared_error_count must be a Decimal"):
        item(
            "macro",
            "sports",
            "policy",
            shared_error_count=1.0,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        item(
            "macro",
            "sports",
            "policy",
            observed_at=datetime(2026, 7, 9, 10, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            item("macro_rates", "sports_rules", "policy_calendar_miss"),
            generated_at=datetime(
                2026,
                7,
                9,
                12,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="cross specialist labels must be unique"):
        build_report(
            item("macro_rates", "sports_rules", "policy_calendar_miss"),
            item("macro_rates", "sports_rules", "policy_calendar_miss"),
        )
    with pytest.raises(ValueError, match="specialist labels must differ"):
        item("macro_rates", "macro_rates", "policy_calendar_miss")
    with pytest.raises(ValueError, match="cross_specialist_overlap_ratio"):
        item(
            "macro_rates",
            "sports_rules",
            "policy_calendar_miss",
            cross_specialist_overlap_ratio=d("1.100000"),
        )
    with pytest.raises(ValueError, match="public aggregate label"):
        item("macro_http_ref", "sports_rules", "policy_calendar_miss")
    with pytest.raises(ValueError, match="unsafe"):
        item("macro_rates", "sports_rules", "candidate_raw_ref")
    with pytest.raises(ValueError, match="max_watch_shared_error_count"):
        config(
            max_pass_shared_error_count=d("5.000000"),
            max_watch_shared_error_count=d("3.000000"),
        )

    payload = module.research_team_cross_specialist_error_memory_report_payload(
        populated,
    )
    assert module.research_team_cross_specialist_error_memory_report_digest(
        populated,
    ) == payload["derived_validation_digest"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_cross_specialist_error_memory_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "market_id": "market-raw-123",
            },
        )
    for unsafe_key, unsafe_value in (
        ("recommendation_surface", "watch"),
        ("sizing_surface", "0.100000"),
        ("routing_surface", "paper"),
        ("execution_surface", "paper"),
        ("auth_surface", "paper"),
        ("live_trading_surface", "paper"),
        ("status", "recommend"),
        ("paper_review_urgency", "paper_order_route"),
    ):
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = unsafe_value
        unsafe_payload["derived_validation_digest"] = canonical_digest(unsafe_payload)
        with pytest.raises(ValueError, match="unsafe"):
            module.research_team_cross_specialist_error_memory_report_payload(
                unsafe_payload,
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
