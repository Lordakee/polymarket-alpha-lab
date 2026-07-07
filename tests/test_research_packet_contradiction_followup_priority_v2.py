from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_contradiction_followup_priority_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "recency_window_hours": d("24.000000"),
        "market_close_urgency_window_seconds": d("3600.000000"),
        "source_family_independence_watch_score": d("0.500000"),
        "recency_watch_score": d("0.500000"),
        "severity_watch_score": d("0.500000"),
        "resolution_rule_sensitivity_watch_score": d("0.500000"),
        "market_close_urgency_watch_score": d("0.500000"),
        "watch_priority_score": d("0.350000"),
        "blocked_priority_score": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchPacketContradictionFollowupPriorityV2Config(**values)


def contradiction(packet_id: str, **overrides: object):
    module = api()
    values = {
        "packet_id": packet_id,
        "event_id": "event-fomc",
        "market_id": f"market-{packet_id}",
        "contradiction_id": f"contradiction-{packet_id}",
        "source_family": "official_release",
        "source_family_count": d("4"),
        "independent_source_family_count": d("2"),
        "contradiction_observed_at": GENERATED_AT - timedelta(hours=6),
        "contradiction_severity_score": d("0.500000"),
        "resolution_rule_sensitivity_score": d("0.500000"),
        "market_close_at": GENERATED_AT + timedelta(hours=2),
    }
    values.update(overrides)
    return module.ResearchPacketContradictionFollowupPriorityV2Input(**values)


def priority_report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_packet_contradiction_followup_priority_v2_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_scalars(value: Any) -> None:
    if isinstance(value, dict):
        for child in value.values():
            assert_no_public_numeric_scalars(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_public_numeric_scalars(child)
    else:
        assert type(value) not in (int, float, Decimal)


def test_empty_report_is_readonly_paper_report_only_with_deterministic_digest() -> None:
    module = api()
    report = priority_report()

    assert type(report) is module.ResearchPacketContradictionFollowupPriorityV2Report
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research-packet-contradiction-followup-priority-v2"
    )
    assert report.status == "empty"
    assert report.input_count == d("0")
    assert report.priority_count == d("0")
    assert report.max_priority_score == d("0.000000")
    assert report.average_priority_score == d("0.000000")
    assert report.reason_codes == ("contradiction_followup_priority_empty",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)


def test_ranks_contradiction_followups_by_independence_recency_severity_rule_and_close_urgency() -> None:
    report = priority_report(
        contradiction(
            "packet-clear",
            source_family="social_proxy",
            source_family_count=d("4"),
            independent_source_family_count=d("1"),
            contradiction_observed_at=GENERATED_AT - timedelta(hours=30),
            contradiction_severity_score=d("0.100000"),
            resolution_rule_sensitivity_score=d("0.100000"),
            market_close_at=GENERATED_AT + timedelta(hours=5),
        ),
        contradiction(
            "packet-blocked",
            source_family="official_release",
            source_family_count=d("4"),
            independent_source_family_count=d("4"),
            contradiction_observed_at=GENERATED_AT - timedelta(hours=1),
            contradiction_severity_score=d("0.900000"),
            resolution_rule_sensitivity_score=d("0.800000"),
            market_close_at=GENERATED_AT + timedelta(minutes=10),
        ),
        contradiction(
            "packet-watch",
            source_family="newswire",
            source_family_count=d("4"),
            independent_source_family_count=d("1"),
            contradiction_observed_at=GENERATED_AT - timedelta(hours=12),
            contradiction_severity_score=d("0.400000"),
            resolution_rule_sensitivity_score=d("0.300000"),
            market_close_at=GENERATED_AT + timedelta(minutes=15),
        ),
    )

    assert tuple(row.packet_id for row in report.rows) == (
        "packet-blocked",
        "packet-watch",
        "packet-clear",
    )
    assert tuple(row.priority_rank for row in report.rows) == (
        d("1"),
        d("2"),
        d("3"),
    )
    assert report.status == "blocked"
    assert report.input_count == d("3")
    assert report.priority_count == d("2")
    assert report.blocked_count == d("1")
    assert report.watch_count == d("1")
    assert report.clear_count == d("1")
    assert report.source_family_independence_count == d("1")
    assert report.recent_contradiction_count == d("2")
    assert report.severe_contradiction_count == d("1")
    assert report.rule_sensitive_count == d("1")
    assert report.market_close_urgent_count == d("2")
    assert report.max_priority_score == d("0.901667")
    assert report.average_priority_score == d("0.473056")
    assert report.reason_codes == (
        "source_family_independent_followup",
        "recent_contradiction_followup",
        "severe_contradiction_followup",
        "resolution_rule_sensitive_followup",
        "market_close_urgent_followup",
        "contradiction_followup_priority_watch",
        "contradiction_followup_priority_blocked",
    )

    first = report.rows[0]
    assert first.packet_id == "packet-blocked"
    assert first.source_family_independence_score == d("1.000000")
    assert first.evidence_age_hours == d("1.000000")
    assert first.recency_score == d("0.958333")
    assert first.seconds_until_market_close == d("600.000000")
    assert first.market_close_urgency_score == d("0.833333")
    assert first.followup_priority_score == d("0.901667")
    assert first.status == "blocked"
    assert first.reason_codes == (
        "source_family_independent_followup",
        "recent_contradiction_followup",
        "severe_contradiction_followup",
        "resolution_rule_sensitive_followup",
        "market_close_urgent_followup",
        "contradiction_followup_priority_blocked",
    )

    watch = report.rows[1]
    assert watch.followup_priority_score == d("0.422500")
    assert watch.status == "watch"
    assert watch.reason_codes == (
        "recent_contradiction_followup",
        "market_close_urgent_followup",
        "contradiction_followup_priority_watch",
    )

    clear = report.rows[2]
    assert clear.recency_score == d("0.000000")
    assert clear.market_close_urgency_score == d("0.000000")
    assert clear.followup_priority_score == d("0.095000")
    assert clear.status == "clear"
    assert clear.reason_codes == ("contradiction_followup_priority_clear",)


