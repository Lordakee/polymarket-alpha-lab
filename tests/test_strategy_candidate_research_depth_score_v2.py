from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_research_depth_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "strategy-candidate-research-depth-score-v2-test",
        "minimum_source_count": d("4.000000"),
        "minimum_independent_source_count": d("2.000000"),
        "minimum_primary_source_count": d("1.000000"),
        "minimum_citation_count": d("6.000000"),
        "maximum_evidence_age_days": d("14.000000"),
        "minimum_source_quality_score": d("0.700000"),
        "minimum_resolution_alignment_score": d("0.700000"),
        "source_coverage_weight": d("0.250000"),
        "independent_source_weight": d("0.200000"),
        "primary_source_weight": d("0.150000"),
        "citation_depth_weight": d("0.150000"),
        "freshness_weight": d("0.150000"),
        "source_quality_weight": d("0.050000"),
        "resolution_alignment_weight": d("0.050000"),
        "missing_source_penalty_weight": d("0.150000"),
        "stale_evidence_penalty_weight": d("0.200000"),
        "ready_score_floor": d("0.750000"),
        "watch_score_floor": d("0.500000"),
    }
    values.update(overrides)
    return module.StrategyCandidateResearchDepthScoreV2Config(**values)


def observation(**overrides: object) -> Any:
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_id": "market-alpha",
        "observed_at": OBSERVED_AT,
        "source_count": d("4.000000"),
        "independent_source_count": d("2.000000"),
        "primary_source_count": d("1.000000"),
        "citation_count": d("6.000000"),
        "current_evidence_age_days": d("1.000000"),
        "average_source_quality_score": d("0.900000"),
        "resolution_alignment_score": d("0.900000"),
        "source_config_version": "source-config-v1",
    }
    values.update(overrides)
    return module.StrategyCandidateResearchDepthScoreV2Observation(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_strategy_candidate_research_depth_score_v2(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def assert_no_float_or_int(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)
        return
    assert type(value) not in (float, int)


def unsafe_terms() -> tuple[str, ...]:
    return (
        "".join(("li", "ve")),
        "".join(("au", "th")),
        "".join(("wall", "et")),
        "".join(("or", "der")),
        "".join(("net", "work")),
        "".join(("data", "base")),
        "".join(("per", "sist")),
        "".join(("sign", "ing")),
        "".join(("muta", "tion")),
        "".join(("b", "uy")),
        "".join(("s", "ell")),
        "".join(("tr", "ade")),
    )


def test_research_depth_scoring_and_decimal_report_rollups() -> None:
    report = build_report(
        observation(candidate_id="candidate-alpha"),
        observation(
            candidate_id="candidate-beta",
            source_count=d("3.000000"),
            citation_count=d("3.000000"),
            average_source_quality_score=d("0.800000"),
            resolution_alignment_score=d("0.800000"),
        ),
    )

    rows = {row.candidate_id: row for row in report.rows}
    assert rows["candidate-alpha"].source_coverage_score == d("1.000000")
    assert rows["candidate-alpha"].evidence_freshness_score == d("0.928571")
    assert rows["candidate-alpha"].research_depth_score == d("0.965000")
    assert rows["candidate-alpha"].depth_status == "ready"
    assert rows["candidate-alpha"].reason_codes == ("research_depth_ready",)

    assert rows["candidate-beta"].source_coverage_score == d("0.750000")
    assert rows["candidate-beta"].citation_depth_score == d("0.500000")
    assert rows["candidate-beta"].missing_source_penalty == d("0.037500")
    assert rows["candidate-beta"].research_depth_score == d("0.780000")
    assert rows["candidate-beta"].reason_codes == (
        "research_depth_ready",
        "missing_research_sources",
        "thin_citation_depth",
    )

    assert report.row_count == d("2.000000")
    assert report.ready_count == d("2.000000")
    assert report.average_research_depth_score == d("0.872500")
    assert report.average_missing_source_penalty == d("0.018750")
    assert report.max_current_evidence_age_days == d("1.000000")

    for item in (cfg(), *report.rows, report):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if field.name.endswith(("_count", "_score", "_days", "_penalty", "_weight")):
                assert type(value) is Decimal


def test_missing_source_penalties_watch_and_blocked_thresholds() -> None:
    report = build_report(
        observation(
            candidate_id="candidate-watch",
            source_count=d("3.000000"),
            independent_source_count=d("2.000000"),
            primary_source_count=d("0.000000"),
            citation_count=d("4.000000"),
            average_source_quality_score=d("0.700000"),
            resolution_alignment_score=d("0.700000"),
        ),
        observation(
            candidate_id="candidate-blocked",
            source_count=d("0.000000"),
            independent_source_count=d("0.000000"),
            primary_source_count=d("0.000000"),
            citation_count=d("0.000000"),
            average_source_quality_score=d("0.400000"),
            resolution_alignment_score=d("0.400000"),
        ),
    )

    rows = {row.candidate_id: row for row in report.rows}
    assert rows["candidate-watch"].research_depth_score == d("0.645000")
    assert rows["candidate-watch"].depth_status == "watch"
    assert rows["candidate-watch"].missing_source_penalty == d("0.037500")
    assert "missing_research_sources" in rows["candidate-watch"].reason_codes

    assert rows["candidate-blocked"].research_depth_score == d("0.015000")
    assert rows["candidate-blocked"].depth_status == "blocked"
    assert rows["candidate-blocked"].missing_source_penalty == d("0.150000")
    assert rows["candidate-blocked"].reason_codes[:2] == (
        "research_depth_blocked_score",
        "missing_research_sources",
    )
    assert report.depth_status == "blocked"
    assert report.blocked_count == d("1.000000")


def test_stale_evidence_penalties_drive_watch_and_block_reasons() -> None:
    report = build_report(
        observation(candidate_id="candidate-watch", current_evidence_age_days=d("10.000000")),
        observation(candidate_id="candidate-blocked", current_evidence_age_days=d("20.000000")),
    )

    rows = {row.candidate_id: row for row in report.rows}
    assert rows["candidate-watch"].evidence_freshness_score == d("0.285714")
    assert rows["candidate-watch"].stale_evidence_penalty == d("0.142857")
    assert rows["candidate-watch"].research_depth_score == d("0.740000")
    assert rows["candidate-watch"].reason_codes == (
        "research_depth_watch_score",
        "stale_evidence_watch",
    )

    assert rows["candidate-blocked"].evidence_freshness_score == d("0.000000")
    assert rows["candidate-blocked"].stale_evidence_penalty == d("0.200000")
    assert rows["candidate-blocked"].research_depth_score == d("0.640000")
    assert rows["candidate-blocked"].depth_status == "watch"
    assert rows["candidate-blocked"].reason_codes == (
        "research_depth_watch_score",
        "stale_evidence_blocked",
    )


def test_payload_serialization_and_validation_are_canonical() -> None:
    module = api()
    report = build_report(observation())
    payload = module.strategy_candidate_research_depth_score_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["row_count"] == "1.000000"
    assert payload["average_research_depth_score"] == "0.965000"
    assert payload["rows"][0]["research_depth_score"] == "0.965000"
    assert payload["rows"][0]["stale_evidence_penalty"] == "0.014286"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert module.validate_strategy_candidate_research_depth_score_v2_payload(payload)
    assert_no_float_or_int(payload)
    json.dumps(payload, sort_keys=True)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_STRATEGY_CANDIDATE_RESEARCH_DEPTH_SCORE_V2_CONFIG_VERSION",
        "StrategyCandidateResearchDepthScoreV2Config",
        "StrategyCandidateResearchDepthScoreV2Observation",
        "StrategyCandidateResearchDepthScoreV2Row",
        "StrategyCandidateResearchDepthScoreV2Report",
        "build_strategy_candidate_research_depth_score_v2",
        "strategy_candidate_research_depth_score_v2_payload",
        "validate_strategy_candidate_research_depth_score_v2_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(observation())
    with pytest.raises(FrozenInstanceError):
        report.rows[0].depth_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.StrategyCandidateResearchDepthScoreV2Config):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(module.StrategyCandidateResearchDepthScoreV2Observation):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.StrategyCandidateResearchDepthScoreV2Row):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.StrategyCandidateResearchDepthScoreV2Report):
            pass

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        observation(source_count=DecimalSubclass("4.000000"))


