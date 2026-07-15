from __future__ import annotations
from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json
from unittest.mock import Mock
import pytest
import polymarket_alpha_lab.team_evidence_aggregation_codec as codec_module
from polymarket_alpha_lab.team_evidence_aggregation_codec import (
    team_evidence_aggregation_config_digest,
    team_evidence_aggregation_config_payload,
    team_evidence_aggregation_core_digest,
    team_evidence_aggregation_core_payload,
    team_evidence_aggregation_input_payload,
    team_evidence_aggregation_payload,
    validate_team_evidence_aggregation_core_digest,
)
import polymarket_alpha_lab.team_evidence_aggregation_types as types
EXPECTED_CONFIG_DIGEST = (
    "1fda9ece725bedd42782ff9af1e0cbe7105a5a33036609066e023696a0acb675"
)
EXPECTED_CORE_DIGEST = (
    "d3c968df35caeb7e8ba1b411029e200117bee21f8c9ee14bda6954679cf1e6cb"
)
EXPECTED_CONFIG_BYTES = (
    b'{"config":{"config_version":"agg-test-v1","contradiction_block_score":"0.670000",'
    b'"contradiction_no_probability_max":"0.210000","contradiction_watch_score":"0.310000",'
    b'"contradiction_yes_probability_min":"0.790000","correlation_group_weight_cap":"0.610000",'
    b'"independence_group_weight_cap":"0.730000","max_capture_lag_seconds":"300.000000",'
    b'"max_evidence_age_seconds":"7200.000000","max_requirement_assignments_per_evidence":3,'
    b'"maximum_records":8,"maximum_requirement_memberships":16,"maximum_requirements":4,'
    b'"maximum_witness_edges":12,"paper_only":true,"publish_probability_ceiling":"0.890000",'
    b'"publish_probability_floor":"0.110000","readonly":true,"report_only":true,'
    b'"requirements":[{"minimum_effective_weight":"0.120000","minimum_witness_count":1,'
    b'"paper_only":true,"readonly":true,"report_only":true,"requirement_id":"macro.release",'
    b'"unmet_status":"blocked"}]},"schema_version":"pal.team_evidence_aggregation.config.v1"}'
)
EXPECTED_CORE_BYTES = (
    b'{"result":{"arithmetic_probability_yes":null,"arithmetic_record_count":0,'
    b'"config_digest":"1fda9ece725bedd42782ff9af1e0cbe7105a5a33036609066e023696a0acb675",'
    b'"config_version":"agg-test-v1","contradiction":{"contradiction_score":"0.000000",'
    b'"neutral_weight":"0.000000","no_support_weight":"0.000000","paper_only":true,'
    b'"readonly":true,"report_only":true,"status":"none","yes_support_weight":"0.000000"},'
    b'"diagnostic_record_count":0,"diagnostics":[],"effective_weight_total":"0.000000",'
    b'"evaluated_at":"2026-07-13T12:00:00.123456+00:00",'
    b'"independence_allocated_weight_total":"0.000000","paper_only":true,'
    b'"publishable_probability_yes":null,"readonly":true,'
    b'"reason_codes":["blocking_requirement_unmet","no_arithmetic_evidence"],'
    b'"report_only":true,"requested_weight_total":"0.000000","requirement_coverage":['
    b'{"assigned_witness_count":0,"minimum_effective_weight":"0.120000",'
    b'"minimum_witness_count":1,"paper_only":true,"readonly":true,"report_only":true,'
    b'"requirement_id":"macro.release","satisfied":false,"unmet_status":"blocked",'
    b'"witnesses":[]}],"status":"blocked"},'
    b'"schema_version":"pal.team_evidence_aggregation.core.v1"}'
)
EVALUATED = datetime(2026, 7, 13, 12, 0, 0, 123456, tzinfo=UTC)
ANCHOR = datetime(2026, 7, 13, 10, 30, tzinfo=UTC)
CAPTURED = datetime(2026, 7, 13, 10, 34, tzinfo=UTC)
RECORDED = datetime(2026, 7, 13, 10, 35, tzinfo=UTC)
ASSESSED = datetime(2026, 7, 13, 10, 36, tzinfo=UTC)
def d(value: str) -> Decimal:
    return Decimal(value)
def digest(character: str) -> str:
    return character * 64
