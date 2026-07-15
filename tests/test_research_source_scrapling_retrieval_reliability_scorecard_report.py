from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from itertools import permutations
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_scrapling_retrieval_reliability_scorecard_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_scrapling_retrieval_reliability_scorecard_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
RETRIEVED_AT = datetime(2026, 7, 9, 11, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


class _DictSubclass(dict):
    pass


class _ListSubclass(list):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _RaisingOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        raise RuntimeError("hostile timezone hook")

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "fresh_content_max_age_seconds": d("3600.000000"),
        "stale_content_block_age_seconds": d("86400.000000"),
        "min_success_ratio_pass": d("0.900000"),
        "min_success_ratio_watch": d("0.650000"),
        "min_primary_source_match_ratio_pass": d("0.800000"),
        "min_primary_source_match_ratio_watch": d("0.500000"),
        "min_parse_completeness_ratio_pass": d("0.900000"),
        "min_parse_completeness_ratio_watch": d("0.600000"),
        "max_contradiction_count_pass": d("0"),
        "max_contradiction_count_watch": d("2"),
        "min_reliability_score_pass": d("0.800000"),
        "min_reliability_score_watch": d("0.500000"),
        "success_ratio_weight": d("0.250000"),
        "content_freshness_weight": d("0.200000"),
        "primary_source_match_weight": d("0.200000"),
        "parse_completeness_weight": d("0.200000"),
        "contradiction_weight": d("0.150000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceScraplingRetrievalReliabilityScorecardConfig(**values)


def observation(
    private_retrieval_ref: str = "private-retrieval",
    *,
    retrieved_at: datetime = RETRIEVED_AT,
    retrieval_attempt_count: Decimal = d("10"),
    retrieval_success_count: Decimal = d("10"),
    primary_source_match_count: Decimal = d("10"),
    parsed_field_count: Decimal = d("10"),
    expected_field_count: Decimal = d("10"),
    contradiction_count: Decimal = d("0"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceScraplingRetrievalReliabilityObservation(
        private_retrieval_ref=private_retrieval_ref,
        retrieved_at=retrieved_at,
        retrieval_attempt_count=retrieval_attempt_count,
        retrieval_success_count=retrieval_success_count,
        primary_source_match_count=primary_source_match_count,
        parsed_field_count=parsed_field_count,
        expected_field_count=expected_field_count,
        contradiction_count=contradiction_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*observations: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_source_scrapling_retrieval_reliability_scorecard_report(
        observations,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = json.loads(json.dumps(payload))
    resigned["derived_validation_digest"] = canonical_digest(resigned)
    return resigned


def assert_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        if value.is_zero():
            assert value.is_signed() is False
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric was not Decimal: {value!r}")
    if type(value) is tuple:
        for item in value:
            assert_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            assert_decimal_public_numbers(getattr(value, field.name))


def assert_payload_has_no_raw_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"payload leaked raw numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_payload_has_no_raw_numbers(item)
    elif type(value) is list:
        for item in value:
            assert_payload_has_no_raw_numbers(item)


def test_empty_input_blocks_with_frozen_decimal_only_canonical_payload() -> None:
    module = api()
    scorecard = report()

    assert type(scorecard) is (
        module.ResearchSourceScraplingRetrievalReliabilityScorecardReport
    )
    assert is_dataclass(scorecard)
    assert scorecard.__dataclass_params__.frozen
    assert scorecard.generated_at == GENERATED_AT
    assert scorecard.config_version == (
        "research-source-scrapling-retrieval-reliability-scorecard-report-v0"
    )
    assert scorecard.input_count == d("0.000000")
    assert scorecard.row_count == d("0.000000")
    assert scorecard.pass_count == d("0.000000")
    assert scorecard.watch_count == d("0.000000")
    assert scorecard.block_count == d("0.000000")
    assert scorecard.attention_count == d("0.000000")
    assert scorecard.contradiction_count == d("0.000000")
    assert scorecard.average_reliability_score == d("0.000000")
    assert scorecard.status == "block"
    assert scorecard.reason_codes == (
        "scrapling_retrieval_reliability_no_inputs",
        "scrapling_retrieval_reliability_block",
    )
    assert scorecard.rows == ()
    assert scorecard.paper_only is True
    assert scorecard.report_only is True
    assert scorecard.readonly is True
    assert_decimal_public_numbers(scorecard)

    payload = (
        module.research_source_scrapling_retrieval_reliability_scorecard_report_payload(
            scorecard,
        )
    )
    assert payload == scorecard.payload
    assert payload["input_count"] == "0.000000"
    assert payload["config"]["max_contradiction_count_watch"] == "2.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert (
        module.research_source_scrapling_retrieval_reliability_scorecard_report_digest(
            scorecard,
        )
        == payload["derived_validation_digest"]
    )
    assert scorecard.digest == payload["derived_validation_digest"]
    assert module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        payload,
    )
    assert_payload_has_no_raw_numbers(payload)


def test_scores_success_freshness_primary_match_parse_and_contradictions() -> None:
    scorecard = report(
        observation("a-private-pass"),
        observation(
            "b-private-watch",
            retrieved_at=GENERATED_AT - timedelta(seconds=7200),
            retrieval_success_count=d("7"),
            primary_source_match_count=d("5"),
            parsed_field_count=d("8"),
            contradiction_count=d("1"),
        ),
        observation(
            "c-private-block",
            retrieved_at=GENERATED_AT - timedelta(seconds=90000),
            retrieval_attempt_count=d("5"),
            retrieval_success_count=d("0"),
            primary_source_match_count=d("0"),
            parsed_field_count=d("4"),
            expected_field_count=d("10"),
            contradiction_count=d("3"),
        ),
    )

    assert scorecard.status == "block"
    assert scorecard.input_count == d("3.000000")
    assert scorecard.pass_count == d("1.000000")
    assert scorecard.watch_count == d("1.000000")
    assert scorecard.block_count == d("1.000000")
    assert scorecard.attention_count == d("2.000000")
    assert scorecard.max_content_age_seconds == d("90000.000000")
    assert scorecard.contradiction_count == d("4.000000")
    assert scorecard.average_success_ratio == d("0.566667")
    assert scorecard.average_content_freshness_score == d("0.652174")
    assert scorecard.average_primary_source_match_ratio == d("0.571429")
    assert scorecard.average_parse_completeness_ratio == d("0.733333")
    assert scorecard.average_contradiction_score == d("0.500000")
    assert scorecard.average_reliability_score == d("0.608054")

    block_row, watch_row, pass_row = scorecard.rows
    assert tuple(row.status for row in scorecard.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert tuple(row.row_label for row in scorecard.rows) == (
        "redacted-scrapling-retrieval-000003",
        "redacted-scrapling-retrieval-000002",
        "redacted-scrapling-retrieval-000001",
    )
    assert block_row.reliability_score == d("0.080000")
    assert block_row.reason_codes == (
        "success_ratio_block",
        "content_freshness_block",
        "primary_source_match_block",
        "parse_completeness_block",
        "contradiction_count_block",
        "scrapling_retrieval_reliability_block",
    )
    assert watch_row.success_ratio == d("0.700000")
    assert watch_row.content_freshness_score == d("0.956522")
    assert watch_row.primary_source_match_ratio == d("0.714286")
    assert watch_row.parse_completeness_ratio == d("0.800000")
    assert watch_row.contradiction_score == d("0.500000")
    assert watch_row.reliability_score == d("0.744162")
    assert watch_row.reason_codes == (
        "success_ratio_watch",
        "content_freshness_watch",
        "primary_source_match_watch",
        "parse_completeness_watch",
        "contradiction_count_watch",
        "scrapling_retrieval_reliability_watch",
    )
    assert pass_row.reliability_score == d("1.000000")
    assert pass_row.reason_codes == ("scrapling_retrieval_reliability_pass",)


def test_payload_is_deterministic_and_rejects_forged_resigned_derived_logic() -> None:
    module = api()
    observations = (
        observation("same-private-ref"),
        observation(
            "same-private-ref",
            retrieval_success_count=d("7"),
            primary_source_match_count=d("5"),
            parsed_field_count=d("8"),
            contradiction_count=d("1"),
        ),
    )
    first = report(*observations)
    second = report(*reversed(observations))
    payload = first.payload

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == second.payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        payload,
    )

    forged_row_status = json.loads(json.dumps(payload))
    forged_row_status["rows"][0]["status"] = "pass"
    forged_row_status = resign_payload(forged_row_status)
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        forged_row_status,
    )

    forged_row_reasons = json.loads(json.dumps(payload))
    forged_row_reasons["rows"][0]["reason_codes"] = [
        "scrapling_retrieval_reliability_pass",
    ]
    forged_row_reasons = resign_payload(forged_row_reasons)
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        forged_row_reasons,
    )

    forged_report_logic = json.loads(json.dumps(payload))
    forged_report_logic["status"] = "pass"
    forged_report_logic["reason_codes"] = [
        "scrapling_retrieval_reliability_pass",
    ]
    forged_report_logic = resign_payload(forged_report_logic)
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        forged_report_logic,
    )

    forged_aggregate = json.loads(json.dumps(payload))
    forged_aggregate["average_success_ratio"] = "1.000000"
    forged_aggregate = resign_payload(forged_aggregate)
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        forged_aggregate,
    )


