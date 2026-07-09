from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from hashlib import sha256
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _MissingOffsetTimezone(tzinfo):
    def utcoffset(self, value: datetime | None) -> None:
        return None

    def dst(self, value: datetime | None) -> None:
        return None

    def tzname(self, value: datetime | None) -> str:
        return "missing-offset"


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_memory_feedback_resolution_sla_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "unresolved_watch_age_seconds": d("86400.000000"),
        "unresolved_block_age_seconds": d("259200.000000"),
        "writeback_watch_ratio_floor": d("0.800000"),
        "writeback_block_ratio_floor": d("0.500000"),
        "calibration_backlog_watch_count": d("1"),
        "calibration_backlog_block_count": d("3"),
        "impacted_domain_watch_count": d("2"),
        "impacted_domain_block_count": d("3"),
        "reviewer_availability_watch_ratio_floor": d("0.500000"),
        "reviewer_availability_block_ratio_floor": d("0.250000"),
        "manual_escalation_watch_urgency": d("0.500000"),
        "manual_escalation_block_urgency": d("0.800000"),
    }
    values.update(overrides)
    return module.ResearchTeamMemoryFeedbackResolutionSlaConfig(**values)


def feedback(**overrides: object) -> Any:
    module = api()
    values = {
        "feedback_key": "candidate-raw-001",
        "team_id": "politics",
        "category_id": "politics",
        "feedback_created_at": GENERATED_AT - timedelta(hours=6),
        "resolved_at": GENERATED_AT - timedelta(hours=1),
        "writeback_completed_at": GENERATED_AT - timedelta(minutes=30),
        "calibration_required": False,
        "calibration_completed_at": None,
        "impacted_domain_ids": ("policy",),
        "required_reviewer_count": d("2"),
        "available_reviewer_count": d("2"),
        "manual_escalation_requested": False,
    }
    values.update(overrides)
    return module.ResearchTeamMemoryFeedbackResolutionSlaInput(**values)


