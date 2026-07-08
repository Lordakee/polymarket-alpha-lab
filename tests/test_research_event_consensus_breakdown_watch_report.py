from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_consensus_breakdown_watch_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "research-event-consensus-breakdown-watch-report-test",
        "watch_score_floor": d("0.400000"),
        "block_score_floor": d("0.700000"),
        "confidence_dispersion_weight": d("0.250000"),
        "evidence_contradiction_weight": d("0.250000"),
        "catalyst_pressure_weight": d("0.200000"),
        "memory_staleness_weight": d("0.200000"),
        "rule_ambiguity_weight": d("0.100000"),
        "fresh_memory_age_hours": d("12.000000"),
        "stale_memory_age_hours": d("48.000000"),
        "minimum_team_count": d("3.000000"),
    }
    values.update(overrides)
    return module.ResearchEventConsensusBreakdownWatchConfig(**values)


def observation(**overrides: object) -> Any:
    module = api()
    values = {
        "event_family": "macro-policy",
        "consensus_bucket": "consensus-alpha",
        "observed_at": OBSERVED_AT,
        "team_count": d("4.000000"),
        "aggregate_confidence_mean": d("0.620000"),
        "aggregate_confidence_min": d("0.540000"),
        "aggregate_confidence_max": d("0.680000"),
        "evidence_contradiction_score": d("0.100000"),
        "catalyst_pressure_score": d("0.100000"),
        "memory_age_hours": d("6.000000"),
        "rule_clarity_score": d("0.900000"),
        "analysis_version": "analysis-v1",
    }
    values.update(overrides)
    return module.ResearchEventConsensusBreakdownWatchObservation(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_event_consensus_breakdown_watch_report(
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
        "recommend",
        "position",
    )


def test_consensus_breakdown_scoring_and_report_rollups() -> None:
    report = build_report(
        observation(consensus_bucket="consensus-pass"),
        observation(
            consensus_bucket="consensus-watch",
            aggregate_confidence_min=d("0.350000"),
            aggregate_confidence_max=d("0.850000"),
            evidence_contradiction_score=d("0.450000"),
            catalyst_pressure_score=d("0.350000"),
            memory_age_hours=d("24.000000"),
            rule_clarity_score=d("0.650000"),
        ),
        observation(
            consensus_bucket="consensus-block",
            aggregate_confidence_min=d("0.050000"),
            aggregate_confidence_max=d("0.950000"),
            evidence_contradiction_score=d("0.900000"),
            catalyst_pressure_score=d("0.800000"),
            memory_age_hours=d("72.000000"),
            rule_clarity_score=d("0.200000"),
        ),
    )

    rows = {row.consensus_bucket: row for row in report.rows}
    assert rows["consensus-pass"].confidence_dispersion_score == d("0.140000")
    assert rows["consensus-pass"].memory_staleness_score == d("0.000000")
    assert rows["consensus-pass"].breakdown_pressure_score == d("0.090000")
    assert rows["consensus-pass"].breakdown_status == "pass"
    assert rows["consensus-pass"].reason_codes == ("consensus_breakdown_pass",)

    assert rows["consensus-watch"].confidence_dispersion_score == d("0.500000")
    assert rows["consensus-watch"].memory_staleness_score == d("0.333333")
    assert rows["consensus-watch"].rule_ambiguity_score == d("0.350000")
    assert rows["consensus-watch"].breakdown_pressure_score == d("0.409167")
    assert rows["consensus-watch"].breakdown_status == "watch"
    assert rows["consensus-watch"].reason_codes == (
        "consensus_breakdown_watch_score",
        "confidence_dispersion_watch",
        "evidence_contradiction_watch",
        "catalyst_pressure_watch",
        "memory_staleness_watch",
        "rule_clarity_watch",
    )

    assert rows["consensus-block"].breakdown_pressure_score == d("0.890000")
    assert rows["consensus-block"].breakdown_status == "block"
    assert rows["consensus-block"].reason_codes == (
        "consensus_breakdown_block_score",
        "confidence_dispersion_block",
        "evidence_contradiction_block",
        "catalyst_pressure_block",
        "memory_staleness_block",
        "rule_clarity_block",
    )

    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.report_status == "block"
    assert report.average_breakdown_pressure_score == d("0.463056")
    assert report.max_breakdown_pressure_score == d("0.890000")
    assert report.reason_codes == ("consensus_breakdown_report_block",)

    for item in (cfg(), *report.rows, report):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if field.name.endswith(("_count", "_score", "_hours", "_weight", "_floor")):
                assert type(value) is Decimal


def test_memory_freshness_team_count_and_rule_clarity_drive_reasons() -> None:
    report = build_report(
        observation(
            consensus_bucket="thin-team",
            team_count=d("2.000000"),
            aggregate_confidence_min=d("0.420000"),
            aggregate_confidence_max=d("0.880000"),
            memory_age_hours=d("50.000000"),
            rule_clarity_score=d("0.450000"),
        ),
    )

    row = report.rows[0]
    assert row.memory_staleness_score == d("1.000000")
    assert row.rule_ambiguity_score == d("0.550000")
    assert row.breakdown_status == "watch"
    assert "thin_specialist_team" in row.reason_codes
    assert "memory_staleness_block" in row.reason_codes
    assert "rule_clarity_watch" in row.reason_codes


def test_payload_serialization_validation_and_digest_are_canonical() -> None:
    module = api()
    report = build_report(observation())
    payload = module.research_event_consensus_breakdown_watch_report_payload(report)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["row_count"] == "1.000000"
    assert payload["report_status"] == "pass"
    assert payload["rows"][0]["breakdown_pressure_score"] == "0.090000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert module.validate_research_event_consensus_breakdown_watch_report_payload(payload)
    assert_no_float_or_int(payload)
    assert json.dumps(payload, sort_keys=True)

    rebuilt = build_report(observation())
    assert rebuilt.derived_validation_digest == report.derived_validation_digest
    assert (
        module.research_event_consensus_breakdown_watch_report_payload(rebuilt)
        == payload
    )


def test_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_CONSENSUS_BREAKDOWN_WATCH_CONFIG_VERSION",
        "ResearchEventConsensusBreakdownWatchConfig",
        "ResearchEventConsensusBreakdownWatchObservation",
        "ResearchEventConsensusBreakdownWatchRow",
        "ResearchEventConsensusBreakdownWatchReport",
        "build_research_event_consensus_breakdown_watch_report",
        "research_event_consensus_breakdown_watch_report_payload",
        "validate_research_event_consensus_breakdown_watch_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(observation())
    with pytest.raises(FrozenInstanceError):
        report.rows[0].breakdown_status = "block"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.ResearchEventConsensusBreakdownWatchConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(module.ResearchEventConsensusBreakdownWatchObservation):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.ResearchEventConsensusBreakdownWatchRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.ResearchEventConsensusBreakdownWatchReport):
            pass

    with pytest.raises(ValueError, match="team_count must be a Decimal"):
        observation(team_count=DecimalSubclass("4.000000"))
    with pytest.raises(ValueError, match="team_count must be a Decimal"):
        observation(team_count=4)
    with pytest.raises(ValueError, match="aggregate_confidence_mean must be a Decimal"):
        observation(aggregate_confidence_mean=d("0.620000").as_tuple())


