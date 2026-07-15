from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_DOWN, localcontext
import inspect
import json

import pytest

import polymarket_alpha_lab.research_strategy_team_source_consensus_memory_report as api
from polymarket_alpha_lab.research_strategy_team_source_consensus_memory_report import (
    ResearchStrategyTeamSourceConsensusMemoryConfig,
    ResearchStrategyTeamSourceConsensusMemoryObservation,
    ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem,
    ResearchStrategyTeamSourceConsensusMemoryReport,
    ResearchStrategyTeamSourceConsensusMemoryRow,
    build_research_strategy_team_source_consensus_memory_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _observation(
    *,
    team_id: str = "team_alpha",
    memory_key: str = "memory_a",
    family_id: str = "family_a",
    confidence_score: Decimal = Decimal("0.700000"),
    supports_consensus: bool = True,
    observed_at: datetime = NOW,
) -> ResearchStrategyTeamSourceConsensusMemoryObservation:
    return ResearchStrategyTeamSourceConsensusMemoryObservation(
        team_id=team_id,
        memory_key=memory_key,
        family_id=family_id,
        confidence_score=confidence_score,
        supports_consensus=supports_consensus,
        observed_at=observed_at,
    )


def _report(
    observations: tuple[ResearchStrategyTeamSourceConsensusMemoryObservation, ...],
    *,
    config: ResearchStrategyTeamSourceConsensusMemoryConfig | None = None,
    public_payload: tuple[ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem, ...] = (),
) -> ResearchStrategyTeamSourceConsensusMemoryReport:
    return build_research_strategy_team_source_consensus_memory_report(
        observations,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def _direct_row(
    **overrides: object,
) -> ResearchStrategyTeamSourceConsensusMemoryRow:
    values: dict[str, object] = {
        "team_id": "team_alpha",
        "memory_key": "memory_a",
        "observation_count": Decimal("1.000000"),
        "supporting_observation_count": Decimal("1.000000"),
        "family_count": Decimal("1.000000"),
        "supporting_family_count": Decimal("1.000000"),
        "conflicting_observation_count": Decimal("0.000000"),
        "average_confidence_score": Decimal("0.700000"),
        "consensus_score": Decimal("0.700000"),
        "memory_state": "watch",
        "reason_codes": ("insufficient_supporting_family_consensus",),
    }
    values.update(overrides)
    return ResearchStrategyTeamSourceConsensusMemoryRow(**values)  # type: ignore[arg-type]


def _resign_payload(payload: dict[str, object]) -> dict[str, object]:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    resigned = dict(payload)
    resigned["derived_validation_digest"] = api._report_digest_from_values(unsigned)
    ordered: dict[str, object] = {}
    for field_name in api._REPORT_PAYLOAD_FIELDS:
        if field_name in resigned:
            ordered[field_name] = resigned[field_name]
    for field_name, value in resigned.items():
        if field_name not in ordered:
            ordered[field_name] = value
    return ordered


def test_source_consensus_memory_report_builds_pass_watch_and_block_states() -> None:
    report = _report(
        (
            _observation(team_id="team_beta", memory_key="memory_block", supports_consensus=False),
            _observation(family_id="family_b", confidence_score=Decimal("0.800000")),
            _observation(team_id="team_alpha", memory_key="memory_watch"),
            _observation(family_id="family_a", confidence_score=Decimal("0.700000")),
        ),
    )

    assert report.memory_state == "block"
    assert report.row_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.rows[0].memory_key == "memory_a"
    assert report.rows[0].memory_state == "pass"
    assert report.rows[0].supporting_family_count == Decimal("2.000000")
    assert report.rows[1].memory_key == "memory_watch"
    assert report.rows[1].memory_state == "watch"
    assert report.rows[2].memory_key == "memory_block"
    assert report.rows[2].memory_state == "block"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_public_payload_is_deterministic_json_ready_and_digest_validated() -> None:
    observations = (
        _observation(family_id="family_b", confidence_score=Decimal("0.800000")),
        _observation(family_id="family_a", confidence_score=Decimal("0.700000")),
    )
    first = _report(
        observations,
        public_payload=(
            ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem("summary", "safe value"),
            ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem("version", "v1"),
        ),
    )
    second = _report(
        tuple(reversed(observations)),
        public_payload=(
            ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem("version", "v1"),
            ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem("summary", "safe value"),
        ),
    )

    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    json.dumps(first.payload, sort_keys=True)
    assert first.payload["row_count"] == "1.000000"
    assert first.payload["rows"][0]["supporting_family_count"] == "2.000000"
    assert first.payload["rows"][0]["consensus_score"] == "0.850000"
    assert first.payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert first.payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    _assert_no_decimal_objects(first.payload)
    _assert_no_non_decimal_public_numbers(first)


def test_decimal_math_is_isolated_from_the_ambient_context() -> None:
    observations = (
        _observation(
            family_id="family_a",
            confidence_score=Decimal("0.333333"),
        ),
        _observation(
            family_id="family_b",
            confidence_score=Decimal("0.666667"),
        ),
    )
    expected = _report(observations).payload

    with localcontext(Context(prec=4, rounding=ROUND_DOWN)) as ambient:
        actual = _report(tuple(reversed(observations))).payload
        assert ambient.prec == 4
        assert ambient.rounding == ROUND_DOWN

    assert actual == expected
    assert actual["rows"][0]["average_confidence_score"] == "0.500000"
    assert actual["rows"][0]["consensus_score"] == "0.600000"


def test_observation_normalization_uses_a_complete_stable_sort_key() -> None:
    high_support = _observation(
        family_id="family_a",
        confidence_score=Decimal("0.600000"),
        supports_consensus=True,
    )
    low_support = _observation(
        family_id="family_a",
        confidence_score=Decimal("0.400000"),
        supports_consensus=True,
    )
    low_conflict = _observation(
        family_id="family_a",
        confidence_score=Decimal("0.400000"),
        supports_consensus=False,
    )
    expected = (low_conflict, low_support, high_support)

    assert api._normalize_observations(
        (high_support, low_support, low_conflict),
    ) == expected
    assert api._normalize_observations(
        (low_conflict, low_support, high_support),
    ) == expected


def test_public_dataclass_and_payload_schemas_are_exact_and_frozen() -> None:
    config = ResearchStrategyTeamSourceConsensusMemoryConfig()
    observation = _observation()
    public_item = ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem(
        "summary",
        "safe value",
    )
    row = _direct_row()
    report = _report(
        (
            _observation(family_id="family_a"),
            _observation(family_id="family_b"),
        ),
        public_payload=(public_item,),
    )
    expected_fields = {
        ResearchStrategyTeamSourceConsensusMemoryConfig: (
            "config_version",
            "min_supporting_family_count",
            "min_consensus_score",
            "conflict_penalty_per_observation",
            "independent_family_boost_per_family",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchStrategyTeamSourceConsensusMemoryObservation: (
            "team_id",
            "memory_key",
            "family_id",
            "confidence_score",
            "supports_consensus",
            "observed_at",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem: (
            "key",
            "value",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchStrategyTeamSourceConsensusMemoryRow: (
            "team_id",
            "memory_key",
            "observation_count",
            "supporting_observation_count",
            "family_count",
            "supporting_family_count",
            "conflicting_observation_count",
            "average_confidence_score",
            "consensus_score",
            "memory_state",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchStrategyTeamSourceConsensusMemoryReport: (
            "generated_at",
            "config_version",
            "config",
            "memory_state",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_consensus_score",
            "rows",
            "reason_codes",
            "public_payload",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }
    instances = {
        ResearchStrategyTeamSourceConsensusMemoryConfig: config,
        ResearchStrategyTeamSourceConsensusMemoryObservation: observation,
        ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem: public_item,
        ResearchStrategyTeamSourceConsensusMemoryRow: row,
        ResearchStrategyTeamSourceConsensusMemoryReport: report,
    }

    for cls, expected in expected_fields.items():
        assert tuple(field.name for field in fields(cls)) == expected
        assert cls.__dataclass_params__.frozen is True
        with pytest.raises(FrozenInstanceError):
            setattr(instances[cls], expected[0], getattr(instances[cls], expected[0]))
        with pytest.raises(TypeError):
            type(f"Bad{cls.__name__}", (cls,), {})

    payload = report.payload
    assert frozenset(payload) == frozenset(expected_fields[ResearchStrategyTeamSourceConsensusMemoryReport])
    assert frozenset(payload["config"]) == frozenset(
        expected_fields[ResearchStrategyTeamSourceConsensusMemoryConfig],
    )
    assert frozenset(payload["rows"][0]) == frozenset(
        expected_fields[ResearchStrategyTeamSourceConsensusMemoryRow],
    )
    assert frozenset(payload["public_payload"][0]) == frozenset(
        expected_fields[ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem],
    )


def test_public_dataclasses_are_final_slotted_and_have_no_instance_dict() -> None:
    instances = (
        ResearchStrategyTeamSourceConsensusMemoryConfig(),
        _observation(),
        ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem(
            "summary",
            "safe value",
        ),
        _direct_row(),
        _report(
            (
                _observation(family_id="family_a"),
                _observation(family_id="family_b"),
            ),
        ),
    )

    for value in instances:
        assert getattr(type(value), "__final__", False) is True
        assert hasattr(type(value), "__slots__")
        assert not hasattr(value, "__dict__")


def test_public_validator_rejects_resigned_schema_type_and_phase_flag_forgery() -> None:
    payload = _report(
        (
            _observation(family_id="family_a"),
            _observation(family_id="family_b"),
        ),
        public_payload=(
            ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem(
                "summary",
                "safe value",
            ),
        ),
    ).payload

    assert (
        api.validate_research_strategy_team_source_consensus_memory_report_payload(
            payload,
        )
        is True
    )

    forged_payloads: list[tuple[dict[str, object], str]] = []

    extra_report_field = json.loads(json.dumps(payload))
    extra_report_field["diagnostic"] = "safe"
    forged_payloads.append((_resign_payload(extra_report_field), "report payload.*exact schema"))

    missing_report_field = json.loads(json.dumps(payload))
    missing_report_field.pop("row_count")
    forged_payloads.append((_resign_payload(missing_report_field), "report payload.*exact schema"))

    extra_config_field = json.loads(json.dumps(payload))
    extra_config_field["config"]["diagnostic"] = "safe"
    forged_payloads.append((_resign_payload(extra_config_field), "config payload.*exact schema"))

    extra_row_field = json.loads(json.dumps(payload))
    extra_row_field["rows"][0]["diagnostic"] = "safe"
    forged_payloads.append((_resign_payload(extra_row_field), "row payload.*exact schema"))

    extra_public_item_field = json.loads(json.dumps(payload))
    extra_public_item_field["public_payload"][0]["diagnostic"] = "safe"
    forged_payloads.append(
        (_resign_payload(extra_public_item_field), "public payload item.*exact schema"),
    )

    noncanonical_decimal = json.loads(json.dumps(payload))
    noncanonical_decimal["row_count"] = "1"
    forged_payloads.append((_resign_payload(noncanonical_decimal), "row_count.*canonical Decimal"))

    noncanonical_datetime = json.loads(json.dumps(payload))
    noncanonical_datetime["generated_at"] = "2025-12-31T19:00:00-05:00"
    forged_payloads.append(
        (_resign_payload(noncanonical_datetime), "generated_at.*canonical UTC"),
    )

    false_report_flag = json.loads(json.dumps(payload))
    false_report_flag["readonly"] = False
    forged_payloads.append((_resign_payload(false_report_flag), "readonly.*True"))

    false_row_flag = json.loads(json.dumps(payload))
    false_row_flag["rows"][0]["report_only"] = False
    forged_payloads.append((_resign_payload(false_row_flag), "report_only.*True"))

    false_public_item_flag = json.loads(json.dumps(payload))
    false_public_item_flag["public_payload"][0]["paper_only"] = False
    forged_payloads.append((_resign_payload(false_public_item_flag), "paper_only.*True"))

    signed_zero_count = json.loads(json.dumps(payload))
    signed_zero_count["watch_count"] = "-0.000000"
    forged_payloads.append((_resign_payload(signed_zero_count), "watch_count.*signed zero"))

    for forged, error_match in forged_payloads:
        with pytest.raises(ValueError, match=error_match):
            api.validate_research_strategy_team_source_consensus_memory_report_payload(
                forged,
            )


def test_public_validator_rejects_resigned_derived_status_reason_count_and_score() -> None:
    payload = _report(
        (
            _observation(family_id="family_a", confidence_score=Decimal("0.700000")),
            _observation(family_id="family_b", confidence_score=Decimal("0.800000")),
        ),
    ).payload

    forged_score = json.loads(json.dumps(payload))
    forged_score["rows"][0]["consensus_score"] = "0.500000"
    forged_score["average_consensus_score"] = "0.500000"

    forged_policy = json.loads(json.dumps(payload))
    forged_policy["rows"][0]["memory_state"] = "watch"
    forged_policy["rows"][0]["reason_codes"] = [
        "independent_family_consensus_boost",
    ]
    forged_policy["memory_state"] = "watch"
    forged_policy["pass_count"] = "0.000000"
    forged_policy["watch_count"] = "1.000000"
    forged_policy["reason_codes"] = [
        "independent_family_consensus_boost",
    ]

    forged_family_count = json.loads(json.dumps(payload))
    forged_family_count["rows"][0]["family_count"] = "1.000000"

    forged_report_count = json.loads(json.dumps(payload))
    forged_report_count["row_count"] = "2.000000"

    forged_all_derived_fields = json.loads(json.dumps(payload))
    forged_all_derived_fields["rows"][0]["consensus_score"] = "0.700000"
    forged_all_derived_fields["rows"][0]["memory_state"] = "watch"
    forged_all_derived_fields["rows"][0]["reason_codes"] = [
        "independent_family_consensus_boost",
    ]
    forged_all_derived_fields["average_consensus_score"] = "0.700000"
    forged_all_derived_fields["memory_state"] = "watch"
    forged_all_derived_fields["pass_count"] = "0.000000"
    forged_all_derived_fields["watch_count"] = "1.000000"
    forged_all_derived_fields["block_count"] = "0.000000"
    forged_all_derived_fields["reason_codes"] = [
        "independent_family_consensus_boost",
    ]

    for forged, error_match in (
        (forged_score, "consensus_score"),
        (forged_policy, "memory_state|reason_codes"),
        (forged_family_count, "supporting_family_count.*family_count"),
        (forged_report_count, "row_count"),
        (forged_all_derived_fields, "consensus_score"),
    ):
        with pytest.raises(ValueError, match=error_match):
            api.validate_research_strategy_team_source_consensus_memory_report_payload(
                _resign_payload(forged),
            )


@pytest.mark.parametrize(
    ("target_name", "field_name", "forged_value", "error_match"),
    (
        (
            "row",
            "conflicting_observation_count",
            "1.000000",
            "conflicting_observation_count",
        ),
        ("row", "consensus_score", "0.700000", "consensus_score"),
        ("row", "memory_state", "watch", "memory_state"),
        (
            "row",
            "reason_codes",
            ["independent_family_consensus_boost"],
            "reason_codes",
        ),
        ("report", "memory_state", "watch", "memory_state"),
        ("report", "row_count", "2.000000", "row_count"),
        ("report", "pass_count", "0.000000", "pass_count"),
        ("report", "watch_count", "1.000000", "watch_count"),
        ("report", "block_count", "1.000000", "block_count"),
        (
            "report",
            "average_consensus_score",
            "0.700000",
            "average_consensus_score",
        ),
        (
            "report",
            "reason_codes",
            ["independent_family_consensus_boost"],
            "reason_codes",
        ),
    ),
)
def test_public_validator_rederives_every_materialized_field(
    target_name: str,
    field_name: str,
    forged_value: object,
    error_match: str,
) -> None:
    payload = _report(
        (
            _observation(family_id="family_a", confidence_score=Decimal("0.700000")),
            _observation(family_id="family_b", confidence_score=Decimal("0.800000")),
        ),
    ).payload
    forged = json.loads(json.dumps(payload))
    target = forged["rows"][0] if target_name == "row" else forged
    target[field_name] = forged_value

    with pytest.raises(ValueError, match=error_match):
        api.validate_research_strategy_team_source_consensus_memory_report_payload(
            _resign_payload(forged),
        )


def test_public_validator_rejects_noncanonical_sequence_order_with_canonical_digest() -> None:
    payload = _report(
        (
            _observation(
                team_id="team_alpha",
                memory_key="memory_a",
                family_id="family_a",
            ),
            _observation(
                team_id="team_beta",
                memory_key="memory_b",
                family_id="family_b",
            ),
        ),
        public_payload=(
            ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem(
                "summary",
                "safe value",
            ),
            ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem(
                "version",
                "v1",
            ),
        ),
    ).payload

    reversed_rows = json.loads(json.dumps(payload))
    reversed_rows["rows"].reverse()
    reversed_rows["derived_validation_digest"] = payload["derived_validation_digest"]

    reversed_public_payload = json.loads(json.dumps(payload))
    reversed_public_payload["public_payload"].reverse()
    reversed_public_payload["derived_validation_digest"] = payload[
        "derived_validation_digest"
    ]

    for forged in (reversed_rows, reversed_public_payload):
        with pytest.raises(ValueError, match="canonical order"):
            api.validate_research_strategy_team_source_consensus_memory_report_payload(
                forged,
            )


@pytest.mark.parametrize(
    "target_name",
    ("report", "config", "row", "public_payload_item"),
)
def test_public_validator_rejects_noncanonical_field_order_with_valid_digest(
    target_name: str,
) -> None:
    payload = _report(
        (
            _observation(family_id="family_a"),
            _observation(family_id="family_b"),
        ),
        public_payload=(
            ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem(
                "summary",
                "safe value",
            ),
        ),
    ).payload
    forged = json.loads(json.dumps(payload))
    if target_name == "report":
        target = forged
    elif target_name == "config":
        target = forged["config"]
    elif target_name == "row":
        target = forged["rows"][0]
    else:
        target = forged["public_payload"][0]
    items = list(target.items())
    items[0], items[1] = items[1], items[0]
    target.clear()
    target.update(items)

    with pytest.raises(ValueError, match="canonical order"):
        api.validate_research_strategy_team_source_consensus_memory_report_payload(
            forged,
        )


def test_direct_rows_reject_impossible_derived_count_relationships() -> None:
    with pytest.raises(ValueError, match="observation_count.*positive"):
        _direct_row(
            observation_count=Decimal("0.000000"),
            supporting_observation_count=Decimal("0.000000"),
            family_count=Decimal("0.000000"),
            supporting_family_count=Decimal("0.000000"),
            conflicting_observation_count=Decimal("0.000000"),
            average_confidence_score=Decimal("0.000000"),
            consensus_score=Decimal("0.000000"),
            memory_state="block",
            reason_codes=(
                "missing_supporting_consensus",
                "insufficient_supporting_family_consensus",
            ),
        )

    with pytest.raises(
        ValueError,
        match="supporting_family_count.*family_count",
    ):
        _direct_row(
            family_count=Decimal("0.000000"),
            supporting_family_count=Decimal("1.000000"),
        )

    with pytest.raises(
        ValueError,
        match="average_confidence_score.*zero",
    ):
        _direct_row(
            supporting_observation_count=Decimal("0.000000"),
            supporting_family_count=Decimal("0.000000"),
            conflicting_observation_count=Decimal("1.000000"),
            average_confidence_score=Decimal("0.500000"),
            consensus_score=Decimal("0.350000"),
            memory_state="block",
            reason_codes=(
                "missing_supporting_consensus",
                "insufficient_supporting_family_consensus",
                "conflicting_memory_observation",
            ),
        )


def test_reason_codes_must_be_unique_and_deterministic() -> None:
    with pytest.raises(ValueError, match="reason_codes.*unique"):
        _direct_row(
            reason_codes=(
                "insufficient_supporting_family_consensus",
                "insufficient_supporting_family_consensus",
            ),
        )

    with pytest.raises(ValueError, match="reason_codes.*deterministic"):
        _direct_row(
            observation_count=Decimal("2.000000"),
            supporting_observation_count=Decimal("2.000000"),
            family_count=Decimal("2.000000"),
            supporting_family_count=Decimal("2.000000"),
            average_confidence_score=Decimal("0.750000"),
            consensus_score=Decimal("0.850000"),
            memory_state="pass",
            reason_codes=(
                "consensus_memory_pass",
                "independent_family_consensus_boost",
            ),
        )


def test_custom_config_is_signed_and_revalidated_against_rows() -> None:
    strict_config = ResearchStrategyTeamSourceConsensusMemoryConfig(
        min_consensus_score=Decimal("0.900000"),
    )
    payload = _report(
        (
            _observation(family_id="family_a", confidence_score=Decimal("0.700000")),
            _observation(family_id="family_b", confidence_score=Decimal("0.800000")),
        ),
        config=strict_config,
    ).payload

    assert payload["config"]["min_consensus_score"] == "0.900000"
    assert payload["rows"][0]["memory_state"] == "watch"
    assert (
        api.validate_research_strategy_team_source_consensus_memory_report_payload(
            payload,
        )
        is True
    )

    forged_config = json.loads(json.dumps(payload))
    forged_config["config"]["min_consensus_score"] = "0.800000"
    with pytest.raises(ValueError, match="memory_state|reason_codes"):
        api.validate_research_strategy_team_source_consensus_memory_report_payload(
            _resign_payload(forged_config),
        )


def test_frozen_dataclasses_exact_types_and_hard_flags_are_enforced() -> None:
    report = _report(
        (
            _observation(family_id="family_a"),
            _observation(family_id="family_b"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.memory_state = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchStrategyTeamSourceConsensusMemoryConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchStrategyTeamSourceConsensusMemoryConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _observation(family_id="family_c", supports_consensus=True).__class__(
            team_id="team_alpha",
            memory_key="memory_b",
            family_id="family_c",
            confidence_score=Decimal("0.700000"),
            supports_consensus=True,
            observed_at=NOW,
            report_only=False,
        )

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error_match"),
    (
        ("readonly", False, "readonly"),
        (
            "confidence_score",
            Decimal("-0.0000004"),
            "confidence_score.*between zero and one",
        ),
        (
            "confidence_score",
            Decimal("-0.000000"),
            "confidence_score.*signed zero",
        ),
        ("supports_consensus", 1, "supports_consensus.*bool"),
    ),
)
def test_builder_revalidates_post_construction_tampered_observations(
    field_name: str,
    forged_value: object,
    error_match: str,
) -> None:
    observation = _observation()
    object.__setattr__(observation, field_name, forged_value)

    with pytest.raises(ValueError, match=error_match):
        _report((observation,))


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error_match"),
    (
        ("paper_only", False, "paper_only"),
        (
            "min_consensus_score",
            Decimal("-0.0000004"),
            "min_consensus_score.*between zero and one",
        ),
    ),
)
def test_builder_revalidates_post_construction_tampered_config(
    field_name: str,
    forged_value: object,
    error_match: str,
) -> None:
    config = ResearchStrategyTeamSourceConsensusMemoryConfig()
    object.__setattr__(config, field_name, forged_value)

    with pytest.raises(ValueError, match=error_match):
        _report((_observation(),), config=config)


def test_builder_revalidates_post_construction_tampered_public_payload_items() -> None:
    public_item = ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem(
        "summary",
        "safe value",
    )
    object.__setattr__(public_item, "report_only", False)

    with pytest.raises(ValueError, match="report_only"):
        _report((_observation(),), public_payload=(public_item,))


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error_match"),
    (
        (
            "observation_count",
            Decimal("-1.000000"),
            "observation_count.*nonnegative",
        ),
        ("readonly", False, "readonly"),
        (
            "average_confidence_score",
            Decimal("0.7500000"),
            "constructor-normalized",
        ),
    ),
)
def test_report_revalidates_post_construction_tampered_nested_rows(
    field_name: str,
    forged_value: object,
    error_match: str,
) -> None:
    report = _report(
        (
            _observation(family_id="family_a", confidence_score=Decimal("0.700000")),
            _observation(family_id="family_b", confidence_score=Decimal("0.800000")),
        ),
    )
    object.__setattr__(report.rows[0], field_name, forged_value)
    resigned_digest = api._report_digest_from_values(
        api._report_values_without_digest(report),
    )

    with pytest.raises(ValueError, match=error_match):
        replace(report, derived_validation_digest=resigned_digest)


def test_decimal_only_inputs_and_public_numbers_are_required() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        ResearchStrategyTeamSourceConsensusMemoryConfig(
            min_supporting_family_count=2,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Decimal"):
        _observation(confidence_score=0.7)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        ResearchStrategyTeamSourceConsensusMemoryRow(
            team_id="team_alpha",
            memory_key="memory_a",
            observation_count=Decimal("1.000000"),
            supporting_observation_count=1,  # type: ignore[arg-type]
            family_count=Decimal("1.000000"),
            supporting_family_count=Decimal("1.000000"),
            conflicting_observation_count=Decimal("0.000000"),
            average_confidence_score=Decimal("0.700000"),
            consensus_score=Decimal("0.700000"),
            memory_state="watch",
            reason_codes=("insufficient_supporting_family_consensus",),
        )


def test_decimal_bounds_counts_and_signed_zero_are_validated_before_quantization() -> None:
    with pytest.raises(ValueError, match="confidence_score.*between zero and one"):
        _observation(confidence_score=Decimal("-0.0000004"))

    with pytest.raises(ValueError, match="min_consensus_score.*between zero and one"):
        ResearchStrategyTeamSourceConsensusMemoryConfig(
            min_consensus_score=Decimal("1.0000004"),
        )

    with pytest.raises(ValueError, match="observation_count.*nonnegative"):
        _direct_row(
            observation_count=Decimal("-0.0000004"),
            supporting_observation_count=Decimal("0.000000"),
            family_count=Decimal("0.000000"),
            supporting_family_count=Decimal("0.000000"),
            conflicting_observation_count=Decimal("0.000000"),
            average_confidence_score=Decimal("0.000000"),
            consensus_score=Decimal("0.000000"),
            memory_state="block",
            reason_codes=(
                "missing_supporting_consensus",
                "insufficient_supporting_family_consensus",
            ),
        )

    with pytest.raises(
        ValueError,
        match="min_supporting_family_count.*whole Decimal",
    ):
        ResearchStrategyTeamSourceConsensusMemoryConfig(
            min_supporting_family_count=Decimal("1.500000"),
        )

    with pytest.raises(ValueError, match="confidence_score.*signed zero"):
        _observation(confidence_score=Decimal("-0.000000"))

    with pytest.raises(
        ValueError,
        match="independent_family_boost_per_family.*signed zero",
    ):
        ResearchStrategyTeamSourceConsensusMemoryConfig(
            independent_family_boost_per_family=Decimal("-0.000000"),
        )

    with pytest.raises(ValueError, match="observation_count.*signed zero"):
        _direct_row(observation_count=Decimal("-0.000000"))


@pytest.mark.parametrize(
    "value",
    (
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ),
)
def test_non_finite_decimals_are_rejected(value: Decimal) -> None:
    with pytest.raises(ValueError, match="confidence_score.*finite"):
        _observation(confidence_score=value)

    with pytest.raises(ValueError, match="Decimal payload value.*finite"):
        api._report_digest_from_values({"summary": value})


def test_digest_canonicalization_rejects_signed_zero() -> None:
    with pytest.raises(ValueError, match="signed zero"):
        api._report_digest_from_values({"summary": Decimal("-0.000000")})


def test_only_pass_watch_and_block_states_are_allowed() -> None:
    with pytest.raises(ValueError, match="memory_state"):
        ResearchStrategyTeamSourceConsensusMemoryRow(
            team_id="team_alpha",
            memory_key="memory_a",
            observation_count=Decimal("1.000000"),
            supporting_observation_count=Decimal("1.000000"),
            family_count=Decimal("1.000000"),
            supporting_family_count=Decimal("1.000000"),
            conflicting_observation_count=Decimal("0.000000"),
            average_confidence_score=Decimal("0.700000"),
            consensus_score=Decimal("0.700000"),
            memory_state="blocked",
            reason_codes=("insufficient_supporting_family_consensus",),
        )

    assert _report(()).memory_state == "block"


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report(
        (
            _observation(family_id="family_a"),
            _observation(family_id="family_b"),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem(
                    "summary",
                    "changed safe value",
                ),
            ),
        )


def test_public_payload_rejects_raw_candidate_market_source_and_secret_surfaces() -> None:
    for key in (
        "candidate_key",
        "market_key",
        "source_url",
        "source_text",
        "dsn_key",
        "table_key",
        "token_key",
        "network_key",
        "wallet_key",
        "auth_key",
        "order_key",
        "live_key",
        "sizing_key",
        "recommendation_key",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem(key, "safe value")

    for value in (
        "https://example.invalid/raw",
        "candidate alpha",
        "market alpha",
        "source alpha",
        "dsn alpha",
        "table alpha",
        "token alpha",
        "network alpha",
        "wallet alpha",
        "auth alpha",
        "order alpha",
        "live alpha",
        "trading alpha",
        "sizing alpha",
        "recommendation alpha",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem("summary", value)

    with pytest.raises(ValueError, match="unsafe public"):
        _observation(family_id="wallet_family")


def test_no_forbidden_capability_imports_or_public_fields_are_exposed() -> None:
    forbidden_public_terms = (
        "db",
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "execution",
        "sizing",
        "recommendation",
        "persistence",
        "file",
        "candidate",
        "market",
        "url",
        "dsn",
        "table",
        "token",
        "raw_text",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_public_terms)

    for cls in (
        ResearchStrategyTeamSourceConsensusMemoryConfig,
        ResearchStrategyTeamSourceConsensusMemoryObservation,
        ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem,
        ResearchStrategyTeamSourceConsensusMemoryRow,
        ResearchStrategyTeamSourceConsensusMemoryReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_public_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)


def test_phase_one_report_only_paper_only_readonly_purity() -> None:
    report = _report(
        (
            _observation(family_id="family_a"),
            _observation(family_id="family_b"),
        ),
        public_payload=(
            ResearchStrategyTeamSourceConsensusMemoryPublicPayloadItem(
                "summary",
                "safe value",
            ),
        ),
    )
    for value in (
        report.config,
        report.rows[0],
        report.public_payload[0],
        report,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    syntax_tree = ast.parse(inspect.getsource(api))
    imported_roots: set[str] = set()
    forbidden_calls = {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
    }
    forbidden_methods = {
        "connect",
        "execute",
        "executemany",
        "commit",
        "request",
        "urlopen",
        "send",
        "sendall",
        "write",
        "write_text",
        "write_bytes",
        "touch",
        "mkdir",
        "unlink",
        "remove",
        "rename",
        "replace",
        "place_order",
        "submit_order",
    }
    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_roots.add((node.module or "").split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_methods

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "re",
        "typing",
    }


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