def config(**changes: object) -> types.TeamEvidenceAggregationConfig:
    values: dict[str, object] = {
        "config_version": "agg-test-v1", "max_evidence_age_seconds": d("7200.000000"),
        "max_capture_lag_seconds": d("300.000000"),
        "independence_group_weight_cap": d("0.730000"),
        "correlation_group_weight_cap": d("0.610000"),
        "max_requirement_assignments_per_evidence": 3,
        "contradiction_no_probability_max": d("0.210000"),
        "contradiction_yes_probability_min": d("0.790000"),
        "contradiction_watch_score": d("0.310000"), "contradiction_block_score": d("0.670000"),
        "publish_probability_floor": d("0.110000"), "publish_probability_ceiling": d("0.890000"),
        "maximum_records": 8, "maximum_requirements": 4,
        "maximum_requirement_memberships": 16, "maximum_witness_edges": 12,
        "requirements": (
            types.TeamEvidenceRequirement(
                requirement_id="macro.release", minimum_witness_count=1,
                minimum_effective_weight=d("0.120000"), unmet_status="blocked",
            ),
        ),
    }
    values.update(changes)
    return types.TeamEvidenceAggregationConfig(**values)
def record(
    prefix: str = "alpha",
    *,
    requirement_ids: tuple[str, ...] = ("macro.release",),
) -> types.TeamEvidenceAggregationRecord:
    characters = {"alpha": "abcdef", "beta": "123456"}[prefix]
    offset = timedelta(minutes=prefix == "beta")
    lineage = types.TeamEvidenceSourceLineage(
        source_lineage_id=f"lineage.{prefix}", source_lineage_digest=digest(characters[0]),
    )
    capture = types.TeamEvidenceCapture(
        capture_id=f"capture.{prefix}.1", capture_digest=digest(characters[1]),
        source_lineage_id=lineage.source_lineage_id,
        source_lineage_digest=lineage.source_lineage_digest,
        content_digest=digest(characters[2]), captured_at=CAPTURED + offset,
    )
    evidence = types.TeamEvidenceRevision(
        evidence_revision_id=f"evidence.{prefix}.1",
        evidence_revision_digest=digest(characters[3]),
        previous_evidence_revision_id=None, previous_evidence_revision_digest=None,
        source_lineage_id=lineage.source_lineage_id,
        source_lineage_digest=lineage.source_lineage_digest,
        content_digest=capture.content_digest, requirement_ids=requirement_ids,
        freshness_anchor_at=ANCHOR + offset, recorded_at=RECORDED + offset,
    )
    assessment = types.TeamEvidenceAssessmentRevision(
        assessment_revision_id=f"assessment.{prefix}.1",
        assessment_revision_digest=digest(characters[4]),
        previous_assessment_revision_id=None, previous_assessment_revision_digest=None,
        evidence_revision_id=evidence.evidence_revision_id,
        evidence_revision_digest=evidence.evidence_revision_digest,
        assessed_at=ASSESSED + offset,
        probability_yes=d("0.640000" if prefix == "alpha" else "0.360000"),
        requested_weight=d("0.400000"), rationale_digest=digest(characters[5]),
        independence_key=f"desk.{prefix}", correlation_key="macro.shared",
    )
    return types.TeamEvidenceAggregationRecord(
        source_lineage=lineage, capture=capture,
        evidence_revision=evidence, assessment_revision=assessment,
    )
def selection(
    item: types.TeamEvidenceAggregationRecord,
) -> types.TeamEvidenceCurrentRevisionSelection:
    return types.TeamEvidenceCurrentRevisionSelection(
        evidence_revision_id=item.evidence_revision.evidence_revision_id,
        evidence_revision_digest=item.evidence_revision.evidence_revision_digest,
        assessment_revision_id=item.assessment_revision.assessment_revision_id,
        assessment_revision_digest=item.assessment_revision.assessment_revision_digest,
    )
def aggregation_input() -> types.TeamEvidenceAggregationInput:
    item = record()
    return types.TeamEvidenceAggregationInput(
        evaluated_at=EVALUATED, records=(item,), current_revisions=(selection(item),),
    )
