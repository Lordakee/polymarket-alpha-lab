from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 15, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def _api():
    return import_module(
        "polymarket_alpha_lab."
        "research_packet_source_disagreement_resolution_playbook_v2",
    )


def _decimal(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> object:
    module = _api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_PACKET_SOURCE_DISAGREEMENT_RESOLUTION_PLAYBOOK_V2_CONFIG_VERSION
        ),
        "min_independent_source_family_count": _decimal("3"),
        "stale_disagreement_age_seconds": _decimal("7200.000000"),
    }
    values.update(overrides)
    return module.ResearchPacketSourceDisagreementResolutionPlaybookConfig(**values)


def _input(
    disagreement_id: str,
    *,
    packet_ref: str = "packet-public-1",
    market_slug: str = "fed-cut-july-2026",
    disagreement_status: str = "open",
    source_families: tuple[str, ...] = ("official", "primary", "proxy"),
    disputed_outcome_keys: tuple[str, ...] = ("yes", "no"),
    observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    has_official_resolution_source: bool = True,
    has_primary_source_trace: bool = True,
    has_rule_text_trace: bool = True,
    has_settlement_evidence: bool = True,
    resolution_owner: str | None = "research-lead",
    source_config_version: str = "research-packet-source-disagreement-feed-v0",
) -> object:
    return _api().ResearchPacketSourceDisagreementInput(
        packet_ref=packet_ref,
        market_slug=market_slug,
        disagreement_id=disagreement_id,
        disagreement_status=disagreement_status,
        source_families=source_families,
        disputed_outcome_keys=disputed_outcome_keys,
        observed_at=observed_at,
        has_official_resolution_source=has_official_resolution_source,
        has_primary_source_trace=has_primary_source_trace,
        has_rule_text_trace=has_rule_text_trace,
        has_settlement_evidence=has_settlement_evidence,
        resolution_owner=resolution_owner,
        source_config_version=source_config_version,
    )


def _report(
    *rows: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> object:
    return _api().build_research_packet_source_disagreement_resolution_playbook_v2(
        rows,
        config=cfg or _config(),
        generated_at=generated_at,
    )


def _assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_float_values(item)


def test_playbook_converts_open_disagreements_to_followups_and_evidence_gaps() -> None:
    module = _api()
    blocked_all = _input(
        "disagreement-z",
        packet_ref="packet-z",
        market_slug="crypto-btc-etf",
        source_families=("proxy", "community"),
        observed_at=GENERATED_AT - timedelta(hours=5),
        has_official_resolution_source=False,
        has_primary_source_trace=False,
        has_rule_text_trace=False,
        has_settlement_evidence=False,
        resolution_owner=None,
    )
    stale_watch = _input(
        "disagreement-a",
        packet_ref="packet-a",
        market_slug="macro-cpi-print",
        observed_at=GENERATED_AT - timedelta(hours=3),
    )
    resolved_ignored = _input(
        "disagreement-r",
        packet_ref="packet-r",
        disagreement_status="resolved",
        source_families=("proxy",),
        observed_at=GENERATED_AT - timedelta(days=2),
        has_official_resolution_source=False,
        has_primary_source_trace=False,
        has_rule_text_trace=False,
        has_settlement_evidence=False,
        resolution_owner=None,
    )

    report = _report(stale_watch, resolved_ignored, blocked_all)

    assert type(report) is module.ResearchPacketSourceDisagreementResolutionPlaybookReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research-packet-source-disagreement-resolution-playbook-v2"
    )
    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "open_source_disagreement",
        "official_resolution_source_followup_required",
        "primary_source_trace_followup_required",
        "independent_source_family_gap",
        "rule_text_trace_gap",
        "settlement_evidence_gap",
        "missing_resolution_owner",
        "stale_source_disagreement",
    )
    assert report.source_row_count == _decimal("3")
    assert report.open_disagreement_count == _decimal("2")
    assert report.blocked_playbook_count == _decimal("1")
    assert report.watch_playbook_count == _decimal("1")
    assert report.official_followup_required_count == _decimal("1")
    assert report.primary_followup_required_count == _decimal("1")
    assert report.independent_family_gap_count == _decimal("1")
    assert report.rule_text_gap_count == _decimal("1")
    assert report.settlement_evidence_gap_count == _decimal("1")
    assert report.owner_escalation_count == _decimal("1")
    assert report.stale_disagreement_count == _decimal("2")
    assert report.max_disagreement_age_seconds == _decimal("18000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert report.rows == (
        module.ResearchPacketSourceDisagreementResolutionPlaybookRow(
            packet_ref="packet-z",
            market_slug="crypto-btc-etf",
            disagreement_id="disagreement-z",
            playbook_status="blocked",
            source_families=("community", "proxy"),
            disputed_outcome_keys=("no", "yes"),
            source_family_count=_decimal("2"),
            disputed_outcome_count=_decimal("2"),
            disagreement_age_seconds=_decimal("18000.000000"),
            required_followup_source_families=(
                "official_resolution_source",
                "primary_source_trace",
                "independent_source_family",
                "rule_text_trace",
                "settlement_evidence",
            ),
            escalation_reasons=(
                "missing_resolution_owner",
                "stale_source_disagreement",
            ),
            minimum_evidence_gaps=(
                "missing_official_resolution_source",
                "missing_primary_source_trace",
                "independent_source_family_count_below_minimum",
                "missing_rule_text_trace",
                "missing_settlement_evidence",
            ),
            reason_codes=(
                "open_source_disagreement",
                "official_resolution_source_followup_required",
                "primary_source_trace_followup_required",
                "independent_source_family_gap",
                "rule_text_trace_gap",
                "settlement_evidence_gap",
                "missing_resolution_owner",
                "stale_source_disagreement",
            ),
            source_config_version="research-packet-source-disagreement-feed-v0",
        ),
        module.ResearchPacketSourceDisagreementResolutionPlaybookRow(
            packet_ref="packet-a",
            market_slug="macro-cpi-print",
            disagreement_id="disagreement-a",
            playbook_status="watch",
            source_families=("official", "primary", "proxy"),
            disputed_outcome_keys=("no", "yes"),
            source_family_count=_decimal("3"),
            disputed_outcome_count=_decimal("2"),
            disagreement_age_seconds=_decimal("10800.000000"),
            required_followup_source_families=(),
            escalation_reasons=("stale_source_disagreement",),
            minimum_evidence_gaps=(),
            reason_codes=(
                "open_source_disagreement",
                "stale_source_disagreement",
            ),
            source_config_version="research-packet-source-disagreement-feed-v0",
        ),
    )


