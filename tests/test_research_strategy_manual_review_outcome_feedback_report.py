from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Context, Decimal, Inexact, ROUND_DOWN, localcontext
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_manual_review_outcome_feedback_report import (
    DEFAULT_RESEARCH_STRATEGY_MANUAL_REVIEW_OUTCOME_FEEDBACK_REPORT_CONFIG_VERSION,
    REVIEW_OUTCOMES,
    STATUSES,
    ResearchStrategyManualReviewOutcomeFeedbackConfig,
    ResearchStrategyManualReviewOutcomeFeedbackInput,
    ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount,
    ResearchStrategyManualReviewOutcomeFeedbackReport,
    ResearchStrategyManualReviewOutcomeFeedbackRow,
    build_research_strategy_manual_review_outcome_feedback_report,
    research_strategy_manual_review_outcome_feedback_report_payload,
    validate_research_strategy_manual_review_outcome_feedback_public_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
REVIEWED_AT = GENERATED_AT - timedelta(hours=2)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_manual_review_outcome_feedback_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyManualReviewOutcomeFeedbackConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_MANUAL_REVIEW_OUTCOME_FEEDBACK_REPORT_CONFIG_VERSION
        ),
        "watch_min_calibration_delta": d("0.020000"),
        "block_min_calibration_delta": d("-0.050000"),
        "watch_min_evidence_usefulness_score": d("0.600000"),
        "block_min_evidence_usefulness_score": d("0.400000"),
        "watch_max_cost_estimate_error": d("0.150000"),
        "block_max_cost_estimate_error": d("0.300000"),
        "watch_min_resolution_clarity_score": d("0.700000"),
        "block_min_resolution_clarity_score": d("0.500000"),
        "watch_min_memory_update_completeness_score": d("0.800000"),
        "block_min_memory_update_completeness_score": d("0.500000"),
        "min_pass_outcome_count": d("10.000000"),
        "min_watch_outcome_count": d("3.000000"),
    }
    values.update(overrides)
    return ResearchStrategyManualReviewOutcomeFeedbackConfig(**values)


