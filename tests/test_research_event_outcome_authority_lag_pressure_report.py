from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_event_outcome_authority_lag_pressure_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_outcome_authority_lag_pressure_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


def api() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, f"{MODULE_NAME} should exist"
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


def lag_input(
    label: str,
    *,
    observed_age_seconds: int = 3600,
    authority_lag_seconds: int | None = 900,
    authority_check_age_seconds: int = 600,
    authority_evidence_count: str | Decimal = "2",
    required_authority_evidence_count: str | Decimal = "2",
    contradiction_pressure: str | Decimal = "0.050000",
) -> Any:
    module = api()
    outcome_observed_at = GENERATED_AT - timedelta(seconds=observed_age_seconds)
    return module.ResearchEventOutcomeAuthorityLagPressureReportInput(
        event_private_label=label,
        outcome_observed_at=outcome_observed_at,
        authority_confirmed_at=(
            None
            if authority_lag_seconds is None
            else outcome_observed_at + timedelta(seconds=authority_lag_seconds)
        ),
        authority_checked_at=GENERATED_AT - timedelta(
            seconds=authority_check_age_seconds,
        ),
        authority_evidence_count=(
            d(authority_evidence_count)
            if type(authority_evidence_count) is str
            else authority_evidence_count
        ),
        required_authority_evidence_count=(
            d(required_authority_evidence_count)
            if type(required_authority_evidence_count) is str
            else required_authority_evidence_count
        ),
        contradiction_pressure=(
            d(contradiction_pressure)
            if type(contradiction_pressure) is str
            else contradiction_pressure
        ),
    )


def build_report(*items: Any, config: Any | None = None) -> Any:
    module = api()
    return module.build_research_event_outcome_authority_lag_pressure_report(
        items,
        generated_at=GENERATED_AT,
        config=config
        or module.ResearchEventOutcomeAuthorityLagPressureReportConfig(),
    )


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert all(character in "0123456789abcdef" for character in value)


def assert_no_public_numeric_scalars(value: object) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if isinstance(value, (Decimal, int, float)):
        raise AssertionError(f"public payload contains numeric scalar: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numeric_scalars(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_public_numeric_scalars(item)
        return
    raise AssertionError(f"unexpected public payload value: {value!r}")


def test_lag_pressure_report_aggregates_pass_watch_and_block_events() -> None:
    report = build_report(
        lag_input("charlie-pass"),
        lag_input(
            "alpha-block",
            observed_age_seconds=36000,
            authority_lag_seconds=None,
            authority_check_age_seconds=18000,
            authority_evidence_count="0",
            contradiction_pressure="0.800000",
        ),
        lag_input(
            "bravo-watch",
            observed_age_seconds=7200,
            authority_lag_seconds=7200,
            authority_check_age_seconds=3600,
            authority_evidence_count="1",
            contradiction_pressure="0.200000",
        ),
    )

    assert is_dataclass(report)
    assert report.status == "block"
    assert report.event_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.max_authority_lag_seconds == d("36000.000000")
    assert report.max_authority_check_age_seconds == d("18000.000000")
    assert report.min_authority_quorum_score == d("0.000000")
    assert report.max_contradiction_pressure == d("0.800000")
    assert report.average_lag_pressure_score == d("0.482847")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    block_row, watch_row, pass_row = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert block_row.event_public_label == "event-001"
    assert watch_row.event_public_label == "event-002"
    assert pass_row.event_public_label == "event-003"

    assert block_row.authority_confirmed_at is None
    assert block_row.authority_lag_seconds == d("36000.000000")
    assert block_row.authority_check_age_seconds == d("18000.000000")
    assert block_row.authority_lag_pressure == d("1.000000")
    assert block_row.authority_check_staleness_pressure == d("1.000000")
    assert block_row.authority_quorum_score == d("0.000000")
    assert block_row.authority_quorum_gap_pressure == d("1.000000")
    assert block_row.lag_pressure_score == d("0.960000")
    assert block_row.reason_codes == (
        "authority_confirmation_missing",
        "authority_lag_block",
        "authority_check_staleness_block",
        "authority_quorum_block",
        "contradiction_pressure_block",
        "outcome_authority_lag_pressure_block",
    )

    assert watch_row.authority_lag_pressure == d("0.500000")
    assert watch_row.authority_check_staleness_pressure == d("0.500000")
    assert watch_row.authority_quorum_score == d("0.500000")
    assert watch_row.lag_pressure_score == d("0.440000")
    assert watch_row.reason_codes == (
        "authority_lag_watch",
        "authority_check_staleness_watch",
        "authority_quorum_watch",
        "contradiction_pressure_watch",
        "outcome_authority_lag_pressure_watch",
    )

    assert pass_row.authority_lag_pressure == d("0.062500")
    assert pass_row.authority_check_staleness_pressure == d("0.083333")
    assert pass_row.authority_quorum_score == d("1.000000")
    assert pass_row.lag_pressure_score == d("0.048542")
    assert pass_row.reason_codes == ("outcome_authority_lag_pressure_pass",)


def test_empty_report_blocks_without_live_or_mutating_surfaces() -> None:
    module = api()
    report = build_report()

    assert report.status == "block"
    assert report.reason_codes == (
        "outcome_authority_lag_pressure_empty",
        "outcome_authority_lag_pressure_block",
    )
    assert report.event_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.rows == ()
    assert report.average_lag_pressure_score == d("1.000000")

    payload = module.research_event_outcome_authority_lag_pressure_report_public_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)
    assert payload["status"] == "block"
    assert payload["event_count"] == "0"
    assert payload["average_lag_pressure_score"] == "1.000000"
    assert payload["public_digest"] == report.public_digest
    assert_no_public_numeric_scalars(payload)


