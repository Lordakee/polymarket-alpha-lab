from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_team_domain_outcome_calibration_feedback_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_domain_outcome_calibration_feedback_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resign(payload: dict[str, Any]) -> dict[str, Any]:
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def config(**overrides: object) -> Any:
    return api().ResearchTeamDomainOutcomeCalibrationFeedbackConfig(**overrides)


def summary(
    domain_id: str,
    team_id: str,
    *,
    sample_count: Decimal = d("40.000000"),
    brier_like_error: Decimal = d("0.050000"),
    source_disagreement_rate: Decimal = d("0.050000"),
    memory_reuse_rate: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return api().ResearchTeamDomainSettledOutcomeFeedbackSummary(
        domain_id=domain_id,
        team_id=team_id,
        sample_count=sample_count,
        brier_like_error=brier_like_error,
        source_disagreement_rate=source_disagreement_rate,
        memory_reuse_rate=memory_reuse_rate,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *summaries: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return api().build_research_team_domain_outcome_calibration_feedback_report(
        summaries,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def direct_report_with_rows(report: Any, rows: tuple[Any, ...]) -> Any:
    module = api()
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["rows"] = rows
    unsigned = {
        field_name: value
        for field_name, value in values.items()
        if field_name != "derived_validation_digest"
    }
    values["derived_validation_digest"] = module._digest_from_values(unsigned)
    return module.ResearchTeamDomainOutcomeCalibrationFeedbackReport(**values)


def test_report_reduces_settled_summaries_into_weighted_domain_diagnostics() -> None:
    summaries = (
        summary("politics", "team_elections"),
        summary(
            "macro",
            "team_rates",
            sample_count=d("20.000000"),
            brier_like_error=d("0.150000"),
            source_disagreement_rate=d("0.200000"),
            memory_reuse_rate=d("0.650000"),
        ),
        summary(
            "crypto",
            "team_protocols",
            sample_count=d("5.000000"),
            brier_like_error=d("0.300000"),
            source_disagreement_rate=d("0.400000"),
            memory_reuse_rate=d("0.400000"),
        ),
    )

    report = build_report(*summaries)
    reversed_report = build_report(*reversed(summaries))

    assert api().OUTCOME_CALIBRATION_REVIEW_BUCKETS == ("pass", "watch", "block")
    assert report.review_bucket == "block"
    assert report.input_count == d("3.000000")
    assert report.total_sample_count == d("65.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_brier_like_error == d("0.100000")
    assert report.average_source_disagreement_rate == d("0.123077")
    assert report.average_memory_reuse_rate == d("0.784615")

    blocked, watched, passed = report.rows
    assert tuple(row.review_bucket for row in report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert (blocked.domain_id, blocked.team_id) == ("crypto", "team_protocols")
    assert blocked.reason_codes == (
        "team_domain_outcome_feedback_sample_count_block",
        "team_domain_outcome_feedback_brier_like_error_block",
        "team_domain_outcome_feedback_source_disagreement_block",
        "team_domain_outcome_feedback_memory_reuse_block",
    )
    assert watched.reason_codes == (
        "team_domain_outcome_feedback_sample_count_watch",
        "team_domain_outcome_feedback_brier_like_error_watch",
        "team_domain_outcome_feedback_source_disagreement_watch",
        "team_domain_outcome_feedback_memory_reuse_watch",
    )
    assert passed.reason_codes == (
        "team_domain_outcome_calibration_feedback_pass",
    )
    assert report.reason_codes == blocked.reason_codes + watched.reason_codes

    payload = api().research_team_domain_outcome_calibration_feedback_report_payload(
        report,
    )
    reversed_payload = (
        api().research_team_domain_outcome_calibration_feedback_report_payload(
            reversed_report,
        )
    )
    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"][0]["brier_like_error"] == "0.300000"
    assert _float_or_int_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_report_is_frozen_decimal_only_flag_hardened_and_empty_safe() -> None:
    module = api()
    report = build_report(summary("macro", "team_rates"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_OUTCOME_CALIBRATION_FEEDBACK_CONFIG_VERSION",
        "OUTCOME_CALIBRATION_REVIEW_BUCKETS",
        "ResearchTeamDomainOutcomeCalibrationFeedbackConfig",
        "ResearchTeamDomainSettledOutcomeFeedbackSummary",
        "ResearchTeamDomainOutcomeCalibrationFeedbackRow",
        "ResearchTeamDomainOutcomeCalibrationFeedbackReport",
        "build_research_team_domain_outcome_calibration_feedback_report",
        "research_team_domain_outcome_calibration_feedback_report_digest",
        "research_team_domain_outcome_calibration_feedback_report_payload",
        "validate_research_team_domain_outcome_calibration_feedback_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    empty = build_report()
    assert empty.review_bucket == "pass"
    assert empty.reason_codes == (
        "team_domain_outcome_calibration_feedback_empty",
    )
    assert empty.rows == ()
    assert empty.input_count == d("0.000000")
    assert empty.total_sample_count == d("0.000000")
    assert empty.average_brier_like_error is None
    assert empty.average_source_disagreement_rate is None
    assert empty.average_memory_reuse_rate is None

    for value in (config(), summary("sports", "team_tennis"), report, *report.rows):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if isinstance(item, Decimal):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].review_bucket = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="sample_count must be a Decimal"):
        summary("macro", "team_rates", sample_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="brier_like_error must be a Decimal"):
        summary(
            "macro",
            "team_rates",
            brier_like_error=DecimalSubclass("0.100000"),
        )
    with pytest.raises(ValueError, match="domain/team summaries must be unique"):
        build_report(
            summary("macro", "team_rates"),
            summary("macro", "team_rates"),
        )
    with pytest.raises(ValueError, match="max_pass_brier_like_error"):
        config(
            max_pass_brier_like_error=d("0.300000"),
            max_watch_brier_like_error=d("0.200000"),
        )
    with pytest.raises(ValueError, match="public identifier"):
        summary("macro_market_slug", "team_rates")


def test_decimal_context_raw_bounds_signed_zero_and_non_finite_are_hardened() -> None:
    baseline = build_report(
        summary(
            "macro",
            "team_rates",
            sample_count=d("999999.000000"),
            brier_like_error=d("0.123456"),
            source_disagreement_rate=d("0.234567"),
            memory_reuse_rate=d("0.765432"),
        ),
        summary(
            "politics",
            "team_elections",
            sample_count=d("888888.000000"),
            brier_like_error=d("0.234567"),
            source_disagreement_rate=d("0.123456"),
            memory_reuse_rate=d("0.654321"),
        ),
    )
    baseline_payload = (
        api().research_team_domain_outcome_calibration_feedback_report_payload(
            baseline,
        )
    )

    with localcontext(Context(prec=6, rounding=ROUND_DOWN)):
        constrained = build_report(
            summary(
                "macro",
                "team_rates",
                sample_count=d("999999.000000"),
                brier_like_error=d("0.123456"),
                source_disagreement_rate=d("0.234567"),
                memory_reuse_rate=d("0.765432"),
            ),
            summary(
                "politics",
                "team_elections",
                sample_count=d("888888.000000"),
                brier_like_error=d("0.234567"),
                source_disagreement_rate=d("0.123456"),
                memory_reuse_rate=d("0.654321"),
            ),
        )
        constrained_payload = (
            api().research_team_domain_outcome_calibration_feedback_report_payload(
                constrained,
            )
        )
    assert constrained_payload == baseline_payload

    with pytest.raises(ValueError, match="nonnegative"):
        summary("macro", "team_rates", sample_count=d("-0.0000004"))
    with pytest.raises(ValueError, match="between zero and one"):
        summary("macro", "team_rates", brier_like_error=d("-0.0000004"))
    with pytest.raises(ValueError, match="between zero and one"):
        summary("macro", "team_rates", memory_reuse_rate=d("1.0000004"))
    for non_finite in ("NaN", "sNaN", "Infinity", "-Infinity"):
        with pytest.raises(ValueError, match="finite"):
            summary("macro", "team_rates", brier_like_error=d(non_finite))
    for signed_zero in ("-0", "-0.000000"):
        with pytest.raises(ValueError, match="signed zero"):
            summary("macro", "team_rates", brier_like_error=d(signed_zero))


def test_rejects_overprecision_even_when_quantization_preserves_the_value() -> None:
    with pytest.raises(ValueError, match="six decimal places"):
        summary("macro", "team_rates", sample_count=d("1.0000000"))
    with pytest.raises(ValueError, match="six decimal places"):
        summary("macro", "team_rates", brier_like_error=d("0.1000000"))
    with pytest.raises(ValueError, match="six decimal places"):
        config(max_pass_brier_like_error=d("0.1000000"))


def test_dataclasses_are_frozen_exact_type_and_non_subclassable() -> None:
    module = api()
    dataclass_types = (
        module.ResearchTeamDomainOutcomeCalibrationFeedbackConfig,
        module.ResearchTeamDomainSettledOutcomeFeedbackSummary,
        module.ResearchTeamDomainOutcomeCalibrationFeedbackRow,
        module.ResearchTeamDomainOutcomeCalibrationFeedbackReport,
    )

    for dataclass_type in dataclass_types:
        assert is_dataclass(dataclass_type)
        assert dataclass_type.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="subclass is not allowed"):
            type(f"Invalid{dataclass_type.__name__}", (dataclass_type,), {})


def test_payload_uses_exact_canonical_schema_and_stable_tie_breaks() -> None:
    module = api()
    summaries = (
        summary(
            "politics",
            "team_zeta",
            sample_count=d("20.000000"),
            brier_like_error=d("0.150000"),
            source_disagreement_rate=d("0.150000"),
            memory_reuse_rate=d("0.650000"),
        ),
        summary(
            "macro",
            "team_beta",
            sample_count=d("20.000000"),
            brier_like_error=d("0.150000"),
            source_disagreement_rate=d("0.150000"),
            memory_reuse_rate=d("0.650000"),
        ),
        summary(
            "macro",
            "team_alpha",
            sample_count=d("20.000000"),
            brier_like_error=d("0.150000"),
            source_disagreement_rate=d("0.150000"),
            memory_reuse_rate=d("0.650000"),
        ),
    )
    report = build_report(*reversed(summaries))
    payload = module.research_team_domain_outcome_calibration_feedback_report_payload(
        report,
    )

    assert tuple((row.domain_id, row.team_id) for row in report.rows) == (
        ("macro", "team_alpha"),
        ("macro", "team_beta"),
        ("politics", "team_zeta"),
    )
    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "min_pass_sample_count",
        "min_watch_sample_count",
        "max_pass_brier_like_error",
        "max_watch_brier_like_error",
        "max_pass_source_disagreement_rate",
        "max_watch_source_disagreement_rate",
        "min_pass_memory_reuse_rate",
        "min_watch_memory_reuse_rate",
        "input_count",
        "total_sample_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_brier_like_error",
        "average_source_disagreement_rate",
        "average_memory_reuse_rate",
        "review_bucket",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )

    assert tuple(payload["rows"][0]) == (
        "domain_id",
        "team_id",
        "sample_count",
        "brier_like_error",
        "source_disagreement_rate",
        "memory_reuse_rate",
        "review_bucket",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )

    reordered_report = dict(reversed(tuple(payload.items())))
    resign(reordered_report)
    with pytest.raises(ValueError, match="canonical field order"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            reordered_report,
        )

    reordered_row = json.loads(json.dumps(payload))
    reordered_row["rows"][0] = dict(
        reversed(tuple(reordered_row["rows"][0].items())),
    )
    resign(reordered_row)
    with pytest.raises(ValueError, match="canonical field order"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            reordered_row,
        )


def test_feedback_report_treats_naive_generated_at_as_utc() -> None:
    report = build_report(generated_at=datetime(2026, 7, 9, 12, 0))

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error_match"),
    (
        ("domain_id", "market_private", "domain_id"),
        ("team_id", "team_secret", "team_id"),
        ("sample_count", DecimalSubclass("40.000000"), "sample_count"),
        ("brier_like_error", DecimalSubclass("0.050000"), "brier_like_error"),
        (
            "source_disagreement_rate",
            DecimalSubclass("0.050000"),
            "source_disagreement_rate",
        ),
        ("memory_reuse_rate", DecimalSubclass("0.900000"), "memory_reuse_rate"),
        ("review_bucket", "invalid", "review_bucket"),
        (
            "reason_codes",
            ("team_domain_outcome_feedback_sample_count_watch",),
            "reason_codes",
        ),
        ("paper_only", False, "paper_only"),
        ("report_only", False, "report_only"),
        ("readonly", False, "readonly"),
    ),
)
def test_report_direct_construction_revalidates_tampered_row_fields(
    field_name: str,
    forged_value: object,
    error_match: str,
) -> None:
    report = build_report(summary("macro", "team_rates"))
    tampered_row = replace(report.rows[0])
    object.__setattr__(tampered_row, field_name, forged_value)

    with pytest.raises(ValueError, match=error_match):
        direct_report_with_rows(report, (tampered_row,))


def test_resigned_payload_rejects_missing_top_level_exact_schema_field() -> None:
    module = api()
    payload = module.research_team_domain_outcome_calibration_feedback_report_payload(
        build_report(summary("macro", "team_rates")),
    )
    missing_field = json.loads(json.dumps(payload))
    missing_field.pop("review_bucket")
    resign(missing_field)

    with pytest.raises(ValueError, match="exact public fields"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            missing_field,
        )


def test_resigned_payload_rejects_missing_row_exact_schema_field() -> None:
    module = api()
    payload = module.research_team_domain_outcome_calibration_feedback_report_payload(
        build_report(summary("macro", "team_rates")),
    )
    missing_field = json.loads(json.dumps(payload))
    missing_field["rows"][0].pop("review_bucket")
    resign(missing_field)

    with pytest.raises(ValueError, match="exact public fields"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            missing_field,
        )


def test_private_team_and_source_identifiers_are_redacted_from_public_surface() -> None:
    for domain_id, team_id in (
        ("macro", "team_internal_rates"),
        ("macro_internal_source", "team_rates"),
        ("macro", "team_confidential_rates"),
        ("macro_proprietary_source", "team_rates"),
    ):
        with pytest.raises(ValueError, match="public identifier"):
            summary(domain_id, team_id)


def test_sensitive_identifier_fragments_are_rejected_before_publication() -> None:
    for unsafe_identifier in (
        "raw",
        "candidate",
        "market",
        "question",
        "source",
        "dsn",
        "api_key",
        "password",
        "credential",
    ):
        with pytest.raises(ValueError, match="public identifier"):
            summary(unsafe_identifier, "team_rates")
        with pytest.raises(ValueError, match="public identifier"):
            summary("macro", f"team_{unsafe_identifier}")


def test_payload_rejects_noncanonical_objects_before_json_normalization() -> None:
    module = api()
    payload = module.research_team_domain_outcome_calibration_feedback_report_payload(
        build_report(summary("macro", "team_rates")),
    )

    class PayloadDict(dict[str, Any]):
        pass

    top_level_subclass = PayloadDict(payload)

    nested_row_subclass = json.loads(json.dumps(payload))
    nested_row_subclass["rows"][0] = PayloadDict(nested_row_subclass["rows"][0])

    tuple_reason_codes = json.loads(json.dumps(payload))
    tuple_reason_codes["reason_codes"] = tuple(tuple_reason_codes["reason_codes"])

    decimal_numeric = json.loads(json.dumps(payload))
    decimal_numeric["input_count"] = d(decimal_numeric["input_count"])

    for noncanonical_payload in (
        top_level_subclass,
        nested_row_subclass,
        tuple_reason_codes,
        decimal_numeric,
    ):
        with pytest.raises(
            ValueError,
            match="canonical|plain|JSON object|dict|public list|Decimal-derived",
        ):
            module.research_team_domain_outcome_calibration_feedback_report_payload(
                noncanonical_payload,
            )


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("input_count", "4.000000"),
        ("total_sample_count", "66.000000"),
        ("pass_count", "2.000000"),
        ("watch_count", "2.000000"),
        ("block_count", "2.000000"),
        ("average_brier_like_error", "0.100001"),
        ("average_source_disagreement_rate", "0.123078"),
        ("average_memory_reuse_rate", "0.784616"),
    ),
)
def test_resigned_payload_recomputes_every_report_derived_field(
    field_name: str,
    forged_value: str,
) -> None:
    module = api()
    payload = module.research_team_domain_outcome_calibration_feedback_report_payload(
        build_report(
            summary("politics", "team_elections"),
            summary(
                "macro",
                "team_rates",
                sample_count=d("20.000000"),
                brier_like_error=d("0.150000"),
                source_disagreement_rate=d("0.200000"),
                memory_reuse_rate=d("0.650000"),
            ),
            summary(
                "crypto",
                "team_protocols",
                sample_count=d("5.000000"),
                brier_like_error=d("0.300000"),
                source_disagreement_rate=d("0.400000"),
                memory_reuse_rate=d("0.400000"),
            ),
        ),
    )
    forged = json.loads(json.dumps(payload))
    forged[field_name] = forged_value
    resign(forged)

    with pytest.raises(ValueError, match=field_name):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            forged,
        )


