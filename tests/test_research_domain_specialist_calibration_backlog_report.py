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
OBSERVED_AT = datetime(2026, 7, 8, 11, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_specialist_calibration_backlog_report",
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
    return module.ResearchDomainSpecialistCalibrationBacklogConfig(**overrides)


def input_row(
    domain_label: str,
    specialist_team_label: str,
    *,
    calibration_sample_count: Decimal = d("150.000000"),
    feedback_age_seconds: Decimal = d("3600.000000"),
    error_taxonomy_coverage_ratio: Decimal = d("0.960000"),
    domain_queue_load_count: Decimal = d("3.000000"),
    escalation_urgency_score: Decimal = d("0.100000"),
    observed_at: datetime = OBSERVED_AT,
):
    module = api()
    return module.ResearchDomainSpecialistCalibrationBacklogInput(
        domain_label=domain_label,
        specialist_team_label=specialist_team_label,
        calibration_sample_count=calibration_sample_count,
        feedback_age_seconds=feedback_age_seconds,
        error_taxonomy_coverage_ratio=error_taxonomy_coverage_ratio,
        domain_queue_load_count=domain_queue_load_count,
        escalation_urgency_score=escalation_urgency_score,
        observed_at=observed_at,
    )


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_domain_specialist_calibration_backlog_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_domain_specialist_calibration_backlog_scores_rows_and_digest() -> None:
    rows = (
        input_row("sports_soccer", "team_referee_rules"),
        input_row(
            "politics_elections",
            "team_settlement_rules",
            calibration_sample_count=d("20.000000"),
            feedback_age_seconds=d("900000.000000"),
            error_taxonomy_coverage_ratio=d("0.400000"),
            domain_queue_load_count=d("40.000000"),
            escalation_urgency_score=d("0.950000"),
        ),
        input_row(
            "crypto_protocols",
            "team_chain_events",
            calibration_sample_count=d("75.000000"),
            feedback_age_seconds=d("172800.000000"),
            error_taxonomy_coverage_ratio=d("0.800000"),
            domain_queue_load_count=d("12.000000"),
            escalation_urgency_score=d("0.750000"),
        ),
    )

    report = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert api().CALIBRATION_BACKLOG_STATUSES == ("pass", "watch", "block")
    assert report.status == "block"
    assert report.escalation_mode == "paper_calibration_backlog_block"
    assert report.input_count == d("3.000000")
    assert report.backlog_item_count == d("2.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.backlog_ratio == d("0.666667")
    assert report.max_backlog_pressure_score == d("1.000000")
    assert report.min_calibration_sample_count == d("20.000000")
    assert report.max_feedback_age_seconds == d("900000.000000")
    assert report.min_error_taxonomy_coverage_ratio == d("0.400000")
    assert report.max_domain_queue_load_count == d("40.000000")
    assert report.max_escalation_urgency_score == d("0.950000")

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.backlog_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert blocked.domain_label == "politics_elections"
    assert blocked.sample_scarcity_ratio == d("0.800000")
    assert blocked.error_taxonomy_gap_ratio == d("0.600000")
    assert blocked.domain_queue_load_ratio == d("1.000000")
    assert blocked.backlog_pressure_score == d("1.000000")
    assert blocked.reason_codes == (
        "domain_specialist_calibration_sample_scarcity_block",
        "domain_specialist_calibration_stale_feedback_block",
        "domain_specialist_calibration_error_taxonomy_coverage_block",
        "domain_specialist_calibration_queue_load_block",
        "domain_specialist_calibration_escalation_urgency_block",
    )
    assert watched.reason_codes == (
        "domain_specialist_calibration_sample_scarcity_watch",
        "domain_specialist_calibration_stale_feedback_watch",
        "domain_specialist_calibration_error_taxonomy_coverage_watch",
        "domain_specialist_calibration_queue_load_watch",
        "domain_specialist_calibration_escalation_urgency_watch",
    )
    assert passed.reason_codes == ("domain_specialist_calibration_backlog_clear",)
    assert (
        api().ResearchDomainSpecialistCalibrationBacklogReasonCodeCount(
            reason_code="domain_specialist_calibration_stale_feedback_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
        in report.reason_code_counts
    )

    payload = api().research_domain_specialist_calibration_backlog_report_payload(report)
    reversed_payload = api().research_domain_specialist_calibration_backlog_report_payload(
        reversed_report,
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["backlog_pressure_score"] == "1.000000"
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_domain_specialist_calibration_backlog_is_report_only_public_safe() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_DOMAIN_SPECIALIST_CALIBRATION_BACKLOG_CONFIG_VERSION",
        "CALIBRATION_BACKLOG_STATUSES",
        "ResearchDomainSpecialistCalibrationBacklogConfig",
        "ResearchDomainSpecialistCalibrationBacklogInput",
        "ResearchDomainSpecialistCalibrationBacklogReasonCodeCount",
        "ResearchDomainSpecialistCalibrationBacklogReport",
        "ResearchDomainSpecialistCalibrationBacklogRow",
        "build_research_domain_specialist_calibration_backlog_report",
        "research_domain_specialist_calibration_backlog_report_digest",
        "research_domain_specialist_calibration_backlog_report_payload",
    )

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    empty = build_report()
    assert empty.status == "pass"
    assert empty.escalation_mode == "paper_calibration_monitor"
    assert empty.reason_codes == ("domain_specialist_calibration_backlog_empty",)
    assert empty.input_count == ZERO
    assert empty.backlog_item_count == ZERO
    assert empty.reason_code_counts == ()
    assert empty.rows == ()

    populated = build_report(input_row("macro_rates", "team_policy_events"))
    for value in (
        populated,
        *populated.rows,
        *populated.reason_code_counts,
        config(),
        input_row("sports_tennis", "team_match_results"),
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item is None:
                continue
            if field.name.endswith(("_count", "_ratio", "_score", "_seconds")):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="calibration_sample_count must be a Decimal"):
        input_row("macro", "team_policy", calibration_sample_count=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        input_row(
            "macro",
            "team_policy",
            observed_at=datetime(2026, 7, 8, 10, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            input_row("macro_rates", "team_policy"),
            generated_at=datetime(
                2026,
                7,
                8,
                12,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="team labels must be unique"):
        build_report(
            input_row("macro_rates", "team_policy"),
            input_row("macro_rates", "team_policy"),
        )
    with pytest.raises(ValueError, match="error_taxonomy_coverage_ratio"):
        input_row(
            "macro_rates",
            "team_policy",
            error_taxonomy_coverage_ratio=d("1.100000"),
        )
    with pytest.raises(ValueError, match="public aggregate label"):
        input_row("macro_http_ref", "team_policy")
    with pytest.raises(ValueError, match="max_watch_domain_queue_load_count"):
        config(
            max_pass_domain_queue_load_count=d("20.000000"),
            max_watch_domain_queue_load_count=d("10.000000"),
        )

    payload = module.research_domain_specialist_calibration_backlog_report_payload(
        populated,
    )
    assert module.research_domain_specialist_calibration_backlog_report_digest(populated) == (
        payload["derived_validation_digest"]
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    for unsafe_key in (
        "market_id",
        "source_table",
        "dsn",
        "private_key",
        "auth_session",
        "trade_id",
        "sizing_model",
        "recommendation",
    ):
        forged_payload = dict(payload)
        forged_payload[unsafe_key] = "public_aggregate"
        forged_payload["derived_validation_digest"] = canonical_digest(forged_payload)
        with pytest.raises(ValueError, match="public aggregate labels"):
            module.research_domain_specialist_calibration_backlog_report_payload(
                forged_payload,
            )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "wallet",
        "order",
        "live",
        "trading",
        "database",
        "network",
        "buy",
        "sell",
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