def review_input(
    review_group_id: str = "macro-feedback",
    strategy_area: str = "rates",
    *,
    review_outcome: str = "confirmed",
    pre_review_calibration_error: Decimal = d("0.180000"),
    post_review_calibration_error: Decimal = d("0.080000"),
    evidence_usefulness_score: Decimal = d("0.900000"),
    cost_estimate_error: Decimal = d("0.050000"),
    resolution_clarity_score: Decimal = d("0.920000"),
    memory_update_completeness_score: Decimal = d("0.950000"),
    outcome_count: Decimal = d("20.000000"),
    reviewed_at: datetime = REVIEWED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyManualReviewOutcomeFeedbackInput:
    return ResearchStrategyManualReviewOutcomeFeedbackInput(
        review_group_id=review_group_id,
        strategy_area=strategy_area,
        review_outcome=review_outcome,
        pre_review_calibration_error=pre_review_calibration_error,
        post_review_calibration_error=post_review_calibration_error,
        evidence_usefulness_score=evidence_usefulness_score,
        cost_estimate_error=cost_estimate_error,
        resolution_clarity_score=resolution_clarity_score,
        memory_update_completeness_score=memory_update_completeness_score,
        outcome_count=outcome_count,
        reviewed_at=reviewed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *items: ResearchStrategyManualReviewOutcomeFeedbackInput,
    cfg: ResearchStrategyManualReviewOutcomeFeedbackConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyManualReviewOutcomeFeedbackReport:
    return build_research_strategy_manual_review_outcome_feedback_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def payload_with_recomputed_digest(payload: dict[str, Any]) -> dict[str, Any]:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return {
        **digest_payload,
        "derived_validation_digest": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
    }


def payload_with_all_recomputed_digests(payload: dict[str, Any]) -> dict[str, Any]:
    recomputed = json.loads(json.dumps(payload, allow_nan=False, sort_keys=True))
    rows = recomputed.get("rows")
    if type(rows) is list:
        recomputed["rows"] = [
            payload_with_recomputed_digest(row) if type(row) is dict else row
            for row in rows
        ]
    return payload_with_recomputed_digest(recomputed)


def test_report_summarizes_manual_review_outcome_feedback_quality_safely() -> None:
    report = build_report(
        review_input(),
        review_input(
            "policy-feedback",
            "courts",
            review_outcome="revised",
            pre_review_calibration_error=d("0.140000"),
            post_review_calibration_error=d("0.130000"),
            evidence_usefulness_score=d("0.550000"),
            cost_estimate_error=d("0.200000"),
            resolution_clarity_score=d("0.650000"),
            memory_update_completeness_score=d("0.700000"),
            outcome_count=d("5.000000"),
        ),
        review_input(
            "crypto-feedback",
            "protocol",
            review_outcome="overturned",
            pre_review_calibration_error=d("0.200000"),
            post_review_calibration_error=d("0.280000"),
            evidence_usefulness_score=d("0.300000"),
            cost_estimate_error=d("0.400000"),
            resolution_clarity_score=d("0.400000"),
            memory_update_completeness_score=d("0.450000"),
            outcome_count=d("2.000000"),
        ),
    )

    assert is_dataclass(report)
    assert STATUSES == ("pass", "watch", "block")
    assert REVIEW_OUTCOMES == ("confirmed", "revised", "overturned", "ambiguous")
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.feedback_queue_count == d("2.000000")
    assert report.feedback_queue_ratio == d("0.666667")
    assert report.memory_update_incomplete_count == d("2.000000")
    assert report.average_calibration_delta == d("0.010000")
    assert report.min_calibration_delta == d("-0.080000")
    assert report.average_evidence_usefulness_score == d("0.583333")
    assert report.average_cost_estimate_error == d("0.216667")
    assert report.max_cost_estimate_error == d("0.400000")
    assert report.average_resolution_clarity_score == d("0.656667")
    assert report.average_memory_update_completeness_score == d("0.700000")
    assert report.reason_codes == (
        "manual_review_outcome_feedback_block",
        "calibration_delta_block",
        "evidence_usefulness_block",
        "cost_estimate_error_block",
        "resolution_clarity_block",
        "memory_update_completeness_block",
        "sample_size_low_block",
        "calibration_delta_watch",
        "evidence_usefulness_watch",
        "cost_estimate_error_watch",
        "resolution_clarity_watch",
        "memory_update_completeness_watch",
        "sample_size_low_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)

    block_row, watch_row, pass_row = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert block_row.review_group_id == "crypto-feedback"
    assert block_row.strategy_area == "protocol"
    assert block_row.calibration_delta == d("-0.080000")
    assert block_row.reason_codes == (
        "calibration_delta_block",
        "evidence_usefulness_block",
        "cost_estimate_error_block",
        "resolution_clarity_block",
        "memory_update_completeness_block",
        "sample_size_low_block",
    )
    assert watch_row.calibration_delta == d("0.010000")
    assert watch_row.reason_codes == (
        "calibration_delta_watch",
        "evidence_usefulness_watch",
        "cost_estimate_error_watch",
        "resolution_clarity_watch",
        "memory_update_completeness_watch",
        "sample_size_low_watch",
    )
    assert pass_row.reason_codes == ("manual_review_outcome_feedback_pass",)
    assert ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount(
        reason_code="calibration_delta_block",
        count=d("1.000000"),
        row_ratio=d("0.333333"),
    ) in report.reason_code_counts

    payload = research_strategy_manual_review_outcome_feedback_report_payload(report)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["status"] == "block"
    assert payload["feedback_queue_count"] == "2.000000"
    assert payload["rows"][0]["derived_validation_digest"] == block_row.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert validate_research_strategy_manual_review_outcome_feedback_public_payload(payload)
    assert_no_public_numeric_values(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    forbidden_payload_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    lowered_keys = tuple(key.lower() for key in payload_keys(payload))
    assert not any(
        fragment in key
        for key in lowered_keys
        for fragment in forbidden_payload_fragments
    )


def test_public_contract_is_frozen_decimal_digest_bound_and_surface_safe() -> None:
    module_classes = (
        ResearchStrategyManualReviewOutcomeFeedbackConfig,
        ResearchStrategyManualReviewOutcomeFeedbackInput,
        ResearchStrategyManualReviewOutcomeFeedbackReasonCodeCount,
        ResearchStrategyManualReviewOutcomeFeedbackRow,
        ResearchStrategyManualReviewOutcomeFeedbackReport,
    )
    for klass in module_classes:
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    report = build_report(review_input())
    for value in (config(), review_input(), report, *report.reason_code_counts, *report.rows):
        for field in fields(value):
            field_value = getattr(value, field.name)
            assert type(field_value) is not float
            if field.name.endswith(
                (
                    "_count",
                    "_ratio",
                    "_score",
                    "_error",
                    "_delta",
                ),
            ):
                assert field_value is None or type(field_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        review_input(paper_only=False)
    with pytest.raises(TypeError, match="subclass"):
        type("DerivedConfig", (ResearchStrategyManualReviewOutcomeFeedbackConfig,), {})
    with pytest.raises(TypeError, match="subclass"):
        type("DerivedRow", (ResearchStrategyManualReviewOutcomeFeedbackRow,), {})
    with pytest.raises(ValueError, match="pre_review_calibration_error"):
        review_input(pre_review_calibration_error=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_calibration_delta"):
        config(watch_min_calibration_delta=_DecimalSubclass("0.020000"))
    with pytest.raises(ValueError, match="reviewed_at must be a datetime"):
        review_input(reviewed_at=_DatetimeSubclass(2026, 7, 8, 10, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="reviewed_at must be timezone-aware"):
        review_input(reviewed_at=datetime(2026, 7, 8, 10, 0))
    with pytest.raises(ValueError, match="duplicate manual review feedback"):
        build_report(review_input(), review_input())
    with pytest.raises(ValueError, match="after generated_at"):
        build_report(review_input(reviewed_at=GENERATED_AT + timedelta(seconds=1)))

    eastern = timezone(timedelta(hours=-4))
    tz_report = build_report(
        review_input(reviewed_at=datetime(2026, 7, 8, 6, 0, tzinfo=eastern)),
    )
    assert tz_report.rows[0].reviewed_at == datetime(2026, 7, 8, 10, 0, tzinfo=UTC)

    payload = research_strategy_manual_review_outcome_feedback_report_payload(report)
    with pytest.raises(ValueError, match="numeric"):
        validate_research_strategy_manual_review_outcome_feedback_public_payload(
            {**payload, "row_count": 1},
        )
    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_strategy_manual_review_outcome_feedback_public_payload(missing_digest)
    for flag_name in ("paper_only", "report_only", "readonly"):
        missing_flag_payload = dict(payload)
        missing_flag_payload.pop(flag_name)
        with pytest.raises(ValueError, match=flag_name):
            validate_research_strategy_manual_review_outcome_feedback_public_payload(
                payload_with_recomputed_digest(missing_flag_payload),
            )

        nested_missing_flag_payload = {
            **payload,
            "rows": [
                {key: item for key, item in payload["rows"][0].items() if key != flag_name},
            ],
        }
        with pytest.raises(ValueError, match=flag_name):
            validate_research_strategy_manual_review_outcome_feedback_public_payload(
                payload_with_recomputed_digest(nested_missing_flag_payload),
            )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_strategy_manual_review_outcome_feedback_public_payload(
            {**payload, "block_count": "9.000000"},
        )
    for forbidden_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question_text",
        "source_url",
        "wallet_address",
        "order_id",
        "trade_id",
        "live_surface",
        "database_dsn",
        "table_name",
        "auth_token",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            validate_research_strategy_manual_review_outcome_feedback_public_payload(
                {**payload, forbidden_key: "not allowed"},
            )
    for forbidden_value in (
        "candidate_id leaked",
        "raw market slug leaked",
        "wallet configured",
        "order configured",
        "trade configured",
        "live surface configured",
        "database configured",
        "token configured",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            validate_research_strategy_manual_review_outcome_feedback_public_payload(
                {**payload, "operator_note": forbidden_value},
            )

    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    forbidden_import_modules = {
        "asyncio",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
        "py_clob_client",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_modules
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_modules

    lowered_source = source.lower()
    forbidden_source_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_text",
        "raw_text",
        "source_url",
        "private_key",
        "wallet",
        "auth_token",
        "network_client",
        "database_url",
        "database_dsn",
        "table_name",
        "place_order",
        "create_order",
        "cancel_order",
        "live_trading",
        "trade_id",
        "position_size",
        "recommended_size",
        "open(",
        "requests.",
        "httpx.",
        "socket.",
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in lowered_source


def test_decimal_math_is_isolated_from_the_ambient_context() -> None:
    items = (
        review_input(),
        review_input(
            "policy-feedback",
            "courts",
            pre_review_calibration_error=d("0.140000"),
            post_review_calibration_error=d("0.130000"),
            evidence_usefulness_score=d("0.550000"),
            cost_estimate_error=d("0.200000"),
            resolution_clarity_score=d("0.650000"),
            memory_update_completeness_score=d("0.700000"),
            outcome_count=d("5.000000"),
        ),
        review_input(
            "crypto-feedback",
            "protocol",
            pre_review_calibration_error=d("0.200000"),
            post_review_calibration_error=d("0.280000"),
            evidence_usefulness_score=d("0.300000"),
            cost_estimate_error=d("0.400000"),
            resolution_clarity_score=d("0.400000"),
            memory_update_completeness_score=d("0.450000"),
            outcome_count=d("2.000000"),
        ),
    )
    expected = build_report(*items)
    hostile_context = Context(prec=3, rounding=ROUND_DOWN)
    hostile_context.traps[Inexact] = True

    with localcontext(hostile_context):
        observed = build_report(*items)

    assert observed == expected
    assert (
        research_strategy_manual_review_outcome_feedback_report_payload(observed)
        == research_strategy_manual_review_outcome_feedback_report_payload(expected)
    )


def test_decimal_validation_uses_raw_values_before_quantization() -> None:
    with pytest.raises(ValueError, match="integral"):
        config(min_pass_outcome_count=d("10.0000004"))
    with pytest.raises(ValueError, match="integral"):
        review_input(outcome_count=d("3.0000004"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        review_input(evidence_usefulness_score=d("1.0000004"))
    with pytest.raises(ValueError, match="between -1 and 1"):
        config(watch_min_calibration_delta=d("-1.0000004"))


@pytest.mark.parametrize(
    "value",
    (
        d("-0"),
        d("-0.000000"),
        d("NaN"),
        d("sNaN"),
        d("Infinity"),
        d("-Infinity"),
    ),
)
def test_decimal_inputs_reject_signed_zero_and_non_finite_values(
    value: Decimal,
) -> None:
    expected_message = "signed zero" if value.is_zero() and value.is_signed() else "finite"
    with pytest.raises(ValueError, match=expected_message):
        review_input(pre_review_calibration_error=value)
    with pytest.raises(ValueError, match=expected_message):
        config(watch_min_calibration_delta=value)


def test_rows_use_complete_stable_quality_sorting() -> None:
    items = (
        review_input(
            "a-clarity",
            "rates",
            resolution_clarity_score=d("0.690000"),
        ),
        review_input(
            "z-clarity",
            "rates",
            resolution_clarity_score=d("0.510000"),
        ),
        review_input(
            "a-memory",
            "rates",
            memory_update_completeness_score=d("0.790000"),
        ),
        review_input(
            "z-memory",
            "rates",
            memory_update_completeness_score=d("0.510000"),
        ),
        review_input(
            "a-sample",
            "rates",
            outcome_count=d("9.000000"),
        ),
        review_input(
            "z-sample",
            "rates",
            outcome_count=d("3.000000"),
        ),
        review_input(
            "a-newer",
            "rates",
            outcome_count=d("5.000000"),
            reviewed_at=REVIEWED_AT + timedelta(minutes=1),
        ),
        review_input(
            "z-older",
            "rates",
            outcome_count=d("5.000000"),
            reviewed_at=REVIEWED_AT - timedelta(minutes=1),
        ),
    )

    first = build_report(*items)
    second = build_report(*reversed(items))

    assert tuple(row.review_group_id for row in first.rows) == (
        "z-clarity",
        "a-clarity",
        "z-memory",
        "a-memory",
        "z-sample",
        "z-older",
        "a-newer",
        "a-sample",
    )
    assert second == first
    assert (
        research_strategy_manual_review_outcome_feedback_report_payload(second)
        == research_strategy_manual_review_outcome_feedback_report_payload(first)
    )


def test_public_payload_requires_the_exact_canonical_schema() -> None:
    payload = research_strategy_manual_review_outcome_feedback_report_payload(
        build_report(
            review_input(
                resolution_clarity_score=d("0.650000"),
                memory_update_completeness_score=d("0.700000"),
                outcome_count=d("5.000000"),
            ),
        ),
    )

    malformed_payloads: list[dict[str, Any]] = []

    extra_report_field = {**payload, "operator_note": "redacted"}
    malformed_payloads.append(payload_with_recomputed_digest(extra_report_field))

    missing_report_field = dict(payload)
    missing_report_field.pop("status")
    malformed_payloads.append(payload_with_recomputed_digest(missing_report_field))

    extra_row_field = json.loads(json.dumps(payload))
    extra_row_field["rows"][0]["operator_note"] = "redacted"
    malformed_payloads.append(payload_with_recomputed_digest(extra_row_field))

    missing_row_field = json.loads(json.dumps(payload))
    missing_row_field["rows"][0].pop("review_outcome")
    malformed_payloads.append(payload_with_recomputed_digest(missing_row_field))

    extra_reason_count_field = json.loads(json.dumps(payload))
    extra_reason_count_field["reason_code_counts"][0]["operator_note"] = "redacted"
    malformed_payloads.append(payload_with_recomputed_digest(extra_reason_count_field))

    noncanonical_decimal = dict(payload)
    noncanonical_decimal["row_count"] = "1.0"
    malformed_payloads.append(payload_with_recomputed_digest(noncanonical_decimal))

    noncanonical_datetime = dict(payload)
    noncanonical_datetime["generated_at"] = "2026-07-08T12:00:00Z"
    malformed_payloads.append(payload_with_recomputed_digest(noncanonical_datetime))

    signed_zero = dict(payload)
    signed_zero["feedback_queue_ratio"] = "-0.000000"
    malformed_payloads.append(payload_with_recomputed_digest(signed_zero))

    for malformed in malformed_payloads:
        with pytest.raises(ValueError):
            validate_research_strategy_manual_review_outcome_feedback_public_payload(
                malformed,
            )


def test_resigned_payload_recomputes_all_derived_fields() -> None:
    payload = research_strategy_manual_review_outcome_feedback_report_payload(
        build_report(
            review_input(
                resolution_clarity_score=d("0.650000"),
                memory_update_completeness_score=d("0.700000"),
                outcome_count=d("5.000000"),
            ),
        ),
    )

    forged_memory_flag = json.loads(json.dumps(payload))
    forged_memory_flag["rows"][0]["memory_update_incomplete"] = False
    forged_memory_flag["memory_update_incomplete_count"] = "0.000000"
    forged_memory_flag = payload_with_all_recomputed_digests(forged_memory_flag)
    with pytest.raises(ValueError, match="memory_update_incomplete"):
        validate_research_strategy_manual_review_outcome_feedback_public_payload(
            forged_memory_flag,
        )

    forged_average = dict(payload)
    forged_average["average_cost_estimate_error"] = "0.060000"
    forged_average = payload_with_recomputed_digest(forged_average)
    with pytest.raises(ValueError, match="average_cost_estimate_error"):
        validate_research_strategy_manual_review_outcome_feedback_public_payload(
            forged_average,
        )


def test_row_and_report_digests_use_canonical_sha256() -> None:
    report = build_report(
        review_input(),
        review_input(
            "policy-feedback",
            "courts",
            resolution_clarity_score=d("0.650000"),
            outcome_count=d("5.000000"),
        ),
    )
    payload = research_strategy_manual_review_outcome_feedback_report_payload(report)
    unsigned_report = dict(payload)
    report_digest = unsigned_report.pop("derived_validation_digest")
    encoded_report = json.dumps(
        unsigned_report,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert report_digest == hashlib.sha256(encoded_report.encode("utf-8")).hexdigest()

    for row in payload["rows"]:
        unsigned_row = dict(row)
        row_digest = unsigned_row.pop("derived_validation_digest")
        encoded_row = json.dumps(
            unsigned_row,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        assert row_digest == hashlib.sha256(encoded_row.encode("utf-8")).hexdigest()
