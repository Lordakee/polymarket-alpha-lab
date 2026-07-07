from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 7, 11, 45, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _api():
    return import_module("polymarket_alpha_lab.research_event_lifecycle_stage_report")


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    api = _api()
    values = {
        "config_version": "research-event-lifecycle-stage-report-v0",
        "minimum_evidence_score": d("0.700000"),
        "minimum_source_quality_score": d("0.700000"),
        "maximum_conflict_score": d("0.300000"),
        "block_conflict_score": d("0.750000"),
        "minimum_settlement_readiness_score": d("0.800000"),
        "minimum_postmortem_score": d("0.700000"),
        "minimum_independent_source_count": d("2"),
        "near_settlement_seconds_threshold": d("86400"),
    }
    values.update(overrides)
    return api.ResearchEventLifecycleStageConfig(**values)


def _observation(
    event_id: str = "event-alpha",
    *,
    lifecycle_stage: str = "evidence_collection",
    observed_at: datetime = OBSERVED_AT,
    evidence_score: Decimal = d("0.920000"),
    source_quality_score: Decimal = d("0.880000"),
    conflict_score: Decimal = d("0.100000"),
    settlement_readiness_score: Decimal = d("0.900000"),
    postmortem_score: Decimal = d("0.800000"),
    seconds_until_settlement: Decimal = d("172800"),
    primary_source_count: Decimal = d("1"),
    independent_source_count: Decimal = d("3"),
    conflicting_source_count: Decimal = d("0"),
    settlement_rule_confirmed: bool = True,
    postmortem_completed: bool = True,
):
    api = _api()
    return api.ResearchEventLifecycleStageInput(
        event_id=event_id,
        lifecycle_stage=lifecycle_stage,
        observed_at=observed_at,
        evidence_score=evidence_score,
        source_quality_score=source_quality_score,
        conflict_score=conflict_score,
        settlement_readiness_score=settlement_readiness_score,
        postmortem_score=postmortem_score,
        seconds_until_settlement=seconds_until_settlement,
        primary_source_count=primary_source_count,
        independent_source_count=independent_source_count,
        conflicting_source_count=conflicting_source_count,
        settlement_rule_confirmed=settlement_rule_confirmed,
        postmortem_completed=postmortem_completed,
    )


def _report(rows: tuple[object, ...], *, cfg=None, generated_at: datetime = GENERATED_AT):
    api = _api()
    return api.build_research_event_lifecycle_stage_report(
        rows,
        config=cfg or _config(),
        generated_at=generated_at,
    )