def test_public_validator_rejects_forged_resigned_derived_logic() -> None:
    module = api()
    report = build_report(
        summary(
            "crypto",
            "team_protocols",
            sample_count=d("5.000000"),
            brier_like_error=d("0.300000"),
            source_disagreement_rate=d("0.400000"),
            memory_reuse_rate=d("0.400000"),
        ),
    )
    payload = module.research_team_domain_outcome_calibration_feedback_report_payload(
        report,
    )

    module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
        payload,
    )
    assert module.research_team_domain_outcome_calibration_feedback_report_digest(
        payload,
    ) == payload["derived_validation_digest"]

    forged_row_bucket = json.loads(json.dumps(payload))
    forged_row_bucket["rows"][0]["review_bucket"] = "pass"
    forged_row_bucket["derived_validation_digest"] = canonical_digest(
        forged_row_bucket,
    )
    with pytest.raises(ValueError, match="review_bucket|reason_codes"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            forged_row_bucket,
        )

    forged_row_reasons = json.loads(json.dumps(payload))
    forged_row_reasons["rows"][0]["reason_codes"] = [
        "team_domain_outcome_calibration_feedback_pass",
    ]
    forged_row_reasons["rows"][0]["review_bucket"] = "pass"
    forged_row_reasons["derived_validation_digest"] = canonical_digest(
        forged_row_reasons,
    )
    with pytest.raises(ValueError, match="reason_codes"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            forged_row_reasons,
        )

    forged_report = json.loads(json.dumps(payload))
    forged_report["review_bucket"] = "pass"
    forged_report["reason_codes"] = [
        "team_domain_outcome_calibration_feedback_pass",
    ]
    forged_report["derived_validation_digest"] = canonical_digest(forged_report)
    with pytest.raises(ValueError, match="review_bucket|reason_codes"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            forged_report,
        )

    forged_numeric = json.loads(json.dumps(payload))
    forged_numeric["total_sample_count"] = 5
    forged_numeric["derived_validation_digest"] = canonical_digest(forged_numeric)
    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            forged_numeric,
        )

    forged_extra = json.loads(json.dumps(payload))
    forged_extra["source_url"] = "redacted"
    forged_extra["derived_validation_digest"] = canonical_digest(forged_extra)
    with pytest.raises(ValueError, match="public fields|unsafe"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            forged_extra,
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            {**payload, "total_sample_count": "6.000000"},
        )

    resigned_row_metric = json.loads(json.dumps(payload))
    resigned_row_metric["rows"][0]["memory_reuse_rate"] = "0.900000"
    resign(resigned_row_metric)
    with pytest.raises(ValueError, match="reason_codes|average_memory_reuse_rate"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            resigned_row_metric,
        )

    resigned_aggregate = json.loads(json.dumps(payload))
    resigned_aggregate["average_memory_reuse_rate"] = "0.900000"
    resign(resigned_aggregate)
    with pytest.raises(ValueError, match="average_memory_reuse_rate"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            resigned_aggregate,
        )

    resigned_sort = build_report(
        summary(
            "crypto",
            "team_protocols",
            sample_count=d("5.000000"),
            brier_like_error=d("0.300000"),
            source_disagreement_rate=d("0.400000"),
            memory_reuse_rate=d("0.400000"),
        ),
        summary(
            "macro",
            "team_rates",
            sample_count=d("5.000000"),
            brier_like_error=d("0.300000"),
            source_disagreement_rate=d("0.400000"),
            memory_reuse_rate=d("0.400000"),
        ),
    )
    resigned_sort_payload = (
        module.research_team_domain_outcome_calibration_feedback_report_payload(
            resigned_sort,
        )
    )
    resigned_sort_payload["rows"].reverse()
    resign(resigned_sort_payload)
    with pytest.raises(ValueError, match="deterministically sorted"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            resigned_sort_payload,
        )

    unsupported_version = json.loads(json.dumps(payload))
    unsupported_version["config_version"] = "unsupported-calibration-version"
    resign(unsupported_version)
    with pytest.raises(ValueError, match="supported config version"):
        module.validate_research_team_domain_outcome_calibration_feedback_public_payload(
            unsupported_version,
        )


