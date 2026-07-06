from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.market_outcome_source_recheck_status_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_outcome_source_recheck_status_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "market-outcome-source-recheck-status-test-v0",
        "due_grace_seconds": d("0.000000"),
        "stale_ack_seconds": d("3600.000000"),
        "stale_evidence_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return module.MarketOutcomeSourceRecheckStatusConfig(**values)


def observation(
    market_slug: str,
    *,
    condition_id: str | None = None,
    source_id: str | None = None,
    source_family: str = "official",
    next_recheck_due_at: datetime = GENERATED_AT + timedelta(minutes=30),
    last_acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=10),
    last_evidence_checked_at: datetime | None = GENERATED_AT - timedelta(minutes=5),
    open_gap_count: Decimal = d("0.000000"),
    conflict_count: Decimal = d("0.000000"),
    blocked: bool = False,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    suffix = market_slug.removeprefix("market-")
    return module.MarketOutcomeSourceRecheckObservation(
        market_slug=market_slug,
        condition_id=condition_id or f"condition-{suffix}",
        source_id=source_id or f"source-{suffix}",
        source_family=source_family,
        next_recheck_due_at=next_recheck_due_at,
        last_acknowledged_at=last_acknowledged_at,
        last_evidence_checked_at=last_evidence_checked_at,
        open_gap_count=open_gap_count,
        conflict_count=conflict_count,
        blocked=blocked,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*values: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_market_outcome_source_recheck_status_report(
        values,
        config=config() if cfg is None else cfg,
        generated_at=GENERATED_AT,
    )


def assert_no_public_float_or_int(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_float_or_int(item)


def test_empty_report_is_readonly_decimal_digest_bound_and_json_safe() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.MarketOutcomeSourceRecheckStatusReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.generated_at == GENERATED_AT
    assert report.report_status == "cleared"
    assert report.row_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.overdue_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.cleared_count == d("0.000000")
    assert report.attention_count == d("0.000000")
    assert report.open_gap_count == d("0.000000")
    assert report.conflict_count == d("0.000000")
    assert report.stale_ack_count == d("0.000000")
    assert report.stale_evidence_count == d("0.000000")
    assert report.attention_ratio == d("0.000000")
    assert report.oldest_due_age_seconds is None
    assert report.rows == ()
    assert report.reason_codes == ("market_outcome_source_recheck_cleared",)
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.market_outcome_source_recheck_status_report_payload(report)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["attention_ratio"] == "0.000000"
    assert payload["rows"] == []
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert_no_public_float_or_int(payload)
    json.dumps(payload, sort_keys=True)


def test_status_rollup_reason_codes_sorting_and_digest_are_deterministic() -> None:
    report = build_report(
        observation(
            "market-cleared",
            source_family="official",
            next_recheck_due_at=GENERATED_AT + timedelta(minutes=15),
        ),
        observation(
            "market-watch",
            source_family="backup",
            next_recheck_due_at=GENERATED_AT + timedelta(minutes=10),
            last_acknowledged_at=GENERATED_AT - timedelta(hours=2),
            last_evidence_checked_at=GENERATED_AT - timedelta(hours=3),
        ),
        observation(
            "market-overdue",
            source_family="official",
            next_recheck_due_at=GENERATED_AT - timedelta(minutes=30),
            open_gap_count=d("1.000000"),
        ),
        observation(
            "market-blocked",
            source_family="official",
            next_recheck_due_at=GENERATED_AT - timedelta(hours=1),
            last_acknowledged_at=None,
            last_evidence_checked_at=None,
            open_gap_count=d("2.000000"),
            conflict_count=d("1.000000"),
            blocked=True,
        ),
    )

    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "market_outcome_source_recheck_blocked",
        "market_outcome_source_recheck_conflict",
        "market_outcome_source_recheck_open_gap",
        "market_outcome_source_recheck_overdue",
        "market_outcome_source_recheck_stale_ack",
        "market_outcome_source_recheck_stale_evidence",
    )
    assert report.row_count == d("4.000000")
    assert report.blocked_count == d("1.000000")
    assert report.overdue_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.cleared_count == d("1.000000")
    assert report.attention_count == d("3.000000")
    assert report.open_gap_count == d("3.000000")
    assert report.conflict_count == d("1.000000")
    assert report.stale_ack_count == d("2.000000")
    assert report.stale_evidence_count == d("2.000000")
    assert report.attention_ratio == d("0.750000")
    assert report.oldest_due_age_seconds == d("3600.000000")

    assert tuple(row.market_slug for row in report.rows) == (
        "market-blocked",
        "market-overdue",
        "market-watch",
        "market-cleared",
    )
    assert tuple(row.recheck_status for row in report.rows) == (
        "blocked",
        "overdue",
        "watch",
        "cleared",
    )
    assert report.rows[0].reason_codes == (
        "market_outcome_source_recheck_blocked",
        "market_outcome_source_recheck_conflict",
        "market_outcome_source_recheck_open_gap",
        "market_outcome_source_recheck_overdue",
        "market_outcome_source_recheck_stale_ack",
        "market_outcome_source_recheck_stale_evidence",
    )
    assert report.rows[1].reason_codes == (
        "market_outcome_source_recheck_open_gap",
        "market_outcome_source_recheck_overdue",
    )
    assert report.rows[2].reason_codes == (
        "market_outcome_source_recheck_stale_ack",
        "market_outcome_source_recheck_stale_evidence",
    )
    assert report.rows[3].reason_codes == ("market_outcome_source_recheck_cleared",)
    assert len({row.derived_validation_digest for row in report.rows}) == 4


def test_public_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    module = api()
    report = build_report(observation("market-decimal"))

    public_classes = (
        module.MarketOutcomeSourceRecheckStatusConfig,
        module.MarketOutcomeSourceRecheckObservation,
        module.MarketOutcomeSourceRecheckStatusRow,
        module.MarketOutcomeSourceRecheckStatusReport,
    )
    for klass in public_classes:
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        observation("market-flag", paper_only=False)
    with pytest.raises(TypeError, match="subclassing"):
        type("DerivedConfig", (module.MarketOutcomeSourceRecheckStatusConfig,), {})
    with pytest.raises(ValueError, match="stale_ack_seconds"):
        config(stale_ack_seconds=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="open_gap_count"):
        observation("market-int-count", open_gap_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="conflict_count"):
        observation("market-fractional", conflict_count=d("1.500000"))

    for instance in (config(), observation("market-fields"), *report.rows, report):
        for field in fields(instance):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
            ):
                value = getattr(instance, field.name)
                if value is not None:
                    assert type(value) is Decimal, (field.name, value)