def minimal_result(**changes: object) -> types.TeamEvidenceAggregationResult:
    values: dict[str, object] = {
        "evaluated_at": EVALUATED, "config_version": "agg-test-v1",
        "config_digest": EXPECTED_CONFIG_DIGEST, "status": "blocked",
        "diagnostic_record_count": 0, "arithmetic_record_count": 0,
        "requested_weight_total": d("0.000000"),
        "independence_allocated_weight_total": d("0.000000"),
        "effective_weight_total": d("0.000000"),
        "arithmetic_probability_yes": None, "publishable_probability_yes": None,
        "contradiction": types.TeamEvidenceContradictionResult(
            yes_support_weight=d("0.000000"), no_support_weight=d("0.000000"),
            neutral_weight=d("0.000000"), contradiction_score=d("0.000000"), status="none",
        ),
        "requirement_coverage": (
            types.TeamEvidenceRequirementCoverage(
                requirement_id="macro.release", minimum_witness_count=1, assigned_witness_count=0,
                minimum_effective_weight=d("0.120000"),
                unmet_status="blocked", satisfied=False, witnesses=(),
            ),
        ),
        "diagnostics": (), "reason_codes": ("blocking_requirement_unmet", "no_arithmetic_evidence"),
        "core_digest": "0" * 64,
    }
    values.update(changes)
    return types.TeamEvidenceAggregationResult(**values)
def diagnostic(prefix: str) -> types.TeamEvidenceDiagnosticRow:
    item = record(prefix, requirement_ids=("policy.signal", "macro.release"))
    return types.TeamEvidenceDiagnosticRow(
        source_lineage_id=item.source_lineage.source_lineage_id, capture_id=item.capture.capture_id,
        captured_at=item.capture.captured_at,
        evidence_revision_id=item.evidence_revision.evidence_revision_id,
        assessment_revision_id=item.assessment_revision.assessment_revision_id,
        probability_yes=item.assessment_revision.probability_yes, requested_weight=d("0.400000"),
        independence_allocated_weight=d("0.300000"),
        effective_weight=d("0.200000"), evidence_age_seconds=d("5400.000000"),
        capture_lag_seconds=d("240.000000"), captured_at_evaluation=True,
        evidence_revision_available_at_evaluation=True,
        assessment_revision_available_at_evaluation=True,
        selected_current_revision=True, canonical_capture=True, disposition="included",
    )
def permutation_fixture(
    reverse: bool,
) -> tuple[
    types.TeamEvidenceAggregationConfig,
    types.TeamEvidenceAggregationInput,
    types.TeamEvidenceAggregationResult,
]:
    requirements = (
        types.TeamEvidenceRequirement(
            requirement_id="macro.release", minimum_witness_count=1,
            minimum_effective_weight=d("0.120000"), unmet_status="blocked",
        ),
        types.TeamEvidenceRequirement(
            requirement_id="policy.signal", minimum_witness_count=1,
            minimum_effective_weight=d("0.100000"), unmet_status="watch",
        ),
    )
    requirement_ids = tuple(item.requirement_id for item in requirements)
    alpha = record("alpha", requirement_ids=requirement_ids[::-1] if reverse else requirement_ids)
    beta = record("beta", requirement_ids=requirement_ids[::-1] if reverse else requirement_ids)
    records = (alpha, beta)
    selections = tuple(selection(item) for item in records)
    witnesses = tuple(
        types.TeamEvidenceRequirementWitness(
            requirement_id="macro.release",
            source_lineage_id=item.source_lineage.source_lineage_id,
            capture_id=item.capture.capture_id,
            evidence_revision_id=item.evidence_revision.evidence_revision_id,
            assessment_revision_id=item.assessment_revision.assessment_revision_id,
            independence_key=item.assessment_revision.independence_key,
            effective_weight=d("0.200000"),
        )
        for item in records
    )
    coverage = (
        types.TeamEvidenceRequirementCoverage(
            requirement_id="macro.release", minimum_witness_count=1, assigned_witness_count=2,
            minimum_effective_weight=d("0.120000"),
            unmet_status="blocked", satisfied=True,
            witnesses=witnesses[::-1] if reverse else witnesses,
        ),
        types.TeamEvidenceRequirementCoverage(
            requirement_id="policy.signal", minimum_witness_count=1, assigned_witness_count=0,
            minimum_effective_weight=d("0.100000"),
            unmet_status="watch", satisfied=False, witnesses=(),
        ),
    )
    diagnostics = tuple(diagnostic(prefix) for prefix in ("alpha", "beta"))
    ordered = (lambda values: values[::-1] if reverse else values)
    result = types.TeamEvidenceAggregationResult(
        evaluated_at=EVALUATED, config_version="agg-test-v1",
        config_digest=EXPECTED_CONFIG_DIGEST, status="watch",
        diagnostic_record_count=2, arithmetic_record_count=2,
        requested_weight_total=d("0.800000"),
        independence_allocated_weight_total=d("0.600000"),
        effective_weight_total=d("0.400000"),
        arithmetic_probability_yes=d("0.500000"), publishable_probability_yes=d("0.500000"),
        contradiction=types.TeamEvidenceContradictionResult(
            yes_support_weight=d("0.200000"), no_support_weight=d("0.200000"),
            neutral_weight=d("0.000000"), contradiction_score=d("0.300000"), status="watch",
        ),
        requirement_coverage=ordered(coverage), diagnostics=ordered(diagnostics),
        reason_codes=ordered(("contradiction.watch", "coverage.watch")),
        core_digest="0" * 64,
    )
    aggregation = types.TeamEvidenceAggregationInput(
        evaluated_at=EVALUATED, records=ordered(records), current_revisions=ordered(selections),
    )
    return config(requirements=ordered(requirements)), aggregation, result
