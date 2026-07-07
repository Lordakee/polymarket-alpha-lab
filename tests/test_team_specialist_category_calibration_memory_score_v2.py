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


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "team_specialist_category_calibration_memory_score_v2.py",
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_category_calibration_memory_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def memory(**overrides: object):
    module = api()
    values = {
        "team_id": "team_alpha",
        "specialist_id": "rates_specialist",
        "category_id": "macro_rates",
        "prior_forecast_count": d("20.000000"),
        "realized_brier_like_error": d("0.020000"),
        "stale_source_incident_count": d("0.000000"),
        "evidence_completeness_score": d("0.950000"),
        "postmortem_replay_age_days": d("2.000000"),
    }
    values.update(overrides)
    return module.TeamSpecialistCategoryCalibrationMemoryScoreV2Input(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    values = {
        "memories": items,
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.build_team_specialist_category_calibration_memory_score_v2_report(
        **values,
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


def test_builds_ranked_category_calibration_memory_report() -> None:
    report = build_report(
        memory(team_id="team_alpha", specialist_id="rates_specialist"),
        memory(
            team_id="team_beta",
            specialist_id="policy_specialist",
            category_id="policy",
            prior_forecast_count=d("10.000000"),
            realized_brier_like_error=d("0.090000"),
            stale_source_incident_count=d("1.000000"),
            evidence_completeness_score=d("0.700000"),
            postmortem_replay_age_days=d("12.000000"),
        ),
        memory(
            team_id="team_gamma",
            specialist_id="sports_specialist",
            category_id="sports",
            prior_forecast_count=d("3.000000"),
            realized_brier_like_error=d("0.200000"),
            stale_source_incident_count=d("5.000000"),
            evidence_completeness_score=d("0.350000"),
            postmortem_replay_age_days=d("60.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.memory_status == "blocked"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.average_memory_score == d("0.589778")
    assert report.reason_codes == (
        "category_calibration_memory_score_watch_rows",
        "category_calibration_memory_score_blocked_rows",
    )

    rows = report.rows
    assert tuple(row.team_id for row in rows) == ("team_alpha", "team_beta", "team_gamma")
    assert tuple(row.specialist_id for row in rows) == (
        "rates_specialist",
        "policy_specialist",
        "sports_specialist",
    )
    assert tuple(row.category_id for row in rows) == ("macro_rates", "policy", "sports")
    assert tuple(row.rank for row in rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.memory_score for row in rows) == (
        d("0.955333"),
        d("0.644000"),
        d("0.170000"),
    )
    assert tuple(row.memory_status for row in rows) == ("pass", "watch", "blocked")

    alpha = rows[0]
    assert alpha.prior_forecast_depth_score == d("1.000000")
    assert alpha.brier_quality_score == d("0.920000")
    assert alpha.stale_source_health_score == d("1.000000")
    assert alpha.postmortem_replay_recency_score == d("0.933333")
    assert alpha.reason_codes == (
        "category_calibration_memory_pass",
        "prior_forecast_depth_full",
        "brier_error_low",
        "stale_sources_clear",
        "evidence_complete",
        "postmortem_replay_fresh",
    )

    payload = report.payload
    assert payload["row_count"] == "3.000000"
    assert payload["average_memory_score"] == "0.589778"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["memory_score"] == "0.955333"
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_report_is_report_only_and_digest_backed() -> None:
    report = build_report()

    assert report.memory_status == "blocked"
    assert report.row_count == d("0.000000")
    assert report.rows == ()
    assert report.average_memory_score == d("0.000000")
    assert report.reason_codes == ("empty_category_calibration_memory_records",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_input_order_does_not_change_ranking_or_digest() -> None:
    first = memory(team_id="team_alpha", specialist_id="rates_specialist")
    second = memory(
        team_id="team_beta",
        specialist_id="policy_specialist",
        category_id="policy",
        prior_forecast_count=d("10.000000"),
        realized_brier_like_error=d("0.090000"),
        stale_source_incident_count=d("1.000000"),
        evidence_completeness_score=d("0.700000"),
        postmortem_replay_age_days=d("12.000000"),
    )

    left = build_report(first, second)
    right = build_report(second, first)

    assert tuple((row.team_id, row.rank) for row in left.rows) == (
        ("team_alpha", d("1.000000")),
        ("team_beta", d("2.000000")),
    )
    assert left.payload == right.payload
    assert left.derived_validation_digest == right.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistCategoryCalibrationMemoryScoreV2Config()
    sample = memory()
    report = build_report(sample)
    row = report.rows[0]

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name.endswith("_count") or field.name.endswith("_score"):
                assert type(value) is Decimal
            if field.name in {
                "prior_forecast_count",
                "realized_brier_like_error",
                "stale_source_incident_count",
                "postmortem_replay_age_days",
                "rank",
                "row_count",
            }:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "prior_forecast_count",
            _DecimalSubclass("1.000000"),
            "prior_forecast_count must be exactly Decimal",
        ),
        (
            "realized_brier_like_error",
            d("1.000001"),
            "realized_brier_like_error must be between zero and one",
        ),
        (
            "evidence_completeness_score",
            d("0.5000004"),
            "evidence_completeness_score must use six decimal places or fewer",
        ),
        (
            "stale_source_incident_count",
            d("-1.000000"),
            "stale_source_incident_count must be nonnegative",
        ),
        (
            "postmortem_replay_age_days",
            Decimal("NaN"),
            "postmortem_replay_age_days must be finite",
        ),
    ),
)
def test_input_validation_rejects_bad_decimal_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        memory(**{field_name: bad_value})


def test_build_validation_rejects_wrong_types_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="memories must be a sequence"):
        module.build_team_specialist_category_calibration_memory_score_v2_report(
            memories=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="memories must contain"):
        build_report(object())
    with pytest.raises(ValueError, match="duplicate team/specialist/category"):
        build_report(memory(), memory())
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_category_calibration_memory_score_v2_report(
            memories=(),
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        memory(readonly=False)
    with pytest.raises(ValueError, match="score weights must sum to 1.000000"):
        module.TeamSpecialistCategoryCalibrationMemoryScoreV2Config(
            evidence_completeness_weight=d("0.210000"),
        )
    with pytest.raises(ValueError, match="max_brier_like_error must be positive"):
        module.TeamSpecialistCategoryCalibrationMemoryScoreV2Config(
            max_brier_like_error=d("0.000000"),
        )


def test_digest_tampering_and_payload_type_downgrades_are_rejected() -> None:
    module = api()
    report = build_report(memory())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="float"):
        module.team_specialist_category_calibration_memory_score_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "score": 0.1,
            },
        )


def test_watch_rows_must_carry_watch_reason_code() -> None:
    watch_report = build_report(
        memory(
            team_id="team_beta",
            specialist_id="policy_specialist",
            category_id="policy",
            prior_forecast_count=d("10.000000"),
            realized_brier_like_error=d("0.090000"),
            stale_source_incident_count=d("1.000000"),
            evidence_completeness_score=d("0.700000"),
            postmortem_replay_age_days=d("12.000000"),
        ),
    )
    row = watch_report.rows[0]

    assert row.memory_status == "watch"
    with pytest.raises(ValueError, match="watch rows must include"):
        replace(
            row,
            reason_codes=tuple(
                reason
                for reason in row.reason_codes
                if reason != "category_calibration_memory_watch"
            ),
        )


def test_unsafe_public_identifiers_are_rejected() -> None:
    module = api()

    for unsafe_value in (
        "live_team",
        "auth_team",
        "wallet_team",
        "order_team",
        "network_team",
        "database_team",
        "persist_team",
        "signing_team",
        "mutation_team",
        "buy_team",
        "sell_team",
        "trade_team",
    ):
        with pytest.raises(ValueError, match="unsafe public value"):
            memory(team_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public field"):
        module.team_specialist_category_calibration_memory_score_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_field": "safe_value",
            },
        )


def test_static_module_surface_has_no_io_or_execution_entrypoints() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "aiohttp",
        "http",
        "httpx",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "urllib",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

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

    assert not float_constants
    assert not any(
        imported == forbidden or imported.startswith(f"{forbidden}.")
        for imported in imports
        for forbidden in forbidden_modules
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
    assert "replace(row, rank=_decimal_count(index))" in source
