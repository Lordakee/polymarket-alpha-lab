from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_calibration_drift_watch_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_calibration_drift_watch_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-strategy-calibration-drift-watch-report-test",
        "min_resolved_sample_count": d("30"),
        "watch_brier_score_delta": d("0.030000"),
        "block_brier_score_delta": d("0.070000"),
        "watch_expected_calibration_error_delta": d("0.025000"),
        "block_expected_calibration_error_delta": d("0.060000"),
        "watch_pending_sample_share": d("0.600000"),
        "block_pending_sample_share": d("0.800000"),
        "watch_resolved_age_seconds": d("604800"),
        "block_resolved_age_seconds": d("1209600"),
    }
    values.update(overrides)
    return module.ResearchStrategyCalibrationDriftWatchConfig(**values)


def aggregate(**overrides: object):
    module = api()
    values = {
        "research_team": "team_alpha",
        "domain": "politics",
        "measured_at": GENERATED_AT - timedelta(hours=1),
        "latest_resolved_at": GENERATED_AT - timedelta(days=2),
        "pending_sample_count": d("10"),
        "resolved_sample_count": d("60"),
        "low_confidence_count": d("20"),
        "medium_confidence_count": d("25"),
        "high_confidence_count": d("25"),
        "baseline_brier_score": d("0.180000"),
        "current_brier_score": d("0.200000"),
        "baseline_expected_calibration_error": d("0.050000"),
        "current_expected_calibration_error": d("0.060000"),
        "reason_codes": (),
    }
    values.update(overrides)
    return module.ResearchStrategyCalibrationAggregate(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_calibration_drift_watch_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        return
    if isinstance(value, datetime):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_public_payload_has_no_forbidden_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate_id",
        "candidate",
        "market_id",
        "market_slug",
        "market",
        "slug",
        "question",
        "http://",
        "https://",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "private_key",
        "private key",
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
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_payload_has_no_forbidden_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def test_public_api_declares_readonly_report_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_STRATEGY_CALIBRATION_DRIFT_WATCH_CONFIG_VERSION == (
        "research-strategy-calibration-drift-watch-report-v0"
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CALIBRATION_DRIFT_WATCH_CONFIG_VERSION",
        "ResearchStrategyCalibrationDriftWatchConfig",
        "ResearchStrategyCalibrationAggregate",
        "ResearchStrategyCalibrationDriftWatchRow",
        "ResearchStrategyCalibrationDriftWatchDigest",
        "ResearchStrategyCalibrationDriftWatchReport",
        "build_research_strategy_calibration_drift_watch_report",
        "research_strategy_calibration_drift_watch_report_payload",
        "research_strategy_calibration_drift_watch_digest_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(module.ResearchStrategyCalibrationDriftWatchConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True


def test_builds_pass_watch_and_block_by_team_domain_with_aggregate_metrics() -> None:
    report = build_report(
        aggregate(research_team="team_alpha", domain="politics"),
        aggregate(
            research_team="team_beta",
            domain="sports",
            latest_resolved_at=GENERATED_AT - timedelta(days=3),
            pending_sample_count=d("15"),
            resolved_sample_count=d("50"),
            low_confidence_count=d("20"),
            medium_confidence_count=d("20"),
            high_confidence_count=d("25"),
            current_brier_score=d("0.225000"),
            current_expected_calibration_error=d("0.082000"),
        ),
        aggregate(
            research_team="team_gamma",
            domain="economics",
            latest_resolved_at=GENERATED_AT - timedelta(days=1),
            pending_sample_count=d("8"),
            resolved_sample_count=d("40"),
            low_confidence_count=d("10"),
            medium_confidence_count=d("18"),
            high_confidence_count=d("20"),
            current_brier_score=d("0.270000"),
            current_expected_calibration_error=d("0.120000"),
        ),
    )

    assert is_dataclass(report)
    assert report.status == "block"
    assert report.aggregate_count == d("3.000000")
    assert report.pending_sample_count == d("33.000000")
    assert report.resolved_sample_count == d("150.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_absolute_brier_score_delta == d("0.051667")
    assert report.max_absolute_brier_score_delta == d("0.090000")
    assert report.average_absolute_expected_calibration_error_delta == d("0.037333")
    assert report.max_absolute_expected_calibration_error_delta == d("0.070000")
    assert report.max_latest_resolved_age_seconds == d("259200.000000")
    assert report.reason_codes == (
        "calibration_drift_watch_report_block_rows",
        "calibration_drift_watch_report_watch_rows",
    )

    assert tuple((row.research_team, row.domain) for row in report.rows) == (
        ("team_alpha", "politics"),
        ("team_beta", "sports"),
        ("team_gamma", "economics"),
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert report.rows[0].reason_codes == ("calibration_drift_watch_pass",)
    assert report.rows[0].total_sample_count == d("70.000000")
    assert report.rows[0].pending_sample_share == d("0.142857")
    assert report.rows[1].reason_codes == (
        "brier_score_drift_watch",
        "calibration_error_drift_watch",
        "calibration_drift_watch",
    )
    assert report.rows[2].reason_codes == (
        "brier_score_drift_block",
        "calibration_error_drift_block",
        "calibration_drift_block",
    )


def test_empty_stale_pending_and_low_sample_reports_are_report_only_blocks() -> None:
    module = api()
    empty = build_report()

    assert empty.status == "block"
    assert empty.aggregate_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("no_calibration_drift_watch_aggregates",)

    low_sample = build_report(aggregate(resolved_sample_count=d("10")))
    assert low_sample.status == "block"
    assert low_sample.rows[0].reason_codes == (
        "calibration_drift_block",
        "insufficient_resolved_samples",
    )

    stale = build_report(
        aggregate(
            latest_resolved_at=GENERATED_AT - timedelta(days=8),
            research_team="team_stale",
        ),
    )
    assert stale.status == "watch"
    assert stale.rows[0].reason_codes == (
        "calibration_drift_watch",
        "stale_resolved_samples_watch",
    )

    pending = build_report(
        aggregate(
            pending_sample_count=d("80"),
            resolved_sample_count=d("20"),
            low_confidence_count=d("30"),
            medium_confidence_count=d("30"),
            high_confidence_count=d("40"),
            research_team="team_pending",
        ),
    )
    assert pending.status == "block"
    assert pending.rows[0].reason_codes == (
        "calibration_drift_block",
        "insufficient_resolved_samples",
        "pending_sample_share_block",
    )

    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(stale.rows[0], status="blocked")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(stale.digest, status="ready")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        module.ResearchStrategyCalibrationDriftWatchReport(
            **{**stale.__dict__, "status": "review"},
        )


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: aggregate(pending_sample_count=10),
            "pending_sample_count must be exactly Decimal",
        ),
        (
            lambda: aggregate(current_brier_score=0.20),
            "current_brier_score must be exactly Decimal",
        ),
        (
            lambda: aggregate(current_expected_calibration_error=_DecimalSubclass("0.060000")),
            "current_expected_calibration_error must be exactly Decimal",
        ),
        (
            lambda: aggregate(current_expected_calibration_error=d("0.6000001")),
            "current_expected_calibration_error must use six decimal places or fewer",
        ),
        (
            lambda: aggregate(resolved_sample_count=d("59.5")),
            "resolved_sample_count must be an integral Decimal",
        ),
        (
            lambda: config(min_resolved_sample_count=d("30.5")),
            "min_resolved_sample_count must be an integral Decimal",
        ),
        (
            lambda: build_report(
                aggregate(),
                generated_at=datetime(2026, 7, 8, 12, 0),
            ),
            "generated_at must be timezone-aware",
        ),
    ),
)
def test_decimal_and_type_validation_rejects_public_numeric_shortcuts(
    factory: Any,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()


def test_rejects_unsafe_identifiers_values_and_payload_tampering() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public payload"):
        aggregate(research_team="candidate-alpha")
    with pytest.raises(ValueError, match="unsafe public payload"):
        aggregate(domain="market-politics")
    with pytest.raises(ValueError, match="unsafe public payload"):
        config(config_version="dsn-prod")
    with pytest.raises(ValueError, match="unsafe public payload"):
        aggregate(reason_codes=("source_url",))

    report = build_report(aggregate())
    payload = dict(report.payload)
    payload["market_id"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_strategy_calibration_drift_watch_report_payload(payload)

    row_payload = dict(report.payload)
    row_payload["rows"] = [dict(row_payload["rows"][0])]
    row_payload["rows"][0]["source_text"] = "hidden note"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_strategy_calibration_drift_watch_report_payload(row_payload)

    assert_public_payload_has_no_forbidden_surface(report.payload)
    encoded = json.dumps(report.payload, sort_keys=True).lower()
    assert "team_alpha" not in encoded
    assert "politics" not in encoded


def test_hard_flags_are_enforced_and_public_dataclasses_are_frozen() -> None:
    module = api()
    cfg = config()
    item = aggregate()
    report = build_report(item)
    row = report.rows[0]
    digest = report.digest

    for value in (cfg, item, row, digest, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(value)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.ResearchStrategyCalibrationDriftWatchConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_payload_and_digest_are_deterministic_decimal_stringed_and_consistent() -> None:
    module = api()
    left = aggregate(research_team="team_left", domain="politics")
    right = aggregate(
        research_team="team_right",
        domain="sports",
        current_brier_score=d("0.225000"),
        current_expected_calibration_error=d("0.082000"),
    )

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload = module.research_strategy_calibration_drift_watch_report_payload(report_a)
    digest_payload = module.research_strategy_calibration_drift_watch_digest_payload(
        report_a.digest,
    )

    assert report_a.payload == report_b.payload
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert report_a.digest == report_b.digest
    assert payload["aggregate_count"] == "2.000000"
    assert payload["rows"][0]["absolute_brier_score_delta"] == "0.020000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert payload["digest"] == digest_payload
    assert digest_payload["derived_validation_digest"] == report_a.digest.derived_validation_digest
    assert digest_payload["status"] == report_a.status
    assert digest_payload["aggregate_count"] == payload["aggregate_count"]
    assert set(payload["rows"][0]) >= {"team_digest", "domain_digest"}
    assert_no_float_values(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    statuses = {report_a.status, report_a.digest.status}
    statuses.update(row.status for row in report_a.rows)
    assert statuses <= {"pass", "watch", "block"}


def test_report_and_digest_validation_rejects_tampering() -> None:
    module = api()
    report = build_report(
        aggregate(),
        aggregate(
            research_team="team_watch",
            domain="sports",
            current_brier_score=d("0.225000"),
            current_expected_calibration_error=d("0.082000"),
        ),
    )

    with pytest.raises(ValueError, match="pass_count must match rows"):
        replace(report, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="average_absolute_brier_score_delta must match rows"):
        replace(report, average_absolute_brier_score_delta=d("0.500000"))
    with pytest.raises(ValueError, match="digest must match report summary"):
        replace(report, digest=build_report().digest)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)

    payload = dict(report.payload)
    payload["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest must match payload fields"):
        module.research_strategy_calibration_drift_watch_report_payload(payload)

    digest_payload = dict(report.digest.payload)
    digest_payload["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest must match payload fields"):
        module.research_strategy_calibration_drift_watch_digest_payload(digest_payload)


def test_module_stays_report_only_without_network_storage_or_trading_surface() -> None:
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

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_source_fragments = (
        "buy",
        "sell",
        "recommend",
        "position sizing",
    )
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
    assert not any(fragment in source for fragment in forbidden_source_fragments)
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