def build_report(*rows: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_team_memory_feedback_resolution_sla_report(
        rows,
        config=config(),
        generated_at=generated_at,
    )


def resign_payload(payload: dict[str, object]) -> dict[str, object]:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    payload["derived_validation_digest"] = sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()
    return payload


def assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_decimal_only_numerics(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only_numerics(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_decimal_only_numerics(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_decimal_only_numerics(item)


def test_report_aggregates_resolution_sla_pressure_without_raw_identifiers() -> None:
    module = api()

    report = build_report(
        feedback(
            feedback_key="candidate-raw-001",
            feedback_created_at=datetime(
                2026,
                7,
                4,
                4,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            resolved_at=None,
            writeback_completed_at=None,
            calibration_required=True,
            impacted_domain_ids=("elections", "policy", "rates"),
            required_reviewer_count=d("4"),
            available_reviewer_count=d("0"),
            manual_escalation_requested=True,
        ),
        feedback(
            feedback_key="market-raw-002",
            feedback_created_at=GENERATED_AT - timedelta(hours=12),
            impacted_domain_ids=("policy",),
            required_reviewer_count=d("4"),
            available_reviewer_count=d("2"),
        ),
        feedback(
            feedback_key="market-slug-raw-003",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            feedback_created_at=GENERATED_AT - timedelta(days=2),
            resolved_at=None,
            writeback_completed_at=GENERATED_AT - timedelta(hours=4),
            calibration_required=True,
            impacted_domain_ids=("bitcoin", "rates"),
            required_reviewer_count=d("2"),
            available_reviewer_count=d("1"),
        ),
    )

    assert type(report) is module.ResearchTeamMemoryFeedbackResolutionSlaReport
    assert report.report_status == "block"
    assert report.team_category_count == d("2")
    assert report.feedback_count == d("3")
    assert report.unresolved_feedback_count == d("2")
    assert report.max_unresolved_feedback_age_seconds == d("360000.000000")
    assert report.writeback_completed_count == d("2")
    assert report.writeback_completeness_ratio == d("0.666667")
    assert report.calibration_backlog_count == d("2")
    assert report.impacted_domain_count == d("4")
    assert report.min_reviewer_availability_ratio == d("0.000000")
    assert report.manual_escalation_urgency_score == d("1.000000")
    assert report.reason_codes == (
        "feedback_resolution_sla_unresolved_age_block",
        "feedback_resolution_sla_unresolved_age_watch",
        "feedback_resolution_sla_calibration_backlog_watch",
        "feedback_resolution_sla_impacted_domain_block",
        "feedback_resolution_sla_impacted_domain_watch",
        "feedback_resolution_sla_reviewer_availability_block",
        "feedback_resolution_sla_manual_escalation_block",
        "feedback_resolution_sla_manual_escalation_watch",
    )

    assert tuple((row.row_status, row.category_id, row.team_id) for row in report.rows) == (
        ("block", "politics", "politics"),
        ("watch", "finance.crypto.btc", "crypto_btc"),
    )
    assert tuple(row.feedback_count for row in report.rows) == (d("2"), d("1"))

    politics = report.rows[0]
    assert politics.unresolved_feedback_count == d("1")
    assert politics.max_unresolved_feedback_age_seconds == d("360000.000000")
    assert politics.writeback_completed_count == d("1")
    assert politics.writeback_completeness_ratio == d("0.500000")
    assert politics.calibration_backlog_count == d("1")
    assert politics.impacted_domain_count == d("3")
    assert politics.min_reviewer_availability_ratio == d("0.000000")
    assert politics.manual_escalation_urgency_score == d("1.000000")
    assert politics.reason_codes == (
        "feedback_resolution_sla_unresolved_age_block",
        "feedback_resolution_sla_calibration_backlog_watch",
        "feedback_resolution_sla_impacted_domain_block",
        "feedback_resolution_sla_reviewer_availability_block",
        "feedback_resolution_sla_manual_escalation_block",
    )

    crypto = report.rows[1]
    assert crypto.row_status == "watch"
    assert crypto.reason_codes == (
        "feedback_resolution_sla_unresolved_age_watch",
        "feedback_resolution_sla_calibration_backlog_watch",
        "feedback_resolution_sla_impacted_domain_watch",
        "feedback_resolution_sla_manual_escalation_watch",
    )

    payload = module.research_team_memory_feedback_resolution_sla_report_payload(report)
    public_text = repr(payload)
    for raw_fragment in (
        "candidate-raw-001",
        "market-raw-002",
        "market-slug-raw-003",
        "question",
        "https://",
        "postgres://",
        "private-token",
    ):
        assert raw_fragment not in public_text
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["rows"][0]["manual_escalation_urgency_score"] == "1.000000"
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    assert_no_float_values(payload)


def test_empty_and_clear_reports_are_digest_backed_with_exact_statuses() -> None:
    module = api()

    empty = build_report()
    assert empty.report_status == "block"
    assert empty.reason_codes == ("feedback_resolution_sla_empty",)
    assert empty.rows == ()
    assert empty.feedback_count == d("0")
    assert empty.writeback_completeness_ratio == d("0.000000")

    clear = build_report(feedback(feedback_key="clear-feedback"))
    assert clear.report_status == "pass"
    assert clear.rows[0].row_status == "pass"
    assert clear.reason_codes == ("feedback_resolution_sla_clear",)
    assert clear.rows[0].reason_codes == ("feedback_resolution_sla_clear",)
    assert clear.derived_validation_digest != empty.derived_validation_digest

    payload = module.research_team_memory_feedback_resolution_sla_report_payload(clear)
    assert module.research_team_memory_feedback_resolution_sla_report_payload(payload) == payload
    tampered = dict(payload)
    tampered["feedback_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_memory_feedback_resolution_sla_report_payload(tampered)


def test_payload_digest_is_canonical_and_input_order_independent() -> None:
    module = api()
    alpha = feedback(feedback_key="alpha-feedback")
    beta = feedback(
        feedback_key="beta-feedback",
        team_id="crypto_btc",
        category_id="finance.crypto.btc",
    )

    first = build_report(alpha, beta)
    second = build_report(beta, alpha)
    first_payload = module.research_team_memory_feedback_resolution_sla_report_payload(
        first,
    )
    second_payload = module.research_team_memory_feedback_resolution_sla_report_payload(
        second,
    )

    assert first == second
    assert first_payload == second_payload
    unsigned_payload = dict(first_payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    canonical_payload = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert digest == sha256(canonical_payload.encode("utf-8")).hexdigest()


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    sample_config = config()
    sample_input = feedback()
    sample_report = build_report(sample_input)
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_input, sample_row, sample_report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_decimal_only_numerics(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchTeamMemoryFeedbackResolutionSlaConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        feedback(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(feedback(readonly=False))


def test_public_dataclasses_are_final() -> None:
    module = api()

    for public_type in (
        module.ResearchTeamMemoryFeedbackResolutionSlaConfig,
        module.ResearchTeamMemoryFeedbackResolutionSlaInput,
        module.ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow,
        module.ResearchTeamMemoryFeedbackResolutionSlaReport,
    ):
        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"Unsafe{public_type.__name__}", (public_type,), {})


def test_integral_decimal_counts_reject_fractional_precision_before_quantization() -> None:
    with pytest.raises(ValueError, match="integral"):
        config(calibration_backlog_watch_count=d("1.0000004"))
    with pytest.raises(ValueError, match="integral"):
        feedback(required_reviewer_count=d("2.0000004"))


def test_validates_inputs_config_time_order_and_public_payload_safety() -> None:
    module = api()
    good = feedback()

    with pytest.raises(ValueError, match="Decimal"):
        config(unresolved_watch_age_seconds=86400)
    with pytest.raises(ValueError, match="Decimal"):
        config(writeback_watch_ratio_floor=_DecimalSubclass("0.8"))
    with pytest.raises(ValueError, match="timezone-aware"):
        feedback(feedback_created_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        feedback(
            feedback_created_at=datetime(
                2026,
                7,
                8,
                11,
                0,
                tzinfo=_MissingOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            good,
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        build_report(
            feedback(
                feedback_created_at=GENERATED_AT + timedelta(seconds=1),
                resolved_at=None,
                writeback_completed_at=None,
            ),
        )
    with pytest.raises(ValueError, match="writeback_completed_at"):
        feedback(
            feedback_created_at=GENERATED_AT - timedelta(hours=2),
            writeback_completed_at=GENERATED_AT - timedelta(hours=3),
        )
    with pytest.raises(ValueError, match="calibration_completed_at"):
        feedback(calibration_required=False, calibration_completed_at=GENERATED_AT)
    with pytest.raises(ValueError, match="available_reviewer_count"):
        feedback(required_reviewer_count=d("1"), available_reviewer_count=d("2"))
    with pytest.raises(ValueError, match="category_id"):
        feedback(team_id="crypto_btc", category_id="politics")
    with pytest.raises(ValueError, match="unique"):
        build_report(good, feedback(feedback_key=good.feedback_key))
    with pytest.raises(ValueError, match="input rows"):
        module.build_research_team_memory_feedback_resolution_sla_report(
            (object(),),
            config=config(),
            generated_at=GENERATED_AT,
        )

    payload = module.research_team_memory_feedback_resolution_sla_report_payload(
        build_report(good),
    )
    unsafe = dict(payload)
    unsafe["source_url"] = "https://example.invalid/raw-text"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_memory_feedback_resolution_sla_report_payload(unsafe)


def test_publication_rejects_tampering_and_noncanonical_public_schemas() -> None:
    module = api()

    flag_tampered_report = build_report(feedback(feedback_key="flag-tamper"))
    object.__setattr__(flag_tampered_report, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        module.research_team_memory_feedback_resolution_sla_report_payload(
            flag_tampered_report,
        )

    count_tampered_report = build_report(feedback(feedback_key="count-tamper"))
    object.__setattr__(count_tampered_report, "feedback_count", d("2"))
    with pytest.raises(ValueError, match="feedback_count|derived_validation_digest"):
        module.research_team_memory_feedback_resolution_sla_report_payload(
            count_tampered_report,
        )

    payload = module.research_team_memory_feedback_resolution_sla_report_payload(
        build_report(feedback(feedback_key="public-schema")),
    )

    extra_field = resign_payload({**payload, "memo": "redacted"})
    with pytest.raises(ValueError, match="fields"):
        module.research_team_memory_feedback_resolution_sla_report_payload(extra_field)

    missing_field = dict(payload)
    missing_field.pop("report_status")
    resign_payload(missing_field)
    with pytest.raises(ValueError, match="fields"):
        module.research_team_memory_feedback_resolution_sla_report_payload(missing_field)

    nested_flag = json.loads(json.dumps(payload))
    nested_flag["rows"][0]["report_only"] = False
    resign_payload(nested_flag)
    with pytest.raises(ValueError, match="report_only"):
        module.research_team_memory_feedback_resolution_sla_report_payload(nested_flag)

    noncanonical_decimal = dict(payload)
    noncanonical_decimal["feedback_count"] = "1.0"
    resign_payload(noncanonical_decimal)
    with pytest.raises(ValueError, match="canonical Decimal"):
        module.research_team_memory_feedback_resolution_sla_report_payload(
            noncanonical_decimal,
        )

    numeric_value = dict(payload)
    numeric_value["feedback_count"] = 1
    resign_payload(numeric_value)
    with pytest.raises(ValueError, match="Decimal"):
        module.research_team_memory_feedback_resolution_sla_report_payload(
            numeric_value,
        )

    for field_name, signed_zero in (
        ("unresolved_feedback_count", "-0"),
        ("max_unresolved_feedback_age_seconds", "-0.000000"),
        ("writeback_completeness_ratio", "-0.000000"),
    ):
        signed_zero_payload = json.loads(json.dumps(payload))
        signed_zero_payload[field_name] = signed_zero
        resign_payload(signed_zero_payload)
        with pytest.raises(ValueError, match="canonical Decimal"):
            module.research_team_memory_feedback_resolution_sla_report_payload(
                signed_zero_payload,
            )

    nested_signed_zero = json.loads(json.dumps(payload))
    nested_signed_zero["rows"][0]["manual_escalation_urgency_score"] = "-0.000000"
    resign_payload(nested_signed_zero)
    with pytest.raises(ValueError, match="canonical Decimal"):
        module.research_team_memory_feedback_resolution_sla_report_payload(
            nested_signed_zero,
        )

    nested_extra_field = json.loads(json.dumps(payload))
    nested_extra_field["rows"][0]["memo"] = "redacted"
    resign_payload(nested_extra_field)
    with pytest.raises(ValueError, match="fields"):
        module.research_team_memory_feedback_resolution_sla_report_payload(
            nested_extra_field,
        )

    contradictory_reasons = json.loads(json.dumps(payload))
    contradictory_reasons["rows"][0]["row_status"] = "block"
    contradictory_reasons["rows"][0]["reason_codes"] = [
        module.UNRESOLVED_AGE_BLOCK_REASON,
        module.CLEAR_REASON,
    ]
    contradictory_reasons["report_status"] = "block"
    contradictory_reasons["reason_codes"] = [module.UNRESOLVED_AGE_BLOCK_REASON]
    resign_payload(contradictory_reasons)
    with pytest.raises(ValueError, match="clear reason"):
        module.research_team_memory_feedback_resolution_sla_report_payload(
            contradictory_reasons,
        )


def test_module_scope_is_pure_report_only_without_live_or_persistence_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "wallet",
        "authentication",
        "authorize",
        "account",
        "broker",
        "order",
        "trade",
        "live execution",
        "submit",
        "cancel",
        "recommendation",
        "sizing",
        "requests",
        "httpx",
        "psycopg",
        "sqlalchemy",
        "sqlite",
        "socket",
        "subprocess",
        "web3",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "write",
                "write_text",
                "write_bytes",
                "touch",
                "mkdir",
                "unlink",
                "rename",
                "request",
                "post",
                "put",
                "patch",
                "delete",
            }

    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in (
            "cli",
            "db",
            "env",
            "httpx",
            "os",
            "pathlib",
            "pickle",
            "psycopg",
            "requests",
            "shelve",
            "shutil",
            "socket",
            "subprocess",
            "supabase",
            "tempfile",
            "urllib",
            "web3",
        )
    )
