from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class DerivedDatetime(datetime):
    pass


class DerivedDecimal(Decimal):
    pass


class NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def module() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_source_recheck_priority_ranker_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    ranker = module()
    values = {
        "config_version": "research-packet-source-recheck-priority-ranker-v2-test",
        "source_age_watch_seconds": d("3600.000000"),
        "source_age_blocked_seconds": d("7200.000000"),
        "contradiction_severity_watch": d("0.250000"),
        "contradiction_severity_blocked": d("0.500000"),
        "market_probability_move_watch": d("0.050000"),
        "market_probability_move_blocked": d("0.150000"),
        "close_urgency_blocked_seconds": d("3600.000000"),
        "close_urgency_watch_seconds": d("21600.000000"),
        "prior_source_reliability_blocked_ceiling": d("0.300000"),
        "prior_source_reliability_watch_ceiling": d("0.600000"),
    }
    values.update(overrides)
    return ranker.ResearchPacketSourceRecheckPriorityRankerV2Config(**values)


def candidate(packet_id: str = "packet-alpha", **overrides: object) -> Any:
    ranker = module()
    values = {
        "packet_id": packet_id,
        "team_id": "crypto_btc",
        "market_id": f"market-{packet_id}",
        "source_id": f"source-{packet_id}",
        "source_family": "exchange_report",
        "source_observed_at": GENERATED_AT - timedelta(minutes=30),
        "official_source_present": True,
        "contradiction_severity": d("0.000000"),
        "market_probability_move_magnitude": d("0.010000"),
        "market_close_at": GENERATED_AT + timedelta(days=3),
        "prior_source_reliability": d("0.900000"),
    }
    values.update(overrides)
    return ranker.ResearchPacketSourceRecheckPriorityCandidateV2(**values)