def test_module_scope_is_pure_in_memory_readonly_report_only() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests.",
        "urllib",
        "sqlite",
        "psycopg",
        "supabase",
        "sqlalchemy",
        "subprocess",
        "socket",
        "open(",
        "getenv",
        "environ",
        "postgres",
        "://",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
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
                "place_order",
                "submit_order",
                "cancel_order",
            }

    assert not imported_roots.intersection(
        {
            "requests",
            "urllib",
            "httpx",
            "socket",
            "psycopg",
            "sqlite3",
            "sqlalchemy",
            "supabase",
            "subprocess",
        },
    )


def test_threshold_boundaries_classify_inclusively_with_reason_codes() -> None:
    report = build_report(
        summary(
            "macro",
            "team_pass_thresholds",
            sample_count=d("30.000000"),
            brier_like_error=d("0.100000"),
            source_disagreement_rate=d("0.100000"),
            memory_reuse_rate=d("0.750000"),
        ),
        summary(
            "politics",
            "team_watch_thresholds",
            sample_count=d("10.000000"),
            brier_like_error=d("0.250000"),
            source_disagreement_rate=d("0.250000"),
            memory_reuse_rate=d("0.500000"),
        ),
    )

    watched, passed = report.rows
    watch_reasons = (
        "team_domain_outcome_feedback_sample_count_watch",
        "team_domain_outcome_feedback_brier_like_error_watch",
        "team_domain_outcome_feedback_source_disagreement_watch",
        "team_domain_outcome_feedback_memory_reuse_watch",
    )
    assert report.review_bucket == "watch"
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("0.000000")
    assert watched.review_bucket == "watch"
    assert watched.reason_codes == watch_reasons
    assert passed.review_bucket == "pass"
    assert passed.reason_codes == (
        "team_domain_outcome_calibration_feedback_pass",
    )
    assert report.reason_codes == watch_reasons