def test_private_retrieval_refs_do_not_influence_public_payload_or_digest() -> None:
    first_observations = (
        observation(
            "private-ref-a",
            retrieval_success_count=d("7"),
            primary_source_match_count=d("5"),
            parsed_field_count=d("8"),
            contradiction_count=d("1"),
        ),
        observation("private-ref-z"),
    )
    second_observations = (
        replace(first_observations[0], private_retrieval_ref="private-ref-z"),
        replace(first_observations[1], private_retrieval_ref="private-ref-a"),
    )

    first = report(*first_observations)
    second = report(*reversed(second_observations))

    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest


def test_complete_public_sort_ties_are_input_order_and_private_ref_independent() -> None:
    observations = (
        observation(
            "private-a",
            retrieved_at=GENERATED_AT - timedelta(seconds=120),
            retrieval_attempt_count=d("5"),
            retrieval_success_count=d("5"),
            primary_source_match_count=d("5"),
            parsed_field_count=d("5"),
            expected_field_count=d("5"),
        ),
        observation(
            "private-b",
            retrieved_at=GENERATED_AT - timedelta(seconds=120),
        ),
        observation(
            "private-c",
            retrieved_at=GENERATED_AT - timedelta(seconds=60),
        ),
    )

    payloads = tuple(report(*ordering).payload for ordering in permutations(observations))

    assert all(payload == payloads[0] for payload in payloads)
    assert tuple(row["row_label"] for row in payloads[0]["rows"]) == (
        "redacted-scrapling-retrieval-000001",
        "redacted-scrapling-retrieval-000002",
        "redacted-scrapling-retrieval-000003",
    )


