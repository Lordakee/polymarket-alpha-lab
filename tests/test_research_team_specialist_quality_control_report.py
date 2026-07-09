from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
import hashlib
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
SHA_A = "sha256:" + ("a" * 64)
SHA_B = "sha256:" + ("b" * 64)
SHA_C = "sha256:" + ("c" * 64)
CAL_A = "sha256:" + ("1" * 64)
CAL_B = "sha256:" + ("2" * 64)
CAL_C = "sha256:" + ("3" * 64)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_quality_control_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "calibration_watch_error_ratio": d("0.100000"),
        "calibration_block_error_ratio": d("0.250000"),
        "memory_watch_age_seconds": d("86400.000000"),
        "memory_block_age_seconds": d("259200.000000"),
        "bias_watch_flag_count": d("1"),
        "bias_block_flag_count": d("3"),
        "min_source_family_count": d("3"),
        "review_watch_latency_seconds": d("3600.000000"),
        "review_block_latency_seconds": d("7200.000000"),
        "correction_watch_gap_ratio": d("0.250000"),
        "correction_block_gap_ratio": d("0.500000"),
        "calibration_weight": d("0.250000"),
        "memory_weight": d("0.150000"),
        "bias_weight": d("0.200000"),
        "source_diversity_weight": d("0.150000"),
        "review_timeliness_weight": d("0.150000"),
        "correction_coverage_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistQualityControlReportConfig(**values)


def quality_record(
    team_ref: str,
    specialist_ref: str,
    output_digest: str,
    calibration_digest: str,
    *,
    calibration_error_ratio: str,
    memory_age_seconds: int,
    bias_flags: str,
    source_families: str,
    review_latency_seconds: int,
    correction_required: str,
    correction_covered: str,
):
    module = api()
    return module.ResearchTeamSpecialistQualityControlRecord(
        team_ref=team_ref,
        specialist_ref=specialist_ref,
        specialist_output_digest=output_digest,
        calibration_record_digest=calibration_digest,
        observed_at=GENERATED_AT - timedelta(seconds=review_latency_seconds),
        memory_last_refreshed_at=GENERATED_AT - timedelta(seconds=memory_age_seconds),
        review_completed_at=GENERATED_AT,
        calibration_error_ratio=d(calibration_error_ratio),
        bias_flag_count=d(bias_flags),
        source_family_count=d(source_families),
        correction_required_count=d(correction_required),
        correction_covered_count=d(correction_covered),
    )