def test_nonempty_zero_sample_report_uses_unweighted_average_fallback() -> None:
    zero_sample_summaries = (
        summary(
            "macro",
            "team_alpha",
            sample_count=d("0.000000"),
            brier_like_error=d("0.100000"),
            source_disagreement_rate=d("0.200000"),
            memory_reuse_rate=d("0.800000"),
        ),
        summary(
            "politics",
            "team_beta",
            sample_count=d("0.000000"),
            brier_like_error=d("0.400000"),
            source_disagreement_rate=d("0.600000"),
            memory_reuse_rate=d("0.200000"),
        ),
    )

    report = build_report(*zero_sample_summaries)
    reversed_report = build_report(*reversed(zero_sample_summaries))

    assert report.input_count == d("2.000000")
    assert report.total_sample_count == d("0.000000")
    assert tuple(row.sample_count for row in report.rows) == (
        d("0.000000"),
        d("0.000000"),
    )
    assert report.average_brier_like_error == d("0.250000")
    assert report.average_source_disagreement_rate == d("0.400000")
    assert report.average_memory_reuse_rate == d("0.500000")
    assert (
        api().research_team_domain_outcome_calibration_feedback_report_payload(report)
        == api().research_team_domain_outcome_calibration_feedback_report_payload(
            reversed_report,
        )
    )