def test_datetime_validation_and_row_consistency_reject_tampering() -> None:
    module = api()
    local = timezone(timedelta(hours=-4))
    normalized = observation(
        "market-local",
        next_recheck_due_at=datetime(2026, 7, 2, 7, 30, tzinfo=local),
        last_acknowledged_at=datetime(2026, 7, 2, 7, 45, tzinfo=local),
        last_evidence_checked_at=datetime(2026, 7, 2, 7, 50, tzinfo=local),
    )
    report = build_report(normalized)

    assert report.rows[0].next_recheck_due_at == datetime(2026, 7, 2, 11, 30, tzinfo=UTC)
    assert report.rows[0].ack_age_seconds == d("900.000000")
    assert report.rows[0].evidence_age_seconds == d("600.000000")

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_market_outcome_source_recheck_status_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="next_recheck_due_at must be timezone-aware"):
        observation(
            "market-naive",
            next_recheck_due_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="known timestamp"):
        build_report(
            observation(
                "market-future",
                last_acknowledged_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="unique"):
        build_report(observation("market-dup"), observation("market-dup"))

    with pytest.raises(ValueError, match="blocked_count"):
        replace(report, blocked_count=d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report.rows[0], reason_codes=("market_outcome_source_recheck_cleared",))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    multi_row_report = build_report(
        observation(
            "market-sort-a",
            next_recheck_due_at=GENERATED_AT - timedelta(minutes=5),
        ),
        observation("market-sort-b"),
    )
    with pytest.raises(ValueError, match="payload"):
        replace(multi_row_report, rows=multi_row_report.rows[::-1])


def test_payload_validator_rejects_unsafe_surface_and_public_numerics() -> None:
    module = api()
    report = build_report(observation("market-payload", open_gap_count=d("1.000000")))
    payload = module.market_outcome_source_recheck_status_report_payload(report)

    assert module.validate_market_outcome_source_recheck_status_report_payload(payload) is True
    assert payload["open_gap_count"] == "1.000000"
    assert payload["rows"][0]["open_gap_count"] == "1.000000"
    assert_no_public_float_or_int(payload)

    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.validate_market_outcome_source_recheck_status_report_payload(
            {**payload, "wallet": "paper"},
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        module.validate_market_outcome_source_recheck_status_report_payload(
            {**payload, "market_slug": "wallet"},
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_market_outcome_source_recheck_status_report_payload(
            {**payload, "row_count": 1},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.validate_market_outcome_source_recheck_status_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_outcome_source_recheck_status_report_payload(
            {**payload, "derived_validation_digest": "0" * 64},
        )


def test_module_surface_is_readonly_report_only_and_external_io_free() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))

    assert tuple(module.__all__) == (
        "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_STATUS_REPORT_CONFIG_VERSION",
        "MarketOutcomeSourceRecheckObservation",
        "MarketOutcomeSourceRecheckStatusConfig",
        "MarketOutcomeSourceRecheckStatusReport",
        "MarketOutcomeSourceRecheckStatusRow",
        "build_market_outcome_source_recheck_status_report",
        "market_outcome_source_recheck_status_report_payload",
        "validate_market_outcome_source_recheck_status_report_payload",
    )
    assert set(_imported_modules(tree)) <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    normalized_names = {
        _normalize_identifier(name)
        for name in _collected_names(tree)
        if _normalize_identifier(name) != "readonly"
    }
    for fragment in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "account",
        "broker",
        "submit",
        "cancel",
        "signing",
    ):
        assert not any(fragment in name for name in normalized_names), fragment
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "__import__",
                "compile",
                "eval",
                "exec",
                "input",
                "open",
                "print",
                "read",
                "write",
            }

    payload_text = repr(
        module.market_outcome_source_recheck_status_report_payload(
            build_report(observation("market-safe")),
        ),
    ).lower()
    for fragment in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
    ):
        assert fragment not in payload_text


def _imported_modules(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def _collected_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add(node.name)
            if node.asname is not None:
                names.add(node.asname)
    return names


def _normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())
