from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_memory_review_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def at_age(seconds: int) -> datetime:
    return GENERATED_AT - timedelta(seconds=seconds)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "calibration_age_pressure_weight": d("0.200000"),
        "forecast_miss_recurrence_weight": d("0.250000"),
        "evidence_reuse_quality_weight": d("0.200000"),
        "unresolved_feedback_weight": d("0.150000"),
        "review_capacity_pressure_weight": d("0.200000"),
        "calibration_age_watch_seconds": d("1209600.000000"),
        "calibration_age_block_seconds": d("2592000.000000"),
        "forecast_miss_recurrence_watch_ratio": d("0.250000"),
        "forecast_miss_recurrence_block_ratio": d("0.500000"),
        "evidence_reuse_quality_watch_below": d("0.750000"),
        "evidence_reuse_quality_block_below": d("0.500000"),
        "unresolved_feedback_watch_count": d("2.000000"),
        "unresolved_feedback_block_count": d("5.000000"),
        "review_capacity_pressure_watch_ratio": d("0.700000"),
        "review_capacity_pressure_block_ratio": d("0.900000"),
        "priority_score_watch_threshold": d("0.400000"),
        "priority_score_block_threshold": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainMemoryReviewPriorityConfig(**values)


def review_input(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "domain_key": "politics",
        "team_key": "policy_team",
        "review_reference": "candidate-123 market_slug question https://example.invalid",
        "last_calibrated_at": GENERATED_AT - timedelta(days=2),
        "reviewed_forecast_count": d("10.000000"),
        "recurring_forecast_miss_count": d("1.000000"),
        "evidence_reuse_quality": d("0.900000"),
        "unresolved_feedback_count": d("0.000000"),
        "review_capacity_pressure": d("0.200000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchTeamDomainMemoryReviewPriorityInput(**values)


def build_report(*items: object, cfg: object | None = None, generated_at=GENERATED_AT):
    module = api()
    return module.build_research_team_domain_memory_review_priority_report(
        items,
        generated_at=generated_at,
        config=cfg or config(),
    )


def test_priority_scoring_and_pass_watch_block_rows() -> None:
    built = build_report(
        review_input(
            domain_key="sports",
            team_key="tennis_team",
            review_reference="watch-memory",
            last_calibrated_at=GENERATED_AT - timedelta(days=16),
            reviewed_forecast_count=d("10.000000"),
            recurring_forecast_miss_count=d("2.000000"),
            evidence_reuse_quality=d("0.680000"),
            unresolved_feedback_count=d("2.000000"),
            review_capacity_pressure=d("0.750000"),
        ),
        review_input(
            domain_key="crypto",
            team_key="chain_team",
            review_reference="block-memory",
            last_calibrated_at=GENERATED_AT - timedelta(days=35),
            reviewed_forecast_count=d("10.000000"),
            recurring_forecast_miss_count=d("6.000000"),
            evidence_reuse_quality=d("0.350000"),
            unresolved_feedback_count=d("6.000000"),
            review_capacity_pressure=d("0.950000"),
        ),
        review_input(
            domain_key="politics",
            team_key="policy_team",
            review_reference="pass-memory",
        ),
    )

    assert is_dataclass(built)
    assert built.generated_at == GENERATED_AT
    assert built.report_status == "block"
    assert built.input_count == d("3.000000")
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.average_review_priority_score == d("0.449667")
    assert built.oldest_calibration_age_seconds == d("3024000.000000")
    assert built.max_forecast_miss_recurrence_ratio == d("0.600000")
    assert built.min_evidence_reuse_quality == d("0.350000")
    assert built.max_review_capacity_pressure == d("0.950000")

    crypto_row, sports_row, politics_row = built.rows
    assert tuple(row.priority_rank for row in built.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert (crypto_row.domain_key, sports_row.domain_key, politics_row.domain_key) == (
        "crypto",
        "sports",
        "politics",
    )

    assert crypto_row.priority_status == "block"
    assert crypto_row.calibration_age_seconds == d("3024000.000000")
    assert crypto_row.calibration_age_pressure == d("1.000000")
    assert crypto_row.forecast_miss_recurrence_ratio == d("0.600000")
    assert crypto_row.evidence_reuse_pressure == d("0.650000")
    assert crypto_row.unresolved_feedback_pressure == d("1.000000")
    assert crypto_row.review_priority_score == d("0.820000")
    assert crypto_row.reason_codes == (
        "calibration_age_block",
        "forecast_miss_recurrence_block",
        "evidence_reuse_quality_block",
        "unresolved_feedback_block",
        "review_capacity_pressure_block",
        "review_priority_score_block",
    )

    assert sports_row.priority_status == "watch"
    assert sports_row.calibration_age_pressure == d("0.533333")
    assert sports_row.review_priority_score == d("0.430667")
    assert sports_row.reason_codes == (
        "calibration_age_watch",
        "evidence_reuse_quality_watch",
        "unresolved_feedback_watch",
        "review_capacity_pressure_watch",
        "review_priority_score_watch",
    )

    assert politics_row.priority_status == "pass"
    assert politics_row.review_priority_score == d("0.098333")
    assert politics_row.reason_codes == ("memory_review_priority_pass",)


def test_memory_freshness_thresholds_and_missing_calibration() -> None:
    cfg = config(
        calibration_age_watch_seconds=d("100.000000"),
        calibration_age_block_seconds=d("200.000000"),
    )
    built = build_report(
        review_input(
            domain_key="fresh",
            team_key="team_fresh",
            review_reference="fresh",
            last_calibrated_at=at_age(99),
        ),
        review_input(
            domain_key="watch",
            team_key="team_watch",
            review_reference="watch",
            last_calibrated_at=at_age(100),
        ),
        review_input(
            domain_key="block",
            team_key="team_block",
            review_reference="block",
            last_calibrated_at=at_age(200),
        ),
        review_input(
            domain_key="missing",
            team_key="team_missing",
            review_reference="missing",
            last_calibrated_at=None,
        ),
        cfg=cfg,
    )

    rows = {row.domain_key: row for row in built.rows}

    assert rows["fresh"].priority_status == "pass"
    assert rows["fresh"].calibration_age_seconds == d("99.000000")
    assert rows["fresh"].reason_codes == ("memory_review_priority_pass",)

    assert rows["watch"].priority_status == "watch"
    assert rows["watch"].calibration_age_seconds == d("100.000000")
    assert "calibration_age_watch" in rows["watch"].reason_codes

    assert rows["block"].priority_status == "block"
    assert rows["block"].calibration_age_seconds == d("200.000000")
    assert "calibration_age_block" in rows["block"].reason_codes

    assert rows["missing"].priority_status == "block"
    assert rows["missing"].calibration_age_seconds is None
    assert rows["missing"].calibration_age_pressure == d("1.000000")
    assert rows["missing"].reason_codes[0] == "calibration_missing_block"


def test_public_payload_digest_is_deterministic_and_validated() -> None:
    records = (
        review_input(
            domain_key="politics",
            team_key="policy_team",
            review_reference="candidate-999 market_id market_slug question text",
        ),
        review_input(
            domain_key="politics",
            team_key="review_team",
            review_reference="https://example.invalid/path?token=secret",
            evidence_reuse_quality=d("0.800000"),
            unresolved_feedback_count=d("1.000000"),
        ),
    )
    built = build_report(
        *records,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    reordered = build_report(*reversed(records))

    assert built.public_payload == reordered.public_payload
    payload = api().research_team_domain_memory_review_priority_public_payload(built)
    assert payload == built.public_payload
    assert json.dumps(payload, sort_keys=True)
    assert payload["input_count"] == "2.000000"
    assert payload["rows"][0]["review_priority_score"] == "0.098333"
    assert payload["derived_validation_digest"] == built.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert api().research_team_domain_memory_review_priority_report_digest(built) == (
        built.derived_validation_digest
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)


def test_public_payload_prevents_sensitive_surface_leaks() -> None:
    built = build_report(
        review_input(
            review_reference=(
                "candidate-999 market_id market_slug question text "
                "https://example.invalid/path?token=secret dsn://warehouse/table "
                "wallet order trade live sizing recommendation"
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
        "sizing",
        "recommendation",
    ):
        assert forbidden not in serialized

    with pytest.raises(ValueError, match="unsafe public"):
        review_input(domain_key="market_slug")
    with pytest.raises(ValueError, match="unsafe public"):
        review_input(team_key="wallet_team")
    with pytest.raises(ValueError, match="unsafe public"):
        api().research_team_domain_memory_review_priority_public_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "source_url": "x"},
        )


def test_custom_config_validation_and_frozen_decimal_only_contract() -> None:
    module = api()
    cfg = config(
        calibration_age_pressure_weight=d("0.300000"),
        forecast_miss_recurrence_weight=d("0.200000"),
        evidence_reuse_quality_weight=d("0.200000"),
        unresolved_feedback_weight=d("0.100000"),
        review_capacity_pressure_weight=d("0.200000"),
        priority_score_watch_threshold=d("0.350000"),
        priority_score_block_threshold=d("0.650000"),
    )
    built = build_report(review_input(), cfg=cfg)

    assert built.rows[0].review_priority_score == d("0.100000")
    assert built.rows[0].priority_status == "pass"
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    with pytest.raises(FrozenInstanceError):
        built.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        review_input(evidence_reuse_quality=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="weights must sum to 1"):
        config(review_capacity_pressure_weight=d("0.300000"))
    with pytest.raises(ValueError, match="priority_score_block_threshold"):
        config(
            priority_score_watch_threshold=d("0.700000"),
            priority_score_block_threshold=d("0.600000"),
        )
    with pytest.raises(ValueError, match="evidence_reuse_quality_block_below"):
        config(
            evidence_reuse_quality_watch_below=d("0.400000"),
            evidence_reuse_quality_block_below=d("0.500000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchTeamDomainMemoryReviewPriorityConfig(paper_only=False)

    for item in (
        cfg,
        review_input(),
        built,
        built.rows[0],
        built.reason_code_counts[0],
    ):
        assert is_dataclass(item)
        for field in fields(item):
            value = getattr(item, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
                or field.name.endswith("_pressure")
                or field.name.endswith("_score")
                or field.name.endswith("_weight")
                or field.name.endswith("_threshold")
                or field.name.endswith("_rank")
                or field.name.endswith("_below")
            ):
                if value is not None:
                    assert type(value) is Decimal


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
            if field.name == "review_reference":
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
        "sizing",
        "recommendation",
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