def test_payload_uses_decimal_strings_iso_datetimes_flags_and_digest_validation() -> None:
    module = api()
    generated_at = datetime(2026, 7, 7, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    report = priority_report(
        contradiction(
            "packet-json",
            source_family="official_release",
            source_family_count=d("4"),
            independent_source_family_count=d("4"),
            contradiction_observed_at=datetime(
                2026,
                7,
                7,
                7,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            contradiction_severity_score=d("0.900000"),
            resolution_rule_sensitivity_score=d("0.800000"),
            market_close_at=datetime(
                2026,
                7,
                7,
                8,
                10,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=generated_at,
    )

    payload = module.research_packet_contradiction_followup_priority_v2_payload(report)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["input_count"] == "1"
    assert payload["max_priority_score"] == "0.901667"
    assert payload["rows"][0]["contradiction_observed_at"] == (
        "2026-07-07T11:00:00+00:00"
    )
    assert payload["rows"][0]["market_close_at"] == "2026-07-07T12:10:00+00:00"
    assert payload["rows"][0]["seconds_until_market_close"] == "600.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["derived_validation_digest"] == (
        report.rows[0].derived_validation_digest
    )
    assert_no_public_numeric_scalars(payload)

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, priority_count=d("0"))

    tampered = dict(payload)
    tampered["status"] = "clear"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.research_packet_contradiction_followup_priority_v2_payload(tampered)


def test_rejects_non_decimal_subclasses_naive_datetimes_false_flags_and_duplicate_ids() -> None:
    with pytest.raises(ValueError, match="recency_window_hours must be a Decimal"):
        config(recency_window_hours=_DecimalSubclass("24.000000"))
    with pytest.raises(ValueError, match="contradiction_observed_at must be timezone-aware"):
        contradiction(
            "packet-naive",
            contradiction_observed_at=datetime(2026, 7, 7, 11, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        priority_report(
            contradiction("packet-datetime-subclass"),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="contradiction_observed_at must not be after generated_at"):
        priority_report(
            contradiction(
                "packet-future",
                contradiction_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="market_close_at must not be before generated_at"):
        priority_report(
            contradiction(
                "packet-closed",
                market_close_at=GENERATED_AT - timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="inputs must not contain duplicate contradiction_id"):
        priority_report(contradiction("packet-a"), contradiction("packet-b", contradiction_id="contradiction-packet-a"))
    with pytest.raises(ValueError, match="independent_source_family_count"):
        contradiction(
            "packet-too-independent",
            source_family_count=d("2"),
            independent_source_family_count=d("3"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(contradiction("packet-not-paper"), paper_only=False)

    report = priority_report(contradiction("packet-frozen"))
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_module_is_pure_readonly_report_only_and_has_no_execution_or_io_surface() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_CONTRADICTION_FOLLOWUP_PRIORITY_V2_CONFIG_VERSION",
        "ResearchPacketContradictionFollowupPriorityV2Config",
        "ResearchPacketContradictionFollowupPriorityV2Input",
        "ResearchPacketContradictionFollowupPriorityV2Report",
        "ResearchPacketContradictionFollowupPriorityV2Row",
        "build_research_packet_contradiction_followup_priority_v2_report",
        "research_packet_contradiction_followup_priority_v2_payload",
    )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    forbidden_import_roots = {
        "builtins",
        "http",
        "io",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_calls = {
        "compile",
        "connect",
        "eval",
        "exec",
        "execute",
        "executemany",
        "open",
        "request",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_calls

    assert not any("db" in imported_module.lower() for imported_module in imported_modules)
    assert "paper_only" in source
    assert "report_only" in source
    assert "readonly" in source