def build_report(
    *records: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_team_specialist_quality_control_report(
        records,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_decimal_only_numerics(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only_numerics(getattr(value, field.name))
        return
    if type(value) is dict:
        for item in value.values():
            assert_decimal_only_numerics(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_decimal_only_numerics(item)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_float_values(item)
    if type(value) in (list, tuple):
        for item in value:
            assert_no_float_values(item)


def canonical_payload_digest(payload: dict[str, Any]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = json.loads(json.dumps(payload))
    resigned["derived_validation_digest"] = canonical_payload_digest(resigned)
    return resigned


def test_scores_specialist_outputs_and_rolls_up_quality_control_statuses() -> None:
    module = api()

    report = build_report(
        quality_record(
            "team-beta",
            "specialist-weather",
            SHA_C,
            CAL_C,
            calibration_error_ratio="0.300000",
            memory_age_seconds=300_000,
            bias_flags="4",
            source_families="0",
            review_latency_seconds=8_000,
            correction_required="4",
            correction_covered="1",
        ),
        quality_record(
            "team-alpha",
            "specialist-macro",
            SHA_A,
            CAL_A,
            calibration_error_ratio="0.020000",
            memory_age_seconds=600,
            bias_flags="0",
            source_families="3",
            review_latency_seconds=600,
            correction_required="2",
            correction_covered="2",
        ),
        quality_record(
            "team-alpha",
            "specialist-rates",
            SHA_B,
            CAL_B,
            calibration_error_ratio="0.150000",
            memory_age_seconds=90_000,
            bias_flags="1",
            source_families="2",
            review_latency_seconds=4_000,
            correction_required="4",
            correction_covered="3",
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        module.DEFAULT_RESEARCH_TEAM_SPECIALIST_QUALITY_CONTROL_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.output_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.stale_memory_count == d("2")
    assert report.bias_flagged_count == d("2")
    assert report.source_diversity_gap_count == d("2")
    assert report.delayed_review_count == d("2")
    assert report.correction_gap_count == d("2")
    assert report.max_quality_control_risk_score == d("0.975000")
    assert report.average_quality_control_risk_score == d("0.478310")
    assert report.reason_codes == (
        "bias_flags_block",
        "bias_flags_watch",
        "calibration_error_block",
        "calibration_error_watch",
        "correction_coverage_block",
        "correction_coverage_watch",
        "review_latency_block",
        "review_latency_watch",
        "source_diversity_block",
        "source_diversity_watch",
        "stale_memory_block",
        "stale_memory_watch",
    )

    passed, watched, blocked = report.rows
    assert (passed.team_ref, passed.specialist_ref) == ("team-alpha", "specialist-macro")
    assert passed.calibration_component == d("0.080000")
    assert passed.stale_memory_component == d("0.002315")
    assert passed.bias_component == d("0.000000")
    assert passed.source_diversity_gap == d("0.000000")
    assert passed.review_timeliness_component == d("0.083333")
    assert passed.correction_coverage_gap == d("0.000000")
    assert passed.quality_control_risk_score == d("0.032847")
    assert passed.status == "pass"
    assert passed.reason_codes == ("specialist_quality_control_pass",)

    assert (watched.team_ref, watched.specialist_ref) == ("team-alpha", "specialist-rates")
    assert watched.quality_control_risk_score == d("0.427083")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "bias_flags_watch",
        "calibration_error_watch",
        "correction_coverage_watch",
        "review_latency_watch",
        "source_diversity_watch",
        "stale_memory_watch",
    )

    assert (blocked.team_ref, blocked.specialist_ref) == ("team-beta", "specialist-weather")
    assert blocked.quality_control_risk_score == d("0.975000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "bias_flags_block",
        "calibration_error_block",
        "correction_coverage_block",
        "review_latency_block",
        "source_diversity_block",
        "stale_memory_block",
    )
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_decimal_only_numerics(report)


def test_empty_report_blocks_without_live_or_recommendation_surface() -> None:
    module = api()

    report = build_report()

    assert report.status == "block"
    assert report.output_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.rows == ()
    assert report.max_quality_control_risk_score == d("0.000000")
    assert report.average_quality_control_risk_score == d("0.000000")
    assert report.reason_codes == ("specialist_quality_control_empty",)
    assert report.reason_code_counts == (
        module.ResearchTeamSpecialistQualityControlReasonCodeCount(
            reason_code="specialist_quality_control_empty",
            count=d("1"),
        ),
    )
    assert_decimal_only_numerics(report)


def test_payload_serialization_is_deterministic_tamper_evident_and_redacted() -> None:
    module = api()
    first = quality_record(
        "team-alpha",
        "specialist-rates",
        SHA_B,
        CAL_B,
        calibration_error_ratio="0.150000",
        memory_age_seconds=90_000,
        bias_flags="1",
        source_families="2",
        review_latency_seconds=4_000,
        correction_required="4",
        correction_covered="3",
    )
    second = quality_record(
        "team-alpha",
        "specialist-macro",
        SHA_A,
        CAL_A,
        calibration_error_ratio="0.020000",
        memory_age_seconds=600,
        bias_flags="0",
        source_families="3",
        review_latency_seconds=600,
        correction_required="2",
        correction_covered="2",
    )

    report_a = build_report(first, second)
    report_b = build_report(second, first)
    payload = module.research_team_specialist_quality_control_report_payload(report_a)
    encoded = json.dumps(payload, sort_keys=True)

    assert report_a.rows == report_b.rows
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["output_count"] == "2"
    assert payload["rows"][0]["quality_control_risk_score"] == "0.032847"
    assert payload["rows"][0]["specialist_output_digest"] == SHA_A
    assert payload["rows"][0]["derived_validation_digest"] == (
        report_a.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == canonical_payload_digest(payload)
    assert_no_float_values(payload)
    json.loads(encoded)

    leaked_fragments = (
        "candidate-raw-123",
        "market-slug",
        "will-this-happen",
        "https://example.test/source",
        "postgres://",
        "secret-token",
        "wallet",
        "order",
        "trade",
    )
    assert not any(fragment in encoded for fragment in leaked_fragments)

    tampered = dict(payload)
    tampered["block_count"] = "7"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_quality_control_report_payload(tampered)

    object.__setattr__(report_a.rows[0], "quality_control_risk_score", d("0.000001"))
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        module.research_team_specialist_quality_control_report_payload(report_a)

    with pytest.raises(ValueError, match="Decimal"):
        module.research_team_specialist_quality_control_report_payload(
            {"score": 1, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="float"):
        module.research_team_specialist_quality_control_report_payload(
            {"score": 0.5, "paper_only": True, "report_only": True, "readonly": True},
        )


def test_public_payload_requires_exact_top_level_schema() -> None:
    module = api()
    payload = module.research_team_specialist_quality_control_report_payload(
        build_report(
            quality_record(
                "team-alpha",
                "specialist-rates",
                SHA_A,
                CAL_A,
                calibration_error_ratio="0.150000",
                memory_age_seconds=90_000,
                bias_flags="1",
                source_families="2",
                review_latency_seconds=4_000,
                correction_required="4",
                correction_covered="3",
            ),
        ),
    )

    with_extra = dict(payload)
    with_extra["quality_label"] = "alpha"
    with pytest.raises(ValueError, match="schema"):
        module.research_team_specialist_quality_control_report_payload(
            resign_payload(with_extra),
        )

    missing_status = dict(payload)
    missing_status.pop("status")
    with pytest.raises(ValueError, match="schema"):
        module.research_team_specialist_quality_control_report_payload(
            resign_payload(missing_status),
        )


def test_public_payload_requires_exact_nested_schema_and_hard_flags() -> None:
    module = api()
    payload = module.research_team_specialist_quality_control_report_payload(
        build_report(
            quality_record(
                "team-alpha",
                "specialist-rates",
                SHA_A,
                CAL_A,
                calibration_error_ratio="0.150000",
                memory_age_seconds=90_000,
                bias_flags="1",
                source_families="2",
                review_latency_seconds=4_000,
                correction_required="4",
                correction_covered="3",
            ),
        ),
    )

    with_extra_row_field = json.loads(json.dumps(payload))
    with_extra_row_field["rows"][0]["quality_label"] = "alpha"
    with_extra_row_field["rows"][0] = resign_payload(with_extra_row_field["rows"][0])
    with pytest.raises(ValueError, match="schema"):
        module.research_team_specialist_quality_control_report_payload(
            resign_payload(with_extra_row_field),
        )

    with_downgraded_row_flag = json.loads(json.dumps(payload))
    with_downgraded_row_flag["rows"][0]["readonly"] = False
    with_downgraded_row_flag["rows"][0] = resign_payload(
        with_downgraded_row_flag["rows"][0],
    )
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_specialist_quality_control_report_payload(
            resign_payload(with_downgraded_row_flag),
        )


def test_public_payload_requires_canonical_decimal_strings() -> None:
    module = api()
    payload = module.research_team_specialist_quality_control_report_payload(
        build_report(
            quality_record(
                "team-alpha",
                "specialist-rates",
                SHA_A,
                CAL_A,
                calibration_error_ratio="0.150000",
                memory_age_seconds=90_000,
                bias_flags="1",
                source_families="2",
                review_latency_seconds=4_000,
                correction_required="4",
                correction_covered="3",
            ),
        ),
    )
    payload["output_count"] = "01"

    with pytest.raises(ValueError, match="canonical"):
        module.research_team_specialist_quality_control_report_payload(
            resign_payload(payload),
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "stale_memory_count",
        "bias_flagged_count",
        "source_diversity_gap_count",
        "delayed_review_count",
        "correction_gap_count",
    ),
)
def test_report_rejects_mismatched_derived_category_counts(field_name: str) -> None:
    report = build_report(
        quality_record(
            "team-alpha",
            "specialist-rates",
            SHA_A,
            CAL_A,
            calibration_error_ratio="0.150000",
            memory_age_seconds=90_000,
            bias_flags="1",
            source_families="2",
            review_latency_seconds=4_000,
            correction_required="4",
            correction_covered="3",
        ),
    )

    with pytest.raises(ValueError, match=field_name):
        replace(
            report,
            **{
                field_name: d("0"),
                "derived_validation_digest": "",
            },
        )


def test_public_dataclasses_do_not_support_subclassing() -> None:
    module = api()

    for class_name in (
        "ResearchTeamSpecialistQualityControlReportConfig",
        "ResearchTeamSpecialistQualityControlRecord",
        "ResearchTeamSpecialistQualityControlRow",
        "ResearchTeamSpecialistQualityControlReasonCodeCount",
        "ResearchTeamSpecialistQualityControlReport",
    ):
        with pytest.raises(TypeError, match="support subclassing"):
            type(f"Unsafe{class_name}", (getattr(module, class_name),), {})


def test_validation_rejects_bad_types_dates_counts_flags_and_unsafe_public_payloads() -> None:
    module = api()
    record = quality_record(
        "team-alpha",
        "specialist-rates",
        SHA_A,
        CAL_A,
        calibration_error_ratio="0.150000",
        memory_age_seconds=90_000,
        bias_flags="1",
        source_families="2",
        review_latency_seconds=4_000,
        correction_required="4",
        correction_covered="3",
    )
    report = build_report(record)

    for value in (config(), record, report.rows[0], report.reason_code_counts[0], report):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(record, paper_only=False)
    with pytest.raises(ValueError, match="calibration_error_ratio"):
        replace(record, calibration_error_ratio=Decimal("1.000001"))
    with pytest.raises(ValueError, match="bias_flag_count"):
        replace(record, bias_flag_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="specialist_output_digest"):
        replace(record, specialist_output_digest="candidate-raw-123")
    for unsafe_public_ref in ("market-slug", "will-this-happen", "Will this happen?"):
        with pytest.raises(ValueError, match="unsafe public"):
            replace(record, team_ref=unsafe_public_ref)
    with pytest.raises(ValueError, match="correction_covered_count"):
        replace(record, correction_covered_count=d("5"))
    with pytest.raises(ValueError, match="review_completed_at"):
        module.ResearchTeamSpecialistQualityControlRecord(
            team_ref="team-alpha",
            specialist_ref="specialist-rates",
            specialist_output_digest=SHA_A,
            calibration_record_digest=CAL_A,
            observed_at=GENERATED_AT,
            memory_last_refreshed_at=GENERATED_AT,
            review_completed_at=GENERATED_AT - timedelta(seconds=1),
            calibration_error_ratio=d("0.100000"),
            bias_flag_count=d("0"),
            source_family_count=d("3"),
            correction_required_count=d("0"),
            correction_covered_count=d("0"),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(record, cfg=config(), generated_at=datetime(2026, 7, 8, 12, 0))

    class MissingOffsetTz(tzinfo):
        def utcoffset(self, dt):  # type: ignore[no-untyped-def]
            return None

        def dst(self, dt):  # type: ignore[no-untyped-def]
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(
            record,
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=MissingOffsetTz()),
        )
    with pytest.raises(ValueError, match="review_completed_at must not be in the future"):
        build_report(
            module.ResearchTeamSpecialistQualityControlRecord(
                team_ref="team-alpha",
                specialist_ref="specialist-rates",
                specialist_output_digest=SHA_A,
                calibration_record_digest=CAL_A,
                observed_at=GENERATED_AT,
                memory_last_refreshed_at=GENERATED_AT,
                review_completed_at=GENERATED_AT + timedelta(seconds=1),
                calibration_error_ratio=d("0.100000"),
                bias_flag_count=d("0"),
                source_family_count=d("3"),
                correction_required_count=d("0"),
                correction_covered_count=d("0"),
            ),
        )

    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_specialist_quality_control_report_payload(
            {
                "candidate_id": "candidate-raw-123",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_specialist_quality_control_report_payload(
            {"note": "https://example.test/source", "paper_only": True, "report_only": True, "readonly": True},
        )
    for unsafe_public_value in ("market-slug", "will-this-happen", "Will this happen?"):
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_team_specialist_quality_control_report_payload(
                {
                    "note": unsafe_public_value,
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )


def test_module_scope_has_no_db_network_wallet_order_sizing_or_live_surface() -> None:
    module = api()
    source_text = inspect.getsource(module)
    tree = ast.parse(source_text)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIST_QUALITY_CONTROL_REPORT_CONFIG_VERSION",
        "RESEARCH_TEAM_SPECIALIST_QUALITY_CONTROL_STATUSES",
        "ResearchTeamSpecialistQualityControlReportConfig",
        "ResearchTeamSpecialistQualityControlRecord",
        "ResearchTeamSpecialistQualityControlReasonCodeCount",
        "ResearchTeamSpecialistQualityControlRow",
        "ResearchTeamSpecialistQualityControlReport",
        "build_research_team_specialist_quality_control_report",
        "research_team_specialist_quality_control_report_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    forbidden_source_terms = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "private_key",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "auth",
        "live",
        "network",
        "connect(",
        "open(",
        "subprocess",
        "pathlib",
    )
    lowered = source_text.lower()
    assert all(term not in lowered for term in forbidden_source_terms)