def canonical_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
def valid_result(
    result: types.TeamEvidenceAggregationResult | None = None,
) -> types.TeamEvidenceAggregationResult:
    provisional = minimal_result() if result is None else result
    return replace(provisional, core_digest=team_evidence_aggregation_core_digest(provisional))
def bypassed(instance: object, field_name: str, value: object) -> object:
    clone = object.__new__(type(instance))
    for field in fields(type(instance)):
        object.__setattr__(
            clone,
            field.name,
            value if field.name == field_name else getattr(instance, field.name),
        )
    return clone
def direct_keys(instance: object) -> set[str]:
    return {field.name for field in fields(type(instance))}
def assert_json_ready_tree(value: object) -> None:
    if type(value) is dict:
        assert all(type(key) is str for key in value)
        for child in value.values():
            assert_json_ready_tree(child)
        return
    if type(value) is list:
        for child in value:
            assert_json_ready_tree(child)
        return
    assert type(value) in {str, int, bool, type(None)}
def test_config_payload_has_exact_closed_envelope_and_direct_field_maps() -> None:
    source = config()
    payload = team_evidence_aggregation_config_payload(source)
    assert set(payload) == {"schema_version", "config"}
    assert payload["schema_version"] == "pal.team_evidence_aggregation.config.v1"
    assert set(payload["config"]) == direct_keys(source)
    assert set(payload["config"]["requirements"][0]) == direct_keys(source.requirements[0])
    for mapping in (payload["config"], payload["config"]["requirements"][0]):
        assert mapping["paper_only"] is True
        assert mapping["report_only"] is True
        assert mapping["readonly"] is True
def test_input_payload_has_exact_closed_envelope_and_every_nested_direct_map() -> None:
    source = aggregation_input()
    payload = team_evidence_aggregation_input_payload(source)
    input_map = payload["input"]
    record_map = input_map["records"][0]
    item = source.records[0]
    assert set(payload) == {"schema_version", "input"}
    assert payload["schema_version"] == "pal.team_evidence_aggregation.input.v1"
    assert set(input_map) == direct_keys(source)
    assert set(record_map) == direct_keys(item)
    for name in ("source_lineage", "capture", "evidence_revision", "assessment_revision"):
        assert set(record_map[name]) == direct_keys(getattr(item, name))
    assert set(input_map["current_revisions"][0]) == direct_keys(source.current_revisions[0])
    assert not ({"type", "class", "schema_version", "extensions"} & set(record_map))
def test_core_and_full_result_payloads_have_exact_distinct_envelopes() -> None:
    source = valid_result()
    core = team_evidence_aggregation_core_payload(source)
    full = team_evidence_aggregation_payload(source)
    result_fields = direct_keys(source)
    assert set(core) == {"schema_version", "result"}
    assert set(full) == {"schema_version", "result"}
    assert core["schema_version"] == "pal.team_evidence_aggregation.core.v1"
    assert full["schema_version"] == "pal.team_evidence_aggregation.result.v1"
    assert set(core["result"]) == result_fields - {"core_digest"}
    assert set(full["result"]) == result_fields
    assert full["result"]["core_digest"] == EXPECTED_CORE_DIGEST
    assert core["result"] is not full["result"]
