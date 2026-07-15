from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from typing import Any, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, value: datetime | None) -> None:
        return None

    def dst(self, value: datetime | None) -> None:
        return None


class _MalformedTimezone(tzinfo):
    def utcoffset(self, value: datetime | None) -> timedelta:
        raise RuntimeError("malformed offset")

    def dst(self, value: datetime | None) -> timedelta:
        return timedelta(0)


class _DictSubclass(dict[str, object]):
    pass


class _ListSubclass(list[object]):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_specialist_benchmark_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-domain-specialist-benchmark-report-test",
        "min_forecast_sample_count": d("10"),
        "min_pass_calibration_accuracy": d("0.850000"),
        "min_watch_calibration_accuracy": d("0.700000"),
        "min_pass_memory_freshness_ratio": d("0.800000"),
        "min_watch_memory_freshness_ratio": d("0.600000"),
        "max_pass_workload_open_item_count": d("8"),
        "max_watch_workload_open_item_count": d("16"),
        "min_pass_source_coverage_ratio": d("0.800000"),
        "min_watch_source_coverage_ratio": d("0.600000"),
        "min_pass_correction_followthrough_ratio": d("0.750000"),
        "min_watch_correction_followthrough_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainSpecialistBenchmarkConfig(**values)


def fact(**overrides: object):
    module = api()
    values = {
        "team_key": "macro-alpha",
        "domain_key": "macro-rates",
        "specialist_key": "macro-alpha-a",
        "forecast_sample_count": d("10"),
        "calibration_accuracy": d("0.900000"),
        "memory_freshness_ratio": d("0.900000"),
        "workload_open_item_count": d("4"),
        "source_coverage_ratio": d("0.900000"),
        "correction_followthrough_ratio": d("0.900000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainSpecialistBenchmarkFact(**values)


def build_report(*facts: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_specialist_benchmark_report(
        facts,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def resigned_payload(payload: dict[str, object]) -> dict[str, object]:
    resigned = json.loads(json.dumps(payload))
    resigned["derived_validation_digest"] = canonical_digest(resigned)
    return resigned


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected primitive numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
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


def assert_no_signed_decimal_zero(value: object) -> None:
    if type(value) is Decimal:
        assert not (value.is_zero() and value.is_signed())
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_no_signed_decimal_zero(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_no_signed_decimal_zero(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_signed_decimal_zero(item)


def test_builds_deterministic_team_domain_specialist_benchmark_report() -> None:
    report = build_report(
        fact(
            team_key="sports-alpha",
            domain_key="sports",
            specialist_key="sports-alpha-a",
            forecast_sample_count=d("20"),
            calibration_accuracy=d("0.950000"),
            memory_freshness_ratio=d("0.900000"),
            workload_open_item_count=d("5"),
            source_coverage_ratio=d("0.900000"),
            correction_followthrough_ratio=d("0.900000"),
        ),
        fact(
            team_key="macro-alpha",
            domain_key="macro-rates",
            specialist_key="macro-alpha-a",
            forecast_sample_count=d("10"),
            calibration_accuracy=d("0.800000"),
            memory_freshness_ratio=d("0.700000"),
            workload_open_item_count=d("12"),
            source_coverage_ratio=d("0.700000"),
            correction_followthrough_ratio=d("0.600000"),
        ),
        fact(
            team_key="crypto-alpha",
            domain_key="crypto",
            specialist_key="crypto-alpha-a",
            forecast_sample_count=d("4"),
            calibration_accuracy=d("0.600000"),
            memory_freshness_ratio=d("0.500000"),
            workload_open_item_count=d("20"),
            source_coverage_ratio=d("0.500000"),
            correction_followthrough_ratio=d("0.400000"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.team_domain_count == d("3")
    assert report.specialist_count == d("3")
    assert report.forecast_sample_count == d("34")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_calibration_accuracy == d("0.864706")
    assert report.average_memory_freshness_ratio == d("0.794118")
    assert report.total_workload_open_item_count == d("37")
    assert report.average_source_coverage_ratio == d("0.794118")
    assert report.average_correction_followthrough_ratio == d("0.752941")
    assert report.average_benchmark_score == d("0.761691")
    assert report.top_benchmark_score == d("0.883125")
    assert report.bottom_benchmark_score == d("0.440000")
    assert tuple((row.status, row.team_key, row.domain_key) for row in report.rows) == (
        ("pass", "sports-alpha", "sports"),
        ("watch", "macro-alpha", "macro-rates"),
        ("block", "crypto-alpha", "crypto"),
    )
    assert tuple(row.workload_capacity_score for row in report.rows) == (
        d("0.687500"),
        d("0.250000"),
        d("0.000000"),
    )
    assert tuple(row.benchmark_score for row in report.rows) == (
        d("0.883125"),
        d("0.647500"),
        d("0.440000"),
    )
    assert report.rows[0].reason_codes == (
        "team_domain_specialist_benchmark_pass",
    )
    assert report.rows[1].reason_codes == (
        "benchmark_calibration_accuracy_watch",
        "benchmark_memory_freshness_watch",
        "benchmark_workload_watch",
        "benchmark_source_coverage_watch",
        "benchmark_correction_followthrough_watch",
        "team_domain_specialist_benchmark_watch",
    )
    assert report.rows[2].reason_codes == (
        "benchmark_forecast_sample_count_block",
        "benchmark_calibration_accuracy_block",
        "benchmark_memory_freshness_block",
        "benchmark_workload_block",
        "benchmark_source_coverage_block",
        "benchmark_correction_followthrough_block",
        "team_domain_specialist_benchmark_block",
    )
    assert report.reason_codes == (
        "benchmark_forecast_sample_count_block",
        "benchmark_calibration_accuracy_block",
        "benchmark_memory_freshness_block",
        "benchmark_workload_block",
        "benchmark_source_coverage_block",
        "benchmark_correction_followthrough_block",
        "benchmark_calibration_accuracy_watch",
        "benchmark_memory_freshness_watch",
        "benchmark_workload_watch",
        "benchmark_source_coverage_watch",
        "benchmark_correction_followthrough_watch",
        "team_domain_specialist_benchmark_block",
        "team_domain_specialist_benchmark_watch",
    )
    assert report.reason_code_counts[0].reason_code == (
        "benchmark_forecast_sample_count_block"
    )
    assert report.reason_code_counts[0].count == d("1")


def test_aggregates_specialists_by_team_domain_before_scoring() -> None:
    report = build_report(
        fact(
            team_key="macro-alpha",
            domain_key="macro-rates",
            specialist_key="macro-alpha-a",
            forecast_sample_count=d("4"),
            calibration_accuracy=d("0.900000"),
            memory_freshness_ratio=d("0.900000"),
            workload_open_item_count=d("2"),
            source_coverage_ratio=d("0.900000"),
            correction_followthrough_ratio=d("0.900000"),
        ),
        fact(
            team_key="macro-alpha",
            domain_key="macro-rates",
            specialist_key="macro-alpha-b",
            forecast_sample_count=d("6"),
            calibration_accuracy=d("0.700000"),
            memory_freshness_ratio=d("0.500000"),
            workload_open_item_count=d("3"),
            source_coverage_ratio=d("0.700000"),
            correction_followthrough_ratio=d("0.500000"),
        ),
    )

    assert report.team_domain_count == d("1")
    assert report.specialist_count == d("2")
    assert report.forecast_sample_count == d("10")
    assert report.total_workload_open_item_count == d("5")
    assert report.rows[0].team_key == "macro-alpha"
    assert report.rows[0].domain_key == "macro-rates"
    assert report.rows[0].specialist_count == d("2")
    assert report.rows[0].calibration_accuracy == d("0.780000")
    assert report.rows[0].memory_freshness_ratio == d("0.660000")
    assert report.rows[0].source_coverage_ratio == d("0.780000")
    assert report.rows[0].correction_followthrough_ratio == d("0.660000")
    assert report.rows[0].workload_open_item_count == d("5")
    assert report.rows[0].status == "watch"


def test_input_permutations_ties_and_specialist_redaction_are_deterministic() -> None:
    module = api()
    facts = (
        fact(
            team_key="team-bravo",
            domain_key="shared-domain",
            specialist_key="sensitive-specialist-bravo",
        ),
        fact(
            team_key="team-alpha",
            domain_key="shared-domain",
            specialist_key="sensitive-specialist-alpha",
        ),
        fact(
            team_key="team-charlie",
            domain_key="another-domain",
            specialist_key="sensitive-specialist-charlie",
        ),
    )

    forward = build_report(*facts)
    reverse = build_report(*reversed(facts))

    assert forward == reverse
    assert forward.payload == reverse.payload
    assert forward.derived_validation_digest == reverse.derived_validation_digest
    assert tuple((row.domain_key, row.team_key) for row in forward.rows) == (
        ("another-domain", "team-charlie"),
        ("shared-domain", "team-alpha"),
        ("shared-domain", "team-bravo"),
    )

    encoded = json.dumps(forward.payload, sort_keys=True)
    for item in facts:
        assert item.specialist_key not in encoded
    assert "specialist_key" not in encoded

    renamed = build_report(
        *(
            fact(
                team_key=item.team_key,
                domain_key=item.domain_key,
                specialist_key=f"redacted-specialist-{index}",
            )
            for index, item in enumerate(facts, start=1)
        ),
    )
    assert renamed == forward
    assert module.research_team_domain_specialist_benchmark_report_digest(
        renamed,
    ) == module.research_team_domain_specialist_benchmark_report_digest(forward)


def test_empty_fact_set_blocks_report_only_summary() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.team_domain_count == d("0")
    assert report.specialist_count == d("0")
    assert report.forecast_sample_count == d("0")
    assert report.average_calibration_accuracy is None
    assert report.average_memory_freshness_ratio is None
    assert report.total_workload_open_item_count == d("0")
    assert report.average_source_coverage_ratio is None
    assert report.average_correction_followthrough_ratio is None
    assert report.average_benchmark_score is None
    assert report.top_benchmark_score is None
    assert report.bottom_benchmark_score is None
    assert report.rows == ()
    assert report.reason_codes == ("no_team_domain_specialist_benchmark_facts",)
    assert report.reason_code_counts[0].reason_code == (
        "no_team_domain_specialist_benchmark_facts"
    )
    assert report.reason_code_counts[0].count == d("1")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_canonical_digest_bound_and_public_safe() -> None:
    module = api()
    report = build_report(fact())

    payload = module.research_team_domain_specialist_benchmark_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["status"] == "pass"
    assert payload["forecast_sample_count"] == "10"
    assert payload["average_calibration_accuracy"] == "0.900000"
    assert payload["average_memory_freshness_ratio"] == "0.900000"
    assert payload["average_source_coverage_ratio"] == "0.900000"
    assert payload["average_correction_followthrough_ratio"] == "0.900000"
    assert payload["rows"][0]["team_key"] == "macro-alpha"
    assert payload["rows"][0]["domain_key"] == "macro-rates"
    assert payload["rows"][0]["benchmark_score"] == "0.877500"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "private",
        "wallet",
        "order",
        "trade",
        "recommendation",
        "sizing",
        "http://",
        "https://",
    )
    assert all(fragment not in encoded.lower() for fragment in forbidden_fragments)

    tampered = dict(payload)
    tampered["average_calibration_accuracy"] = "0.100000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_specialist_benchmark_report_payload(tampered)

    unsafe = dict(payload)
    unsafe["source_" + "url"] = "https://private.example/source"
    unsafe["derived_validation_digest"] = canonical_digest(unsafe)
    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_domain_specialist_benchmark_report_payload(unsafe)


def test_payload_rejects_resigned_forged_derived_semantics() -> None:
    module = api()
    payload = build_report(fact()).payload

    forged_score = json.loads(json.dumps(payload))
    forged_score["rows"][0]["benchmark_score"] = "0.100000"
    forged_score["average_benchmark_score"] = "0.100000"
    forged_score["top_benchmark_score"] = "0.100000"
    forged_score["bottom_benchmark_score"] = "0.100000"
    with pytest.raises(ValueError, match="benchmark_score"):
        module.research_team_domain_specialist_benchmark_report_payload(
            resigned_payload(forged_score),
        )

    forged_reasons = json.loads(json.dumps(payload))
    forged_reasons["rows"][0]["status"] = "watch"
    forged_reasons["rows"][0]["reason_codes"] = [
        "benchmark_calibration_accuracy_watch",
        "team_domain_specialist_benchmark_watch",
    ]
    forged_reasons["status"] = "watch"
    forged_reasons["pass_count"] = "0"
    forged_reasons["watch_count"] = "1"
    forged_reasons["reason_codes"] = [
        "benchmark_calibration_accuracy_watch",
        "team_domain_specialist_benchmark_watch",
    ]
    forged_reasons["reason_code_counts"] = [
        {
            "reason_code": "benchmark_calibration_accuracy_watch",
            "count": "1",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "reason_code": "team_domain_specialist_benchmark_watch",
            "count": "1",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    with pytest.raises(ValueError, match="status|reason_codes"):
        module.research_team_domain_specialist_benchmark_report_payload(
            resigned_payload(forged_reasons),
        )

    forged_count = dict(payload)
    forged_count["team_domain_count"] = "2"
    with pytest.raises(ValueError, match="team_domain_count"):
        module.research_team_domain_specialist_benchmark_report_payload(
            resigned_payload(forged_count),
        )


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("team_domain_count", "2"),
        ("specialist_count", "2"),
        ("forecast_sample_count", "11"),
        ("pass_count", "0"),
        ("watch_count", "1"),
        ("block_count", "1"),
        ("average_calibration_accuracy", "0.800000"),
        ("average_memory_freshness_ratio", "0.800000"),
        ("total_workload_open_item_count", "5"),
        ("average_source_coverage_ratio", "0.800000"),
        ("average_correction_followthrough_ratio", "0.800000"),
        ("average_benchmark_score", "0.800000"),
        ("top_benchmark_score", "0.800000"),
        ("bottom_benchmark_score", "0.800000"),
    ),
)
def test_resigned_payload_rejects_each_forged_report_derivation(
    field_name: str,
    forged_value: str,
) -> None:
    module = api()
    payload = build_report(fact()).payload
    payload[field_name] = forged_value

    with pytest.raises(ValueError, match=field_name):
        module.research_team_domain_specialist_benchmark_report_payload(
            resigned_payload(payload),
        )


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("workload_capacity_score", "0.700000"),
        ("benchmark_score", "0.700000"),
        ("status", "watch"),
        (
            "reason_codes",
            (
                "benchmark_calibration_accuracy_watch",
                "team_domain_specialist_benchmark_watch",
            ),
        ),
    ),
)
def test_resigned_payload_rejects_each_forged_row_derivation(
    field_name: str,
    forged_value: str | tuple[str, ...],
) -> None:
    module = api()
    payload = build_report(fact()).payload
    payload["rows"][0][field_name] = (
        list(forged_value) if type(forged_value) is tuple else forged_value
    )

    with pytest.raises(ValueError, match=field_name):
        module.research_team_domain_specialist_benchmark_report_payload(
            resigned_payload(payload),
        )


def test_resigned_payload_rejects_reason_counts_and_noncanonical_row_order() -> None:
    module = api()
    payload = build_report(
        fact(
            team_key="team-bravo",
            domain_key="shared-domain",
            specialist_key="specialist-bravo",
        ),
        fact(
            team_key="team-alpha",
            domain_key="shared-domain",
            specialist_key="specialist-alpha",
        ),
    ).payload

    forged_reason_count = json.loads(json.dumps(payload))
    forged_reason_count["reason_code_counts"][0]["count"] = "3"
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.research_team_domain_specialist_benchmark_report_payload(
            resigned_payload(forged_reason_count),
        )

    reordered_rows = json.loads(json.dumps(payload))
    reordered_rows["rows"].reverse()
    with pytest.raises(ValueError, match="deterministic"):
        module.research_team_domain_specialist_benchmark_report_payload(
            resigned_payload(reordered_rows),
        )


def test_payload_requires_exact_nested_schemas_even_when_resigned() -> None:
    module = api()
    payload = build_report(fact()).payload

    def extra_report_field(value: dict[str, Any]) -> None:
        value["public_note"] = "benchmark"

    def missing_report_field(value: dict[str, Any]) -> None:
        value.pop("status")

    def extra_row_field(value: dict[str, Any]) -> None:
        value["rows"][0]["public_note"] = "benchmark"

    def missing_row_field(value: dict[str, Any]) -> None:
        value["rows"][0].pop("benchmark_score")

    def extra_reason_count_field(value: dict[str, Any]) -> None:
        value["reason_code_counts"][0]["public_note"] = "benchmark"

    def missing_reason_count_field(value: dict[str, Any]) -> None:
        value["reason_code_counts"][0].pop("count")

    for mutate in (
        extra_report_field,
        missing_report_field,
        extra_row_field,
        missing_row_field,
        extra_reason_count_field,
        missing_reason_count_field,
    ):
        forged = json.loads(json.dumps(payload))
        mutate(forged)
        with pytest.raises(ValueError, match="schema"):
            module.research_team_domain_specialist_benchmark_report_payload(
                resigned_payload(forged),
            )


def test_payload_requires_exact_json_containers_and_canonical_key_order() -> None:
    module = api()
    payload = build_report(fact()).payload

    top_level_subclass = _DictSubclass(payload)
    with pytest.raises(ValueError, match="exact|JSON object|schema"):
        module.research_team_domain_specialist_benchmark_report_payload(
            top_level_subclass,
        )

    nested_dict_subclass = json.loads(json.dumps(payload))
    nested_dict_subclass["rows"][0] = _DictSubclass(
        nested_dict_subclass["rows"][0],
    )
    with pytest.raises(ValueError, match="exact|JSON object|schema"):
        module.research_team_domain_specialist_benchmark_report_payload(
            nested_dict_subclass,
        )

    nested_list_subclass = json.loads(json.dumps(payload))
    nested_list_subclass["reason_codes"] = _ListSubclass(
        nested_list_subclass["reason_codes"],
    )
    with pytest.raises(ValueError, match="list|schema"):
        module.research_team_domain_specialist_benchmark_report_payload(
            nested_list_subclass,
        )

    tuple_rows = json.loads(json.dumps(payload))
    tuple_rows["rows"] = tuple(tuple_rows["rows"])
    with pytest.raises(ValueError, match="list|schema"):
        module.research_team_domain_specialist_benchmark_report_payload(tuple_rows)

    reordered_report = {
        key: payload[key]
        for key in reversed(tuple(payload))
    }
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_specialist_benchmark_report_payload(
            resigned_payload(reordered_report),
        )

    reordered_row = json.loads(json.dumps(payload))
    row = reordered_row["rows"][0]
    reordered_row["rows"][0] = {key: row[key] for key in reversed(tuple(row))}
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_specialist_benchmark_report_payload(
            resigned_payload(reordered_row),
        )


def test_decimal_bounds_are_checked_before_quantization_and_zero_is_unsigned() -> None:
    module = api()

    canonical = fact(
        forecast_sample_count=d("-0"),
        calibration_accuracy=d("-0.000000"),
        workload_open_item_count=d("-0"),
    )
    for field_name in (
        "forecast_sample_count",
        "calibration_accuracy",
        "workload_open_item_count",
    ):
        value = getattr(canonical, field_name)
        assert value.is_zero()
        assert not value.is_signed()

    with pytest.raises(ValueError, match="calibration_accuracy"):
        fact(calibration_accuracy=d("1.0000004"))
    with pytest.raises(ValueError, match="calibration_accuracy"):
        fact(calibration_accuracy=d("-0.0000004"))

    payload = build_report(fact()).payload
    forged_bound = json.loads(json.dumps(payload))
    forged_bound["rows"][0]["calibration_accuracy"] = "1.0000004"
    with pytest.raises(ValueError, match="calibration_accuracy"):
        module.research_team_domain_specialist_benchmark_report_payload(
            resigned_payload(forged_bound),
        )

    forged_zero = json.loads(json.dumps(payload))
    forged_zero["rows"][0]["calibration_accuracy"] = "-0.000000"
    with pytest.raises(ValueError, match="signed zero"):
        module.research_team_domain_specialist_benchmark_report_payload(
            resigned_payload(forged_zero),
        )


def test_decimal_arithmetic_and_payload_validation_ignore_ambient_context() -> None:
    module = api()
    facts = (
        fact(
            team_key="sports-alpha",
            domain_key="sports",
            specialist_key="sports-alpha-a",
            forecast_sample_count=d("17"),
            calibration_accuracy=d("0.912345"),
            memory_freshness_ratio=d("0.823456"),
            workload_open_item_count=d("5"),
            source_coverage_ratio=d("0.734567"),
            correction_followthrough_ratio=d("0.645678"),
        ),
        fact(
            team_key="macro-alpha",
            domain_key="macro-rates",
            specialist_key="macro-alpha-a",
            forecast_sample_count=d("13"),
            calibration_accuracy=d("0.712345"),
            memory_freshness_ratio=d("0.623456"),
            workload_open_item_count=d("11"),
            source_coverage_ratio=d("0.634567"),
            correction_followthrough_ratio=d("0.545678"),
        ),
    )
    expected = build_report(*facts)
    expected_payload = expected.payload

    with localcontext() as ambient:
        ambient.prec = 2
        ambient.rounding = ROUND_DOWN
        ambient.Emin = -2
        ambient.Emax = 2
        ambient.traps[Inexact] = True
        ambient.traps[Rounded] = True
        actual = build_report(*facts)
        actual_payload = (
            module.research_team_domain_specialist_benchmark_report_payload(actual)
        )
        mapped_payload = (
            module.research_team_domain_specialist_benchmark_report_payload(
                json.loads(json.dumps(actual_payload)),
            )
        )
        canonical_zero_fact = fact(
            forecast_sample_count=d("-0"),
            calibration_accuracy=d("-0.000000"),
            memory_freshness_ratio=d("-0.000000"),
            workload_open_item_count=d("-0"),
            source_coverage_ratio=d("-0.000000"),
            correction_followthrough_ratio=d("-0.000000"),
        )
        zero_report = build_report(canonical_zero_fact)

    assert actual == expected
    assert actual_payload == expected_payload
    assert mapped_payload == expected_payload
    assert_no_signed_decimal_zero(actual)
    assert_no_signed_decimal_zero(canonical_zero_fact)
    assert_no_signed_decimal_zero(zero_report)


def test_supported_config_profile_is_pinned_for_semantic_revalidation() -> None:
    with pytest.raises(ValueError, match="min_pass_calibration_accuracy.*supported default"):
        config(min_pass_calibration_accuracy=d("0.900000"))
    with pytest.raises(ValueError, match="max_watch_workload_open_item_count.*supported default"):
        config(max_watch_workload_open_item_count=d("20"))


def test_validation_rejects_non_decimal_bad_statuses_unsafe_values_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="generated_at"):
        build_report(fact(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            fact(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_research_team_domain_specialist_benchmark_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="team_key"):
        fact(team_key="https://private.example/team")
    with pytest.raises(ValueError, match="forecast_sample_count"):
        fact(forecast_sample_count=10)
    with pytest.raises(ValueError, match="calibration_accuracy"):
        fact(calibration_accuracy=0.1)
    with pytest.raises(ValueError, match="memory_freshness_ratio"):
        fact(memory_freshness_ratio=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="workload_open_item_count"):
        fact(workload_open_item_count=d("1.5"))
    with pytest.raises(ValueError, match="source_coverage_ratio"):
        fact(source_coverage_ratio=Decimal("NaN"))
    with pytest.raises(ValueError, match="pass threshold"):
        config(min_pass_calibration_accuracy=d("0.600000"))
    with pytest.raises(ValueError, match="workload watch threshold"):
        config(max_pass_workload_open_item_count=d("20"))
    with pytest.raises(ValueError, match="facts"):
        build_report(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicate"):
        build_report(fact(), fact())
    with pytest.raises(ValueError, match="paper_only"):
        replace(fact(), paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(build_report(fact()), status="blocked")
    with pytest.raises(TypeError):
        type("FactSubclass", (module.ResearchTeamDomainSpecialistBenchmarkFact,), {})


def test_builder_revalidates_frozen_config_and_fact_instances_at_ingress() -> None:
    tampered_config = config()
    object.__setattr__(
        tampered_config,
        "max_watch_workload_open_item_count",
        d("20"),
    )
    with pytest.raises(
        ValueError,
        match="max_watch_workload_open_item_count.*supported default",
    ):
        build_report(fact(), cfg=tampered_config)

    tampered_scalar = fact()
    object.__setattr__(tampered_scalar, "calibration_accuracy", 0.9)
    with pytest.raises(ValueError, match="calibration_accuracy.*Decimal"):
        build_report(tampered_scalar)

    tampered_identifier = fact()
    object.__setattr__(tampered_identifier, "specialist_key", "Unsafe Specialist")
    with pytest.raises(ValueError, match="specialist_key"):
        build_report(tampered_identifier)


def test_generated_at_is_exact_canonical_utc_report_as_of() -> None:
    module = api()
    shifted_as_of = GENERATED_AT.astimezone(timezone(-timedelta(hours=7)))
    shifted_report = build_report(fact(), generated_at=shifted_as_of)

    assert shifted_report.generated_at == GENERATED_AT
    assert shifted_report.generated_at.tzinfo is UTC
    assert shifted_report.payload["generated_at"] == "2026-07-08T12:00:00+00:00"

    future_report_as_of = datetime(2099, 1, 1, tzinfo=UTC)
    assert build_report(fact(), generated_at=future_report_as_of).generated_at == (
        future_report_as_of
    )

    for bad_timezone in (_NoneOffsetTimezone(), _MalformedTimezone()):
        with pytest.raises(ValueError, match="generated_at.*timezone-aware"):
            build_report(
                fact(),
                generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=bad_timezone),
            )

    payload = shifted_report.payload
    for noncanonical_text in (
        "2026-07-08T12:00:00Z",
        "2026-07-08T05:00:00-07:00",
        "2026-07-08T12:00:00.000000+00:00",
    ):
        forged = json.loads(json.dumps(payload))
        forged["generated_at"] = noncanonical_text
        with pytest.raises(ValueError, match="generated_at.*canonical UTC"):
            module.research_team_domain_specialist_benchmark_report_payload(
                resigned_payload(forged),
            )


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    report = build_report(fact())
    items = (
        config(),
        fact(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )

    for item in items:
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    decimal_fields = {
        "min_forecast_sample_count",
        "min_pass_calibration_accuracy",
        "min_watch_calibration_accuracy",
        "min_pass_memory_freshness_ratio",
        "min_watch_memory_freshness_ratio",
        "max_pass_workload_open_item_count",
        "max_watch_workload_open_item_count",
        "min_pass_source_coverage_ratio",
        "min_watch_source_coverage_ratio",
        "min_pass_correction_followthrough_ratio",
        "min_watch_correction_followthrough_ratio",
        "forecast_sample_count",
        "calibration_accuracy",
        "memory_freshness_ratio",
        "workload_open_item_count",
        "source_coverage_ratio",
        "correction_followthrough_ratio",
        "specialist_count",
        "workload_capacity_score",
        "benchmark_score",
        "team_domain_count",
        "pass_count",
        "watch_count",
        "block_count",
        "total_workload_open_item_count",
        "count",
    }
    optional_decimal_fields = {
        "average_calibration_accuracy",
        "average_memory_freshness_ratio",
        "average_source_coverage_ratio",
        "average_correction_followthrough_ratio",
        "average_benchmark_score",
        "top_benchmark_score",
        "bottom_benchmark_score",
    }
    for cls in (
        module.ResearchTeamDomainSpecialistBenchmarkConfig,
        module.ResearchTeamDomainSpecialistBenchmarkFact,
        module.ResearchTeamDomainSpecialistBenchmarkRow,
        module.ResearchTeamDomainSpecialistBenchmarkReasonCodeCount,
        module.ResearchTeamDomainSpecialistBenchmarkReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in decimal_fields:
                assert hints[item.name] is Decimal
            if item.name in optional_decimal_fields:
                assert hints[item.name] == Decimal | None
        with pytest.raises(TypeError):
            type(f"{cls.__name__}Subclass", (cls,), {})

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    assert module.research_team_domain_specialist_benchmark_report_digest(
        report,
    ) == report.derived_validation_digest


def test_public_dataclass_and_export_schemas_are_exact_final_and_timeless() -> None:
    module = api()
    expected_fields = {
        module.ResearchTeamDomainSpecialistBenchmarkConfig: (
            "config_version",
            "min_forecast_sample_count",
            "min_pass_calibration_accuracy",
            "min_watch_calibration_accuracy",
            "min_pass_memory_freshness_ratio",
            "min_watch_memory_freshness_ratio",
            "max_pass_workload_open_item_count",
            "max_watch_workload_open_item_count",
            "min_pass_source_coverage_ratio",
            "min_watch_source_coverage_ratio",
            "min_pass_correction_followthrough_ratio",
            "min_watch_correction_followthrough_ratio",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchTeamDomainSpecialistBenchmarkFact: (
            "team_key",
            "domain_key",
            "specialist_key",
            "forecast_sample_count",
            "calibration_accuracy",
            "memory_freshness_ratio",
            "workload_open_item_count",
            "source_coverage_ratio",
            "correction_followthrough_ratio",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchTeamDomainSpecialistBenchmarkRow: (
            "team_key",
            "domain_key",
            "specialist_count",
            "forecast_sample_count",
            "calibration_accuracy",
            "memory_freshness_ratio",
            "workload_open_item_count",
            "workload_capacity_score",
            "source_coverage_ratio",
            "correction_followthrough_ratio",
            "benchmark_score",
            "status",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchTeamDomainSpecialistBenchmarkReasonCodeCount: (
            "reason_code",
            "count",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchTeamDomainSpecialistBenchmarkReport: (
            "generated_at",
            "config_version",
            "status",
            "team_domain_count",
            "specialist_count",
            "forecast_sample_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_calibration_accuracy",
            "average_memory_freshness_ratio",
            "total_workload_open_item_count",
            "average_source_coverage_ratio",
            "average_correction_followthrough_ratio",
            "average_benchmark_score",
            "top_benchmark_score",
            "bottom_benchmark_score",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }
    expected_exports = (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_BENCHMARK_CONFIG_VERSION",
        "ResearchTeamDomainSpecialistBenchmarkConfig",
        "ResearchTeamDomainSpecialistBenchmarkFact",
        "ResearchTeamDomainSpecialistBenchmarkReasonCodeCount",
        "ResearchTeamDomainSpecialistBenchmarkReport",
        "ResearchTeamDomainSpecialistBenchmarkRow",
        "build_research_team_domain_specialist_benchmark_report",
        "research_team_domain_specialist_benchmark_report_digest",
        "research_team_domain_specialist_benchmark_report_payload",
    )

    assert module.__all__ == expected_exports
    module_dataclasses = {
        value
        for value in vars(module).values()
        if isinstance(value, type) and is_dataclass(value)
    }
    assert module_dataclasses == set(expected_fields)
    for dataclass_type, schema in expected_fields.items():
        assert tuple(field.name for field in fields(dataclass_type)) == schema
        with pytest.raises(TypeError, match="subclassing"):
            type(f"Unsafe{dataclass_type.__name__}", (dataclass_type,), {})

    fact_schema = expected_fields[module.ResearchTeamDomainSpecialistBenchmarkFact]
    assert "observed_at" not in fact_schema
    assert "as_of" not in fact_schema


def test_owned_module_has_no_db_network_wallet_order_trade_sizing_or_recommendation_surface() -> None:
    source = inspect.getsource(api())
    lowered = source.lower()
    for forbidden in (
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "private",
        "wallet",
        "order",
        "trade",
        "database",
        "network",
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "recommend",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    field_names: list[str] = []
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
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            field_names.append(node.target.id)
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
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "cancel",
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
        "persist",
        "rollback",
        "send",
        "write",
    }
    forbidden_field_names = {
        "account_id",
        "auth_token",
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "order_id",
        "private_token",
        "raw_candidate_id",
        "raw_market_id",
        "source_text",
        "source_url",
        "trade_id",
        "wallet_address",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert not any(name in forbidden_field_names for name in field_names)
    assert_no_float_or_int_values([imports, call_names, attribute_names, field_names])
