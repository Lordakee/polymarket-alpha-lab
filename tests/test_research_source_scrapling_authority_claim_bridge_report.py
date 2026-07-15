from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 14, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_scrapling_authority_claim_bridge_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    unsigned_payload = deepcopy(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    payload["derived_validation_digest"] = sha256(
        json.dumps(
            unsigned_payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    return payload


def observation(
    *,
    private_bridge_ref: str = (
        "raw_candidate_id=secret-candidate|market_id=secret-market|"
        "market_slug=secret-slug|question=private question|"
        "source_url=https://example.invalid/path?token=secret&wallet=secret"
    ),
    observed_seconds_ago: int = 300,
    scrapling_claim_capture_score: Decimal = d("0.940000"),
    scrapling_claim_extraction_score: Decimal = d("0.900000"),
    authority_claim_match_score: Decimal = d("0.910000"),
    authority_source_confidence_score: Decimal = d("0.880000"),
    claim_semantic_alignment_score: Decimal = d("0.890000"),
    claim_freshness_score: Decimal = d("0.950000"),
    contradiction_pressure_score: Decimal = d("0.040000"),
    unresolved_authority_gap_score: Decimal = d("0.030000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceScraplingAuthorityClaimBridgeObservation(
        private_bridge_ref=private_bridge_ref,
        observed_at=GENERATED_AT - timedelta(seconds=observed_seconds_ago),
        scrapling_claim_capture_score=scrapling_claim_capture_score,
        scrapling_claim_extraction_score=scrapling_claim_extraction_score,
        authority_claim_match_score=authority_claim_match_score,
        authority_source_confidence_score=authority_source_confidence_score,
        claim_semantic_alignment_score=claim_semantic_alignment_score,
        claim_freshness_score=claim_freshness_score,
        contradiction_pressure_score=contradiction_pressure_score,
        unresolved_authority_gap_score=unresolved_authority_gap_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_scrapling_authority_claim_bridge_report(
        rows,
        config=cfg,
        generated_at=GENERATED_AT,
    )


def test_decimal_math_uses_a_fixed_local_context() -> None:
    module = api()
    baseline = build_report(observation())
    baseline_payload = deepcopy(baseline.payload)

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        context.traps[Inexact] = True
        context.traps[Rounded] = True

        rebuilt = build_report(observation())
        assert rebuilt.payload == baseline_payload
        assert module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
            baseline_payload,
        )


def test_payload_uses_exact_canonical_bridge_evidence_and_config_schema() -> None:
    module = api()
    config = module.ResearchSourceScraplingAuthorityClaimBridgeConfig(
        max_pass_claim_gap_ratio=d("0.120000"),
    )
    payload = build_report(observation(), cfg=config).payload

    assert set(payload) == {
        "generated_at",
        "config_version",
        "config",
        "observation_count",
        "row_count",
        "average_scrapling_claim_score",
        "average_authority_claim_score",
        "average_claim_semantic_alignment_score",
        "average_claim_freshness_score",
        "average_bridge_authority_score",
        "average_dual_claim_floor_score",
        "average_claim_gap_ratio",
        "highest_claim_gap_ratio",
        "highest_contradiction_pressure_score",
        "highest_unresolved_authority_gap_score",
        "pass_count",
        "watch_count",
        "block_count",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(payload["config"]) == {
        "config_version",
        "min_pass_bridge_authority_score",
        "min_watch_bridge_authority_score",
        "min_pass_dual_claim_floor_score",
        "min_watch_dual_claim_floor_score",
        "max_pass_claim_gap_ratio",
        "max_watch_claim_gap_ratio",
        "max_pass_contradiction_pressure_score",
        "max_watch_contradiction_pressure_score",
        "max_pass_unresolved_authority_gap_score",
        "max_watch_unresolved_authority_gap_score",
        "bridge_claim_consensus_weight",
        "bridge_semantic_alignment_weight",
        "bridge_freshness_weight",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert set(payload["rows"][0]) == {
        "row_index",
        "observed_at",
        "scrapling_claim_capture_score",
        "scrapling_claim_extraction_score",
        "authority_claim_match_score",
        "authority_source_confidence_score",
        "scrapling_claim_score",
        "authority_claim_score",
        "claim_semantic_alignment_score",
        "claim_freshness_score",
        "contradiction_pressure_score",
        "unresolved_authority_gap_score",
        "claim_gap_ratio",
        "dual_claim_floor_score",
        "bridge_authority_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert payload["config"]["max_pass_claim_gap_ratio"] == "0.120000"
    assert "private_bridge_ref" not in json.dumps(payload, sort_keys=True)
    assert module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


def test_pass_report_redacts_private_inputs_and_exports_stable_digest_payload() -> None:
    module = api()
    report_a = build_report(
        observation(private_bridge_ref="private-alpha"),
        observation(
            private_bridge_ref=(
                "raw_candidate_id=secret-two|source_text=verbatim private text"
            ),
            observed_seconds_ago=600,
            scrapling_claim_capture_score=d("0.960000"),
            scrapling_claim_extraction_score=d("0.920000"),
            authority_claim_match_score=d("0.930000"),
            authority_source_confidence_score=d("0.900000"),
        ),
    )
    report_b = build_report(
        observation(
            private_bridge_ref="changed-private-two",
            observed_seconds_ago=600,
            scrapling_claim_capture_score=d("0.960000"),
            scrapling_claim_extraction_score=d("0.920000"),
            authority_claim_match_score=d("0.930000"),
            authority_source_confidence_score=d("0.900000"),
        ),
        observation(private_bridge_ref="changed-private-one"),
    )
    changed_report = build_report(
        observation(scrapling_claim_capture_score=d("0.700000")),
    )

    assert type(report_a) is module.ResearchSourceScraplingAuthorityClaimBridgeReport
    assert is_dataclass(report_a)
    assert report_a.__dataclass_params__.frozen
    assert report_a.status == "pass"
    assert report_a.observation_count == d("2.000000")
    assert report_a.pass_count == d("2.000000")
    assert report_a.watch_count == d("0.000000")
    assert report_a.block_count == d("0.000000")
    assert report_a.average_bridge_authority_score == d("0.914531")
    assert report_a.highest_claim_gap_ratio == d("0.015000")
    assert report_a.reason_codes == (
        "scrapling_authority_claim_bridge_pass",
    )
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert report_a.derived_validation_digest != changed_report.derived_validation_digest

    payload = report_a.payload
    assert payload == module.research_source_scrapling_authority_claim_bridge_report_payload(
        report_a,
    )
    assert payload["derived_validation_digest"] == module.research_source_scrapling_authority_claim_bridge_report_digest(
        report_a,
    )
    assert payload["observation_count"] == "2.000000"
    assert payload["rows"][0]["row_index"] == "1.000000"
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    json.dumps(payload, sort_keys=True)
    assert module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )
    assert_no_decimal_or_float_values(payload)
    assert_payload_has_no_forbidden_values(payload)


def test_watch_and_block_statuses_use_only_pass_watch_block_reason_order() -> None:
    watch_report = build_report(
        observation(
            scrapling_claim_capture_score=d("0.720000"),
            scrapling_claim_extraction_score=d("0.720000"),
            authority_claim_match_score=d("0.680000"),
            authority_source_confidence_score=d("0.680000"),
            claim_semantic_alignment_score=d("0.700000"),
            claim_freshness_score=d("0.700000"),
            contradiction_pressure_score=d("0.200000"),
            unresolved_authority_gap_score=d("0.140000"),
        ),
    )
    block_report = build_report(
        observation(
            scrapling_claim_capture_score=d("0.900000"),
            scrapling_claim_extraction_score=d("0.900000"),
            authority_claim_match_score=d("0.200000"),
            authority_source_confidence_score=d("0.200000"),
            claim_semantic_alignment_score=d("0.300000"),
            claim_freshness_score=d("0.400000"),
            contradiction_pressure_score=d("0.500000"),
            unresolved_authority_gap_score=d("0.400000"),
        ),
    )

    assert watch_report.status == "watch"
    assert watch_report.rows[0].status == "watch"
    assert watch_report.rows[0].reason_codes == (
        "bridge_authority_score_below_pass_threshold",
        "dual_claim_floor_below_pass_threshold",
        "contradiction_pressure_above_pass_threshold",
        "unresolved_authority_gap_above_pass_threshold",
    )
    assert block_report.status == "block"
    assert block_report.rows[0].status == "block"
    assert block_report.rows[0].reason_codes == (
        "bridge_authority_score_below_watch_threshold",
        "dual_claim_floor_below_watch_threshold",
        "claim_gap_above_watch_threshold",
        "contradiction_pressure_above_watch_threshold",
        "unresolved_authority_gap_above_watch_threshold",
    )
    assert {watch_report.status, block_report.status, "pass"} == {
        "pass",
        "watch",
        "block",
    }


def test_empty_report_blocks_with_decimal_zeroes_and_frozen_report_only_flags() -> None:
    module = api()
    report = build_report()

    assert module.RESEARCH_SOURCE_SCRAPLING_AUTHORITY_CLAIM_BRIDGE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "block"
    assert report.observation_count == d("0.000000")
    assert report.average_bridge_authority_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "scrapling_authority_claim_bridge_no_inputs",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.derived_validation_digest == module.research_source_scrapling_authority_claim_bridge_report_digest(
        report,
    )

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(TypeError):

        class BadReport(module.ResearchSourceScraplingAuthorityClaimBridgeReport):
            pass


def test_validation_rejects_non_decimal_future_dates_flags_digest_and_unsafe_payloads() -> None:
    module = api()

    with pytest.raises(ValueError, match="Decimal"):
        observation(scrapling_claim_capture_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(authority_claim_match_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(observation(observed_seconds_ago=-1))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_scrapling_authority_claim_bridge_report(
            (),
            generated_at=datetime(2026, 7, 9, 14, 0),
        )
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)

    report = build_report(observation())
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    broken_payload = dict(report.payload)
    broken_payload["average_bridge_authority_score"] = "0.100000"
    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        broken_payload,
    )
    unsafe_payload = dict(report.payload)
    unsafe_payload["source_url"] = "https://example.invalid/private"
    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        unsafe_payload,
    )


def test_validation_rejects_resigned_forged_row_status_and_reasons() -> None:
    module = api()
    payload = deepcopy(build_report(observation()).payload)
    forged_reason = "bridge_authority_score_below_pass_threshold"
    payload["status"] = "watch"
    payload["reason_codes"] = [forged_reason]
    payload["reason_code_counts"] = [
        {
            "reason_code": forged_reason,
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


def test_validation_rejects_resigned_forged_derived_counts() -> None:
    module = api()
    payload = deepcopy(build_report(observation()).payload)
    payload["pass_count"] = "2.000000"

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


def test_validation_rejects_resigned_forged_derived_score() -> None:
    module = api()
    payload = deepcopy(build_report(observation()).payload)
    payload["average_bridge_authority_score"] = "0.900000"

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


def test_validation_rejects_resigned_forged_row_derived_floor_score() -> None:
    module = api()
    payload = deepcopy(build_report(observation()).payload)
    payload["rows"][0]["dual_claim_floor_score"] = "0.100000"
    payload["average_dual_claim_floor_score"] = "0.100000"

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


def test_validation_rejects_resigned_payload_without_full_derived_recomputation() -> None:
    module = api()
    payload = deepcopy(build_report(observation()).payload)
    payload["rows"][0]["claim_semantic_alignment_score"] = "0.000000"
    payload["average_claim_semantic_alignment_score"] = "0.000000"

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


@pytest.mark.parametrize(
    "field_name",
    (
        "scrapling_claim_capture_score",
        "scrapling_claim_extraction_score",
        "authority_claim_match_score",
        "authority_source_confidence_score",
    ),
)
def test_validation_rejects_resigned_mutated_public_bridge_evidence(
    field_name: str,
) -> None:
    module = api()
    payload = deepcopy(build_report(observation()).payload)
    payload["rows"][0][field_name] = "0.100000"

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


def test_validation_rejects_resigned_config_without_rederived_rows() -> None:
    module = api()
    payload = deepcopy(build_report(observation()).payload)
    payload["config"]["bridge_claim_consensus_weight"] = "0.600000"
    payload["config"]["bridge_semantic_alignment_weight"] = "0.200000"
    payload["config"]["bridge_freshness_weight"] = "0.200000"

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


@pytest.mark.parametrize("rank_forgery", ("reversed_rows", "duplicate_row_index"))
def test_validation_rejects_resigned_noncanonical_row_rank(
    rank_forgery: str,
) -> None:
    module = api()
    payload = deepcopy(
        build_report(
            observation(observed_seconds_ago=300),
            observation(
                observed_seconds_ago=600,
                scrapling_claim_capture_score=d("0.960000"),
            ),
        ).payload,
    )
    if rank_forgery == "reversed_rows":
        payload["rows"].reverse()
    else:
        payload["rows"][1]["row_index"] = "1.000000"

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


@pytest.mark.parametrize(
    "schema_change",
    (
        "extra_report_key",
        "missing_report_key",
        "extra_row_key",
        "missing_row_key",
        "extra_config_key",
        "missing_config_key",
        "extra_reason_count_key",
        "missing_reason_count_key",
    ),
)
def test_validation_rejects_resigned_payloads_without_exact_schemas(
    schema_change: str,
) -> None:
    module = api()
    payload = deepcopy(build_report(observation()).payload)
    if schema_change == "extra_report_key":
        payload["unexpected"] = "safe"
    elif schema_change == "missing_report_key":
        payload.pop("row_count")
    elif schema_change == "extra_row_key":
        payload["rows"][0]["unexpected"] = "safe"
    elif schema_change == "missing_row_key":
        payload["rows"][0].pop("claim_gap_ratio")
    elif schema_change == "extra_config_key":
        payload["config"]["unexpected"] = "safe"
    elif schema_change == "missing_config_key":
        payload["config"].pop("bridge_freshness_weight")
    elif schema_change == "extra_reason_count_key":
        payload["reason_code_counts"][0]["unexpected"] = "safe"
    else:
        payload["reason_code_counts"][0].pop("count")

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


@pytest.mark.parametrize("scope", ("report", "config", "row", "reason_code_count"))
def test_validation_rejects_resigned_payloads_with_noncanonical_key_order(
    scope: str,
) -> None:
    module = api()
    payload = deepcopy(build_report(observation()).payload)
    if scope == "report":
        payload = {key: payload[key] for key in reversed(tuple(payload))}
    elif scope == "config":
        config = payload["config"]
        payload["config"] = {
            key: config[key]
            for key in reversed(tuple(config))
        }
    elif scope == "row":
        row = payload["rows"][0]
        payload["rows"][0] = {
            key: row[key]
            for key in reversed(tuple(row))
        }
    else:
        reason_code_count = payload["reason_code_counts"][0]
        payload["reason_code_counts"][0] = {
            key: reason_code_count[key]
            for key in reversed(tuple(reason_code_count))
        }

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


def test_builder_revalidates_object_setattr_mutated_config() -> None:
    module = api()
    config = module.ResearchSourceScraplingAuthorityClaimBridgeConfig()
    object.__setattr__(config, "bridge_claim_consensus_weight", d("0.000000"))
    object.__setattr__(config, "bridge_semantic_alignment_weight", d("0.000000"))
    object.__setattr__(config, "bridge_freshness_weight", d("0.000000"))

    with pytest.raises(ValueError, match="weights must sum to 1"):
        build_report(observation(), cfg=config)


def test_builder_revalidates_object_setattr_mutated_observation() -> None:
    item = observation()
    object.__setattr__(item, "private_bridge_ref", " ")

    with pytest.raises(ValueError, match="canonical nonblank string"):
        build_report(item)


def test_report_revalidates_object_setattr_mutated_nested_values() -> None:
    report = build_report(observation())
    row = report.rows[0]
    reason_code_count = report.reason_code_counts[0]
    object.__setattr__(row, "row_index", d("1.0000000"))
    object.__setattr__(reason_code_count, "count", d("1.0000000"))

    reconstructed = replace(
        report,
        rows=(row,),
        reason_code_counts=(reason_code_count,),
        derived_validation_digest="",
    )

    assert reconstructed.rows[0].row_index.as_tuple().exponent == -6
    assert reconstructed.reason_code_counts[0].count.as_tuple().exponent == -6


def test_validation_rejects_resigned_noncanonical_reason_code_order() -> None:
    module = api()
    payload = deepcopy(
        build_report(
            observation(
                scrapling_claim_capture_score=d("0.900000"),
                scrapling_claim_extraction_score=d("0.900000"),
                authority_claim_match_score=d("0.200000"),
                authority_source_confidence_score=d("0.200000"),
                claim_semantic_alignment_score=d("0.300000"),
                claim_freshness_score=d("0.400000"),
                contradiction_pressure_score=d("0.500000"),
                unresolved_authority_gap_score=d("0.400000"),
            ),
        ).payload,
    )
    payload["reason_codes"].reverse()
    payload["rows"][0]["reason_codes"].reverse()

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


@pytest.mark.parametrize(
    "field_name",
    (
        "scrapling_claim_score",
        "authority_claim_score",
        "claim_gap_ratio",
        "dual_claim_floor_score",
        "bridge_authority_score",
    ),
)
def test_validation_rederives_every_public_row_score_after_resigning(
    field_name: str,
) -> None:
    module = api()
    payload = deepcopy(build_report(observation()).payload)
    payload["rows"][0][field_name] = "0.000000"

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("observation_count", "2.000000"),
        ("row_count", "2.000000"),
        ("average_scrapling_claim_score", "0.000000"),
        ("average_authority_claim_score", "0.000000"),
        ("average_claim_semantic_alignment_score", "0.000000"),
        ("average_claim_freshness_score", "0.000000"),
        ("average_bridge_authority_score", "0.000000"),
        ("average_dual_claim_floor_score", "0.000000"),
        ("average_claim_gap_ratio", "0.000000"),
        ("highest_claim_gap_ratio", "0.000000"),
        ("highest_contradiction_pressure_score", "0.000000"),
        ("highest_unresolved_authority_gap_score", "0.000000"),
        ("pass_count", "0.000000"),
        ("watch_count", "1.000000"),
        ("block_count", "1.000000"),
        ("status", "watch"),
        ("reason_codes", []),
    ),
)
def test_validation_rederives_every_public_report_aggregate_after_resigning(
    field_name: str,
    value: str | list[str],
) -> None:
    module = api()
    payload = deepcopy(build_report(observation()).payload)
    payload[field_name] = value

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


def test_validation_rederives_reason_code_counts_after_resigning() -> None:
    module = api()
    payload = deepcopy(build_report(observation()).payload)
    payload["reason_code_counts"][0]["count"] = "2.000000"

    resign_payload(payload)

    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


def test_complete_public_sort_ties_are_input_order_independent() -> None:
    first = observation(private_bridge_ref="private-first")
    second = observation(private_bridge_ref="private-second")

    assert build_report(first, second).payload == build_report(second, first).payload


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("scrapling_claim_capture_score", d("1.0000004")),
        ("authority_source_confidence_score", d("-0.0000004")),
    ),
)
def test_probability_bounds_are_checked_before_quantization(
    field_name: str,
    value: Decimal,
) -> None:
    with pytest.raises(ValueError, match="between zero and one"):
        observation(**{field_name: value})


def test_config_probability_bounds_are_checked_before_quantization() -> None:
    module = api()

    with pytest.raises(ValueError, match="between zero and one"):
        module.ResearchSourceScraplingAuthorityClaimBridgeConfig(
            min_pass_bridge_authority_score=d("1.0000004"),
        )
    with pytest.raises(ValueError, match="between zero and one"):
        module.ResearchSourceScraplingAuthorityClaimBridgeConfig(
            max_watch_claim_gap_ratio=d("-0.0000004"),
        )


@pytest.mark.parametrize("value", (d("NaN"), d("Infinity"), d("-Infinity")))
def test_non_finite_decimals_are_rejected_in_inputs_and_resigned_payloads(
    value: Decimal,
) -> None:
    module = api()

    with pytest.raises(ValueError, match="finite"):
        observation(scrapling_claim_capture_score=value)

    payload = deepcopy(build_report(observation()).payload)
    payload["rows"][0]["scrapling_claim_capture_score"] = str(value)
    resign_payload(payload)
    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


def test_signed_zero_is_rejected_for_probabilities_and_counts() -> None:
    module = api()

    with pytest.raises(ValueError, match="signed zero"):
        observation(scrapling_claim_capture_score=d("-0"))
    with pytest.raises(ValueError, match="signed zero"):
        module.ResearchSourceScraplingAuthorityClaimBridgeConfig(
            min_pass_bridge_authority_score=d("-0"),
        )

    report = build_report()
    with pytest.raises(ValueError, match="signed zero"):
        replace(
            report,
            pass_count=d("-0"),
            derived_validation_digest="",
        )

    payload = deepcopy(build_report(observation()).payload)
    payload["rows"][0]["authority_claim_match_score"] = "-0.000000"
    resign_payload(payload)
    assert not module.validate_research_source_scrapling_authority_claim_bridge_report_payload(
        payload,
    )


def test_all_public_dataclasses_are_frozen_phase_one_surfaces() -> None:
    module = api()
    report = build_report(observation())
    values = (
        module.ResearchSourceScraplingAuthorityClaimBridgeConfig(),
        observation(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )

    for value in values:
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.readonly = False


def test_all_public_dataclasses_are_non_subclassable() -> None:
    module = api()

    for public_type in (
        module.ResearchSourceScraplingAuthorityClaimBridgeConfig,
        module.ResearchSourceScraplingAuthorityClaimBridgeObservation,
        module.ResearchSourceScraplingAuthorityClaimBridgeRow,
        module.ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount,
        module.ResearchSourceScraplingAuthorityClaimBridgeReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Bad{public_type.__name__}", (public_type,), {})


def test_module_scope_has_no_network_database_wallet_order_or_trade_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    forbidden_calls = {
        "connect",
        "authenticate",
        "authorize",
        "commit",
        "execute",
        "executemany",
        "fetch",
        "login",
        "mkdir",
        "open",
        "persist",
        "read_bytes",
        "read_text",
        "request",
        "post",
        "put",
        "patch",
        "save",
        "send",
        "trade",
        "order",
        "recommend",
        "size",
        "unlink",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_calls

    forbidden_import_fragments = (
        "db",
        "agent_reach",
        "aiohttp",
        "auth",
        "http",
        "pathlib",
        "psycopg",
        "requests",
        "scrapling",
        "socket",
        "sql",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert imported_modules <= {
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
    forbidden_public_names = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_trade",
        "position_sizing",
        "recommendation",
    }
    public_field_names = {
        field.name
        for cls in (
            module.ResearchSourceScraplingAuthorityClaimBridgeConfig,
            module.ResearchSourceScraplingAuthorityClaimBridgeRow,
            module.ResearchSourceScraplingAuthorityClaimBridgeReasonCodeCount,
            module.ResearchSourceScraplingAuthorityClaimBridgeReport,
        )
        for field in fields(cls)
    }
    assert forbidden_public_names.isdisjoint(public_field_names)


def assert_no_decimal_or_float_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_decimal_or_float_values(item)
    else:
        assert type(value) is not Decimal
        assert type(value) is not float


def assert_payload_has_no_forbidden_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "verbatim private",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommendation",
        "private-alpha",
        "changed-private",
        "secret",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_forbidden_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_forbidden_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