def test_codec_renders_fixed_six_decimal_microsecond_utc_arrays_ints_bools_and_null() -> None:
    config_map = team_evidence_aggregation_config_payload(config())["config"]
    input_map = team_evidence_aggregation_input_payload(aggregation_input())["input"]
    result_map = team_evidence_aggregation_core_payload(minimal_result())["result"]
    assert config_map["max_evidence_age_seconds"] == "7200.000000"
    assert config_map["requirements"][0]["minimum_effective_weight"] == "0.120000"
    assert result_map["requested_weight_total"] == "0.000000"
    assert not result_map["requested_weight_total"].startswith("-")
    assert "e" not in config_map["independence_group_weight_cap"].lower()
    assert input_map["evaluated_at"] == "2026-07-13T12:00:00.123456+00:00"
    assert type(config_map["requirements"]) is list
    assert type(input_map["records"]) is list
    assert type(config_map["maximum_records"]) is int
    assert type(config_map["maximum_records"]) is not bool
    assert config_map["paper_only"] is True
    assert input_map["records"][0]["evidence_revision"]["previous_evidence_revision_id"] is None
    assert result_map["arithmetic_probability_yes"] is None
def test_payload_trees_contain_no_float_or_non_json_ready_value() -> None:
    result = valid_result()
    payloads = (
        team_evidence_aggregation_config_payload(config()),
        team_evidence_aggregation_input_payload(aggregation_input()),
        team_evidence_aggregation_core_payload(result),
        team_evidence_aggregation_payload(result),
    )
    for payload in payloads:
        assert_json_ready_tree(payload)
def test_semantic_tuple_permutations_produce_equal_payloads_and_bytes() -> None:
    forward_config, forward_input, forward_result = permutation_fixture(False)
    reverse_config, reverse_input, reverse_result = permutation_fixture(True)
    assert forward_config == reverse_config
    assert forward_input == reverse_input
    assert forward_result == reverse_result
    pairs = (
        (
            team_evidence_aggregation_config_payload(forward_config),
            team_evidence_aggregation_config_payload(reverse_config),
        ),
        (
            team_evidence_aggregation_input_payload(forward_input),
            team_evidence_aggregation_input_payload(reverse_input),
        ),
        (
            team_evidence_aggregation_core_payload(forward_result),
            team_evidence_aggregation_core_payload(reverse_result),
        ),
        (
            team_evidence_aggregation_payload(valid_result(forward_result)),
            team_evidence_aggregation_payload(valid_result(reverse_result)),
        ),
    )
    for left, right in pairs:
        assert left == right
        assert canonical_bytes(left) == canonical_bytes(right)
def test_config_digest_matches_literal_domain_separated_vector() -> None:
    payload = team_evidence_aggregation_config_payload(config())
    assert canonical_bytes(payload) == EXPECTED_CONFIG_BYTES
    assert team_evidence_aggregation_config_digest(config()) == EXPECTED_CONFIG_DIGEST
def test_core_digest_matches_literal_domain_separated_vector() -> None:
    source = minimal_result()
    payload = team_evidence_aggregation_core_payload(source)
    assert canonical_bytes(payload) == EXPECTED_CORE_BYTES
    assert team_evidence_aggregation_core_digest(source) == EXPECTED_CORE_DIGEST