def test_resigned_payload_rejects_forged_row_identity_rank_mapping() -> None:
    module = api()
    payload = report(
        observation(
            "private-five-attempts",
            retrieval_attempt_count=d("5"),
            retrieval_success_count=d("5"),
            primary_source_match_count=d("5"),
        ),
        observation("private-ten-attempts"),
    ).payload

    forged = json.loads(json.dumps(payload))
    first_label = forged["rows"][0]["row_label"]
    second_label = forged["rows"][1]["row_label"]
    forged["rows"][0]["row_label"] = second_label
    forged["rows"][1]["row_label"] = first_label
    forged["rows"].sort(key=lambda row: row["row_label"])
    forged = resign_payload(forged)

    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        forged,
    )


def test_resigned_payload_rederives_score_counts_and_aggregates() -> None:
    module = api()
    payload = report(observation()).payload

    forged_score = json.loads(json.dumps(payload))
    forged_score["rows"][0]["reliability_score"] = "0.999999"

    forged_row_count = json.loads(json.dumps(payload))
    forged_row_count["row_count"] = "2.000000"

    forged_reason_count = json.loads(json.dumps(payload))
    forged_reason_count["reason_code_counts"][0]["count"] = "2.000000"

    forged_aggregate = json.loads(json.dumps(payload))
    forged_aggregate["average_reliability_score"] = "0.999999"

    for forged in (
        forged_score,
        forged_row_count,
        forged_reason_count,
        forged_aggregate,
    ):
        assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
            resign_payload(forged),
        )


