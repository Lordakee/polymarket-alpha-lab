from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_review_latency_score.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_review_latency_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def hidden_word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("ascii")


def latency_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "team_id": "team-alpha",
        "specialist_id": "review-latency-alpha",
        "observed_event_count": d("10"),
        "delayed_event_count": d("0"),
        "median_research_latency_hours": d("2.000000"),
        "p90_review_latency_hours": d("4.000000"),
        "oldest_unreviewed_event_age_hours": d("3.000000"),
    }
    values.update(overrides)
    return module.TeamSpecialistReviewLatencyScoreInput(**values)


def score(**overrides: object) -> Any:
    module = api()
    return module.score_team_specialist_review_latency(
        latency_input(**overrides),
        config=module.TeamSpecialistReviewLatencyScoreConfig(),
    )


def assert_no_public_int_or_float(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_int_or_float(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_int_or_float(item)


def assert_status_vocabulary(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("_status"):
                assert item in {"pass", "watch", "block"}
                assert item != hidden_word("626c6f636b6564")
            assert_status_vocabulary(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_status_vocabulary(item)


def test_low_latency_reviews_pass_without_raising_workflow_priority() -> None:
    report = score()

    assert report.team_id == "team-alpha"
    assert report.specialist_id == "review-latency-alpha"
    assert report.observed_event_count == d("10")
    assert report.delayed_event_count == d("0")
    assert report.delayed_event_ratio == d("0.000000")
    assert report.median_research_sla_ratio == d("0.166667")
    assert report.p90_review_sla_ratio == d("0.333333")
    assert report.oldest_unreviewed_sla_ratio == d("0.250000")
    assert report.review_latency_score == d("0.212500")
    assert report.timeliness_impact_status == "pass"
    assert report.workflow_priority_status == "pass"
    assert report.report_status == "pass"
    assert report.reason_codes == (
        "review_latency_pass",
        "median_research_latency_clear",
        "p90_review_latency_clear",
        "oldest_unreviewed_event_clear",
        "delayed_event_share_clear",
    )


def test_elevated_review_latency_watches_candidate_event_timeliness() -> None:
    report = score(
        observed_event_count=d("10"),
        delayed_event_count=d("2"),
        median_research_latency_hours=d("8.000000"),
        p90_review_latency_hours=d("10.000000"),
        oldest_unreviewed_event_age_hours=d("9.000000"),
    )

    assert report.delayed_event_ratio == d("0.200000")
    assert report.median_research_sla_ratio == d("0.666667")
    assert report.p90_review_sla_ratio == d("0.833333")
    assert report.oldest_unreviewed_sla_ratio == d("0.750000")
    assert report.review_latency_score == d("0.667500")
    assert report.timeliness_impact_status == "watch"
    assert report.workflow_priority_status == "watch"
    assert report.report_status == "watch"
    assert report.reason_codes == (
        "review_latency_watch",
        "median_research_latency_clear",
        "p90_review_latency_watch",
        "oldest_unreviewed_event_watch",
        "delayed_event_share_watch",
    )


def test_stale_review_response_blocks_workflow_priority_only() -> None:
    report = score(
        observed_event_count=d("12"),
        delayed_event_count=d("7"),
        median_research_latency_hours=d("14.000000"),
        p90_review_latency_hours=d("18.000000"),
        oldest_unreviewed_event_age_hours=d("16.000000"),
    )

    assert report.delayed_event_ratio == d("0.583333")
    assert report.median_research_sla_ratio == d("1.000000")
    assert report.p90_review_sla_ratio == d("1.000000")
    assert report.oldest_unreviewed_sla_ratio == d("1.000000")
    assert report.review_latency_score == d("0.937500")
    assert report.timeliness_impact_status == "block"
    assert report.workflow_priority_status == "block"
    assert report.report_status == "block"
    assert report.reason_codes == (
        "review_latency_block",
        "median_research_latency_over_sla",
        "p90_review_latency_over_sla",
        "oldest_unreviewed_event_over_sla",
        "delayed_event_share_block",
    )


def test_decimal_exact_type_validation_rejects_int_float_and_subclass_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="observed_event_count must be exactly Decimal"):
        latency_input(observed_event_count=10)

    with pytest.raises(ValueError, match="median_research_latency_hours must be exactly Decimal"):
        latency_input(median_research_latency_hours=2.0)

    with pytest.raises(ValueError, match="delayed_event_count must be exactly Decimal"):
        latency_input(delayed_event_count=_DecimalSubclass("1"))

    with pytest.raises(ValueError, match="p90_review_latency_hours must use six decimal places or fewer"):
        latency_input(p90_review_latency_hours=d("1.0000001"))

    with pytest.raises(ValueError, match="delayed_event_count must not exceed observed_event_count"):
        latency_input(observed_event_count=d("2"), delayed_event_count=d("3"))

    with pytest.raises(ValueError, match="latency weights must sum to 1.000000"):
        module.TeamSpecialistReviewLatencyScoreConfig(
            delayed_event_share_weight=d("0.160000"),
        )


def test_public_payload_rejects_leaks_and_non_public_status_words() -> None:
    module = api()
    leak = hidden_word("77616c6c6574")

    with pytest.raises(ValueError, match="unsafe public value"):
        latency_input(team_id=f"team-{leak}")

    payload = score().payload
    assert_status_vocabulary(payload)
    payload_text = json.dumps(payload, sort_keys=True)
    for hidden in (
        "7261775f63616e6469646174655f6964",
        "63616e6469646174655f6964",
        "6d61726b65745f6964",
        "6d61726b65745f736c7567",
        "6d61726b65745f7175657374696f6e",
        "7175657374696f6e",
        "736f757263655f726566",
        "75726c",
        "736f757263655f74657874",
        "64736e",
        "7461626c65",
        "746f6b656e",
        "77616c6c6574",
        "61757468",
        "6f72646572",
        "7472616465",
        "706f736974696f6e",
        "627579",
        "73656c6c",
        "7265636f6d6d656e646174696f6e",
    ):
        assert hidden_word(hidden) not in payload_text.lower()

    tampered_payload = dict(payload)
    tampered_payload[hidden_word("6d61726b65745f6964")] = "redacted"
    with pytest.raises(ValueError, match="unsafe public key"):
        module.team_specialist_review_latency_score_payload(tampered_payload)

    tampered_payload = dict(payload)
    tampered_payload["team_id"] = f"team-{hidden_word('7472616465')}"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.team_specialist_review_latency_score_payload(tampered_payload)

    tampered_payload = dict(payload)
    tampered_payload["report_status"] = hidden_word("626c6f636b6564")
    with pytest.raises(ValueError, match="status|unsafe public value"):
        module.team_specialist_review_latency_score_payload(tampered_payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistReviewLatencyScoreConfig()
    input_signal = latency_input()
    report = score()

    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_REVIEW_LATENCY_SCORE_CONFIG_VERSION",
        "TEAM_SPECIALIST_REVIEW_LATENCY_SCORE_STATUSES",
        "TeamSpecialistReviewLatencyScoreConfig",
        "TeamSpecialistReviewLatencyScoreInput",
        "TeamSpecialistReviewLatencyScoreReport",
        "score_team_specialist_review_latency",
        "team_specialist_review_latency_score_payload",
    )

    for item in (config, input_signal, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    numeric_fields = {
        "response_sla_hours",
        "median_research_weight",
        "p90_review_weight",
        "oldest_unreviewed_weight",
        "delayed_event_share_weight",
        "watch_latency_ratio",
        "block_latency_ratio",
        "delayed_event_share_watch_floor",
        "delayed_event_share_block_floor",
        "score_watch_floor",
        "score_block_floor",
        "observed_event_count",
        "delayed_event_count",
        "median_research_latency_hours",
        "p90_review_latency_hours",
        "oldest_unreviewed_event_age_hours",
        "delayed_event_ratio",
        "median_research_sla_ratio",
        "p90_review_sla_ratio",
        "oldest_unreviewed_sla_ratio",
        "review_latency_score",
    }
    for cls in (
        module.TeamSpecialistReviewLatencyScoreConfig,
        module.TeamSpecialistReviewLatencyScoreInput,
        module.TeamSpecialistReviewLatencyScoreReport,
    ):
        hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name in numeric_fields:
                assert hints[field.name] is Decimal

    assert_no_public_int_or_float(report.payload)


def test_payload_and_digest_are_deterministic_and_consistent() -> None:
    module = api()
    report_a = score()
    report_b = score()

    assert report_a.payload == report_b.payload
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert json.dumps(report_a.payload, sort_keys=True) == json.dumps(
        report_b.payload,
        sort_keys=True,
    )
    assert module.team_specialist_review_latency_score_payload(report_a) == report_a.payload
    assert module.team_specialist_review_latency_score_payload(dict(report_a.payload)) == report_a.payload

    tampered_payload = dict(report_a.payload)
    tampered_payload["review_latency_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.team_specialist_review_latency_score_payload(tampered_payload)

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report_a, derived_validation_digest="0" * 64)