def test_payload_calls_return_fresh_mutation_isolated_dictionaries() -> None:
    source_config, source_input, provisional = permutation_fixture(False)
    source_result = valid_result(provisional)
    expected_config = team_evidence_aggregation_config_payload(source_config)
    mutated_config = team_evidence_aggregation_config_payload(source_config)
    mutated_config["schema_version"] = "changed"
    mutated_config["config"]["requirements"][0]["requirement_id"] = "changed"
    mutated_config["config"]["requirements"].append({})
    assert team_evidence_aggregation_config_payload(source_config) == expected_config
    expected_input = team_evidence_aggregation_input_payload(source_input)
    mutated_input = team_evidence_aggregation_input_payload(source_input)
    mutated_input["input"]["records"][0]["source_lineage"]["source_lineage_id"] = "changed"
    mutated_input["input"]["records"][0]["evidence_revision"]["requirement_ids"].append("changed")
    mutated_input["input"]["current_revisions"][0]["assessment_revision_id"] = "changed"
    mutated_input["input"]["records"].append({})
    assert team_evidence_aggregation_input_payload(source_input) == expected_input
    core = team_evidence_aggregation_core_payload(source_result)
    core_snapshot = canonical_bytes(core)
    full = team_evidence_aggregation_payload(source_result)
    full["result"]["contradiction"]["status"] = "changed"
    full["result"]["requirement_coverage"][0]["witnesses"][0]["capture_id"] = "changed"
    full["result"]["diagnostics"][0]["disposition"] = "changed"
    full["result"]["reason_codes"].append("changed")
    assert canonical_bytes(core) == core_snapshot
    assert "core_digest" not in core["result"]
    assert team_evidence_aggregation_payload(source_result) != full
    assert source_config.requirements[0].requirement_id == "macro.release"
    assert source_input.records[0].source_lineage.source_lineage_id == "lineage.alpha"
    assert source_result.contradiction.status == "watch"
def test_public_codec_functions_reject_wrong_exact_dataclass_types() -> None:
    class MappingSubclass(dict[str, object]):
        pass
    with pytest.raises(TypeError):
        type("ConfigSubclass", (types.TeamEvidenceAggregationConfig,), {})
    requirement = config().requirements[0]
    cases = (
        (team_evidence_aggregation_config_payload, types.TeamEvidenceAggregationConfig),
        (team_evidence_aggregation_config_digest, types.TeamEvidenceAggregationConfig),
        (team_evidence_aggregation_input_payload, types.TeamEvidenceAggregationInput),
        (team_evidence_aggregation_core_payload, types.TeamEvidenceAggregationResult),
        (team_evidence_aggregation_payload, types.TeamEvidenceAggregationResult),
        (team_evidence_aggregation_core_digest, types.TeamEvidenceAggregationResult),
        (validate_team_evidence_aggregation_core_digest, types.TeamEvidenceAggregationResult),
    )
    for function, expected_type in cases:
        for wrong in (Mock(spec=expected_type), requirement, MappingSubclass()):
            with pytest.raises(ValueError):
                function(wrong)
def test_codec_rejects_constructor_bypassed_noncanonical_values() -> None:
    source_config = config()
    bad_configs = (
        bypassed(source_config, "max_evidence_age_seconds", 7200.0),
        bypassed(source_config, "independence_group_weight_cap", d("0.73")),
        bypassed(source_config, "max_capture_lag_seconds", d("-0.000000")),
        bypassed(source_config, "requirements", (object(),)),
        bypassed(source_config, "paper_only", False),
        bypassed(source_config, "contradiction_watch_score", d("NaN")),
        bypassed(source_config, "contradiction_block_score", d("Infinity")),
    )
    for malformed in bad_configs:
        for function in (
            team_evidence_aggregation_config_payload,
            team_evidence_aggregation_config_digest,
        ):
            with pytest.raises(ValueError):
                function(malformed)
    source_input = aggregation_input()
    bad_inputs = (
        bypassed(source_input, "evaluated_at", EVALUATED.replace(tzinfo=None)),
        bypassed(
            source_input,
            "evaluated_at",
            EVALUATED.astimezone(timezone(timedelta(hours=1))),
        ),
        bypassed(source_input, "records", list(source_input.records)),
        bypassed(source_input, "readonly", False),
    )
    for malformed in bad_inputs:
        with pytest.raises(ValueError):
            team_evidence_aggregation_input_payload(malformed)
    source_result = valid_result()
    bad_results = (
        bypassed(source_result, "requested_weight_total", 0.0),
        bypassed(source_result, "requested_weight_total", d("0")),
        bypassed(source_result, "effective_weight_total", d("-0.000000")),
        bypassed(source_result, "evaluated_at", EVALUATED.replace(tzinfo=None)),
        bypassed(source_result, "reason_codes", list(source_result.reason_codes)),
        bypassed(source_result, "report_only", False),
        bypassed(source_result, "contradiction", object()),
    )
    for malformed in bad_results:
        for function in (
            team_evidence_aggregation_core_payload,
            team_evidence_aggregation_payload,
            team_evidence_aggregation_core_digest,
            validate_team_evidence_aggregation_core_digest,
        ):
            with pytest.raises(ValueError):
                function(malformed)
