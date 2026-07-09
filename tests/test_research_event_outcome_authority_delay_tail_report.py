from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "research-event-outcome-authority-delay-tail-report-v0"
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_outcome_authority_delay_tail_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    report = module()
    values = {
        "config_version": CONFIG_VERSION,
        "watch_authority_delay_seconds_threshold": d("86400.000000"),
        "block_authority_delay_seconds_threshold": d("604800.000000"),
        "watch_unresolved_tail_probability_threshold": d("0.050000"),
        "block_unresolved_tail_probability_threshold": d("0.150000"),
    }
    values.update(overrides)
    return report.ResearchEventOutcomeAuthorityDelayTailConfig(**values)


def event(
    event_reference: str,
    *,
    event_ended_at: datetime,
    authority_last_checked_at: datetime | None = None,
    outcome_authority_available: bool = False,
    unresolved_tail_probability: Decimal = d("0.180000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    report = module()
    return report.ResearchEventOutcomeAuthorityDelayTailInput(
        event_reference=event_reference,
        event_ended_at=event_ended_at,
        authority_last_checked_at=authority_last_checked_at or GENERATED_AT,
        outcome_authority_available=outcome_authority_available,
        unresolved_tail_probability=unresolved_tail_probability,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*events, cfg=None, generated_at: datetime = GENERATED_AT):
    report = module()
    return report.build_research_event_outcome_authority_delay_tail_report(
        events,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_delay_tail_report_blocks_and_watches_without_public_identifier_leakage() -> None:
    report = build_report(
        event(
            "candidate-alpha market_slug will-event-resolve https://source.example/?token=secret",
            event_ended_at=GENERATED_AT - timedelta(days=9),
            unresolved_tail_probability=d("0.180000"),
        ),
        event(
            "event-beta",
            event_ended_at=GENERATED_AT - timedelta(days=2),
            authority_last_checked_at=GENERATED_AT - timedelta(hours=12),
            outcome_authority_available=True,
            unresolved_tail_probability=d("0.070000"),
        ),
        event(
            "event-clear",
            event_ended_at=GENERATED_AT - timedelta(hours=2),
            authority_last_checked_at=GENERATED_AT - timedelta(hours=1),
            outcome_authority_available=True,
            unresolved_tail_probability=d("0.010000"),
        ),
        generated_at=datetime(2026, 7, 9, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert type(report) is module().ResearchEventOutcomeAuthorityDelayTailReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.event_count == d("3.000000")
    assert report.tail_event_count == d("2.000000")
    assert report.authority_missing_count == d("1.000000")
    assert report.authority_delay_watch_count == d("1.000000")
    assert report.authority_delay_block_count == d("1.000000")
    assert report.unresolved_tail_watch_count == d("1.000000")
    assert report.unresolved_tail_block_count == d("1.000000")
    assert report.max_authority_delay_seconds == d("777600.000000")
    assert report.max_unresolved_tail_probability == d("0.180000")
    assert report.status == "block"
    assert report.reason_codes == (
        "authority_missing_present",
        "authority_delay_watch_present",
        "authority_delay_block_present",
        "unresolved_tail_watch_present",
        "unresolved_tail_block_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, watched = report.tail_rows
    assert blocked == module().ResearchEventOutcomeAuthorityDelayTailRow(
        row_sequence=d("1.000000"),
        status="block",
        authority_delay_seconds=d("777600.000000"),
        unresolved_tail_probability=d("0.180000"),
        authority_available=False,
        authority_missing=True,
        authority_delay_watch=False,
        authority_delay_block=True,
        unresolved_tail_watch=False,
        unresolved_tail_block=True,
        flag_count=d("3.000000"),
        reason_codes=(
            "authority_missing",
            "authority_delay_block",
            "unresolved_tail_block",
        ),
    )
    assert watched.status == "watch"
    assert watched.row_sequence == d("2.000000")
    assert watched.authority_delay_seconds == d("129600.000000")
    assert watched.unresolved_tail_probability == d("0.070000")
    assert watched.authority_available is True
    assert watched.reason_codes == (
        "authority_delay_watch",
        "unresolved_tail_watch",
    )

    payload = module().research_event_outcome_authority_delay_tail_payload(report)
    encoded = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "candidate-alpha",
        "market_slug",
        "will-event-resolve",
        "https://source.example",
        "token",
        "secret",
        "event-beta",
        "event-clear",
    ):
        assert forbidden not in encoded
    assert payload["tail_rows"][0]["row_sequence"] == "1.000000"
    assert payload["tail_rows"][0]["authority_delay_seconds"] == "777600.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert not _contains_float(payload)


def test_empty_and_clear_reports_are_pass_report_only_and_json_ready() -> None:
    empty = build_report()
    clear = build_report(
        event(
            "private-clear-ref",
            event_ended_at=GENERATED_AT - timedelta(hours=2),
            authority_last_checked_at=GENERATED_AT - timedelta(hours=1),
            outcome_authority_available=True,
            unresolved_tail_probability=d("0.010000"),
        ),
    )

    assert empty.event_count == ZERO
    assert empty.tail_event_count == ZERO
    assert empty.status == "pass"
    assert empty.reason_codes == ("event_outcome_authority_delay_tail_empty",)
    assert empty.tail_rows == ()

    assert clear.event_count == d("1.000000")
    assert clear.tail_event_count == ZERO
    assert clear.status == "pass"
    assert clear.reason_codes == ("event_outcome_authority_delay_tail_clear",)
    assert clear.tail_rows == ()

    payload = module().research_event_outcome_authority_delay_tail_payload(clear)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["event_count"] == "1.000000"
    assert payload["tail_rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)


def test_digest_payload_rejects_tampering_and_flag_downgrades() -> None:
    report = build_report(
        event("private-blocked-ref", event_ended_at=GENERATED_AT - timedelta(days=8)),
    )
    payload = module().research_event_outcome_authority_delay_tail_payload(report)

    assert type(report.derived_validation_digest) is str
    assert len(report.derived_validation_digest) == 64
    assert int(report.derived_validation_digest, 16) >= 0
    assert build_report(
        event("private-blocked-ref", event_ended_at=GENERATED_AT - timedelta(days=8)),
    ).derived_validation_digest == report.derived_validation_digest
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_count = dict(payload)
    tampered_count["tail_event_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module().research_event_outcome_authority_delay_tail_payload(tampered_count)

    tampered_digest = dict(payload)
    tampered_digest["derived_validation_digest"] = "not-the-derived-digest"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module().research_event_outcome_authority_delay_tail_payload(tampered_digest)

    downgraded = dict(payload)
    downgraded["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        module().research_event_outcome_authority_delay_tail_payload(downgraded)


def test_frozen_dataclasses_decimal_only_utc_and_hard_flag_guards() -> None:
    api = module()
    report = build_report(
        event("private-blocked-ref", event_ended_at=GENERATED_AT - timedelta(days=8)),
    )

    assert is_dataclass(api.ResearchEventOutcomeAuthorityDelayTailConfig)
    assert is_dataclass(api.ResearchEventOutcomeAuthorityDelayTailInput)
    assert is_dataclass(api.ResearchEventOutcomeAuthorityDelayTailRow)
    assert is_dataclass(api.ResearchEventOutcomeAuthorityDelayTailReport)
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.tail_rows[0].status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        event("private-ref", event_ended_at=GENERATED_AT, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="Decimal"):
        config(watch_authority_delay_seconds_threshold=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="unresolved_tail_probability"):
        event(
            "private-ref",
            event_ended_at=GENERATED_AT,
            unresolved_tail_probability=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        event("private-ref", event_ended_at=datetime(2026, 7, 9, 11, 0))
    with pytest.raises(ValueError, match="UTC offset"):
        event(
            "private-ref",
            event_ended_at=datetime(2026, 7, 9, 11, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_report(generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="outcome_authority_available"):
        event(
            "private-ref",
            event_ended_at=GENERATED_AT,
            outcome_authority_available=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="config"):
        api.build_research_event_outcome_authority_delay_tail_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    for item in (report, *report.tail_rows):
        for field_name, value in item.__dict__.items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field_name
            assert type(value) is not float, field_name


def test_rejects_duplicates_future_inputs_inconsistent_counts_and_bad_status() -> None:
    report = build_report(
        event("private-a", event_ended_at=GENERATED_AT - timedelta(days=8)),
        event(
            "private-b",
            event_ended_at=GENERATED_AT - timedelta(days=2),
            outcome_authority_available=True,
            unresolved_tail_probability=d("0.070000"),
        ),
    )

    with pytest.raises(ValueError, match="duplicate event_reference"):
        build_report(
            event("private-dup", event_ended_at=GENERATED_AT),
            event("private-dup", event_ended_at=GENERATED_AT),
        )
    with pytest.raises(ValueError, match="event_ended_at"):
        build_report(event("future-ref", event_ended_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="authority_last_checked_at"):
        build_report(
            event(
                "future-check-ref",
                event_ended_at=GENERATED_AT,
                authority_last_checked_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="tail_event_count"):
        replace(report, tail_event_count=d("3.000000"))
    with pytest.raises(ValueError, match="tail_rows"):
        replace(report, tail_rows=tuple(reversed(report.tail_rows)))
    with pytest.raises(ValueError, match="status"):
        replace(report.tail_rows[0], status="hold")


def test_public_payload_schema_rejects_unsafe_surfaces_and_identifier_fields() -> None:
    api = module()
    report = build_report(
        event("private-blocked-ref", event_ended_at=GENERATED_AT - timedelta(days=8)),
    )
    payload = api.research_event_outcome_authority_delay_tail_payload(report)

    for unsafe_key in (
        "candidate_id",
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet_address",
        "order_id",
        "trade_id",
        "sizing",
        "live_trading",
        "network_endpoint",
    ):
        with pytest.raises(ValueError, match="unsafe|schema"):
            api.research_event_outcome_authority_delay_tail_payload(
                {**payload, unsafe_key: "blocked"},
            )

    for unsafe_value in (
        "candidate_id=cnd_123",
        "market_slug=will-resolve",
        "question=Will this happen?",
        "source_url=https://example.com",
        "source_text=raw evidence",
        "postgres://dsn",
        "wallet 0xabc",
        "order 123",
        "trade 123",
        "live trading enabled",
        "network endpoint",
        "position sizing",
    ):
        bad_row = {**payload["tail_rows"][0], "reason_codes": [unsafe_value]}
        with pytest.raises(ValueError, match="unsafe|known"):
            api.research_event_outcome_authority_delay_tail_payload(
                {**payload, "tail_rows": [bad_row]},
            )


def test_static_module_surface_is_independent_decimal_only_and_report_only() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_event_outcome_authority_delay_tail_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests.",
        "urllib",
        "sqlite",
        "psycopg",
        "subprocess",
        "socket",
        "open(",
        "read_text",
        "write_text",
        "private_key",
        "api_key",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name is not None:
                called_names.add(call_name.rsplit(".", maxsplit=1)[-1])

    assert imported_modules == {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    assert {
        "connect",
        "execute",
        "executemany",
        "float",
        "open",
        "print",
        "request",
        "send",
    }.isdisjoint(called_names)
    assert not re.search(r"\b(requests|urllib|sqlite|psycopg|socket)\b", lowered)

    sample_report = build_report(
        event("private-blocked-ref", event_ended_at=GENERATED_AT - timedelta(days=8)),
    )
    public_field_names = {
        *(field.name for field in fields(sample_report)),
        *(field.name for field in fields(sample_report.tail_rows[0])),
    }
    for forbidden_public_field in (
        "candidate_id",
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
    ):
        assert forbidden_public_field not in public_field_names


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None
