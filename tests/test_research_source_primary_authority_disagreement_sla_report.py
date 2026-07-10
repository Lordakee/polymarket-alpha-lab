from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_primary_authority_disagreement_sla_report"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "disagreement_watch_age_seconds": d("1800.000000"),
        "disagreement_block_age_seconds": d("7200.000000"),
        "primary_authority_watch_threshold": d("0.700000"),
        "primary_authority_block_threshold": d("0.400000"),
        "counter_authority_watch_pressure": d("0.300000"),
        "counter_authority_block_pressure": d("0.600000"),
        "minimum_independent_crosscheck_count": d("2.000000"),
    }
    values.update(overrides)
    return module.ResearchSourcePrimaryAuthorityDisagreementSlaConfig(**values)


def signal(
    review_bucket: str,
    *,
    opened_seconds_ago: int | None = None,
    primary_authority_score: Decimal = d("0.950000"),
    counter_authority_pressure_score: Decimal = d("0.050000"),
    independent_crosscheck_count: Decimal = d("3.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourcePrimaryAuthorityDisagreementSlaSignal(
        review_bucket=review_bucket,
        disagreement_opened_at=(
            None
            if opened_seconds_ago is None
            else GENERATED_AT - timedelta(seconds=opened_seconds_ago)
        ),
        primary_authority_score=primary_authority_score,
        counter_authority_pressure_score=counter_authority_pressure_score,
        independent_crosscheck_count=independent_crosscheck_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_primary_authority_disagreement_sla_report(
        signals,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def mutable_payload(report: Any) -> dict[str, Any]:
    module = api()
    payload = module.research_source_primary_authority_disagreement_sla_report_payload(
        report,
    )
    return json.loads(json.dumps(payload))


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def test_report_scores_pass_watch_and_block_primary_authority_disagreement_sla() -> None:
    module = api()
    report = build_report(
        signal("official-consensus"),
        signal(
            "agency-review",
            opened_seconds_ago=2400,
            primary_authority_score=d("0.650000"),
            counter_authority_pressure_score=d("0.350000"),
            independent_crosscheck_count=d("1.000000"),
        ),
        signal(
            "manual-escalation",
            opened_seconds_ago=8000,
            primary_authority_score=d("0.300000"),
            counter_authority_pressure_score=d("0.700000"),
            independent_crosscheck_count=d("0.000000"),
        ),
    )

    assert type(report) is module.ResearchSourcePrimaryAuthorityDisagreementSlaReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.review_bucket_count == d("3.000000")
    assert report.open_disagreement_count == d("2.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.overdue_disagreement_count == d("1.000000")
    assert report.weak_primary_authority_count == d("2.000000")
    assert report.counter_authority_pressure_count == d("2.000000")
    assert report.low_independent_crosscheck_count == d("2.000000")
    assert report.lowest_resolution_readiness_score == d("0.150000")
    assert report.highest_disagreement_age_seconds == d("8000.000000")
    assert report.highest_counter_authority_pressure_score == d("0.700000")
    assert report.reason_codes == (
        "primary_authority_disagreement_open_block",
        "primary_authority_score_block",
        "counter_authority_pressure_block",
        "independent_crosscheck_block",
        "primary_authority_disagreement_open_watch",
        "primary_authority_score_watch",
        "counter_authority_pressure_watch",
        "independent_crosscheck_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, watched, passed = report.rows
    assert (blocked.review_bucket, blocked.status) == ("manual-escalation", "block")
    assert blocked.disagreement_age_seconds == d("8000.000000")
    assert blocked.sla_score == d("0.000000")
    assert blocked.crosscheck_score == d("0.000000")
    assert blocked.resolution_readiness_score == d("0.150000")
    assert blocked.reason_codes == (
        "primary_authority_disagreement_open_block",
        "primary_authority_score_block",
        "counter_authority_pressure_block",
        "independent_crosscheck_block",
    )

    assert (watched.review_bucket, watched.status) == ("agency-review", "watch")
    assert watched.disagreement_age_seconds == d("2400.000000")
    assert watched.sla_score == d("0.888889")
    assert watched.crosscheck_score == d("0.500000")
    assert watched.resolution_readiness_score == d("0.672222")
    assert watched.reason_codes == (
        "primary_authority_disagreement_open_watch",
        "primary_authority_score_watch",
        "counter_authority_pressure_watch",
        "independent_crosscheck_watch",
    )

    assert (passed.review_bucket, passed.status) == ("official-consensus", "pass")
    assert passed.disagreement_age_seconds == d("0.000000")
    assert passed.sla_score == d("1.000000")
    assert passed.crosscheck_score == d("1.000000")
    assert passed.resolution_readiness_score == d("0.975000")
    assert passed.reason_codes == ("primary_authority_disagreement_sla_clear",)

    assert (
        "primary_authority_disagreement_sla_clear",
        d("1.000000"),
    ) in tuple((row.reason_code, row.count) for row in report.reason_code_counts)


def test_empty_report_is_pass_readonly_and_digest_checked() -> None:
    module = api()
    report = build_report()

    assert report.status == "pass"
    assert report.review_bucket_count == d("0.000000")
    assert report.open_disagreement_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.lowest_resolution_readiness_score == d("0.000000")
    assert report.highest_disagreement_age_seconds == d("0.000000")
    assert report.reason_codes == ("primary_authority_disagreement_sla_empty",)
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert report.derived_validation_digest == (
        module.research_source_primary_authority_disagreement_sla_report_digest(report)
    )
    assert (
        module.validate_research_source_primary_authority_disagreement_sla_report_digest(
            report,
        )
        is True
    )

    payload = module.research_source_primary_authority_disagreement_sla_report_payload(
        report,
    )
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert_no_public_numeric_values(payload)
    assert_payload_has_no_leaked_values(payload)


def test_payload_is_deterministic_json_ready_immutable_and_tamper_checked() -> None:
    module = api()
    report_a = build_report(
        signal("official-consensus"),
        signal(
            "manual-escalation",
            opened_seconds_ago=8000,
            primary_authority_score=d("0.300000"),
            counter_authority_pressure_score=d("0.700000"),
            independent_crosscheck_count=d("0.000000"),
        ),
    )
    report_b = build_report(
        signal(
            "manual-escalation",
            opened_seconds_ago=8000,
            primary_authority_score=d("0.300000"),
            counter_authority_pressure_score=d("0.700000"),
            independent_crosscheck_count=d("0.000000"),
        ),
        signal("official-consensus"),
    )

    payload_a = module.research_source_primary_authority_disagreement_sla_report_payload(
        report_a,
    )
    payload_b = module.research_source_primary_authority_disagreement_sla_report_payload(
        report_b,
    )
    digest_a = module.research_source_primary_authority_disagreement_sla_report_digest(
        report_a,
    )

    assert payload_a == payload_b
    assert digest_a == report_b.derived_validation_digest
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert payload_a["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload_a["review_bucket_count"] == "2.000000"
    assert payload_a["rows"][0]["review_bucket"] == "manual-escalation"
    assert payload_a["rows"][0]["resolution_readiness_score"] == "0.150000"
    json.dumps(payload_a, sort_keys=True, allow_nan=False)
    assert_no_public_numeric_values(payload_a)
    assert_payload_has_no_leaked_values(payload_a)
    module.validate_research_source_primary_authority_disagreement_sla_public_payload(
        payload_a,
    )

    with pytest.raises(TypeError, match="immutable"):
        payload_a["status"] = "pass"
    with pytest.raises(TypeError, match="immutable"):
        payload_a["rows"].append({})
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)

    tampered = dict(payload_a)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            tampered,
        )


def test_public_payload_validation_enforces_exact_nested_schema_and_types() -> None:
    module = api()
    report = build_report(signal("official-consensus"))

    unexpected_top_level = mutable_payload(report)
    unexpected_top_level["safe_extra"] = "safe"
    resign_payload(unexpected_top_level)
    with pytest.raises(ValueError, match="public payload schema"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            unexpected_top_level,
        )

    missing_top_level = mutable_payload(report)
    missing_top_level.pop("status")
    resign_payload(missing_top_level)
    with pytest.raises(ValueError, match="public payload schema"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            missing_top_level,
        )

    noncanonical_decimal = mutable_payload(report)
    noncanonical_decimal["review_bucket_count"] = "1"
    resign_payload(noncanonical_decimal)
    with pytest.raises(ValueError, match="review_bucket_count"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            noncanonical_decimal,
        )

    downgraded_flag = mutable_payload(report)
    downgraded_flag["paper_only"] = False
    resign_payload(downgraded_flag)
    with pytest.raises(ValueError, match="paper_only"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            downgraded_flag,
        )

    unexpected_row_surface = mutable_payload(report)
    unexpected_row_surface["rows"][0]["recommendation"] = "hold"
    resign_payload(unexpected_row_surface)
    with pytest.raises(ValueError, match="row schema|unsafe key"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            unexpected_row_surface,
        )

    missing_row_surface = mutable_payload(report)
    missing_row_surface["rows"][0].pop("status")
    resign_payload(missing_row_surface)
    with pytest.raises(ValueError, match="row schema"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            missing_row_surface,
        )

    unexpected_reason_count_surface = mutable_payload(report)
    unexpected_reason_count_surface["reason_code_counts"][0]["safe_extra"] = "safe"
    resign_payload(unexpected_reason_count_surface)
    with pytest.raises(ValueError, match="reason_code_count schema"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            unexpected_reason_count_surface,
        )

    noncanonical_nested_decimal = mutable_payload(report)
    noncanonical_nested_decimal["reason_code_counts"][0]["count"] = "1"
    resign_payload(noncanonical_nested_decimal)
    with pytest.raises(ValueError, match="count"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            noncanonical_nested_decimal,
        )


def test_public_report_apis_revalidate_bypassed_report_and_row_objects() -> None:
    module = api()

    malformed_report = build_report(signal("official-consensus"))
    malformed_report_payload = mutable_payload(malformed_report)
    malformed_report_payload["status"] = "watch"
    resign_payload(malformed_report_payload)
    object.__setattr__(malformed_report, "status", "watch")
    object.__setattr__(
        malformed_report,
        "derived_validation_digest",
        malformed_report_payload["derived_validation_digest"],
    )

    for public_api in (
        module.research_source_primary_authority_disagreement_sla_report_digest,
        module.validate_research_source_primary_authority_disagreement_sla_report_digest,
        module.research_source_primary_authority_disagreement_sla_report_payload,
    ):
        with pytest.raises(ValueError, match="status must match rows"):
            public_api(malformed_report)

    malformed_row_report = build_report(signal("official-consensus"))
    malformed_row_payload = mutable_payload(malformed_row_report)
    malformed_row_payload["rows"][0]["resolution_readiness_score"] = "0.500000"
    malformed_row_payload["lowest_resolution_readiness_score"] = "0.500000"
    resign_payload(malformed_row_payload)
    object.__setattr__(
        malformed_row_report.rows[0],
        "resolution_readiness_score",
        d("0.500000"),
    )
    object.__setattr__(
        malformed_row_report,
        "lowest_resolution_readiness_score",
        d("0.500000"),
    )
    object.__setattr__(
        malformed_row_report,
        "derived_validation_digest",
        malformed_row_payload["derived_validation_digest"],
    )

    for public_api in (
        module.research_source_primary_authority_disagreement_sla_report_digest,
        module.validate_research_source_primary_authority_disagreement_sla_report_digest,
        module.research_source_primary_authority_disagreement_sla_report_payload,
    ):
        with pytest.raises(
            ValueError,
            match="resolution_readiness_score must match component scores",
        ):
            public_api(malformed_row_report)


def test_resigned_payload_rejects_impossible_sla_score() -> None:
    module = api()

    forged_sla = mutable_payload(build_report(signal("official-consensus")))
    forged_sla["rows"][0]["sla_score"] = "0.000000"
    forged_sla["rows"][0]["resolution_readiness_score"] = "0.725000"
    forged_sla["lowest_resolution_readiness_score"] = "0.725000"
    resign_payload(forged_sla)
    with pytest.raises(
        ValueError,
        match="sla_score must be one without an open disagreement",
    ):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            forged_sla,
        )


def test_resigned_payload_rejects_impossible_crosscheck_score() -> None:
    module = api()

    forged_crosscheck = mutable_payload(
        build_report(
            signal(
                "zero-crosscheck",
                independent_crosscheck_count=d("0.000000"),
            ),
        ),
    )
    forged_crosscheck["rows"][0]["crosscheck_score"] = "1.000000"
    forged_crosscheck["rows"][0]["resolution_readiness_score"] = "0.975000"
    forged_crosscheck["lowest_resolution_readiness_score"] = "0.975000"
    resign_payload(forged_crosscheck)
    with pytest.raises(
        ValueError,
        match="crosscheck_score must be zero when independent_crosscheck_count is zero",
    ):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            forged_crosscheck,
        )


def test_resigned_payload_rejects_disagreement_age_mismatched_to_timestamp() -> None:
    module = api()

    forged_age = mutable_payload(
        build_report(signal("aged-review", opened_seconds_ago=2400)),
    )
    forged_age["rows"][0]["disagreement_age_seconds"] = "2401.000000"
    forged_age["highest_disagreement_age_seconds"] = "2401.000000"
    resign_payload(forged_age)
    with pytest.raises(
        ValueError,
        match="disagreement_age_seconds must match disagreement_opened_at",
    ):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            forged_age,
        )


def test_resigned_payload_rejects_clear_reason_combined_with_trigger() -> None:
    module = api()

    forged_clear = mutable_payload(build_report(signal("official-consensus")))
    forged_clear["rows"][0]["status"] = "watch"
    forged_clear["rows"][0]["reason_codes"] = [
        module.CLEAR_REASON,
        module.PRIMARY_AUTHORITY_WATCH_REASON,
    ]
    forged_clear["pass_count"] = "0.000000"
    forged_clear["watch_count"] = "1.000000"
    forged_clear["weak_primary_authority_count"] = "1.000000"
    forged_clear["status"] = "watch"
    forged_clear["reason_codes"] = [module.PRIMARY_AUTHORITY_WATCH_REASON]
    forged_clear["reason_code_counts"].append(
        {
            "reason_code": module.PRIMARY_AUTHORITY_WATCH_REASON,
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    resign_payload(forged_clear)
    with pytest.raises(ValueError, match="clear reason must be exclusive"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            forged_clear,
        )


def test_resigned_payload_rejects_crosscheck_reason_mismatched_to_zero_count() -> None:
    module = api()

    forged_crosscheck_reason = mutable_payload(
        build_report(
            signal(
                "zero-crosscheck",
                independent_crosscheck_count=d("0.000000"),
            ),
        ),
    )
    forged_crosscheck_reason["rows"][0]["status"] = "pass"
    forged_crosscheck_reason["rows"][0]["reason_codes"] = [module.CLEAR_REASON]
    forged_crosscheck_reason["pass_count"] = "1.000000"
    forged_crosscheck_reason["block_count"] = "0.000000"
    forged_crosscheck_reason["low_independent_crosscheck_count"] = "0.000000"
    forged_crosscheck_reason["status"] = "pass"
    forged_crosscheck_reason["reason_codes"] = [module.CLEAR_REASON]
    forged_crosscheck_reason["reason_code_counts"] = [
        {
            "reason_code": module.CLEAR_REASON,
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    resign_payload(forged_crosscheck_reason)
    with pytest.raises(
        ValueError,
        match="independent crosscheck reason_codes must match count",
    ):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            forged_crosscheck_reason,
        )


def test_resigned_payload_rejects_mutually_exclusive_primary_reasons() -> None:
    module = api()

    forged_primary_reasons = mutable_payload(
        build_report(
            signal(
                "weak-primary",
                primary_authority_score=d("0.300000"),
            ),
        ),
    )
    forged_primary_reasons["rows"][0]["reason_codes"].append(
        module.PRIMARY_AUTHORITY_WATCH_REASON,
    )
    forged_primary_reasons["reason_codes"].append(
        module.PRIMARY_AUTHORITY_WATCH_REASON,
    )
    forged_primary_reasons["reason_code_counts"].append(
        {
            "reason_code": module.PRIMARY_AUTHORITY_WATCH_REASON,
            "count": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    resign_payload(forged_primary_reasons)
    with pytest.raises(ValueError, match="primary authority reasons are mutually exclusive"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            forged_primary_reasons,
        )


def test_resigned_payload_rejects_primary_reason_mismatched_to_score() -> None:
    module = api()

    forged_primary_score = mutable_payload(
        build_report(signal("official-consensus")),
    )
    forged_primary_score["rows"][0]["primary_authority_score"] = "0.300000"
    forged_primary_score["rows"][0]["resolution_readiness_score"] = "0.812500"
    forged_primary_score["lowest_resolution_readiness_score"] = "0.812500"
    resign_payload(forged_primary_score)
    with pytest.raises(ValueError, match="reason_codes must match row inputs"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            forged_primary_score,
        )


def test_resigned_payload_rejects_counter_reason_mismatched_to_score() -> None:
    module = api()

    forged_counter_score = mutable_payload(
        build_report(signal("official-consensus")),
    )
    forged_counter_score["rows"][0]["counter_authority_pressure_score"] = "0.700000"
    forged_counter_score["rows"][0]["resolution_readiness_score"] = "0.812500"
    forged_counter_score["highest_counter_authority_pressure_score"] = "0.700000"
    forged_counter_score["lowest_resolution_readiness_score"] = "0.812500"
    resign_payload(forged_counter_score)
    with pytest.raises(ValueError, match="reason_codes must match row inputs"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            forged_counter_score,
        )


def test_resigned_payload_rejects_watch_sla_score_mismatched_to_age() -> None:
    module = api()

    forged_sla_score = mutable_payload(
        build_report(signal("aged-review", opened_seconds_ago=2400)),
    )
    forged_sla_score["rows"][0]["sla_score"] = "0.500000"
    forged_sla_score["rows"][0]["resolution_readiness_score"] = "0.850000"
    forged_sla_score["lowest_resolution_readiness_score"] = "0.850000"
    resign_payload(forged_sla_score)
    with pytest.raises(ValueError, match="sla_score must match disagreement age"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            forged_sla_score,
        )


def test_resigned_payload_rejects_crosscheck_score_mismatched_to_count() -> None:
    module = api()

    forged_crosscheck_score = mutable_payload(
        build_report(
            signal(
                "thin-crosscheck",
                independent_crosscheck_count=d("1.000000"),
            ),
        ),
    )
    forged_crosscheck_score["rows"][0]["crosscheck_score"] = "0.750000"
    forged_crosscheck_score["rows"][0]["resolution_readiness_score"] = "0.912500"
    forged_crosscheck_score["lowest_resolution_readiness_score"] = "0.912500"
    resign_payload(forged_crosscheck_score)
    with pytest.raises(
        ValueError,
        match="crosscheck_score must match independent_crosscheck_count",
    ):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            forged_crosscheck_score,
        )


def test_resigned_payload_rejects_unsupported_config_version() -> None:
    module = api()

    forged_config_version = mutable_payload(
        build_report(signal("official-consensus")),
    )
    forged_config_version["config_version"] = "forged-config-v1"
    resign_payload(forged_config_version)
    with pytest.raises(ValueError, match="config_version must be the supported"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            forged_config_version,
        )


def test_config_rejects_signed_zero() -> None:
    with pytest.raises(ValueError, match="signed zero"):
        config(counter_authority_watch_pressure=d("-0.000000"))


def test_signal_rejects_signed_zero() -> None:
    with pytest.raises(ValueError, match="signed zero"):
        signal(
            "official-consensus",
            primary_authority_score=d("-0.000000"),
        )


def test_reason_code_count_rejects_signed_zero() -> None:
    module = api()

    with pytest.raises(ValueError, match="signed zero"):
        module.ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount(
            reason_code=module.CLEAR_REASON,
            count=d("-0.000000"),
        )


def test_config_rejects_fractional_whole_decimal_before_quantizing() -> None:
    with pytest.raises(ValueError, match="whole Decimal"):
        config(minimum_independent_crosscheck_count=d("2.0000001"))


def test_signal_rejects_fractional_whole_decimal_before_quantizing() -> None:
    with pytest.raises(ValueError, match="whole Decimal"):
        signal(
            "official-consensus",
            independent_crosscheck_count=d("1.0000004"),
        )


def test_resigned_payload_rejects_signed_zero() -> None:
    module = api()

    forged_signed_zero = mutable_payload(build_report())
    forged_signed_zero["review_bucket_count"] = "-0.000000"
    resign_payload(forged_signed_zero)
    with pytest.raises(ValueError, match="signed zero"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            forged_signed_zero,
        )


def test_all_public_dataclasses_are_frozen_exact_schema_values() -> None:
    module = api()
    report = build_report(signal("official-consensus"))
    values = (
        config(),
        signal("official-consensus"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )

    for value in values:
        assert is_dataclass(value)
        assert type(value).__dataclass_params__.frozen is True
        first_field = fields(type(value))[0].name
        with pytest.raises(FrozenInstanceError):
            setattr(value, first_field, getattr(value, first_field))

    assert tuple(field.name for field in fields(type(config()))) == (
        "config_version",
        "disagreement_watch_age_seconds",
        "disagreement_block_age_seconds",
        "primary_authority_watch_threshold",
        "primary_authority_block_threshold",
        "counter_authority_watch_pressure",
        "counter_authority_block_pressure",
        "minimum_independent_crosscheck_count",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(field.name for field in fields(type(signal("official-consensus")))) == (
        "review_bucket",
        "disagreement_opened_at",
        "primary_authority_score",
        "counter_authority_pressure_score",
        "independent_crosscheck_count",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(field.name for field in fields(type(report.rows[0]))) == (
        "review_bucket",
        "disagreement_opened_at",
        "disagreement_age_seconds",
        "primary_authority_score",
        "counter_authority_pressure_score",
        "independent_crosscheck_count",
        "sla_score",
        "crosscheck_score",
        "resolution_readiness_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(field.name for field in fields(type(report.reason_code_counts[0]))) == (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(field.name for field in fields(type(report))) == (
        "generated_at",
        "config_version",
        "review_bucket_count",
        "open_disagreement_count",
        "pass_count",
        "watch_count",
        "block_count",
        "overdue_disagreement_count",
        "weak_primary_authority_count",
        "counter_authority_pressure_count",
        "low_independent_crosscheck_count",
        "lowest_resolution_readiness_score",
        "highest_disagreement_age_seconds",
        "highest_counter_authority_pressure_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert module._PUBLIC_REPORT_SCHEMA == tuple(  # noqa: SLF001
        field.name for field in fields(type(report))
    )


def test_builder_revalidates_bypassed_config_before_reducing() -> None:
    malformed_config = config()
    object.__setattr__(
        malformed_config,
        "disagreement_watch_age_seconds",
        d("9000.000000"),
    )

    with pytest.raises(ValueError, match="disagreement_block_age_seconds"):
        build_report(cfg=malformed_config)


def test_custom_config_report_payload_round_trips_with_explicit_validation_config() -> None:
    module = api()
    custom_config = config(
        disagreement_watch_age_seconds=d("100.000000"),
        disagreement_block_age_seconds=d("200.000000"),
        primary_authority_watch_threshold=d("0.900000"),
        primary_authority_block_threshold=d("0.800000"),
        counter_authority_watch_pressure=d("0.100000"),
        counter_authority_block_pressure=d("0.200000"),
        minimum_independent_crosscheck_count=d("4.000000"),
    )
    report = build_report(
        signal(
            "custom-threshold-review",
            opened_seconds_ago=150,
            primary_authority_score=d("0.850000"),
            counter_authority_pressure_score=d("0.150000"),
            independent_crosscheck_count=d("2.000000"),
        ),
        cfg=custom_config,
    )

    assert report.rows[0].sla_score == d("0.500000")
    assert report.rows[0].crosscheck_score == d("0.500000")
    payload = module.research_source_primary_authority_disagreement_sla_report_payload(
        report,
    )
    assert (
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            payload,
            config=custom_config,
        )
        is True
    )
    with pytest.raises(ValueError, match="sla_score must match disagreement age"):
        module.validate_research_source_primary_authority_disagreement_sla_public_payload(
            payload,
        )


def test_validation_rejects_bad_decimal_types_flags_timestamps_and_public_surfaces() -> None:
    module = api()

    assert signal("opposition-review").review_bucket == "opposition-review"
    with pytest.raises(ValueError, match="disagreement_watch_age_seconds"):
        config(disagreement_watch_age_seconds=1800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="primary_authority_watch_threshold"):
        config(primary_authority_watch_threshold=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="disagreement_block_age_seconds"):
        config(disagreement_block_age_seconds=d("1800.000000"))
    with pytest.raises(ValueError, match="review_bucket"):
        signal("market_slug_2026")
    with pytest.raises(ValueError, match="review_bucket"):
        signal("https://example.invalid/source")
    with pytest.raises(ValueError, match="review_bucket"):
        signal("candidate_id_123")
    with pytest.raises(ValueError, match="primary_authority_score"):
        signal("official-consensus", primary_authority_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="counter_authority_pressure_score"):
        signal(
            "official-consensus",
            counter_authority_pressure_score=_DecimalSubclass("0.300000"),
        )
    with pytest.raises(ValueError, match="independent_crosscheck_count"):
        signal("official-consensus", independent_crosscheck_count=d("1.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_primary_authority_disagreement_sla_report(
            (signal("official-consensus"),),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="disagreement_opened_at"):
        build_report(signal("future-gap", opened_seconds_ago=-1))
    with pytest.raises(ValueError, match="paper_only"):
        signal("official-consensus", paper_only=False)

    report = build_report(signal("official-consensus"))
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(TypeError):
        class _BadRow(module.ResearchSourcePrimaryAuthorityDisagreementSlaRow):  # type: ignore[misc, valid-type]
            pass


def test_public_api_and_module_scope_stay_report_only_and_safe() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_PRIMARY_AUTHORITY_DISAGREEMENT_SLA_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_PRIMARY_AUTHORITY_DISAGREEMENT_SLA_STATUSES",
        "ResearchSourcePrimaryAuthorityDisagreementSlaConfig",
        "ResearchSourcePrimaryAuthorityDisagreementSlaReasonCodeCount",
        "ResearchSourcePrimaryAuthorityDisagreementSlaReport",
        "ResearchSourcePrimaryAuthorityDisagreementSlaRow",
        "ResearchSourcePrimaryAuthorityDisagreementSlaSignal",
        "build_research_source_primary_authority_disagreement_sla_report",
        "research_source_primary_authority_disagreement_sla_report_digest",
        "research_source_primary_authority_disagreement_sla_report_payload",
        "validate_research_source_primary_authority_disagreement_sla_public_payload",
        "validate_research_source_primary_authority_disagreement_sla_report_digest",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(signal("official-consensus"))
    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "recommendation",
        "recommended_action",
        "position_size",
        "suggested_notional",
        "stake",
    }
    exported_fields = {
        field.name
        for cls in (
            type(config()),
            type(signal("official-consensus")),
            type(report),
            type(report.rows[0]),
        )
        for field in fields(cls)
    }
    assert unsafe_keys.isdisjoint(exported_fields)

    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_primary_authority_disagreement_sla_report.py"
    )
    source = source_path.read_text()
    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncpg",
        "aiohttp",
        "boto3",
        "httpx",
        "pathlib",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "write",
                "write_text",
                "write_bytes",
            }

    assert imported_roots.isdisjoint(forbidden_import_roots)
    payload = module.research_source_primary_authority_disagreement_sla_report_payload(
        report,
    )
    assert_payload_has_no_leaked_values(payload)

    for unsafe_payload in (
        {"candidate_id": "safe"},
        {"safe": "https://example.invalid/source"},
        {"safe": "wallet token"},
        {"safe": "live order trade"},
        {"table_name": "public_summary"},
    ):
        with pytest.raises(ValueError, match="public payload"):
            module.validate_research_source_primary_authority_disagreement_sla_public_payload(
                {
                    **dict(payload),
                    **unsafe_payload,
                    "derived_validation_digest": payload["derived_validation_digest"],
                },
            )


def assert_no_public_numeric_values(payload: object) -> None:
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))


def assert_payload_has_no_leaked_values(payload: object) -> None:
    unsafe_fragments = (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    for key, value in _walk_payload_items(payload):
        lowered_key = key.lower()
        assert not any(fragment in lowered_key for fragment in unsafe_fragments)
        if type(value) is str:
            lowered_value = value.lower()
            assert not any(fragment in lowered_value for fragment in unsafe_fragments)


def _walk_payload_items(value: object) -> tuple[tuple[str, object], ...]:
    items: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            items.append((key, item))
            items.extend(_walk_payload_items(item))
        return tuple(items)
    if isinstance(value, list | tuple):
        for item in value:
            items.extend(_walk_payload_items(item))
    return tuple(items)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list | tuple):
        for item in value:
            values.extend(_walk_payload_values(item))
    return tuple(values)