def test_resigned_payload_rederives_every_remaining_public_derivative() -> None:
    module = api()
    payload = report(
        observation(
            "block",
            retrieved_at=GENERATED_AT - timedelta(seconds=90000),
            retrieval_attempt_count=d("5"),
            retrieval_success_count=d("0"),
            primary_source_match_count=d("0"),
            parsed_field_count=d("4"),
            expected_field_count=d("10"),
            contradiction_count=d("3"),
        ),
        observation(
            "watch",
            retrieved_at=GENERATED_AT - timedelta(seconds=7200),
            retrieval_success_count=d("7"),
            primary_source_match_count=d("5"),
            parsed_field_count=d("8"),
            contradiction_count=d("1"),
        ),
        observation("pass"),
    ).payload

    forged_payloads: list[dict[str, Any]] = []
    for field_name in (
        "retrieval_attempt_count",
        "retrieval_success_count",
        "primary_source_match_count",
        "parsed_field_count",
        "expected_field_count",
        "contradiction_count",
        "success_ratio",
        "content_freshness_score",
        "primary_source_match_ratio",
        "parse_completeness_ratio",
        "contradiction_score",
    ):
        forged = json.loads(json.dumps(payload))
        forged["rows"][0][field_name] = "0.999999"
        forged_payloads.append(forged)

    for field_name in (
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "attention_count",
        "max_content_age_seconds",
        "contradiction_count",
        "average_success_ratio",
        "average_content_freshness_score",
        "average_primary_source_match_ratio",
        "average_parse_completeness_ratio",
        "average_contradiction_score",
    ):
        forged = json.loads(json.dumps(payload))
        forged[field_name] = "0.999999"
        forged_payloads.append(forged)

    forged_rows_order = json.loads(json.dumps(payload))
    forged_rows_order["rows"].reverse()
    forged_payloads.append(forged_rows_order)

    for forged in forged_payloads:
        assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
            resign_payload(forged),
        )


def test_payload_schema_and_canonical_encoding_are_exact() -> None:
    module = api()
    payload = report(observation()).payload

    extra_top_level = json.loads(json.dumps(payload))
    extra_top_level["unexpected"] = "field"
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        resign_payload(extra_top_level),
    )

    missing_nested = json.loads(json.dumps(payload))
    del missing_nested["rows"][0]["success_ratio"]
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        resign_payload(missing_nested),
    )

    noncanonical_decimal = json.loads(json.dumps(payload))
    noncanonical_decimal["rows"][0]["success_ratio"] = "1"
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        resign_payload(noncanonical_decimal),
    )

    noncanonical_datetime = json.loads(json.dumps(payload))
    noncanonical_datetime["generated_at"] = "2026-07-09T12:00:00Z"
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        resign_payload(noncanonical_datetime),
    )