def test_core_payload_covers_every_result_field_except_only_core_digest() -> None:
    source = minimal_result()
    included = {field.name for field in fields(types.TeamEvidenceAggregationResult)} - {
        "core_digest"
    }
    assert set(team_evidence_aggregation_core_payload(source)["result"]) == included
    alternatives: dict[str, object] = {
        "evaluated_at": source.evaluated_at + timedelta(seconds=1),
        "config_version": "agg-test-v2",
        "config_digest": digest("a"),
        "status": "watch",
        "diagnostic_record_count": object(),
        "arithmetic_record_count": object(),
        "requested_weight_total": d("0.100000"),
        "independence_allocated_weight_total": object(),
        "effective_weight_total": object(),
        "arithmetic_probability_yes": d("0.500000"),
        "publishable_probability_yes": d("0.500000"),
        "contradiction": replace(
            source.contradiction,
            contradiction_score=d("0.100000"),
            status="watch",
        ),
        "requirement_coverage": (),
        "diagnostics": (diagnostic("alpha"),),
        "reason_codes": ("different.reason",),
        "paper_only": False,
        "report_only": False,
        "readonly": False,
    }
    assert set(alternatives) == included
    baseline = team_evidence_aggregation_core_digest(source)
    for field_name, alternative in alternatives.items():
        changed = bypassed(source, field_name, alternative)
        try:
            changed_digest = team_evidence_aggregation_core_digest(changed)
        except ValueError:
            continue
        assert changed_digest != baseline, field_name
def test_validate_core_digest_returns_exact_none_and_rejects_tampering() -> None:
    source = valid_result()
    assert validate_team_evidence_aggregation_core_digest(source) is None
    for malformed in (
        replace(source, core_digest="f" * 64),
        bypassed(source, "core_digest", source.core_digest.upper()),
        bypassed(source, "core_digest", source.core_digest[:-1]),
        bypassed(source, "status", "watch"),
    ):
        with pytest.raises(ValueError):
            validate_team_evidence_aggregation_core_digest(malformed)
def test_full_payload_fails_closed_before_emitting_invalid_core_digest() -> None:
    invalid = replace(valid_result(), core_digest="f" * 64)
    core = team_evidence_aggregation_core_payload(invalid)
    snapshot = canonical_bytes(core)
    with pytest.raises(ValueError):
        emitted = team_evidence_aggregation_payload(invalid)
    assert "emitted" not in locals()
    assert canonical_bytes(core) == snapshot
    assert "core_digest" not in core["result"]
def test_codec_has_no_decoder_legacy_projection_or_node3_identity() -> None:
    expected_all = (
        "team_evidence_aggregation_config_payload",
        "team_evidence_aggregation_input_payload",
        "team_evidence_aggregation_config_digest",
        "team_evidence_aggregation_core_payload",
        "team_evidence_aggregation_payload",
        "team_evidence_aggregation_core_digest",
        "validate_team_evidence_aggregation_core_digest",
    )
    assert codec_module.__all__ == expected_all
    assert {name for name in vars(codec_module) if not name.startswith("_")} == set(
        expected_all
    )
    source_result = valid_result()
    payloads = (
        team_evidence_aggregation_config_payload(config()),
        team_evidence_aggregation_input_payload(aggregation_input()),
        team_evidence_aggregation_core_payload(source_result),
        team_evidence_aggregation_payload(source_result),
    )
    forbidden_keys = {
        "run_id",
        "forecast_id",
        "evidence_id",
        "receipt",
        "receipts",
        "legacy",
        "legacy_projection",
        "team_evidence_aggregation_id",
        "team_forecast_result_id",
        "team_forecast_evidence_id",
    }
    def assert_no_forbidden_identity(value: object) -> None:
        if type(value) is dict:
            assert forbidden_keys.isdisjoint(value)
            for key, child in value.items():
                if key == "schema_version":
                    assert child not in {"tea:v1", "tfr:v1", "tfe:v1"}
                assert_no_forbidden_identity(child)
        elif type(value) is list:
            for child in value:
                assert_no_forbidden_identity(child)
    for payload in payloads:
        assert_no_forbidden_identity(payload)
