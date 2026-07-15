from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_DOWN, localcontext
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_probability_resolution_source_triage_report"
)
GENERATED_AT = datetime(2026, 7, 9, 18, 0, tzinfo=UTC)
SOURCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_probability_resolution_source_triage_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def forecast(
    seed: str,
    *,
    forecast_confidence: Decimal = d("0.950000"),
    source_age_seconds: Decimal = d("600.000000"),
    authority_coverage: Decimal = d("0.950000"),
    contradiction_pressure: Decimal = d("0.050000"),
    seconds_until_resolution: Decimal = d("86400.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchStrategyProbabilityResolutionSourceTriageInput(
        forecast_digest=digest(seed),
        forecast_confidence=forecast_confidence,
        source_age_seconds=source_age_seconds,
        authority_coverage=authority_coverage,
        contradiction_pressure=contradiction_pressure,
        seconds_until_resolution=seconds_until_resolution,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, config: Any | None = None) -> Any:
    module = api()
    return module.build_research_strategy_probability_resolution_source_triage_report(
        rows,
        generated_at=GENERATED_AT,
        config=config,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = deepcopy(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resign(payload: dict[str, Any]) -> dict[str, Any]:
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def replace_path(value: Any, path: tuple[Any, ...], replacement: Any) -> None:
    target = value
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = replacement


def move_first_key_to_end(value: dict[str, Any]) -> None:
    first_key = next(iter(value))
    value[first_key] = value.pop(first_key)


def test_reducer_ranks_five_factor_triage_risk_deterministically() -> None:
    module = api()
    passed = forecast("pass")
    watched = forecast(
        "watch",
        forecast_confidence=d("0.650000"),
        source_age_seconds=d("7200.000000"),
        authority_coverage=d("0.700000"),
        contradiction_pressure=d("0.300000"),
        seconds_until_resolution=d("10800.000000"),
    )
    blocked = forecast(
        "block",
        forecast_confidence=d("0.300000"),
        source_age_seconds=d("90000.000000"),
        authority_coverage=d("0.300000"),
        contradiction_pressure=d("0.700000"),
        seconds_until_resolution=d("900.000000"),
    )

    report = build_report(passed, watched, blocked)
    reversed_report = build_report(blocked, watched, passed)

    assert type(report) is module.ResearchStrategyProbabilityResolutionSourceTriageReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.forecast_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_triage_risk_score == d("0.377671")
    assert report.highest_triage_risk_score == d("0.805000")
    assert tuple(row.rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.forecast_digest for row in report.rows) == (
        blocked.forecast_digest,
        watched.forecast_digest,
        passed.forecast_digest,
    )
    assert tuple(row.triage_risk_score for row in report.rows) == (
        d("0.805000"),
        d("0.295514"),
        d("0.032500"),
    )
    assert report.payload == reversed_report.payload
    assert report.derived_validation_digest == reversed_report.derived_validation_digest

    blocked_row, watched_row, passed_row = report.rows
    assert blocked_row.status == "block"
    assert blocked_row.reason_codes == (
        "forecast_confidence_block",
        "source_freshness_block",
        "authority_coverage_block",
        "contradiction_pressure_block",
        "resolution_clock_proximity_block",
        "triage_risk_score_block",
    )
    assert watched_row.status == "watch"
    assert watched_row.reason_codes == (
        "forecast_confidence_watch",
        "source_freshness_watch",
        "authority_coverage_watch",
        "contradiction_pressure_watch",
        "resolution_clock_proximity_watch",
        "triage_risk_score_watch",
    )
    assert passed_row.status == "pass"
    assert passed_row.reason_codes == (
        "probability_resolution_source_triage_pass",
    )
    assert report.reason_codes == (
        "forecast_confidence_block",
        "source_freshness_block",
        "authority_coverage_block",
        "contradiction_pressure_block",
        "resolution_clock_proximity_block",
        "triage_risk_score_block",
        "forecast_confidence_watch",
        "source_freshness_watch",
        "authority_coverage_watch",
        "contradiction_pressure_watch",
        "resolution_clock_proximity_watch",
        "triage_risk_score_watch",
        "probability_resolution_source_triage_pass",
    )


def test_empty_report_is_blocked_frozen_decimal_only_and_reason_only() -> None:
    module = api()
    report = build_report()

    assert report.status == "block"
    assert report.forecast_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_triage_risk_score == d("0.000000")
    assert report.highest_triage_risk_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "probability_resolution_source_triage_no_inputs",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_decimal_public_numbers(report)

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadReport(
            module.ResearchStrategyProbabilityResolutionSourceTriageReport,
        ):
            pass


def test_payload_is_canonical_and_rejects_forged_resigned_derived_logic() -> None:
    module = api()
    report = build_report(
        forecast(
            "forgery-target",
            forecast_confidence=d("0.300000"),
            source_age_seconds=d("90000.000000"),
            authority_coverage=d("0.300000"),
            contradiction_pressure=d("0.700000"),
            seconds_until_resolution=d("900.000000"),
        ),
    )
    payload = report.payload

    assert payload == (
        module.research_strategy_probability_resolution_source_triage_report_payload(
            report,
        )
    )
    assert payload["generated_at"] == "2026-07-09T18:00:00+00:00"
    assert payload["forecast_count"] == "1.000000"
    assert payload["rows"][0]["triage_risk_score"] == "0.805000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["derived_validation_digest"] == (
        module.research_strategy_probability_resolution_source_triage_report_digest(
            report,
        )
    )
    assert module.validate_research_strategy_probability_resolution_source_triage_report_payload(
        payload,
    )
    assert module.validate_research_strategy_probability_resolution_source_triage_public_payload(
        payload,
    )
    assert_no_public_numeric_scalars(payload)
    json.dumps(payload, sort_keys=True, allow_nan=False)

    forged_status = deepcopy(payload)
    forged_status["rows"][0]["status"] = "pass"
    forged_status["rows"][0]["reason_codes"] = [
        "probability_resolution_source_triage_pass",
    ]
    forged_status["status"] = "pass"
    forged_status["pass_count"] = "1.000000"
    forged_status["block_count"] = "0.000000"
    forged_status["reason_codes"] = [
        "probability_resolution_source_triage_pass",
    ]
    forged_status["reason_code_counts"] = [
        {
            "reason_code": "probability_resolution_source_triage_pass",
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    resign(forged_status)
    assert not module.validate_research_strategy_probability_resolution_source_triage_report_payload(
        forged_status,
    )
    assert not module.validate_research_strategy_probability_resolution_source_triage_public_payload(
        forged_status,
    )

    forged_reasons = deepcopy(payload)
    forged_reasons["rows"][0]["reason_codes"] = [
        "probability_resolution_source_triage_pass",
    ]
    forged_reasons["reason_codes"] = [
        "probability_resolution_source_triage_pass",
    ]
    forged_reasons["reason_code_counts"] = [
        {
            "reason_code": "probability_resolution_source_triage_pass",
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    resign(forged_reasons)
    assert not module.validate_research_strategy_probability_resolution_source_triage_report_payload(
        forged_reasons,
    )

    forged_score = deepcopy(payload)
    forged_score["rows"][0]["triage_risk_score"] = "0.100000"
    forged_score["average_triage_risk_score"] = "0.100000"
    forged_score["highest_triage_risk_score"] = "0.100000"
    resign(forged_score)
    assert not module.validate_research_strategy_probability_resolution_source_triage_report_payload(
        forged_score,
    )


def test_decimal_config_flags_duplicates_and_caller_context_are_validated() -> None:
    module = api()

    with pytest.raises(ValueError, match="forecast_confidence"):
        forecast("int-confidence", forecast_confidence=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_coverage"):
        forecast(
            "decimal-subclass",
            authority_coverage=_DecimalSubclass("0.800000"),
        )
    with pytest.raises(ValueError, match="contradiction_pressure"):
        forecast("bad-pressure", contradiction_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        forecast("bad-flags", paper_only=False)

    duplicate = forecast("duplicate")
    with pytest.raises(ValueError, match="forecast_digest"):
        build_report(duplicate, duplicate)

    with pytest.raises(ValueError, match="fresh_source_age_seconds"):
        module.ResearchStrategyProbabilityResolutionSourceTriageConfig(
            fresh_source_age_seconds=d("90000.000000"),
            stale_source_age_seconds=d("86400.000000"),
        )
    with pytest.raises(ValueError, match="weights"):
        module.ResearchStrategyProbabilityResolutionSourceTriageConfig(
            forecast_confidence_weight=d("0.500000"),
        )
    with pytest.raises(ValueError, match="triage_risk"):
        module.ResearchStrategyProbabilityResolutionSourceTriageConfig(
            triage_risk_watch_threshold=d("0.700000"),
            triage_risk_block_threshold=d("0.600000"),
        )

    row = forecast(
        "context-stable",
        forecast_confidence=d("0.654321"),
        source_age_seconds=d("12345.678901"),
        authority_coverage=d("0.765432"),
        contradiction_pressure=d("0.234567"),
        seconds_until_resolution=d("9876.543210"),
    )
    expected = build_report(row).payload
    with localcontext() as context:
        context.prec = 7
        context.rounding = ROUND_DOWN
        actual = build_report(row).payload
    assert actual == expected


def test_decimal_validation_uses_raw_bounds_and_rejects_signed_zero() -> None:
    module = api()

    with pytest.raises(ValueError, match="forecast_confidence.*between 0 and 1"):
        forecast(
            "raw-upper-bound",
            forecast_confidence=d("1.0000004"),
        )
    with pytest.raises(ValueError, match="source_age_seconds.*nonnegative"):
        forecast(
            "raw-lower-bound",
            source_age_seconds=d("-0.0000004"),
        )
    with pytest.raises(ValueError, match="source_age_seconds.*signed zero"):
        forecast(
            "signed-zero",
            source_age_seconds=d("-0.000000"),
        )

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        with pytest.raises(ValueError, match="weights"):
            module.ResearchStrategyProbabilityResolutionSourceTriageConfig(
                resolution_clock_weight=d("0.150001"),
            )


def test_all_decimal_arithmetic_is_independent_of_hostile_caller_context() -> None:
    row = forecast(
        "hostile-context",
        forecast_confidence=d("0.654321"),
        source_age_seconds=d("12345.678901"),
        authority_coverage=d("0.765432"),
        contradiction_pressure=d("0.234567"),
        seconds_until_resolution=d("9876.543210"),
    )
    expected = build_report(row).payload

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        actual = build_report(row).payload

    assert actual == expected


def test_object_setattr_corruption_is_revalidated_at_every_object_boundary() -> None:
    module = api()

    corrupted_input = forecast("corrupted-input")
    object.__setattr__(corrupted_input, "forecast_confidence", object())
    with pytest.raises(ValueError, match="forecast_confidence must be exactly Decimal"):
        build_report(corrupted_input)

    corrupted_config = module.ResearchStrategyProbabilityResolutionSourceTriageConfig()
    object.__setattr__(corrupted_config, "forecast_confidence_weight", object())
    with pytest.raises(
        ValueError,
        match="forecast_confidence_weight must be exactly Decimal",
    ):
        build_report(config=corrupted_config)

    row_report = build_report(forecast("corrupted-nested-row"))
    object.__setattr__(row_report.rows[0], "forecast_confidence", object())
    with pytest.raises(ValueError, match="forecast_confidence must be exactly Decimal"):
        module.research_strategy_probability_resolution_source_triage_report_payload(
            row_report,
        )

    count_report = build_report(forecast("corrupted-nested-count"))
    object.__setattr__(
        count_report.reason_code_counts[0],
        "count",
        d("1.0000004"),
    )
    with pytest.raises(ValueError, match="count must be a whole Decimal"):
        module.research_strategy_probability_resolution_source_triage_report_payload(
            count_report,
        )


def test_every_public_dataclass_is_frozen_exact_type_and_final() -> None:
    module = api()
    report = build_report(forecast("all-final-types"))
    instances = (
        report.config,
        forecast("final-input"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )

    for instance in instances:
        with pytest.raises(FrozenInstanceError):
            setattr(instance, fields(instance)[0].name, None)
        with pytest.raises(TypeError, match="does not support subclassing"):
            type("ForbiddenSubclass", (type(instance),), {})


def test_public_payload_requires_exact_schema_key_order_and_sha256() -> None:
    module = api()
    report = build_report(forecast("canonical-schema"))
    payload = report.payload

    assert tuple(payload) == tuple(field.name for field in fields(type(report)))
    assert tuple(payload["config"]) == tuple(
        field.name for field in fields(type(report.config))
    )
    assert tuple(payload["rows"][0]) == tuple(
        field.name for field in fields(type(report.rows[0]))
    )
    assert tuple(payload["reason_code_counts"][0]) == tuple(
        field.name for field in fields(type(report.reason_code_counts[0]))
    )

    reordered_payloads = []
    top_level = deepcopy(payload)
    move_first_key_to_end(top_level)
    reordered_payloads.append(top_level)
    nested_config = deepcopy(payload)
    move_first_key_to_end(nested_config["config"])
    reordered_payloads.append(nested_config)
    nested_row = deepcopy(payload)
    move_first_key_to_end(nested_row["rows"][0])
    reordered_payloads.append(nested_row)
    nested_count = deepcopy(payload)
    move_first_key_to_end(nested_count["reason_code_counts"][0])
    reordered_payloads.append(nested_count)

    for reordered in reordered_payloads:
        assert canonical_digest(reordered) == payload["derived_validation_digest"]
        assert not module.validate_research_strategy_probability_resolution_source_triage_report_payload(
            reordered,
        )

    uppercase_digest = deepcopy(payload)
    uppercase_digest["derived_validation_digest"] = payload[
        "derived_validation_digest"
    ].upper()
    assert not module.validate_research_strategy_probability_resolution_source_triage_report_payload(
        uppercase_digest,
    )
    truncated_digest = deepcopy(payload)
    truncated_digest["derived_validation_digest"] = payload[
        "derived_validation_digest"
    ][:-1]
    assert not module.validate_research_strategy_probability_resolution_source_triage_report_payload(
        truncated_digest,
    )


def test_resigned_payload_rederives_every_observation_and_diagnostic_field() -> None:
    module = api()
    report = build_report(
        forecast(
            "tamper-block",
            forecast_confidence=d("0.300000"),
            source_age_seconds=d("90000.000000"),
            authority_coverage=d("0.300000"),
            contradiction_pressure=d("0.700000"),
            seconds_until_resolution=d("900.000000"),
        ),
        forecast("tamper-pass"),
    )
    payload = report.payload
    mutations = (
        (("rows", 0, "forecast_confidence"), "0.310000"),
        (("rows", 0, "source_age_seconds"), "80000.000000"),
        (("rows", 0, "authority_coverage"), "0.310000"),
        (("rows", 0, "contradiction_pressure"), "0.690000"),
        (("rows", 0, "seconds_until_resolution"), "1900.000000"),
        (("rows", 0, "forecast_confidence_risk"), "0.699999"),
        (("rows", 0, "source_freshness_risk"), "0.999999"),
        (("rows", 0, "authority_coverage_risk"), "0.699999"),
        (("rows", 0, "contradiction_pressure_risk"), "0.699999"),
        (("rows", 0, "resolution_clock_risk"), "0.999999"),
        (("rows", 0, "triage_risk_score"), "0.804999"),
        (("rows", 0, "status"), "watch"),
        (("rows", 0, "reason_codes"), ["forecast_confidence_block"]),
        (("rows", 0, "rank"), "2.000000"),
        (("status",), "pass"),
        (("forecast_count",), "3.000000"),
        (("pass_count",), "0.000000"),
        (("watch_count",), "1.000000"),
        (("block_count",), "0.000000"),
        (("average_triage_risk_score",), "0.400000"),
        (("highest_triage_risk_score",), "0.804999"),
        (("reason_codes",), ["probability_resolution_source_triage_pass"]),
        (("reason_code_counts", 0, "count"), "2.000000"),
    )

    for path, replacement in mutations:
        forged = deepcopy(payload)
        replace_path(forged, path, replacement)
        resign(forged)
        assert not module.validate_research_strategy_probability_resolution_source_triage_report_payload(
            forged,
        ), path

    reordered_rows = deepcopy(payload)
    reordered_rows["rows"].reverse()
    resign(reordered_rows)
    assert not module.validate_research_strategy_probability_resolution_source_triage_report_payload(
        reordered_rows,
    )
    reordered_counts = deepcopy(payload)
    reordered_counts["reason_code_counts"].reverse()
    resign(reordered_counts)
    assert not module.validate_research_strategy_probability_resolution_source_triage_report_payload(
        reordered_counts,
    )


def test_equal_scores_use_forecast_digest_as_complete_deterministic_tie_break() -> None:
    first = forecast("tie-first")
    second = forecast("tie-second")
    expected_digests = tuple(sorted((first.forecast_digest, second.forecast_digest)))

    forward = build_report(first, second)
    reverse = build_report(second, first)

    assert tuple(row.forecast_digest for row in forward.rows) == expected_digests
    assert tuple(row.rank for row in forward.rows) == (
        d("1.000000"),
        d("2.000000"),
    )
    assert forward.payload == reverse.payload


def test_public_surface_is_report_only_without_io_execution_or_action_fields() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_RESOLUTION_SOURCE_TRIAGE_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_PROBABILITY_RESOLUTION_SOURCE_TRIAGE_STATUSES",
        "ResearchStrategyProbabilityResolutionSourceTriageConfig",
        "ResearchStrategyProbabilityResolutionSourceTriageInput",
        "ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount",
        "ResearchStrategyProbabilityResolutionSourceTriageReport",
        "ResearchStrategyProbabilityResolutionSourceTriageRow",
        "build_research_strategy_probability_resolution_source_triage_report",
        "research_strategy_probability_resolution_source_triage_report_digest",
        "research_strategy_probability_resolution_source_triage_report_payload",
        "validate_research_strategy_probability_resolution_source_triage_public_payload",
        "validate_research_strategy_probability_resolution_source_triage_report_payload",
    )
    public_types = (
        module.ResearchStrategyProbabilityResolutionSourceTriageConfig,
        module.ResearchStrategyProbabilityResolutionSourceTriageInput,
        module.ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount,
        module.ResearchStrategyProbabilityResolutionSourceTriageReport,
        module.ResearchStrategyProbabilityResolutionSourceTriageRow,
    )
    forbidden_field_fragments = (
        "wallet",
        "authentication",
        "authorization",
        "auth_token",
        "order",
        "trade",
        "execution",
        "recommend",
        "sizing",
        "notional",
        "stake",
        "persist",
        "database",
        "file",
        "url",
        "text",
    )
    for public_type in public_types:
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        for field in fields(public_type):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_field_fragments)

    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    forbidden_calls = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "send",
        "post",
        "put",
        "patch",
        "write",
        "write_text",
        "write_bytes",
        "trade",
        "order",
        "recommend",
        "size",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_calls

    assert imported_roots.isdisjoint(
        {
            "aiohttp",
            "httpx",
            "pathlib",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "subprocess",
            "urllib",
            "web3",
        },
    )


def assert_decimal_public_numbers(value: object) -> None:
    if type(value) is Decimal:
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric was not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            assert_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            assert_decimal_public_numbers(getattr(value, field.name))


def assert_no_public_numeric_scalars(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"public numeric scalar must be a string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_scalars(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_numeric_scalars(item)