def test_payload_rejects_resigned_noncanonical_mapping_key_order() -> None:
    module = api()
    payload = report(observation()).payload

    for field_name in ("report", "config", "reason_code_counts", "rows"):
        noncanonical = json.loads(json.dumps(payload))
        if field_name == "report":
            noncanonical = dict(reversed(noncanonical.items()))
        elif field_name == "config":
            noncanonical[field_name] = dict(reversed(noncanonical[field_name].items()))
        else:
            noncanonical[field_name][0] = dict(
                reversed(noncanonical[field_name][0].items()),
            )

        assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
            resign_payload(noncanonical),
        )


def test_payload_validator_fails_closed_for_recursive_mappings() -> None:
    module = api()
    recursive: dict[str, Any] = {}
    recursive["recursive"] = recursive

    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        recursive,
    )


def test_utc_conversion_boundaries_fail_closed_without_overflow_leaks() -> None:
    module = api()
    underflowing_utc = datetime.min.replace(
        tzinfo=timezone(timedelta(hours=1)),
    )

    with pytest.raises(ValueError, match="generated_at.*UTC"):
        module.build_research_source_scrapling_retrieval_reliability_scorecard_report(
            (),
            config=config(),
            generated_at=underflowing_utc,
        )

    payload = report().payload
    payload["generated_at"] = underflowing_utc.isoformat()
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        resign_payload(payload),
    )


def test_retrieval_time_uses_utc_and_rejects_the_first_future_microsecond() -> None:
    equivalent_offset_time = GENERATED_AT.astimezone(
        timezone(timedelta(hours=5, minutes=30)),
    )
    at_boundary = report(observation(retrieved_at=equivalent_offset_time))

    assert at_boundary.rows[0].content_age_seconds == d("0.000000")
    with pytest.raises(ValueError, match="cannot be after generated_at"):
        report(
            observation(
                retrieved_at=GENERATED_AT + timedelta(microseconds=1),
            ),
        )


def test_build_revalidates_config_tampered_via_object_setattr() -> None:
    corrupted_config = config()
    object.__setattr__(corrupted_config, "min_success_ratio_watch", d("1.100000"))

    with pytest.raises(ValueError, match="min_success_ratio_watch must be between 0 and 1"):
        report(
            observation(
                retrieval_success_count=d("7"),
                primary_source_match_count=d("5"),
                parsed_field_count=d("8"),
                contradiction_count=d("1"),
            ),
            cfg=corrupted_config,
        )


def test_build_revalidates_observation_tampered_via_object_setattr() -> None:
    corrupted_observation = observation()
    object.__setattr__(corrupted_observation, "private_retrieval_ref", "")

    with pytest.raises(ValueError, match="private_retrieval_ref must be a non-empty string"):
        report(corrupted_observation)


def test_report_revalidates_nested_row_tampered_via_object_setattr() -> None:
    module = api()
    built = report(observation())
    corrupted_row = built.rows[0]
    object.__setattr__(corrupted_row, "retrieval_attempt_count", d("0"))

    with pytest.raises(ValueError, match="retrieval_attempt_count must be positive"):
        module.ResearchSourceScraplingRetrievalReliabilityScorecardReport(
            **{**built.__dict__, "derived_validation_digest": ""},
        )


def test_report_revalidates_reason_count_tampered_via_object_setattr() -> None:
    module = api()
    built = report(observation())
    corrupted_count = built.reason_code_counts[0]
    object.__setattr__(corrupted_count, "count", _DecimalSubclass("1"))

    with pytest.raises(ValueError, match="count must be exactly Decimal"):
        module.ResearchSourceScraplingRetrievalReliabilityScorecardReport(
            **{**built.__dict__, "derived_validation_digest": ""},
        )


def test_public_export_rejects_redigested_signed_zero_object_state() -> None:
    module = api()
    built = report()
    object.__setattr__(built, "input_count", d("-0.000000"))
    object.__setattr__(built, "derived_validation_digest", module._report_digest(built))

    with pytest.raises(ValueError, match="input_count|derived_validation_digest"):
        _ = built.payload


