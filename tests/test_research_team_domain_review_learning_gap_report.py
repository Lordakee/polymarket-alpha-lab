from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_team_domain_review_learning_gap_report"
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "unresolved_corrections_watch_threshold": d("1"),
        "unresolved_corrections_block_threshold": d("3"),
        "stale_memory_reuse_watch_threshold": d("1"),
        "stale_memory_reuse_block_threshold": d("2"),
        "calibration_drift_watch_threshold": d("0.150000"),
        "calibration_drift_block_threshold": d("0.300000"),
        "evidence_coverage_pass_threshold": d("0.850000"),
        "evidence_coverage_block_threshold": d("0.500000"),
        "peer_review_depth_pass_threshold": d("2"),
        "peer_review_depth_block_threshold": d("1"),
        "review_latency_watch_hours": d("48.000000"),
        "review_latency_block_hours": d("96.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainReviewLearningGapConfig(**values)


def review(**overrides: object) -> Any:
    module = api()
    values = {
        "review_key": "private-review-alpha",
        "domain_key": "private-domain-alpha",
        "unresolved_corrections": d("0"),
        "stale_memory_reuse_count": d("0"),
        "calibration_drift": d("0.050000"),
        "evidence_coverage_ratio": d("0.950000"),
        "peer_review_depth": d("3"),
        "review_latency_hours": d("12.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainReviewLearningGapInput(**values)


def report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_team_domain_review_learning_gap_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool or item is None or type(item) is str:
            continue
        if isinstance(item, datetime):
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)
            continue
        if field.name.endswith("_count") or field.name.endswith("_hours"):
            assert type(item) is Decimal
        elif isinstance(item, Decimal):
            assert type(item) is Decimal


def assert_no_float_or_int_values(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def canonical_digest(values: dict[str, Any]) -> str:
    encoded = json.dumps(values, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("results")
    if type(rows) is list:
        for row in rows:
            if type(row) is dict:
                unsigned_row = {
                    key: value
                    for key, value in row.items()
                    if key != "validation_digest"
                }
                row["validation_digest"] = canonical_digest(unsigned_row)
    unsigned_report = {
        key: value
        for key, value in payload.items()
        if key != "validation_digest"
    }
    payload["validation_digest"] = canonical_digest(unsigned_report)
    return payload


def cloned_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(payload))


def with_first_key_moved_to_end(payload: dict[str, Any]) -> dict[str, Any]:
    first_key, *remaining_keys = tuple(payload)
    return {key: payload[key] for key in (*remaining_keys, first_key)}


def set_payload_path(payload: dict[str, Any], path: tuple[str | int, ...], value: Any) -> None:
    target: Any = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def test_learning_gap_report_blocks_watches_and_passes_deterministically() -> None:
    result = report(
        review(
            review_key="pass-review-secret",
            domain_key="pass-domain-secret",
            unresolved_corrections=d("0"),
            stale_memory_reuse_count=d("0"),
            calibration_drift=d("0.050000"),
            evidence_coverage_ratio=d("0.950000"),
            peer_review_depth=d("3"),
            review_latency_hours=d("12.000000"),
        ),
        review(
            review_key="watch-review-secret",
            domain_key="watch-domain-secret",
            unresolved_corrections=d("1"),
            stale_memory_reuse_count=d("1"),
            calibration_drift=d("0.200000"),
            evidence_coverage_ratio=d("0.700000"),
            peer_review_depth=d("1"),
            review_latency_hours=d("72.000000"),
        ),
        review(
            review_key="block-review-secret",
            domain_key="block-domain-secret",
            unresolved_corrections=d("3"),
            stale_memory_reuse_count=d("2"),
            calibration_drift=d("0.400000"),
            evidence_coverage_ratio=d("0.400000"),
            peer_review_depth=d("0"),
            review_latency_hours=d("120.000000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-team-domain-review-learning-gap-report-v1"
    assert result.review_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.report_status == "block"
    assert result.reason_codes == (
        "unresolved_corrections_block",
        "unresolved_corrections_watch",
        "stale_memory_reuse_block",
        "stale_memory_reuse_watch",
        "calibration_drift_block",
        "calibration_drift_watch",
        "evidence_coverage_block",
        "evidence_coverage_watch",
        "peer_review_depth_block",
        "peer_review_depth_watch",
        "review_latency_block",
        "review_latency_watch",
        "domain_review_learning_gap_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.review_status for row in result.results) == ("block", "watch", "pass")

    blocked = result.results[0]
    assert blocked.learning_gap_score == d("0.933333")
    assert blocked.review_status == "block"
    assert blocked.reason_codes == (
        "unresolved_corrections_block",
        "stale_memory_reuse_block",
        "calibration_drift_block",
        "evidence_coverage_block",
        "peer_review_depth_block",
        "review_latency_block",
    )
    assert_digest(blocked.review_fingerprint)
    assert_digest(blocked.domain_fingerprint)
    assert_digest(blocked.validation_digest)

    watched = result.results[1]
    assert watched.learning_gap_score == d("0.508333")
    assert watched.review_status == "watch"

    passed = result.results[2]
    assert passed.learning_gap_score == d("0.056944")
    assert passed.review_status == "pass"
    assert passed.reason_codes == ("domain_review_learning_gap_pass",)

    same_result = report(
        review(
            review_key="pass-review-secret",
            domain_key="pass-domain-secret",
            unresolved_corrections=d("0"),
            stale_memory_reuse_count=d("0"),
            calibration_drift=d("0.050000"),
            evidence_coverage_ratio=d("0.950000"),
            peer_review_depth=d("3"),
            review_latency_hours=d("12.000000"),
        ),
        review(
            review_key="watch-review-secret",
            domain_key="watch-domain-secret",
            unresolved_corrections=d("1"),
            stale_memory_reuse_count=d("1"),
            calibration_drift=d("0.200000"),
            evidence_coverage_ratio=d("0.700000"),
            peer_review_depth=d("1"),
            review_latency_hours=d("72.000000"),
        ),
        review(
            review_key="block-review-secret",
            domain_key="block-domain-secret",
            unresolved_corrections=d("3"),
            stale_memory_reuse_count=d("2"),
            calibration_drift=d("0.400000"),
            evidence_coverage_ratio=d("0.400000"),
            peer_review_depth=d("0"),
            review_latency_hours=d("120.000000"),
        ),
    )
    assert same_result.validation_digest == result.validation_digest


def test_empty_report_is_blocked_readonly_and_decimal_zeroed() -> None:
    result = report()

    assert result.review_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.report_status == "block"
    assert result.reason_codes == ("research_team_domain_review_learning_gap_report_empty",)
    assert result.results == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)


def test_reason_code_counts_are_public_decimal_aggregate_objects() -> None:
    module = api()
    result = report(
        review(
            review_key="reason-count-watch-alpha",
            unresolved_corrections=d("1"),
        ),
        review(
            review_key="reason-count-watch-beta",
            unresolved_corrections=d("1"),
        ),
        review(review_key="reason-count-pass"),
    )

    assert result.reason_code_counts == (
        module.ResearchTeamDomainReviewLearningGapReasonCodeCount(
            "unresolved_corrections_watch",
            d("2"),
        ),
        module.ResearchTeamDomainReviewLearningGapReasonCodeCount(
            "domain_review_learning_gap_pass",
            d("1"),
        ),
    )

    payload = module.research_team_domain_review_learning_gap_report_payload(result)
    assert payload["reason_code_counts"] == [
        {
            "reason_code": "unresolved_corrections_watch",
            "count": "2",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "reason_code": "domain_review_learning_gap_pass",
            "count": "1",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]


def test_payload_is_json_ready_and_excludes_private_surfaces() -> None:
    module = api()
    raw_private = (
        "candidate-alpha|market-123|event-slug|Will this happen?|"
        "https://example.test/feed?token=secret"
    )
    result = report(
        review(
            review_key=raw_private,
            domain_key="orders-table-dsn-private",
        ),
    )

    payload = module.research_team_domain_review_learning_gap_report_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["review_count"] == "1"
    assert payload["results"][0]["unresolved_corrections"] == "0"
    assert payload["results"][0]["review_latency_hours"] == "12.000000"
    assert payload["results"][0]["validation_digest"] == result.results[0].validation_digest
    assert raw_private not in encoded
    assert "candidate-alpha" not in encoded
    assert "market-123" not in encoded
    assert "event-slug" not in encoded
    assert "Will this happen?" not in encoded
    assert "https://example.test" not in encoded
    assert "token=secret" not in encoded
    assert "orders-table-dsn-private" not in encoded
    assert_no_float_or_int_values(payload)
    assert module.research_team_domain_review_learning_gap_report_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly"):
        module.research_team_domain_review_learning_gap_report_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_domain_review_learning_gap_report_payload(
            {**payload, "candidate_id": "raw-candidate"},
        )

    with pytest.raises(ValueError, match="numeric"):
        module.research_team_domain_review_learning_gap_report_payload(
            {**payload, "review_count": 1},
        )

    with pytest.raises(ValueError, match="numeric"):
        module.research_team_domain_review_learning_gap_report_payload(
            {**payload, "pass_count": 1.0},
        )


def test_inputs_config_and_datetimes_reject_invalid_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="unresolved_corrections must be a Decimal"):
        review(unresolved_corrections=1)
    with pytest.raises(ValueError, match="unresolved_corrections must be an integer"):
        review(unresolved_corrections=d("1.5"))
    with pytest.raises(ValueError, match="evidence_coverage_ratio must be between 0 and 1"):
        review(evidence_coverage_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="peer_review_depth must be nonnegative"):
        review(peer_review_depth=d("-1"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        review(paper_only=False)
    with pytest.raises(ValueError, match="watch threshold must not exceed block threshold"):
        config(
            calibration_drift_watch_threshold=d("0.400000"),
            calibration_drift_block_threshold=d("0.300000"),
        )
    with pytest.raises(ValueError, match="block threshold must not exceed pass threshold"):
        config(
            evidence_coverage_block_threshold=d("0.900000"),
            evidence_coverage_pass_threshold=d("0.850000"),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_team_domain_review_learning_gap_report(
            (review(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_team_domain_review_learning_gap_report(
            (review(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="review_key values must be unique"):
        report(review(), review())

    result = report(review())
    with pytest.raises(FrozenInstanceError):
        result.results[0].review_status = "block"


@pytest.mark.parametrize(
    "generated_at",
    (
        datetime.min.replace(tzinfo=timezone(timedelta(hours=1))),
        datetime.max.replace(tzinfo=timezone(timedelta(hours=-1))),
    ),
)
def test_generated_at_rejects_utc_conversion_overflow(generated_at: datetime) -> None:
    module = api()

    with pytest.raises(ValueError, match="UTC datetime boundary"):
        module.build_research_team_domain_review_learning_gap_report(
            (review(),),
            config=config(),
            generated_at=generated_at,
        )


def test_validation_digest_and_report_validation_recompute_fields() -> None:
    result = report(review())
    row = result.results[0]

    with pytest.raises(ValueError, match="learning_gap_score must match"):
        replace(row, learning_gap_score=row.learning_gap_score + d("0.000001"))

    with pytest.raises(ValueError, match="review_status must match"):
        replace(row, review_status="block")

    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)

    with pytest.raises(ValueError, match="pass_count must match"):
        replace(result, pass_count=result.pass_count + d("1"))

    with pytest.raises(ValueError, match="results must be sorted deterministically"):
        replace(
            result,
            review_count=d("2"),
            pass_count=d("2"),
            max_learning_gap_score=d("0.056944"),
            results=(
                domain_review_result("review-alpha"),
                domain_review_result("review-zeta"),
            ),
        )

    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)


def test_result_rejects_resigned_unsupported_reason_code() -> None:
    module = api()
    original = domain_review_result("unsupported-reason-result")
    values = {
        field.name: getattr(original, field.name)
        for field in fields(original)
    }
    values["review_status"] = "watch"
    values["reason_codes"] = ("unexpected_safe_reason",)
    values["validation_digest"] = module._validation_digest(
        {
            field_name: value
            for field_name, value in values.items()
            if field_name != "validation_digest"
        },
    )

    with pytest.raises(ValueError, match="supported reason code"):
        module.ResearchTeamDomainReviewLearningGapResult(**values)


def test_reason_count_rejects_unsupported_reason_code() -> None:
    module = api()

    with pytest.raises(ValueError, match="supported reason code"):
        module.ResearchTeamDomainReviewLearningGapReasonCodeCount(
            "unexpected_safe_reason",
            d("1"),
        )


def test_decimal_arithmetic_uses_a_fixed_local_context() -> None:
    values = {
        "review_key": "fixed-context-review",
        "domain_key": "fixed-context-domain",
        "unresolved_corrections": d("1"),
        "stale_memory_reuse_count": d("1"),
        "calibration_drift": d("0.200000"),
        "evidence_coverage_ratio": d("0.700000"),
        "peer_review_depth": d("1"),
        "review_latency_hours": d("72.000000"),
    }
    expected = report(review(**values))

    with localcontext() as ambient:
        ambient.prec = 2
        ambient.rounding = ROUND_DOWN
        ambient.traps[Inexact] = True
        actual = report(review(**values))

    assert actual == expected


def test_raw_decimal_bounds_subclasses_nonfinite_and_signed_zero_are_rejected() -> None:
    with pytest.raises(ValueError, match="signed zero"):
        review(peer_review_depth=d("-0"))
    with pytest.raises(ValueError, match="signed zero"):
        review(review_latency_hours=d("-0.000000"))
    with pytest.raises(ValueError, match="finite"):
        review(calibration_drift=d("NaN"))
    with pytest.raises(ValueError, match="finite"):
        review(calibration_drift=d("Infinity"))
    with pytest.raises(ValueError, match="Decimal"):
        review(calibration_drift=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        review(calibration_drift=d("1.0000004"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        review(evidence_coverage_ratio=d("-0.0000004"))
    with pytest.raises(ValueError, match="positive"):
        config(review_latency_watch_hours=d("0.0000004"))


def test_decimal_quantization_overflow_has_stable_fixed_context_error() -> None:
    with pytest.raises(ValueError, match="fixed Decimal context"):
        review(review_latency_hours=d("1E+64"))


def test_count_quantization_overflow_has_stable_fixed_context_error() -> None:
    with pytest.raises(ValueError, match="fixed Decimal context"):
        review(unresolved_corrections=d("1E+64"))


def test_internal_decimal_arithmetic_canonicalizes_signed_zero() -> None:
    module = api()
    zero_values = (
        module._negative_decimal(d("0.000000")),
        module._quantize(d("-0.0000004")),
        module._quantize_count(d("-0.4")),
    )

    assert all(value.is_zero() for value in zero_values)
    assert not any(value.is_signed() for value in zero_values)


def test_public_dataclasses_are_frozen_and_non_subclassable() -> None:
    module = api()
    public_classes = (
        module.ResearchTeamDomainReviewLearningGapConfig,
        module.ResearchTeamDomainReviewLearningGapInput,
        module.ResearchTeamDomainReviewLearningGapReasonCodeCount,
        module.ResearchTeamDomainReviewLearningGapResult,
        module.ResearchTeamDomainReviewLearningGapReport,
    )

    for public_class in public_classes:
        assert is_dataclass(public_class)
        assert public_class.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="subclass"):
            type(f"Bad{public_class.__name__}", (public_class,), {})


def test_public_dataclass_post_init_rejects_exact_type_impostors() -> None:
    module = api()
    instances = (
        (module.ResearchTeamDomainReviewLearningGapConfig, config()),
        (module.ResearchTeamDomainReviewLearningGapInput, review()),
        (
            module.ResearchTeamDomainReviewLearningGapReasonCodeCount,
            module.ResearchTeamDomainReviewLearningGapReasonCodeCount(
                "domain_review_learning_gap_pass",
                d("1"),
            ),
        ),
        (
            module.ResearchTeamDomainReviewLearningGapResult,
            domain_review_result("exact-type-result"),
        ),
        (
            module.ResearchTeamDomainReviewLearningGapReport,
            report(review(review_key="exact-type-report")),
        ),
    )

    for public_class, instance in instances:
        impostor = SimpleNamespace(
            **{
                field.name: getattr(instance, field.name)
                for field in fields(instance)
            },
        )
        with pytest.raises(ValueError, match="must be exactly"):
            public_class.__post_init__(impostor)


def test_object_setattr_revalidation_catches_config_input_reason_count_and_nested_row() -> None:
    module = api()

    mutated_config = config()
    object.__setattr__(
        mutated_config,
        "review_latency_watch_hours",
        d("-0.000000"),
    )
    with pytest.raises(ValueError, match="signed zero"):
        mutated_config.__post_init__()

    mutated_input = review()
    object.__setattr__(mutated_input, "calibration_drift", d("NaN"))
    with pytest.raises(ValueError, match="finite"):
        mutated_input.__post_init__()

    mutated_reason_count = module.ResearchTeamDomainReviewLearningGapReasonCodeCount(
        "domain_review_learning_gap_pass",
        d("1"),
    )
    object.__setattr__(mutated_reason_count, "count", d("-0"))
    with pytest.raises(ValueError, match="signed zero"):
        mutated_reason_count.__post_init__()

    mutated_report = report(review())
    object.__setattr__(mutated_report.results[0], "validation_digest", "0" * 64)
    object.__setattr__(
        mutated_report,
        "validation_digest",
        module._validation_digest(module._report_digest_values(mutated_report)),
    )
    with pytest.raises(ValueError, match="validation_digest"):
        mutated_report.__post_init__()


def test_build_rejects_config_modified_after_initialization() -> None:
    mutated_config = config()
    object.__setattr__(
        mutated_config,
        "calibration_drift_watch_threshold",
        d("0.200000"),
    )

    with pytest.raises(ValueError, match="config was modified after initialization"):
        report(review(), cfg=mutated_config)


def test_build_rejects_input_modified_after_initialization() -> None:
    mutated_review = review(review_key="original-private-review")
    object.__setattr__(mutated_review, "review_key", "substituted-private-review")

    with pytest.raises(ValueError, match="input was modified after initialization"):
        report(mutated_review)


def test_payload_rejects_resigned_result_modified_after_initialization() -> None:
    module = api()
    mutated_report = report(review())
    mutated_result = mutated_report.results[0]
    object.__setattr__(mutated_result, "domain_fingerprint", "f" * 64)
    object.__setattr__(
        mutated_result,
        "validation_digest",
        module._validation_digest(module._result_digest_values(mutated_result)),
    )
    object.__setattr__(
        mutated_report,
        "validation_digest",
        module._validation_digest(module._report_digest_values(mutated_report)),
    )

    with pytest.raises(ValueError, match="result was modified after initialization"):
        module.research_team_domain_review_learning_gap_report_payload(mutated_report)


def test_reason_count_revalidation_rejects_post_initialization_change() -> None:
    module = api()
    mutated_count = module.ResearchTeamDomainReviewLearningGapReasonCodeCount(
        "domain_review_learning_gap_pass",
        d("1"),
    )
    object.__setattr__(mutated_count, "count", d("2"))

    with pytest.raises(ValueError, match="modified after initialization"):
        mutated_count.__post_init__()


def test_payload_rejects_reason_count_modified_after_initialization() -> None:
    module = api()
    mutated_report = report(review())
    object.__setattr__(mutated_report.reason_code_counts[0], "count", d("1.0"))
    object.__setattr__(
        mutated_report,
        "validation_digest",
        module._validation_digest(module._report_digest_values(mutated_report)),
    )

    with pytest.raises(ValueError, match="reason count was modified after initialization"):
        module.research_team_domain_review_learning_gap_report_payload(mutated_report)


def test_payload_rejects_resigned_report_modified_after_initialization() -> None:
    module = api()
    mutated_report = report(review())
    object.__setattr__(
        mutated_report,
        "generated_at",
        mutated_report.generated_at + timedelta(seconds=1),
    )
    object.__setattr__(
        mutated_report,
        "validation_digest",
        module._validation_digest(module._report_digest_values(mutated_report)),
    )

    with pytest.raises(ValueError, match="report was modified after initialization"):
        module.research_team_domain_review_learning_gap_report_payload(mutated_report)


def test_payload_rejects_undeclared_report_attribute() -> None:
    module = api()
    mutated_report = report(review())
    object.__setattr__(mutated_report, "safe_extra", "unexpected")

    with pytest.raises(ValueError, match="report was modified after initialization"):
        module.research_team_domain_review_learning_gap_report_payload(mutated_report)


def test_payload_rejects_deleted_report_attribute_with_stable_error() -> None:
    module = api()
    mutated_report = report(review())
    object.__delattr__(mutated_report, "validation_digest")

    with pytest.raises(ValueError, match="report was modified after initialization"):
        module.research_team_domain_review_learning_gap_report_payload(mutated_report)


def test_config_version_is_fixed_for_objects_and_resigned_payloads() -> None:
    module = api()

    with pytest.raises(ValueError, match="supported config version"):
        config(config_version="research-team-domain-review-learning-gap-report-v2")

    payload = module.research_team_domain_review_learning_gap_report_payload(
        report(review()),
    )
    forged = cloned_payload(payload)
    forged["config_version"] = "research-team-domain-review-learning-gap-report-v2"
    resign_payload(forged)

    with pytest.raises(ValueError, match="supported config version"):
        module.research_team_domain_review_learning_gap_report_payload(forged)


def test_payload_requires_exact_canonical_report_and_result_schema() -> None:
    module = api()
    payload = module.research_team_domain_review_learning_gap_report_payload(
        report(review()),
    )
    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "unresolved_corrections_watch_threshold",
        "unresolved_corrections_block_threshold",
        "stale_memory_reuse_watch_threshold",
        "stale_memory_reuse_block_threshold",
        "calibration_drift_watch_threshold",
        "calibration_drift_block_threshold",
        "evidence_coverage_pass_threshold",
        "evidence_coverage_block_threshold",
        "peer_review_depth_pass_threshold",
        "peer_review_depth_block_threshold",
        "review_latency_watch_hours",
        "review_latency_block_hours",
        "review_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_learning_gap_score",
        "report_status",
        "reason_codes",
        "reason_code_counts",
        "results",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["results"][0]) == (
        "review_fingerprint",
        "domain_fingerprint",
        "unresolved_corrections",
        "stale_memory_reuse_count",
        "calibration_drift",
        "evidence_coverage_ratio",
        "peer_review_depth",
        "review_latency_hours",
        "unresolved_corrections_score",
        "stale_memory_reuse_score",
        "calibration_drift_score",
        "evidence_gap_score",
        "peer_review_gap_score",
        "review_latency_score",
        "learning_gap_score",
        "review_status",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["reason_code_counts"][0]) == (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    )

    invalid_payloads: list[dict[str, Any]] = []
    extra_report_field = cloned_payload(payload)
    extra_report_field["safe_extra"] = "pass"
    invalid_payloads.append(resign_payload(extra_report_field))

    missing_report_field = cloned_payload(payload)
    missing_report_field.pop("report_status")
    invalid_payloads.append(resign_payload(missing_report_field))

    extra_result_field = cloned_payload(payload)
    extra_result_field["results"][0]["safe_extra"] = "pass"
    invalid_payloads.append(resign_payload(extra_result_field))

    missing_result_field = cloned_payload(payload)
    missing_result_field["results"][0].pop("review_status")
    invalid_payloads.append(resign_payload(missing_result_field))

    extra_reason_count_field = cloned_payload(payload)
    extra_reason_count_field["reason_code_counts"][0]["safe_extra"] = "pass"
    invalid_payloads.append(resign_payload(extra_reason_count_field))

    missing_reason_count_field = cloned_payload(payload)
    missing_reason_count_field["reason_code_counts"][0].pop("count")
    invalid_payloads.append(resign_payload(missing_reason_count_field))

    for invalid in invalid_payloads:
        with pytest.raises(ValueError, match="exact canonical schema"):
            module.research_team_domain_review_learning_gap_report_payload(invalid)


def test_payload_rejects_resigned_noncanonical_mapping_key_order() -> None:
    module = api()
    payload = module.research_team_domain_review_learning_gap_report_payload(
        report(review()),
    )

    reordered_report = with_first_key_moved_to_end(cloned_payload(payload))
    resign_payload(reordered_report)
    with pytest.raises(ValueError, match="exact canonical schema"):
        module.research_team_domain_review_learning_gap_report_payload(
            reordered_report,
        )

    reordered_result = cloned_payload(payload)
    reordered_result["results"][0] = with_first_key_moved_to_end(
        reordered_result["results"][0],
    )
    resign_payload(reordered_result)
    with pytest.raises(ValueError, match="exact canonical schema"):
        module.research_team_domain_review_learning_gap_report_payload(
            reordered_result,
        )

    reordered_reason_count = cloned_payload(payload)
    reordered_reason_count["reason_code_counts"][0] = with_first_key_moved_to_end(
        reordered_reason_count["reason_code_counts"][0],
    )
    resign_payload(reordered_reason_count)
    with pytest.raises(ValueError, match="exact canonical schema"):
        module.research_team_domain_review_learning_gap_report_payload(
            reordered_reason_count,
        )


def test_payload_rejects_cyclic_object_graph() -> None:
    module = api()
    cyclic_payload = cloned_payload(
        module.research_team_domain_review_learning_gap_report_payload(
            report(review()),
        ),
    )
    cyclic_payload["results"] = [cyclic_payload]

    with pytest.raises(ValueError, match="cycles"):
        module.research_team_domain_review_learning_gap_report_payload(
            cyclic_payload,
        )


def test_payload_rejects_excessive_object_graph_depth() -> None:
    module = api()
    deep_payload = cloned_payload(
        module.research_team_domain_review_learning_gap_report_payload(
            report(review()),
        ),
    )
    nested: Any = "safe"
    for _ in range(1_100):
        nested = [nested]
    deep_payload["results"] = nested

    with pytest.raises(ValueError, match="nesting depth"):
        module.research_team_domain_review_learning_gap_report_payload(deep_payload)


def test_payload_requires_sha256_and_canonical_decimal_strings() -> None:
    module = api()
    payload = module.research_team_domain_review_learning_gap_report_payload(
        report(review()),
    )
    unsigned_report = {
        key: value
        for key, value in payload.items()
        if key != "validation_digest"
    }
    assert payload["validation_digest"] == canonical_digest(unsigned_report)
    unsigned_result = {
        key: value
        for key, value in payload["results"][0].items()
        if key != "validation_digest"
    }
    assert payload["results"][0]["validation_digest"] == canonical_digest(
        unsigned_result,
    )

    bad_digest = cloned_payload(payload)
    bad_digest["validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="validation_digest"):
        module.research_team_domain_review_learning_gap_report_payload(bad_digest)

    negative_zero = cloned_payload(payload)
    negative_zero["max_learning_gap_score"] = "-0.000000"
    resign_payload(negative_zero)
    with pytest.raises(ValueError, match="signed zero|canonical"):
        module.research_team_domain_review_learning_gap_report_payload(negative_zero)

    noncanonical_count = cloned_payload(payload)
    noncanonical_count["review_count"] = "01"
    resign_payload(noncanonical_count)
    with pytest.raises(ValueError, match="canonical"):
        module.research_team_domain_review_learning_gap_report_payload(
            noncanonical_count,
        )

    noncanonical_ratio = cloned_payload(payload)
    noncanonical_ratio["results"][0]["calibration_drift"] = "0.05"
    resign_payload(noncanonical_ratio)
    with pytest.raises(ValueError, match="canonical"):
        module.research_team_domain_review_learning_gap_report_payload(
            noncanonical_ratio,
        )


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("unresolved_corrections", "3"),
        ("stale_memory_reuse_count", "2"),
        ("calibration_drift", "0.300000"),
        ("evidence_coverage_ratio", "0.500000"),
        ("peer_review_depth", "0"),
        ("review_latency_hours", "96.000000"),
    ),
)
def test_resigned_payload_recomputes_all_result_derived_fields(
    field_name: str,
    forged_value: str,
) -> None:
    module = api()
    payload = module.research_team_domain_review_learning_gap_report_payload(
        report(review()),
    )
    forged = cloned_payload(payload)
    forged["results"][0][field_name] = forged_value
    resign_payload(forged)

    with pytest.raises(
        ValueError,
        match="score|reason_codes|review_status|derived",
    ):
        module.research_team_domain_review_learning_gap_report_payload(forged)


@pytest.mark.parametrize(
    ("path", "forged_value", "match"),
    (
        (("results", 0, "unresolved_corrections_score"), "1.000000", "score"),
        (("results", 0, "learning_gap_score"), "0.000000", "learning_gap_score"),
        (("results", 0, "review_status"), "watch", "review_status"),
        (("results", 0, "reason_codes"), ["calibration_drift_watch"], "reason_codes"),
        (("review_count",), "2", "review_count"),
        (("pass_count",), "0", "pass_count"),
        (("watch_count",), "1", "watch_count"),
        (("block_count",), "1", "block_count"),
        (("max_learning_gap_score",), "1.000000", "max_learning_gap_score"),
        (("report_status",), "watch", "report_status"),
        (("reason_codes",), ["calibration_drift_watch"], "reason_codes"),
        (("reason_code_counts", 0, "count"), "2", "reason_code_counts"),
        (
            ("reason_code_counts", 0, "reason_code"),
            "calibration_drift_watch",
            "reason_code_counts",
        ),
    ),
)
def test_resigned_payload_rederives_status_reason_score_count_and_aggregate_values(
    path: tuple[str | int, ...],
    forged_value: Any,
    match: str,
) -> None:
    module = api()
    payload = module.research_team_domain_review_learning_gap_report_payload(
        report(review()),
    )
    forged = cloned_payload(payload)
    set_payload_path(forged, path, forged_value)
    resign_payload(forged)

    with pytest.raises(ValueError, match=match):
        module.research_team_domain_review_learning_gap_report_payload(forged)


def test_resigned_payload_rederives_internally_consistent_result_reasons_from_raw_values() -> None:
    module = api()
    payload = module.research_team_domain_review_learning_gap_report_payload(
        report(review()),
    )
    forged = cloned_payload(payload)
    forged["results"][0]["review_status"] = "watch"
    forged["results"][0]["reason_codes"] = ["calibration_drift_watch"]
    resign_payload(forged)

    with pytest.raises(ValueError, match="reason_codes"):
        module.research_team_domain_review_learning_gap_report_payload(forged)


def test_resigned_payload_rejects_nondeterministic_result_and_reason_count_order() -> None:
    module = api()
    result_order_payload = module.research_team_domain_review_learning_gap_report_payload(
        report(
            review(review_key="order-review-alpha", domain_key="order-domain-alpha"),
            review(review_key="order-review-beta", domain_key="order-domain-beta"),
        ),
    )
    result_order_payload["results"] = list(reversed(result_order_payload["results"]))
    resign_payload(result_order_payload)
    with pytest.raises(ValueError, match="results must be sorted deterministically"):
        module.research_team_domain_review_learning_gap_report_payload(
            result_order_payload,
        )

    reason_count_order_payload = module.research_team_domain_review_learning_gap_report_payload(
        report(
            review(
                review_key="reason-order-watch",
                unresolved_corrections=d("1"),
            ),
            review(review_key="reason-order-pass"),
        ),
    )
    reason_count_order_payload["reason_code_counts"] = list(
        reversed(reason_count_order_payload["reason_code_counts"]),
    )
    resign_payload(reason_count_order_payload)
    with pytest.raises(
        ValueError,
        match="reason_code_counts must be sorted deterministically",
    ):
        module.research_team_domain_review_learning_gap_report_payload(
            reason_count_order_payload,
        )


def test_resigned_payload_rejects_duplicate_review_fingerprints() -> None:
    module = api()
    payload = module.research_team_domain_review_learning_gap_report_payload(
        report(
            review(review_key="duplicate-review-alpha"),
            review(review_key="duplicate-review-beta"),
        ),
    )
    forged = cloned_payload(payload)
    forged["results"][1]["review_fingerprint"] = forged["results"][0][
        "review_fingerprint"
    ]
    resign_payload(forged)

    with pytest.raises(ValueError, match="review_fingerprint values must be unique"):
        module.research_team_domain_review_learning_gap_report_payload(forged)


def test_equal_score_results_use_stable_fingerprint_tie_breaks() -> None:
    rows = (
        review(review_key="review-zeta", domain_key="domain-beta"),
        review(review_key="review-alpha", domain_key="domain-beta"),
        review(review_key="review-beta", domain_key="domain-alpha"),
    )
    first = report(*rows)
    second = report(*reversed(rows))

    assert first.results == second.results
    fingerprint_keys = tuple(
        (row.domain_fingerprint, row.review_fingerprint)
        for row in first.results
    )
    assert fingerprint_keys == tuple(sorted(fingerprint_keys))


def test_private_team_and_source_identifiers_are_fingerprinted_and_redacted() -> None:
    module = api()
    private_team = "private-team-rates|reviewer-alice|https://internal.test/team"
    private_source = "private-source-wire|credential-secret|dsn-internal"
    payload = module.research_team_domain_review_learning_gap_report_payload(
        report(
            review(
                review_key=private_team,
                domain_key=private_source,
            ),
        ),
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert private_team not in encoded
    assert private_source not in encoded
    assert "reviewer-alice" not in encoded
    assert "credential-secret" not in encoded

    forged = cloned_payload(payload)
    forged["results"][0]["private_team_key"] = "redacted"
    forged["results"][0]["private_source_key"] = "redacted"
    resign_payload(forged)
    with pytest.raises(ValueError, match="exact canonical schema"):
        module.research_team_domain_review_learning_gap_report_payload(forged)


def test_canonical_snapshots_do_not_retain_private_identifier_text() -> None:
    module = api()
    private_review = "snapshot-private-review-credential-alpha"
    private_domain = "snapshot-private-domain-internal-alpha"
    value = review(review_key=private_review, domain_key=private_domain)

    snapshot_text = repr(module._PUBLIC_SNAPSHOTS[id(value)])

    assert private_review not in snapshot_text
    assert private_domain not in snapshot_text


def domain_review_result(review_key: str) -> Any:
    return report(review(review_key=review_key)).results[0]


def test_module_is_pure_readonly_report_only_and_contains_no_io_surfaces() -> None:
    path = Path(
        "src/polymarket_alpha_lab/"
        "research_team_domain_review_learning_gap_report.py",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    source = path.read_text(encoding="utf-8").lower()

    banned_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    banned_calls = {
        "connect",
        "delete",
        "execute",
        "insert",
        "login",
        "open",
        "post",
        "request",
        "send",
        "submit",
        "update",
        "urlopen",
        "write",
    }
    banned_attributes = banned_calls | {"commit", "replace", "rollback", "session"}
    forbidden_terms = (
        "auth",
        "broker",
        "database",
        "db write",
        "live trading",
        "order",
        "supabase",
        "wallet",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes

    assert [term for term in forbidden_terms if term in source] == []
