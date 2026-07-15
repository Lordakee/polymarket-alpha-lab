from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal, InvalidOperation, ROUND_DOWN, localcontext
import hashlib
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_memory_signal_reuse_value_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "historical_calibration_gain_weight": d("0.250000"),
        "evidence_reuse_quality_weight": d("0.250000"),
        "prior_error_avoidance_weight": d("0.200000"),
        "review_latency_reduction_weight": d("0.150000"),
        "current_evidence_gap_pressure_weight": d("0.150000"),
        "pass_threshold": d("0.800000"),
        "watch_threshold": d("0.600000"),
        "min_pass_historical_calibration_gain": d("0.750000"),
        "min_watch_historical_calibration_gain": d("0.500000"),
        "min_pass_evidence_reuse_quality": d("0.750000"),
        "min_watch_evidence_reuse_quality": d("0.500000"),
        "min_pass_prior_error_avoidance": d("0.750000"),
        "min_watch_prior_error_avoidance": d("0.500000"),
        "min_pass_review_latency_reduction": d("0.650000"),
        "min_watch_review_latency_reduction": d("0.400000"),
        "max_pass_current_evidence_gap_pressure": d("0.200000"),
        "max_watch_current_evidence_gap_pressure": d("0.600000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainMemorySignalReuseValueConfig(**values)


def observation(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "domain_key": "politics",
        "team_key": "policy_team",
        "memory_reference": "candidate-123 market_slug question https://example.invalid",
        "observed_at": GENERATED_AT - timedelta(minutes=30),
        "historical_calibration_gain": d("0.900000"),
        "evidence_reuse_quality": d("0.850000"),
        "prior_error_avoidance": d("0.800000"),
        "review_latency_reduction": d("0.750000"),
        "current_evidence_gap_pressure": d("0.100000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchTeamDomainMemorySignalReuseValueObservation(**values)


def build_report(*items: object, cfg: object | None = None, generated_at=GENERATED_AT):
    module = api()
    return module.build_research_team_domain_memory_signal_reuse_value_report(
        items,
        generated_at=generated_at,
        config=cfg or config(),
    )


def test_scores_memory_reuse_value_and_aggregates_by_domain() -> None:
    built = build_report(
        observation(
            domain_key="sports",
            team_key="tennis_team",
            memory_reference="watch-memory",
            historical_calibration_gain=d("0.650000"),
            evidence_reuse_quality=d("0.680000"),
            prior_error_avoidance=d("0.700000"),
            review_latency_reduction=d("0.500000"),
            current_evidence_gap_pressure=d("0.350000"),
        ),
        observation(
            domain_key="politics",
            team_key="policy_team",
            memory_reference="pass-memory-a",
        ),
        observation(
            domain_key="crypto",
            team_key="chain_team",
            memory_reference="block-memory",
            historical_calibration_gain=d("0.250000"),
            evidence_reuse_quality=d("0.300000"),
            prior_error_avoidance=d("0.250000"),
            review_latency_reduction=d("0.250000"),
            current_evidence_gap_pressure=d("0.850000"),
        ),
        observation(
            domain_key="politics",
            team_key="review_team",
            memory_reference="pass-memory-b",
            historical_calibration_gain=d("0.800000"),
            evidence_reuse_quality=d("0.900000"),
            prior_error_avoidance=d("0.850000"),
            review_latency_reduction=d("0.700000"),
            current_evidence_gap_pressure=d("0.200000"),
        ),
    )

    assert is_dataclass(built)
    assert built.generated_at == GENERATED_AT
    assert built.report_status == "block"
    assert built.domain_count == d("3.000000")
    assert built.observation_count == d("4.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.average_memory_reuse_value_score == d("0.639375")
    assert built.highest_current_evidence_gap_pressure == d("0.850000")

    crypto_row, politics_row, sports_row = built.rows
    assert crypto_row.domain_key == "crypto"
    assert crypto_row.reuse_value_status == "block"
    assert crypto_row.memory_reuse_value_score == d("0.247500")
    assert "current_evidence_gap_pressure_block" in crypto_row.reason_codes
    assert "memory_reuse_value_score_block" in crypto_row.reason_codes

    assert politics_row.domain_key == "politics"
    assert politics_row.reuse_value_status == "pass"
    assert politics_row.observation_count == d("2.000000")
    assert politics_row.team_count == d("2.000000")
    assert politics_row.average_historical_calibration_gain == d("0.850000")
    assert politics_row.average_evidence_reuse_quality == d("0.875000")
    assert politics_row.average_prior_error_avoidance == d("0.825000")
    assert politics_row.average_review_latency_reduction == d("0.725000")
    assert politics_row.average_current_evidence_gap_pressure == d("0.150000")
    assert politics_row.memory_reuse_value_score == d("0.832500")
    assert politics_row.signal_memory_digests[0].startswith("sha256:")
    assert politics_row.reason_codes == ("memory_signal_reuse_value_pass",)

    assert sports_row.domain_key == "sports"
    assert sports_row.reuse_value_status == "watch"
    assert sports_row.memory_reuse_value_score == d("0.645000")
    assert "review_latency_reduction_watch" in sports_row.reason_codes
    assert "current_evidence_gap_pressure_watch" in sports_row.reason_codes
    assert "memory_reuse_value_score_watch" in sports_row.reason_codes


def test_public_payload_digest_is_deterministic_and_validated() -> None:
    records = (
        observation(
            domain_key="politics",
            team_key="policy_team",
            memory_reference="candidate-999 market_id market_slug question text",
        ),
        observation(
            domain_key="politics",
            team_key="review_team",
            memory_reference="https://example.invalid/path?token=secret",
            historical_calibration_gain=d("0.800000"),
            evidence_reuse_quality=d("0.900000"),
            prior_error_avoidance=d("0.850000"),
            review_latency_reduction=d("0.700000"),
            current_evidence_gap_pressure=d("0.200000"),
        ),
    )
    built = build_report(
        *records,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    reordered = build_report(*reversed(records))

    assert built.public_payload == reordered.public_payload
    payload = api().research_team_domain_memory_signal_reuse_value_public_payload(built)
    assert payload == built.public_payload
    assert json.dumps(payload, sort_keys=True)
    assert payload["observation_count"] == "2.000000"
    assert payload["rows"][0]["memory_reuse_value_score"] == "0.832500"
    assert payload["derived_validation_digest"] == built.derived_validation_digest
    assert payload["derived_validation_digest"] == _canonical_payload_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    assert api().research_team_domain_memory_signal_reuse_value_report_digest(built) == (
        built.derived_validation_digest
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)


def test_public_payload_prevents_sensitive_surface_leaks() -> None:
    built = build_report(
        observation(
            memory_reference=(
                "candidate-999 market_id market_slug question text "
                "https://example.invalid/path?token=secret dsn://warehouse/table "
                "wallet order trade live"
            ),
        ),
    )

    payload = built.public_payload
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(built)
    _assert_no_forbidden_public_surface(payload)

    serialized = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "candidate-999",
        "market_id",
        "market_slug",
        "question text",
        "https://example.invalid",
        "token=secret",
        "dsn://warehouse",
        "table",
        "wallet",
        "order",
        "trade",
        "live",
    ):
        assert forbidden not in serialized

    with pytest.raises(ValueError, match="unsafe public"):
        observation(domain_key="market_slug")
    with pytest.raises(ValueError, match="unsafe public"):
        observation(team_key="wallet_team")
    with pytest.raises(ValueError, match="unsafe public"):
        api().research_team_domain_memory_signal_reuse_value_public_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "source_url": "x"},
        )
    for field_name in (
        "database_dsn",
        "network_endpoint",
        "execution_plan",
        "position_sizing",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            api().research_team_domain_memory_signal_reuse_value_public_payload(
                {
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                    field_name: "redacted",
                },
            )


def test_dict_public_payload_requires_exact_schema_and_valid_digest() -> None:
    module = api()
    payload = build_report(observation()).public_payload

    assert module.research_team_domain_memory_signal_reuse_value_public_payload(
        dict(payload),
    ) == payload
    assert module.research_team_domain_memory_signal_reuse_value_report_digest(
        dict(payload),
    ) == payload["derived_validation_digest"]

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(
            missing_digest,
        )

    extra_field = dict(payload)
    extra_field["note"] = "sanitized"
    extra_field["derived_validation_digest"] = _canonical_payload_digest(extra_field)
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(
            extra_field,
        )

    bad_digest = dict(payload)
    bad_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(
            bad_digest,
        )

    inconsistent = dict(payload)
    inconsistent["domain_count"] = "2.000000"
    inconsistent["derived_validation_digest"] = _canonical_payload_digest(inconsistent)
    with pytest.raises(ValueError, match="domain_count"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(
            inconsistent,
        )


def test_dict_public_payload_requires_json_runtime_types_without_coercion() -> None:
    module = api()
    built = build_report(observation())
    payload = built.public_payload

    typed_datetime = dict(payload)
    typed_datetime["generated_at"] = built.generated_at

    typed_decimal = dict(payload)
    typed_decimal["domain_count"] = built.domain_count

    tuple_rows = dict(payload)
    tuple_rows["rows"] = tuple(payload["rows"])

    typed_row_decimal = json.loads(json.dumps(payload))
    typed_row_decimal["rows"][0]["observation_count"] = d("1.000000")

    for forged, error_match in (
        (typed_datetime, "generated_at.*canonical datetime string"),
        (typed_decimal, "domain_count.*canonical Decimal string"),
        (tuple_rows, "rows.*JSON array"),
        (
            typed_row_decimal,
            "rows\\[0\\]\\.observation_count.*canonical Decimal string",
        ),
    ):
        with pytest.raises(ValueError, match=error_match):
            module.research_team_domain_memory_signal_reuse_value_public_payload(
                forged,
            )


def test_dict_public_payload_returns_a_detached_canonical_copy() -> None:
    module = api()
    payload = build_report(observation()).public_payload

    validated = (
        module.research_team_domain_memory_signal_reuse_value_public_payload(payload)
    )

    assert validated == payload
    assert validated is not payload
    assert validated["rows"] is not payload["rows"]
    assert validated["rows"][0] is not payload["rows"][0]

    payload["rows"][0]["domain_key"] = "mutated_after_validation"
    assert validated["rows"][0]["domain_key"] == "politics"


def test_resigned_payload_rejects_forged_derived_score_reasons_and_counts() -> None:
    module = api()
    payload = build_report(observation()).public_payload

    forged_score = json.loads(json.dumps(payload))
    forged_score["rows"][0]["memory_reuse_value_score"] = "0.600000"
    forged_score["rows"][0]["reuse_value_status"] = "watch"
    forged_score["rows"][0]["reason_codes"] = ["memory_reuse_value_score_watch"]
    forged_score["report_status"] = "watch"
    forged_score["pass_count"] = "0.000000"
    forged_score["watch_count"] = "1.000000"
    forged_score["average_memory_reuse_value_score"] = "0.600000"
    forged_score["reason_codes"] = [
        "memory_signal_reuse_value_report_watch",
        "memory_reuse_value_score_watch",
    ]
    forged_score["reason_code_counts"] = [
        {
            "reason_code": "memory_signal_reuse_value_report_watch",
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "reason_code": "memory_reuse_value_score_watch",
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    forged_score["derived_validation_digest"] = _canonical_payload_digest(forged_score)
    with pytest.raises(ValueError, match="memory_reuse_value_score must match"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(forged_score)

    forged_reasons = json.loads(json.dumps(payload))
    forged_reasons["rows"][0]["average_historical_calibration_gain"] = "0.600000"
    forged_reasons["rows"][0]["memory_reuse_value_score"] = "0.770000"
    forged_reasons["average_memory_reuse_value_score"] = "0.770000"
    forged_reasons["derived_validation_digest"] = _canonical_payload_digest(forged_reasons)
    with pytest.raises(ValueError, match="reason_codes must match"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(forged_reasons)

    forged_count = json.loads(json.dumps(payload))
    forged_count["pass_count"] = "2.000000"
    forged_count["domain_count"] = "2.000000"
    forged_count["derived_validation_digest"] = _canonical_payload_digest(forged_count)
    with pytest.raises(ValueError, match="domain_count|pass_count|status counts"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(forged_count)


def test_raw_decimal_bounds_and_signed_zero_are_rejected_before_quantization() -> None:
    module = api()

    with pytest.raises(ValueError, match="historical_calibration_gain.*between 0 and 1"):
        observation(historical_calibration_gain=d("-0.0000004"))
    with pytest.raises(ValueError, match="historical_calibration_gain.*between 0 and 1"):
        observation(historical_calibration_gain=d("1.0000004"))
    with pytest.raises(ValueError, match="historical_calibration_gain.*signed zero"):
        observation(historical_calibration_gain=d("-0.000000"))

    built = build_report(observation())
    with pytest.raises(ValueError, match="observation_count.*nonnegative"):
        replace(built.rows[0], observation_count=d("-0.0000004"))
    with pytest.raises(ValueError, match="observation_count.*whole count"):
        replace(built.rows[0], observation_count=d("1.0000004"))
    with pytest.raises(ValueError, match="team_count.*signed zero"):
        replace(built.rows[0], team_count=d("-0.000000"))

    signed_zero_payload = json.loads(json.dumps(built.public_payload))
    signed_zero_payload["rows"][0]["average_current_evidence_gap_pressure"] = "-0.000000"
    signed_zero_payload["highest_current_evidence_gap_pressure"] = "-0.000000"
    signed_zero_payload["derived_validation_digest"] = _canonical_payload_digest(
        signed_zero_payload,
    )
    with pytest.raises(ValueError, match="signed zero"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(
            signed_zero_payload,
        )


def test_decimal_math_is_independent_of_ambient_context_and_input_order() -> None:
    cfg = config()
    records = (
        observation(
            team_key="internal_alpha",
            memory_reference="private-memory-a",
            historical_calibration_gain=d("0.712345"),
            evidence_reuse_quality=d("0.823456"),
            prior_error_avoidance=d("0.734567"),
            review_latency_reduction=d("0.645678"),
            current_evidence_gap_pressure=d("0.256789"),
        ),
        observation(
            team_key="internal_beta",
            memory_reference="private-memory-b",
            historical_calibration_gain=d("0.812345"),
            evidence_reuse_quality=d("0.723456"),
            prior_error_avoidance=d("0.834567"),
            review_latency_reduction=d("0.745678"),
            current_evidence_gap_pressure=d("0.156789"),
        ),
    )
    expected = build_report(*records, cfg=cfg)

    with localcontext() as ambient:
        ambient.prec = 4
        ambient.rounding = ROUND_DOWN
        ambient.traps[InvalidOperation] = True
        actual = build_report(*reversed(records), cfg=cfg)

    assert actual.public_payload == expected.public_payload


def test_datetime_fields_require_a_defined_utc_offset() -> None:
    module = api()

    class MissingOffsetTimezone(tzinfo):
        def utcoffset(self, dt: datetime | None) -> None:
            return None

        def dst(self, dt: datetime | None) -> None:
            return None

    missing_offset = datetime(
        2026,
        7,
        8,
        12,
        0,
        tzinfo=MissingOffsetTimezone(),
    )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=missing_offset)
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(observation(), generated_at=missing_offset)
    with pytest.raises(ValueError, match="datetime value must be timezone-aware"):
        module._json_ready(missing_offset)
    with pytest.raises(ValueError, match="payload must be timezone-aware"):
        module._reject_unsafe_public_payload("payload", missing_offset)


def test_observation_future_boundary_uses_normalized_utc_instants() -> None:
    equivalent_generated_at = GENERATED_AT.astimezone(
        timezone(timedelta(hours=-4)),
    )

    at_boundary = build_report(
        observation(observed_at=GENERATED_AT),
        generated_at=equivalent_generated_at,
    )
    assert at_boundary.generated_at == GENERATED_AT
    assert at_boundary.observation_count == d("1.000000")

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(
            observation(observed_at=GENERATED_AT + timedelta(microseconds=1)),
            generated_at=equivalent_generated_at,
        )


def test_utc_conversion_rejects_unrepresentable_datetime_boundaries() -> None:
    underflow = datetime.min.replace(
        tzinfo=timezone(timedelta(hours=14)),
    )
    overflow = datetime.max.replace(
        tzinfo=timezone(timedelta(hours=-12)),
    )

    for value in (underflow, overflow):
        with pytest.raises(ValueError, match="observed_at.*representable in UTC"):
            observation(observed_at=value)


def test_observation_normalization_has_a_complete_stable_tie_break() -> None:
    module = api()
    lower = observation(
        team_key="internal_team",
        memory_reference="same-private-memory",
        historical_calibration_gain=d("0.700000"),
    )
    higher = observation(
        team_key="internal_team",
        memory_reference="same-private-memory",
        historical_calibration_gain=d("0.800000"),
    )

    lower_first = module._normalize_observations(
        (lower, higher),
        generated_at=GENERATED_AT,
    )
    higher_first = module._normalize_observations(
        (higher, lower),
        generated_at=GENERATED_AT,
    )

    assert lower_first == higher_first
    assert lower_first == (lower, higher)


def test_public_payload_requires_canonical_field_order_at_every_level() -> None:
    module = api()
    payload = build_report(observation()).public_payload

    reversed_report = dict(reversed(tuple(payload.items())))
    reversed_report["derived_validation_digest"] = _canonical_payload_digest(
        reversed_report,
    )
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(
            reversed_report,
        )

    reversed_row = json.loads(json.dumps(payload))
    reversed_row["rows"][0] = dict(
        reversed(tuple(reversed_row["rows"][0].items())),
    )
    reversed_row["derived_validation_digest"] = _canonical_payload_digest(reversed_row)
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(
            reversed_row,
        )

    reversed_reason_count = json.loads(json.dumps(payload))
    reversed_reason_count["reason_code_counts"][0] = dict(
        reversed(tuple(reversed_reason_count["reason_code_counts"][0].items())),
    )
    reversed_reason_count["derived_validation_digest"] = _canonical_payload_digest(
        reversed_reason_count,
    )
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(
            reversed_reason_count,
        )


def test_private_team_and_memory_reference_are_sha256_redacted() -> None:
    team_key = "internal_policy_cell_42"
    memory_reference = (
        "candidate-42 source_url=https://private.invalid token=private-secret"
    )
    private_observation = observation(
        team_key=team_key,
        memory_reference=memory_reference,
    )
    built = build_report(private_observation)

    serialized = json.dumps(built.public_payload, sort_keys=True)
    assert team_key not in serialized
    assert memory_reference not in serialized
    assert team_key not in repr(private_observation)
    assert memory_reference not in repr(private_observation)
    assert built.rows[0].signal_memory_digests == (
        "sha256:" + hashlib.sha256(memory_reference.encode("utf-8")).hexdigest(),
    )


@pytest.mark.parametrize("non_finite", ("NaN", "sNaN", "Infinity", "-Infinity"))
def test_non_finite_decimals_are_rejected_before_any_derivation(
    non_finite: str,
) -> None:
    module = api()

    with pytest.raises(ValueError, match="finite"):
        observation(historical_calibration_gain=d(non_finite))
    with pytest.raises(ValueError, match="finite"):
        config(pass_threshold=d(non_finite))

    payload = build_report(observation()).public_payload
    forged = json.loads(json.dumps(payload))
    forged["rows"][0]["memory_reuse_value_score"] = non_finite
    forged["derived_validation_digest"] = _canonical_payload_digest(forged)
    with pytest.raises(ValueError, match="finite"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(forged)


def test_all_public_dataclasses_are_non_subclassable() -> None:
    module = api()
    public_dataclasses = (
        module.ResearchTeamDomainMemorySignalReuseValueConfig,
        module.ResearchTeamDomainMemorySignalReuseValueObservation,
        module.ResearchTeamDomainMemorySignalReuseValueRow,
        module.ResearchTeamDomainMemorySignalReuseValueReasonCodeCount,
        module.ResearchTeamDomainMemorySignalReuseValueReport,
    )

    for cls in public_dataclasses:
        assert cls.__final__ is True
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"Invalid{cls.__name__}", (cls,), {})


def test_resigned_payload_recomputes_every_report_derived_field() -> None:
    module = api()
    payload = build_report(observation()).public_payload
    mutations = (
        ("report_status", "watch", "report_status"),
        ("domain_count", "2.000000", "domain_count"),
        ("observation_count", "2.000000", "observation_count"),
        ("pass_count", "2.000000", "pass_count"),
        (
            "average_memory_reuse_value_score",
            "0.700000",
            "average_memory_reuse_value_score",
        ),
        (
            "highest_current_evidence_gap_pressure",
            "0.200000",
            "highest_current_evidence_gap_pressure",
        ),
    )

    for field_name, forged_value, message in mutations:
        forged = json.loads(json.dumps(payload))
        forged[field_name] = forged_value
        forged["derived_validation_digest"] = _canonical_payload_digest(forged)
        with pytest.raises(ValueError, match=message):
            module.research_team_domain_memory_signal_reuse_value_public_payload(
                forged,
            )

    forged_reason_count = json.loads(json.dumps(payload))
    forged_reason_count["reason_code_counts"][0]["count"] = "2.000000"
    forged_reason_count["derived_validation_digest"] = _canonical_payload_digest(
        forged_reason_count,
    )
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(
            forged_reason_count,
        )


def test_resigned_payload_rejects_duplicate_domain_rows() -> None:
    module = api()
    forged = json.loads(json.dumps(build_report(observation()).public_payload))
    forged["rows"].append(dict(forged["rows"][0]))
    forged["domain_count"] = "2.000000"
    forged["observation_count"] = "2.000000"
    forged["pass_count"] = "2.000000"
    for reason_count in forged["reason_code_counts"]:
        if reason_count["reason_code"] == "memory_signal_reuse_value_pass":
            reason_count["count"] = "2.000000"
    forged["derived_validation_digest"] = _canonical_payload_digest(forged)

    with pytest.raises(ValueError, match="domain_key.*unique"):
        module.research_team_domain_memory_signal_reuse_value_public_payload(forged)


def test_public_exports_dataclass_and_payload_schemas_are_exact_and_frozen() -> None:
    module = api()
    built = build_report(observation())

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_SIGNAL_REUSE_VALUE_CONFIG_VERSION",
        "PUBLIC_STATUSES",
        "ResearchTeamDomainMemorySignalReuseValueConfig",
        "ResearchTeamDomainMemorySignalReuseValueObservation",
        "ResearchTeamDomainMemorySignalReuseValueRow",
        "ResearchTeamDomainMemorySignalReuseValueReasonCodeCount",
        "ResearchTeamDomainMemorySignalReuseValueReport",
        "build_research_team_domain_memory_signal_reuse_value_report",
        "research_team_domain_memory_signal_reuse_value_public_payload",
        "research_team_domain_memory_signal_reuse_value_report_digest",
    )
    expected_fields = {
        module.ResearchTeamDomainMemorySignalReuseValueConfig: (
            "config_version",
            "historical_calibration_gain_weight",
            "evidence_reuse_quality_weight",
            "prior_error_avoidance_weight",
            "review_latency_reduction_weight",
            "current_evidence_gap_pressure_weight",
            "pass_threshold",
            "watch_threshold",
            "min_pass_historical_calibration_gain",
            "min_watch_historical_calibration_gain",
            "min_pass_evidence_reuse_quality",
            "min_watch_evidence_reuse_quality",
            "min_pass_prior_error_avoidance",
            "min_watch_prior_error_avoidance",
            "min_pass_review_latency_reduction",
            "min_watch_review_latency_reduction",
            "max_pass_current_evidence_gap_pressure",
            "max_watch_current_evidence_gap_pressure",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchTeamDomainMemorySignalReuseValueObservation: (
            "domain_key",
            "team_key",
            "memory_reference",
            "observed_at",
            "historical_calibration_gain",
            "evidence_reuse_quality",
            "prior_error_avoidance",
            "review_latency_reduction",
            "current_evidence_gap_pressure",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchTeamDomainMemorySignalReuseValueRow: (
            "domain_key",
            "reuse_value_status",
            "observation_count",
            "team_count",
            "average_historical_calibration_gain",
            "average_evidence_reuse_quality",
            "average_prior_error_avoidance",
            "average_review_latency_reduction",
            "average_current_evidence_gap_pressure",
            "memory_reuse_value_score",
            "signal_memory_digests",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchTeamDomainMemorySignalReuseValueReasonCodeCount: (
            "reason_code",
            "count",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchTeamDomainMemorySignalReuseValueReport: (
            "generated_at",
            "config_version",
            "report_status",
            "domain_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_memory_reuse_value_score",
            "highest_current_evidence_gap_pressure",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }
    for cls, schema in expected_fields.items():
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert tuple(field.name for field in fields(cls)) == schema

    payload = built.public_payload
    assert tuple(payload) == expected_fields[type(built)]
    assert tuple(payload["rows"][0]) == expected_fields[type(built.rows[0])]
    assert tuple(payload["reason_code_counts"][0]) == expected_fields[
        type(built.reason_code_counts[0])
    ]

    with pytest.raises(FrozenInstanceError):
        built.rows[0].memory_reuse_value_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(TypeError, match="may not be subclassed"):

        class InvalidRowSubclass(type(built.rows[0])):
            pass


def test_phase1_module_is_report_only_paper_only_readonly_and_io_free() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    imported_roots: set[str] = set()
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "urlopen",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")

    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "re",
        "typing",
    }

    built = build_report(observation())
    for value in (
        config(),
        observation(),
        built,
        *built.rows,
        *built.reason_code_counts,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True


def test_custom_config_validation_and_frozen_decimal_only_contract() -> None:
    module = api()
    cfg = config(
        historical_calibration_gain_weight=d("0.200000"),
        evidence_reuse_quality_weight=d("0.300000"),
        prior_error_avoidance_weight=d("0.200000"),
        review_latency_reduction_weight=d("0.200000"),
        current_evidence_gap_pressure_weight=d("0.100000"),
        pass_threshold=d("0.750000"),
        watch_threshold=d("0.550000"),
        max_pass_current_evidence_gap_pressure=d("0.250000"),
    )
    built = build_report(observation(), cfg=cfg)

    assert built.rows[0].memory_reuse_value_score == d("0.835000")
    assert built.rows[0].reuse_value_status == "pass"
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    with pytest.raises(FrozenInstanceError):
        built.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        observation(evidence_reuse_quality=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="weights must sum to 1"):
        config(current_evidence_gap_pressure_weight=d("0.200000"))
    with pytest.raises(ValueError, match="pass_threshold"):
        config(pass_threshold=d("0.500000"), watch_threshold=d("0.600000"))
    with pytest.raises(ValueError, match="max_pass_current_evidence_gap_pressure"):
        config(
            max_pass_current_evidence_gap_pressure=d("0.700000"),
            max_watch_current_evidence_gap_pressure=d("0.600000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchTeamDomainMemorySignalReuseValueConfig(paper_only=False)

    for public_name in module.__all__:
        _assert_public_name(public_name)
    for cls in (
        module.ResearchTeamDomainMemorySignalReuseValueConfig,
        module.ResearchTeamDomainMemorySignalReuseValueObservation,
        type(built.rows[0]),
        type(built.reason_code_counts[0]),
        module.ResearchTeamDomainMemorySignalReuseValueReport,
    ):
        for field in fields(cls):
            if field.name == "memory_reference":
                continue
            _assert_public_name(field.name)


def test_report_revalidates_rows_against_its_validation_config() -> None:
    custom_config = config(
        historical_calibration_gain_weight=d("0.200000"),
        evidence_reuse_quality_weight=d("0.300000"),
        prior_error_avoidance_weight=d("0.200000"),
        review_latency_reduction_weight=d("0.200000"),
        current_evidence_gap_pressure_weight=d("0.100000"),
    )
    built = build_report(observation(), cfg=custom_config)
    assert built.rows[0].memory_reuse_value_score == d("0.835000")

    with pytest.raises(ValueError, match="memory_reuse_value_score must match"):
        replace(built, validation_config=config())


def test_builder_revalidates_frozen_config_and_observation_inputs() -> None:
    forged_config = config()
    object.__setattr__(
        forged_config,
        "historical_calibration_gain_weight",
        d("-0.000000"),
    )
    with pytest.raises(
        ValueError,
        match="historical_calibration_gain_weight.*signed zero",
    ):
        build_report(observation(), cfg=forged_config)

    forged_observation = observation()
    object.__setattr__(
        forged_observation,
        "historical_calibration_gain",
        d("-0.000000"),
    )
    with pytest.raises(
        ValueError,
        match="historical_calibration_gain.*signed zero",
    ):
        build_report(forged_observation)


def test_report_revalidates_frozen_nested_rows_before_digest_validation() -> None:
    module = api()
    built = build_report(observation())
    object.__setattr__(
        built.rows[0],
        "signal_memory_digests",
        ("safe-but-not-a-sha256-digest",),
    )
    resigned_digest = module._report_digest_from_values(
        module._report_values_without_digest(built),
    )

    with pytest.raises(ValueError, match="signal_memory_digests.*sha256"):
        replace(built, derived_validation_digest=resigned_digest)


def test_report_revalidates_frozen_nested_reason_code_counts() -> None:
    built = build_report(observation())
    object.__setattr__(
        built.reason_code_counts[0],
        "reason_code",
        "safe_unknown_reason",
    )

    with pytest.raises(ValueError, match="reason_code.*supported"):
        replace(built)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("public payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if type(value) is Decimal:
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal: {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == "memory_reference":
                continue
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
        return
    if type(value) in (tuple, list):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)


def _assert_no_forbidden_public_surface(value: object) -> None:
    forbidden = (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "://",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "trading",
        "live",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(fragment in lowered_key for fragment in forbidden), lowered_key
            _assert_no_forbidden_public_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_forbidden_public_surface(item)
        return
    if isinstance(value, str):
        lowered_value = value.lower()
        assert not any(fragment in lowered_value for fragment in forbidden), lowered_value


def _assert_public_name(value: str) -> None:
    lowered = value.lower()
    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "recommendation",
    ):
        assert forbidden not in lowered


def _canonical_payload_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
