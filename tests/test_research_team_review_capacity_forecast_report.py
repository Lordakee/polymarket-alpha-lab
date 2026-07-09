from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, get_type_hints

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_review_capacity_forecast_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_review_capacity_forecast_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def domain_input(**overrides: object):
    module = api()
    values = {
        "team_key": "macro_review",
        "domain": "politics",
        "current_queue_load": d("2.000000"),
        "stale_memory_count": d("0.000000"),
        "calibration_backlog_count": d("0.000000"),
        "correction_debt_count": d("0.000000"),
        "available_analyst_capacity": d("10.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamReviewCapacityForecastInput(**values)


def build_report(*rows: object, **overrides: object):
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    return module.build_research_team_review_capacity_forecast_report(
        rows,
        generated_at=generated_at,
        **overrides,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_values(item))
        return tuple(values)
    return (value,)


def assert_no_int_float_or_decimal_payload_values(value: Any) -> None:
    if type(value) in (int, float) or type(value) is Decimal:
        raise AssertionError(f"unexpected public payload numeric value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_float_or_decimal_payload_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_int_float_or_decimal_payload_values(item)


def signed_payload(payload: dict[str, Any]) -> dict[str, Any]:
    unsigned = dict(payload)
    unsigned.pop("payload_digest", None)
    digest = sha256(
        json.dumps(
            unsigned,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    return {**unsigned, "payload_digest": digest}


def test_capacity_forecast_reports_domain_pressure_from_queue_memory_calibration_and_debt() -> None:
    report = build_report(
        domain_input(
            team_key="politics_review",
            domain="politics",
            current_queue_load=d("9.000000"),
            stale_memory_count=d("10.000000"),
            calibration_backlog_count=d("8.000000"),
            correction_debt_count=d("5.000000"),
            available_analyst_capacity=d("8.000000"),
        ),
        domain_input(
            team_key="crypto_review",
            domain="crypto",
            current_queue_load=d("5.000000"),
            stale_memory_count=d("1.000000"),
            calibration_backlog_count=d("3.000000"),
            correction_debt_count=d("0.000000"),
            available_analyst_capacity=d("10.000000"),
        ),
        domain_input(team_key="sports_review", domain="football"),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.capacity_status == "block"
    assert report.report_status == "block"
    assert report.domain_count == d("3.000000")
    assert report.pass_domain_count == d("1.000000")
    assert report.watch_domain_count == d("1.000000")
    assert report.block_domain_count == d("1.000000")
    assert report.total_current_queue_load == d("16.000000")
    assert report.total_stale_memory_count == d("11.000000")
    assert report.total_calibration_backlog_count == d("11.000000")
    assert report.total_correction_debt_count == d("5.000000")
    assert report.total_available_analyst_capacity == d("28.000000")
    assert report.weighted_capacity_pressure_ratio == d("1.285714")
    assert report.max_capacity_pressure_ratio == d("3.281250")
    assert report.reason_codes == (
        "review_capacity_pressure_report_block",
        "weighted_capacity_pressure_block",
        "queue_load_block",
        "stale_memory_block",
        "calibration_backlog_block",
        "correction_debt_block",
        "weighted_capacity_pressure_watch",
        "calibration_backlog_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, watched, passed = report.rows
    assert tuple((row.team_key, row.domain, row.capacity_status) for row in report.rows) == (
        ("politics_review", "politics", "block"),
        ("crypto_review", "crypto", "watch"),
        ("sports_review", "football", "pass"),
    )
    assert blocked.queue_pressure_ratio == d("1.125000")
    assert blocked.stale_memory_pressure_ratio == d("1.250000")
    assert blocked.calibration_backlog_pressure_ratio == d("1.000000")
    assert blocked.correction_debt_pressure_ratio == d("0.625000")
    assert blocked.weighted_review_load == d("26.250000")
    assert blocked.capacity_pressure_ratio == d("3.281250")
    assert blocked.reason_codes == (
        "weighted_capacity_pressure_block",
        "queue_load_block",
        "stale_memory_block",
        "calibration_backlog_block",
        "correction_debt_block",
    )
    assert watched.capacity_pressure_ratio == d("0.775000")
    assert watched.reason_codes == (
        "weighted_capacity_pressure_watch",
        "calibration_backlog_watch",
    )
    assert passed.reason_codes == ("review_capacity_pressure_clear",)


def test_empty_report_is_pass_report_only_and_decimal_zeroed() -> None:
    report = build_report()

    assert report.capacity_status == "pass"
    assert report.report_status == "pass"
    assert report.domain_count == d("0.000000")
    assert report.pass_domain_count == d("0.000000")
    assert report.watch_domain_count == d("0.000000")
    assert report.block_domain_count == d("0.000000")
    assert report.total_current_queue_load == d("0.000000")
    assert report.total_stale_memory_count == d("0.000000")
    assert report.total_calibration_backlog_count == d("0.000000")
    assert report.total_correction_debt_count == d("0.000000")
    assert report.total_available_analyst_capacity == d("0.000000")
    assert report.weighted_capacity_pressure_ratio == d("0.000000")
    assert report.max_capacity_pressure_ratio == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == ()
    assert report.reason_codes == ("no_review_domains",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_deterministic_decimal_stringed_public_safe_and_digest_checked() -> None:
    module = api()
    first = build_report(
        domain_input(
            team_key="crypto_review",
            domain="crypto",
            current_queue_load=d("5.000000"),
            stale_memory_count=d("1.000000"),
            calibration_backlog_count=d("3.000000"),
            correction_debt_count=d("0.000000"),
            available_analyst_capacity=d("10.000000"),
        ),
        domain_input(
            team_key="politics_review",
            domain="politics",
            current_queue_load=d("9.000000"),
            stale_memory_count=d("10.000000"),
            calibration_backlog_count=d("8.000000"),
            correction_debt_count=d("5.000000"),
            available_analyst_capacity=d("8.000000"),
        ),
    )
    second = build_report(tuple(reversed(first.rows)))

    payload = module.research_team_review_capacity_forecast_report_payload(first)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == first.payload
    assert payload == module.research_team_review_capacity_forecast_report_payload(payload)
    assert first.payload_digest == second.payload_digest
    assert payload["payload_digest"] == first.payload_digest
    assert len(payload["payload_digest"]) == 64
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["weighted_capacity_pressure_ratio"] == "1.888889"
    assert payload["rows"][0]["weighted_review_load"] == "26.250000"
    assert payload["rows"][0]["reason_codes"] == [
        "weighted_capacity_pressure_block",
        "queue_load_block",
        "stale_memory_block",
        "calibration_backlog_block",
        "correction_debt_block",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"1.888889"' in encoded
    assert_no_int_float_or_decimal_payload_values(payload)

    tampered = dict(payload)
    tampered["total_current_queue_load"] = "999.000000"
    with pytest.raises(ValueError, match="payload_digest"):
        module.research_team_review_capacity_forecast_report_payload(tampered)


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    numeric_fields = {
        "watch_capacity_pressure_ratio",
        "block_capacity_pressure_ratio",
        "watch_queue_pressure_ratio",
        "block_queue_pressure_ratio",
        "watch_stale_memory_pressure_ratio",
        "block_stale_memory_pressure_ratio",
        "watch_calibration_backlog_pressure_ratio",
        "block_calibration_backlog_pressure_ratio",
        "watch_correction_debt_pressure_ratio",
        "block_correction_debt_pressure_ratio",
        "queue_load_weight",
        "stale_memory_weight",
        "calibration_backlog_weight",
        "correction_debt_weight",
        "current_queue_load",
        "stale_memory_count",
        "calibration_backlog_count",
        "correction_debt_count",
        "available_analyst_capacity",
        "queue_pressure_ratio",
        "stale_memory_pressure_ratio",
        "calibration_backlog_pressure_ratio",
        "correction_debt_pressure_ratio",
        "weighted_review_load",
        "capacity_pressure_ratio",
        "count",
        "domain_ratio",
        "domain_count",
        "pass_domain_count",
        "watch_domain_count",
        "block_domain_count",
        "total_current_queue_load",
        "total_stale_memory_count",
        "total_calibration_backlog_count",
        "total_correction_debt_count",
        "total_available_analyst_capacity",
        "weighted_capacity_pressure_ratio",
        "max_capacity_pressure_ratio",
    }

    for cls in (
        module.ResearchTeamReviewCapacityForecastConfig,
        module.ResearchTeamReviewCapacityForecastInput,
        module.ResearchTeamReviewCapacityForecastRow,
        module.ResearchTeamReviewCapacityForecastReasonCodeCount,
        module.ResearchTeamReviewCapacityForecastReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal


def test_validation_rejects_bad_numeric_types_ranges_precision_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="team_key"):
        domain_input(team_key=_StringSubclass("macro_review"))

    with pytest.raises(ValueError, match="current_queue_load must be a Decimal"):
        domain_input(current_queue_load=2)

    with pytest.raises(ValueError, match="stale_memory_count must be a Decimal"):
        domain_input(stale_memory_count=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="available_analyst_capacity must be positive"):
        domain_input(available_analyst_capacity=d("0.000000"))

    with pytest.raises(ValueError, match="correction_debt_count must be nonnegative"):
        domain_input(correction_debt_count=d("-0.000001"))

    with pytest.raises(ValueError, match="required decimal precision"):
        domain_input(current_queue_load=d("0.3333333"))

    with pytest.raises(ValueError, match="reason_codes must be unique"):
        module.ResearchTeamReviewCapacityForecastRow(
            team_key="macro_review",
            domain="politics",
            current_queue_load=d("5.000000"),
            stale_memory_count=d("1.000000"),
            calibration_backlog_count=d("3.000000"),
            correction_debt_count=d("0.000000"),
            available_analyst_capacity=d("10.000000"),
            queue_pressure_ratio=d("0.500000"),
            stale_memory_pressure_ratio=d("0.100000"),
            calibration_backlog_pressure_ratio=d("0.300000"),
            correction_debt_pressure_ratio=d("0.000000"),
            weighted_review_load=d("7.750000"),
            capacity_pressure_ratio=d("0.775000"),
            capacity_status="watch",
            reason_codes=(
                "weighted_capacity_pressure_watch",
                "weighted_capacity_pressure_watch",
            ),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(domain_input(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(build_report(domain_input()), readonly=False)

    with pytest.raises(FrozenInstanceError):
        report = build_report(domain_input())
        report.capacity_status = "watch"  # type: ignore[misc]


def test_public_payload_rejects_raw_identifiers_and_live_surface_fragments() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public"):
        domain_input(team_key=("candi" + "date") + "_123")

    with pytest.raises(ValueError, match="unsafe public"):
        domain_input(domain=("mar" + "ket") + "_slug")

    payload = build_report(domain_input()).payload
    payload[("wal" + "let") + "_field"] = "not_public"
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_review_capacity_forecast_report_payload(payload)


def test_public_status_values_are_exactly_pass_watch_block() -> None:
    module = api()

    assert module.PUBLIC_STATUSES == ("pass", "watch", "block")

    with pytest.raises(ValueError, match="capacity_status must be one of pass, watch, block"):
        module.ResearchTeamReviewCapacityForecastRow(
            team_key="macro_review",
            domain="politics",
            current_queue_load=d("5.000000"),
            stale_memory_count=d("1.000000"),
            calibration_backlog_count=d("3.000000"),
            correction_debt_count=d("0.000000"),
            available_analyst_capacity=d("10.000000"),
            queue_pressure_ratio=d("0.500000"),
            stale_memory_pressure_ratio=d("0.100000"),
            calibration_backlog_pressure_ratio=d("0.300000"),
            correction_debt_pressure_ratio=d("0.000000"),
            weighted_review_load=d("7.750000"),
            capacity_pressure_ratio=d("0.775000"),
            capacity_status="review",
            reason_codes=("weighted_capacity_pressure_watch",),
        )

    payload = build_report(domain_input()).payload
    invalid_report_status = signed_payload({**payload, "report_status": "review"})
    with pytest.raises(ValueError, match="report_status must be one of pass, watch, block"):
        module.research_team_review_capacity_forecast_report_payload(
            invalid_report_status,
        )

    invalid_row_payload = dict(payload)
    invalid_row_payload["rows"] = [dict(payload["rows"][0], capacity_status="review")]
    with pytest.raises(ValueError, match="capacity_status must be one of pass, watch, block"):
        module.research_team_review_capacity_forecast_report_payload(
            signed_payload(invalid_row_payload),
        )


def test_module_scope_is_report_only_without_io_or_execution_imports() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    forbidden_imports = {
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "urllib",
        "http",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "float", "exec", "eval"}

    assert imported_roots.isdisjoint(forbidden_imports)