def test_lifecycle_report_scores_stages_and_outputs_research_actions_only():
    api = _api()
    report = _report(
        (
            _observation(
                "event-discovery",
                lifecycle_stage="discovery",
                source_quality_score=d("0.650000"),
                primary_source_count=d("0"),
                independent_source_count=d("1"),
            ),
            _observation(
                "event-evidence",
                lifecycle_stage="evidence_collection",
                evidence_score=d("0.420000"),
                source_quality_score=d("0.610000"),
                primary_source_count=d("0"),
            ),
            _observation(
                "event-conflict",
                lifecycle_stage="conflict_validation",
                conflict_score=d("0.820000"),
                conflicting_source_count=d("2"),
            ),
            _observation(
                "event-settlement",
                lifecycle_stage="near_settlement",
                settlement_readiness_score=d("0.740000"),
                seconds_until_settlement=d("3600"),
                settlement_rule_confirmed=False,
            ),
            _observation(
                "event-postmortem",
                lifecycle_stage="postmortem",
                postmortem_score=d("0.620000"),
                seconds_until_settlement=d("0"),
                postmortem_completed=False,
            ),
            _observation("event-pass", lifecycle_stage="evidence_collection"),
        ),
        generated_at=datetime(2026, 7, 7, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert type(report) is api.ResearchEventLifecycleStageReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-event-lifecycle-stage-report-v0"
    assert report.event_count == d("6")
    assert report.pass_count == d("1")
    assert report.watch_count == d("2")
    assert report.block_count == d("3")
    assert report.average_stage_readiness_score == d("0.600833")
    assert report.min_stage_readiness_score == d("0.180000")
    assert report.status == "block"
    assert report.reason_codes == (
        "lifecycle_block_present",
        "lifecycle_watch_present",
        "discovery_watch_present",
        "evidence_collection_watch_present",
        "conflict_validation_block_present",
        "near_settlement_block_present",
        "postmortem_watch_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert report.stage_rows == (
        api.ResearchEventLifecycleStageRow(
            event_id="event-conflict",
            lifecycle_stage="conflict_validation",
            observed_at=OBSERVED_AT,
            status="block",
            stage_readiness_score=d("0.180000"),
            evidence_score=d("0.920000"),
            source_quality_score=d("0.880000"),
            conflict_score=d("0.820000"),
            settlement_readiness_score=d("0.900000"),
            postmortem_score=d("0.800000"),
            seconds_until_settlement=d("172800"),
            primary_source_count=d("1"),
            independent_source_count=d("3"),
            conflicting_source_count=d("2"),
            settlement_rule_confirmed=True,
            postmortem_completed=True,
            next_research_actions=("resolve_source_conflict",),
            reason_codes=("unresolved_conflict",),
        ),
        api.ResearchEventLifecycleStageRow(
            event_id="event-settlement",
            lifecycle_stage="near_settlement",
            observed_at=OBSERVED_AT,
            status="block",
            stage_readiness_score=d("0.740000"),
            evidence_score=d("0.920000"),
            source_quality_score=d("0.880000"),
            conflict_score=d("0.100000"),
            settlement_readiness_score=d("0.740000"),
            postmortem_score=d("0.800000"),
            seconds_until_settlement=d("3600"),
            primary_source_count=d("1"),
            independent_source_count=d("3"),
            conflicting_source_count=d("0"),
            settlement_rule_confirmed=False,
            postmortem_completed=True,
            next_research_actions=(
                "confirm_settlement_rules",
                "prepare_settlement_recheck",
            ),
            reason_codes=(
                "settlement_rule_unconfirmed",
                "settlement_window_imminent",
            ),
        ),
        api.ResearchEventLifecycleStageRow(
            event_id="event-evidence",
            lifecycle_stage="evidence_collection",
            observed_at=OBSERVED_AT,
            status="block",
            stage_readiness_score=d("0.515000"),
            evidence_score=d("0.420000"),
            source_quality_score=d("0.610000"),
            conflict_score=d("0.100000"),
            settlement_readiness_score=d("0.900000"),
            postmortem_score=d("0.800000"),
            seconds_until_settlement=d("172800"),
            primary_source_count=d("0"),
            independent_source_count=d("3"),
            conflicting_source_count=d("0"),
            settlement_rule_confirmed=True,
            postmortem_completed=True,
            next_research_actions=(
                "collect_primary_evidence",
                "catalog_public_sources",
            ),
            reason_codes=(
                "missing_primary_source",
                "incomplete_evidence",
                "weak_source_quality",
            ),
        ),
        api.ResearchEventLifecycleStageRow(
            event_id="event-discovery",
            lifecycle_stage="discovery",
            observed_at=OBSERVED_AT,
            status="watch",
            stage_readiness_score=d("0.650000"),
            evidence_score=d("0.920000"),
            source_quality_score=d("0.650000"),
            conflict_score=d("0.100000"),
            settlement_readiness_score=d("0.900000"),
            postmortem_score=d("0.800000"),
            seconds_until_settlement=d("172800"),
            primary_source_count=d("0"),
            independent_source_count=d("1"),
            conflicting_source_count=d("0"),
            settlement_rule_confirmed=True,
            postmortem_completed=True,
            next_research_actions=(
                "collect_primary_evidence",
                "catalog_public_sources",
            ),
            reason_codes=(
                "missing_primary_source",
                "insufficient_independent_sources",
                "weak_source_quality",
            ),
        ),
        api.ResearchEventLifecycleStageRow(
            event_id="event-postmortem",
            lifecycle_stage="postmortem",
            observed_at=OBSERVED_AT,
            status="watch",
            stage_readiness_score=d("0.620000"),
            evidence_score=d("0.920000"),
            source_quality_score=d("0.880000"),
            conflict_score=d("0.100000"),
            settlement_readiness_score=d("0.900000"),
            postmortem_score=d("0.620000"),
            seconds_until_settlement=d("0"),
            primary_source_count=d("1"),
            independent_source_count=d("3"),
            conflicting_source_count=d("0"),
            settlement_rule_confirmed=True,
            postmortem_completed=False,
            next_research_actions=("write_postmortem_notes",),
            reason_codes=(
                "postmortem_missing",
                "postmortem_incomplete",
            ),
        ),
        api.ResearchEventLifecycleStageRow(
            event_id="event-pass",
            lifecycle_stage="evidence_collection",
            observed_at=OBSERVED_AT,
            status="pass",
            stage_readiness_score=d("0.900000"),
            evidence_score=d("0.920000"),
            source_quality_score=d("0.880000"),
            conflict_score=d("0.100000"),
            settlement_readiness_score=d("0.900000"),
            postmortem_score=d("0.800000"),
            seconds_until_settlement=d("172800"),
            primary_source_count=d("1"),
            independent_source_count=d("3"),
            conflicting_source_count=d("0"),
            settlement_rule_confirmed=True,
            postmortem_completed=True,
            next_research_actions=("continue_stage_monitoring",),
            reason_codes=("lifecycle_stage_clear",),
        ),
    )

    payload = api.research_event_lifecycle_stage_report_payload(report)
    rendered = repr(payload).lower()
    for forbidden in ("recommend", "buy", "sell", "wallet", "order_id"):
        assert forbidden not in rendered


def test_empty_and_clear_reports_are_decimal_report_only_and_json_ready():
    api = _api()
    empty = _report(())
    clear = _report((_observation("event-clear"),))

    assert empty.event_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.average_stage_readiness_score == d("0.000000")
    assert empty.min_stage_readiness_score == d("0.000000")
    assert empty.status == "pass"
    assert empty.reason_codes == ("lifecycle_report_empty",)
    assert empty.stage_rows == ()

    assert clear.event_count == d("1")
    assert clear.pass_count == d("1")
    assert clear.watch_count == d("0")
    assert clear.block_count == d("0")
    assert clear.status == "pass"
    assert clear.reason_codes == ("lifecycle_report_clear",)
    assert clear.stage_rows[0].next_research_actions == ("continue_stage_monitoring",)

    payload = api.research_event_lifecycle_stage_report_payload(clear)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["event_count"] == "1"
    assert payload["average_stage_readiness_score"] == "0.900000"
    assert payload["stage_rows"][0]["evidence_score"] == "0.920000"
    assert payload["derived_validation_digest"] == clear.derived_validation_digest
    _assert_no_public_numbers(payload)


def test_payload_digest_roundtrips_and_rejects_tampering_or_unsafe_surface():
    api = _api()
    report = _report((_observation(),))

    assert type(report.derived_validation_digest) is str
    assert len(report.derived_validation_digest) == 64
    assert int(report.derived_validation_digest, 16) >= 0
    assert _report((_observation(),)).derived_validation_digest == report.derived_validation_digest
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = api.research_event_lifecycle_stage_report_payload(report)
    assert api.research_event_lifecycle_stage_report_payload(payload) == payload

    with pytest.raises(ValueError, match="paper_only"):
        api.research_event_lifecycle_stage_report_payload({**payload, "paper_only": False})
    with pytest.raises(ValueError, match="Decimal-derived"):
        api.research_event_lifecycle_stage_report_payload({**payload, "event_count": 1})
    with pytest.raises(ValueError, match="Decimal-derived"):
        api.research_event_lifecycle_stage_report_payload(
            {**payload, "average_stage_readiness_score": 0.5},
        )
    with pytest.raises(ValueError, match="public readonly schema"):
        api.research_event_lifecycle_stage_report_payload(
            {**payload, "live_trading_enabled": "redacted"},
        )

    for unsafe_key in (
        "auth_token",
        "wallet_address",
        "order_id",
        "trade_mutation",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            api.research_event_lifecycle_stage_report_payload(
                {**payload, "stage_rows": [{**payload["stage_rows"][0], unsafe_key: "x"}]},
            )

    for unsafe_value in (
        "live-trading-event",
        "auth-event",
        "wallet-event",
        "order-event",
        "mutation-event",
    ):
        bad_row = {**payload["stage_rows"][0], "event_id": unsafe_value}
        with pytest.raises(ValueError, match="unsafe"):
            api.research_event_lifecycle_stage_report_payload(
                {**payload, "stage_rows": [bad_row]},
            )

    bad_digest = {**payload, "derived_validation_digest": "0" * 64}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.research_event_lifecycle_stage_report_payload(bad_digest)


def test_dataclasses_are_frozen_strict_decimal_utc_and_flag_guarded():
    api = _api()
    report = _report((_observation(),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.stage_rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        _config(minimum_evidence_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="Decimal"):
        _observation(evidence_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="datetime"):
        _observation(observed_at=_DatetimeSubclass(2026, 7, 7, 11, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        _observation(observed_at=datetime(2026, 7, 7, 11, 0))
    with pytest.raises(ValueError, match="UTC offset"):
        _observation(
            observed_at=datetime(
                2026,
                7,
                7,
                11,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report((_observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="bool"):
        _observation(settlement_rule_confirmed=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="lifecycle_stage"):
        _observation(lifecycle_stage="order_execution")
    with pytest.raises(ValueError, match="event_id"):
        _observation(event_id=" event-alpha ")


def test_module_public_api_does_not_expose_live_trading_or_order_mutation_surface():
    api = _api()
    source = inspect.getsource(api)
    tree = ast.parse(source)

    forbidden_imports = {
        "py_clob_client",
        "web3",
        "eth_account",
        "requests",
        "httpx",
        "subprocess",
        "socket",
    }
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    assigned_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr.lower())
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned_names.add(target.id.lower())

    assert forbidden_imports.isdisjoint(imported_roots)
    assert not any("wallet" in name for name in assigned_names)
    assert not any("auth" in name for name in assigned_names)
    assert not any("order" in name and name != "sorted" for name in called_names)
    assert not any("trade" in name for name in called_names)


def _assert_no_public_numbers(value: object) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"public payload contains raw number {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_numbers(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_public_numbers(item)
