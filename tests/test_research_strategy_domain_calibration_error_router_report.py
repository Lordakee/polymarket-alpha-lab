from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal, ROUND_DOWN, getcontext, setcontext
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_domain_calibration_error_router_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_domain_calibration_error_router_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            "research-strategy-domain-calibration-error-router-report-test"
        ),
        "watch_expected_calibration_error": d("0.050000"),
        "block_expected_calibration_error": d("0.100000"),
        "watch_mean_brier_score": d("0.220000"),
        "block_mean_brier_score": d("0.300000"),
        "watch_error_trend_delta": d("0.020000"),
        "block_error_trend_delta": d("0.050000"),
        "watch_min_review_quality_score": d("0.750000"),
        "block_min_review_quality_score": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDomainCalibrationErrorRouterConfig(**values)


def domain(**overrides: object) -> Any:
    module = api()
    values = {
        "domain_label": "politics",
        "team_key": "research-team-alpha",
        "observation_count": d("40"),
        "expected_calibration_error": d("0.030000"),
        "mean_brier_score": d("0.180000"),
        "calibration_error_trend_delta": d("0.000000"),
        "review_quality_score": d("0.900000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDomainCalibrationErrorRouterDomainInput(**values)


def build_report(*items: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_strategy_domain_calibration_error_router_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = deepcopy(payload)
    unsigned = {
        key: value
        for key, value in resigned.items()
        if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        unsigned,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    resigned["derived_validation_digest"] = hashlib.sha256(encoded).hexdigest()
    return resigned


def assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
        return
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
        "candidate",
        "candidate_id",
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
        "sizing",
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


def test_public_api_declares_independent_readonly_report_contract() -> None:
    module = api()

    assert module.DEFAULT_RESEARCH_STRATEGY_DOMAIN_CALIBRATION_ERROR_ROUTER_REPORT_CONFIG_VERSION == (
        "research-strategy-domain-calibration-error-router-report-v0"
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_DOMAIN_CALIBRATION_ERROR_ROUTER_REPORT_CONFIG_VERSION",
        "ResearchStrategyDomainCalibrationErrorRouterConfig",
        "ResearchStrategyDomainCalibrationErrorRouterDomainInput",
        "ResearchStrategyDomainCalibrationErrorRouterDomainRow",
        "ResearchStrategyDomainCalibrationErrorRouterReasonCodeCount",
        "ResearchStrategyDomainCalibrationErrorRouterReport",
        "build_research_strategy_domain_calibration_error_router_report",
        "research_strategy_domain_calibration_error_router_report_payload",
    )

    public_types = {
        "ResearchStrategyDomainCalibrationErrorRouterConfig",
        "ResearchStrategyDomainCalibrationErrorRouterDomainInput",
        "ResearchStrategyDomainCalibrationErrorRouterDomainRow",
        "ResearchStrategyDomainCalibrationErrorRouterReasonCodeCount",
        "ResearchStrategyDomainCalibrationErrorRouterReport",
    }
    for name in public_types:
        cls = getattr(module, name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    field_defaults = {
        field.name: field.default
        for field in fields(module.ResearchStrategyDomainCalibrationErrorRouterConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True


def test_builds_pass_watch_and_block_domain_error_router_report() -> None:
    report = build_report(
        domain(domain_label="politics"),
        domain(
            domain_label="sports",
            expected_calibration_error=d("0.070000"),
            mean_brier_score=d("0.230000"),
            calibration_error_trend_delta=d("0.030000"),
            review_quality_score=d("0.700000"),
        ),
        domain(
            domain_label="macro",
            expected_calibration_error=d("0.120000"),
            mean_brier_score=d("0.320000"),
            calibration_error_trend_delta=d("0.060000"),
            review_quality_score=d("0.450000"),
        ),
    )

    assert type(report) is api().ResearchStrategyDomainCalibrationErrorRouterReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research-strategy-domain-calibration-error-router-report-test"
    )
    assert report.status == "block"
    assert report.domain_count == d("3.000000")
    assert report.pass_domain_count == d("1.000000")
    assert report.watch_domain_count == d("1.000000")
    assert report.block_domain_count == d("1.000000")
    assert report.average_expected_calibration_error == d("0.073333")
    assert report.max_expected_calibration_error == d("0.120000")
    assert report.average_error_pressure_score == d("0.250000")
    assert report.max_error_pressure_score == d("0.512500")
    assert report.reason_codes == (
        "research_strategy_domain_calibration_error_router_block_domains_present",
        "research_strategy_domain_calibration_error_router_watch_domains_present",
    )
    assert tuple(
        (row.domain_label, row.status, row.manual_review_priority_rank)
        for row in report.rows
    ) == (
        ("macro", "block", d("1.000000")),
        ("sports", "watch", d("2.000000")),
        ("politics", "pass", d("3.000000")),
    )
    assert tuple((row.domain_label, row.status) for row in report.rows) == (
        ("macro", "block"),
        ("sports", "watch"),
        ("politics", "pass"),
    )

    macro = report.rows[0]
    assert macro.positive_error_trend_delta == d("0.060000")
    assert macro.error_pressure_score == d("0.512500")
    assert macro.reason_codes == (
        "research_strategy_domain_calibration_error_router_expected_error_block",
        "research_strategy_domain_calibration_error_router_brier_score_block",
        "research_strategy_domain_calibration_error_router_error_trend_block",
        "research_strategy_domain_calibration_error_router_review_quality_block",
    )
    assert report.reason_code_counts[0].reason_code == (
        "research_strategy_domain_calibration_error_router_expected_error_block"
    )
    assert report.reason_code_counts[0].count == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_report_blocks_without_rows() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.domain_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "research_strategy_domain_calibration_error_router_empty",
    )
    assert report.average_expected_calibration_error == d("0.000000")
    assert report.max_error_pressure_score == d("0.000000")


def test_payload_digest_is_deterministic_decimal_stringed_and_public_safe() -> None:
    module = api()
    left = domain(domain_label="politics")
    right = domain(
        domain_label="sports",
        expected_calibration_error=d("0.070000"),
        mean_brier_score=d("0.230000"),
        calibration_error_trend_delta=d("0.030000"),
        review_quality_score=d("0.700000"),
    )

    report_a = build_report(right, left)
    report_b = build_report(left, right)
    payload = module.research_strategy_domain_calibration_error_router_report_payload(
        report_a,
    )

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert len(report_a.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report_a.derived_validation_digest)
    assert payload == report_a.payload
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["domain_count"] == "2.000000"
    assert payload["average_error_pressure_score"] == "0.118750"
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert payload["rows"][0]["domain_label"] == "sports"
    assert payload["rows"][0]["observation_count"] == "40.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert module.research_strategy_domain_calibration_error_router_report_payload(
        payload,
    ) == payload
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert_no_float_values(payload)
    assert_public_payload_has_no_forbidden_surface(payload)
    assert "candidate" not in json.dumps(payload, sort_keys=True).lower()
    assert "market" not in json.dumps(payload, sort_keys=True).lower()


def test_routes_manual_review_priority_and_redacts_private_team_keys() -> None:
    module = api()
    report = build_report(
        domain(
            domain_label="routine",
            team_key="private-team-routine",
        ),
        domain(
            domain_label="urgent-b",
            team_key="private-team-urgent-b",
            expected_calibration_error=d("0.150000"),
            mean_brier_score=d("0.350000"),
            calibration_error_trend_delta=d("0.080000"),
            review_quality_score=d("0.400000"),
        ),
        domain(
            domain_label="urgent-a",
            team_key="private-team-urgent-a",
            expected_calibration_error=d("0.150000"),
            mean_brier_score=d("0.350000"),
            calibration_error_trend_delta=d("0.080000"),
            review_quality_score=d("0.400000"),
        ),
        domain(
            domain_label="watch",
            team_key="private-team-watch",
            expected_calibration_error=d("0.070000"),
            mean_brier_score=d("0.230000"),
            calibration_error_trend_delta=d("0.030000"),
            review_quality_score=d("0.700000"),
        ),
    )

    assert tuple(row.domain_label for row in report.rows) == (
        "urgent-a",
        "urgent-b",
        "watch",
        "routine",
    )
    assert tuple(row.manual_review_priority_rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
        d("4.000000"),
    )
    expected_team_digest = (
        "sha256:"
        + hashlib.sha256(b"team:private-team-urgent-a").hexdigest()
    )
    assert report.rows[0].team_digest == expected_team_digest

    payload = module.research_strategy_domain_calibration_error_router_report_payload(
        report,
    )
    serialized = json.dumps(payload, sort_keys=True)
    assert "private-team-" not in serialized
    assert "team_key" not in serialized
    assert payload["rows"][0]["team_digest"] == expected_team_digest


def test_uses_exact_canonical_payload_schema_and_sha256() -> None:
    module = api()
    payload = module.research_strategy_domain_calibration_error_router_report_payload(
        build_report(domain()),
    )

    assert frozenset(payload) == frozenset(
        {
            "generated_at",
            "config_version",
            "watch_expected_calibration_error",
            "block_expected_calibration_error",
            "watch_mean_brier_score",
            "block_mean_brier_score",
            "watch_error_trend_delta",
            "block_error_trend_delta",
            "watch_min_review_quality_score",
            "block_min_review_quality_score",
            "status",
            "domain_count",
            "pass_domain_count",
            "watch_domain_count",
            "block_domain_count",
            "average_expected_calibration_error",
            "max_expected_calibration_error",
            "average_error_pressure_score",
            "max_error_pressure_score",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        },
    )
    assert frozenset(payload["rows"][0]) == frozenset(
        {
            "domain_label",
            "team_digest",
            "manual_review_priority_rank",
            "observation_count",
            "expected_calibration_error",
            "mean_brier_score",
            "calibration_error_trend_delta",
            "positive_error_trend_delta",
            "review_quality_score",
            "error_pressure_score",
            "status",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        },
    )
    assert frozenset(payload["reason_code_counts"][0]) == frozenset(
        {
            "reason_code",
            "count",
            "paper_only",
            "report_only",
            "readonly",
        },
    )

    unsigned = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    expected_digest = hashlib.sha256(
        json.dumps(
            unsigned,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert payload["derived_validation_digest"] == expected_digest

    with pytest.raises(ValueError, match="schema"):
        module.research_strategy_domain_calibration_error_router_report_payload(
            resign_payload({**payload, "unexpected": "value"}),
        )
    payload_with_extra_row_key = deepcopy(payload)
    payload_with_extra_row_key["rows"][0]["unexpected"] = "value"
    with pytest.raises(ValueError, match="schema"):
        module.research_strategy_domain_calibration_error_router_report_payload(
            resign_payload(payload_with_extra_row_key),
        )
    payload_with_noncanonical_decimal = deepcopy(payload)
    payload_with_noncanonical_decimal["domain_count"] = "1"
    with pytest.raises(ValueError, match="canonical Decimal"):
        module.research_strategy_domain_calibration_error_router_report_payload(
            resign_payload(payload_with_noncanonical_decimal),
        )


def test_rejects_resigned_payload_when_derived_values_or_order_are_tampered() -> None:
    module = api()
    payload = module.research_strategy_domain_calibration_error_router_report_payload(
        build_report(
            domain(domain_label="routine"),
            domain(
                domain_label="urgent",
                team_key="private-team-urgent",
                expected_calibration_error=d("0.120000"),
                mean_brier_score=d("0.320000"),
                calibration_error_trend_delta=d("0.060000"),
                review_quality_score=d("0.450000"),
            ),
        ),
    )

    mutations: list[tuple[str, Any]] = []

    wrong_count = deepcopy(payload)
    wrong_count["domain_count"] = "9.000000"
    mutations.append(("domain_count", wrong_count))

    wrong_average = deepcopy(payload)
    wrong_average["average_error_pressure_score"] = "0.999999"
    mutations.append(("average_error_pressure_score", wrong_average))

    wrong_positive_trend = deepcopy(payload)
    wrong_positive_trend["rows"][0]["positive_error_trend_delta"] = "0.010000"
    mutations.append(("positive_error_trend_delta", wrong_positive_trend))

    wrong_score = deepcopy(payload)
    wrong_score["rows"][0]["error_pressure_score"] = "0.100000"
    mutations.append(("error_pressure_score", wrong_score))

    wrong_rank = deepcopy(payload)
    wrong_rank["rows"][0]["manual_review_priority_rank"] = "2.000000"
    mutations.append(("manual_review_priority_rank", wrong_rank))

    wrong_order = deepcopy(payload)
    wrong_order["rows"] = list(reversed(wrong_order["rows"]))
    mutations.append(("deterministic", wrong_order))

    wrong_route = deepcopy(payload)
    removed_reason = (
        "research_strategy_domain_calibration_error_router_expected_error_block"
    )
    wrong_route["rows"][0]["reason_codes"].remove(removed_reason)
    wrong_route["reason_code_counts"] = [
        item
        for item in wrong_route["reason_code_counts"]
        if item["reason_code"] != removed_reason
    ]
    mutations.append(("reason_codes must match calibration thresholds", wrong_route))

    for expected_message, mutated in mutations:
        with pytest.raises(ValueError, match=expected_message):
            module.research_strategy_domain_calibration_error_router_report_payload(
                resign_payload(mutated),
            )


def test_decimal_context_raw_bounds_signed_zero_and_non_finite_are_hardened() -> None:
    api()
    original_context = getcontext().copy()
    try:
        getcontext().prec = 4
        getcontext().rounding = ROUND_DOWN
        report = build_report(
            domain(
                observation_count=d("-0.000000"),
                expected_calibration_error=d("-0.000000"),
                calibration_error_trend_delta=d("-0.000000"),
            ),
        )
        assert report.rows[0].observation_count == d("0.000000")
        assert report.rows[0].observation_count.is_signed() is False
        assert report.rows[0].expected_calibration_error == d("0.000000")
        assert report.rows[0].expected_calibration_error.is_signed() is False
        assert report.rows[0].calibration_error_trend_delta == d("0.000000")
        assert report.rows[0].calibration_error_trend_delta.is_signed() is False
        assert getcontext().prec == 4
        assert getcontext().rounding == ROUND_DOWN
    finally:
        setcontext(original_context)

    for invalid in (d("NaN"), d("Infinity"), d("-Infinity")):
        with pytest.raises(ValueError, match="finite"):
            domain(expected_calibration_error=invalid)
    with pytest.raises(ValueError, match="must be >= 0.000000"):
        domain(expected_calibration_error=d("-0.000001"))
    with pytest.raises(ValueError, match="must be <= 1.000000"):
        domain(expected_calibration_error=d("1.000001"))
    with pytest.raises(ValueError, match="must be >= -1.000000"):
        domain(calibration_error_trend_delta=d("-1.000001"))
    with pytest.raises(ValueError, match="must be <= 1.000000"):
        domain(calibration_error_trend_delta=d("1.000001"))


def test_public_dataclasses_are_frozen_exact_and_non_subclassable() -> None:
    module = api()
    instances = (
        config(),
        domain(),
        build_report(domain()).rows[0],
        build_report(domain()).reason_code_counts[0],
        build_report(domain()),
    )
    for name, instance in zip(
        (
            "ResearchStrategyDomainCalibrationErrorRouterConfig",
            "ResearchStrategyDomainCalibrationErrorRouterDomainInput",
            "ResearchStrategyDomainCalibrationErrorRouterDomainRow",
            "ResearchStrategyDomainCalibrationErrorRouterReasonCodeCount",
            "ResearchStrategyDomainCalibrationErrorRouterReport",
        ),
        instances,
    ):
        cls = getattr(module, name)
        with pytest.raises(TypeError, match="subclass"):
            type(f"Invalid{name}Subclass", (cls,), {})
        assert cls.__slots__ == tuple(field.name for field in fields(cls))
        assert not hasattr(instance, "__dict__")


def test_rejects_resigned_payload_with_noncanonical_reason_code_sequences() -> None:
    module = api()
    payload = module.research_strategy_domain_calibration_error_router_report_payload(
        build_report(
            domain(domain_label="routine"),
            domain(
                domain_label="urgent",
                expected_calibration_error=d("0.120000"),
                mean_brier_score=d("0.320000"),
                calibration_error_trend_delta=d("0.060000"),
                review_quality_score=d("0.450000"),
            ),
        ),
    )

    reversed_row_reasons = deepcopy(payload)
    reversed_row_reasons["rows"][0]["reason_codes"].reverse()
    with pytest.raises(ValueError, match="canonical reason_codes"):
        module.research_strategy_domain_calibration_error_router_report_payload(
            resign_payload(reversed_row_reasons),
        )

    duplicate_report_reason = deepcopy(payload)
    duplicate_report_reason["reason_codes"] = [
        duplicate_report_reason["reason_codes"][0],
        duplicate_report_reason["reason_codes"][0],
    ]
    with pytest.raises(ValueError, match="canonical reason_codes"):
        module.research_strategy_domain_calibration_error_router_report_payload(
            resign_payload(duplicate_report_reason),
        )


def test_rejects_decimal_values_that_exceed_fixed_context_precision() -> None:
    with pytest.raises(ValueError, match="fit configured precision"):
        domain(observation_count=d("1" * 65))


def test_validates_decimal_inputs_status_consistency_flags_and_safe_labels() -> None:
    module = api()
    report = build_report(
        domain(),
        generated_at=datetime(2026, 7, 9, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert {report.status, *(row.status for row in report.rows)} <= {
        "pass",
        "watch",
        "block",
    }
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="expected_calibration_error must be exactly Decimal"):
        domain(expected_calibration_error=0.03)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="mean_brier_score must be exactly Decimal"):
        domain(mean_brier_score=_DecimalSubclass("0.180000"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_research_strategy_domain_calibration_error_router_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="watch_expected_calibration_error"):
        config(watch_expected_calibration_error=d("0.100001"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(domain(), report_only=False)
    with pytest.raises(ValueError, match="domain_label must be public"):
        domain(domain_label="market_slug_value")
    with pytest.raises(ValueError, match="domain_label values must be unique"):
        build_report(domain(domain_label="politics"), domain(domain_label="politics"))
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report.rows[0], status="ready")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, average_error_pressure_score=d("0.500000"))
    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_domain_calibration_error_router_report_payload(
            {**report.payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_strategy_domain_calibration_error_router_report_payload(
            {**report.payload, "source_url": "https://example.invalid/item"},
        )


def test_module_stays_readonly_without_storage_network_or_execution_surface() -> None:
    module = api()
    report = build_report(domain())

    for value in (config(), domain(), report.rows[0], report.reason_code_counts[0], report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        assert_public_numeric_values_are_decimal(value)

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
        "os",
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

    module_text = MODULE_PATH.read_text(encoding="utf-8").lower()
    for forbidden in (
        "database",
        "network",
        "wallet",
        "credential",
        "private_key",
        "secret",
        "order",
        "live",
        "trade",
        "broker",
        "buy",
        "sell",
        "request",
        "submit",
        "supabase",
        "sqlite",
        "postgres",
        "insert",
        "update",
        "delete",
        "commit",
        "cursor",
    ):
        assert forbidden not in module_text
