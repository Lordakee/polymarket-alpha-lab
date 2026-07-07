from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_topic_novelty_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "team-specialist-topic-novelty-score-v1-test",
        "topic_overlap_weight": d("0.450000"),
        "event_type_overlap_weight": d("0.350000"),
        "prior_case_depth_weight": d("0.200000"),
        "min_topic_overlap_ratio": d("0.500000"),
        "min_event_type_overlap_ratio": d("0.500000"),
        "min_prior_case_count": d("5.000000"),
        "full_prior_case_count": d("20.000000"),
        "pass_score_floor": d("0.750000"),
        "watch_score_floor": d("0.400000"),
    }
    values.update(overrides)
    return module.TeamSpecialistTopicNoveltyScoreConfig(**values)


def topic_input(**overrides: object):
    module = api()
    values = {
        "team_id": "alpha_research",
        "specialist_id": "macro_mapper",
        "topic_family_id": "rates_policy",
        "event_type_family_id": "central_bank_decision",
        "topic_overlap_ratio": d("0.900000"),
        "event_type_overlap_ratio": d("0.850000"),
        "prior_case_count": d("20.000000"),
    }
    values.update(overrides)
    return module.TeamSpecialistTopicNoveltyScoreInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_topic_novelty_score_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def test_builds_pass_watch_and_block_rows_with_public_statuses() -> None:
    report = build_report(
        topic_input(
            team_id="watch_team",
            specialist_id="mapper_b",
            topic_family_id="weather_event",
            event_type_family_id="seasonal_window",
            topic_overlap_ratio=d("0.450000"),
            event_type_overlap_ratio=d("0.700000"),
            prior_case_count=d("10.000000"),
        ),
        topic_input(
            team_id="pass_team",
            specialist_id="mapper_a",
            topic_family_id="rates_policy",
            event_type_family_id="central_bank_decision",
            topic_overlap_ratio=d("0.900000"),
            event_type_overlap_ratio=d("0.850000"),
            prior_case_count=d("20.000000"),
        ),
        topic_input(
            team_id="block_team",
            specialist_id="mapper_c",
            topic_family_id="new_topic_family",
            event_type_family_id="new_event_family",
            topic_overlap_ratio=d("0.200000"),
            event_type_overlap_ratio=d("0.000000"),
            prior_case_count=d("2.000000"),
        ),
    )

    assert report.report_status == "block"
    assert report.item_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_novelty_score == d("0.520000")
    assert report.minimum_novelty_score == d("0.110000")
    assert tuple(row.team_id for row in report.rows) == (
        "block_team",
        "pass_team",
        "watch_team",
    )
    assert tuple(row.status for row in report.rows) == ("block", "pass", "watch")
    assert report.rows[0].reason_codes == (
        "topic_novelty_unseen_event_type",
        "topic_novelty_low_topic_overlap",
        "topic_novelty_low_event_type_overlap",
        "topic_novelty_low_prior_case_count",
        "topic_novelty_score_block",
    )
    assert report.rows[1].reason_codes == ("team_specialist_topic_novelty_pass",)
    assert report.rows[1].novelty_score == d("0.902500")
    assert report.rows[2].reason_codes == ("topic_novelty_low_topic_overlap",)
    assert report.rows[2].novelty_score == d("0.547500")
    assert {row.status for row in report.rows} == {"pass", "watch", "block"}


def test_empty_report_blocks_with_stable_zero_scores() -> None:
    report = build_report()

    assert report.report_status == "block"
    assert report.item_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_novelty_score == d("0.000000")
    assert report.minimum_novelty_score == d("0.000000")
    assert report.reason_code_counts == ()
    assert report.rows == ()


def test_decimal_type_rejection_and_hard_flags() -> None:
    sample_config = config()
    sample_input = topic_input()
    sample_report = build_report(topic_input(team_id="frozen_team"))
    sample_row = sample_report.rows[0]
    sample_reason_count = sample_report.reason_code_counts[0]

    for item in (
        sample_config,
        sample_input,
        sample_row,
        sample_reason_count,
        sample_report,
    ):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="topic_overlap_ratio must be exactly Decimal"):
        topic_input(topic_overlap_ratio=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="prior_case_count must be exactly Decimal"):
        topic_input(prior_case_count=20)
    with pytest.raises(ValueError, match="event_type_overlap_ratio must be between"):
        topic_input(event_type_overlap_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        topic_input(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_report(topic_input(readonly=False))


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "candidate_alpha",
        "market_alpha",
        "slug_alpha",
        "question_alpha",
        "source_alpha",
        "ref_alpha",
        "url_alpha",
        "text_alpha",
        "dsn_alpha",
        "table_alpha",
        "token_alpha",
        "auth_alpha",
        "wallet_alpha",
        "order_alpha",
        "trade_alpha",
        "position_alpha",
        "buy_alpha",
        "sell_alpha",
        "recommendation_alpha",
    ),
)
def test_rejects_unsafe_public_keys_and_values(unsafe_value: str) -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public payload"):
        topic_input(team_id=unsafe_value)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload(
            "payload",
            {"paper_only": True, "report_only": True, "readonly": True, unsafe_value: "x"},
            allow_json_containers=True,
        )
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload(
            "payload",
            {"paper_only": True, "report_only": True, "readonly": True, "note": unsafe_value},
            allow_json_containers=True,
        )


def test_payload_is_deterministic_and_contains_no_raw_or_action_language() -> None:
    module = api()
    report_a = build_report(
        topic_input(team_id="z_team", specialist_id="mapper_z"),
        topic_input(team_id="a_team", specialist_id="mapper_a"),
    )
    report_b = build_report(
        topic_input(team_id="a_team", specialist_id="mapper_a"),
        topic_input(team_id="z_team", specialist_id="mapper_z"),
    )

    payload_a = module.team_specialist_topic_novelty_score_payload(report_a)
    payload_b = module.team_specialist_topic_novelty_score_payload(report_b)

    assert payload_a == payload_b
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload_a["derived_validation_digest"] == report_a.derived_validation_digest
    assert payload_a["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload_a["paper_only"] is True
    assert payload_a["report_only"] is True
    assert payload_a["readonly"] is True
    assert payload_a["item_count"] == "2.000000"
    assert payload_a["rows"][0]["rank"] == "1.000000"
    assert payload_a["rows"][0]["novelty_score"] == "0.902500"
    assert_no_float_values(payload_a)
    json.dumps(payload_a, allow_nan=False, sort_keys=True)

    encoded = json.dumps(payload_a, sort_keys=True).casefold()
    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "ref",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert forbidden not in encoded


def test_report_and_digest_consistency_rejects_tampering() -> None:
    report = build_report(topic_input(team_id="digest_team"))

    assert len(report.derived_validation_digest) == 64
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="average_novelty_score must match rows"):
        replace(report, average_novelty_score=d("0.900000"))
    with pytest.raises(ValueError, match="novelty_score must match scoring fields"):
        replace(report.rows[0], novelty_score=d("0.900000"))
