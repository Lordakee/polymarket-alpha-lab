from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
MODULE_NAME = (
    "polymarket_alpha_lab.research_event_resolution_conflict_recheck_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_resolution_conflict_recheck_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


@dataclass(frozen=True)
class SuppliedConflictShape:
    public_case_key: str
    aggregate_contradiction_pressure: Decimal
    evidence_age_seconds: Decimal
    source_reliability_score: Decimal
    deadline_proximity: Decimal
    oracle_lag_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "fresh_evidence_age_seconds": d("3600"),
        "stale_evidence_age_seconds": d("86400"),
        "oracle_watch_lag_seconds": d("1800"),
        "oracle_block_lag_seconds": d("14400"),
        "watch_recheck_pressure_threshold": d("0.350000"),
        "block_recheck_pressure_threshold": d("0.700000"),
        "aggregate_contradiction_weight": d("0.300000"),
        "evidence_age_weight": d("0.200000"),
        "source_reliability_weight": d("0.200000"),
        "deadline_proximity_weight": d("0.150000"),
        "oracle_lag_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchEventResolutionConflictRecheckConfig(**values)


def conflict_item(
    public_case_key: str = "case-a",
    *,
    aggregate_contradiction_pressure: Decimal = d("0.050000"),
    evidence_age_seconds: Decimal = d("1800"),
    source_reliability_score: Decimal = d("0.950000"),
    deadline_proximity: Decimal = d("0.100000"),
    oracle_lag_seconds: Decimal = d("600"),
    reason_codes: tuple[str, ...] = (),
) -> Any:
    module = api()
    return module.ResearchEventResolutionConflictRecheckInput(
        public_case_key=public_case_key,
        aggregate_contradiction_pressure=aggregate_contradiction_pressure,
        evidence_age_seconds=evidence_age_seconds,
        source_reliability_score=source_reliability_score,
        deadline_proximity=deadline_proximity,
        oracle_lag_seconds=oracle_lag_seconds,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_event_resolution_conflict_recheck_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_public_safe_pass_report_with_digest() -> None:
    module = api()
    conflict_report = report(())

    assert module.STATUSES == ("pass", "watch", "block")
    assert type(conflict_report) is module.ResearchEventResolutionConflictRecheckReport
    assert conflict_report.generated_at == GENERATED_AT
    assert conflict_report.case_count == d("0")
    assert conflict_report.pass_count == d("0")
    assert conflict_report.watch_count == d("0")
    assert conflict_report.block_count == d("0")
    assert conflict_report.average_conflict_recheck_pressure is None
    assert conflict_report.max_conflict_recheck_pressure == d("0.000000")
    assert conflict_report.max_evidence_age_seconds == d("0.000000")
    assert conflict_report.max_oracle_lag_seconds == d("0.000000")
    assert conflict_report.status == "pass"
    assert conflict_report.reason_codes == ("no_resolution_conflict_recheck_items",)
    assert conflict_report.reason_code_counts == (
        module.ResearchEventResolutionConflictRecheckReasonCodeCount(
            reason_code="no_resolution_conflict_recheck_items",
            count=d("1.000000"),
        ),
    )
    assert conflict_report.rows == ()
    assert len(conflict_report.derived_validation_digest) == 64
    assert conflict_report.paper_only is True
    assert conflict_report.report_only is True
    assert conflict_report.readonly is True

    payload = module.research_event_resolution_conflict_recheck_report_payload(
        conflict_report,
    )
    assert payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert payload["case_count"] == "0.000000"
    assert payload["derived_validation_digest"] == (
        conflict_report.derived_validation_digest
    )
    assert module.validate_research_event_resolution_conflict_recheck_public_payload(
        payload,
    )
    assert_no_numeric_payload(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_conflict_recheck_queue_uses_all_pressure_inputs() -> None:
    module = api()
    conflict_report = report(
        (
            conflict_item(
                "case-block",
                aggregate_contradiction_pressure=d("0.800000"),
                evidence_age_seconds=d("172800"),
                source_reliability_score=d("0.300000"),
                deadline_proximity=d("0.900000"),
                oracle_lag_seconds=d("28800"),
                reason_codes=("public_dispute_review",),
            ),
            conflict_item("case-pass"),
            conflict_item(
                "case-watch",
                aggregate_contradiction_pressure=d("0.350000"),
                evidence_age_seconds=d("45000"),
                source_reliability_score=d("0.700000"),
                deadline_proximity=d("0.400000"),
                oracle_lag_seconds=d("7200"),
            ),
        ),
    )

    assert conflict_report.status == "block"
    assert conflict_report.case_count == d("3.000000")
    assert conflict_report.pass_count == d("1.000000")
    assert conflict_report.watch_count == d("1.000000")
    assert conflict_report.block_count == d("1.000000")
    assert conflict_report.average_conflict_recheck_pressure == d("0.437083")
    assert conflict_report.max_conflict_recheck_pressure == d("0.865000")
    assert conflict_report.max_evidence_age_seconds == d("172800.000000")
    assert conflict_report.max_oracle_lag_seconds == d("28800.000000")

    assert tuple(row.public_case_key for row in conflict_report.rows) == (
        "case-block",
        "case-watch",
        "case-pass",
    )
    block_row, watch_row, pass_row = conflict_report.rows
    assert type(block_row) is module.ResearchEventResolutionConflictRecheckRow
    assert block_row.evidence_age_pressure == d("1.000000")
    assert block_row.source_reliability_gap == d("0.700000")
    assert block_row.oracle_lag_pressure == d("1.000000")
    assert block_row.conflict_recheck_pressure == d("0.865000")
    assert block_row.status == "block"
    assert "input_public_dispute_review" in block_row.reason_codes

    assert watch_row.evidence_age_pressure == d("0.500000")
    assert watch_row.source_reliability_gap == d("0.300000")
    assert watch_row.oracle_lag_pressure == d("0.500000")
    assert watch_row.conflict_recheck_pressure == d("0.400000")
    assert watch_row.status == "watch"

    assert pass_row.evidence_age_pressure == d("0.000000")
    assert pass_row.source_reliability_gap == d("0.050000")
    assert pass_row.oracle_lag_pressure == d("0.041667")
    assert pass_row.conflict_recheck_pressure == d("0.046250")
    assert pass_row.status == "pass"
    assert conflict_report.reason_code_counts == tuple(
        sorted(conflict_report.reason_code_counts, key=lambda item: item.reason_code),
    )


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_strings() -> None:
    module = api()
    rows = (
        SuppliedConflictShape(
            public_case_key="case-b",
            aggregate_contradiction_pressure=d("0.350000"),
            evidence_age_seconds=d("45000"),
            source_reliability_score=d("0.700000"),
            deadline_proximity=d("0.400000"),
            oracle_lag_seconds=d("7200"),
            reason_codes=("manual_public_recheck",),
        ),
        conflict_item("case-a"),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = module.research_event_resolution_conflict_recheck_report_payload(
        first_report,
    )
    second_payload = module.research_event_resolution_conflict_recheck_report_payload(
        second_report,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["rows"][0]["public_case_key"] == "case-b"
    assert first_payload["rows"][0]["conflict_recheck_pressure"] == "0.400000"
    assert first_payload["rows"][1]["oracle_lag_seconds"] == "600.000000"
    assert_no_numeric_payload(first_payload)
    assert_no_forbidden_payload_language(first_payload)
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "event_id",
            "market_id",
            "market_slug",
            "condition_id",
            "source_id",
            "source_url",
            "source_text",
            "source_ref",
            "raw_event",
            "raw_market",
            "raw_source",
            "wallet",
            "auth",
            "order",
            "trade",
            "recommendation",
            "position",
            "sizing",
        )
    )


def test_dataclasses_are_frozen_decimal_only_flagged_and_digest_bound() -> None:
    module = api()

    for klass in (
        module.ResearchEventResolutionConflictRecheckConfig,
        module.ResearchEventResolutionConflictRecheckInput,
        module.ResearchEventResolutionConflictRecheckReasonCodeCount,
        module.ResearchEventResolutionConflictRecheckRow,
        module.ResearchEventResolutionConflictRecheckReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(ValueError, match="fresh_evidence_age_seconds"):
        config(fresh_evidence_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="oracle_lag_weight"):
        config(oracle_lag_weight=_DecimalSubclass("0.150000"))
    with pytest.raises(ValueError, match="aggregate_contradiction_weight"):
        config(aggregate_contradiction_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_recheck_pressure_threshold"):
        config(block_recheck_pressure_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="oracle_watch_lag_seconds"):
        config(oracle_watch_lag_seconds=d("20000"))
    with pytest.raises(ValueError, match="aggregate_contradiction_pressure"):
        conflict_item(aggregate_contradiction_pressure=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_reliability_score"):
        conflict_item(source_reliability_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="deadline_proximity"):
        conflict_item(deadline_proximity=d("1.100000"))
    with pytest.raises(ValueError, match="oracle_lag_seconds"):
        conflict_item(oracle_lag_seconds=d("-1"))
    with pytest.raises(ValueError, match="public_case_key"):
        conflict_item(public_case_key="event-alpha")
    with pytest.raises(ValueError, match="public_case_key"):
        conflict_item(public_case_key="source-alpha")
    with pytest.raises(ValueError, match="reason_codes"):
        conflict_item(reason_codes=("Needs Review",))

    item = conflict_item()
    with pytest.raises(FrozenInstanceError):
        item.public_case_key = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)

    good_report = report((item,))
    with pytest.raises(FrozenInstanceError):
        good_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        good_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):
        type("BadConfig", (module.ResearchEventResolutionConflictRecheckConfig,), {})
    with pytest.raises(ValueError, match="readonly"):
        replace(good_report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(good_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="case_count"):
        replace(good_report, case_count=d("2.000000"))

    for value in (
        item,
        good_report.rows[0],
        good_report.reason_code_counts[0],
        good_report,
    ):
        for field in fields(value):
            field_value = getattr(value, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal


def test_timezone_payload_validation_and_unsafe_surfaces_are_rejected() -> None:
    module = api()

    timezone_report = report(
        (conflict_item("case-timezone"),),
        generated_at=datetime(2026, 7, 8, 14, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    assert timezone_report.generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_resolution_conflict_recheck_report(
            (conflict_item(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 18, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_resolution_conflict_recheck_report(
            (conflict_item(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 18, 0, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_research_event_resolution_conflict_recheck_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report((conflict_item("case-dup"), conflict_item("case-dup")))

    payload = module.research_event_resolution_conflict_recheck_report_payload(
        report((conflict_item("case-payload"),)),
    )
    assert module.validate_research_event_resolution_conflict_recheck_public_payload(
        payload,
    )
    with pytest.raises(ValueError, match="Decimal strings"):
        module.validate_research_event_resolution_conflict_recheck_public_payload(
            {**payload, "case_count": 1},
        )
    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_resolution_conflict_recheck_public_payload(
            missing_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_resolution_conflict_recheck_public_payload(
            {**payload, "case_count": "9.000000"},
        )

    for forbidden_key in (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "source_identifier",
        "wallet_address",
        "auth_token",
        "order_id",
        "trade_intent",
        "live_execution",
        "stake_size",
        "recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe|raw identifier|action language"):
            module.validate_research_event_resolution_conflict_recheck_public_payload(
                {**payload, forbidden_key: "not allowed"},
            )

    tampered = report((conflict_item("case-tampered"),))
    object.__setattr__(tampered, "case_count", d("9.000000"))
    with pytest.raises(ValueError, match="case_count|derived_validation_digest"):
        module.research_event_resolution_conflict_recheck_report_payload(tampered)


def test_module_scope_is_report_only_readonly_and_external_io_free() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source_text.lower()
    for forbidden in (
        "wallet",
        "auth",
        "account",
        "broker",
        "database",
        "payload_json",
        "open(",
        "requests",
        "network",
        "submit",
        "persist",
        "recommend",
        "sizing",
        "position_size",
        "allocation",
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "raw_event",
        "raw_market",
        "raw_source",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

    forbidden_import_fragments = (
        "db",
        "env",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_numeric_payload(value: Any) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int | float | Decimal):
        raise AssertionError(f"numeric payload value leaked: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_payload(item)
    if isinstance(value, list | tuple):
        for item in value:
            assert_no_numeric_payload(item)


def assert_no_forbidden_payload_language(payload: dict[str, Any]) -> None:
    payload_text = repr(payload).lower()
    for forbidden in (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "source_identifier",
        "wallet",
        "auth",
        "order",
        "trade",
        "live_execution",
        "recommend",
        "position",
        "sizing",
    ):
        assert forbidden not in payload_text