def test_public_export_revalidates_redigested_nested_safety_state() -> None:
    module = api()

    row_tampered = report(observation())
    object.__setattr__(row_tampered.rows[0], "readonly", False)
    object.__setattr__(
        row_tampered,
        "derived_validation_digest",
        module._report_digest(row_tampered),
    )
    with pytest.raises(ValueError, match="readonly"):
        _ = row_tampered.payload

    config_tampered = report()
    object.__setattr__(
        config_tampered.config,
        "min_success_ratio_watch",
        d("1.100000"),
    )
    object.__setattr__(
        config_tampered,
        "derived_validation_digest",
        module._report_digest(config_tampered),
    )
    with pytest.raises(ValueError, match="min_success_ratio_watch"):
        _ = config_tampered.payload


def test_public_api_dataclass_and_payload_schemas_are_exact_and_final() -> None:
    module = api()
    expected_fields = {
        module.ResearchSourceScraplingRetrievalReliabilityScorecardConfig: (
            "config_version",
            "fresh_content_max_age_seconds",
            "stale_content_block_age_seconds",
            "min_success_ratio_pass",
            "min_success_ratio_watch",
            "min_primary_source_match_ratio_pass",
            "min_primary_source_match_ratio_watch",
            "min_parse_completeness_ratio_pass",
            "min_parse_completeness_ratio_watch",
            "max_contradiction_count_pass",
            "max_contradiction_count_watch",
            "min_reliability_score_pass",
            "min_reliability_score_watch",
            "success_ratio_weight",
            "content_freshness_weight",
            "primary_source_match_weight",
            "parse_completeness_weight",
            "contradiction_weight",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchSourceScraplingRetrievalReliabilityObservation: (
            "private_retrieval_ref",
            "retrieved_at",
            "retrieval_attempt_count",
            "retrieval_success_count",
            "primary_source_match_count",
            "parsed_field_count",
            "expected_field_count",
            "contradiction_count",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchSourceScraplingRetrievalReliabilityScorecardRow: (
            "row_label",
            "content_age_seconds",
            "retrieval_attempt_count",
            "retrieval_success_count",
            "primary_source_match_count",
            "parsed_field_count",
            "expected_field_count",
            "contradiction_count",
            "success_ratio",
            "content_freshness_score",
            "primary_source_match_ratio",
            "parse_completeness_ratio",
            "contradiction_score",
            "reliability_score",
            "status",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount: (
            "reason_code",
            "count",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchSourceScraplingRetrievalReliabilityScorecardReport: (
            "generated_at",
            "config_version",
            "config",
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "attention_count",
            "max_content_age_seconds",
            "contradiction_count",
            "average_success_ratio",
            "average_content_freshness_score",
            "average_primary_source_match_ratio",
            "average_parse_completeness_ratio",
            "average_contradiction_score",
            "average_reliability_score",
            "status",
            "reason_codes",
            "reason_code_counts",
            "rows",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_SCRAPLING_RETRIEVAL_RELIABILITY_SCORECARD_REPORT_CONFIG_VERSION",
        "ResearchSourceScraplingRetrievalReliabilityObservation",
        "ResearchSourceScraplingRetrievalReliabilityScorecardConfig",
        "ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount",
        "ResearchSourceScraplingRetrievalReliabilityScorecardReport",
        "ResearchSourceScraplingRetrievalReliabilityScorecardRow",
        "STATUSES",
        "build_research_source_scrapling_retrieval_reliability_scorecard_report",
        "research_source_scrapling_retrieval_reliability_scorecard_report_digest",
        "research_source_scrapling_retrieval_reliability_scorecard_report_payload",
        "validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload",
    )
    for dataclass_type, expected_names in expected_fields.items():
        assert tuple(field.name for field in fields(dataclass_type)) == expected_names
        assert dataclass_type.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Bad{dataclass_type.__name__}", (dataclass_type,), {})

    payload = report(observation()).payload
    assert tuple(payload) == expected_fields[
        module.ResearchSourceScraplingRetrievalReliabilityScorecardReport
    ]
    assert tuple(payload["config"]) == expected_fields[
        module.ResearchSourceScraplingRetrievalReliabilityScorecardConfig
    ]
    assert tuple(payload["rows"][0]) == expected_fields[
        module.ResearchSourceScraplingRetrievalReliabilityScorecardRow
    ]
    assert tuple(payload["reason_code_counts"][0]) == expected_fields[
        module.ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount
    ]


def test_strict_types_frozen_records_hard_flags_and_count_consistency() -> None:
    module = api()
    built = report(observation())

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    public_dataclass_types = (
        module.ResearchSourceScraplingRetrievalReliabilityScorecardConfig,
        module.ResearchSourceScraplingRetrievalReliabilityObservation,
        module.ResearchSourceScraplingRetrievalReliabilityScorecardRow,
        module.ResearchSourceScraplingRetrievalReliabilityScorecardReasonCodeCount,
        module.ResearchSourceScraplingRetrievalReliabilityScorecardReport,
    )
    for dataclass_type in public_dataclass_types:
        assert is_dataclass(dataclass_type)
        assert dataclass_type.__dataclass_params__.frozen
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Bad{dataclass_type.__name__}", (dataclass_type,), {})

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(observation(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)
    with pytest.raises(ValueError, match="exactly Decimal"):
        observation(retrieval_success_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="retrieved_at must be exactly datetime"):
        observation(
            retrieved_at=_DatetimeSubclass(2026, 7, 9, 11, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="private_retrieval_ref"):
        observation(_StringSubclass("private-retrieval"))
    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                "research-source-scrapling-retrieval-reliability-scorecard-report-v0",
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status=_StringSubclass(built.rows[0].status))
    with pytest.raises(ValueError, match="timezone-aware"):
        observation(retrieved_at=datetime(2026, 7, 9, 11, 30))
    with pytest.raises(ValueError, match="utcoffset"):
        observation(
            retrieved_at=datetime(2026, 7, 9, 11, 30, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="valid UTC offset"):
        observation(
            retrieved_at=datetime(2026, 7, 9, 11, 30, tzinfo=_RaisingOffsetTz()),
        )
    with pytest.raises(ValueError, match="cannot be after generated_at"):
        report(observation(retrieved_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="retrieval_success_count"):
        observation(
            retrieval_attempt_count=d("1"),
            retrieval_success_count=d("2"),
            primary_source_match_count=d("1"),
        )
    with pytest.raises(ValueError, match="primary_source_match_count"):
        observation(
            retrieval_success_count=d("1"),
            primary_source_match_count=d("2"),
        )
    with pytest.raises(ValueError, match="parsed_field_count"):
        observation(parsed_field_count=d("11"), expected_field_count=d("10"))
    with pytest.raises(ValueError, match="weights"):
        config(success_ratio_weight=d("0.300000"))
    with pytest.raises(ValueError, match="contradiction"):
        config(
            max_contradiction_count_pass=d("3"),
            max_contradiction_count_watch=d("2"),
        )

    payload = built.payload
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        _DictSubclass(payload),
    )
    row_list_subclass = json.loads(json.dumps(payload))
    row_list_subclass["rows"] = _ListSubclass(row_list_subclass["rows"])
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        row_list_subclass,
    )
    status_subclass = json.loads(json.dumps(payload))
    status_subclass["status"] = _StringSubclass(status_subclass["status"])
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        status_subclass,
    )

    for value in (
        config(),
        observation(),
        built,
        *built.reason_code_counts,
        *built.rows,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        assert_decimal_public_numbers(value)


def test_decimal_inputs_validate_raw_values_before_quantization() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        config(min_success_ratio_watch=d("-0.0000004"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        config(min_success_ratio_pass=d("1.0000004"))
    with pytest.raises(ValueError, match="whole number"):
        observation(retrieval_success_count=d("1.0000004"))


def test_decimal_math_is_isolated_from_a_hostile_ambient_context() -> None:
    baseline = report(
        observation(
            retrieval_success_count=d("7"),
            primary_source_match_count=d("5"),
            parsed_field_count=d("8"),
            contradiction_count=d("1"),
        ),
    )

    with localcontext() as ambient:
        ambient.prec = 1
        ambient.rounding = ROUND_DOWN
        ambient.traps[Inexact] = True
        ambient.traps[Rounded] = True
        hardened = report(
            observation(
                retrieval_success_count=d("7"),
                primary_source_match_count=d("5"),
                parsed_field_count=d("8"),
                contradiction_count=d("1"),
            ),
        )

    assert hardened.payload == baseline.payload


def test_signed_zero_is_canonicalized_in_models_and_rejected_in_payloads() -> None:
    module = api()

    zero_observation = observation(
        retrieval_success_count=d("-0"),
        primary_source_match_count=d("-0.000000"),
        parsed_field_count=d("-0"),
        contradiction_count=d("-0.000000"),
    )
    zero_config = config(max_contradiction_count_pass=d("-0"))
    zero_report = report(zero_observation, cfg=zero_config)

    assert zero_observation.retrieval_success_count == d("0.000000")
    assert zero_observation.primary_source_match_count == d("0.000000")
    assert zero_observation.parsed_field_count == d("0.000000")
    assert zero_observation.contradiction_count == d("0.000000")
    assert zero_config.max_contradiction_count_pass == d("0.000000")
    assert_decimal_public_numbers(zero_observation)
    assert_decimal_public_numbers(zero_config)
    assert_decimal_public_numbers(zero_report)

    payload = report(observation()).payload
    signed_zero = json.loads(json.dumps(payload))
    signed_zero["config"]["max_contradiction_count_pass"] = "-0.000000"
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        resign_payload(signed_zero),
    )

    for invalid_decimal in ("NaN", "sNaN", "Infinity", "-Infinity", "not-a-decimal"):
        forged = json.loads(json.dumps(payload))
        forged["rows"][0]["success_ratio"] = invalid_decimal
        assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
            resign_payload(forged),
        )

    oversized = json.loads(json.dumps(payload))
    oversized["rows"][0]["retrieval_attempt_count"] = "1E+1000000"
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        resign_payload(oversized),
    )


def test_private_retrieval_refs_stay_redacted_and_row_labels_are_canonical() -> None:
    module = api()
    private_ref = "https://private.example/source?token=do-not-leak"
    payload = report(observation(private_ref)).payload

    assert private_ref not in json.dumps(payload, sort_keys=True)
    assert payload["rows"][0]["row_label"] == (
        "redacted-scrapling-retrieval-000001"
    )

    forged = json.loads(json.dumps(payload))
    forged["rows"][0]["row_label"] = "redacted-scrapling-retrieval-000002"
    assert not module.validate_research_source_scrapling_retrieval_reliability_scorecard_report_payload(
        resign_payload(forged),
    )


def test_owned_module_has_no_network_execution_persistence_or_float_surfaces() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    banned_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "post",
        "put",
        "delete",
        "write",
    }
    banned_imports = {
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "subprocess",
        "urllib",
        "web3",
        "py_clob_client",
        "scrapling",
        "agent_reach",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        if isinstance(node, ast.Call):
            func = node.func
            name = ""
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            assert name.lower() not in banned_calls
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")

    assert imported_roots.isdisjoint(banned_imports)
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert "wallet" not in lowered
        assert "order" not in lowered
        assert "trading" not in lowered
        assert "recommendation" not in lowered
        assert "sizing" not in lowered