@pytest.mark.parametrize(
    ("overrides", "error_match"),
    (
        (
            {
                "min_pass_sample_count": d("9.000000"),
                "min_watch_sample_count": d("10.000000"),
            },
            "min_pass_sample_count",
        ),
        (
            {
                "max_pass_brier_like_error": d("0.300000"),
                "max_watch_brier_like_error": d("0.200000"),
            },
            "max_pass_brier_like_error",
        ),
        (
            {
                "max_pass_source_disagreement_rate": d("0.300000"),
                "max_watch_source_disagreement_rate": d("0.200000"),
            },
            "max_pass_source_disagreement_rate",
        ),
        (
            {
                "min_pass_memory_reuse_rate": d("0.400000"),
                "min_watch_memory_reuse_rate": d("0.500000"),
            },
            "min_pass_memory_reuse_rate",
        ),
    ),
)
def test_config_rejects_all_cross_field_ordering_invariants(
    overrides: dict[str, Decimal],
    error_match: str,
) -> None:
    with pytest.raises(ValueError, match=error_match):
        config(**overrides)


@pytest.mark.parametrize(
    "field_name",
    (
        "sample_count",
        "brier_like_error",
        "source_disagreement_rate",
        "memory_reuse_rate",
    ),
)
@pytest.mark.parametrize("signed_zero", ("-0", "-0.000000"))
def test_summary_metric_fields_reject_signed_zero(
    field_name: str,
    signed_zero: str,
) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must not be signed zero"):
        summary("macro", "team_rates", **{field_name: d(signed_zero)})


@pytest.mark.parametrize(
    "field_name",
    (
        "min_pass_sample_count",
        "min_watch_sample_count",
        "max_pass_brier_like_error",
        "max_watch_brier_like_error",
        "max_pass_source_disagreement_rate",
        "max_watch_source_disagreement_rate",
        "min_pass_memory_reuse_rate",
        "min_watch_memory_reuse_rate",
    ),
)
@pytest.mark.parametrize("signed_zero", ("-0", "-0.000000"))
def test_config_decimal_fields_reject_signed_zero(
    field_name: str,
    signed_zero: str,
) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must not be signed zero"):
        config(**{field_name: d(signed_zero)})


def _float_or_int_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if type(value) in (float, int):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_float_or_int_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_float_or_int_paths(nested, child))
        return tuple(paths)
    return ()