def test_clear_report_payload_utc_and_decimal_only_contract() -> None:
    module = _api()
    offset = timezone(timedelta(hours=-4))

    clear = _report(generated_at=datetime(2026, 7, 2, 11, 0, tzinfo=offset))
    resolved = _report(
        _input(
            "resolved-only",
            disagreement_status="resolved",
            observed_at=datetime(2026, 7, 2, 8, 0, tzinfo=offset),
        ),
    )

    assert clear == module.ResearchPacketSourceDisagreementResolutionPlaybookReport(
        generated_at=GENERATED_AT,
        config_version="research-packet-source-disagreement-resolution-playbook-v2",
        report_status="clear",
        reason_codes=(),
        source_row_count=_decimal("0"),
        open_disagreement_count=_decimal("0"),
        blocked_playbook_count=_decimal("0"),
        watch_playbook_count=_decimal("0"),
        official_followup_required_count=_decimal("0"),
        primary_followup_required_count=_decimal("0"),
        independent_family_gap_count=_decimal("0"),
        rule_text_gap_count=_decimal("0"),
        settlement_evidence_gap_count=_decimal("0"),
        owner_escalation_count=_decimal("0"),
        stale_disagreement_count=_decimal("0"),
        max_disagreement_age_seconds=_decimal("0.000000"),
        rows=(),
    )
    assert resolved.report_status == "clear"
    assert resolved.source_row_count == _decimal("1")
    assert resolved.open_disagreement_count == _decimal("0")
    assert resolved.rows == ()
    assert all(
        type(value) is Decimal
        for value in (
            clear.source_row_count,
            clear.open_disagreement_count,
            clear.max_disagreement_age_seconds,
        )
    )

    payload = module.research_packet_source_disagreement_resolution_playbook_v2_payload(
        clear,
    )
    assert payload["generated_at"] == "2026-07-02T15:00:00+00:00"
    assert payload["source_row_count"] == "0"
    assert payload["max_disagreement_age_seconds"] == "0.000000"
    _assert_no_float_values(payload)


def test_validation_rejects_impure_flags_duplicate_rows_and_non_decimal_scores() -> None:
    module = _api()

    with pytest.raises(ValueError, match="stale_disagreement_age_seconds must be a Decimal"):
        _config(stale_disagreement_age_seconds=7200.0)
    with pytest.raises(ValueError, match="must be exactly datetime"):
        _input("bad-datetime", observed_at=_DatetimeSubclass(2026, 7, 2, tzinfo=UTC))
    with pytest.raises(ValueError, match="min_independent_source_family_count must be a Decimal"):
        _config(min_independent_source_family_count=_DecimalSubclass("3"))
    with pytest.raises(ValueError, match="must be True"):
        module.ResearchPacketSourceDisagreementInput(
            packet_ref="packet-public-1",
            market_slug="fed-cut-july-2026",
            disagreement_id="unsafe-flags",
            disagreement_status="open",
            source_families=("official",),
            disputed_outcome_keys=("yes", "no"),
            observed_at=GENERATED_AT,
            has_official_resolution_source=True,
            has_primary_source_trace=True,
            has_rule_text_trace=True,
            has_settlement_evidence=True,
            resolution_owner="research-lead",
            source_config_version="source-config-v0",
            readonly=False,
        )
    with pytest.raises(ValueError, match="disagreement_id values must be unique per packet_ref"):
        _report(_input("duplicate"), _input("duplicate"))

    row = _input("frozen")
    with pytest.raises(FrozenInstanceError):
        row.market_slug = "mutated"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly must be True for source row"):
        _report(replace(row, readonly=False))


def test_module_is_readonly_report_only_paper_only_without_io_or_live_side_effects() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "src/polymarket_alpha_lab/research_packet_source_disagreement_resolution_playbook_v2.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "asyncio",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "get",
        "open",
        "post",
        "put",
        "send",
        "submit_order",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".", maxsplit=1)[0] for alias in node.names}
            assert imported_roots.isdisjoint(forbidden_import_roots)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", maxsplit=1)[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            if isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