def test_public_payload_is_deterministic_digest_backed_and_redacted() -> None:
    module = api()
    raw_private_label = (
        "candidate-market-id-slug-question-source-url-source-text-dsn-table-token-"
        "wallet-order-trade"
    )
    first = build_report(
        lag_input("charlie-pass"),
        lag_input(raw_private_label, authority_lag_seconds=None),
        lag_input("bravo-watch", observed_age_seconds=7200, authority_lag_seconds=7200),
    )
    second = build_report(
        lag_input("bravo-watch", observed_age_seconds=7200, authority_lag_seconds=7200),
        lag_input("charlie-pass"),
        lag_input(raw_private_label, authority_lag_seconds=None),
    )

    first_payload = (
        module.research_event_outcome_authority_lag_pressure_report_public_payload(first)
    )
    second_payload = (
        module.research_event_outcome_authority_lag_pressure_report_public_payload(second)
    )
    encoded_payload = json.dumps(first_payload, sort_keys=True)

    assert first.public_digest == second.public_digest
    assert first_payload == second_payload
    assert first_payload["public_digest"] == first.public_digest
    assert module.research_event_outcome_authority_lag_pressure_report_public_digest(
        first,
    ) == first.public_digest
    assert_sha256(first.public_digest)
    assert_no_public_numeric_scalars(first_payload)
    assert raw_private_label not in encoded_payload
    assert not _unsafe_public_fragments(first_payload)

    tampered_payload = dict(first_payload)
    tampered_payload["event_count"] = "9"
    with pytest.raises(ValueError, match="public_digest"):
        module.validate_research_event_outcome_authority_lag_pressure_public_payload(
            tampered_payload,
        )

    unsafe_payload = dict(first_payload)
    unsafe_payload["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_research_event_outcome_authority_lag_pressure_public_payload(
            unsafe_payload,
        )


