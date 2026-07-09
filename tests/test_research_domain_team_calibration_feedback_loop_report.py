from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
LAST_REVIEWED_AT = datetime(2026, 7, 8, 11, 0, tzinfo=UTC)
MODULE_NAME = (
    "polymarket_alpha_lab.research_domain_team_calibration_feedback_loop_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_domain_team_calibration_feedback_loop_report.py"
)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object) -> Any:
    module = api()
    return module.ResearchDomainTeamCalibrationFeedbackLoopConfig(**overrides)


def input_row(
    domain_label: str,
    specialist_team_label: str,
    *,
    resolved_outcome_count: Decimal = d("100.000000"),
    calibration_note_count: Decimal = d("96.000000"),
    recurring_bias_label_count: Decimal = d("85.000000"),
    future_review_safeguard_count: Decimal = d("90.000000"),
    unreviewed_bias_label_count: Decimal = d("0.000000"),
    feedback_last_reviewed_at: datetime | None = LAST_REVIEWED_AT,
    observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchDomainTeamCalibrationFeedbackLoopInput(
        domain_label=domain_label,
        specialist_team_label=specialist_team_label,
        resolved_outcome_count=resolved_outcome_count,
        calibration_note_count=calibration_note_count,
        recurring_bias_label_count=recurring_bias_label_count,
        future_review_safeguard_count=future_review_safeguard_count,
        unreviewed_bias_label_count=unreviewed_bias_label_count,
        feedback_last_reviewed_at=feedback_last_reviewed_at,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_domain_team_calibration_feedback_loop_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_feedback_loop_report_scores_rows_rollups_and_digest_deterministically() -> None:
    rows = (
        input_row("sports_rules", "team_resolution_memory"),
        input_row(
            "macro_policy",
            "team_calibration_notes",
            resolved_outcome_count=d("50.000000"),
            calibration_note_count=d("38.000000"),
            recurring_bias_label_count=d("30.000000"),
            future_review_safeguard_count=d("34.000000"),
            unreviewed_bias_label_count=d("2.000000"),
            feedback_last_reviewed_at=GENERATED_AT - timedelta(days=2),
        ),
        input_row(
            "crypto_protocols",
            "team_settlement_bias",
            resolved_outcome_count=d("8.000000"),
            calibration_note_count=d("2.000000"),
            recurring_bias_label_count=d("1.000000"),
            future_review_safeguard_count=d("1.000000"),
            unreviewed_bias_label_count=d("5.000000"),
            feedback_last_reviewed_at=GENERATED_AT - timedelta(seconds=900000),
        ),
    )

    report = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert api().CALIBRATION_FEEDBACK_LOOP_STATUSES == ("pass", "watch", "block")
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.resolved_outcome_count == d("158.000000")
    assert report.calibration_note_coverage_ratio == d("0.860759")
    assert report.recurring_bias_label_coverage_ratio == d("0.734177")
    assert report.future_review_safeguard_coverage_ratio == d("0.791139")
    assert report.max_feedback_age_seconds == d("900000.000000")
    assert report.max_unreviewed_bias_label_count == d("5.000000")

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.feedback_loop_rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert blocked.domain_label == "crypto_protocols"
    assert blocked.specialist_team_label == "team_settlement_bias"
    assert blocked.calibration_note_coverage_ratio == d("0.250000")
    assert blocked.recurring_bias_label_coverage_ratio == d("0.125000")
    assert blocked.future_review_safeguard_coverage_ratio == d("0.125000")
    assert blocked.feedback_loop_health_score == d("0.125000")
    assert blocked.feedback_age_seconds == d("900000.000000")
    assert blocked.reason_codes == (
        "domain_team_feedback_resolved_outcome_sample_block",
        "domain_team_feedback_calibration_note_coverage_block",
        "domain_team_feedback_recurring_bias_label_coverage_block",
        "domain_team_feedback_future_safeguard_coverage_block",
        "domain_team_feedback_stale_review_block",
        "domain_team_feedback_unreviewed_bias_label_block",
    )
    assert watched.reason_codes == (
        "domain_team_feedback_calibration_note_coverage_watch",
        "domain_team_feedback_recurring_bias_label_coverage_watch",
        "domain_team_feedback_future_safeguard_coverage_watch",
        "domain_team_feedback_stale_review_watch",
        "domain_team_feedback_unreviewed_bias_label_watch",
    )
    assert passed.reason_codes == ("domain_team_feedback_loop_pass",)

    payload = api().research_domain_team_calibration_feedback_loop_report_payload(report)
    reversed_payload = api().research_domain_team_calibration_feedback_loop_report_payload(
        reversed_report,
    )
    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["feedback_loop_health_score"] == "0.125000"
    assert _float_or_int_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_feedback_loop_report_is_frozen_decimal_only_and_flag_hardened() -> None:
    module = api()
    report = build_report(input_row("macro_rates", "team_policy_memory"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_DOMAIN_TEAM_CALIBRATION_FEEDBACK_LOOP_CONFIG_VERSION",
        "CALIBRATION_FEEDBACK_LOOP_STATUSES",
        "ResearchDomainTeamCalibrationFeedbackLoopConfig",
        "ResearchDomainTeamCalibrationFeedbackLoopInput",
        "ResearchDomainTeamCalibrationFeedbackLoopReport",
        "ResearchDomainTeamCalibrationFeedbackLoopRow",
        "build_research_domain_team_calibration_feedback_loop_report",
        "research_domain_team_calibration_feedback_loop_report_digest",
        "research_domain_team_calibration_feedback_loop_report_payload",
        "validate_research_domain_team_calibration_feedback_loop_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    empty = build_report()
    assert empty.status == "pass"
    assert empty.reason_codes == ("domain_team_feedback_loop_empty",)
    assert empty.rows == ()
    assert empty.input_count == d("0.000000")

    for value in (config(), input_row("sports_tennis", "team_match_memory"), report, *report.rows):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if isinstance(item, Decimal):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="resolved_outcome_count must be a Decimal"):
        input_row("macro_rates", "team_policy_memory", resolved_outcome_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="calibration_note_count must be a Decimal"):
        input_row(
            "macro_rates",
            "team_policy_memory",
            calibration_note_count=DecimalSubclass("1.000000"),
        )
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        input_row(
            "macro_rates",
            "team_policy_memory",
            observed_at=datetime(2026, 7, 8, 10, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            input_row("macro_rates", "team_policy_memory"),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
        )
    with pytest.raises(ValueError, match="team labels must be unique"):
        build_report(
            input_row("macro_rates", "team_policy_memory"),
            input_row("macro_rates", "team_policy_memory"),
        )
    with pytest.raises(ValueError, match="future_review_safeguard_count"):
        input_row(
            "macro_rates",
            "team_policy_memory",
            resolved_outcome_count=d("2.000000"),
            calibration_note_count=d("1.000000"),
            recurring_bias_label_count=d("1.000000"),
            future_review_safeguard_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="public aggregate label"):
        input_row("macro_market_slug", "team_policy_memory")


def test_public_payload_validator_rejects_identifier_source_and_live_surface_leaks() -> None:
    module = api()
    report = build_report(input_row("macro_rates", "team_policy_memory"))
    payload = module.research_domain_team_calibration_feedback_loop_report_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert module.research_domain_team_calibration_feedback_loop_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    module.validate_research_domain_team_calibration_feedback_loop_public_payload(payload)

    for unsafe_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "position_sizing",
    ):
        forged_payload = dict(payload)
        forged_payload[unsafe_key] = "public_aggregate"
        forged_payload["derived_validation_digest"] = canonical_digest(forged_payload)
        with pytest.raises(ValueError, match="public aggregate labels|unsafe"):
            module.research_domain_team_calibration_feedback_loop_report_payload(
                forged_payload,
            )

    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_research_domain_team_calibration_feedback_loop_public_payload(
            {**payload, "input_count": 1},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_domain_team_calibration_feedback_loop_public_payload(
            {**payload, "readonly": False},
        )
    for forged_payload, match in (
        ({**payload, "status": "hold"}, "status"),
        ({**payload, "rows": [{**payload["rows"][0], "status": "hold"}]}, "status"),
        (
            {**payload, "rows": [{**payload["rows"][0], "readonly": False}]},
            "readonly",
        ),
    ):
        forged_payload["derived_validation_digest"] = canonical_digest(forged_payload)
        with pytest.raises(ValueError, match=match):
            module.validate_research_domain_team_calibration_feedback_loop_public_payload(
                forged_payload,
            )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_domain_team_calibration_feedback_loop_public_payload(
            {**payload, "input_count": "9.000000"},
        )


def test_module_scope_is_pure_in_memory_readonly_report_only() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests.",
        "urllib",
        "sqlite",
        "psycopg",
        "supabase",
        "sqlalchemy",
        "subprocess",
        "socket",
        "open(",
        "getenv",
        "environ",
        "postgres",
        "://",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
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
                "place_order",
                "submit_order",
                "cancel_order",
            }

    assert not imported_roots.intersection(
        {
            "requests",
            "urllib",
            "httpx",
            "socket",
            "psycopg",
            "sqlite3",
            "sqlalchemy",
            "supabase",
            "subprocess",
        },
    )


def _float_or_int_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if type(value) in (float, int):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_float_or_int_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_float_or_int_paths(nested, child))
        return tuple(paths)
    return ()
