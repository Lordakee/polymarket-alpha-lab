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


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_specialist_calibration_drift_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_calibration_drift_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-specialist-calibration-drift-report-v0",
        "min_recent_resolved_outcome_count": d("10"),
        "watch_calibration_error_rate": d("0.060000"),
        "block_calibration_error_rate": d("0.120000"),
        "max_pass_stale_memory_signal_count": d("0"),
        "max_watch_stale_memory_signal_count": d("2"),
        "max_pass_bias_flag_count": d("0"),
        "max_watch_bias_flag_count": d("1"),
        "min_pass_correction_follow_through_ratio": d("0.900000"),
        "min_watch_correction_follow_through_ratio": d("0.700000"),
        "min_pass_source_family_count": d("3"),
        "min_watch_source_family_count": d("2"),
        "max_pass_workload_pressure_score": d("0.500000"),
        "max_watch_workload_pressure_score": d("0.800000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistCalibrationDriftConfig(**values)


def specialist_signal(**overrides: object):
    module = api()
    values = {
        "team_key": "macro_rates",
        "team_domain": "macro",
        "observed_at": GENERATED_AT - timedelta(minutes=30),
        "recent_resolved_outcome_count": d("20"),
        "calibration_error_rate": d("0.030000"),
        "stale_memory_signal_count": d("0"),
        "bias_flag_count": d("0"),
        "pending_correction_count": d("0"),
        "correction_follow_through_ratio": d("0.950000"),
        "source_family_count": d("4"),
        "workload_pressure_score": d("0.250000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistCalibrationDriftInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_specialist_calibration_drift_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "http://",
        "https://",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "position",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name in {"paper_only", "report_only", "readonly"}:
            assert item is True
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
        if field.name.endswith(("_count", "_rate", "_ratio", "_score", "_seconds")):
            assert type(item) is Decimal


def resigned_payload(payload: dict[str, Any]) -> dict[str, Any]:
    def strip_digest(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: strip_digest(item)
                for key, item in sorted(value.items())
                if key != "derived_validation_digest"
            }
        if isinstance(value, list):
            return [strip_digest(item) for item in value]
        return value

    resigned = json.loads(json.dumps(payload, allow_nan=False, sort_keys=True))
    canonical = json.dumps(
        strip_digest(resigned),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    resigned["derived_validation_digest"] = sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return resigned


def test_specialist_calibration_drift_rolls_up_pass_watch_and_block() -> None:
    report = build_report(
        specialist_signal(team_key="sports_soccer", team_domain="sports"),
        specialist_signal(
            team_key="macro_rates",
            team_domain="macro",
            observed_at=GENERATED_AT - timedelta(hours=2),
            calibration_error_rate=d("0.150000"),
            stale_memory_signal_count=d("3"),
            bias_flag_count=d("2"),
            pending_correction_count=d("4"),
            correction_follow_through_ratio=d("0.600000"),
            source_family_count=d("1"),
            workload_pressure_score=d("0.900000"),
        ),
        specialist_signal(
            team_key="crypto_policy",
            team_domain="crypto",
            observed_at=GENERATED_AT - timedelta(hours=1),
            calibration_error_rate=d("0.080000"),
            stale_memory_signal_count=d("1"),
            bias_flag_count=d("1"),
            pending_correction_count=d("2"),
            correction_follow_through_ratio=d("0.800000"),
            source_family_count=d("2"),
            workload_pressure_score=d("0.650000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-team-specialist-calibration-drift-report-v0"
    assert report.status == "block"
    assert report.specialist_team_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.drift_team_count == d("2")
    assert report.stale_memory_team_count == d("2")
    assert report.bias_flag_team_count == d("2")
    assert report.correction_gap_team_count == d("2")
    assert report.source_coverage_gap_team_count == d("2")
    assert report.workload_pressure_team_count == d("2")
    assert report.total_recent_resolved_outcome_count == d("60")
    assert report.average_calibration_error_rate == d("0.086667")
    assert report.max_calibration_error_rate == d("0.150000")
    assert report.min_correction_follow_through_ratio == d("0.600000")
    assert report.min_source_family_count == d("1")
    assert report.max_workload_pressure_score == d("0.900000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, watched, passed = report.rows
    assert tuple((row.status, row.team_domain) for row in report.rows) == (
        ("block", "macro"),
        ("watch", "crypto"),
        ("pass", "sports"),
    )
    assert blocked.observation_age_seconds == d("7200.000000")
    assert blocked.reason_codes == (
        "specialist_calibration_error_block",
        "specialist_stale_memory_block",
        "specialist_bias_flag_block",
        "specialist_correction_follow_through_block",
        "specialist_source_coverage_block",
        "specialist_workload_pressure_block",
    )
    assert watched.reason_codes == (
        "specialist_calibration_error_watch",
        "specialist_stale_memory_watch",
        "specialist_bias_flag_watch",
        "specialist_correction_follow_through_watch",
        "specialist_source_coverage_watch",
        "specialist_workload_pressure_watch",
    )
    assert passed.reason_codes == ("specialist_calibration_drift_clear",)
    assert report.reason_codes[:2] == (
        "specialist_calibration_drift_report_block",
        "specialist_calibration_error_block",
    )
    assert len(report.derived_validation_digest) == 64


def test_empty_and_low_recent_outcome_reports_block() -> None:
    module = api()
    empty = build_report()

    assert empty.status == "block"
    assert empty.specialist_team_count == d("0")
    assert empty.rows == ()
    assert empty.reason_codes == ("specialist_calibration_drift_no_teams",)
    assert empty.reason_code_counts == (
        module.ResearchTeamSpecialistCalibrationDriftReasonCodeCount(
            reason_code="specialist_calibration_drift_no_teams",
            count=d("1"),
            team_ratio=d("1.000000"),
        ),
    )

    thin = build_report(specialist_signal(recent_resolved_outcome_count=d("4")))
    assert thin.status == "block"
    assert thin.block_count == d("1")
    assert thin.rows[0].reason_codes == (
        "specialist_recent_outcomes_below_minimum",
    )


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    module = api()
    left = specialist_signal(team_key="sports_soccer", team_domain="sports")
    right = specialist_signal(
        team_key="crypto_policy",
        team_domain="crypto",
        observed_at=datetime(2026, 7, 8, 4, 0, tzinfo=timezone(timedelta(hours=-7))),
        calibration_error_rate=d("0.080000"),
        stale_memory_signal_count=d("1"),
        bias_flag_count=d("1"),
        pending_correction_count=d("2"),
        correction_follow_through_ratio=d("0.800000"),
        source_family_count=d("2"),
        workload_pressure_score=d("0.650000"),
    )

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload = module.research_team_specialist_calibration_drift_report_payload(report_a)

    assert payload == module.research_team_specialist_calibration_drift_report_payload(
        report_b,
    )
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload["specialist_team_count"] == "2"
    assert payload["average_calibration_error_rate"] == "0.055000"
    assert payload["rows"][0]["observation_age_seconds"] == "3600.000000"
    assert payload["rows"][0]["team_digest"].startswith("sha256:")
    assert "team_key" not in json.dumps(payload, sort_keys=True)
    assert "sports_soccer" not in json.dumps(payload, sort_keys=True)
    assert "crypto_policy" not in json.dumps(payload, sort_keys=True)
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert_no_public_numeric_values(payload)
    assert_public_payload_has_no_forbidden_surface(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest does not match"):
        module.research_team_specialist_calibration_drift_report_payload(tampered)

    unsafe = dict(payload)
    unsafe["source_url"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_specialist_calibration_drift_report_payload(unsafe)


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    (
        ("contradictory_status", "status must match rows"),
        ("raw_team_key", "unexpected public payload field"),
    ),
)
def test_payload_dict_revalidation_rejects_digest_correct_public_bypasses(
    mutation: str,
    expected_error: str,
) -> None:
    module = api()
    payload = module.research_team_specialist_calibration_drift_report_payload(
        build_report(specialist_signal(calibration_error_rate=d("0.150000"))),
    )
    assert payload["status"] == "block"

    forged = json.loads(json.dumps(payload, allow_nan=False, sort_keys=True))
    if mutation == "contradictory_status":
        forged["status"] = "pass"
    elif mutation == "raw_team_key":
        forged["team_key"] = "macro_rates"
    else:  # pragma: no cover - defensive for future parametrization edits.
        raise AssertionError(mutation)

    with pytest.raises(ValueError, match=expected_error):
        module.research_team_specialist_calibration_drift_report_payload(
            resigned_payload(forged),
        )


def test_validates_decimal_flags_statuses_and_frozen_dataclasses() -> None:
    module = api()
    cfg = config()
    item = specialist_signal()
    report = build_report(item)

    for value in (cfg, item, report.rows[0], report.reason_code_counts[0], report):
        assert_decimal_public_fields(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="calibration_error_rate must be a Decimal"):
        specialist_signal(calibration_error_rate=0.1)
    with pytest.raises(ValueError, match="workload_pressure_score must be a Decimal"):
        specialist_signal(workload_pressure_score=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="recent_resolved_outcome_count must be integral"):
        specialist_signal(recent_resolved_outcome_count=d("1.5"))
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        build_report(specialist_signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        replace(report.rows[0], status="review")
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchTeamSpecialistCalibrationDriftConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="unsafe public"):
        specialist_signal(team_key="market_alpha")
    with pytest.raises(ValueError, match="unsafe public"):
        specialist_signal(team_domain="source_ops")


def test_module_stays_report_only_without_live_or_storage_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sql",
        "subprocess",
        "urllib",
    )
    forbidden_call_fragments = (
        "connect",
        "delete",
        "execute",
        "insert",
        "open",
        "patch",
        "post",
        "put",
        "request",
        "send",
        "sign",
        "submit",
        "update",
        "write",
    )
    forbidden_attribute_fragments = (
        "private_key",
        "place_order",
        "submit_order",
        "wallet",
    )

    assert float_constants == []
    assert not any(
        fragment in imported.lower()
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(
        fragment in call.lower()
        for call in call_names
        for fragment in forbidden_call_fragments
    )
    assert not any(
        fragment in attribute.lower()
        for attribute in attribute_names
        for fragment in forbidden_attribute_fragments
    )
