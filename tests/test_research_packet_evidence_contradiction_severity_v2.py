from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
import inspect
import json

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_packet_evidence_contradiction_severity_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_PACKET_EVIDENCE_CONTRADICTION_SEVERITY_V2_CONFIG_VERSION
        ),
        "freshness_window_hours": d("24.000000"),
        "market_close_urgency_window_hours": d("12.000000"),
        "independent_source_family_block_threshold": d("3.000000"),
        "claim_conflict_block_threshold": d("3.000000"),
        "watch_severity_threshold": d("0.350000"),
        "blocked_severity_threshold": d("0.750000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchPacketEvidenceContradictionSeverityConfig(**values)


def evidence(
    evidence_id: str,
    *,
    source_family: str,
    source_id: str,
    hours_ago: int,
    claimed_outcome: str,
    reference_outcome: str,
    official_source: bool,
    resolution_rule_sensitivity_score: str,
    packet_id: str = "packet-fed-rate-cut",
    event_id: str = "event-fed-rate-cut",
    market_close_hours: int = 2,
):
    module = api()
    return module.ResearchPacketEvidenceContradictionInput(
        packet_id=packet_id,
        event_id=event_id,
        evidence_id=evidence_id,
        source_family=source_family,
        source_id=source_id,
        observed_at=GENERATED_AT - timedelta(hours=hours_ago),
        market_closes_at=GENERATED_AT + timedelta(hours=market_close_hours),
        claimed_outcome=claimed_outcome,
        reference_outcome=reference_outcome,
        official_source=official_source,
        resolution_rule_sensitivity_score=d(resolution_rule_sensitivity_score),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def scored_report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_packet_evidence_contradiction_severity_v2_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def sample_rows() -> tuple[object, ...]:
    return (
        evidence(
            "evidence-clear",
            source_family="analyst-model",
            source_id="model-a",
            hours_ago=1,
            claimed_outcome="rate-cut-yes",
            reference_outcome="rate-cut-yes",
            official_source=False,
            resolution_rule_sensitivity_score="0.400000",
        ),
        evidence(
            "evidence-proxy",
            source_family="prediction-proxy",
            source_id="proxy-a",
            hours_ago=8,
            claimed_outcome="rate-cut-no",
            reference_outcome="rate-cut-yes",
            official_source=False,
            resolution_rule_sensitivity_score="0.500000",
        ),
        evidence(
            "evidence-official",
            source_family="official-release",
            source_id="fomc-release",
            hours_ago=1,
            claimed_outcome="rate-cut-no",
            reference_outcome="rate-cut-yes",
            official_source=True,
            resolution_rule_sensitivity_score="0.900000",
        ),
        evidence(
            "evidence-wire",
            source_family="newswire",
            source_id="wire-a",
            hours_ago=2,
            claimed_outcome="rate-cut-no",
            reference_outcome="rate-cut-yes",
            official_source=False,
            resolution_rule_sensitivity_score="0.800000",
        ),
    )


def test_scores_contradiction_severity_from_required_components_deterministically() -> None:
    report = scored_report(*sample_rows())
    repeated = scored_report(*reversed(sample_rows()))

    assert type(report) is api().ResearchPacketEvidenceContradictionSeverityReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research-packet-evidence-contradiction-severity-v2"
    )
    assert report.packet_count == d("1.000000")
    assert report.event_count == d("1.000000")
    assert report.evidence_count == d("4.000000")
    assert report.contradiction_count == d("3.000000")
    assert report.independent_source_family_conflict_count == d("3.000000")
    assert report.fresh_conflict_count == d("3.000000")
    assert report.official_source_conflict_count == d("1.000000")
    assert report.resolution_rule_sensitive_conflict_count == d("3.000000")
    assert report.market_close_urgent_conflict_count == d("3.000000")
    assert report.blocked_count == d("2.000000")
    assert report.watch_count == d("1.000000")
    assert report.clear_count == d("1.000000")
    assert report.max_contradiction_severity_score == d("0.953750")
    assert report.status == "blocked"
    assert report.reason_codes == (
        "evidence_claim_conflicts_present",
        "independent_source_family_conflicts_present",
        "fresh_contradictory_evidence_present",
        "official_source_conflict_present",
        "resolution_rule_sensitive_conflict_present",
        "market_close_urgency_present",
        "evidence_contradiction_severity_blocked",
    )
    assert report.derived_validation_digest == repeated.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert tuple(row.evidence_id for row in report.rows) == (
        "evidence-official",
        "evidence-wire",
        "evidence-proxy",
        "evidence-clear",
    )

    official = report.rows[0]
    assert official.contradicts_reference is True
    assert official.evidence_age_hours == d("1.000000")
    assert official.hours_to_market_close == d("2.000000")
    assert official.source_family_independence_score == d("1.000000")
    assert official.evidence_freshness_score == d("0.958333")
    assert official.claim_conflict_count == d("3.000000")
    assert official.claim_conflict_score == d("1.000000")
    assert official.official_source_conflict_score == d("1.000000")
    assert official.resolution_rule_sensitivity_score == d("0.900000")
    assert official.market_close_urgency_score == d("0.833333")
    assert official.contradiction_severity_score == d("0.953750")
    assert official.status == "blocked"
    assert official.reason_codes == (
        "evidence_claim_conflict",
        "evidence_source_family_independent_conflict",
        "evidence_fresh_conflict",
        "evidence_official_source_conflict",
        "evidence_resolution_rule_sensitive",
        "evidence_market_close_urgent",
        "evidence_contradiction_severity_blocked",
    )

    wire = report.rows[1]
    assert wire.official_source_conflict_score == d("0.000000")
    assert wire.evidence_freshness_score == d("0.916667")
    assert wire.contradiction_severity_score == d("0.782500")
    assert wire.status == "blocked"

    proxy = report.rows[2]
    assert proxy.evidence_freshness_score == d("0.666667")
    assert proxy.contradiction_severity_score == d("0.700000")
    assert proxy.status == "watch"

    clear = report.rows[3]
    assert clear.contradicts_reference is False
    assert clear.contradiction_severity_score == d("0.000000")
    assert clear.status == "clear"
    assert clear.reason_codes == ("evidence_contradiction_severity_clear",)


def test_payload_is_json_ready_decimal_stringed_and_digest_validated() -> None:
    module = api()
    report = scored_report(*sample_rows())

    payload = module.research_packet_evidence_contradiction_severity_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["evidence_count"] == "4.000000"
    assert payload["contradiction_count"] == "3.000000"
    assert payload["max_contradiction_severity_score"] == "0.953750"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    official = payload["rows"][0]
    assert official["evidence_id"] == "evidence-official"
    assert official["contradiction_severity_score"] == "0.953750"
    assert official["claim_conflict_count"] == "3.000000"
    assert_no_numeric_scalars(payload)
    json.dumps(payload, sort_keys=True)

    accepted_payload = module.research_packet_evidence_contradiction_severity_v2_payload(
        payload,
    )
    assert accepted_payload == payload

    tampered = dict(payload)
    tampered["status"] = "clear"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.research_packet_evidence_contradiction_severity_v2_payload(tampered)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_packet_evidence_contradiction_severity_v2_payload(missing_digest)


def test_low_severity_contradiction_below_watch_threshold_remains_clear() -> None:
    report = scored_report(
        evidence(
            "evidence-low-severity-conflict",
            source_family="low-impact-source",
            source_id="low-impact-source-a",
            hours_ago=30,
            claimed_outcome="rate-cut-no",
            reference_outcome="rate-cut-yes",
            official_source=False,
            resolution_rule_sensitivity_score="0.000000",
            market_close_hours=48,
        ),
    )

    assert report.status == "clear"
    assert report.contradiction_count == d("1.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.clear_count == d("1.000000")
    assert report.reason_codes == (
        "evidence_claim_conflicts_present",
        "evidence_contradiction_severity_clear",
    )

    row = report.rows[0]
    assert row.contradicts_reference is True
    assert row.contradiction_severity_score == d("0.133333")
    assert row.watch_severity_threshold == d("0.350000")
    assert row.blocked_severity_threshold == d("0.750000")
    assert row.status == "clear"
    assert row.reason_codes == (
        "evidence_claim_conflict",
        "evidence_source_family_independent_conflict",
        "evidence_contradiction_severity_clear",
    )

    payload = api().research_packet_evidence_contradiction_severity_v2_payload(report)
    payload_row = payload["rows"][0]
    assert payload_row["watch_severity_threshold"] == "0.350000"
    assert payload_row["blocked_severity_threshold"] == "0.750000"


def test_empty_and_clear_inputs_are_report_only_decimal_and_deterministic() -> None:
    empty = scored_report()
    clear = scored_report(
        evidence(
            "evidence-clear-b",
            source_family="model-b",
            source_id="model-b",
            hours_ago=2,
            claimed_outcome="rate-cut-yes",
            reference_outcome="rate-cut-yes",
            official_source=False,
            resolution_rule_sensitivity_score="0.200000",
        ),
        evidence(
            "evidence-clear-a",
            source_family="model-a",
            source_id="model-a",
            hours_ago=3,
            claimed_outcome="rate-cut-yes",
            reference_outcome="rate-cut-yes",
            official_source=False,
            resolution_rule_sensitivity_score="0.300000",
        ),
    )

    assert empty.status == "blocked"
    assert empty.evidence_count == d("0.000000")
    assert empty.contradiction_count == d("0.000000")
    assert empty.max_contradiction_severity_score == d("0.000000")
    assert empty.reason_codes == ("evidence_contradiction_severity_no_inputs",)
    assert empty.rows == ()

    assert clear.status == "clear"
    assert clear.evidence_count == d("2.000000")
    assert clear.contradiction_count == d("0.000000")
    assert clear.reason_codes == ("evidence_contradiction_severity_clear",)
    assert tuple(row.evidence_id for row in clear.rows) == (
        "evidence-clear-a",
        "evidence-clear-b",
    )
    assert all(row.status == "clear" for row in clear.rows)
    assert all(type(row.contradiction_severity_score) is Decimal for row in clear.rows)


def test_dataclasses_are_frozen_strict_decimal_only_and_hard_flagged() -> None:
    module = api()
    row = sample_rows()[0]
    report = scored_report(*sample_rows())

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_EVIDENCE_CONTRADICTION_SEVERITY_V2_CONFIG_VERSION",
        "ResearchPacketEvidenceContradictionInput",
        "ResearchPacketEvidenceContradictionSeverityConfig",
        "ResearchPacketEvidenceContradictionSeverityReport",
        "ResearchPacketEvidenceContradictionSeverityRow",
        "build_research_packet_evidence_contradiction_severity_v2_report",
        "research_packet_evidence_contradiction_severity_v2_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    with pytest.raises(FrozenInstanceError):
        report.rows[0].evidence_id = "mutated"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                "research-packet-evidence-contradiction-severity-v2",
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        scored_report(*sample_rows(), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="resolution_rule_sensitivity_score"):
        replace(row, resolution_rule_sensitivity_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        evidence(
            "evidence-naive",
            source_family="model-naive",
            source_id="model-naive",
            hours_ago=1,
            claimed_outcome="yes",
            reference_outcome="no",
            official_source=False,
            resolution_rule_sensitivity_score="0.100000",
        ).__class__(
            packet_id="packet-naive",
            event_id="event-naive",
            evidence_id="evidence-naive",
            source_family="model-naive",
            source_id="model-naive",
            observed_at=datetime(2026, 7, 6, 11, 0),
            market_closes_at=GENERATED_AT + timedelta(hours=2),
            claimed_outcome="yes",
            reference_outcome="no",
            official_source=False,
            resolution_rule_sensitivity_score=d("0.100000"),
        )
    with pytest.raises(ValueError, match="official_source must be a bool"):
        replace(row, official_source="true")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, contradiction_count=d("9.000000"))


def test_reducer_rejects_bad_inputs_duplicates_future_times_and_bad_config() -> None:
    module = api()
    row = sample_rows()[0]

    with pytest.raises(ValueError, match="ResearchPacketEvidenceContradictionSeverityConfig"):
        module.build_research_packet_evidence_contradiction_severity_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="evidence must be a list or tuple"):
        module.build_research_packet_evidence_contradiction_severity_v2_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="ResearchPacketEvidenceContradictionInput"):
        scored_report(object())
    with pytest.raises(ValueError, match="unique by packet_id and evidence_id"):
        scored_report(row, row)
    with pytest.raises(ValueError, match="packet_id must map to exactly one event_id"):
        scored_report(
            row,
            evidence(
                "evidence-other-event",
                packet_id=row.packet_id,
                event_id="event-other",
                source_family="wire-other",
                source_id="wire-other",
                hours_ago=1,
                claimed_outcome="no",
                reference_outcome="yes",
                official_source=False,
                resolution_rule_sensitivity_score="0.100000",
            ),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        scored_report(replace(row, observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="market_closes_at must be timezone-aware"):
        replace(row, market_closes_at=datetime(2026, 7, 6, 14, 0))
    with pytest.raises(ValueError, match="blocked_severity_threshold"):
        config(blocked_severity_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="claim_conflict_block_threshold"):
        config(claim_conflict_block_threshold=d("0.000000"))
    with pytest.raises(ValueError, match="unsafe live surface"):
        replace(row, source_id="wallet")


def test_module_is_pure_readonly_report_only_and_has_no_live_io_surface() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

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
        "eval",
        "exec",
        "input",
        "open",
    }
    forbidden_identifiers = (
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in forbidden_identifiers)
        if isinstance(node, ast.arg):
            lowered = node.arg.lower()
            assert not any(fragment in lowered for fragment in forbidden_identifiers)

    assert "paper_only" in source
    assert "report_only" in source
    assert "readonly" in source


def assert_no_numeric_scalars(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float found in payload: {value!r}")
    if type(value) is int:
        raise AssertionError(f"integer found in payload: {value!r}")
    if type(value) is Decimal:
        raise AssertionError(f"Decimal found in payload: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_numeric_scalars(child)
    if isinstance(value, list):
        for child in value:
            assert_no_numeric_scalars(child)