def test_validation_rejects_invalid_inputs_thresholds_flags_and_digest_tampering() -> None:
    module = api()

    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_outcome_authority_lag_pressure_report(
            (),
            generated_at=datetime(2026, 7, 9, 12, 0),
            config=module.ResearchEventOutcomeAuthorityLagPressureReportConfig(),
        )
    with pytest.raises(ValueError, match="outcome_observed_at must be timezone-aware"):
        lag_input("bad-time", observed_age_seconds=0). __class__(
            event_private_label="bad-time",
            outcome_observed_at=datetime(2026, 7, 9, 12, 0, tzinfo=NoneOffsetTimezone()),
            authority_confirmed_at=None,
            authority_checked_at=GENERATED_AT,
            authority_evidence_count=d("1"),
            required_authority_evidence_count=d("1"),
            contradiction_pressure=d("0"),
        )
    with pytest.raises(ValueError, match="outcome_observed_at must be a datetime"):
        module.ResearchEventOutcomeAuthorityLagPressureReportInput(
            event_private_label="bad-subclass",
            outcome_observed_at=DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
            authority_confirmed_at=None,
            authority_checked_at=GENERATED_AT,
            authority_evidence_count=d("1"),
            required_authority_evidence_count=d("1"),
            contradiction_pressure=d("0"),
        )
    with pytest.raises(ValueError, match="authority_confirmed_at"):
        module.ResearchEventOutcomeAuthorityLagPressureReportInput(
            event_private_label="bad-confirmed",
            outcome_observed_at=GENERATED_AT,
            authority_confirmed_at=GENERATED_AT - timedelta(seconds=1),
            authority_checked_at=GENERATED_AT,
            authority_evidence_count=d("1"),
            required_authority_evidence_count=d("1"),
            contradiction_pressure=d("0"),
        )
    with pytest.raises(ValueError, match="authority_evidence_count must be a Decimal"):
        lag_input("bad-decimal", authority_evidence_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_pressure must be an exact Decimal"):
        lag_input("bad-decimal-subclass", contradiction_pressure=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="authority_evidence_count"):
        lag_input(
            "bad-counts",
            authority_evidence_count=d("3"),
            required_authority_evidence_count=d("2"),
        )
    with pytest.raises(ValueError, match="pressure weights"):
        module.ResearchEventOutcomeAuthorityLagPressureReportConfig(
            contradiction_pressure_weight=d("0.300000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            module.ResearchEventOutcomeAuthorityLagPressureReportConfig(),
            paper_only=False,
        )

    report = build_report(lag_input("stable"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="public_digest"):
        replace(report, public_digest="0" * 64)


def test_public_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    report = build_report(lag_input("stable"))

    for klass in (
        module.ResearchEventOutcomeAuthorityLagPressureReportConfig,
        module.ResearchEventOutcomeAuthorityLagPressureReportInput,
        module.ResearchEventOutcomeAuthorityLagPressureReportRow,
        module.ResearchEventOutcomeAuthorityLagPressureReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "pass"  # type: ignore[misc]

    for value in (report, *report.rows):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                assert item_value is True
            elif item.name.endswith(("count", "seconds", "score", "pressure")):
                assert type(item_value) is Decimal

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(module.ResearchEventOutcomeAuthorityLagPressureReportConfig):
            pass


def test_static_module_has_no_io_network_wallet_order_trade_or_sizing_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "requests",
        "httpx",
        "socket",
        "psycopg",
        "sqlite",
        "open(",
        "database",
        "private_key",
        "wallet",
        "order",
        "trade",
        "recommendation",
        "sizing",
        "submit_",
        "cancel_",
        "live trading",
    )

    assert not [term for term in forbidden_terms if term in lowered]

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def _unsafe_public_fragments(value: object) -> tuple[str, ...]:
    fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = key.lower()
            findings.extend(fragment for fragment in fragments if fragment in normalized_key)
            findings.extend(_unsafe_public_fragments(item))
    elif isinstance(value, list):
        for item in value:
            findings.extend(_unsafe_public_fragments(item))
    elif type(value) is str:
        normalized_value = value.lower()
        findings.extend(fragment for fragment in fragments if fragment in normalized_value)
    return tuple(findings)