def test_hard_flags_are_enforced_on_inputs_report_and_payload() -> None:
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
    assert (
        module.research_event_consensus_breakdown_watch_report_payload(report)["readonly"]
        is True
    )

    payload = module.research_event_consensus_breakdown_watch_report_payload(report)
    flag_payload = dict(payload)
    flag_payload["paper_only"] = False
    with pytest.raises(ValueError, match="payload paper_only must be True"):
        module.validate_research_event_consensus_breakdown_watch_report_payload(
            flag_payload,
        )


def test_digest_tampering_is_rejected_for_report_and_payload() -> None:
    module = api()
    report = build_report(observation())

    with pytest.raises(ValueError, match="average_breakdown_pressure_score"):
        replace(report, average_breakdown_pressure_score=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.research_event_consensus_breakdown_watch_report_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_consensus_breakdown_watch_report_payload(
            tampered_payload,
        )

    object.__setattr__(report.rows[0], "breakdown_pressure_score", d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_consensus_breakdown_watch_report_payload(report)


def test_no_raw_event_market_or_source_identifiers_reach_public_surface() -> None:
    module = api()

    with pytest.raises(ValueError, match="raw event identifiers"):
        observation(event_id="event-alpha")
    with pytest.raises(ValueError, match="raw market identifiers"):
        observation(market_id="market-alpha")
    with pytest.raises(ValueError, match="raw source identifiers"):
        observation(source_reference="source-alpha")

    report = build_report(observation())
    payload = module.research_event_consensus_breakdown_watch_report_payload(report)
    public_text = json.dumps(payload, sort_keys=True)
    assert "event_id" not in public_text
    assert "market_id" not in public_text
    assert "source_reference" not in public_text


def test_unsafe_public_payload_keys_values_and_execution_surfaces_are_rejected() -> None:
    module = api()

    for term in unsafe_terms():
        with pytest.raises(ValueError, match="unsafe public surface"):
            observation(consensus_bucket=f"consensus-{term}")

    payload = module.research_event_consensus_breakdown_watch_report_payload(
        build_report(observation()),
    )
    unsafe_key_payload = dict(payload)
    unsafe_key_payload["".join(("wall", "et"))] = "forbidden"
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_research_event_consensus_breakdown_watch_report_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_value_payload["rows"][0]["consensus_bucket"] = (
        "consensus-" + "".join(("tr", "ade"))
    )
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_research_event_consensus_breakdown_watch_report_payload(
            unsafe_value_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["row_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        module.validate_research_event_consensus_breakdown_watch_report_payload(
            numeric_payload,
        )

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
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "position",
    ):
        assert forbidden not in source.lower()