def build_report(*items: object, generated_at: datetime = GENERATED_AT) -> Any:
    ranker = module()
    return ranker.build_research_packet_source_recheck_priority_ranker_v2(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def assert_no_public_int_or_float(value: object) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_int_or_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_int_or_float(item)


def test_ranker_scores_six_recheck_factors_and_emits_decimal_payload() -> None:
    ranker = module()
    report = build_report(
        candidate(
            "packet-clear",
            market_id="market-clear",
            source_observed_at=GENERATED_AT - timedelta(minutes=20),
            market_close_at=GENERATED_AT + timedelta(days=4),
            prior_source_reliability=d("0.950000"),
        ),
        candidate(
            "packet-watch",
            market_id="market-watch",
            source_observed_at=GENERATED_AT - timedelta(minutes=90),
            contradiction_severity=d("0.300000"),
            market_probability_move_magnitude=d("0.060000"),
            market_close_at=GENERATED_AT + timedelta(hours=5),
            prior_source_reliability=d("0.500000"),
        ),
        candidate(
            "packet-contradiction",
            market_id="market-contradiction",
            contradiction_severity=d("0.650000"),
            market_probability_move_magnitude=d("0.020000"),
            market_close_at=GENERATED_AT + timedelta(days=2),
            prior_source_reliability=d("0.800000"),
        ),
        candidate(
            "packet-severe",
            market_id="market-severe",
            source_observed_at=GENERATED_AT - timedelta(hours=5),
            official_source_present=False,
            contradiction_severity=d("0.700000"),
            market_probability_move_magnitude=d("0.200000"),
            market_close_at=GENERATED_AT + timedelta(minutes=30),
            prior_source_reliability=d("0.200000"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-packet-source-recheck-priority-ranker-v2-test"
    assert report.candidate_count == d("4.000000")
    assert report.row_count == d("4.000000")
    assert report.blocked_count == d("2.000000")
    assert report.watch_count == d("1.000000")
    assert report.clear_count == d("1.000000")
    assert report.recheck_count == d("3.000000")
    assert report.priority_ratio == d("0.750000")
    assert report.official_source_absent_count == d("1.000000")
    assert report.source_age_pressure_count == d("2.000000")
    assert report.contradiction_pressure_count == d("3.000000")
    assert report.market_probability_move_pressure_count == d("2.000000")
    assert report.close_urgency_count == d("2.000000")
    assert report.low_reliability_count == d("2.000000")
    assert report.max_priority_score == d("100.000000")
    assert report.max_source_age_seconds == d("18000.000000")
    assert report.max_contradiction_severity == d("0.700000")
    assert report.max_market_probability_move_magnitude == d("0.200000")
    assert report.nearest_close_time_seconds == d("1800.000000")
    assert report.min_prior_source_reliability == d("0.200000")
    assert report.status == "blocked"
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.priority_rank, row.priority_status, row.packet_id) for row in report.rows) == (
        (d("1.000000"), "blocked", "packet-severe"),
        (d("2.000000"), "blocked", "packet-contradiction"),
        (d("3.000000"), "watch", "packet-watch"),
        (d("4.000000"), "clear", "packet-clear"),
    )

    severe, contradiction, watch, clear = report.rows
    assert severe.priority_score == d("100.000000")
    assert severe.source_age_seconds == d("18000.000000")
    assert severe.seconds_until_close == d("1800.000000")
    assert severe.reason_codes == (
        "source_age_blocked",
        "official_source_absent",
        "contradiction_severity_blocked",
        "market_probability_move_blocked",
        "close_urgency_blocked",
        "prior_source_reliability_blocked",
        "priority_score_clamped",
    )
    assert contradiction.priority_score == d("35.000000")
    assert contradiction.reason_codes == ("contradiction_severity_blocked",)
    assert watch.priority_score == d("50.000000")
    assert watch.reason_codes == (
        "source_age_watch",
        "contradiction_severity_watch",
        "market_probability_move_watch",
        "close_urgency_watch",
        "prior_source_reliability_watch",
    )
    assert clear.priority_score == d("0.000000")
    assert clear.reason_codes == ("source_recheck_priority_clear",)

    payload = ranker.research_packet_source_recheck_priority_ranker_v2_payload(report)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["candidate_count"] == "4.000000"
    assert payload["priority_ratio"] == "0.750000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["priority_rank"] == "1.000000"
    assert payload["rows"][0]["priority_score"] == "100.000000"
    assert payload["rows"][0]["source_observed_at"] == "2026-07-02T07:00:00+00:00"
    assert payload["rows"][0]["seconds_until_close"] == "1800.000000"
    assert ranker.validate_research_packet_source_recheck_priority_ranker_v2_payload(
        payload,
    )
    assert_no_public_int_or_float(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_input_returns_stable_readonly_report() -> None:
    report_one = build_report()
    report_two = build_report()

    assert report_one.candidate_count == d("0.000000")
    assert report_one.row_count == d("0.000000")
    assert report_one.blocked_count == d("0.000000")
    assert report_one.watch_count == d("0.000000")
    assert report_one.clear_count == d("0.000000")
    assert report_one.recheck_count == d("0.000000")
    assert report_one.priority_ratio == d("0.000000")
    assert report_one.max_priority_score == d("0.000000")
    assert report_one.max_source_age_seconds is None
    assert report_one.min_prior_source_reliability is None
    assert report_one.status == "empty"
    assert report_one.reason_codes == ("empty_source_recheck_priority_inputs",)
    assert report_one.rows == ()
    assert report_one.derived_validation_digest == report_two.derived_validation_digest
    assert report_one.paper_only is True
    assert report_one.report_only is True
    assert report_one.readonly is True


def test_dataclasses_are_frozen_exact_decimal_only_and_reject_subclassing() -> None:
    ranker = module()

    assert ranker.__all__ == (
        "DEFAULT_RESEARCH_PACKET_SOURCE_RECHECK_PRIORITY_RANKER_V2_CONFIG_VERSION",
        "ResearchPacketSourceRecheckPriorityRankerV2Config",
        "ResearchPacketSourceRecheckPriorityCandidateV2",
        "ResearchPacketSourceRecheckPriorityRowV2",
        "ResearchPacketSourceRecheckPriorityReportV2",
        "build_research_packet_source_recheck_priority_ranker_v2",
        "research_packet_source_recheck_priority_ranker_v2_payload",
        "validate_research_packet_source_recheck_priority_ranker_v2_payload",
    )
    for exported_name in ranker.__all__:
        value = getattr(ranker, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    report = build_report(candidate("packet-frozen"))
    for item in (cfg(), candidate(), report, *report.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) not in (int, float)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_score")
                or field.name.endswith("_seconds")
                or field.name.endswith("_severity")
                or field.name.endswith("_magnitude")
                or field.name.endswith("_ratio")
                or field.name.endswith("_reliability")
                or field.name.endswith("_ceiling")
                or field.name == "priority_rank"
            ):
                assert value is None or type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].priority_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(cfg(), report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="source_age_watch_seconds must be a Decimal"):
        cfg(source_age_watch_seconds=DerivedDecimal("3600.000000"))

    with pytest.raises(TypeError, match="subclassing"):

        class ConfigSubclass(ranker.ResearchPacketSourceRecheckPriorityRankerV2Config):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class CandidateSubclass(ranker.ResearchPacketSourceRecheckPriorityCandidateV2):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class RowSubclass(ranker.ResearchPacketSourceRecheckPriorityRowV2):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class ReportSubclass(ranker.ResearchPacketSourceRecheckPriorityReportV2):
            pass


def test_validation_rejects_bad_times_ratios_flags_duplicates_and_tampering() -> None:
    ranker = module()

    with pytest.raises(ValueError, match="official_source_present must be a bool"):
        candidate(official_source_present=1)
    with pytest.raises(ValueError, match="contradiction_severity must be a Decimal"):
        candidate(contradiction_severity=0.5)
    with pytest.raises(ValueError, match="prior_source_reliability"):
        candidate(prior_source_reliability=d("1.100000"))
    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        candidate(source_observed_at=datetime(2026, 7, 2, 11, 0))
    with pytest.raises(ValueError, match="market_close_at must be timezone-aware"):
        candidate(
            market_close_at=datetime(
                2026,
                7,
                2,
                13,
                0,
                tzinfo=NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        ranker.build_research_packet_source_recheck_priority_ranker_v2(
            (),
            config=cfg(),
            generated_at=DerivedDatetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_observed_at must not be after generated_at"):
        build_report(
            candidate(
                source_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="duplicate source keys"):
        build_report(candidate("packet-dupe"), candidate("packet-dupe"))
    with pytest.raises(ValueError, match="source_age_blocked_seconds"):
        cfg(source_age_watch_seconds=d("7200.000000"), source_age_blocked_seconds=d("3600.000000"))
    with pytest.raises(ValueError, match="close_urgency_blocked_seconds"):
        cfg(
            close_urgency_blocked_seconds=d("21600.000000"),
            close_urgency_watch_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="config"):
        ranker.build_research_packet_source_recheck_priority_ranker_v2(
            (candidate(),),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="candidates"):
        ranker.build_research_packet_source_recheck_priority_ranker_v2(
            "bad",
            config=cfg(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unsafe"):
        candidate(packet_id="wallet-packet")

    shifted = build_report(
        candidate("packet-shifted"),
        generated_at=datetime(2026, 7, 2, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    assert shifted.generated_at == GENERATED_AT
    assert shifted.generated_at.tzinfo is UTC

    report = build_report(candidate("packet-tamper", contradiction_severity=d("0.650000")))
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=d("2.000000"))
    with pytest.raises(ValueError, match="priority_score"):
        replace(report.rows[0], priority_score=d("1.000000"))
    with pytest.raises(ValueError, match="priority_rank"):
        replace(report.rows[0], priority_rank=d("2.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = ranker.research_packet_source_recheck_priority_ranker_v2_payload(report)
    tampered = {
        **payload,
        "rows": [{**payload["rows"][0], "priority_score": "1.000000"}],
    }
    with pytest.raises(ValueError, match="derived_validation_digest"):
        ranker.validate_research_packet_source_recheck_priority_ranker_v2_payload(
            tampered,
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        ranker.validate_research_packet_source_recheck_priority_ranker_v2_payload(
            {**payload, "candidate_count": 1},
        )
    with pytest.raises(ValueError, match="readonly"):
        ranker.validate_research_packet_source_recheck_priority_ranker_v2_payload(
            {**payload, "readonly": False},
        )


def test_module_scope_is_pure_phase_one_without_external_effects() -> None:
    ranker = module()
    source = ranker.__loader__.get_source(ranker.__name__)
    assert source is not None
    lowered = source.lower()

    for forbidden in (
        "requests",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "sqlite",
        "open(",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
        "fast",
        "live",
        "network",
        "database",
        "write(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "http",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "executemany",
        "float",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "delete",
        "send",
        "write",
        "dump",
        "dumps",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
