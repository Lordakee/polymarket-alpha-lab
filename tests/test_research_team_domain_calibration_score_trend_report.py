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
    "src/polymarket_alpha_lab/research_team_domain_calibration_score_trend_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_calibration_score_trend_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-domain-calibration-score-trend-report-v0",
        "min_resolved_outcome_count": d("5"),
        "watch_calibration_score_floor": d("0.700000"),
        "block_calibration_score_floor": d("0.550000"),
        "watch_forecast_error_worsening": d("0.030000"),
        "block_forecast_error_worsening": d("0.080000"),
        "min_pass_playbook_adoption_rate": d("0.850000"),
        "min_watch_playbook_adoption_rate": d("0.650000"),
        "min_pass_stale_memory_correction_rate": d("0.900000"),
        "min_watch_stale_memory_correction_rate": d("0.700000"),
        "max_pass_review_capacity_pressure_score": d("0.700000"),
        "max_watch_review_capacity_pressure_score": d("0.900000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainCalibrationScoreTrendConfig(**values)


def trend_signal(**overrides: object):
    module = api()
    values = {
        "team_key": "sports_soccer",
        "domain_key": "sports",
        "observed_at": GENERATED_AT - timedelta(minutes=30),
        "resolved_outcome_count": d("20"),
        "outcome_learning_score": d("0.900000"),
        "prior_forecast_error_rate": d("0.110000"),
        "current_forecast_error_rate": d("0.080000"),
        "playbook_adoption_rate": d("0.920000"),
        "stale_memory_correction_rate": d("0.950000"),
        "review_capacity_pressure_score": d("0.300000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainCalibrationScoreTrendInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_calibration_score_trend_report(
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


def payload_digest_for(payload: dict[str, Any]) -> str:
    comparable = json.loads(json.dumps(payload, allow_nan=False, sort_keys=True))
    comparable["payload_digest"] = ""
    payload_text = json.dumps(
        comparable,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(payload_text.encode("utf-8")).hexdigest()


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "http://",
        "https://",
        "url",
        "source",
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
        "live",
        "execute",
        "execution",
        "route",
        "size",
        "sizing",
        "recommend",
        "recommendation",
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


def test_domain_calibration_score_trend_rolls_up_pass_watch_and_block() -> None:
    report = build_report(
        trend_signal(team_key="sports_soccer", domain_key="sports"),
        trend_signal(
            team_key="crypto_policy",
            domain_key="crypto",
            observed_at=GENERATED_AT - timedelta(hours=1),
            resolved_outcome_count=d("18"),
            outcome_learning_score=d("0.720000"),
            prior_forecast_error_rate=d("0.100000"),
            current_forecast_error_rate=d("0.140000"),
            playbook_adoption_rate=d("0.800000"),
            stale_memory_correction_rate=d("0.800000"),
            review_capacity_pressure_score=d("0.800000"),
        ),
        trend_signal(
            team_key="macro_rates",
            domain_key="macro",
            observed_at=GENERATED_AT - timedelta(hours=2),
            resolved_outcome_count=d("12"),
            outcome_learning_score=d("0.300000"),
            prior_forecast_error_rate=d("0.100000"),
            current_forecast_error_rate=d("0.400000"),
            playbook_adoption_rate=d("0.500000"),
            stale_memory_correction_rate=d("0.500000"),
            review_capacity_pressure_score=d("1.000000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-team-domain-calibration-score-trend-report-v0"
    assert report.status == "block"
    assert report.domain_team_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.forecast_error_worsening_team_count == d("2")
    assert report.playbook_gap_team_count == d("2")
    assert report.stale_memory_gap_team_count == d("2")
    assert report.capacity_pressure_team_count == d("2")
    assert report.total_resolved_outcome_count == d("50")
    assert report.average_calibration_score_trend == d("0.663333")
    assert report.min_calibration_score_trend == d("0.400000")
    assert report.max_forecast_error_delta == d("0.300000")
    assert report.average_playbook_adoption_rate == d("0.740000")
    assert report.average_stale_memory_correction_rate == d("0.750000")
    assert report.max_review_capacity_pressure_score == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, watched, passed = report.rows
    assert tuple((row.status, row.domain_key) for row in report.rows) == (
        ("block", "macro"),
        ("watch", "crypto"),
        ("pass", "sports"),
    )
    assert blocked.observation_age_seconds == d("7200.000000")
    assert blocked.forecast_error_delta == d("0.300000")
    assert blocked.calibration_score_trend == d("0.400000")
    assert blocked.reason_codes == (
        "domain_calibration_score_block",
        "forecast_error_worsening_block",
        "playbook_adoption_block",
        "stale_memory_correction_block",
        "review_capacity_pressure_block",
    )
    assert watched.reason_codes == (
        "domain_calibration_score_watch",
        "forecast_error_worsening_watch",
        "playbook_adoption_watch",
        "stale_memory_correction_watch",
        "review_capacity_pressure_watch",
    )
    assert passed.reason_codes == ("domain_calibration_score_trend_clear",)
    assert report.reason_codes[:2] == (
        "domain_calibration_score_trend_report_block",
        "domain_calibration_score_block",
    )
    assert len(report.payload_digest) == 64


def test_empty_and_low_resolved_outcome_reports_block() -> None:
    module = api()
    empty = build_report()

    assert empty.status == "block"
    assert empty.domain_team_count == d("0")
    assert empty.rows == ()
    assert empty.reason_codes == ("domain_calibration_score_trend_no_domains",)
    assert empty.reason_code_counts == (
        module.ResearchTeamDomainCalibrationScoreTrendReasonCodeCount(
            reason_code="domain_calibration_score_trend_no_domains",
            count=d("1"),
            team_ratio=d("1.000000"),
        ),
    )

    thin = build_report(trend_signal(resolved_outcome_count=d("4")))
    assert thin.status == "block"
    assert thin.block_count == d("1")
    assert thin.rows[0].reason_codes == (
        "resolved_outcome_learning_below_minimum",
    )


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    module = api()
    left = trend_signal(team_key="sports_soccer", domain_key="sports")
    right = trend_signal(
        team_key="crypto_policy",
        domain_key="crypto",
        observed_at=datetime(2026, 7, 8, 4, 0, tzinfo=timezone(timedelta(hours=-7))),
        resolved_outcome_count=d("18"),
        outcome_learning_score=d("0.720000"),
        prior_forecast_error_rate=d("0.100000"),
        current_forecast_error_rate=d("0.140000"),
        playbook_adoption_rate=d("0.800000"),
        stale_memory_correction_rate=d("0.800000"),
        review_capacity_pressure_score=d("0.800000"),
    )

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload = module.research_team_domain_calibration_score_trend_report_payload(report_a)

    assert payload == module.research_team_domain_calibration_score_trend_report_payload(
        report_b,
    )
    assert report_a.payload_digest == report_b.payload_digest
    assert payload["domain_team_count"] == "2"
    assert payload["average_calibration_score_trend"] == "0.795000"
    assert payload["rows"][0]["observation_age_seconds"] == "3600.000000"
    assert payload["rows"][0]["team_digest"].startswith("sha256:")
    assert payload["rows"][0]["domain_digest"].startswith("sha256:")
    encoded = json.dumps(payload, sort_keys=True)
    assert "team_key" not in encoded
    assert "domain_key" not in encoded
    assert "sports_soccer" not in encoded
    assert "crypto_policy" not in encoded
    assert "sports" not in encoded
    assert "crypto" not in encoded
    assert payload["payload_digest"] == report_a.payload_digest
    assert_no_public_numeric_values(payload)
    assert_public_payload_has_no_forbidden_surface(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="payload_digest does not match"):
        module.research_team_domain_calibration_score_trend_report_payload(tampered)

    unsafe = dict(payload)
    unsafe["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_domain_calibration_score_trend_report_payload(unsafe)

    invalid_status = dict(payload)
    invalid_status["status"] = "review"
    invalid_status["payload_digest"] = payload_digest_for(invalid_status)
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        module.research_team_domain_calibration_score_trend_report_payload(
            invalid_status,
        )

    execution_surface = dict(payload)
    execution_surface["execution_route"] = "paper_queue"
    execution_surface["payload_digest"] = payload_digest_for(execution_surface)
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_domain_calibration_score_trend_report_payload(
            execution_surface,
        )


def test_validates_decimal_flags_statuses_and_frozen_dataclasses() -> None:
    module = api()
    cfg = config()
    item = trend_signal()
    report = build_report(item)

    for value in (cfg, item, report.rows[0], report.reason_code_counts[0], report):
        assert_decimal_public_fields(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="outcome_learning_score must be a Decimal"):
        trend_signal(outcome_learning_score=0.1)
    with pytest.raises(ValueError, match="review_capacity_pressure_score must be a Decimal"):
        trend_signal(review_capacity_pressure_score=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="resolved_outcome_count must be integral"):
        trend_signal(resolved_outcome_count=d("1.5"))
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        build_report(trend_signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        replace(report.rows[0], status="review")
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchTeamDomainCalibrationScoreTrendConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="unsafe public"):
        trend_signal(team_key="market_alpha")
    with pytest.raises(ValueError, match="unsafe public"):
        trend_signal(domain_key="question_ops")


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
        "size",
        "submit",
        "update",
        "route",
        "recommend",
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