def test_hard_flags_are_enforced() -> None:
    module = api()
    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)

    report = build_report(observation())
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(report, report_only=False)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert module.strategy_candidate_research_depth_score_v2_payload(report)["readonly"] is True

    payload = module.strategy_candidate_research_depth_score_v2_payload(report)
    flag_payload = dict(payload)
    flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.validate_strategy_candidate_research_depth_score_v2_payload(flag_payload)


def test_digest_tampering_is_rejected_for_report_and_payload() -> None:
    module = api()
    report = build_report(observation())

    with pytest.raises(ValueError, match="average_research_depth_score"):
        replace(report, average_research_depth_score=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.strategy_candidate_research_depth_score_v2_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_strategy_candidate_research_depth_score_v2_payload(tampered_payload)

    object.__setattr__(report.rows[0], "research_depth_score", d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_research_depth_score_v2_payload(report)


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    module = api()

    for term in unsafe_terms():
        with pytest.raises(ValueError, match="unsafe public surface"):
            observation(candidate_id=f"candidate-{term}")

    payload = module.strategy_candidate_research_depth_score_v2_payload(
        build_report(observation()),
    )
    unsafe_key_payload = dict(payload)
    unsafe_key_payload["".join(("wall", "et"))] = "forbidden"
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_strategy_candidate_research_depth_score_v2_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_value_payload["rows"][0]["candidate_id"] = (
        "candidate-" + "".join(("tr", "ade"))
    )
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_strategy_candidate_research_depth_score_v2_payload(
            unsafe_value_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["row_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        module.validate_strategy_candidate_research_depth_score_v2_payload(
            numeric_payload,
        )


def test_module_omits_unsafe_public_surfaces() -> None:
    module = api()
    public_names = set(module.__all__) | {
        name for name in dir(module) if not name.startswith("_")
    }
    for public_name in public_names:
        lower_name = public_name.lower()
        assert "db" not in lower_name
        for term in unsafe_terms():
            assert term not in lower_name

    source = inspect.getsource(module)
    for forbidden in (
        "requests",
        "urllib",
        "http.client",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "subprocess",
        "Path(",
        "open(",
        ".write(",
        ".read(",
    ):
        assert forbidden not in source
